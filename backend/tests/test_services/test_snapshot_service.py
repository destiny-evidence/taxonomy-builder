"""Tests for the SnapshotService."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from taxonomy_builder.models.concept_related import ConceptRelated
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.core_ontology_service import CoreOntology, OntologyClass
from taxonomy_builder.services.project_service import ProjectNotFoundError, ProjectService
from taxonomy_builder.services.snapshot_service import SnapshotService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Snapshot Test Project", namespace="http://example.org/vocab")
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
        publisher="Test Publisher",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


def service(db_session: AsyncSession) -> SnapshotService:
    """Create a SnapshotService instance.

    Clears the identity map so the service loads fresh from DB,
    simulating a production request with a clean session.
    """
    db_session.expunge_all()
    return SnapshotService(
        db_session,
        project_service=ProjectService(db_session),
        concept_service=ConceptService(db_session),
    )


@pytest.mark.asyncio
async def test_empty_project(db_session: AsyncSession, project: Project) -> None:
    """Test snapshot of a project with no schemes, properties, or classes."""
    snapshot = await service(db_session).build_snapshot(project.id)

    assert snapshot == {
        "concept_schemes": [],
        "properties": [],
        "classes": [],
    }


@pytest.mark.asyncio
async def test_project_not_found(db_session: AsyncSession) -> None:
    """Test that a non-existent project raises ProjectNotFoundError."""
    with pytest.raises(ProjectNotFoundError):
        await service(db_session).build_snapshot(uuid4())


@pytest.mark.asyncio
async def test_scheme_with_no_concepts(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test snapshot includes scheme with empty concepts list."""
    snapshot = await service(db_session).build_snapshot(project.id)

    assert len(snapshot["concept_schemes"]) == 1
    s = snapshot["concept_schemes"][0]
    assert s["id"] == str(scheme.id)
    assert s["title"] == "Test Taxonomy"
    assert s["description"] == "A test taxonomy"
    assert s["uri"] == "http://example.org/taxonomy"
    assert s["concepts"] == []


