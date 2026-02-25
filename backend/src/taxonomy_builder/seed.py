"""Seed database with sample data for development."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.blob_store import FilesystemBlobStore, NoOpPurger
from taxonomy_builder.config import settings
from taxonomy_builder.database import DatabaseSessionManager
from taxonomy_builder.models import (
    Concept,
    ConceptBroader,
    ConceptScheme,
    OntologyClass,
    Project,
    Property,
    User,
)
from taxonomy_builder.schemas.publishing import PublishRequest
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.publishing_service import PublishingService
from taxonomy_builder.services.reader_file_service import ReaderFileService
from taxonomy_builder.services.snapshot_service import SnapshotService


async def create_seed_data(session: AsyncSession) -> dict:
    """Create sample data for development.

    Returns a summary of created objects.
    """
    created = {
        "users": 0,
        "projects": 0,
        "schemes": 0,
        "concepts": 0,
        "classes": 0,
        "properties": 0,
    }

    # Create a dev user
    existing_user = await session.execute(select(User).where(User.email == "dev@example.com"))
    if not existing_user.scalar_one_or_none():
        user = User(
            keycloak_user_id="dev-user-local-12345",
            email="dev@example.com",
            display_name="Dev User",
        )
        session.add(user)
        created["users"] += 1

    # Check if we already have the sample project
    existing_project = await session.execute(
        select(Project).where(Project.name == "Evidence Synthesis Taxonomy")
    )
    if existing_project.scalar_one_or_none():
        await session.flush()
        return created

    # Create a sample project
    project = Project(
        name="Evidence Synthesis Taxonomy",
        description="A taxonomy for categorizing systematic review methods and approaches.",
        namespace="https://evrepo.example.org/vocab",
    )
    session.add(project)
    await session.flush()
    created["projects"] += 1

    # Create a concept scheme for study designs
    study_designs = ConceptScheme(
        project_id=project.id,
        title="Study Design Types",
        description="Classification of study design types used in evidence synthesis.",
        uri="http://example.org/taxonomy/study-designs",
    )
    session.add(study_designs)
    await session.flush()
    created["schemes"] += 1

    # Create concepts with hierarchy
    # Top-level concepts
    primary_studies = Concept(
        scheme_id=study_designs.id,
        identifier="primary-studies",
        pref_label="Primary Studies",
        definition="Original research studies that collect and analyze data.",
        alt_labels=["Original Research", "Primary Research"],
    )
    secondary_studies = Concept(
        scheme_id=study_designs.id,
        identifier="secondary-studies",
        pref_label="Secondary Studies",
        definition="Studies that synthesize or analyze existing research.",
        alt_labels=["Research Synthesis"],
    )
    session.add_all([primary_studies, secondary_studies])
    await session.flush()
    created["concepts"] += 2

    # Primary study types
    rct = Concept(
        scheme_id=study_designs.id,
        identifier="rct",
        pref_label="Randomized Controlled Trial",
        definition="An experimental study where participants are randomly allocated to intervention or control groups.",
        scope_note="Considered the gold standard for testing interventions.",
        alt_labels=["RCT", "Randomised Controlled Trial"],
    )
    cohort = Concept(
        scheme_id=study_designs.id,
        identifier="cohort-study",
        pref_label="Cohort Study",
        definition="An observational study following groups over time to compare outcomes.",
        alt_labels=["Cohort", "Longitudinal Study"],
    )
    case_control = Concept(
        scheme_id=study_designs.id,
        identifier="case-control",
        pref_label="Case-Control Study",
        definition="A study comparing people with a condition to those without.",
    )
    cross_sectional = Concept(
        scheme_id=study_designs.id,
        identifier="cross-sectional",
        pref_label="Cross-Sectional Study",
        definition="A study measuring outcomes at a single point in time.",
        alt_labels=["Prevalence Study"],
    )
    session.add_all([rct, cohort, case_control, cross_sectional])
    await session.flush()
    created["concepts"] += 4

    # Secondary study types
    systematic_review = Concept(
        scheme_id=study_designs.id,
        identifier="systematic-review",
        pref_label="Systematic Review",
        definition="A review using systematic methods to identify, select, and synthesize research.",
        scope_note="May or may not include meta-analysis.",
        alt_labels=["SR"],
    )
    meta_analysis = Concept(
        scheme_id=study_designs.id,
        identifier="meta-analysis",
        pref_label="Meta-Analysis",
        definition="Statistical technique combining results from multiple studies.",
        alt_labels=["MA", "Quantitative Synthesis"],
    )
    scoping_review = Concept(
        scheme_id=study_designs.id,
        identifier="scoping-review",
        pref_label="Scoping Review",
        definition="A review mapping available evidence on a topic.",
        alt_labels=["Scoping Study", "Mapping Review"],
    )
    rapid_review = Concept(
        scheme_id=study_designs.id,
        identifier="rapid-review",
        pref_label="Rapid Review",
        definition="A systematic review with accelerated methods.",
        scope_note="Often used when timely evidence is needed.",
    )
    session.add_all([systematic_review, meta_analysis, scoping_review, rapid_review])
    await session.flush()
    created["concepts"] += 4

    # Create broader relationships
    broader_relationships = [
        # Primary study types -> Primary Studies
        (rct.id, primary_studies.id),
        (cohort.id, primary_studies.id),
        (case_control.id, primary_studies.id),
        (cross_sectional.id, primary_studies.id),
        # Secondary study types -> Secondary Studies
        (systematic_review.id, secondary_studies.id),
        (meta_analysis.id, secondary_studies.id),
        (scoping_review.id, secondary_studies.id),
        (rapid_review.id, secondary_studies.id),
        # Meta-analysis can also be under Systematic Review (polyhierarchy example)
        (meta_analysis.id, systematic_review.id),
    ]

    for concept_id, broader_id in broader_relationships:
        session.add(ConceptBroader(concept_id=concept_id, broader_concept_id=broader_id))
    await session.flush()

    # Create a second scheme for risk of bias
    risk_of_bias = ConceptScheme(
        project_id=project.id,
        title="Risk of Bias Domains",
        description="Domains for assessing risk of bias in studies.",
        uri="http://example.org/taxonomy/risk-of-bias",
    )
    session.add(risk_of_bias)
    await session.flush()
    created["schemes"] += 1

    # Risk of bias concepts
    selection_bias = Concept(
        scheme_id=risk_of_bias.id,
        identifier="selection-bias",
        pref_label="Selection Bias",
        definition="Systematic differences in participant selection.",
    )
    performance_bias = Concept(
        scheme_id=risk_of_bias.id,
        identifier="performance-bias",
        pref_label="Performance Bias",
        definition="Systematic differences in care provided apart from intervention.",
    )
    detection_bias = Concept(
        scheme_id=risk_of_bias.id,
        identifier="detection-bias",
        pref_label="Detection Bias",
        definition="Systematic differences in outcome assessment.",
    )
    attrition_bias = Concept(
        scheme_id=risk_of_bias.id,
        identifier="attrition-bias",
        pref_label="Attrition Bias",
        definition="Systematic differences in withdrawals from the study.",
    )
    reporting_bias = Concept(
        scheme_id=risk_of_bias.id,
        identifier="reporting-bias",
        pref_label="Reporting Bias",
        definition="Systematic differences in reported vs unreported findings.",
    )
    session.add_all(
        [selection_bias, performance_bias, detection_bias, attrition_bias, reporting_bias]
    )
    await session.flush()
    created["concepts"] += 5

    # Ontology classes from evrepo-core
    ns = project.namespace
    class_data = [
        ("Investigation", "Investigation", "A research investigation or study."),
        ("Finding", "Finding", "A finding or result reported by an investigation."),
        ("Intervention", "Intervention", "An intervention evaluated in a study."),
        ("Outcome", "Outcome", "A measured outcome of an intervention."),
        (
            "EffectEstimate",
            "Effect Estimate",
            "A quantitative estimate of an intervention's effect.",
        ),
        ("Context", "Context", "The context in which a study was conducted."),
        ("Funder", "Funder", "An entity that funded a study."),
        ("Implementer", "Implementer", "An entity that implemented an intervention."),
    ]
    classes = {}
    for identifier, label, description in class_data:
        cls = OntologyClass(
            project_id=project.id,
            identifier=identifier,
            label=label,
            description=description,
            uri=f"{ns}/{identifier}",
        )
        session.add(cls)
        classes[identifier] = cls
    await session.flush()
    created["classes"] += len(class_data)

    # Properties from evrepo-core — exercising all three range types
    property_records = [
        # class-to-class (range_class)
        Property(
            project_id=project.id,
            identifier="hasFinding",
            label="has finding",
            description="Links an investigation to one of its findings.",
            domain_class=f"{ns}/Investigation",
            range_class=f"{ns}/Finding",
            cardinality="multiple",
            uri=f"{ns}/hasFinding",
        ),
        Property(
            project_id=project.id,
            identifier="evaluates",
            label="evaluates",
            description="Links a finding to the intervention it evaluates.",
            domain_class=f"{ns}/Finding",
            range_class=f"{ns}/Intervention",
            cardinality="single",
            uri=f"{ns}/evaluates",
        ),
        Property(
            project_id=project.id,
            identifier="hasContext",
            label="has context",
            description="Links a finding to its study context.",
            domain_class=f"{ns}/Finding",
            range_class=f"{ns}/Context",
            cardinality="single",
            uri=f"{ns}/hasContext",
        ),
        Property(
            project_id=project.id,
            identifier="hasEffectEstimate",
            label="has effect estimate",
            description="Links a finding to a quantitative effect estimate.",
            domain_class=f"{ns}/Finding",
            range_class=f"{ns}/EffectEstimate",
            cardinality="multiple",
            uri=f"{ns}/hasEffectEstimate",
        ),
        Property(
            project_id=project.id,
            identifier="implementedBy",
            label="implemented by",
            description="Links an intervention to its implementing entity.",
            domain_class=f"{ns}/Intervention",
            range_class=f"{ns}/Implementer",
            cardinality="multiple",
            uri=f"{ns}/implementedBy",
        ),
        # class-to-scheme (range_scheme_id)
        Property(
            project_id=project.id,
            identifier="studyDesign",
            label="study design",
            description="The study design used by an investigation.",
            domain_class=f"{ns}/Investigation",
            range_scheme_id=study_designs.id,
            cardinality="single",
            uri=f"{ns}/studyDesign",
        ),
        # class-to-datatype (range_datatype)
        Property(
            project_id=project.id,
            identifier="effectSize",
            label="effect size",
            description="The numeric effect size of an effect estimate.",
            domain_class=f"{ns}/EffectEstimate",
            range_datatype="xsd:decimal",
            cardinality="single",
            uri=f"{ns}/effectSize",
        ),
        Property(
            project_id=project.id,
            identifier="outcomeDescription",
            label="outcome description",
            description="A textual description of an outcome.",
            domain_class=f"{ns}/Outcome",
            range_datatype="xsd:string",
            cardinality="single",
            uri=f"{ns}/outcomeDescription",
        ),
    ]
    session.add_all(property_records)
    await session.flush()
    created["properties"] += len(property_records)

    # Create another project with a simpler structure
    demo_project = Project(
        name="Demo Taxonomy",
        description="A simple demo taxonomy for testing.",
        namespace="http://example.org/taxonomies/demo",
    )
    session.add(demo_project)
    await session.flush()
    created["projects"] += 1

    demo_scheme = ConceptScheme(
        project_id=demo_project.id,
        title="Colors",
        description="A simple color taxonomy.",
        uri="http://example.org/demo/colors",
    )
    session.add(demo_scheme)
    await session.flush()
    created["schemes"] += 1

    warm = Concept(
        scheme_id=demo_scheme.id,
        identifier="warm",
        pref_label="Warm Colors",
        definition="Colors associated with warmth.",
    )
    cool = Concept(
        scheme_id=demo_scheme.id,
        identifier="cool",
        pref_label="Cool Colors",
        definition="Colors associated with coolness.",
    )
    session.add_all([warm, cool])
    await session.flush()
    created["concepts"] += 2

    red = Concept(
        scheme_id=demo_scheme.id,
        identifier="red",
        pref_label="Red",
        alt_labels=["Crimson", "Scarlet"],
    )
    orange = Concept(
        scheme_id=demo_scheme.id,
        identifier="orange",
        pref_label="Orange",
    )
    yellow = Concept(
        scheme_id=demo_scheme.id,
        identifier="yellow",
        pref_label="Yellow",
        alt_labels=["Gold"],
    )
    blue = Concept(
        scheme_id=demo_scheme.id,
        identifier="blue",
        pref_label="Blue",
        alt_labels=["Azure", "Navy"],
    )
    green = Concept(
        scheme_id=demo_scheme.id,
        identifier="green",
        pref_label="Green",
        alt_labels=["Emerald"],
    )
    purple = Concept(
        scheme_id=demo_scheme.id,
        identifier="purple",
        pref_label="Purple",
        alt_labels=["Violet"],
    )
    session.add_all([red, orange, yellow, blue, green, purple])
    await session.flush()
    created["concepts"] += 6

    # Broader relationships for colors
    color_relationships = [
        (red.id, warm.id),
        (orange.id, warm.id),
        (yellow.id, warm.id),
        (blue.id, cool.id),
        (green.id, cool.id),
        (purple.id, cool.id),
    ]
    for concept_id, broader_id in color_relationships:
        session.add(ConceptBroader(concept_id=concept_id, broader_concept_id=broader_id))
    await session.flush()

    return created


async def publish_seed_projects(session_manager: DatabaseSessionManager) -> None:
    """Publish all unpublished projects and write reader files to blob storage."""
    blob_root = Path(settings.blob_filesystem_root).resolve()
    blob_store = FilesystemBlobStore(root=blob_root)
    cdn_purger = NoOpPurger()

    try:
        async with session_manager.session() as session:
            project_svc = ProjectService(session)
            concept_svc = ConceptService(session)
            snapshot_svc = SnapshotService(session, project_svc, concept_svc)
            publishing_svc = PublishingService(session, project_svc, snapshot_svc)
            reader_svc = ReaderFileService(publishing_svc, blob_store, cdn_purger)

            projects = await project_svc.list_projects()
            published = 0
            for project in projects:
                existing = await publishing_svc.list_versions(project.id)
                if existing:
                    continue

                version = await publishing_svc.publish(
                    project.id,
                    PublishRequest(
                        version="1.0",
                        title=f"{project.name} v1.0",
                        notes="Seed data for local development.",
                    ),
                    publisher="seed",
                )
                await reader_svc.publish_reader_files(version)
                published += 1
                print(f"  - {project.name}: published v1.0")

            if published == 0:
                print("  (all projects already published)")
    finally:
        await blob_store.close()
        await cdn_purger.close()


async def run_seed() -> None:
    """Run the seeding process."""
    db_url = settings.effective_database_url
    print(f"Seeding database: {db_url.split('@')[-1]}")  # Only show host/db, not creds

    session_manager = DatabaseSessionManager()
    session_manager.init(db_url)

    try:
        async with session_manager.session() as session:
            created = await create_seed_data(session)
            await session.commit()

        print("Seed data created:")
        for entity, count in created.items():
            if count > 0:
                print(f"  - {entity}: {count}")

        if all(c == 0 for c in created.values()):
            print("  (data already exists, nothing created)")

        print("Publishing seed projects:")
        await publish_seed_projects(session_manager)

    finally:
        await session_manager.close()


def main() -> None:
    """Entry point for CLI."""
    asyncio.run(run_seed())


if __name__ == "__main__":
    sys.exit(main() or 0)
