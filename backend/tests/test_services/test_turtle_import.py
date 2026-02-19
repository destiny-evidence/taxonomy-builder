"""Tests for full ontology Turtle import (OWL classes + properties)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.services.skos_import_service import SKOSImportService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Turtle Import Test Project", namespace="http://example.org")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
def import_service(db_session: AsyncSession) -> SKOSImportService:
    """Create import service instance."""
    return SKOSImportService(db_session)


# --- Test data ---

# Full ontology: classes, concept-subclasses, schemes, concepts, properties
FULL_ONTOLOGY_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

# Domain classes (should become OntologyClass)
ex:Finding a owl:Class ;
    rdfs:label "Finding" ;
    rdfs:comment "A research finding" .

ex:Outcome a owl:Class ;
    rdfs:label "Outcome" ;
    skos:scopeNote "Used in evidence synthesis" .

# Concept subclass (should NOT become OntologyClass)
ex:EducationLevel a owl:Class ;
    rdfs:subClassOf skos:Concept ;
    rdfs:label "Education Level" .

# Concept schemes
ex:EducationLevelScheme a skos:ConceptScheme ;
    rdfs:label "Education Levels" .

ex:OutcomeTypeScheme a skos:ConceptScheme ;
    rdfs:label "Outcome Types" .

# Concepts (typed via subclass)
ex:Primary a ex:EducationLevel ;
    skos:inScheme ex:EducationLevelScheme ;
    skos:prefLabel "Primary Education" .

ex:Secondary a ex:EducationLevel ;
    skos:inScheme ex:EducationLevelScheme ;
    skos:prefLabel "Secondary Education" ;
    skos:broader ex:Primary .

ex:Academic a skos:Concept ;
    skos:inScheme ex:OutcomeTypeScheme ;
    skos:prefLabel "Academic" .

# Object property - range resolves to scheme via RDF linkage
ex:educationLevel a owl:ObjectProperty ;
    rdfs:label "Education Level" ;
    rdfs:comment "The education level of a finding" ;
    rdfs:domain ex:Finding ;
    rdfs:range ex:EducationLevel .

# Object property - range IS a scheme URI (direct match)
ex:outcomeType a owl:ObjectProperty ;
    rdfs:label "Outcome Type" ;
    rdfs:domain ex:Outcome ;
    rdfs:range ex:OutcomeTypeScheme .

# Object property - range resolves to OntologyClass
ex:hasFinding a owl:ObjectProperty ;
    rdfs:label "has finding" ;
    rdfs:domain ex:Outcome ;
    rdfs:range ex:Finding .

# Datatype property
ex:sampleSize a owl:DatatypeProperty ;
    rdfs:label "Sample Size" ;
    rdfs:comment "Number of participants" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:integer .
"""

# Property whose range doesn't exist in the project
NO_RANGE_MATCH_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:mysteryCoding a owl:ObjectProperty ;
    rdfs:label "Mystery Coding" ;
    rdfs:domain ex:Finding ;
    rdfs:range ex:UnknownClass .
"""

# Datatype properties only (no classes, no schemes)
DATATYPE_ONLY_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

ex:title a owl:DatatypeProperty ;
    rdfs:label "Title" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:string .

ex:count a owl:DatatypeProperty ;
    rdfs:label "Count" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:integer .
"""


class TestPreview:
    """Preview (dry run) tests."""

    @pytest.mark.asyncio
    async def test_preview_counts_all_entity_types(
        self, import_service: SKOSImportService, project: Project
    ) -> None:
        """Preview shows correct counts for classes, schemes, concepts, properties."""
        result = await import_service.preview(project.id, FULL_ONTOLOGY_TTL, "test.ttl")

        assert result.valid is True
        assert result.classes_count == 2  # Finding, Outcome (not EducationLevel)
        assert len(result.schemes) == 2
        assert result.total_concepts_count == 3
        assert result.properties_count == 4

        # Class detail
        identifiers = {c.identifier for c in result.classes}
        assert identifiers == {"Finding", "Outcome"}

        # Property detail
        edu = next(p for p in result.properties if p.identifier == "educationLevel")
        assert edu.property_type == "object"
        assert edu.domain_class_uri == "http://example.org/Finding"

        sample = next(p for p in result.properties if p.identifier == "sampleSize")
        assert sample.property_type == "datatype"
        assert sample.range_uri == "http://www.w3.org/2001/XMLSchema#integer"

    @pytest.mark.asyncio
    async def test_preview_datatype_only(
        self, import_service: SKOSImportService, project: Project
    ) -> None:
        """File with only datatype properties, no classes or schemes."""
        result = await import_service.preview(project.id, DATATYPE_ONLY_TTL, "test.ttl")

        assert result.classes_count == 0
        assert result.properties_count == 2
        assert all(p.property_type == "datatype" for p in result.properties)


