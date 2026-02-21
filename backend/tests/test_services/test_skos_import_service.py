"""Tests for SKOS Import Service."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.services.skos_import_service import (
    InvalidRDFError,
    SchemeURIConflictError,
    SKOSImportService,
)


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
def import_service(db_session: AsyncSession) -> SKOSImportService:
    """Create import service instance."""
    return SKOSImportService(db_session)


# Sample SKOS data for testing

SIMPLE_SCHEME_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "Test Scheme" ;
    rdfs:comment "A test concept scheme" .

ex:Concept1 a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:prefLabel "First Concept" ;
    skos:definition "The first concept in the scheme" .

ex:Concept2 a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:prefLabel "Second Concept" ;
    skos:broader ex:Concept1 .
"""

MULTI_SCHEME_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:SchemeA a skos:ConceptScheme ;
    rdfs:label "Scheme A" .

ex:SchemeB a skos:ConceptScheme ;
    rdfs:label "Scheme B" .

ex:ConceptA1 a skos:Concept ;
    skos:inScheme ex:SchemeA ;
    skos:prefLabel "Concept A1" .

ex:ConceptB1 a skos:Concept ;
    skos:inScheme ex:SchemeB ;
    skos:prefLabel "Concept B1" .

ex:ConceptB2 a skos:Concept ;
    skos:inScheme ex:SchemeB ;
    skos:prefLabel "Concept B2" .
"""

SUBCLASS_CONCEPT_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:EducationLevel a owl:Class ;
    rdfs:subClassOf skos:Concept .

ex:EducationLevelScheme a skos:ConceptScheme ;
    rdfs:label "Education Levels" .

ex:Primary a ex:EducationLevel ;
    skos:inScheme ex:EducationLevelScheme ;
    skos:prefLabel "Primary Education" .

ex:Secondary a ex:EducationLevel ;
    skos:inScheme ex:EducationLevelScheme ;
    skos:prefLabel "Secondary Education" ;
    skos:broader ex:Primary .
"""

NO_PREFLABEL_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "Test Scheme" .

ex:ConceptWithoutLabel a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:definition "This concept has no prefLabel" .
"""

ALT_LABELS_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "Test Scheme" .

ex:Dogs a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:prefLabel "Dogs" ;
    skos:altLabel "Canines" ;
    skos:altLabel "Domestic dogs" .
"""

ORPHAN_CONCEPT_SINGLE_SCHEME_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "Test Scheme" .

ex:ConceptWithScheme a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:prefLabel "Concept With Scheme" .

ex:OrphanConcept a skos:Concept ;
    skos:prefLabel "Orphan Concept" .
"""

ORPHAN_CONCEPT_MULTI_SCHEME_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:SchemeA a skos:ConceptScheme ;
    rdfs:label "Scheme A" .

ex:SchemeB a skos:ConceptScheme ;
    rdfs:label "Scheme B" .

ex:ConceptA a skos:Concept ;
    skos:inScheme ex:SchemeA ;
    skos:prefLabel "Concept A" .

ex:OrphanConcept a skos:Concept ;
    skos:prefLabel "Orphan Concept" .
"""

TOP_CONCEPT_OF_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "Test Scheme" .

ex:TopConcept a skos:Concept ;
    skos:topConceptOf ex:TestScheme ;
    skos:prefLabel "Top Concept" .
"""

SCHEME_TITLE_PRIORITY_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "RDFS Label Title" ;
    skos:prefLabel "SKOS PrefLabel Title" ;
    dcterms:title "DCTerms Title" .
"""

INVALID_RDF = b"""
This is not valid RDF at all.
Just random text.
"""


# Preview tests - single scheme


