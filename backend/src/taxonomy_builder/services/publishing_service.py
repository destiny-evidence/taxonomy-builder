"""Service for the publishing workflow: validation, diff, and orchestration."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.publishing import (
    ContentSummary,
    PublishPreview,
    PublishRequest,
)
from taxonomy_builder.schemas.snapshot import (
    DiffItem,
    DiffResult,
    FieldChange,
    ModifiedItem,
    SnapshotConcept,
    SnapshotScheme,
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


# --- Service ---


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

    async def validate(self, project_id: UUID) -> ValidationResult:
        """Validate a project is ready to publish.

        Raises ProjectNotFoundError if the project does not exist.
        """
        project = await self._project_service.get_project(project_id)
        errors: list[ValidationError] = []

        schemes = project.schemes
        if not schemes:
            errors.append(
                ValidationError(
                    code="no_schemes",
                    message="Project has no concept schemes.",
                )
            )
            return ValidationResult(valid=False, errors=errors)

        total_concepts = 0
        for scheme in schemes:
            if not scheme.uri:
                errors.append(
                    ValidationError(
                        code="scheme_missing_uri",
                        message=f"Scheme '{scheme.title}' has no URI.",
                        entity_type="scheme",
                        entity_id=scheme.id,
                        entity_label=scheme.title,
                    )
                )

            for concept in scheme.concepts:
                total_concepts += 1
                if not concept.pref_label or not concept.pref_label.strip():
                    errors.append(
                        ValidationError(
                            code="concept_missing_pref_label",
                            message=f"A concept in scheme '{scheme.title}' has no preferred label.",
                            entity_type="concept",
                            entity_id=concept.id,
                            entity_label=concept.pref_label,
                        )
                    )

        if total_concepts == 0:
            errors.append(
                ValidationError(
                    code="no_concepts",
                    message="No scheme has any concepts.",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    @staticmethod
    def _diff_fields(
        prev: SnapshotScheme | SnapshotConcept,
        curr: SnapshotScheme | SnapshotConcept,
        exclude: set[str],
    ) -> list[FieldChange]:
        prev_data = prev.model_dump(exclude=exclude)
        curr_data = curr.model_dump(exclude=exclude)
        return [
            FieldChange(field=field, old=str(prev_data[field]), new=str(curr_data[field]))
            for field in prev_data
            if prev_data[field] != curr_data[field]
        ]

    @staticmethod
    def compute_diff(
        previous: SnapshotVocabulary | None,
        current: SnapshotVocabulary,
    ) -> DiffResult:
        """Diff two snapshots, returning added/modified/removed items."""
        added: list[DiffItem] = []
        modified: list[ModifiedItem] = []
        removed: list[DiffItem] = []

        if previous is None:
            for scheme in current.concept_schemes:
                added.append(DiffItem(id=scheme.id, label=scheme.title, entity_type="scheme"))
                for concept in scheme.concepts:
                    added.append(
                        DiffItem(id=concept.id, label=concept.pref_label, entity_type="concept")
                    )
            return DiffResult(added=added, modified=modified, removed=removed)

        prev_schemes = {s.id: s for s in previous.concept_schemes}
        curr_schemes = {s.id: s for s in current.concept_schemes}

        for sid, scheme in curr_schemes.items():
            if sid not in prev_schemes:
                added.append(DiffItem(id=sid, label=scheme.title, entity_type="scheme"))
                for concept in scheme.concepts:
                    added.append(
                        DiffItem(id=concept.id, label=concept.pref_label, entity_type="concept")
                    )
            else:
                scheme_changes = PublishingService._diff_fields(
                    prev_schemes[sid], scheme, {"id", "concepts"}
                )
                if scheme_changes:
                    modified.append(
                        ModifiedItem(
                            id=sid,
                            label=scheme.title,
                            entity_type="scheme",
                            changes=scheme_changes,
                        )
                    )

                prev_concepts = {c.id: c for c in prev_schemes[sid].concepts}
                curr_concepts = {c.id: c for c in scheme.concepts}

                for cid, concept in curr_concepts.items():
                    if cid not in prev_concepts:
                        added.append(
                            DiffItem(id=cid, label=concept.pref_label, entity_type="concept")
                        )
                    else:
                        changes = PublishingService._diff_fields(
                            prev_concepts[cid], concept, {"id"}
                        )
                        if changes:
                            modified.append(
                                ModifiedItem(
                                    id=cid,
                                    label=concept.pref_label,
                                    entity_type="concept",
                                    changes=changes,
                                )
                            )

                for cid, concept in prev_concepts.items():
                    if cid not in curr_concepts:
                        removed.append(
                            DiffItem(id=cid, label=concept.pref_label, entity_type="concept")
                        )

        for sid, scheme in prev_schemes.items():
            if sid not in curr_schemes:
                removed.append(DiffItem(id=sid, label=scheme.title, entity_type="scheme"))
                for concept in scheme.concepts:
                    removed.append(
                        DiffItem(id=concept.id, label=concept.pref_label, entity_type="concept")
                    )

        return DiffResult(added=added, modified=modified, removed=removed)

    async def publish(
        self,
        project_id: UUID,
        request: PublishRequest,
        publisher: str | None = None,
    ) -> PublishedVersion:
        """Publish a new version (or create a draft) of a project.

        Drafts skip validation. Finalized versions must pass validation.
        """
        if request.finalized:
            validation = await self.validate(project_id)
            if not validation.valid:
                raise ValidationFailedError(validation)

        snapshot = await self._snapshot_service.build_snapshot(project_id)
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
        validation = await self.validate(project_id)
        snapshot = await self._snapshot_service.build_snapshot(project_id)

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