class TestExecute:
    """Import execution tests."""

    @pytest.mark.asyncio
    async def test_full_ontology_creates_all_entities(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """Import creates classes, schemes, concepts, and properties."""
        result = await import_service.execute(project.id, FULL_ONTOLOGY_TTL, "test.ttl")

        assert len(result.classes_created) == 2
        assert len(result.schemes_created) == 2
        assert result.total_concepts_created == 3
        assert len(result.properties_created) == 4

    @pytest.mark.asyncio
    async def test_concept_subclasses_excluded_from_classes(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """Classes with rdfs:subClassOf skos:Concept are not OntologyClass records."""
        await import_service.execute(project.id, FULL_ONTOLOGY_TTL, "test.ttl")

        classes = (
            await db_session.execute(
                select(OntologyClass).where(OntologyClass.project_id == project.id)
            )
        ).scalars().all()
        assert {c.identifier for c in classes} == {"Finding", "Outcome"}

    @pytest.mark.asyncio
    async def test_class_metadata_stored(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """OntologyClass records have correct label, description, scope_note."""
        await import_service.execute(project.id, FULL_ONTOLOGY_TTL, "test.ttl")

        classes = (
            await db_session.execute(
                select(OntologyClass).where(OntologyClass.project_id == project.id)
            )
        ).scalars().all()

        finding = next(c for c in classes if c.identifier == "Finding")
        assert finding.label == "Finding"
        assert finding.description == "A research finding"

        outcome = next(c for c in classes if c.identifier == "Outcome")
        assert outcome.scope_note == "Used in evidence synthesis"

    @pytest.mark.asyncio
    async def test_duplicate_class_skipped(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """Re-importing the same class identifier is silently skipped."""
        await import_service.execute(project.id, FULL_ONTOLOGY_TTL, "test.ttl")
        # Import again - classes should not duplicate
        # (schemes will conflict, so use a class-only file)
        class_only = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .
"""
        result = await import_service.execute(project.id, class_only, "test.ttl")
        assert len(result.classes_created) == 0

    @pytest.mark.asyncio
    async def test_range_resolved_to_scheme_via_rdf_linkage(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """Object property range resolves to scheme when typed concepts exist."""
        await import_service.execute(project.id, FULL_ONTOLOGY_TTL, "test.ttl")

        props = (
            await db_session.execute(
                select(Property).where(Property.project_id == project.id)
            )
        ).scalars().all()

        edu_prop = next(p for p in props if p.identifier == "educationLevel")
        assert edu_prop.range_scheme_id is not None
        scheme = await db_session.get(ConceptScheme, edu_prop.range_scheme_id)
        assert scheme.title == "Education Levels"

    @pytest.mark.asyncio
    async def test_range_resolved_to_scheme_by_direct_match(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """Object property range resolves when the URI IS a scheme URI."""
        await import_service.execute(project.id, FULL_ONTOLOGY_TTL, "test.ttl")

        props = (
            await db_session.execute(
                select(Property).where(Property.project_id == project.id)
            )
        ).scalars().all()

        prop = next(p for p in props if p.identifier == "outcomeType")
        assert prop.range_scheme_id is not None
        scheme = await db_session.get(ConceptScheme, prop.range_scheme_id)
        assert scheme.title == "Outcome Types"

    @pytest.mark.asyncio
    async def test_range_resolved_to_ontology_class(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """Object property range resolves to OntologyClass in same project."""
        await import_service.execute(project.id, FULL_ONTOLOGY_TTL, "test.ttl")

        props = (
            await db_session.execute(
                select(Property).where(Property.project_id == project.id)
            )
        ).scalars().all()

        prop = next(p for p in props if p.identifier == "hasFinding")
        assert prop.range_class_id is not None
        assert prop.range_scheme_id is None
        ont_class = await db_session.get(OntologyClass, prop.range_class_id)
        assert ont_class.identifier == "Finding"

    @pytest.mark.asyncio
    async def test_unresolvable_range_emits_warning(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """Unresolvable range leaves all range fields NULL and emits warning."""
        result = await import_service.execute(project.id, NO_RANGE_MATCH_TTL, "test.ttl")

        props = (
            await db_session.execute(
                select(Property).where(Property.project_id == project.id)
            )
        ).scalars().all()
        prop = props[0]
        assert prop.range_scheme_id is None
        assert prop.range_datatype is None
        assert prop.range_class_id is None

        assert len(result.warnings) == 1
        assert "UnknownClass" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_datatype_property_xsd_abbreviated(
        self, db_session: AsyncSession, import_service: SKOSImportService, project: Project
    ) -> None:
        """XSD ranges are abbreviated to xsd: prefix."""
        await import_service.execute(project.id, DATATYPE_ONLY_TTL, "test.ttl")

        props = (
            await db_session.execute(
                select(Property).where(Property.project_id == project.id)
            )
        ).scalars().all()

        title_prop = next(p for p in props if p.identifier == "title")
        assert title_prop.range_datatype == "xsd:string"

        count_prop = next(p for p in props if p.identifier == "count")
        assert count_prop.range_datatype == "xsd:integer"

    @pytest.mark.asyncio
    async def test_skos_only_backward_compatible(
        self, import_service: SKOSImportService, project: Project
    ) -> None:
        """SKOS-only file still works with zero classes/properties."""
        skos_only = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "Test Scheme" .

ex:Concept1 a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:prefLabel "First Concept" .
"""
        result = await import_service.execute(project.id, skos_only, "test.ttl")

        assert len(result.schemes_created) == 1
        assert result.total_concepts_created == 1
        assert len(result.classes_created) == 0
        assert len(result.properties_created) == 0
