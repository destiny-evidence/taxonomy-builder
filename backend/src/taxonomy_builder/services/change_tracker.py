"""Change tracker service for recording audit events."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme


class ChangeTracker:
    """Service for recording change events to the audit log."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record(
        self,
        scheme_id: UUID,
        entity_type: str,
        entity_id: UUID,
        action: str,
        before: dict | None,
        after: dict | None,
        user_id: UUID | None = None,
    ) -> ChangeEvent:
        """Record a change event.

        Args:
            scheme_id: The scheme this change belongs to
            entity_type: Type of entity changed (concept, concept_scheme, etc.)
            entity_id: ID of the entity that changed
            action: The action performed (create, update, delete)
            before: State before the change (None for create)
            after: State after the change (None for delete)
            user_id: Optional user who made the change

        Returns:
            The created ChangeEvent
        """
        event = ChangeEvent(
            scheme_id=scheme_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_state=before,
            after_state=after,
            user_id=user_id,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    def serialize_concept(self, concept: Concept) -> dict:
        """Serialize a concept to a dictionary for storage in change events.

        Args:
            concept: The concept to serialize

        Returns:
            Dictionary representation suitable for JSONB storage
        """
        return {
            "id": str(concept.id),
            "pref_label": concept.pref_label,
            "identifier": concept.identifier,
            "definition": concept.definition,
            "scope_note": concept.scope_note,
            "alt_labels": concept.alt_labels,
        }

    def serialize_scheme(self, scheme: ConceptScheme) -> dict:
        """Serialize a concept scheme to a dictionary for storage in change events.

        Args:
            scheme: The concept scheme to serialize

        Returns:
            Dictionary representation suitable for JSONB storage
        """
        return {
            "id": str(scheme.id),
            "title": scheme.title,
            "description": scheme.description,
            "uri": scheme.uri,
            "publisher": scheme.publisher,
            "version": scheme.version,
        }

    def serialize_broader(
        self,
        concept_id: UUID,
        broader_concept_id: UUID,
        concept_label: str,
        broader_label: str,
    ) -> dict:
        """Serialize a broader relationship to a dictionary for storage in change events.

        Args:
            concept_id: The narrower concept ID
            broader_concept_id: The broader concept ID
            concept_label: The pref_label of the narrower concept
            broader_label: The pref_label of the broader concept

        Returns:
            Dictionary representation suitable for JSONB storage
        """
        return {
            "concept_id": str(concept_id),
            "broader_concept_id": str(broader_concept_id),
            "concept_label": concept_label,
            "broader_label": broader_label,
        }

    def serialize_related(
        self,
        concept_id: UUID,
        related_concept_id: UUID,
        concept_label: str,
        related_label: str,
    ) -> dict:
        """Serialize a related relationship to a dictionary for storage in change events.

        Args:
            concept_id: The first concept ID (smaller UUID)
            related_concept_id: The second concept ID (larger UUID)
            concept_label: The pref_label of the first concept
            related_label: The pref_label of the second concept

        Returns:
            Dictionary representation suitable for JSONB storage
        """
        return {
            "concept_id": str(concept_id),
            "related_concept_id": str(related_concept_id),
            "concept_label": concept_label,
            "related_label": related_label,
        }
