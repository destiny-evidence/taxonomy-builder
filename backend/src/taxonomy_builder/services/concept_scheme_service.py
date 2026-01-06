"""ConceptScheme service for business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept_scheme import ConceptSchemeCreate, ConceptSchemeUpdate


class SchemeNotFoundError(Exception):
    """Raised when a concept scheme is not found."""

    def __init__(self, scheme_id: UUID) -> None:
        self.scheme_id = scheme_id
        super().__init__(f"Concept scheme with id '{scheme_id}' not found")


class SchemeTitleExistsError(Exception):
    """Raised when a scheme title already exists in the project."""

    def __init__(self, title: str, project_id: UUID) -> None:
        self.title = title
        self.project_id = project_id
        super().__init__(f"Concept scheme with title '{title}' already exists in project")


class ProjectNotFoundError(Exception):
    """Raised when a project is not found."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(f"Project with id '{project_id}' not found")


class ConceptSchemeService:
    """Service for managing concept schemes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_project(self, project_id: UUID) -> Project:
        """Get a project by ID or raise ProjectNotFoundError."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def list_schemes_for_project(self, project_id: UUID) -> list[ConceptScheme]:
        """List all concept schemes for a project, ordered by title."""
        # Verify project exists
        await self._get_project(project_id)

        result = await self.db.execute(
            select(ConceptScheme)
            .where(ConceptScheme.project_id == project_id)
            .order_by(ConceptScheme.title)
        )
        return list(result.scalars().all())

    async def create_scheme(
        self, project_id: UUID, scheme_in: ConceptSchemeCreate
    ) -> ConceptScheme:
        """Create a new concept scheme in a project."""
        # Verify project exists
        await self._get_project(project_id)

        scheme = ConceptScheme(
            project_id=project_id,
            title=scheme_in.title,
            description=scheme_in.description,
            uri=scheme_in.uri,
            publisher=scheme_in.publisher,
            version=scheme_in.version,
        )
        self.db.add(scheme)
        try:
            await self.db.flush()
            await self.db.refresh(scheme)
        except IntegrityError:
            await self.db.rollback()
            raise SchemeTitleExistsError(scheme_in.title, project_id)
        return scheme

    async def get_scheme(self, scheme_id: UUID) -> ConceptScheme:
        """Get a concept scheme by ID."""
        result = await self.db.execute(
            select(ConceptScheme).where(ConceptScheme.id == scheme_id)
        )
        scheme = result.scalar_one_or_none()
        if scheme is None:
            raise SchemeNotFoundError(scheme_id)
        return scheme

    async def update_scheme(
        self, scheme_id: UUID, scheme_in: ConceptSchemeUpdate
    ) -> ConceptScheme:
        """Update an existing concept scheme."""
        scheme = await self.get_scheme(scheme_id)
        project_id = scheme.project_id  # Capture before potential rollback

        if scheme_in.title is not None:
            scheme.title = scheme_in.title
        if scheme_in.description is not None:
            scheme.description = scheme_in.description
        if scheme_in.uri is not None:
            scheme.uri = scheme_in.uri
        if scheme_in.publisher is not None:
            scheme.publisher = scheme_in.publisher
        if scheme_in.version is not None:
            scheme.version = scheme_in.version

        try:
            await self.db.flush()
            await self.db.refresh(scheme)
        except IntegrityError:
            await self.db.rollback()
            raise SchemeTitleExistsError(scheme_in.title or "", project_id)
        return scheme

    async def delete_scheme(self, scheme_id: UUID) -> None:
        """Delete a concept scheme."""
        scheme = await self.get_scheme(scheme_id)
        await self.db.delete(scheme)
        await self.db.flush()
