"""PropertyService for managing properties."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.property import Property
from taxonomy_builder.schemas.property import PropertyCreate, PropertyUpdate
from taxonomy_builder.services.change_tracker import ChangeTracker
from taxonomy_builder.services.concept_scheme_service import (
    ConceptSchemeService,
    SchemeNotFoundError,
)
from taxonomy_builder.services.core_ontology_service import get_core_ontology
from taxonomy_builder.services.project_service import ProjectService


class PropertyNotFoundError(Exception):
    """Raised when a property is not found."""

    def __init__(self, property_id: UUID) -> None:
        self.property_id = property_id
        super().__init__(f"Property '{property_id}' not found")


class DomainClassNotFoundError(Exception):
    """Raised when a domain class is not found in the core ontology."""

    def __init__(self, domain_class: str) -> None:
        self.domain_class = domain_class
        super().__init__(f"Domain class '{domain_class}' not found in core ontology")


class InvalidRangeError(Exception):
    """Raised when range specification is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SchemeNotInProjectError(Exception):
    """Raised when a scheme does not belong to the project."""

    def __init__(self, scheme_id: UUID, project_id: UUID) -> None:
        self.scheme_id = scheme_id
        self.project_id = project_id
        super().__init__(
            f"Concept scheme '{scheme_id}' does not belong to project '{project_id}'"
        )


class PropertyIdentifierExistsError(Exception):
    """Raised when a property identifier already exists in the project."""

    def __init__(self, identifier: str, project_id: UUID) -> None:
        self.identifier = identifier
        self.project_id = project_id
        super().__init__(
            f"Property with identifier '{identifier}' already exists in project"
        )


