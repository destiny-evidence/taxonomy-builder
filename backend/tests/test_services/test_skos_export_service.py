"""Tests for SKOS Export Service."""

from uuid import uuid4

import pytest
from rdflib import Graph
from rdflib.namespace import DCTERMS, RDF, SKOS
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from taxonomy_builder.models.concept_related import ConceptRelated
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.snapshot import (
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotScheme,
    SnapshotVocabulary,
)
from taxonomy_builder.services.skos_export_service import SchemeNotFoundError, SKOSExportService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Taxonomy",
        description="A test taxonomy",
        uri="http://example.org/taxonomy",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.fixture
def export_service(db_session: AsyncSession) -> SKOSExportService:
    """Create export service instance."""
    return SKOSExportService(db_session)


# Empty scheme tests


@pytest.mark.asyncio
async def test_export_empty_scheme(
    export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test exporting a scheme with no concepts."""
    result = await export_service.export_scheme(scheme.id, "ttl")

    # Parse the result as RDF
    g = Graph()
    g.parse(data=result, format="turtle")

    # Should have ConceptScheme
    scheme_uri = next(g.subjects(RDF.type, SKOS.ConceptScheme))
    assert str(scheme_uri) == "http://example.org/taxonomy"

    # Should have title
    title = g.value(scheme_uri, DCTERMS.title)
    assert str(title) == "Test Taxonomy"

    # Should have no concepts
    concepts = list(g.subjects(RDF.type, SKOS.Concept))
    assert len(concepts) == 0


@pytest.mark.asyncio
async def test_export_scheme_metadata(
    export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test that scheme metadata is exported correctly."""
    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    scheme_uri = next(g.subjects(RDF.type, SKOS.ConceptScheme))

    # Check all metadata fields
    assert str(g.value(scheme_uri, DCTERMS.title)) == "Test Taxonomy"
    assert str(g.value(scheme_uri, DCTERMS.description)) == "A test taxonomy"


# Single concept tests


@pytest.mark.asyncio
async def test_export_single_concept(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test exporting a scheme with a single concept."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Animals",
        identifier="animals",
        definition="Living organisms that are not plants",
        scope_note="Use for general animal topics",
    )
    db_session.add(concept)
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    # Should have one concept
    concepts = list(g.subjects(RDF.type, SKOS.Concept))
    assert len(concepts) == 1

    concept_uri = concepts[0]
    assert str(concept_uri) == "http://example.org/taxonomy/animals"

    # Check concept properties
    assert str(g.value(concept_uri, SKOS.prefLabel)) == "Animals"
    assert str(g.value(concept_uri, SKOS.definition)) == "Living organisms that are not plants"
    assert str(g.value(concept_uri, SKOS.scopeNote)) == "Use for general animal topics"

    # Check inScheme relationship
    in_scheme = g.value(concept_uri, SKOS.inScheme)
    assert str(in_scheme) == "http://example.org/taxonomy"

    # Check hasTopConcept (concept with no broader is a top concept)
    scheme_uri = next(g.subjects(RDF.type, SKOS.ConceptScheme))
    top_concepts = list(g.objects(scheme_uri, SKOS.hasTopConcept))
    assert len(top_concepts) == 1
    assert str(top_concepts[0]) == "http://example.org/taxonomy/animals"


# Hierarchy tests


@pytest.mark.asyncio
async def test_export_with_hierarchy(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test exporting a scheme with broader/narrower relationships."""
    # Create parent concept
    animals = Concept(
        scheme_id=scheme.id,
        pref_label="Animals",
        identifier="animals",
    )
    db_session.add(animals)
    await db_session.flush()

    # Create child concept
    mammals = Concept(
        scheme_id=scheme.id,
        pref_label="Mammals",
        identifier="mammals",
    )
    db_session.add(mammals)
    await db_session.flush()

    # Create broader relationship
    rel = ConceptBroader(concept_id=mammals.id, broader_concept_id=animals.id)
    db_session.add(rel)
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    animals_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "animals" in str(uri)
    )
    mammals_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "mammals" in str(uri)
    )

    # Check broader relationship
    broader = g.value(mammals_uri, SKOS.broader)
    assert str(broader) == str(animals_uri)

    # Check narrower relationship (inverse)
    narrower = list(g.objects(animals_uri, SKOS.narrower))
    assert len(narrower) == 1
    assert str(narrower[0]) == str(mammals_uri)

    # Only animals should be a top concept
    scheme_uri = next(g.subjects(RDF.type, SKOS.ConceptScheme))
    top_concepts = list(g.objects(scheme_uri, SKOS.hasTopConcept))
    assert len(top_concepts) == 1
    assert str(top_concepts[0]) == str(animals_uri)


@pytest.mark.asyncio
async def test_export_polyhierarchy(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test exporting a concept with multiple broader concepts."""
    # Create two parent concepts
    mammals = Concept(scheme_id=scheme.id, pref_label="Mammals", identifier="mammals")
    pets = Concept(scheme_id=scheme.id, pref_label="Pets", identifier="pets")
    db_session.add_all([mammals, pets])
    await db_session.flush()

    # Create child with two parents
    dogs = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="dogs")
    db_session.add(dogs)
    await db_session.flush()

    # Create broader relationships
    rel1 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    rel2 = ConceptBroader(concept_id=dogs.id, broader_concept_id=pets.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    dogs_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "dogs" in str(uri)
    )

    # Dogs should have two broader concepts
    broader_list = list(g.objects(dogs_uri, SKOS.broader))
    assert len(broader_list) == 2


# Format tests


@pytest.mark.asyncio
async def test_export_turtle_format(
    export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test export in Turtle format."""
    result = await export_service.export_scheme(scheme.id, "ttl")

    # Should be valid Turtle
    g = Graph()
    g.parse(data=result, format="turtle")
    assert len(g) > 0

    # Should contain @prefix declarations
    assert "@prefix" in result


@pytest.mark.asyncio
async def test_export_rdf_xml_format(
    export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test export in RDF/XML format."""
    result = await export_service.export_scheme(scheme.id, "xml")

    # Should be valid RDF/XML
    g = Graph()
    g.parse(data=result, format="xml")
    assert len(g) > 0

    # Should be XML
    assert result.strip().startswith("<?xml") or result.strip().startswith("<rdf:RDF")


@pytest.mark.asyncio
async def test_export_jsonld_format(
    export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test export in JSON-LD format."""
    result = await export_service.export_scheme(scheme.id, "json-ld")

    # Should be valid JSON-LD
    g = Graph()
    g.parse(data=result, format="json-ld")
    assert len(g) > 0

    # Should be JSON
    import json

    parsed = json.loads(result)
    assert isinstance(parsed, (dict, list))


# Error tests


@pytest.mark.asyncio
async def test_export_scheme_not_found(export_service: SKOSExportService) -> None:
    """Test exporting a non-existent scheme raises error."""
    with pytest.raises(SchemeNotFoundError):
        await export_service.export_scheme(uuid4(), "ttl")


# Edge cases


@pytest.mark.asyncio
async def test_export_concept_without_identifier(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test exporting a concept without an identifier uses UUID in URI."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Unnamed Concept",
        # No identifier set
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    concepts = list(g.subjects(RDF.type, SKOS.Concept))
    assert len(concepts) == 1

    # URI should contain the concept ID
    concept_uri = str(concepts[0])
    assert str(concept.id) in concept_uri


@pytest.mark.asyncio
async def test_export_scheme_without_uri(
    db_session: AsyncSession, project: Project
) -> None:
    """Test exporting a scheme without a URI generates a default."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="No URI Scheme",
        # No URI set
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    service = SKOSExportService(db_session)
    result = await service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    scheme_uri = next(g.subjects(RDF.type, SKOS.ConceptScheme))
    # Should have a generated URI
    assert str(scheme_uri).startswith("http://")
    assert str(scheme.id) in str(scheme_uri)


# Alt labels tests


@pytest.mark.asyncio
async def test_export_concept_with_alt_labels(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test that alt labels are exported as skos:altLabel."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Dogs",
        identifier="dogs",
        alt_labels=["Canines", "Domestic dogs", "Canis familiaris"],
    )
    db_session.add(concept)
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    concept_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "dogs" in str(uri)
    )

    # Should have exactly 3 alt labels
    alt_labels = list(g.objects(concept_uri, SKOS.altLabel))
    assert len(alt_labels) == 3

    alt_label_values = {str(label) for label in alt_labels}
    assert alt_label_values == {"Canines", "Domestic dogs", "Canis familiaris"}


@pytest.mark.asyncio
async def test_export_concept_without_alt_labels(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test that concept without alt labels exports correctly."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Animals",
        identifier="animals",
        # No alt_labels
    )
    db_session.add(concept)
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    concept_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "animals" in str(uri)
    )

    # Should have no alt labels
    alt_labels = list(g.objects(concept_uri, SKOS.altLabel))
    assert len(alt_labels) == 0


@pytest.mark.asyncio
async def test_export_multiple_concepts_with_alt_labels(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test exporting multiple concepts with different alt labels."""
    concept1 = Concept(
        scheme_id=scheme.id,
        pref_label="Dogs",
        identifier="dogs",
        alt_labels=["Canines"],
    )
    concept2 = Concept(
        scheme_id=scheme.id,
        pref_label="Cats",
        identifier="cats",
        alt_labels=["Felines", "Kitties"],
    )
    db_session.add_all([concept1, concept2])
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    # Check dogs
    dogs_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "dogs" in str(uri)
    )
    dogs_alt = list(g.objects(dogs_uri, SKOS.altLabel))
    assert len(dogs_alt) == 1
    assert str(dogs_alt[0]) == "Canines"

    # Check cats
    cats_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "cats" in str(uri)
    )
    cats_alt = list(g.objects(cats_uri, SKOS.altLabel))
    assert len(cats_alt) == 2
    cats_alt_values = {str(label) for label in cats_alt}
    assert cats_alt_values == {"Felines", "Kitties"}


# Related relationship tests


@pytest.mark.asyncio
async def test_export_includes_related_relationship(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test that related relationships are exported as skos:related."""
    dogs = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="dogs")
    cats = Concept(scheme_id=scheme.id, pref_label="Cats", identifier="cats")
    db_session.add_all([dogs, cats])
    await db_session.flush()

    # Create related relationship (ordered: smaller ID first)
    id1, id2 = (dogs.id, cats.id) if dogs.id < cats.id else (cats.id, dogs.id)
    rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
    db_session.add(rel)
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    # Find dogs concept
    dogs_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "dogs" in str(uri)
    )

    # Dogs should have a related relationship
    related_list = list(g.objects(dogs_uri, SKOS.related))
    assert len(related_list) == 1
    assert "cats" in str(related_list[0])


