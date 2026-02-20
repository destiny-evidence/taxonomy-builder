"""Service for the publishing workflow orchestration."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.publishing import (
    ContentSummary,
    PublishPreview,
    PublishRequest,
)
from taxonomy_builder.schemas.snapshot import (
    DiffResult,
    ValidationResult,
)
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.snapshot_service import (
    SnapshotService,
    compute_diff,
    validate_snapshot,
)


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

    async def publish(
        self,
        project_id: UUID,
        request: PublishRequest,
        publisher: str | None = None,
    ) -> PublishedVersion:
        """Publish a new version (release or pre-release) of a project."""
        snapshot = await self._snapshot_service.build_snapshot(project_id)
        validation = validate_snapshot(snapshot)
        if not validation.valid:
            raise ValidationFailedError(validation)

        previous = await self._get_latest_finalized(project_id)
        finalized = not request.pre_release

        version = PublishedVersion(
            project_id=project_id,
            version=request.version,
            title=request.title,
            notes=request.notes,
            finalized=finalized,
            published_at=datetime.now(tz=UTC),
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
            raise

        await self.db.refresh(version)
        return version

    async def list_versions(self, project_id: UUID) -> list[PublishedVersion]:
        """List all published versions for a project, newest first."""
        await self._project_service.get_project(project_id)
        result = await self.db.execute(
            select(PublishedVersion)
            .where(PublishedVersion.project_id == project_id)
            .order_by(PublishedVersion.version_sort_key.desc())
        )
        return list(result.scalars().all())

    async def list_projects_with_latest_version(self) -> list[tuple[Project, str | None]]:
        """All projects with published versions and their latest finalized version string."""
        result = await self.db.execute(
            select(PublishedVersion).order_by(PublishedVersion.version_sort_key.desc())
        )
        all_versions = result.scalars().all()

        project_latest: dict[UUID, tuple[Project, str | None]] = {}
        for version in all_versions:
            if version.project_id not in project_latest:
                project_latest[version.project_id] = (
                    version.project,
                    version.version if version.finalized else None,
                )
            elif project_latest[version.project_id][1] is None and version.finalized:
                project_latest[version.project_id] = (version.project, version.version)

        return list(project_latest.values())

    async def preview(self, project_id: UUID) -> PublishPreview:
        """Build a publish preview: validation, content summary, and diff."""
        snapshot = await self._snapshot_service.build_snapshot(project_id)
        validation = validate_snapshot(snapshot)

        content_summary = ContentSummary(
            schemes=len(snapshot.concept_schemes),
            concepts=sum(len(s.concepts) for s in snapshot.concept_schemes),
            properties=len(snapshot.properties),
            classes=len(snapshot.classes),
        )

        latest = await self._get_latest_finalized(project_id)
        diff = None
        if latest:
            diff = compute_diff(latest.snapshot_vocabulary, snapshot)

        latest_version = latest.version if latest else None
        suggested = await self._suggest_version(latest_version, diff)
        suggested_pre = await self._suggest_version(
            latest_version, diff, pre_release=True, project_id=project_id
        )

        latest_pre = await self._get_latest_pre_release(project_id)
        # Only show pre-release if it's newer than the latest finalized
        latest_pre_version: str | None = None
        if latest_pre:
            if not latest or latest_pre.version_sort_key > latest.version_sort_key:
                latest_pre_version = latest_pre.version

        return PublishPreview(
            validation=validation,
            diff=diff,
            content_summary=content_summary,
            suggested_version=suggested,
            suggested_pre_release_version=suggested_pre,
            latest_version=latest.version if latest else None,
            latest_pre_release_version=latest_pre_version,
        )

    async def _get_latest_pre_release(self, project_id: UUID) -> PublishedVersion | None:
        result = await self.db.execute(
            select(PublishedVersion)
            .where(
                PublishedVersion.project_id == project_id,
                PublishedVersion.finalized.is_(False),
            )
            .order_by(PublishedVersion.version_sort_key.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_latest_finalized(self, project_id: UUID) -> PublishedVersion | None:
        result = await self.db.execute(
            select(PublishedVersion).where(
                PublishedVersion.project_id == project_id,
                PublishedVersion.latest.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def _next_pre_release_number(self, project_id: UUID, base_version: str) -> int:
        """Find the next pre-release number for a given base version.

        Queries for versions matching '{base_version}-pre*' and returns max(n)+1,
        or 1 if no pre-releases exist for this base version.
        """
        result = await self.db.execute(
            select(PublishedVersion.version).where(
                PublishedVersion.project_id == project_id,
                PublishedVersion.version.like(f"{base_version}-pre%"),
            )
        )
        existing = result.scalars().all()
        if not existing:
            return 1

        max_n = 0
        for v in existing:
            suffix = v.split("-pre")[-1]
            try:
                n = int(suffix)
                max_n = max(max_n, n)
            except ValueError:
                continue
        return max_n + 1

    async def _suggest_version(
        self,
        latest_version: str | None,
        diff: DiffResult | None,
        *,
        pre_release: bool = False,
        project_id: UUID | None = None,
    ) -> str:
        """Suggest next version string.

        For releases: major bump if modifications/removals, minor bump otherwise.
        For pre-releases: always major bump with -preN suffix.
        """
        if latest_version is None:
            base = "1.0"
        else:
            parts = latest_version.split(".")
            try:
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
            except ValueError, IndexError:
                base = "1.0"
            else:
                if pre_release or (diff and (diff.modified or diff.removed)):
                    base = f"{major + 1}.0"
                else:
                    base = f"{major}.{minor + 1}"

        if pre_release and project_id is not None:
            pre_num = await self._next_pre_release_number(project_id, base)
            return f"{base}-pre{pre_num}"
        return base
