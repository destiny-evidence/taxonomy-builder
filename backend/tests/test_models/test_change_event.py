"""Tests for the ChangeEvent model."""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    ChangeEventFactory,
    ConceptSchemeFactory,
    ProjectFactory,
    flush,
)


@pytest.mark.asyncio
async def test_create_change_event(db_session: AsyncSession) -> None:
    """Test creating a change event with required fields."""
    scheme = await flush(db_session, ConceptSchemeFactory.create())

    event = await flush(
        db_session,
        ChangeEventFactory.create(
            scheme_id=scheme.id,
            after_state={"pref_label": "Dogs", "definition": "A domestic animal"},
        ),
    )

    assert event.id is not None
    assert isinstance(event.id, UUID)
    assert event.scheme_id == scheme.id
    assert event.entity_type == "concept"
    assert event.entity_id is not None
    assert event.action == "create"
    assert event.before_state is None
    assert event.after_state == {"pref_label": "Dogs", "definition": "A domestic animal"}
    assert event.timestamp is not None
    assert event.user_id is None


@pytest.mark.asyncio
async def test_change_event_id_is_uuidv7(db_session: AsyncSession) -> None:
    """Test that change event IDs are UUIDv7."""
    scheme = await flush(db_session, ConceptSchemeFactory.create())

    event = await flush(
        db_session,
        ChangeEventFactory.create(
            scheme_id=scheme.id,
            after_state={"pref_label": "Test"},
        ),
    )

    assert event.id.version == 7


@pytest.mark.asyncio
async def test_change_event_update_with_before_after(db_session: AsyncSession) -> None:
    """Test creating an update event with before and after states."""
    scheme = await flush(db_session, ConceptSchemeFactory.create())

    event = await flush(
        db_session,
        ChangeEventFactory.create(
            scheme_id=scheme.id,
            action="update",
            before_state={"pref_label": "Dog", "definition": None},
            after_state={"pref_label": "Dogs", "definition": "A domestic animal"},
        ),
    )

    assert event.action == "update"
    assert event.before_state == {"pref_label": "Dog", "definition": None}
    assert event.after_state == {"pref_label": "Dogs", "definition": "A domestic animal"}


@pytest.mark.asyncio
async def test_change_event_delete_with_before_only(db_session: AsyncSession) -> None:
    """Test creating a delete event with only before state."""
    scheme = await flush(db_session, ConceptSchemeFactory.create())

    event = await flush(
        db_session,
        ChangeEventFactory.create(
            scheme_id=scheme.id,
            action="delete",
            before_state={"pref_label": "Dogs", "definition": "A domestic animal"},
            after_state=None,
        ),
    )

    assert event.action == "delete"
    assert event.before_state == {"pref_label": "Dogs", "definition": "A domestic animal"}
    assert event.after_state is None


@pytest.mark.asyncio
async def test_change_event_with_project_id_and_no_scheme(db_session: AsyncSession) -> None:
    """Test creating a change event with project_id and no scheme_id.

    This supports tracking changes to project-level entities like properties.
    """
    project = await flush(db_session, ProjectFactory.create())

    event = await flush(
        db_session,
        ChangeEventFactory.create(
            project_id=project.id,
            entity_type="property",
            after_state={"identifier": "educationLevel", "label": "Education Level"},
        ),
    )

    assert event.id is not None
    assert event.project_id == project.id
    assert event.scheme_id is None
    assert event.entity_type == "property"
    assert event.action == "create"


@pytest.mark.asyncio
async def test_change_event_with_both_project_and_scheme(db_session: AsyncSession) -> None:
    """Test creating a change event with both project_id and scheme_id."""
    scheme = await flush(db_session, ConceptSchemeFactory.create())
    project = scheme.project

    event = await flush(
        db_session,
        ChangeEventFactory.create(
            project_id=project.id,
            scheme_id=scheme.id,
            after_state={"pref_label": "Test Concept"},
        ),
    )

    assert event.project_id == project.id
    assert event.scheme_id == scheme.id
