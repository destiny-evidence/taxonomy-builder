"""Tests for the ChangeTracker service."""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.services.change_tracker import ChangeTracker


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
        title="Test Scheme",
        uri="http://example.org/concepts",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.mark.asyncio
async def test_record_creates_change_event(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test that record() creates a ChangeEvent."""
    tracker = ChangeTracker(db_session)
    entity_id = uuid4()

    event = await tracker.record(
        project_id=project.id,
        entity_type="concept",
        entity_id=entity_id,
        action="create",
        before=None,
        after={"pref_label": "Dogs"},
        scheme_id=scheme.id,
    )

    assert event.id is not None
    assert event.project_id == project.id
    assert event.scheme_id == scheme.id
    assert event.entity_type == "concept"
    assert event.entity_id == entity_id
    assert event.action == "create"
    assert event.before_state is None
    assert event.after_state == {"pref_label": "Dogs"}

    # Verify it was persisted
    result = await db_session.execute(
        select(ChangeEvent).where(ChangeEvent.id == event.id)
    )
    persisted = result.scalar_one()
    assert persisted.action == "create"


@pytest.mark.asyncio
async def test_serialize_concept_captures_all_fields(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that serialize_concept() captures all concept fields."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Dogs",
        identifier="dogs",
        definition="A domestic animal",
        scope_note="Use for domestic dogs",
        alt_labels=["Canines", "Pups"],
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    tracker = ChangeTracker(db_session)
    serialized = tracker.serialize_concept(concept)

    assert serialized["id"] == str(concept.id)
    assert serialized["pref_label"] == "Dogs"
    assert serialized["identifier"] == "dogs"
    assert serialized["definition"] == "A domestic animal"
    assert serialized["scope_note"] == "Use for domestic dogs"
    assert serialized["alt_labels"] == ["Canines", "Pups"]


@pytest.mark.asyncio
async def test_serialize_scheme_captures_all_fields(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that serialize_scheme() captures all scheme fields."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Animals",
        description="A taxonomy of animals",
        uri="http://example.org/animals",
        publisher="Example Org",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    tracker = ChangeTracker(db_session)
    serialized = tracker.serialize_scheme(scheme)

    assert serialized["id"] == str(scheme.id)
    assert serialized["title"] == "Animals"
    assert serialized["description"] == "A taxonomy of animals"
    assert serialized["uri"] == "http://example.org/animals"
    assert serialized["publisher"] == "Example Org"


@pytest.mark.asyncio
async def test_serialize_broader_includes_labels(db_session: AsyncSession) -> None:
    """Test that serialize_broader() includes concept labels."""
    tracker = ChangeTracker(db_session)
    concept_id = uuid4()
    broader_id = uuid4()

    serialized = tracker.serialize_broader(
        concept_id=concept_id,
        broader_concept_id=broader_id,
        concept_label="Mammals",
        broader_label="Animals",
    )

    assert serialized["concept_id"] == str(concept_id)
    assert serialized["broader_concept_id"] == str(broader_id)
    assert serialized["concept_label"] == "Mammals"
    assert serialized["broader_label"] == "Animals"


@pytest.mark.asyncio
async def test_serialize_related_includes_labels(db_session: AsyncSession) -> None:
    """Test that serialize_related() includes concept labels."""
    tracker = ChangeTracker(db_session)
    concept_id = uuid4()
    related_id = uuid4()

    serialized = tracker.serialize_related(
        concept_id=concept_id,
        related_concept_id=related_id,
        concept_label="Dogs",
        related_label="Cats",
    )

    assert serialized["concept_id"] == str(concept_id)
    assert serialized["related_concept_id"] == str(related_id)
    assert serialized["concept_label"] == "Dogs"
    assert serialized["related_label"] == "Cats"


@pytest.mark.asyncio
async def test_record_with_project_id_and_no_scheme(
    db_session: AsyncSession, project: Project
) -> None:
    """Test recording a project-level event without scheme_id."""
    tracker = ChangeTracker(db_session)
    entity_id = uuid4()

    event = await tracker.record(
        project_id=project.id,
        scheme_id=None,
        entity_type="property",
        entity_id=entity_id,
        action="create",
        before=None,
        after={"identifier": "educationLevel", "label": "Education Level"},
    )

    assert event.project_id == project.id
    assert event.scheme_id is None
    assert event.entity_type == "property"
    assert event.action == "create"


@pytest.mark.asyncio
async def test_record_with_both_project_and_scheme(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test recording an event with both project_id and scheme_id."""
    tracker = ChangeTracker(db_session)
    entity_id = uuid4()

    event = await tracker.record(
        project_id=project.id,
        scheme_id=scheme.id,
        entity_type="concept",
        entity_id=entity_id,
        action="create",
        before=None,
        after={"pref_label": "Test Concept"},
    )

    assert event.project_id == project.id
    assert event.scheme_id == scheme.id