@pytest.mark.asyncio
async def test_export_related_is_symmetric(
    db_session: AsyncSession, export_service: SKOSExportService, scheme: ConceptScheme
) -> None:
    """Test that related relationships are exported from both directions."""
    dogs = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="dogs")
    cats = Concept(scheme_id=scheme.id, pref_label="Cats", identifier="cats")
    db_session.add_all([dogs, cats])
    await db_session.flush()

    # Create related relationship (ordered: smaller ID first)
    id1, id2 = (dogs.id, cats.id) if dogs.id < cats.id else (cats.id, dogs.id)
    rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
    db_session.add(rel)
    await db_session.flush()

    result = await export_service.export_scheme(scheme.id, "ttl")

    g = Graph()
    g.parse(data=result, format="turtle")

    dogs_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "dogs" in str(uri)
    )
    cats_uri = next(
        uri for uri in g.subjects(RDF.type, SKOS.Concept) if "cats" in str(uri)
    )

    # Dogs should show related to cats
    dogs_related = list(g.objects(dogs_uri, SKOS.related))
    assert len(dogs_related) == 1
    assert str(dogs_related[0]) == str(cats_uri)

    # Cats should show related to dogs (symmetric)
    cats_related = list(g.objects(cats_uri, SKOS.related))
    assert len(cats_related) == 1
    assert str(cats_related[0]) == str(dogs_uri)


