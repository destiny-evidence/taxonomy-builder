"""Tests for Feedback API endpoints."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import AuthenticatedUser, get_current_user, require_role
from taxonomy_builder.main import app
from taxonomy_builder.models.feedback import Feedback
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.models.user import User

# Fixed UUIDs for snapshot entities
CONCEPT_ID = "01234567-89ab-7def-8123-456789abcdef"
SCHEME_ID = "01234567-89ab-7def-8123-456789abcde0"
CLASS_ID = "01234567-89ab-7def-8123-456789abcde1"
PROPERTY_ID = "01234567-89ab-7def-8123-456789abcde2"


def _make_snapshot(project_id: UUID) -> dict:
    """Build a minimal snapshot dict matching the PublishedVersion.snapshot shape."""
    return {
        "project": {
            "id": str(project_id),
            "name": "Test Project",
        },
        "concept_schemes": [
            {
                "id": SCHEME_ID,
                "title": "Test Scheme",
                "uri": "http://example.org/schemes/test",
                "concepts": [
                    {
                        "id": CONCEPT_ID,
                        "pref_label": "Test Concept",
                        "uri": "http://example.org/concepts/test",
                        "identifier": "test",
                        "alt_labels": [],
                        "broader_ids": [],
                        "related_ids": [],
                    }
                ],
            }
        ],
        "classes": [
            {
                "id": CLASS_ID,
                "identifier": "TestClass",
                "label": "Test Class",
                "uri": "http://example.org/classes/TestClass",
            }
        ],
        "properties": [
            {
                "id": PROPERTY_ID,
                "identifier": "testProp",
                "label": "Test Property",
                "uri": "http://example.org/properties/testProp",
                "domain_class": "TestClass",
                "range_datatype": "xsd:string",
                "cardinality": "0..*",
                "required": False,
            }
        ],
    }


def _make_feedback(user: User, **overrides: Any) -> Feedback:
    """Build a Feedback instance with sensible defaults.

    Only ``content`` is truly required from callers; everything else falls back
    to the most common values used across the test suite.
    """
    defaults: dict[str, Any] = {
        "snapshot_version": "1.0",
        "entity_type": "concept",
        "entity_id": CONCEPT_ID,
        "entity_label": "Test Concept",
        "feedback_type": "unclear_definition",
        "user_id": user.id,
        "author_name": user.display_name,
        "author_email": user.email,
    }
    return Feedback(**(defaults | overrides))


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def published_version(
    db_session: AsyncSession, project: Project
) -> PublishedVersion:
    """Create a published version with snapshot data."""
    pv = PublishedVersion(
        project_id=project.id,
        version="1.0",
        title="v1.0",
        finalized=True,
        published_at=datetime.now(UTC),
        snapshot=_make_snapshot(project.id),
    )
    db_session.add(pv)
    await db_session.flush()
    await db_session.refresh(pv)
    return pv


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a user for testing."""
    user = User(
        keycloak_user_id="feedback-test-keycloak-id",
        email="feedback-test@example.com",
        display_name="Feedback Tester",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create another user for ownership tests."""
    user = User(
        keycloak_user_id="feedback-other-keycloak-id",
        email="feedback-other@example.com",
        display_name="Other Tester",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_client(
    client: AsyncClient, user: User
) -> AsyncGenerator[AsyncClient]:
    """Client authenticated as the test user."""

    async def override_current_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            user=user,
            org_id=None,
            org_name=None,
            org_roles=[],
            client_roles=["feedback-user"],
        )

    app.dependency_overrides[get_current_user] = override_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def other_auth_client(
    client: AsyncClient, other_user: User
) -> AsyncGenerator[AsyncClient]:
    """Client authenticated as a different user."""

    async def override_current_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            user=other_user,
            org_id=None,
            org_name=None,
            org_roles=[],
            client_roles=["feedback-user"],
        )

    app.dependency_overrides[get_current_user] = override_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


def _valid_feedback_body() -> dict:
    """Minimal valid feedback creation body."""
    return {
        "snapshot_version": "1.0",
        "entity_type": "concept",
        "entity_id": CONCEPT_ID,
        "entity_label": "Whatever — overridden by backend",
        "feedback_type": "unclear_definition",
        "content": "The definition is ambiguous.",
    }


# ============ Create Feedback Tests ============


@pytest.mark.asyncio
async def test_create_feedback(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
) -> None:
    """POST with valid body returns 201 with correct fields."""
    body = _valid_feedback_body()
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 201
    data = response.json()
    assert data["entity_type"] == "concept"
    assert data["entity_id"] == CONCEPT_ID
    assert data["feedback_type"] == "unclear_definition"
    assert data["content"] == "The definition is ambiguous."
    assert data["status"] == "open"
    assert data["can_delete"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_feedback_requires_auth(
    client: AsyncClient, project: Project, published_version: PublishedVersion
) -> None:
    """POST without auth returns 401."""
    body = _valid_feedback_body()
    response = await client.post(f"/api/feedback/{project.id}", json=body)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_feedback_invalid_type_for_entity(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
) -> None:
    """POST with feedback_type invalid for entity_type returns 422."""
    body = _valid_feedback_body()
    body["feedback_type"] = "incorrect_modelling"  # class/property only
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_feedback_empty_content(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
) -> None:
    """POST with empty content returns 422."""
    body = _valid_feedback_body()
    body["content"] = ""
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_feedback_overrides_label(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
) -> None:
    """Response label matches snapshot, not the submitted label."""
    body = _valid_feedback_body()
    body["entity_label"] = "Wrong Label"
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 201
    data = response.json()
    assert data["entity_label"] == "Test Concept"


@pytest.mark.asyncio
async def test_create_feedback_invalid_entity_id(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
) -> None:
    """POST with entity_id not in snapshot returns 422."""
    body = _valid_feedback_body()
    body["entity_id"] = str(uuid4())
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_feedback_invalid_version(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
) -> None:
    """POST with nonexistent version returns 404."""
    body = _valid_feedback_body()
    body["snapshot_version"] = "99.0"
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 404


# ============ Create Feedback — Other Entity Types ============


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entity_type", "entity_id", "feedback_type", "expected_label"),
    [
        ("scheme", SCHEME_ID, "missing_term", "Test Scheme"),
        ("class", CLASS_ID, "incorrect_modelling", "Test Class"),
        ("property", PROPERTY_ID, "missing_relationship", "Test Property"),
    ],
    ids=["scheme", "class", "property"],
)
async def test_create_feedback_on_entity_type(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    entity_type: str,
    entity_id: str,
    feedback_type: str,
    expected_label: str,
) -> None:
    """POST feedback on non-concept entity types succeeds and resolves label from snapshot."""
    body = {
        "snapshot_version": "1.0",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_label": "ignored",
        "feedback_type": feedback_type,
        "content": f"Feedback on {entity_type}.",
    }
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 201
    data = response.json()
    assert data["entity_label"] == expected_label


# ============ List Own Feedback Tests ============


@pytest.mark.asyncio
async def test_list_own(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    user: User,
    other_user: User,
    db_session: AsyncSession,
) -> None:
    """GET /mine returns only own feedback, excludes others'."""
    fb_own = _make_feedback(user, project_id=project.id, content="My feedback")
    fb_other = _make_feedback(
        other_user, project_id=project.id, content="Other user's feedback"
    )
    db_session.add_all([fb_own, fb_other])
    await db_session.flush()

    response = await auth_client.get(f"/api/feedback/{project.id}/mine")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "My feedback"
    assert data[0]["can_delete"] is True


@pytest.mark.asyncio
async def test_list_own_excludes_deleted(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    user: User,
    db_session: AsyncSession,
) -> None:
    """Soft-deleted feedback is not returned."""
    fb = _make_feedback(
        user,
        project_id=project.id,
        content="Deleted feedback",
        deleted_at=datetime.now(),
    )
    db_session.add(fb)
    await db_session.flush()

    response = await auth_client.get(f"/api/feedback/{project.id}/mine")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_own_filter_version(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    user: User,
    db_session: AsyncSession,
) -> None:
    """?version=1.0 filters correctly."""
    fb_v1 = _make_feedback(user, project_id=project.id, content="v1 feedback")
    fb_v2 = _make_feedback(
        user, project_id=project.id, content="v2 feedback", snapshot_version="2.0"
    )
    db_session.add_all([fb_v1, fb_v2])
    await db_session.flush()

    response = await auth_client.get(
        f"/api/feedback/{project.id}/mine?version=1.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "v1 feedback"


@pytest.mark.asyncio
async def test_list_own_filter_entity_type(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    user: User,
    db_session: AsyncSession,
) -> None:
    """?entity_type=concept filters correctly."""
    fb_concept = _make_feedback(
        user, project_id=project.id, content="concept feedback"
    )
    fb_class = _make_feedback(
        user,
        project_id=project.id,
        content="class feedback",
        entity_type="class",
        entity_id=CLASS_ID,
        entity_label="Test Class",
        feedback_type="incorrect_modelling",
    )
    db_session.add_all([fb_concept, fb_class])
    await db_session.flush()

    response = await auth_client.get(
        f"/api/feedback/{project.id}/mine?entity_type=concept"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "concept feedback"


@pytest.mark.asyncio
async def test_list_own_requires_auth(
    client: AsyncClient, project: Project
) -> None:
    """GET /mine without auth returns 401."""
    response = await client.get(f"/api/feedback/{project.id}/mine")
    assert response.status_code == 401


# ============ Delete Feedback Tests ============


@pytest.mark.asyncio
async def test_delete_own(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    user: User,
    db_session: AsyncSession,
) -> None:
    """DELETE own feedback returns 204, excluded from subsequent list."""
    fb = _make_feedback(user, project_id=project.id, content="To be deleted")
    db_session.add(fb)
    await db_session.flush()

    response = await auth_client.delete(f"/api/feedback/{fb.id}")
    assert response.status_code == 204

    # Verify excluded from list
    list_response = await auth_client.get(f"/api/feedback/{project.id}/mine")
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_delete_other_user(
    other_auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    user: User,
    db_session: AsyncSession,
) -> None:
    """DELETE another user's feedback returns 403."""
    fb = _make_feedback(
        user, project_id=project.id, content="Owned by user, not other_user"
    )
    db_session.add(fb)
    await db_session.flush()

    response = await other_auth_client.delete(f"/api/feedback/{fb.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_nonexistent(auth_client: AsyncClient) -> None:
    """DELETE nonexistent feedback returns 404."""
    response = await auth_client.delete(f"/api/feedback/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_requires_auth(
    client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
    user: User,
    db_session: AsyncSession,
) -> None:
    """DELETE without auth returns 401."""
    fb = _make_feedback(user, project_id=project.id, content="Auth test")
    db_session.add(fb)
    await db_session.flush()

    response = await client.delete(f"/api/feedback/{fb.id}")
    assert response.status_code == 401


# ============ Role-Based Authorization Tests ============


@pytest.mark.asyncio
async def test_feedback_user_cannot_access_projects(
    auth_client: AsyncClient,
) -> None:
    """A feedback-only user gets 403 on non-feedback endpoints."""
    response = await auth_client.get("/api/projects")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_feedback_user_can_create_feedback(
    auth_client: AsyncClient,
    project: Project,
    published_version: PublishedVersion,
) -> None:
    """A feedback-only user can submit feedback."""
    body = _valid_feedback_body()
    response = await auth_client.post(
        f"/api/feedback/{project.id}", json=body
    )
    assert response.status_code == 201
