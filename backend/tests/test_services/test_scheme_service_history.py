"""Tests for change tracking in ConceptSchemeService."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept_scheme import ConceptSchemeCreate, ConceptSchemeUpdate
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.history_service import HistoryService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_create_scheme_creates_change_event(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that creating a scheme records a change event."""
    service = ConceptSchemeService(db_session)

    scheme = await service.create_scheme(
        project_id=project.id,
        scheme_in=ConceptSchemeCreate(
            title="Test Scheme",
            uri="http://example.org/scheme",
            description="A test scheme",
        ),
    )

    events = await HistoryService(db_session).get_scheme_history(scheme.id)
    event = next(e for e in events if e.action == "create")

    assert event.scheme_id == scheme.id
    assert event.before_state is None
    assert event.after_state is not None
    assert event.after_state["title"] == "Test Scheme"
    assert event.after_state["uri"] == "http://example.org/scheme"
    assert event.after_state["description"] == "A test scheme"


@pytest.mark.asyncio
async def test_update_scheme_creates_change_event_with_before_after(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that updating a scheme records before and after states."""
    service = ConceptSchemeService(db_session)

    # Create a scheme first
    scheme = await service.create_scheme(
        project_id=project.id,
        scheme_in=ConceptSchemeCreate(
            title="Original Title",
            uri="http://example.org/scheme",
        ),
    )
    scheme_id = scheme.id

    # Update the scheme
    await service.update_scheme(
        scheme_id=scheme_id,
        scheme_in=ConceptSchemeUpdate(
            title="Updated Title",
            description="A new description",
        ),
    )

    events = await HistoryService(db_session).get_scheme_history(scheme_id)
    event = next(e for e in events if e.action == "update")

    assert event.scheme_id == scheme_id
    assert event.before_state is not None
    assert event.after_state is not None
    assert event.before_state["title"] == "Original Title"
    assert event.before_state["description"] is None
    assert event.after_state["title"] == "Updated Title"
    assert event.after_state["description"] == "A new description"


@pytest.mark.asyncio
async def test_delete_scheme_creates_change_event(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that deleting a scheme records a change event with before state."""
    service = ConceptSchemeService(db_session)

    # Create a scheme first
    scheme = await service.create_scheme(
        project_id=project.id,
        scheme_in=ConceptSchemeCreate(
            title="Test Scheme",
            uri="http://example.org/scheme",
            description="A test scheme",
        ),
    )
    scheme_id = scheme.id

    # Delete the scheme
    await service.delete_scheme(scheme_id)

    # scheme_id FK is SET NULL on cascade, so query ChangeEvent directly
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept_scheme",
            ChangeEvent.entity_id == scheme_id,
            ChangeEvent.action == "delete",
        )
    )
    event = result.scalar_one()

    # scheme_id is set to NULL after scheme deletion (SET NULL cascade)
    assert event.scheme_id is None
    assert event.before_state is not None
    assert event.after_state is None
    assert event.before_state["title"] == "Test Scheme"
    assert event.before_state["uri"] == "http://example.org/scheme"
    assert event.before_state["description"] == "A test scheme"
    # The scheme id is captured in before_state
    assert event.before_state["id"] == str(scheme_id)
