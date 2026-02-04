"""ConceptScheme service for business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept_scheme import ConceptSchemeCreate, ConceptSchemeUpdate
from taxonomy_builder.services.change_tracker import ChangeTracker


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


class SchemeReferencedByPropertyError(Exception):
    """Raised when attempting to delete a scheme that is referenced by properties."""

    def __init__(self, scheme_id: UUID) -> None:
        self.scheme_id = scheme_id
        super().__init__(
            f"Concept scheme '{scheme_id}' cannot be deleted because it is referenced by one or more properties"
        )


class ConceptSchemeService:
    """Service for managing concept schemes."""

    def __init__(self, db: AsyncSession, user_id: UUID | None = None) -> None:
        self.db = db
        self._tracker = ChangeTracker(db, user_id)

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

        # Record change event
        await self._tracker.record(
            project_id=project_id,
            entity_type="concept_scheme",
            entity_id=scheme.id,
            action="create",
            before=None,
            after=self._tracker.serialize_scheme(scheme),
            scheme_id=scheme.id,
        )

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

        # Capture before state
        before_state = self._tracker.serialize_scheme(scheme)

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

        # Record change event
        await self._tracker.record(
            project_id=project_id,
            entity_type="concept_scheme",
            entity_id=scheme.id,
            action="update",
            before=before_state,
            after=self._tracker.serialize_scheme(scheme),
            scheme_id=scheme.id,
        )

        return scheme

    async def delete_scheme(self, scheme_id: UUID) -> None:
        """Delete a concept scheme.

        Raises:
            SchemeNotFoundError: If the scheme doesn't exist
            SchemeReferencedByPropertyError: If the scheme is referenced by properties
        """
        scheme = await self.get_scheme(scheme_id)
        project_id = scheme.project_id

        # Capture before state before deletion
        before_state = self._tracker.serialize_scheme(scheme)

        # Record change event BEFORE deleting scheme (FK constraint)
        await self._tracker.record(
            project_id=project_id,
            entity_type="concept_scheme",
            entity_id=scheme_id,
            action="delete",
            before=before_state,
            after=None,
            scheme_id=scheme_id,
        )

        await self.db.delete(scheme)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise SchemeReferencedByPropertyError(scheme_id)