@pytest.mark.asyncio
async def test_scheme_with_concepts(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test snapshot captures all concept fields correctly with UUIDs as strings."""
    concept = Concept(
        scheme_id=scheme.id,
        identifier="finding-1",
        pref_label="Finding One",
        definition="The first finding",
        scope_note="Use carefully",
        alt_labels=["Alt 1", "Alt 2"],
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    snapshot = await service(db_session).build_snapshot(project.id)

    concepts = snapshot["concept_schemes"][0]["concepts"]
    assert len(concepts) == 1
    c = concepts[0]
    assert c["id"] == str(concept.id)
    assert c["identifier"] == "finding-1"
    assert c["pref_label"] == "Finding One"
    assert c["definition"] == "The first finding"
    assert c["scope_note"] == "Use carefully"
    assert c["alt_labels"] == ["Alt 1", "Alt 2"]
    assert c["broader_ids"] == []
    assert c["related_ids"] == []


@pytest.mark.asyncio
async def test_concept_uris(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test that concept URIs are computed from scheme URI + identifier."""
    with_id = Concept(
        scheme_id=scheme.id, identifier="concept-1", pref_label="With Identifier"
    )
    without_id = Concept(scheme_id=scheme.id, pref_label="Without Identifier")
    db_session.add_all([with_id, without_id])
    await db_session.flush()

    snapshot = await service(db_session).build_snapshot(project.id)

    concepts = {c["pref_label"]: c for c in snapshot["concept_schemes"][0]["concepts"]}
    assert concepts["With Identifier"]["uri"] == "http://example.org/taxonomy/concept-1"
    assert concepts["Without Identifier"]["uri"] is None


@pytest.mark.asyncio
async def test_broader_relationships(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test that broader_ids are populated correctly."""
    parent = Concept(scheme_id=scheme.id, pref_label="Parent")
    child = Concept(scheme_id=scheme.id, pref_label="Child")
    db_session.add_all([parent, child])
    await db_session.flush()
    await db_session.refresh(parent)
    await db_session.refresh(child)

    rel = ConceptBroader(concept_id=child.id, broader_concept_id=parent.id)
    db_session.add(rel)
    await db_session.flush()

    snapshot = await service(db_session).build_snapshot(project.id)

    concepts = {c["pref_label"]: c for c in snapshot["concept_schemes"][0]["concepts"]}
    assert concepts["Child"]["broader_ids"] == [str(parent.id)]
    assert concepts["Parent"]["broader_ids"] == []


@pytest.mark.asyncio
async def test_related_relationships(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test that related_ids are populated correctly in both directions."""
    concept_a = Concept(scheme_id=scheme.id, pref_label="Concept A")
    concept_b = Concept(scheme_id=scheme.id, pref_label="Concept B")
    db_session.add_all([concept_a, concept_b])
    await db_session.flush()
    await db_session.refresh(concept_a)
    await db_session.refresh(concept_b)

    # Store with smaller UUID first (per ConceptRelated convention)
    id1, id2 = sorted([concept_a.id, concept_b.id])
    rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
    db_session.add(rel)
    await db_session.flush()

    snapshot = await service(db_session).build_snapshot(project.id)

    concepts = {c["pref_label"]: c for c in snapshot["concept_schemes"][0]["concepts"]}
    # Both directions should appear
    assert str(concept_b.id) in concepts["Concept A"]["related_ids"]
    assert str(concept_a.id) in concepts["Concept B"]["related_ids"]


@pytest.mark.asyncio
async def test_properties(db_session: AsyncSession, project: Project) -> None:
    """Test that properties are captured with all fields and computed URI."""
    scheme = ConceptScheme(
        project_id=project.id, title="Range Scheme", uri="http://example.org/range"
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    prop = Property(
        project_id=project.id,
        identifier="testProp",
        label="Test Property",
        description="A test property",
        domain_class="http://example.org/vocab/Finding",
        range_scheme_id=scheme.id,
        cardinality="single",
        required=True,
    )
    db_session.add(prop)
    await db_session.flush()
    await db_session.refresh(prop)

    snapshot = await service(db_session).build_snapshot(project.id)

    assert len(snapshot["properties"]) == 1
    p = snapshot["properties"][0]
    assert p["id"] == str(prop.id)
    assert p["identifier"] == "testProp"
    assert p["uri"] == "http://example.org/vocab/testProp"
    assert p["label"] == "Test Property"
    assert p["description"] == "A test property"
    assert p["domain_class"] == "http://example.org/vocab/Finding"
    assert p["range_scheme_id"] == str(scheme.id)
    assert p["range_datatype"] is None
    assert p["cardinality"] == "single"
    assert p["required"] is True


@pytest.mark.asyncio
async def test_classes_filtered_by_properties(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that only ontology classes referenced by properties are included."""
    prop = Property(
        project_id=project.id,
        identifier="prop1",
        label="Prop 1",
        domain_class="http://example.org/vocab/Finding",
        range_datatype="xsd:string",
        cardinality="single",
        required=False,
    )
    db_session.add(prop)
    await db_session.flush()

    mock_ontology = CoreOntology(
        classes=[
            OntologyClass(
                uri="http://example.org/vocab/Finding",
                label="Finding",
                comment="A finding",
            ),
            OntologyClass(
                uri="http://example.org/vocab/Study",
                label="Study",
                comment="A study",
            ),
        ]
    )

    with patch(
        "taxonomy_builder.services.snapshot_service.get_core_ontology",
        return_value=mock_ontology,
    ):
        snapshot = await service(db_session).build_snapshot(project.id)

    assert len(snapshot["classes"]) == 1
    cls = snapshot["classes"][0]
    assert cls["uri"] == "http://example.org/vocab/Finding"
    assert cls["label"] == "Finding"
    assert cls["description"] == "A finding"


@pytest.mark.asyncio
async def test_full_integration(
    db_session: AsyncSession, project: Project
) -> None:
    """Test a complete snapshot with multiple schemes, concepts, relationships, and properties."""
    # Create two schemes
    scheme1 = ConceptScheme(
        project_id=project.id,
        title="Scheme One",
        uri="http://example.org/scheme1",
    )
    scheme2 = ConceptScheme(
        project_id=project.id,
        title="Scheme Two",
        uri="http://example.org/scheme2",
    )
    db_session.add_all([scheme1, scheme2])
    await db_session.flush()
    await db_session.refresh(scheme1)
    await db_session.refresh(scheme2)

    # Create concepts with hierarchy in scheme1
    parent = Concept(
        scheme_id=scheme1.id, identifier="parent", pref_label="Parent Concept"
    )
    child = Concept(
        scheme_id=scheme1.id, identifier="child", pref_label="Child Concept"
    )
    db_session.add_all([parent, child])
    await db_session.flush()
    await db_session.refresh(parent)
    await db_session.refresh(child)

    broader_rel = ConceptBroader(concept_id=child.id, broader_concept_id=parent.id)
    db_session.add(broader_rel)

    # Create concept in scheme2
    standalone = Concept(
        scheme_id=scheme2.id, identifier="standalone", pref_label="Standalone"
    )
    db_session.add(standalone)
    await db_session.flush()

    # Create property
    prop = Property(
        project_id=project.id,
        identifier="topic",
        label="Topic",
        domain_class="http://example.org/vocab/Finding",
        range_scheme_id=scheme1.id,
        cardinality="multiple",
        required=False,
    )
    db_session.add(prop)
    await db_session.flush()

    mock_ontology = CoreOntology(
        classes=[
            OntologyClass(
                uri="http://example.org/vocab/Finding",
                label="Finding",
                comment="A finding",
            ),
        ]
    )

    with patch(
        "taxonomy_builder.services.snapshot_service.get_core_ontology",
        return_value=mock_ontology,
    ):
        snapshot = await service(db_session).build_snapshot(project.id)

    # Two schemes
    assert len(snapshot["concept_schemes"]) == 2
    schemes_by_title = {s["title"]: s for s in snapshot["concept_schemes"]}

    # Scheme1 has 2 concepts with hierarchy
    s1 = schemes_by_title["Scheme One"]
    assert len(s1["concepts"]) == 2
    concepts_by_label = {c["pref_label"]: c for c in s1["concepts"]}
    assert concepts_by_label["Child Concept"]["broader_ids"] == [str(parent.id)]

    # Scheme2 has 1 concept
    s2 = schemes_by_title["Scheme Two"]
    assert len(s2["concepts"]) == 1
    assert s2["concepts"][0]["pref_label"] == "Standalone"

    # One property
    assert len(snapshot["properties"]) == 1
    assert snapshot["properties"][0]["identifier"] == "topic"

    # One class
    assert len(snapshot["classes"]) == 1
    assert snapshot["classes"][0]["uri"] == "http://example.org/vocab/Finding"
