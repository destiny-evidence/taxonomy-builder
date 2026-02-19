"""Integration tests for the publishing API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.blob_store import FilesystemBlobStore
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    project = Project(name="API Publish Test", namespace="http://example.org/vocab")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def publishable_project(db_session: AsyncSession, project: Project) -> Project:
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/scheme",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    db_session.add(Concept(scheme_id=scheme.id, pref_label="Term A", identifier="term-a"))
    await db_session.flush()

    # Expunge so the API handler loads a fresh project with relationships
    db_session.expunge(project)
    return project


class TestPreview:
    @pytest.mark.asyncio
    async def test_preview_valid(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/publish/preview"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation"]["valid"] is True
        assert data["content_summary"]["schemes"] >= 1
        assert data["content_summary"]["concepts"] >= 1
        assert data["content_summary"]["classes"] == 0
        assert data["suggested_version"] == "1.0"
        assert data["suggested_pre_release_version"] == "1.0-pre1"
        assert data["latest_version"] is None
        assert data["latest_pre_release_version"] is None
        assert data["diff"] is None

    @pytest.mark.asyncio
    async def test_preview_invalid(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        resp = await authenticated_client.get(
            f"/api/projects/{project.id}/publish/preview"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation"]["valid"] is False

    @pytest.mark.asyncio
    async def test_preview_includes_diff_after_publish(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/publish/preview"
        )
        data = resp.json()
        assert data["diff"] is not None
        assert data["suggested_version"] == "1.1"
        assert data["suggested_pre_release_version"] == "2.0-pre1"
        assert data["latest_version"] == "1.0"
        assert data["latest_pre_release_version"] is None

    @pytest.mark.asyncio
    async def test_preview_suggests_major_bump_for_removals(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        publishable_project: Project,
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        # Delete the concept and add a replacement so validation still passes
        result = await db_session.execute(select(Concept))
        for concept in result.scalars().all():
            await db_session.delete(concept)
        scheme_result = await db_session.execute(select(ConceptScheme))
        scheme = scheme_result.scalar_one()
        db_session.add(Concept(scheme_id=scheme.id, pref_label="Replacement", identifier="replacement"))
        await db_session.flush()
        db_session.expunge_all()

        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/publish/preview"
        )
        data = resp.json()
        assert data["suggested_version"] == "2.0"
        assert data["suggested_pre_release_version"] == "2.0-pre1"

    @pytest.mark.asyncio
    async def test_preview_pre_release_version_increments(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        """Pre-release version number increments when pre-releases exist."""
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0-pre1", "title": "Pre 1", "pre_release": True},
        )
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/publish/preview"
        )
        data = resp.json()
        assert data["suggested_version"] == "1.0"
        assert data["suggested_pre_release_version"] == "1.0-pre2"
        assert data["latest_version"] is None
        assert data["latest_pre_release_version"] == "1.0-pre1"

    @pytest.mark.asyncio
    async def test_preview_pre_release_always_major_bump(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        """Pre-release suggestion always uses major bump even for minor diffs."""
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        # Publish a pre-release at the major bump version
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "2.0-pre1", "title": "Pre 1", "pre_release": True},
        )
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/publish/preview"
        )
        data = resp.json()
        # Release uses diff-based minor bump, pre-release uses major bump
        assert data["suggested_version"] == "1.1"
        assert data["suggested_pre_release_version"] == "2.0-pre2"
        assert data["latest_version"] == "1.0"
        assert data["latest_pre_release_version"] == "2.0-pre1"

    @pytest.mark.asyncio
    async def test_preview_hides_pre_release_older_than_latest(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        """latest_pre_release_version is None when the pre-release predates the latest finalized."""
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0-pre1", "title": "Pre", "pre_release": True},
        )
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Release"},
        )
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/publish/preview"
        )
        data = resp.json()
        assert data["latest_version"] == "1.0"
        assert data["latest_pre_release_version"] is None

    @pytest.mark.asyncio
    async def test_preview_not_found(self, authenticated_client: AsyncClient) -> None:
        resp = await authenticated_client.get(
            f"/api/projects/{uuid4()}/publish/preview"
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_preview_unauthenticated(
        self, client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await client.get(
            f"/api/projects/{publishable_project.id}/publish/preview"
        )
        assert resp.status_code == 401


class TestPublish:
    @pytest.mark.asyncio
    async def test_publish_release(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "First Release"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["version"] == "1.0"
        assert data["title"] == "First Release"
        assert data["finalized"] is True
        assert data["published_at"] is not None
        assert data["publisher"] == "Test User"

    @pytest.mark.asyncio
    async def test_publish_pre_release(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0-pre1", "title": "Pre-release", "pre_release": True},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["version"] == "1.0-pre1"
        assert data["finalized"] is False
        assert data["published_at"] is not None

    @pytest.mark.asyncio
    async def test_publish_multiple_pre_releases(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        """Multiple pre-releases can coexist for the same project."""
        resp1 = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0-pre1", "title": "Pre 1", "pre_release": True},
        )
        assert resp1.status_code == 201

        resp2 = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0-pre2", "title": "Pre 2", "pre_release": True},
        )
        assert resp2.status_code == 201

        list_resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/versions"
        )
        assert len(list_resp.json()) == 2

    @pytest.mark.asyncio
    async def test_publish_links_previous_version(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        v1_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        v1_id = v1_resp.json()["id"]

        v2_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "2.0", "title": "V2"},
        )
        assert v2_resp.json()["previous_version_id"] == v1_id

    @pytest.mark.asyncio
    async def test_publish_pre_release_links_previous_finalized(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        """Pre-releases link to the latest finalized version as previous."""
        v1_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        v1_id = v1_resp.json()["id"]

        pre_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.1-pre1", "title": "Pre", "pre_release": True},
        )
        assert pre_resp.json()["previous_version_id"] == v1_id

    @pytest.mark.asyncio
    async def test_publish_validation_failure(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{project.id}/publish",
            json={"version": "1.0", "title": "Nope"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data["detail"]

    @pytest.mark.asyncio
    async def test_publish_duplicate_version(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "First"},
        )
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Dup"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_publish_pre_release_flag_requires_suffix(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "X", "pre_release": True},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_publish_release_rejects_pre_release_suffix(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0-pre1", "title": "X", "pre_release": False},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_publish_not_found(self, authenticated_client: AsyncClient) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{uuid4()}/publish",
            json={"version": "1.0", "title": "X"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_publish_unauthenticated(
        self, client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "X"},
        )
        assert resp.status_code == 401


class TestListVersions:
    @pytest.mark.asyncio
    async def test_list_empty(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/versions"
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_not_found(self, authenticated_client: AsyncClient) -> None:
        resp = await authenticated_client.get(
            f"/api/projects/{uuid4()}/versions"
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_with_versions(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "2.0", "title": "V2"},
        )
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/versions"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["version"] == "2.0"

    @pytest.mark.asyncio
    async def test_list_includes_pre_releases(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Release"},
        )
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.1-pre1", "title": "Pre", "pre_release": True},
        )
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/versions"
        )
        data = resp.json()
        assert len(data) == 2
        assert data[0]["version"] == "1.1-pre1"
        assert data[0]["finalized"] is False
        assert data[1]["version"] == "1.0"
        assert data[1]["finalized"] is True


class TestReaderFiles:
    """Verify that publishing writes reader files to blob storage."""

    @pytest.mark.asyncio
    async def test_publish_writes_vocabulary_file(
        self,
        authenticated_client: AsyncClient,
        publishable_project: Project,
        blob_store: FilesystemBlobStore,
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        assert resp.status_code == 201
        path = f"{publishable_project.id}/1.0/vocabulary.json"
        assert await blob_store.exists(path)

    @pytest.mark.asyncio
    async def test_publish_writes_project_index(
        self,
        authenticated_client: AsyncClient,
        publishable_project: Project,
        blob_store: FilesystemBlobStore,
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        path = f"{publishable_project.id}/index.json"
        assert await blob_store.exists(path)

    @pytest.mark.asyncio
    async def test_publish_writes_root_index(
        self,
        authenticated_client: AsyncClient,
        publishable_project: Project,
        blob_store: FilesystemBlobStore,
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        assert await blob_store.exists("index.json")
