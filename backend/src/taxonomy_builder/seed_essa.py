"""Seed database with ESSA (evidence in education) project data.

Derived from the ESSA JSON-LD instance document describing a Reading Recovery
RCT (May et al., 2015). Creates:
  - 1 project
  - 11 concept schemes
  - 8 concepts across those schemes
  - 20 properties linking ontology classes to schemes and datatypes
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.config import settings
from taxonomy_builder.database import DatabaseSessionManager
from taxonomy_builder.models import Concept, ConceptScheme, Project, Property

ESSA_NAMESPACE = "https://example.org/destiny/essa/"
EVREPO_NS = "https://evrepo.example.org/vocab/"


async def create_essa_data(session: AsyncSession) -> dict:
    """Create ESSA project with schemes, concepts, and properties."""
    created = {"projects": 0, "schemes": 0, "concepts": 0, "properties": 0}

    # Check if ESSA project already exists
    existing = await session.execute(
        select(Project).where(Project.name == "ESSA")
    )
    if existing.scalar_one_or_none():
        return created

    # --- Project ---
    project = Project(
        name="ESSA",
        description=(
            "Evidence for ESSA: a taxonomy for categorizing education research "
            "evidence aligned with the Every Student Succeeds Act evidence tiers."
        ),
        namespace=ESSA_NAMESPACE,
    )
    session.add(project)
    await session.flush()
    created["projects"] += 1

    # --- Concept Schemes ---
    scheme_defs = [
        {
            "title": "Study Design Types",
            "description": "Classification of research study designs (RCT, quasi-experimental, etc.).",
            "uri": f"{ESSA_NAMESPACE}concept/study-design",
        },
        {
            "title": "Education Level",
            "description": "Grade levels and education stages.",
            "uri": f"{ESSA_NAMESPACE}concept/education-level",
        },
        {
            "title": "Education Setting",
            "description": "Geographic and institutional settings for education research.",
            "uri": f"{ESSA_NAMESPACE}concept/education-setting",
        },
        {
            "title": "Education Outcome",
            "description": "Types of measured education outcomes.",
            "uri": f"{ESSA_NAMESPACE}concept/edu-outcome",
        },
        {
            "title": "Education Theme",
            "description": "Thematic areas in education research.",
            "uri": f"{ESSA_NAMESPACE}concept/edu-theme",
        },
        {
            "title": "Sample Feature",
            "description": "Characteristics of study samples and populations.",
            "uri": f"{ESSA_NAMESPACE}concept/sample-feature",
        },
        {
            "title": "Effect Size Type",
            "description": "Types of effect size metrics used in quantitative research.",
            "uri": f"{ESSA_NAMESPACE}concept/effect-size-type",
        },
        {
            "title": "Implementer Type",
            "description": "Categories of organisations that implement interventions.",
            "uri": f"{ESSA_NAMESPACE}concept/implementer-type",
        },
        {
            "title": "Implementation Components",
            "description": "Elements included in intervention delivery (training, materials, etc.).",
            "uri": f"{ESSA_NAMESPACE}concept/implementation-component",
        },
        {
            "title": "Participant Type",
            "description": "Types of research participants (students, teachers, etc.).",
            "uri": f"{ESSA_NAMESPACE}concept/participant-type",
        },
        {
            "title": "Fidelity Type",
            "description": "Types of implementation fidelity information reported.",
            "uri": f"{ESSA_NAMESPACE}concept/fidelity-type",
        },
    ]

    scheme_map: dict[str, ConceptScheme] = {}
    for sdef in scheme_defs:
        scheme = ConceptScheme(project_id=project.id, **sdef)
        session.add(scheme)
        scheme_map[sdef["title"]] = scheme
    await session.flush()
    created["schemes"] += len(scheme_defs)

    # --- Concepts (from the JSON-LD @graph) ---
    concept_defs = [
        # Study Design Types
        {
            "scheme": "Study Design Types",
            "identifier": "rct",
            "pref_label": "Randomized controlled trial (RCT)",
            "alt_labels": ["RCT"],
        },
        # Education Level
        {
            "scheme": "Education Level",
            "identifier": "grade-1",
            "pref_label": "Grade 1",
        },
        # Education Setting
        {
            "scheme": "Education Setting",
            "identifier": "us-elementary-multisite",
            "pref_label": "Elementary schools (United States, multisite)",
        },
        # Education Outcome
        {
            "scheme": "Education Outcome",
            "identifier": "reading-achievement",
            "pref_label": "Reading achievement",
        },
        # Education Theme
        {
            "scheme": "Education Theme",
            "identifier": "early-literacy",
            "pref_label": "Early literacy",
        },
        # Sample Feature
        {
            "scheme": "Sample Feature",
            "identifier": "lowest-achieving-readers",
            "pref_label": "Lowest achieving readers / struggling readers",
            "definition": "Students identified as lowest achieving readers, eligible for Reading Recovery or similar interventions.",
        },
        # Effect Size Type
        {
            "scheme": "Effect Size Type",
            "identifier": "cohens-d-population-based",
            "pref_label": "Cohen's d (population-based)",
            "definition": "Standardized mean difference using national norm SD.",
            "alt_labels": ["Cohen's d"],
        },
        {
            "scheme": "Effect Size Type",
            "identifier": "glass-d-sample-based",
            "pref_label": "Glass's D (sample-based)",
            "definition": "Standardized mean difference using control-group SD.",
            "alt_labels": ["Glass's D", "Glass's delta"],
        },
    ]

    for cdef in concept_defs:
        scheme = scheme_map[cdef["scheme"]]
        concept = Concept(
            scheme_id=scheme.id,
            identifier=cdef["identifier"],
            pref_label=cdef["pref_label"],
            definition=cdef.get("definition"),
            alt_labels=cdef.get("alt_labels", []),
        )
        session.add(concept)
    await session.flush()
    created["concepts"] += len(concept_defs)

    # --- Properties (linking ontology classes to schemes and datatypes) ---

    def cls(name: str) -> str:
        """Return the full ontology class URI."""
        return f"{EVREPO_NS}{name}"

    property_defs = [
        # Investigation properties
        {
            "identifier": "studyDesign",
            "label": "study design",
            "description": "The research design used in the investigation.",
            "domain_class": cls("Investigation"),
            "range_scheme": "Study Design Types",
            "cardinality": "single",
            "required": True,
        },
        {
            "identifier": "educationSetting",
            "label": "education setting",
            "description": "Geographic and institutional setting of the investigation.",
            "domain_class": cls("Investigation"),
            "range_scheme": "Education Setting",
            "cardinality": "multiple",
        },
        {
            "identifier": "educationLevel",
            "label": "education level",
            "description": "Grade level or education stage of the study population.",
            "domain_class": cls("Investigation"),
            "range_scheme": "Education Level",
            "cardinality": "multiple",
        },
        {
            "identifier": "publicationYear",
            "label": "publication year",
            "description": "Year the investigation was published.",
            "domain_class": cls("Investigation"),
            "range_datatype": "xsd:integer",
            "cardinality": "single",
        },
        {
            "identifier": "sampleSize",
            "label": "sample size",
            "description": "Total number of participants enrolled in the study.",
            "domain_class": cls("Investigation"),
            "range_datatype": "xsd:integer",
            "cardinality": "single",
        },
        # Finding properties
        {
            "identifier": "eduOutcome",
            "label": "education outcome",
            "description": "The type of education outcome measured.",
            "domain_class": cls("Finding"),
            "range_scheme": "Education Outcome",
            "cardinality": "single",
        },
        {
            "identifier": "eduTheme",
            "label": "education theme",
            "description": "Thematic classification of the finding.",
            "domain_class": cls("Finding"),
            "range_scheme": "Education Theme",
            "cardinality": "multiple",
        },
        {
            "identifier": "sampleFeature",
            "label": "sample feature",
            "description": "Characteristics of the study sample relevant to this finding.",
            "domain_class": cls("Finding"),
            "range_scheme": "Sample Feature",
            "cardinality": "multiple",
        },
        # EffectEstimate properties
        {
            "identifier": "effectSizeType",
            "label": "effect size type",
            "description": "The metric used for the effect size (e.g., Cohen's d, Hedges' g).",
            "domain_class": cls("EffectEstimate"),
            "range_scheme": "Effect Size Type",
            "cardinality": "single",
            "required": True,
        },
        {
            "identifier": "effectSizeValue",
            "label": "effect size value",
            "description": "The numerical value of the effect size.",
            "domain_class": cls("EffectEstimate"),
            "range_datatype": "xsd:decimal",
            "cardinality": "single",
            "required": True,
        },
        {
            "identifier": "standardError",
            "label": "standard error",
            "description": "Standard error of the effect estimate.",
            "domain_class": cls("EffectEstimate"),
            "range_datatype": "xsd:decimal",
            "cardinality": "single",
        },
        {
            "identifier": "pValue",
            "label": "p-value",
            "description": "Statistical significance level.",
            "domain_class": cls("EffectEstimate"),
            "range_datatype": "xsd:string",
            "cardinality": "single",
        },
        # Context properties
        {
            "identifier": "contextEducationLevel",
            "label": "education level",
            "description": "Grade level or education stage of the study context.",
            "domain_class": cls("Context"),
            "range_scheme": "Education Level",
            "cardinality": "multiple",
        },
        {
            "identifier": "contextEducationSetting",
            "label": "education setting",
            "description": "Geographic and institutional setting of the study context.",
            "domain_class": cls("Context"),
            "range_scheme": "Education Setting",
            "cardinality": "multiple",
        },
        # Intervention properties
        {
            "identifier": "educationTheme",
            "label": "education theme",
            "description": "Strategic domain of focus within education.",
            "domain_class": cls("Intervention"),
            "range_scheme": "Education Theme",
            "cardinality": "multiple",
        },
        {
            "identifier": "implementerType",
            "label": "implementer type",
            "description": "Category of implementing organisation.",
            "domain_class": cls("Intervention"),
            "range_scheme": "Implementer Type",
            "cardinality": "single",
        },
        {
            "identifier": "implementationComponent",
            "label": "implementation component",
            "description": "Elements included in delivery (training, materials, etc.).",
            "domain_class": cls("Intervention"),
            "range_scheme": "Implementation Components",
            "cardinality": "multiple",
        },
        {
            "identifier": "implementationFidelity",
            "label": "implementation fidelity",
            "description": "Type of fidelity information provided.",
            "domain_class": cls("Intervention"),
            "range_scheme": "Fidelity Type",
            "cardinality": "single",
        },
        # Finding — additional properties
        {
            "identifier": "participantType",
            "label": "participant type",
            "description": "Type of participants (students, teachers, etc.).",
            "domain_class": cls("Finding"),
            "range_scheme": "Participant Type",
            "cardinality": "multiple",
        },
        # Outcome properties
        {
            "identifier": "outcomeType",
            "label": "education outcome",
            "description": "Education-specific outcome type classification.",
            "domain_class": cls("Outcome"),
            "range_scheme": "Education Outcome",
            "cardinality": "single",
        },
    ]

    for pdef in property_defs:
        prop = Property(
            project_id=project.id,
            identifier=pdef["identifier"],
            label=pdef["label"],
            description=pdef.get("description"),
            domain_class=pdef["domain_class"],
            range_scheme_id=scheme_map[pdef["range_scheme"]].id if pdef.get("range_scheme") else None,
            range_datatype=pdef.get("range_datatype"),
            cardinality=pdef["cardinality"],
            required=pdef.get("required", False),
        )
        session.add(prop)
    await session.flush()
    created["properties"] += len(property_defs)

    return created


async def run_seed() -> None:
    """Run the ESSA seeding process."""
    db_url = settings.effective_database_url
    print(f"Seeding ESSA data into: {db_url.split('@')[-1]}")

    session_manager = DatabaseSessionManager()
    session_manager.init(db_url)

    try:
        async with session_manager.session() as session:
            created = await create_essa_data(session)
            await session.commit()

        print("ESSA seed data created:")
        for entity, count in created.items():
            if count > 0:
                print(f"  - {entity}: {count}")

        if all(c == 0 for c in created.values()):
            print("  (ESSA data already exists, nothing created)")

    finally:
        await session_manager.close()


def main() -> None:
    """Entry point for CLI."""
    asyncio.run(run_seed())


if __name__ == "__main__":
    sys.exit(main() or 0)