# Published version export tests


def _build_snapshot(project: Project, scheme: ConceptScheme) -> SnapshotVocabulary:
    """Build a SnapshotVocabulary from existing DB fixtures for test use."""
    animal_id = uuid4()
    mammal_id = uuid4()

    return SnapshotVocabulary(
        project=SnapshotProjectMetadata(
            id=project.id,
            name=project.name,
            description=project.description,
        ),
        concept_schemes=[
            SnapshotScheme(
                id=scheme.id,
                title=scheme.title,
                description=scheme.description,
                uri=scheme.uri,
                concepts=[
                    SnapshotConcept(
                        id=animal_id,
                        pref_label="Animals",
                        identifier="animals",
                        uri=f"{scheme.uri}/animals",
                        definition="Living organisms",
                        alt_labels=["Fauna"],
                    ),
                    SnapshotConcept(
                        id=mammal_id,
                        pref_label="Mammals",
                        identifier="mammals",
                        uri=f"{scheme.uri}/mammals",
                        broader_ids=[animal_id],
                    ),
                ],
            )
        ],
    )


@pytest.mark.asyncio
async def test_export_published_version_basic(
    db_session: AsyncSession,
    export_service: SKOSExportService,
    project: Project,
    scheme: ConceptScheme,
) -> None:
    """Test exporting a published version produces valid SKOS RDF."""
    snapshot = _build_snapshot(project, scheme)

    published = PublishedVersion(
        project_id=project.id,
        version="1.0",
        title="v1.0",
        snapshot=snapshot.model_dump(mode="json"),
    )
    db_session.add(published)
    await db_session.flush()
    await db_session.refresh(published)

    result = await export_service.export_published_version(published, "turtle")

    g = Graph()
    g.parse(data=result, format="turtle")

    # Should contain the scheme
    scheme_uri = next(g.subjects(RDF.type, SKOS.ConceptScheme))
    assert str(scheme_uri) == "http://example.org/taxonomy"
    assert str(g.value(scheme_uri, DCTERMS.title)) == "Test Taxonomy"

    # Should contain both concepts
    concepts = list(g.subjects(RDF.type, SKOS.Concept))
    assert len(concepts) == 2

    # Animals should be a top concept
    top_concepts = list(g.objects(scheme_uri, SKOS.hasTopConcept))
    assert len(top_concepts) == 1
    assert "animals" in str(top_concepts[0])

    # Mammals should have broader -> Animals
    mammals_uri = next(u for u in concepts if "mammals" in str(u))
    broader = g.value(mammals_uri, SKOS.broader)
    assert "animals" in str(broader)

    # Animals should have alt label
    animals_uri = next(u for u in concepts if "animals" in str(u))
    alt_labels = [str(label) for label in g.objects(animals_uri, SKOS.altLabel)]
    assert alt_labels == ["Fauna"]


