"""Service for the publishing workflow: validation, diff, and orchestration."""

from datetime import datetime
from uuid import UUID

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.publishing import (
    ContentSummary,
    PublishPreview,
    PublishRequest,
    UpdateDraftRequest,
)
from taxonomy_builder.schemas.snapshot import (
    DiffItem,
    DiffResult,
    FieldChange,
    ModifiedItem,
    SnapshotVocabulary,
    ValidationError,
    ValidationResult,
)
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.snapshot_service import SnapshotService


class ValidationFailedError(Exception):
    """Raised when a project fails validation and cannot be published."""

    def __init__(self, validation_result: ValidationResult) -> None:
        self.validation_result = validation_result
        super().__init__("Project failed pre-publish validation.")


class VersionConflictError(Exception):
    """Raised when a version string already exists for this project."""

    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(f"Version '{version}' already exists for this project.")


class DraftExistsError(Exception):
    """Raised when trying to create a second draft for a project."""

    def __init__(self) -> None:
        super().__init__("A draft version already exists for this project.")


class VersionNotFoundError(Exception):
    """Raised when a published version is not found."""

    def __init__(self, version_id: UUID) -> None:
        self.version_id = version_id
        super().__init__(f"Published version '{version_id}' not found.")


class NotADraftError(Exception):
    """Raised when trying to update/delete a finalized version."""

    def __init__(self, version_id: UUID) -> None:
        self.version_id = version_id
        super().__init__(f"Version '{version_id}' is finalized and cannot be modified.")


