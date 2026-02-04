"""PropertyService for managing properties."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.schemas.property import PropertyCreate
from taxonomy_builder.services.change_tracker import ChangeTracker
from taxonomy_builder.services.core_ontology_service import get_core_ontology


class ProjectNotFoundError(Exception):
    """Raised when a project is not found."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(f"Project with id '{project_id}' not found")


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

    async def _get_scheme(self, scheme_id: UUID) -> ConceptScheme | None:
        """Get a scheme by ID or return None if not found."""
        result = await self.db.execute(
            select(ConceptScheme).where(ConceptScheme.id == scheme_id)
        )
        return result.scalar_one_or_none()

    def _validate_domain_class(self, domain_class: str) -> None:
        """Validate that domain_class exists in the core ontology."""
        ontology = get_core_ontology()
        valid_classes = {c.uri for c in ontology.classes}
        if domain_class not in valid_classes:
            raise DomainClassNotFoundError(domain_class)

    async def _validate_range(
        self, project_id: UUID, range_scheme_id: UUID | None, range_datatype: str | None
    ) -> None:
        """Validate that exactly one of range_scheme_id or range_datatype is provided."""
        has_scheme = range_scheme_id is not None
        has_datatype = range_datatype is not None

        if has_scheme and has_datatype:
            raise InvalidRangeError(
                "Exactly one of range_scheme_id or range_datatype must be provided, not both"
            )
        if not has_scheme and not has_datatype:
            raise InvalidRangeError(
                "Exactly one of range_scheme_id or range_datatype must be provided"
            )

        # Validate scheme belongs to project
        if has_scheme:
            scheme = await self._get_scheme(range_scheme_id)
            if scheme is None or scheme.project_id != project_id:
                raise SchemeNotInProjectError(range_scheme_id, project_id)

    def _serialize_property(self, prop: Property) -> dict:
        """Serialize a property for change tracking."""
        return {
            "id": str(prop.id),
            "identifier": prop.identifier,
            "label": prop.label,
            "description": prop.description,
            "domain_class": prop.domain_class,
            "range_scheme_id": str(prop.range_scheme_id) if prop.range_scheme_id else None,
            "range_datatype": prop.range_datatype,
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
        await self._get_project(project_id)

        # Validate domain class
        self._validate_domain_class(property_in.domain_class)

        # Validate range
        await self._validate_range(
            project_id, property_in.range_scheme_id, property_in.range_datatype
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