@pytest.mark.asyncio
async def test_export_published_version_respects_format(
    db_session: AsyncSession,
    export_service: SKOSExportService,
    project: Project,
    scheme: ConceptScheme,
) -> None:
    """Test that export_published_version serializes in the requested format."""
    snapshot = _build_snapshot(project, scheme)

    published = PublishedVersion(
        project_id=project.id,
        version="1.0",
        title="v1.0",
        snapshot=snapshot.model_dump(mode="json"),
    )
    db_session.add(published)
    await db_session.flush()
    await db_session.refresh(published)

    result = await export_service.export_published_version(published, "xml")

    g = Graph()
    g.parse(data=result, format="xml")
    assert len(list(g.subjects(RDF.type, SKOS.Concept))) == 2


@pytest.mark.asyncio
async def test_export_published_version_multiple_schemes(
    db_session: AsyncSession,
    export_service: SKOSExportService,
    project: Project,
    scheme: ConceptScheme,
) -> None:
    """Test exporting a published version with multiple concept schemes."""
    concept_id = uuid4()
    snapshot = SnapshotVocabulary(
        project=SnapshotProjectMetadata(
            id=project.id,
            name=project.name,
        ),
        concept_schemes=[
            SnapshotScheme(
                id=scheme.id,
                title=scheme.title,
                uri=scheme.uri,
                concepts=[
                    SnapshotConcept(
                        id=uuid4(),
                        pref_label="Alpha",
                        uri=f"{scheme.uri}/alpha",
                    ),
                ],
            ),
            SnapshotScheme(
                id=uuid4(),
                title="Second Scheme",
                uri="http://example.org/second",
                concepts=[
                    SnapshotConcept(
                        id=concept_id,
                        pref_label="Beta",
                        uri="http://example.org/second/beta",
                    ),
                ],
            ),
        ],
    )

    published = PublishedVersion(
        project_id=project.id,
        version="2.0",
        title="v2.0",
        snapshot=snapshot.model_dump(mode="json"),
    )
    db_session.add(published)
    await db_session.flush()
    await db_session.refresh(published)

    result = await export_service.export_published_version(published, "turtle")

    g = Graph()
    g.parse(data=result, format="turtle")

    # Should have two concept schemes
    schemes = list(g.subjects(RDF.type, SKOS.ConceptScheme))
    assert len(schemes) == 2

    # Should have two concepts total
    concepts = list(g.subjects(RDF.type, SKOS.Concept))
    assert len(concepts) == 2