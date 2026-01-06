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
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that record() creates a ChangeEvent."""
    tracker = ChangeTracker(db_session)
    entity_id = uuid4()

    event = await tracker.record(
        scheme_id=scheme.id,
        entity_type="concept",
        entity_id=entity_id,
        action="create",
        before=None,
        after={"pref_label": "Dogs"},
    )

    assert event.id is not None
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
        version="1.0",
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
    assert serialized["version"] == "1.0"
