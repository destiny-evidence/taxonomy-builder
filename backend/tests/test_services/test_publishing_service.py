"""Tests for the PublishingService."""


import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.publishing import PublishRequest, UpdateDraftRequest
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectNotFoundError, ProjectService
from taxonomy_builder.services.publishing_service import (
    DraftExistsError,
    NotADraftError,
    PublishingService,
    ValidationFailedError,
    VersionConflictError,
    VersionNotFoundError,
)
from taxonomy_builder.services.snapshot_service import SnapshotService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    project = Project(name="Publish Test", namespace="http://example.org/vocab")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def publishable_project(db_session: AsyncSession, project: Project) -> Project:
    """A project with enough content to pass validation."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/scheme",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    db_session.add(Concept(scheme_id=scheme.id, pref_label="Term A"))
    await db_session.flush()
    return project


def service(db_session: AsyncSession) -> PublishingService:
    db_session.expunge_all()
    project_service = ProjectService(db_session)
    concept_service = ConceptService(db_session)
    snapshot_service = SnapshotService(db_session, project_service, concept_service)
    return PublishingService(db_session, project_service, snapshot_service)


class TestPublish:
    @pytest.mark.asyncio
    async def test_publish_creates_finalized_version(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        request = PublishRequest(version="1.0", title="First Release")
        version = await service(db_session).publish(
            publishable_project.id, request, publisher="test-user"
        )

        assert version.version == "1.0"
        assert version.title == "First Release"
        assert version.finalized is True
        assert version.published_at is not None
        assert version.publisher == "test-user"
        assert version.snapshot is not None

    @pytest.mark.asyncio
    async def test_publish_creates_draft(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        request = PublishRequest(version="1.0", title="Draft", finalized=False)
        version = await service(db_session).publish(
            publishable_project.id, request, publisher="test-user"
        )

        assert version.finalized is False
        assert version.published_at is None

    @pytest.mark.asyncio
    async def test_publish_links_previous_version(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        v1 = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="V1"),
            publisher="user",
        )
        v2 = await svc.publish(
            publishable_project.id,
            PublishRequest(version="2.0", title="V2"),
            publisher="user",
        )

        assert v2.previous_version_id == v1.id

    @pytest.mark.asyncio
    async def test_publish_rejects_invalid_project(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        """An empty project fails validation when finalized."""
        request = PublishRequest(version="1.0", title="Nope")
        with pytest.raises(ValidationFailedError) as exc_info:
            await service(db_session).publish(project.id, request, publisher="user")
        assert exc_info.value.validation_result.valid is False

    @pytest.mark.asyncio
    async def test_publish_rejects_invalid_draft(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        """An invalid project cannot be saved even as a draft."""
        request = PublishRequest(version="1.0", title="WIP Draft", finalized=False)
        with pytest.raises(ValidationFailedError):
            await service(db_session).publish(project.id, request, publisher="user")

    @pytest.mark.asyncio
    async def test_publish_rejects_duplicate_version(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="First"),
            publisher="user",
        )
        with pytest.raises(VersionConflictError):
            await svc.publish(
                publishable_project.id,
                PublishRequest(version="1.0", title="Duplicate"),
                publisher="user",
            )

    @pytest.mark.asyncio
    async def test_publish_rejects_second_draft(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Draft 1", finalized=False),
            publisher="user",
        )
        with pytest.raises(DraftExistsError):
            await svc.publish(
                publishable_project.id,
                PublishRequest(version="2.0", title="Draft 2", finalized=False),
                publisher="user",
            )

    @pytest.mark.asyncio
    async def test_publish_not_found(self, db_session: AsyncSession) -> None:
        from uuid import uuid4

        with pytest.raises(ProjectNotFoundError):
            await service(db_session).publish(
                uuid4(),
                PublishRequest(version="1.0", title="X"),
                publisher="user",
            )

    @pytest.mark.asyncio
    async def test_publish_stores_snapshot(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        version = await service(db_session).publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="With Snapshot"),
            publisher="user",
        )
        assert "concept_schemes" in version.snapshot
        assert "project" in version.snapshot


class TestFinalize:
    @pytest.mark.asyncio
    async def test_finalize_draft(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        draft = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Draft", finalized=False),
            publisher="user",
        )
        finalized = await svc.finalize(publishable_project.id, draft.id)

        assert finalized.finalized is True
        assert finalized.published_at is not None

    @pytest.mark.asyncio
    async def test_finalize_not_found(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        from uuid import uuid4

        with pytest.raises(VersionNotFoundError):
            await service(db_session).finalize(publishable_project.id, uuid4())


class TestListVersions:
    @pytest.mark.asyncio
    async def test_list_versions(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="V1"),
            publisher="user",
        )
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="2.0", title="V2"),
            publisher="user",
        )
        versions = await svc.list_versions(publishable_project.id)
        assert len(versions) == 2

    @pytest.mark.asyncio
    async def test_list_versions_empty(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        versions = await service(db_session).list_versions(publishable_project.id)
        assert versions == []


class TestGetVersion:
    @pytest.mark.asyncio
    async def test_get_version(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        created = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="V1"),
            publisher="user",
        )
        fetched = await svc.get_version(publishable_project.id, created.id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_version_not_found(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        from uuid import uuid4

        with pytest.raises(VersionNotFoundError):
            await service(db_session).get_version(publishable_project.id, uuid4())


class TestUpdateDraft:
    @pytest.mark.asyncio
    async def test_update_draft_refreshes_snapshot(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        draft = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Draft", finalized=False),
            publisher="user",
        )
        original_snapshot = draft.snapshot

        # Add a concept so the snapshot changes
        scheme_result = await db_session.execute(select(ConceptScheme))
        scheme = scheme_result.scalar_one()
        db_session.add(Concept(scheme_id=scheme.id, pref_label="Term B"))
        await db_session.flush()
        db_session.expunge_all()

        updated = await svc.update_draft(
            publishable_project.id, draft.id, UpdateDraftRequest()
        )
        assert updated.snapshot != original_snapshot

    @pytest.mark.asyncio
    async def test_update_draft_metadata(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        draft = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Draft", finalized=False),
            publisher="user",
        )
        updated = await svc.update_draft(
            publishable_project.id,
            draft.id,
            UpdateDraftRequest(version="1.1", title="Updated", notes="Some notes"),
        )
        assert updated.version == "1.1"
        assert updated.title == "Updated"
        assert updated.notes == "Some notes"

    @pytest.mark.asyncio
    async def test_update_finalized_raises(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        version = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Final"),
            publisher="user",
        )
        with pytest.raises(NotADraftError):
            await svc.update_draft(
                publishable_project.id, version.id, UpdateDraftRequest()
            )

    @pytest.mark.asyncio
    async def test_update_draft_version_conflict(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Final"),
            publisher="user",
        )
        draft = await svc.publish(
            publishable_project.id,
            PublishRequest(version="2.0", title="Draft", finalized=False),
            publisher="user",
        )
        with pytest.raises(VersionConflictError):
            await svc.update_draft(
                publishable_project.id,
                draft.id,
                UpdateDraftRequest(version="1.0"),
            )

    @pytest.mark.asyncio
    async def test_update_draft_not_found(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        from uuid import uuid4

        with pytest.raises(VersionNotFoundError):
            await service(db_session).update_draft(
                publishable_project.id, uuid4(), UpdateDraftRequest()
            )


class TestDeleteDraft:
    @pytest.mark.asyncio
    async def test_delete_draft(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        draft = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Draft", finalized=False),
            publisher="user",
        )
        await svc.delete_draft(publishable_project.id, draft.id)
        versions = await svc.list_versions(publishable_project.id)
        assert versions == []

    @pytest.mark.asyncio
    async def test_delete_finalized_raises(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        svc = service(db_session)
        version = await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="Final"),
            publisher="user",
        )
        with pytest.raises(NotADraftError):
            await svc.delete_draft(publishable_project.id, version.id)

    @pytest.mark.asyncio
    async def test_delete_draft_not_found(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        from uuid import uuid4

        with pytest.raises(VersionNotFoundError):
            await service(db_session).delete_draft(publishable_project.id, uuid4())


class TestPreview:
    @pytest.mark.asyncio
    async def test_preview_valid_project(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        preview = await service(db_session).preview(publishable_project.id)
        assert preview.validation.valid is True
        assert preview.content_summary.schemes >= 1
        assert preview.content_summary.concepts >= 1

    @pytest.mark.asyncio
    async def test_preview_invalid_project(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        preview = await service(db_session).preview(project.id)
        assert preview.validation.valid is False

    @pytest.mark.asyncio
    async def test_preview_includes_diff(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        """Preview after a first publish should show diff against last version."""
        svc = service(db_session)
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="V1"),
            publisher="user",
        )
        preview = await svc.preview(publishable_project.id)
        assert preview.diff is not None

    @pytest.mark.asyncio
    async def test_preview_first_publish_no_diff(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        """First publish preview has no previous version to diff against."""
        preview = await service(db_session).preview(publishable_project.id)
        assert preview.diff is None

    @pytest.mark.asyncio
    async def test_preview_suggests_version(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        preview = await service(db_session).preview(publishable_project.id)
        assert preview.suggested_version == "1.0"

    @pytest.mark.asyncio
    async def test_preview_suggests_minor_bump_for_no_changes(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        """No changes since last publish → minor bump."""
        svc = service(db_session)
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="V1"),
            publisher="user",
        )
        preview = await svc.preview(publishable_project.id)
        assert preview.suggested_version == "1.1"

    @pytest.mark.asyncio
    async def test_preview_suggests_major_bump_for_removals(
        self, db_session: AsyncSession, publishable_project: Project
    ) -> None:
        """Removals since last publish → major bump."""
        svc = service(db_session)
        await svc.publish(
            publishable_project.id,
            PublishRequest(version="1.0", title="V1"),
            publisher="user",
        )
        # Delete the concept so the diff shows a removal
        result = await db_session.execute(select(Concept))
        for concept in result.scalars().all():
            await db_session.delete(concept)
        # Add a replacement so validation still passes
        scheme_result = await db_session.execute(select(ConceptScheme))
        scheme = scheme_result.scalar_one()
        db_session.add(Concept(scheme_id=scheme.id, pref_label="Replacement"))
        await db_session.flush()
        db_session.expunge_all()

        preview = await svc.preview(publishable_project.id)
        assert preview.suggested_version == "2.0"