@pytest.mark.asyncio
async def test_preview_simple_scheme(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test previewing a simple single-scheme file."""
    result = await import_service.preview(
        project.id, SIMPLE_SCHEME_TTL, "test.ttl"
    )

    assert result.valid is True
    assert len(result.schemes) == 1
    assert result.schemes[0].title == "Test Scheme"
    assert result.schemes[0].uri == "http://example.org/TestScheme"
    assert result.schemes[0].concepts_count == 2
    assert result.schemes[0].relationships_count == 1  # One broader relationship
    assert result.total_concepts_count == 2
    assert result.total_relationships_count == 1


@pytest.mark.asyncio
async def test_preview_multiple_schemes(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test previewing a file with multiple schemes."""
    result = await import_service.preview(
        project.id, MULTI_SCHEME_TTL, "test.ttl"
    )

    assert result.valid is True
    assert len(result.schemes) == 2
    assert result.total_concepts_count == 3

    # Find schemes by title
    scheme_a = next(s for s in result.schemes if s.title == "Scheme A")
    scheme_b = next(s for s in result.schemes if s.title == "Scheme B")

    assert scheme_a.concepts_count == 1
    assert scheme_b.concepts_count == 2


@pytest.mark.asyncio
async def test_preview_subclassed_concepts(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that concepts typed as subclasses of skos:Concept are detected."""
    result = await import_service.preview(
        project.id, SUBCLASS_CONCEPT_TTL, "test.ttl"
    )

    assert result.valid is True
    assert len(result.schemes) == 1
    assert result.schemes[0].concepts_count == 2
    assert result.schemes[0].relationships_count == 1


@pytest.mark.asyncio
async def test_preview_missing_preflabel_warning(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that missing prefLabel generates a warning."""
    result = await import_service.preview(
        project.id, NO_PREFLABEL_TTL, "test.ttl"
    )

    assert result.valid is True
    assert len(result.schemes[0].warnings) > 0
    assert any("prefLabel" in w for w in result.schemes[0].warnings)


@pytest.mark.asyncio
async def test_preview_scheme_title_priority(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that rdfs:label takes priority over skos:prefLabel for scheme title."""
    result = await import_service.preview(
        project.id, SCHEME_TITLE_PRIORITY_TTL, "test.ttl"
    )

    assert result.valid is True
    assert result.schemes[0].title == "RDFS Label Title"


@pytest.mark.asyncio
async def test_preview_orphan_concept_single_scheme(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that orphan concepts are assigned to single scheme in file."""
    result = await import_service.preview(
        project.id, ORPHAN_CONCEPT_SINGLE_SCHEME_TTL, "test.ttl"
    )

    assert result.valid is True
    assert result.schemes[0].concepts_count == 2  # Both concepts assigned


@pytest.mark.asyncio
async def test_preview_orphan_concept_multi_scheme_warning(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that orphan concepts generate warning when multiple schemes exist."""
    result = await import_service.preview(
        project.id, ORPHAN_CONCEPT_MULTI_SCHEME_TTL, "test.ttl"
    )

    assert result.valid is True
    # Orphan should be skipped, only 1 concept in Scheme A
    scheme_a = next(s for s in result.schemes if s.title == "Scheme A")
    assert scheme_a.concepts_count == 1
    # Should have warning about skipped orphan
    all_warnings = [w for s in result.schemes for w in s.warnings]
    assert any("OrphanConcept" in w or "orphan" in w.lower() for w in all_warnings) or len(result.errors) > 0


@pytest.mark.asyncio
async def test_preview_top_concept_of(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that skos:topConceptOf is used for scheme membership."""
    result = await import_service.preview(
        project.id, TOP_CONCEPT_OF_TTL, "test.ttl"
    )

    assert result.valid is True
    assert result.schemes[0].concepts_count == 1


# Error cases


@pytest.mark.asyncio
async def test_preview_invalid_rdf(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that invalid RDF raises an error."""
    with pytest.raises(InvalidRDFError):
        await import_service.preview(project.id, INVALID_RDF, "test.ttl")


@pytest.mark.asyncio
async def test_preview_unsupported_format(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that unsupported file extension raises an error."""
    with pytest.raises(InvalidRDFError):
        await import_service.preview(project.id, SIMPLE_SCHEME_TTL, "test.xyz")


@pytest.mark.asyncio
async def test_preview_scheme_uri_conflict(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Test that existing scheme with same URI is skipped in preview."""
    # Create existing scheme with same URI
    existing = ConceptScheme(
        project_id=project.id,
        title="Existing Scheme",
        uri="http://example.org/TestScheme",
    )
    db_session.add(existing)
    await db_session.flush()

    result = await import_service.preview(project.id, SIMPLE_SCHEME_TTL, "test.ttl")
    # Scheme should be skipped (already exists), so 0 new schemes
    assert len(result.schemes) == 0


# Execute tests


@pytest.mark.asyncio
async def test_execute_simple_scheme(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Test executing import of a simple scheme."""
    result = await import_service.execute(
        project.id, SIMPLE_SCHEME_TTL, "test.ttl"
    )

    assert len(result.schemes_created) == 1
    assert result.schemes_created[0].title == "Test Scheme"
    assert result.schemes_created[0].concepts_created == 2
    assert result.total_concepts_created == 2
    assert result.total_relationships_created == 1

    # Verify database
    from sqlalchemy import select
    from taxonomy_builder.models.concept import Concept

    schemes = (
        await db_session.execute(
            select(ConceptScheme).where(ConceptScheme.project_id == project.id)
        )
    ).scalars().all()
    assert len(schemes) == 1
    assert schemes[0].title == "Test Scheme"

    concepts = (
        await db_session.execute(
            select(Concept).where(Concept.scheme_id == schemes[0].id)
        )
    ).scalars().all()
    assert len(concepts) == 2


@pytest.mark.asyncio
async def test_execute_multiple_schemes(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Test executing import of multiple schemes."""
    result = await import_service.execute(
        project.id, MULTI_SCHEME_TTL, "test.ttl"
    )

    assert len(result.schemes_created) == 2
    assert result.total_concepts_created == 3

    # Verify database
    from sqlalchemy import select

    schemes = (
        await db_session.execute(
            select(ConceptScheme).where(ConceptScheme.project_id == project.id)
        )
    ).scalars().all()
    assert len(schemes) == 2


@pytest.mark.asyncio
async def test_execute_scheme_title_conflict_auto_rename(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Test that title conflict results in auto-rename."""
    # Create existing scheme with same title
    existing = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/different-uri",
    )
    db_session.add(existing)
    await db_session.flush()

    result = await import_service.execute(
        project.id, SIMPLE_SCHEME_TTL, "test.ttl"
    )

    # Should succeed with renamed title
    assert len(result.schemes_created) == 1
    assert result.schemes_created[0].title == "Test Scheme (2)"


@pytest.mark.asyncio
async def test_execute_creates_broader_relationships(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Test that broader relationships are created."""
    result = await import_service.execute(
        project.id, SIMPLE_SCHEME_TTL, "test.ttl"
    )

    assert result.total_relationships_created == 1

    # Verify in database
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from taxonomy_builder.models.concept import Concept

    scheme_id = result.schemes_created[0].id
    concepts = (
        await db_session.execute(
            select(Concept)
            .where(Concept.scheme_id == scheme_id)
            .options(selectinload(Concept.broader))
        )
    ).scalars().all()

    concept_with_broader = next(
        (c for c in concepts if c.pref_label == "Second Concept"), None
    )
    assert concept_with_broader is not None
    assert len(concept_with_broader.broader) == 1
    assert concept_with_broader.broader[0].pref_label == "First Concept"


@pytest.mark.asyncio
async def test_execute_alt_labels(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Test that alt labels are imported."""
    result = await import_service.execute(
        project.id, ALT_LABELS_TTL, "test.ttl"
    )

    # Verify in database
    from sqlalchemy import select
    from taxonomy_builder.models.concept import Concept

    scheme_id = result.schemes_created[0].id
    concepts = (
        await db_session.execute(
            select(Concept).where(Concept.scheme_id == scheme_id)
        )
    ).scalars().all()

    dogs = next((c for c in concepts if c.pref_label == "Dogs"), None)
    assert dogs is not None
    assert set(dogs.alt_labels) == {"Canines", "Domestic dogs"}


@pytest.mark.asyncio
async def test_execute_extracts_identifier_from_uri(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Test that concept identifiers are extracted from URIs."""
    result = await import_service.execute(
        project.id, SIMPLE_SCHEME_TTL, "test.ttl"
    )

    from sqlalchemy import select
    from taxonomy_builder.models.concept import Concept

    scheme_id = result.schemes_created[0].id
    concepts = (
        await db_session.execute(
            select(Concept).where(Concept.scheme_id == scheme_id)
        )
    ).scalars().all()

    concept1 = next((c for c in concepts if c.pref_label == "First Concept"), None)
    assert concept1 is not None
    assert concept1.identifier == "Concept1"


# Format detection tests


@pytest.mark.asyncio
async def test_format_detection_turtle(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that .ttl extension is detected as Turtle."""
    result = await import_service.preview(
        project.id, SIMPLE_SCHEME_TTL, "test.ttl"
    )
    assert result.valid is True


@pytest.mark.asyncio
async def test_format_detection_rdf_xml(
    import_service: SKOSImportService, project: Project
) -> None:
    """Test that .rdf extension is detected as RDF/XML."""
    rdf_xml = b"""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:skos="http://www.w3.org/2004/02/skos/core#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
  <skos:ConceptScheme rdf:about="http://example.org/TestScheme">
    <rdfs:label>Test Scheme</rdfs:label>
  </skos:ConceptScheme>
</rdf:RDF>
"""
    result = await import_service.preview(project.id, rdf_xml, "test.rdf")
    assert result.valid is True
    assert result.schemes[0].title == "Test Scheme"


# --- Domain-less property tests ---


PROPERTY_WITHOUT_DOMAIN_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:domainlessProp a owl:DatatypeProperty ;
    rdfs:label "Domainless Property" ;
    rdfs:range xsd:string .

ex:domainedProp a owl:DatatypeProperty ;
    rdfs:label "Domained Property" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:integer .
"""


@pytest.mark.asyncio
async def test_execute_property_without_domain_skipped_with_warning(
    db_session: AsyncSession, import_service: SKOSImportService, project: Project
) -> None:
    """Property without rdfs:domain is skipped; domained property is imported."""
    from sqlalchemy import select
    from taxonomy_builder.models.property import Property

    result = await import_service.execute(
        project.id, PROPERTY_WITHOUT_DOMAIN_TTL, "test.ttl"
    )

    # Only the domained property is created
    assert len(result.properties_created) == 1
    assert result.properties_created[0].identifier == "domainedProp"

    # Warning about the skipped one
    assert any(
        "domainlessProp" in w and "skipped" in w
        for w in result.warnings
    )

    # Verify only one property in DB
    props = (
        await db_session.execute(
            select(Property).where(Property.project_id == project.id)
        )
    ).scalars().all()
    assert len(props) == 1


@pytest.mark.asyncio
async def test_preview_property_without_domain_skipped_with_warning(
    import_service: SKOSImportService, project: Project
) -> None:
    """Preview skips domain-less properties and warns."""
    result = await import_service.preview(
        project.id, PROPERTY_WITHOUT_DOMAIN_TTL, "test.ttl"
    )

    assert result.properties_count == 1
    assert result.properties[0].identifier == "domainedProp"
    assert any(
        "domainlessProp" in w and "skipped" in w
        for w in result.warnings
    )


# --- Dual-typed property deduplication tests ---


DUAL_TYPED_PROPERTY_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:dualProp a owl:ObjectProperty, owl:DatatypeProperty ;
    rdfs:label "Dual Typed Property" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:string .
"""


@pytest.mark.asyncio
async def test_preview_dual_typed_property_not_duplicated(
    import_service: SKOSImportService, project: Project
) -> None:
    """A dual-typed property appears once; XSD range -> datatype."""
    result = await import_service.preview(
        project.id, DUAL_TYPED_PROPERTY_TTL, "test.ttl"
    )

    assert result.properties_count == 1
    assert result.properties[0].property_type == "datatype"


DUAL_TYPED_OBJECT_RANGE_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:Outcome a owl:Class ;
    rdfs:label "Outcome" .

ex:dualProp a owl:ObjectProperty, owl:DatatypeProperty ;
    rdfs:label "Dual With Object Range" ;
    rdfs:domain ex:Finding ;
    rdfs:range ex:Outcome .
"""


@pytest.mark.asyncio
async def test_dual_typed_with_object_range_becomes_object(
    import_service: SKOSImportService, project: Project
) -> None:
    """Dual-typed property with non-XSD range -> treated as object."""
    result = await import_service.preview(
        project.id, DUAL_TYPED_OBJECT_RANGE_TTL, "test.ttl"
    )

    assert result.properties_count == 1
    assert result.properties[0].property_type == "object"
