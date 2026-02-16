"""Tests for change tracking in ProjectService."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.schemas.project import ProjectCreate, ProjectUpdate
from taxonomy_builder.services.history_service import HistoryService
from taxonomy_builder.services.project_service import ProjectService


@pytest.mark.asyncio
async def test_create_project_records_change_event(db_session: AsyncSession) -> None:
    """Creating a project records a 'create' change event."""
    service = ProjectService(db_session)

    project = await service.create_project(
        ProjectCreate(
            name="Test Project",
            description="A test project",
            namespace="http://example.org/ns/",
        )
    )

    events = await HistoryService(db_session).get_project_history(project.id)
    event = next(e for e in events if e.action == "create")

    assert event.project_id == project.id
    assert event.before_state is None
    assert event.after_state is not None
    assert event.after_state["name"] == "Test Project"
    assert event.after_state["namespace"] == "http://example.org/ns/"


@pytest.mark.asyncio
async def test_update_project_records_before_and_after(db_session: AsyncSession) -> None:
    """Updating a project records both before and after states."""
    service = ProjectService(db_session)

    project = await service.create_project(
        ProjectCreate(name="Original Name", description="Original desc")
    )

    await service.update_project(
        project.id,
        ProjectUpdate(name="Updated Name", description="Updated desc"),
    )

    events = await HistoryService(db_session).get_project_history(project.id)
    event = next(e for e in events if e.action == "update")

    assert event.before_state["name"] == "Original Name"
    assert event.after_state["name"] == "Updated Name"
    assert event.before_state["description"] == "Original desc"
    assert event.after_state["description"] == "Updated desc"


@pytest.mark.asyncio
async def test_update_namespace_records_change(db_session: AsyncSession) -> None:
    """Updating just the namespace records the change."""
    service = ProjectService(db_session)

    project = await service.create_project(
        ProjectCreate(name="NS Project", namespace="http://old.example.org/")
    )

    await service.update_project(
        project.id,
        ProjectUpdate(namespace="http://new.example.org/"),
    )

    events = await HistoryService(db_session).get_project_history(project.id)
    event = next(e for e in events if e.action == "update")

    assert event.before_state["namespace"] == "http://old.example.org/"
    assert event.after_state["namespace"] == "http://new.example.org/"


@pytest.mark.asyncio
async def test_delete_project_records_change_event(db_session: AsyncSession) -> None:
    """Deleting a project records a 'delete' event with before state."""
    service = ProjectService(db_session)

    project = await service.create_project(
        ProjectCreate(name="Doomed Project", namespace="http://example.org/doomed/")
    )
    project_id = project.id

    await service.delete_project(project_id)

    # project_id FK is SET NULL on cascade, so query ChangeEvent directly
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "project",
            ChangeEvent.entity_id == project_id,
            ChangeEvent.action == "delete",
        )
    )
    event = result.scalar_one()

    assert event.before_state is not None
    assert event.after_state is None
    assert event.before_state["name"] == "Doomed Project"
