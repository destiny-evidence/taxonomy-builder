"""Tests for the ChangeEvent model."""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project


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
async def test_create_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test creating a change event with required fields."""
    from uuid import uuid4

    entity_id = uuid4()

    event = ChangeEvent(
        scheme_id=scheme.id,
        entity_type="concept",
        entity_id=entity_id,
        action="create",
        after_state={"pref_label": "Dogs", "definition": "A domestic animal"},
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)

    assert event.id is not None
    assert isinstance(event.id, UUID)
    assert event.scheme_id == scheme.id
    assert event.entity_type == "concept"
    assert event.entity_id == entity_id
    assert event.action == "create"
    assert event.before_state is None
    assert event.after_state == {"pref_label": "Dogs", "definition": "A domestic animal"}
    assert event.timestamp is not None
    assert event.user_id is None


@pytest.mark.asyncio
async def test_change_event_id_is_uuidv7(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that change event IDs are UUIDv7."""
    from uuid import uuid4

    event = ChangeEvent(
        scheme_id=scheme.id,
        entity_type="concept",
        entity_id=uuid4(),
        action="create",
        after_state={"pref_label": "Test"},
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)

    assert event.id.version == 7


@pytest.mark.asyncio
async def test_change_event_update_with_before_after(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test creating an update event with before and after states."""
    from uuid import uuid4

    entity_id = uuid4()

    event = ChangeEvent(
        scheme_id=scheme.id,
        entity_type="concept",
        entity_id=entity_id,
        action="update",
        before_state={"pref_label": "Dog", "definition": None},
        after_state={"pref_label": "Dogs", "definition": "A domestic animal"},
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)

    assert event.action == "update"
    assert event.before_state == {"pref_label": "Dog", "definition": None}
    assert event.after_state == {"pref_label": "Dogs", "definition": "A domestic animal"}


@pytest.mark.asyncio
async def test_change_event_delete_with_before_only(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test creating a delete event with only before state."""
    from uuid import uuid4

    entity_id = uuid4()

    event = ChangeEvent(
        scheme_id=scheme.id,
        entity_type="concept",
        entity_id=entity_id,
        action="delete",
        before_state={"pref_label": "Dogs", "definition": "A domestic animal"},
        after_state=None,
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)

    assert event.action == "delete"
    assert event.before_state == {"pref_label": "Dogs", "definition": "A domestic animal"}
    assert event.after_state is None


@pytest.mark.asyncio
async def test_change_event_with_project_id_and_no_scheme(
    db_session: AsyncSession, project: Project
) -> None:
    """Test creating a change event with project_id and no scheme_id.

    This supports tracking changes to project-level entities like properties.
    """
    from uuid import uuid4

    entity_id = uuid4()

    event = ChangeEvent(
        project_id=project.id,
        scheme_id=None,
        entity_type="property",
        entity_id=entity_id,
        action="create",
        after_state={"identifier": "educationLevel", "label": "Education Level"},
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)

    assert event.id is not None
    assert event.project_id == project.id
    assert event.scheme_id is None
    assert event.entity_type == "property"
    assert event.action == "create"


@pytest.mark.asyncio
async def test_change_event_with_both_project_and_scheme(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test creating a change event with both project_id and scheme_id."""
    from uuid import uuid4

    entity_id = uuid4()

    event = ChangeEvent(
        project_id=project.id,
        scheme_id=scheme.id,
        entity_type="concept",
        entity_id=entity_id,
        action="create",
        after_state={"pref_label": "Test Concept"},
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)

    assert event.project_id == project.id
    assert event.scheme_id == scheme.id
