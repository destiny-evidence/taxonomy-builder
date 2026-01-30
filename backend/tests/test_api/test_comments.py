"""Tests for Comment API endpoints."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import AuthenticatedUser, get_current_user
from taxonomy_builder.main import app
from taxonomy_builder.models.comment import Comment
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.user import User


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/concepts",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.fixture
async def concept(db_session: AsyncSession, scheme: ConceptScheme) -> Concept:
    """Create a concept for testing."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test Concept",
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)
    return concept


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a user for testing."""
    user = User(
        keycloak_user_id="test-keycloak-id",
        email="test@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create another user for testing ownership checks."""
    user = User(
        keycloak_user_id="other-keycloak-id",
        email="other@example.com",
        display_name="Other User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_client(
    client: AsyncClient, user: User
) -> AsyncGenerator[AsyncClient, None]:
    """Client with mocked authentication returning the test user."""

    async def override_current_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            user=user,
            org_id=None,
            org_name=None,
            org_roles=[],
        )

    app.dependency_overrides[get_current_user] = override_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def other_auth_client(
    client: AsyncClient, other_user: User
) -> AsyncGenerator[AsyncClient, None]:
    """Client authenticated as a different user."""

    async def override_current_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            user=other_user,
            org_id=None,
            org_name=None,
            org_roles=[],
        )

    app.dependency_overrides[get_current_user] = override_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ============ List Comments Tests ============


@pytest.mark.asyncio
async def test_list_comments_empty(
    auth_client: AsyncClient, concept: Concept
) -> None:
    """Test listing comments when none exist."""
    response = await auth_client.get(f"/api/concepts/{concept.id}/comments")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_comments(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    concept: Concept,
    user: User,
) -> None:
    """Test listing comments returns comments with author info."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Test comment",
    )
    db_session.add(comment)
    await db_session.flush()

    response = await auth_client.get(f"/api/concepts/{concept.id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Test comment"
    assert data[0]["user"]["display_name"] == "Test User"
    assert data[0]["can_delete"] is True  # User owns this comment


@pytest.mark.asyncio
async def test_list_comments_can_delete_false_for_others(
    db_session: AsyncSession,
    concept: Concept,
    user: User,
    other_user: User,
    other_auth_client: AsyncClient,
) -> None:
    """Test that can_delete is false for comments owned by others."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,  # Owned by 'user'
        content="User's comment",
    )
    db_session.add(comment)
    await db_session.flush()

    # other_auth_client is authenticated as other_user
    response = await other_auth_client.get(f"/api/concepts/{concept.id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["can_delete"] is False


@pytest.mark.asyncio
async def test_list_comments_concept_not_found(auth_client: AsyncClient) -> None:
    """Test listing comments for non-existent concept returns 404."""
    response = await auth_client.get(f"/api/concepts/{uuid4()}/comments")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_comments_requires_auth(
    client: AsyncClient, concept: Concept
) -> None:
    """Test that listing comments requires authentication."""
    response = await client.get(f"/api/concepts/{concept.id}/comments")
    assert response.status_code == 401


# ============ Create Comment Tests ============


@pytest.mark.asyncio
async def test_create_comment(auth_client: AsyncClient, concept: Concept) -> None:
    """Test creating a new comment."""
    response = await auth_client.post(
        f"/api/concepts/{concept.id}/comments",
        json={"content": "New comment"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "New comment"
    assert data["user"]["display_name"] == "Test User"
    assert data["can_delete"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_comment_requires_auth(
    client: AsyncClient, concept: Concept
) -> None:
    """Test that creating comment requires authentication."""
    response = await client.post(
        f"/api/concepts/{concept.id}/comments",
        json={"content": "Test"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_comment_empty_content(
    auth_client: AsyncClient, concept: Concept
) -> None:
    """Test creating comment with empty content fails validation."""
    response = await auth_client.post(
        f"/api/concepts/{concept.id}/comments",
        json={"content": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_comment_whitespace_content(
    auth_client: AsyncClient, concept: Concept
) -> None:
    """Test creating comment with whitespace-only content fails validation."""
    response = await auth_client.post(
        f"/api/concepts/{concept.id}/comments",
        json={"content": "   "},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_comment_concept_not_found(auth_client: AsyncClient) -> None:
    """Test creating comment for non-existent concept returns 404."""
    response = await auth_client.post(
        f"/api/concepts/{uuid4()}/comments",
        json={"content": "Test"},
    )
    assert response.status_code == 404


# ============ Delete Comment Tests ============


@pytest.mark.asyncio
async def test_delete_comment(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    concept: Concept,
    user: User,
) -> None:
    """Test deleting own comment."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="To delete",
    )
    db_session.add(comment)
    await db_session.flush()

    response = await auth_client.delete(f"/api/comments/{comment.id}")
    assert response.status_code == 204

    # Verify comment is no longer in list
    list_response = await auth_client.get(f"/api/concepts/{concept.id}/comments")
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_delete_comment_not_owner(
    db_session: AsyncSession,
    concept: Concept,
    user: User,
    other_auth_client: AsyncClient,
) -> None:
    """Test that users cannot delete others' comments."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,  # Owned by 'user'
        content="User's comment",
    )
    db_session.add(comment)
    await db_session.flush()

    # other_auth_client is authenticated as other_user
    response = await other_auth_client.delete(f"/api/comments/{comment.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_comment_not_found(auth_client: AsyncClient) -> None:
    """Test deleting non-existent comment returns 404."""
    response = await auth_client.delete(f"/api/comments/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_comment_requires_auth(
    client: AsyncClient,
    db_session: AsyncSession,
    concept: Concept,
    user: User,
) -> None:
    """Test that deleting comment requires authentication."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Test",
    )
    db_session.add(comment)
    await db_session.flush()

    response = await client.delete(f"/api/comments/{comment.id}")
    assert response.status_code == 401


# ============ Comment Threading API Tests ============


@pytest.mark.asyncio
async def test_create_reply_to_comment(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    concept: Concept,
    user: User,
) -> None:
    """Test creating a reply to a top-level comment via API."""
    # Create parent comment
    parent = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Parent comment",
    )
    db_session.add(parent)
    await db_session.flush()

    # Create reply via API
    response = await auth_client.post(
        f"/api/concepts/{concept.id}/comments",
        json={"content": "Reply comment", "parent_comment_id": str(parent.id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Reply comment"
    assert data["parent_comment_id"] == str(parent.id)


@pytest.mark.asyncio
async def test_reject_nested_reply_via_api(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    concept: Concept,
    user: User,
) -> None:
    """Test that API rejects replies to replies (no nesting)."""
    # Create parent comment
    parent = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Parent comment",
    )
    db_session.add(parent)
    await db_session.flush()

    # Create first reply
    first_reply = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="First reply",
        parent_comment_id=parent.id,
    )
    db_session.add(first_reply)
    await db_session.flush()

    # Try to create nested reply via API (should be rejected)
    response = await auth_client.post(
        f"/api/concepts/{concept.id}/comments",
        json={
            "content": "Nested reply",
            "parent_comment_id": str(first_reply.id),
        },
    )

    assert response.status_code == 409  # Conflict
    assert "reply" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reject_invalid_parent_comment_id_via_api(
    auth_client: AsyncClient, concept: Concept
) -> None:
    """Test that API rejects invalid parent_comment_id."""
    fake_id = uuid4()
    response = await auth_client.post(
        f"/api/concepts/{concept.id}/comments",
        json={"content": "Test reply", "parent_comment_id": str(fake_id)},
    )

    assert response.status_code == 409  # Conflict
    assert "parent" in response.json()["detail"].lower()
