"""Shared fixtures for service tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_import_service import SKOSImportService


@pytest.fixture
def import_service(db_session: AsyncSession) -> SKOSImportService:
    """Create import service instance."""
    return SKOSImportService(db_session, project_service=ProjectService(db_session))


@pytest.fixture
async def project_with_prefix(db_session: AsyncSession) -> Project:
    """Create a project with identifier_prefix set."""
    project = Project(
        name="Prefixed Project",
        namespace="https://example.org/vocab/",
        identifier_prefix="EVD",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project
