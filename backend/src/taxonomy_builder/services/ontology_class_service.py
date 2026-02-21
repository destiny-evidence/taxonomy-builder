"""OntologyClassService for managing ontology classes."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.schemas.ontology_class import OntologyClassCreate, OntologyClassUpdate
from taxonomy_builder.services.change_tracker import ChangeTracker
from taxonomy_builder.services.project_service import ProjectService


class OntologyClassNotFoundError(Exception):
    """Raised when an ontology class is not found."""

    def __init__(self, ontology_class_id: UUID) -> None:
        self.ontology_class_id = ontology_class_id
        super().__init__(f"Ontology class '{ontology_class_id}' not found")


class OntologyClassIdentifierExistsError(Exception):
    """Raised when an ontology class identifier already exists in the project."""

    def __init__(self, identifier: str, project_id: UUID) -> None:
        self.identifier = identifier
        self.project_id = project_id
        super().__init__(
            f"Ontology class with identifier '{identifier}' already exists in project"
        )


class OntologyClassService:
    """Service for managing ontology classes."""

    def __init__(
        self,
        db: AsyncSession,
        project_service: ProjectService,
        user_id: UUID | None = None,
    ) -> None:
        self.db = db
        self._project_service = project_service
        self._tracker = ChangeTracker(db, user_id)

    def _serialize_ontology_class(self, ontology_class: OntologyClass) -> dict:
        """Serialize an ontology class for change tracking."""
        return {
            "id": str(ontology_class.id),
            "identifier": ontology_class.identifier,
            "label": ontology_class.label,
            "description": ontology_class.description,
            "scope_note": ontology_class.scope_note,
        }

    async def create_ontology_class(
        self, project_id: UUID, ontology_class_in: OntologyClassCreate
    ) -> OntologyClass:
        """Create a new ontology class in a project.

        Args:
            project_id: The project to create the ontology class in
            ontology_class_in: The ontology class data

        Returns:
            The created OntologyClass

        Raises:
            ProjectNotFoundError: If the project doesn't exist
            OntologyClassIdentifierExistsError: If the identifier already exists
        """
        project = await self._project_service.get_project(project_id)

        if ontology_class_in.uri:
            uri = ontology_class_in.uri
        elif project.namespace:
            uri = project.namespace.rstrip("/") + "/" + ontology_class_in.identifier
        else:
            raise ValueError(
                "Project namespace required to create ontology classes without explicit URI"
            )

        ontology_class = OntologyClass(
            project_id=project_id,
            identifier=ontology_class_in.identifier,
            label=ontology_class_in.label,
            description=ontology_class_in.description,
            scope_note=ontology_class_in.scope_note,
            uri=uri,
        )
        self.db.add(ontology_class)

        try:
            await self.db.flush()
            await self.db.refresh(ontology_class)
        except IntegrityError:
            await self.db.rollback()
            raise OntologyClassIdentifierExistsError(
                ontology_class_in.identifier, project_id
            )

        await self._tracker.record(
            project_id=project_id,
            entity_type="ontology_class",
            entity_id=ontology_class.id,
            action="create",
            before=None,
            after=self._serialize_ontology_class(ontology_class),
        )

        return ontology_class

    async def list_ontology_classes(self, project_id: UUID) -> list[OntologyClass]:
        """List all ontology classes for a project.

        Args:
            project_id: The project ID

        Returns:
            List of ontology classes in the project

        Raises:
            ProjectNotFoundError: If the project doesn't exist
        """
        await self._project_service.get_project(project_id)
        result = await self.db.execute(
            select(OntologyClass).where(OntologyClass.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_ontology_class(self, ontology_class_id: UUID) -> OntologyClass | None:
        """Get an ontology class by ID.

        Args:
            ontology_class_id: The ontology class ID

        Returns:
            The ontology class or None if not found
        """
        result = await self.db.execute(
            select(OntologyClass).where(OntologyClass.id == ontology_class_id)
        )
        return result.scalar_one_or_none()

    async def update_ontology_class(
        self, ontology_class_id: UUID, ontology_class_in: OntologyClassUpdate
    ) -> OntologyClass | None:
        """Update an ontology class.

        Args:
            ontology_class_id: The ontology class ID
            ontology_class_in: The update data

        Returns:
            The updated ontology class or None if not found

        Raises:
            OntologyClassIdentifierExistsError: If the new identifier already exists
        """
        ontology_class = await self.get_ontology_class(ontology_class_id)
        if ontology_class is None:
            return None

        before = self._serialize_ontology_class(ontology_class)

        update_data = ontology_class_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ontology_class, key, value)

        try:
            await self.db.flush()
            await self.db.refresh(ontology_class)
        except IntegrityError:
            await self.db.rollback()
            identifier = update_data.get("identifier", ontology_class.identifier)
            raise OntologyClassIdentifierExistsError(
                identifier, ontology_class.project_id
            )

        await self._tracker.record(
            project_id=ontology_class.project_id,
            entity_type="ontology_class",
            entity_id=ontology_class.id,
            action="update",
            before=before,
            after=self._serialize_ontology_class(ontology_class),
        )

        return ontology_class

    async def delete_ontology_class(self, ontology_class_id: UUID) -> bool:
        """Delete an ontology class.

        Args:
            ontology_class_id: The ontology class ID

        Returns:
            True if deleted, False if not found
        """
        ontology_class = await self.get_ontology_class(ontology_class_id)
        if ontology_class is None:
            return False

        before = self._serialize_ontology_class(ontology_class)
        project_id = ontology_class.project_id
        entity_id = ontology_class.id

        await self.db.delete(ontology_class)
        await self.db.flush()

        await self._tracker.record(
            project_id=project_id,
            entity_type="ontology_class",
            entity_id=entity_id,
            action="delete",
            before=before,
            after=None,
        )

        return True
