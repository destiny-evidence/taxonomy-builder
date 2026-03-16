"""Project service for business logic."""

import re
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.project import ProjectCreate, ProjectUpdate
from taxonomy_builder.services.change_tracker import ChangeTracker


class ProjectNotFoundError(Exception):
    """Raised when a project is not found."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(f"Project with id '{project_id}' not found")


class VersionNotFoundError(Exception):
    """Raised when a published version is not found."""

    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(f"Published version '{version}' not found")


class ProjectNameExistsError(Exception):
    """Raised when a project name already exists."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Project with name '{name}' already exists")


class PrefixLockedError(Exception):
    """Raised when identifier_prefix cannot be changed because concepts already have identifiers."""

    def __init__(self) -> None:
        super().__init__(
            "Cannot change identifier_prefix: concepts with assigned identifiers exist"
        )


IDENTIFIER_WIDTH = 6
MAX_COUNTER = 10**IDENTIFIER_WIDTH - 1


class IdentifierAllocationError(Exception):
    """Raised when an identifier cannot be allocated for a project."""

    def __init__(self, project_name: str, reason: str) -> None:
        self.project_name = project_name
        super().__init__(
            f"Cannot allocate identifier for project '{project_name}': {reason}"
        )


class ProjectService:
    """Service for managing projects."""

    def __init__(self, db: AsyncSession, user_id: UUID | None = None) -> None:
        self.db = db
        self._tracker = ChangeTracker(db, user_id)

    def _serialize_project(self, project: Project) -> dict:
        """Serialize a project for change tracking.

        Manual serialization because Project is a SQLAlchemy model (no model_dump).
        Intentionally excludes timestamps and relationships — only domain fields.
        """
        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "namespace": project.namespace,
            "identifier_prefix": project.identifier_prefix,
            "identifier_counter": project.identifier_counter,
        }

    async def _check_prefix_mutable(self, project_id: UUID) -> None:
        """Raise PrefixLockedError if any concept exists in the project."""
        result = await self.db.execute(
            select(Concept.id)
            .join(ConceptScheme, Concept.scheme_id == ConceptScheme.id)
            .where(ConceptScheme.project_id == project_id)
            .limit(1)
        )
        if result.scalar_one_or_none() is not None:
            raise PrefixLockedError()

    async def allocate_identifier(self, project_id: UUID) -> str:
        """Allocate the next sequential identifier for a project.

        Atomically increments counter and returns identifier string like "EVD000001".

        Raises:
            ProjectNotFoundError: If project does not exist.
            IdentifierAllocationError: If no prefix configured or counter at max.
        """
        project = await self.get_project(project_id)

        if project.identifier_prefix is None:
            raise IdentifierAllocationError(project.name, "no identifier prefix configured")

        result = await self.db.execute(
            update(Project)
            .where(
                Project.id == project_id,
                Project.identifier_counter < MAX_COUNTER,
            )
            .values(identifier_counter=Project.identifier_counter + 1)
            .returning(Project.identifier_prefix, Project.identifier_counter)
        )
        row = result.one_or_none()

        if row is not None:
            prefix, counter = row[0], row[1]
            return f"{prefix}{counter:0{IDENTIFIER_WIDTH}d}"

        raise IdentifierAllocationError(
            project.name, f"counter at maximum ({MAX_COUNTER})"
        )

    async def reconcile_identifier_counter(
        self, project_id: UUID, identifiers: list[str]
    ) -> None:
        """Advance project counter past the highest imported identifier matching the prefix.

        Monotonic: never moves counter backward.
        Skips identifiers above MAX_COUNTER to prevent bricking future allocations.
        """
        project = await self.get_project(project_id)
        if project.identifier_prefix is None:
            return

        prefix = project.identifier_prefix
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        max_found = 0
        for ident in identifiers:
            m = pattern.match(ident)
            if m:
                value = int(m.group(1))
                if value <= MAX_COUNTER:
                    max_found = max(max_found, value)

        if max_found > 0:
            await self.db.execute(
                update(Project)
                .where(Project.id == project_id, Project.identifier_counter < max_found)
                .values(identifier_counter=max_found)
            )

    async def list_projects(self) -> list[Project]:
        """List all projects ordered by name."""
        result = await self.db.execute(select(Project).order_by(Project.name))
        return list(result.scalars().all())

    async def create_project(self, project_in: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(
            name=project_in.name,
            description=project_in.description,
            namespace=project_in.namespace,
            identifier_prefix=project_in.identifier_prefix,
        )
        self.db.add(project)
        try:
            await self.db.flush()
            await self.db.refresh(project)
        except IntegrityError:
            await self.db.rollback()
            raise ProjectNameExistsError(project_in.name)

        await self._tracker.record(
            project_id=project.id,
            entity_type="project",
            entity_id=project.id,
            action="create",
            before=None,
            after=self._serialize_project(project),
        )
        return project

    async def get_project(self, project_id: UUID) -> Project:
        """Get a project by ID."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def update_project(self, project_id: UUID, project_in: ProjectUpdate) -> Project:
        """Update an existing project."""
        project = await self.get_project(project_id)
        before = self._serialize_project(project)

        if project_in.name is not None:
            project.name = project_in.name
        if "description" in project_in.model_fields_set:
            project.description = project_in.description
        if "namespace" in project_in.model_fields_set:
            project.namespace = project_in.namespace
        if "identifier_prefix" in project_in.model_fields_set:
            if project_in.identifier_prefix != project.identifier_prefix:
                await self._check_prefix_mutable(project_id)
            project.identifier_prefix = project_in.identifier_prefix

        try:
            await self.db.flush()
            await self.db.refresh(project)
        except IntegrityError:
            await self.db.rollback()
            raise ProjectNameExistsError(project_in.name or "")

        await self._tracker.record(
            project_id=project.id,
            entity_type="project",
            entity_id=project.id,
            action="update",
            before=before,
            after=self._serialize_project(project),
        )
        return project

    async def delete_project(self, project_id: UUID) -> None:
        """Delete a project."""
        project = await self.get_project(project_id)
        before = self._serialize_project(project)

        await self._tracker.record(
            project_id=project.id,
            entity_type="project",
            entity_id=project.id,
            action="delete",
            before=before,
            after=None,
        )

        await self.db.delete(project)
        await self.db.flush()

    async def get_project_version(
        self, project_id: UUID, version: str
    ) -> PublishedVersion:
        """Get a published version by version string, scoped to a project."""
        result = await self.db.execute(
            select(PublishedVersion).where(
                PublishedVersion.version == version,
                PublishedVersion.project_id == project_id,
            )
        )
        published = result.scalar_one_or_none()
        if published is None:
            raise VersionNotFoundError(version)
        return published
