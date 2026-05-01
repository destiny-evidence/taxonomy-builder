"""Dependency injection for MCP tool handlers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp.dependencies import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.database import db_manager
from taxonomy_builder.models.user import User
from taxonomy_builder.services.auth_service import AuthService
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.feedback_service import FeedbackService
from taxonomy_builder.services.history_service import HistoryService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_export_service import SKOSExportService

# Set by the stdio CLI at startup. HTTP tools resolve the user per-request.
_stdio_user: User | None = None


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Provide a database session."""
    async with db_manager.session() as session:
        yield session


async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Resolve the current user from stdio preset or HTTP access token."""
    if _stdio_user is not None:
        return _stdio_user

    from fastmcp.server.dependencies import get_access_token

    token = get_access_token()
    if token is None:
        raise RuntimeError("No authenticated user available")

    auth_service = AuthService(session)
    return await auth_service.get_or_create_user(token.claims)


def get_project_service(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ProjectService:
    return ProjectService(session, user_id=user.id)


def get_concept_service(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ConceptService:
    return ConceptService(session, user_id=user.id)


def get_scheme_service(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ConceptSchemeService:
    return ConceptSchemeService(session, user_id=user.id)


def get_feedback_service(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> FeedbackService:
    return FeedbackService(
        session,
        user_id=user.id,
        user_display_name=user.display_name,
        user_email=user.email,
    )


def get_history_service(
    session: AsyncSession = Depends(get_db_session),
) -> HistoryService:
    return HistoryService(session)


def get_export_service(
    session: AsyncSession = Depends(get_db_session),
) -> SKOSExportService:
    return SKOSExportService(session)
