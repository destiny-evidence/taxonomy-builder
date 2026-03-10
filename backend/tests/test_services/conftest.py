"""Shared fixtures for service tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.services.skos_import_service import SKOSImportService


@pytest.fixture
def import_service(db_session: AsyncSession) -> SKOSImportService:
    """Create import service instance."""
    return SKOSImportService(db_session)
