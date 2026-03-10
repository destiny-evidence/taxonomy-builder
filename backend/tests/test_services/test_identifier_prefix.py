"""Tests for identifier prefix and counter on Project."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project


@pytest.fixture
async def project_with_prefix(db_session: AsyncSession) -> Project:
    """Create a project with identifier prefix configured."""
    project = Project(name="Prefixed Project", identifier_prefix="EVD")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


async def test_project_has_identifier_prefix_column(
    project_with_prefix: Project,
) -> None:
    assert project_with_prefix.identifier_prefix == "EVD"


async def test_project_identifier_counter_defaults_to_zero(
    project_with_prefix: Project,
) -> None:
    assert project_with_prefix.identifier_counter == 0


async def test_project_prefix_nullable(db_session: AsyncSession) -> None:
    project = Project(name="No Prefix Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    assert project.identifier_prefix is None
    assert project.identifier_counter == 0
