"""Feedback service for business logic."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.feedback import EntityType, Feedback
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.feedback import FeedbackCreate


class VersionNotFoundError(Exception):
    def __init__(self, project_id: UUID, version: str) -> None:
        self.project_id = project_id
        self.version = version
        super().__init__(f"Version '{version}' not found for project '{project_id}'")


class EntityNotInSnapshotError(Exception):
    def __init__(self, entity_id: str, entity_type: str) -> None:
        self.entity_id = entity_id
        self.entity_type = entity_type
        super().__init__(
            f"Entity '{entity_id}' of type '{entity_type}' not found in snapshot"
        )


class FeedbackNotFoundError(Exception):
    def __init__(self, feedback_id: UUID) -> None:
        self.feedback_id = feedback_id
        super().__init__(f"Feedback with id '{feedback_id}' not found")


class NotFeedbackOwnerError(Exception):
    def __init__(self, feedback_id: UUID, user_id: UUID) -> None:
        self.feedback_id = feedback_id
        self.user_id = user_id
        super().__init__("Cannot delete another user's feedback")


_ENTITY_LOOKUP: dict[EntityType, tuple[str, str]] = {
    EntityType.scheme: ("concept_schemes", "title"),
    EntityType.ontology_class: ("classes", "label"),
    EntityType.property: ("properties", "label"),
}


def _find_entity_label(
    snapshot: dict, entity_type: EntityType, entity_id: str
) -> str | None:
    """Search the snapshot JSONB for an entity and return its label."""
    if entity_type == EntityType.concept:
        for scheme in snapshot.get("concept_schemes", []):
            for concept in scheme.get("concepts", []):
                if str(concept.get("id", "")) == entity_id:
                    return concept.get("pref_label")
        return None

    collection_key, label_field = _ENTITY_LOOKUP[entity_type]
    for entity in snapshot.get(collection_key, []):
        if str(entity.get("id", "")) == entity_id:
            return entity.get(label_field)
    return None


class FeedbackService:
    """Service for managing reader feedback on published entities."""

    def __init__(
        self,
        db: AsyncSession,
        user_id: UUID,
        user_display_name: str,
        user_email: str,
    ) -> None:
        self.db = db
        self.user_id = user_id
        self.user_display_name = user_display_name
        self.user_email = user_email

    async def _get_published_version(
        self, project_id: UUID, version: str
    ) -> PublishedVersion:
        result = await self.db.execute(
            select(PublishedVersion).where(
                PublishedVersion.project_id == project_id,
                PublishedVersion.version == version,
            )
        )
        pv = result.scalar_one_or_none()
        if pv is None:
            raise VersionNotFoundError(project_id, version)
        return pv

    async def create(
        self, project_id: UUID, feedback_in: FeedbackCreate
    ) -> Feedback:
        pv = await self._get_published_version(
            project_id, feedback_in.snapshot_version
        )

        entity_label = _find_entity_label(
            pv.snapshot, feedback_in.entity_type, feedback_in.entity_id
        )
        if entity_label is None:
            raise EntityNotInSnapshotError(
                feedback_in.entity_id, feedback_in.entity_type.value
            )

        feedback = Feedback(
            project_id=project_id,
            snapshot_version=feedback_in.snapshot_version,
            entity_type=feedback_in.entity_type.value,
            entity_id=feedback_in.entity_id,
            entity_label=entity_label,
            feedback_type=feedback_in.feedback_type,
            content=feedback_in.content,
            user_id=self.user_id,
            author_name=self.user_display_name,
            author_email=self.user_email,
        )
        self.db.add(feedback)
        await self.db.flush()
        await self.db.refresh(feedback)
        return feedback

    async def list_own(
        self,
        project_id: UUID,
        version: str | None = None,
        entity_type: str | None = None,
    ) -> list[Feedback]:
        query = (
            select(Feedback)
            .where(
                Feedback.project_id == project_id,
                Feedback.user_id == self.user_id,
                Feedback.deleted_at.is_(None),
            )
            .order_by(Feedback.created_at.desc())
        )
        if version is not None:
            query = query.where(Feedback.snapshot_version == version)
        if entity_type is not None:
            query = query.where(Feedback.entity_type == entity_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete(self, feedback_id: UUID) -> None:
        result = await self.db.execute(
            select(Feedback).where(
                Feedback.id == feedback_id,
                Feedback.user_id == self.user_id,
                Feedback.deleted_at.is_(None),
            )
        )
        feedback = result.scalar_one_or_none()
        if feedback is None:
            raise FeedbackNotFoundError(feedback_id)

        feedback.deleted_at = datetime.now()
        await self.db.flush()
