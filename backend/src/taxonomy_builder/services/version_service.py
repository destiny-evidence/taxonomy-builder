"""Version service for managing published versions of concept schemes."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.services.change_tracker import ChangeTracker


class SchemeNotFoundError(Exception):
    """Raised when a concept scheme is not found."""

    def __init__(self, scheme_id: UUID) -> None:
        self.scheme_id = scheme_id
        super().__init__(f"Concept scheme with id '{scheme_id}' not found")


class DuplicateVersionLabelError(Exception):
    """Raised when a version label already exists for a scheme."""

    def __init__(self, scheme_id: UUID, version_label: str) -> None:
        self.scheme_id = scheme_id
        self.version_label = version_label
        super().__init__(
            f"Version '{version_label}' already exists for scheme '{scheme_id}'"
        )


class VersionService:
    """Service for publishing and managing versions of concept schemes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._tracker = ChangeTracker(db)

    async def _get_scheme(self, scheme_id: UUID) -> ConceptScheme:
        """Get a scheme by ID or raise SchemeNotFoundError."""
        result = await self.db.execute(
            select(ConceptScheme).where(ConceptScheme.id == scheme_id)
        )
        scheme = result.scalar_one_or_none()
        if scheme is None:
            raise SchemeNotFoundError(scheme_id)
        return scheme

    async def _get_concepts_for_scheme(self, scheme_id: UUID) -> list[Concept]:
        """Get all concepts for a scheme with relationships loaded."""
        result = await self.db.execute(
            select(Concept)
            .where(Concept.scheme_id == scheme_id)
            .options(selectinload(Concept.broader))
            .options(selectinload(Concept._related_as_subject))
            .options(selectinload(Concept._related_as_object))
        )
        return list(result.scalars().all())

    def _serialize_scheme(self, scheme: ConceptScheme) -> dict:
        """Serialize a scheme for snapshot storage."""
        return {
            "id": str(scheme.id),
            "title": scheme.title,
            "description": scheme.description,
            "uri": scheme.uri,
            "publisher": scheme.publisher,
            "version": scheme.version,
        }

    def _serialize_concept(self, concept: Concept) -> dict:
        """Serialize a concept for snapshot storage."""
        return {
            "id": str(concept.id),
            "pref_label": concept.pref_label,
            "identifier": concept.identifier,
            "definition": concept.definition,
            "scope_note": concept.scope_note,
            "alt_labels": concept.alt_labels,
            "broader_ids": [str(b.id) for b in concept.broader],
            "related_ids": [str(r.id) for r in concept.related],
        }

    async def _create_snapshot(self, scheme_id: UUID) -> dict:
        """Create a complete snapshot of a scheme and its concepts."""
        # Expire all cached objects to ensure fresh data with relationships
        self.db.expire_all()
        scheme = await self._get_scheme(scheme_id)
        concepts = await self._get_concepts_for_scheme(scheme_id)
        return {
            "scheme": self._serialize_scheme(scheme),
            "concepts": [self._serialize_concept(c) for c in concepts],
        }

    async def publish_version(
        self,
        scheme_id: UUID,
        version_label: str,
        notes: str | None = None,
    ) -> PublishedVersion:
        """Publish a new version of a concept scheme.

        Creates an immutable snapshot of the scheme and all its concepts.

        Args:
            scheme_id: The scheme to publish
            version_label: Version label (e.g., "1.0", "2.0")
            notes: Optional release notes

        Returns:
            The created PublishedVersion

        Raises:
            SchemeNotFoundError: If the scheme doesn't exist
        """
        # Verify scheme exists before creating snapshot
        await self._get_scheme(scheme_id)
        snapshot = await self._create_snapshot(scheme_id)

        version = PublishedVersion(
            scheme_id=scheme_id,
            version_label=version_label,
            snapshot=snapshot,
            notes=notes,
        )
        self.db.add(version)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise DuplicateVersionLabelError(scheme_id, version_label)
        await self.db.refresh(version)

        # Record the publish event
        await self._tracker.record(
            scheme_id=scheme_id,
            entity_type="published_version",
            entity_id=version.id,
            action="publish",
            before=None,
            after={
                "id": str(version.id),
                "version_label": version.version_label,
                "notes": version.notes,
            },
        )

        return version

    async def list_versions(self, scheme_id: UUID) -> list[PublishedVersion]:
        """List all published versions for a scheme.

        Args:
            scheme_id: The scheme to list versions for

        Returns:
            List of published versions, ordered by published_at descending
        """
        result = await self.db.execute(
            select(PublishedVersion)
            .where(PublishedVersion.scheme_id == scheme_id)
            .order_by(PublishedVersion.published_at.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, version_id: UUID) -> PublishedVersion | None:
        """Get a specific published version.

        Args:
            version_id: The version ID

        Returns:
            The published version, or None if not found
        """
        result = await self.db.execute(
            select(PublishedVersion).where(PublishedVersion.id == version_id)
        )
        return result.scalar_one_or_none()