class PropertyService:
    """Service for managing properties."""

    def __init__(
        self,
        db: AsyncSession,
        project_service: ProjectService,
        scheme_service: ConceptSchemeService,
        user_id: UUID | None = None,
    ) -> None:
        self.db = db
        self._project_service = project_service
        self._scheme_service = scheme_service
        self._tracker = ChangeTracker(db, user_id)

    def _validate_domain_class(self, domain_class: str) -> None:
        """Validate that domain_class exists in the core ontology."""
        ontology = get_core_ontology()
        valid_classes = {c.uri for c in ontology.classes}
        if domain_class not in valid_classes:
            raise DomainClassNotFoundError(domain_class)

    async def _validate_range(
        self,
        project_id: UUID,
        range_scheme_id: UUID | None,
        range_datatype: str | None,
        range_class: str | None,
    ) -> None:
        """Validate that exactly one of the three range fields is provided."""
        provided = sum(
            v is not None for v in (range_scheme_id, range_datatype, range_class)
        )
        if provided != 1:
            raise InvalidRangeError(
                "Exactly one of range_scheme_id, range_datatype, or range_class "
                "must be provided"
            )

        # Validate scheme belongs to project
        if range_scheme_id is not None:
            try:
                scheme = await self._scheme_service.get_scheme(range_scheme_id)
            except SchemeNotFoundError:
                raise SchemeNotInProjectError(range_scheme_id, project_id)
            if scheme.project_id != project_id:
                raise SchemeNotInProjectError(range_scheme_id, project_id)

    def _serialize_property(self, prop: Property) -> dict:
        """Serialize a property for change tracking.

        Manual serialization because Property is a SQLAlchemy model (no model_dump).
        Intentionally excludes timestamps and relationships — only domain fields.
        """
        return {
            "id": str(prop.id),
            "identifier": prop.identifier,
            "label": prop.label,
            "description": prop.description,
            "domain_class": prop.domain_class,
            "range_scheme_id": str(prop.range_scheme_id) if prop.range_scheme_id else None,
            "range_datatype": prop.range_datatype,
            "range_class": prop.range_class,
            "cardinality": prop.cardinality,
            "required": prop.required,
        }

    async def create_property(
        self, project_id: UUID, property_in: PropertyCreate
    ) -> Property:
        """Create a new property in a project.

        Args:
            project_id: The project to create the property in
            property_in: The property data

        Returns:
            The created Property

        Raises:
            ProjectNotFoundError: If the project doesn't exist
            DomainClassNotFoundError: If the domain class is not in the core ontology
            InvalidRangeError: If range specification is invalid
            SchemeNotInProjectError: If the scheme doesn't belong to the project
            PropertyIdentifierExistsError: If the identifier already exists
        """
        # Verify project exists
        await self._project_service.get_project(project_id)

        # Validate domain class
        self._validate_domain_class(property_in.domain_class)

        # Validate range
        await self._validate_range(
            project_id,
            property_in.range_scheme_id,
            property_in.range_datatype,
            property_in.range_class,
        )

        # Create property
        prop = Property(
            project_id=project_id,
            identifier=property_in.identifier,
            label=property_in.label,
            description=property_in.description,
            domain_class=property_in.domain_class,
            range_scheme_id=property_in.range_scheme_id,
            range_datatype=property_in.range_datatype,
            range_class=property_in.range_class,
            cardinality=property_in.cardinality,
            required=property_in.required,
        )
        self.db.add(prop)

        try:
            await self.db.flush()
            await self.db.refresh(prop)
        except IntegrityError:
            await self.db.rollback()
            raise PropertyIdentifierExistsError(property_in.identifier, project_id)

        # Record change event
        await self._tracker.record(
            project_id=project_id,
            entity_type="property",
            entity_id=prop.id,
            action="create",
            before=None,
            after=self._serialize_property(prop),
        )

        return prop

    async def list_properties(self, project_id: UUID) -> list[Property]:
        """List all properties for a project.

        Args:
            project_id: The project ID

        Returns:
            List of properties in the project

        Raises:
            ProjectNotFoundError: If the project doesn't exist
        """
        await self._project_service.get_project(project_id)
        result = await self.db.execute(
            select(Property).where(Property.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_property(self, property_id: UUID) -> Property | None:
        """Get a property by ID.

        Args:
            property_id: The property ID

        Returns:
            The property or None if not found
        """
        result = await self.db.execute(
            select(Property).where(Property.id == property_id)
        )
        return result.scalar_one_or_none()

    async def update_property(
        self, property_id: UUID, property_in: PropertyUpdate
    ) -> Property | None:
        """Update a property.

        Args:
            property_id: The property ID
            property_in: The update data

        Returns:
            The updated property or None if not found

        Raises:
            InvalidRangeError: If range specification becomes invalid
            SchemeNotInProjectError: If scheme doesn't belong to the project
        """
        prop = await self.get_property(property_id)
        if prop is None:
            return None

        before = self._serialize_property(prop)

        # Determine what the new range values will be
        new_scheme_id = prop.range_scheme_id
        new_datatype = prop.range_datatype
        new_range_class = prop.range_class

        # Check if we're updating range fields
        update_data = property_in.model_dump(exclude_unset=True)
        if "range_scheme_id" in update_data:
            new_scheme_id = update_data["range_scheme_id"]
        if "range_datatype" in update_data:
            new_datatype = update_data["range_datatype"]
        if "range_class" in update_data:
            new_range_class = update_data["range_class"]

        # Validate range if any range field is being updated
        range_fields = {"range_scheme_id", "range_datatype", "range_class"}
        if range_fields & update_data.keys():
            await self._validate_range(
                prop.project_id, new_scheme_id, new_datatype, new_range_class
            )

        # Apply updates
        for key, value in update_data.items():
            setattr(prop, key, value)

        await self.db.flush()
        await self.db.refresh(prop)

        # Record change event
        await self._tracker.record(
            project_id=prop.project_id,
            entity_type="property",
            entity_id=prop.id,
            action="update",
            before=before,
            after=self._serialize_property(prop),
        )

        return prop

    async def delete_property(self, property_id: UUID) -> bool:
        """Delete a property.

        Args:
            property_id: The property ID

        Returns:
            True if deleted, False if not found
        """
        prop = await self.get_property(property_id)
        if prop is None:
            return False

        before = self._serialize_property(prop)
        project_id = prop.project_id
        entity_id = prop.id

        await self.db.delete(prop)
        await self.db.flush()

        # Record change event
        await self._tracker.record(
            project_id=project_id,
            entity_type="property",
            entity_id=entity_id,
            action="delete",
            before=before,
            after=None,
        )

        return True
