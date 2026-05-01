"""Fixtures for MCP tool tests — provide pre-built service instances."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.user import User
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.feedback_service import FeedbackService
from taxonomy_builder.services.history_service import HistoryService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_export_service import SKOSExportService


@pytest.fixture
def project_svc(db_session: AsyncSession, test_user: User) -> ProjectService:
    return ProjectService(db_session, user_id=test_user.id)


@pytest.fixture
def concept_svc(db_session: AsyncSession, test_user: User) -> ConceptService:
    return ConceptService(db_session, user_id=test_user.id)


@pytest.fixture
def scheme_svc(db_session: AsyncSession, test_user: User) -> ConceptSchemeService:
    return ConceptSchemeService(db_session, user_id=test_user.id)


@pytest.fixture
def feedback_svc(db_session: AsyncSession, test_user: User) -> FeedbackService:
    return FeedbackService(
        db_session,
        user_id=test_user.id,
        user_display_name=test_user.display_name,
        user_email=test_user.email,
    )


@pytest.fixture
def history_svc(db_session: AsyncSession) -> HistoryService:
    return HistoryService(db_session)


@pytest.fixture
def export_svc(db_session: AsyncSession) -> SKOSExportService:
    return SKOSExportService(db_session)