class PublishingService:
    """Orchestrates validation, snapshot, diff, and version creation."""

    def __init__(
        self,
        db: AsyncSession,
        project_service: ProjectService,
        snapshot_service: SnapshotService,
    ) -> None:
        self.db = db
        self._project_service = project_service
        self._snapshot_service = snapshot_service

    @staticmethod
    def validate_snapshot(snapshot: SnapshotVocabulary) -> ValidationResult:
        """Validate a snapshot is ready to publish.

        Runs Pydantic validators on the snapshot data, collecting all errors.
        """
        try:
            SnapshotVocabulary.model_validate(snapshot.model_dump(mode="json"))
            return ValidationResult(valid=True, errors=[])
        except PydanticValidationError as e:
            errors = []
            for err in e.errors():
                ctx = err.get("ctx", {})
                entity_id_str = ctx.get("entity_id")
                errors.append(
                    ValidationError(
                        code=err["type"],
                        message=err["msg"],
                        entity_type=ctx.get("entity_type"),
                        entity_id=UUID(entity_id_str) if entity_id_str else None,
                        entity_label=ctx.get("entity_label"),
                    )
                )
            return ValidationResult(valid=False, errors=errors)

    @staticmethod
    def _field_changes(prev, curr, exclude: set[str]) -> list[FieldChange]:
        prev_data = prev.model_dump(exclude=exclude)
        curr_data = curr.model_dump(exclude=exclude)
        return [
            FieldChange(field=f, old=str(prev_data[f]), new=str(curr_data[f]))
            for f in prev_data
            if prev_data[f] != curr_data[f]
        ]

    @staticmethod
    def compute_diff(
        previous: SnapshotVocabulary | None,
        current: SnapshotVocabulary,
    ) -> DiffResult:
        """Diff two snapshots, returning added/modified/removed items."""
        prev_schemes = {s.id: s for s in previous.concept_schemes} if previous else {}
        curr_schemes = {s.id: s for s in current.concept_schemes}

        # Categorise schemes
        added_schemes = [
            curr_schemes[scheme_id] for scheme_id in curr_schemes.keys() - prev_schemes.keys()
        ]
        removed_schemes = [
            prev_schemes[scheme_id] for scheme_id in prev_schemes.keys() - curr_schemes.keys()
        ]
        modified_schemes = [
            (
                prev_schemes[scheme_id],
                curr_schemes[scheme_id],
                {concept.id: concept for concept in prev_schemes[scheme_id].concepts},
                {concept.id: concept for concept in curr_schemes[scheme_id].concepts},
            )
            for scheme_id in prev_schemes.keys() & curr_schemes.keys()
        ]

        added = (
            # New schemes
            [
                DiffItem(id=scheme.id, label=scheme.title, entity_type="scheme")
                for scheme in added_schemes
            ]
            # Concepts in new schemes
            + [
                DiffItem(id=concept.id, label=concept.pref_label, entity_type="concept")
                for scheme in added_schemes
                for concept in scheme.concepts
            ]
            # New concepts in existing schemes
            + [
                DiffItem(id=cid, label=curr_c[cid].pref_label, entity_type="concept")
                for _, _, prev_c, curr_c in modified_schemes
                for cid in curr_c.keys() - prev_c.keys()
            ]
        )

        removed = (
            # Removed schemes
            [
                DiffItem(id=scheme.id, label=scheme.title, entity_type="scheme")
                for scheme in removed_schemes
            ]
            # Concepts in removed schemes
            + [
                DiffItem(id=concept.id, label=concept.pref_label, entity_type="concept")
                for scheme in removed_schemes
                for concept in scheme.concepts
            ]
            # Removed concepts in existing schemes
            + [
                DiffItem(id=cid, label=prev_c[cid].pref_label, entity_type="concept")
                for _, _, prev_c, curr_c in modified_schemes
                for cid in prev_c.keys() - curr_c.keys()
            ]
        )

        modified = (
            # Modified scheme metadata
            [
                ModifiedItem(
                    id=curr_scheme.id,
                    label=curr_scheme.title,
                    entity_type="scheme",
                    changes=changes,
                )
                for prev_scheme, curr_scheme, _, _ in modified_schemes
                if (
                    changes := PublishingService._field_changes(
                        prev_scheme, curr_scheme, {"id", "concepts"}
                    )
                )
            ]
            # Modified concepts in existing schemes
            + [
                ModifiedItem(
                    id=concept_id,
                    label=curr_concepts[concept_id].pref_label,
                    entity_type="concept",
                    changes=changes,
                )
                for _, _, prev_concepts, curr_concepts in modified_schemes
                for concept_id in prev_concepts.keys() & curr_concepts.keys()
                if (
                    changes := PublishingService._field_changes(
                        prev_concepts[concept_id], curr_concepts[concept_id], {"id"}
                    )
                )
            ]
        )

        return DiffResult(added=added, modified=modified, removed=removed)

    async def publish(
        self,
        project_id: UUID,
        request: PublishRequest,
        publisher: str | None = None,
    ) -> PublishedVersion:
        """Publish a new version (or create a draft) of a project."""
        snapshot = await self._snapshot_service.build_snapshot(project_id)
        validation = self.validate_snapshot(snapshot)
        if not validation.valid:
            raise ValidationFailedError(validation)

        previous = await self._get_latest_finalized(project_id)

        version = PublishedVersion(
            project_id=project_id,
            version=request.version,
            title=request.title,
            notes=request.notes,
            finalized=request.finalized,
            published_at=datetime.now() if request.finalized else None,
            publisher=publisher,
            previous_version_id=previous.id if previous else None,
            snapshot=snapshot.model_dump(mode="json"),
        )
        self.db.add(version)

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            error_msg = str(e.orig) if e.orig else str(e)
            if "uq_published_version_per_project" in error_msg:
                raise VersionConflictError(request.version)
            if "ix_one_draft_per_project" in error_msg:
                raise DraftExistsError()
            raise

        await self.db.refresh(version)
        return version

    async def finalize(
        self,
        project_id: UUID,
        version_id: UUID,
    ) -> PublishedVersion:
        """Promote a draft version to finalized."""
        version = await self.get_version(project_id, version_id)
        version.finalized = True
        version.published_at = datetime.now()
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def list_versions(self, project_id: UUID) -> list[PublishedVersion]:
        """List all published versions for a project, newest first."""
        result = await self.db.execute(
            select(PublishedVersion)
            .where(PublishedVersion.project_id == project_id)
            .order_by(PublishedVersion.version_sort_key.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, project_id: UUID, version_id: UUID) -> PublishedVersion:
        """Get a single published version.

        Raises VersionNotFoundError if not found.
        """
        result = await self.db.execute(
            select(PublishedVersion).where(
                PublishedVersion.id == version_id,
                PublishedVersion.project_id == project_id,
            )
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise VersionNotFoundError(version_id)
        return version

    async def preview(self, project_id: UUID) -> PublishPreview:
        """Build a publish preview: validation, content summary, and diff."""
        snapshot = await self._snapshot_service.build_snapshot(project_id)
        validation = self.validate_snapshot(snapshot)

        content_summary = ContentSummary(
            schemes=len(snapshot.concept_schemes),
            concepts=sum(len(s.concepts) for s in snapshot.concept_schemes),
            properties=len(snapshot.properties),
        )

        latest = await self._get_latest_finalized(project_id)
        diff = None
        if latest:
            prev_snapshot = SnapshotVocabulary.model_validate(latest.snapshot)
            diff = self.compute_diff(prev_snapshot, snapshot)

        suggested = self._suggest_version(latest.version if latest else None, diff)

        return PublishPreview(
            validation=validation,
            diff=diff,
            content_summary=content_summary,
            suggested_version=suggested,
        )

    async def update_draft(
        self,
        project_id: UUID,
        version_id: UUID,
        request: UpdateDraftRequest,
    ) -> PublishedVersion:
        """Update a draft version with a fresh snapshot and optional metadata."""
        version = await self.get_version(project_id, version_id)
        if version.finalized:
            raise NotADraftError(version_id)

        snapshot = await self._snapshot_service.build_snapshot(project_id)
        validation = self.validate_snapshot(snapshot)
        if not validation.valid:
            raise ValidationFailedError(validation)

        version.snapshot = snapshot.model_dump(mode="json")
        if request.version is not None:
            version.version = request.version
        if request.title is not None:
            version.title = request.title
        if request.notes is not None:
            version.notes = request.notes

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            error_msg = str(e.orig) if e.orig else str(e)
            if "uq_published_version_per_project" in error_msg:
                raise VersionConflictError(request.version or version.version)
            raise

        await self.db.refresh(version)
        return version

    async def delete_draft(
        self,
        project_id: UUID,
        version_id: UUID,
    ) -> None:
        """Delete a draft version."""
        version = await self.get_version(project_id, version_id)
        if version.finalized:
            raise NotADraftError(version_id)
        await self.db.delete(version)
        await self.db.flush()

    async def _get_latest_finalized(self, project_id: UUID) -> PublishedVersion | None:
        result = await self.db.execute(
            select(PublishedVersion).where(
                PublishedVersion.project_id == project_id,
                PublishedVersion.latest.is_(True),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _suggest_version(latest_version: str | None, diff: DiffResult | None) -> str:
        """Suggest next version: major bump for edits/removals, minor otherwise."""
        if latest_version is None:
            return "1.0"
        parts = latest_version.split(".")
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
        except ValueError, IndexError:
            return "1.0"
        if diff and (diff.modified or diff.removed):
            return f"{major + 1}.0"
        return f"{major}.{minor + 1}"
