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
    Project,
    User,
)
from taxonomy_builder.schemas.publishing import PublishRequest
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.publishing_service import PublishingService
from taxonomy_builder.services.reader_file_service import ReaderFileService
from taxonomy_builder.services.skos_export_service import SKOSExportService
from taxonomy_builder.services.skos_import_service import SKOSImportService
from taxonomy_builder.services.snapshot_service import SnapshotService

_BACKEND_ROOT = Path(__file__).parent.parent.parent.parent
_EVREPO_CORE_TTL = _BACKEND_ROOT / "vocab" / "evrepo-core" / "evrepo-core.ttl"
_EXPRESSIVITY_TTL = _BACKEND_ROOT / "backend" / "tests" / "fixtures" / "ttl" / "ontology-expressivity.ttl"


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
        "published_versions": 0,
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
        namespace="https://vocab.evidence-repository.org/",
        identifier_prefix="EVD",
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
        definition=(
            "An experimental study where participants are randomly"
            " allocated to intervention or control groups."
        ),
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
        definition=(
            "A review using systematic methods to identify, select, and synthesize research."
        ),
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
        # Meta-analysis under Systematic Review AND Primary Studies (polyhierarchy example)
        (meta_analysis.id, systematic_review.id),
        (meta_analysis.id, primary_studies.id),
    ]

    for concept_id, broader_id in broader_relationships:
        session.add(ConceptBroader(concept_id=concept_id, broader_concept_id=broader_id))

    # Publish a version
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

    # Import ontology classes and properties from evrepo-core TTL
    project_service = ProjectService(session)
    import_service = SKOSImportService(session, project_service=project_service)
    ttl_content = _EVREPO_CORE_TTL.read_bytes()
    import_result = await import_service.execute(project.id, ttl_content, "evrepo-core.ttl")
    created["classes"] += len(import_result.classes_created)
    created["properties"] += len(import_result.properties_created)

    # Create another project with a simpler structure
    demo_project = Project(
        name="Demo Taxonomy",
        description="A simple demo taxonomy for testing.",
        namespace="http://example.org/taxonomies/demo",
        identifier_prefix="DMO",
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
        # Polyhierarchy: Yellow and Green span both warm and cool
        (yellow.id, cool.id),
        (green.id, warm.id),
    ]
    for concept_id, broader_id in color_relationships:
        session.add(ConceptBroader(concept_id=concept_id, broader_concept_id=broader_id))
    await session.flush()

    # Create a third project by importing the ontology expressivity test fixture.
    # Exercises: class hierarchy, diamond inheritance, multi-domain properties,
    # property types, OWL restrictions, concept-typed classes, scheme-backed ranges.
    expressivity_project = Project(
        name="Ontology Expressivity Test",
        description="Exercises the full range of OWL/RDFS features supported by the import pipeline.",
        namespace="https://example.org/epic108",
        identifier_prefix="OET",
    )
    session.add(expressivity_project)
    await session.flush()
    created["projects"] += 1

    expressivity_ttl = _EXPRESSIVITY_TTL.read_bytes()
    expressivity_result = await import_service.execute(
        expressivity_project.id, expressivity_ttl, "ontology-expressivity.ttl"
    )
    created["schemes"] += len(expressivity_result.schemes_created)
    created["concepts"] += expressivity_result.total_concepts_created
    created["classes"] += len(expressivity_result.classes_created)
    created["properties"] += len(expressivity_result.properties_created)

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
            publishing_svc = PublishingService(
                session,
                project_svc,
                snapshot_svc,
                reader_file_service=ReaderFileService(blob_store, cdn_purger),
                blob_store=blob_store,
                skos_export_service=SKOSExportService(session),
            )

            projects = await project_svc.list_projects()
            published = 0
            for project in projects:
                existing = await publishing_svc.list_versions(project.id)
                if existing:
                    continue

                try:
                    version = await publishing_svc.publish(
                        project.id,
                        PublishRequest(
                            version="1.0",
                            title=f"{project.name} v1.0",
                            notes="Seed data for local development.",
                        ),
                        publisher="seed",
                    )
                    await publishing_svc.publish_artifacts(version)
                    published += 1
                    print(f"  - {project.name}: published v1.0")
                except Exception as exc:
                    print(f"  - {project.name}: skipped ({exc})")

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
