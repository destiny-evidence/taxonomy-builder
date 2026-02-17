"""Integration tests for the publishing API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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

    db_session.add(Concept(scheme_id=scheme.id, pref_label="Term A"))
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
        assert data["suggested_version"] == "1.0"

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
    async def test_publish(
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
    async def test_publish_draft(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Draft", "finalized": False},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["finalized"] is False
        assert data["published_at"] is None

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
    async def test_publish_rejects_invalid_draft(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """An invalid project cannot be saved even as a draft."""
        resp = await authenticated_client.post(
            f"/api/projects/{project.id}/publish",
            json={"version": "1.0", "title": "WIP", "finalized": False},
        )
        assert resp.status_code == 422

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
    async def test_publish_finalized_rejects_when_draft_exists(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Draft", "finalized": False},
        )
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "2.0", "title": "Final"},
        )
        assert resp.status_code == 409

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
        # Newest first
        assert data[0]["version"] == "2.0"


class TestGetVersion:
    @pytest.mark.asyncio
    async def test_get_version(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        create_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "V1"},
        )
        version_id = create_resp.json()["id"]

        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/versions/{version_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == version_id
        assert "snapshot" in data

    @pytest.mark.asyncio
    async def test_get_version_not_found(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/versions/{uuid4()}"
        )
        assert resp.status_code == 404


class TestUpdateDraft:
    @pytest.mark.asyncio
    async def test_update_draft_metadata(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        create_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Draft", "finalized": False},
        )
        version_id = create_resp.json()["id"]

        resp = await authenticated_client.patch(
            f"/api/projects/{publishable_project.id}/versions/{version_id}",
            json={"title": "Updated Draft", "notes": "Some notes"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Draft"
        assert data["notes"] == "Some notes"

    @pytest.mark.asyncio
    async def test_update_finalized_rejected(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        create_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Final"},
        )
        version_id = create_resp.json()["id"]

        resp = await authenticated_client.patch(
            f"/api/projects/{publishable_project.id}/versions/{version_id}",
            json={"title": "Nope"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_update_draft_not_found(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.patch(
            f"/api/projects/{publishable_project.id}/versions/{uuid4()}",
            json={"title": "X"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_draft_unauthenticated(
        self, client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await client.patch(
            f"/api/projects/{publishable_project.id}/versions/{uuid4()}",
            json={"title": "X"},
        )
        assert resp.status_code == 401


class TestDeleteDraft:
    @pytest.mark.asyncio
    async def test_delete_draft(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        create_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Draft", "finalized": False},
        )
        version_id = create_resp.json()["id"]

        resp = await authenticated_client.delete(
            f"/api/projects/{publishable_project.id}/versions/{version_id}"
        )
        assert resp.status_code == 204

        # Verify it's gone
        list_resp = await authenticated_client.get(
            f"/api/projects/{publishable_project.id}/versions"
        )
        assert list_resp.json() == []

    @pytest.mark.asyncio
    async def test_delete_finalized_rejected(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        create_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Final"},
        )
        version_id = create_resp.json()["id"]

        resp = await authenticated_client.delete(
            f"/api/projects/{publishable_project.id}/versions/{version_id}"
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_delete_draft_not_found(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.delete(
            f"/api/projects/{publishable_project.id}/versions/{uuid4()}"
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_draft_unauthenticated(
        self, client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await client.delete(
            f"/api/projects/{publishable_project.id}/versions/{uuid4()}"
        )
        assert resp.status_code == 401


class TestFinalize:
    @pytest.mark.asyncio
    async def test_finalize_draft(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        create_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Draft", "finalized": False},
        )
        version_id = create_resp.json()["id"]

        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/versions/{version_id}/finalize"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["finalized"] is True
        assert data["published_at"] is not None

    @pytest.mark.asyncio
    async def test_finalize_rejects_finalized(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        create_resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/publish",
            json={"version": "1.0", "title": "Final"},
        )
        version_id = create_resp.json()["id"]

        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/versions/{version_id}/finalize"
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_finalize_not_found(
        self, authenticated_client: AsyncClient, publishable_project: Project
    ) -> None:
        resp = await authenticated_client.post(
            f"/api/projects/{publishable_project.id}/versions/{uuid4()}/finalize"
        )
        assert resp.status_code == 404
