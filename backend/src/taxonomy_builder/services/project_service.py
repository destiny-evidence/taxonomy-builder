"""Project service for business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectUpdate


class ProjectNotFoundError(Exception):
    """Raised when a project is not found."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(f"Project with id '{project_id}' not found")


class ProjectNameExistsError(Exception):
    """Raised when a project name already exists."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Project with name '{name}' already exists")


class ProjectService:
    """Service for managing projects."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
        )
        self.db.add(project)
        try:
            await self.db.flush()
            await self.db.refresh(project)
        except IntegrityError:
            await self.db.rollback()
            raise ProjectNameExistsError(project_in.name)
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

        if project_in.name is not None:
            project.name = project_in.name
        if "description" in project_in.model_fields_set:
            project.description = project_in.description
        if "namespace" in project_in.model_fields_set:
            project.namespace = project_in.namespace

        try:
            await self.db.flush()
            await self.db.refresh(project)
        except IntegrityError:
            await self.db.rollback()
            raise ProjectNameExistsError(project_in.name or "")
        return project

    async def delete_project(self, project_id: UUID) -> None:
        """Delete a project."""
        project = await self.get_project(project_id)
        await self.db.delete(project)
        await self.db.flush()
