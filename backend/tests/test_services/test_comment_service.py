"""Tests for the CommentService."""

from datetime import datetime
from uuid import UUID
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.comment import Comment
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.user import User
from taxonomy_builder.schemas.comment import CommentCreate
from taxonomy_builder.services.comment_service import (
    CommentNotFoundError,
    CommentService,
    ConceptNotFoundError,
    NotCommentOwnerError,
    NotTopLevelCommentError,
)


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
    """Create another user for testing."""
    user = User(
        keycloak_user_id="other-keycloak-id",
        email="other@example.com",
        display_name="Other User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# ============ List Comments Tests ============


@pytest.mark.asyncio
async def test_list_comments_empty(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test listing comments when none exist."""
    service = CommentService(db_session, user_id=user.id)
    comments = await service.get_comments(concept.id)
    assert comments == []


@pytest.mark.asyncio
async def test_list_comments(
    db_session: AsyncSession, concept: Concept, user: User,
) -> None:
    """Test listing comments for a concept."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Test comment",
    )
    db_session.add(comment)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    comments = await service.get_comments(concept.id)

    assert len(comments) == 1
    assert comments[0].content == "Test comment"
    assert comments[0].user.display_name == "Test User"

@pytest.mark.asyncio
async def test_list_comments_resolution_filtering(
    db_session: AsyncSession, concept: Concept, user: User, other_user: User
) -> None:
    """Test listing comments for a concept."""
    unresolved_comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Unresolved comment",
    )

    resolved_comment = Comment(
        concept_id=concept.id,
        user_id=other_user.id,
        content="Resolved comment",
        resolved_at=datetime.now(),
        resolved_by=user.id
    )

    db_session.add(unresolved_comment)
    db_session.add(resolved_comment)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    comments = await service.get_comments(concept.id)

    assert len(comments) == 2

    unresolved_comments = await service.get_comments(concept.id, resolved=False)
    assert len(unresolved_comments) == 1

    assert unresolved_comments[0].content == unresolved_comment.content
    assert unresolved_comments[0].user.display_name == unresolved_comment.user.display_name

    resolved_comments = await service.get_comments(concept.id, resolved=True)
    assert len(resolved_comments) == 1
    assert resolved_comments[0].content == resolved_comment.content
    assert resolved_comments[0].user.display_name == resolved_comment.user.display_name

@pytest.mark.asyncio
async def test_list_comments_excludes_deleted(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that soft-deleted comments are excluded."""
    active_comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Active comment",
    )
    deleted_comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Deleted comment",
        deleted_at=datetime.now(),
    )
    db_session.add_all([active_comment, deleted_comment])
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    comments = await service.get_comments(concept.id)

    assert len(comments) == 1
    assert comments[0].content == "Active comment"


@pytest.mark.asyncio
async def test_list_comments_ordered_by_created_at(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test comments are ordered by created_at ascending (oldest first)."""
    comment1 = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="First comment",
    )
    db_session.add(comment1)
    await db_session.flush()

    comment2 = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Second comment",
    )
    db_session.add(comment2)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    comments = await service.get_comments(concept.id)

    assert len(comments) == 2
    assert comments[0].created_at <= comments[1].created_at
    assert comments[0].content == "First comment"
    assert comments[1].content == "Second comment"


@pytest.mark.asyncio
async def test_list_comments_concept_not_found(
    db_session: AsyncSession, user: User
) -> None:
    """Test listing comments for non-existent concept."""
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")
    service = CommentService(db_session, user_id=user.id)

    with pytest.raises(ConceptNotFoundError) as exc_info:
        await service.get_comments(fake_id)

    assert str(fake_id) in str(exc_info.value)


# ============ Create Comment Tests ============


@pytest.mark.asyncio
async def test_create_comment(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test creating a comment."""
    service = CommentService(db_session, user_id=user.id)
    comment_in = CommentCreate(content="New comment")

    comment = await service.create_comment(concept.id, comment_in)

    assert comment.id is not None
    assert isinstance(comment.id, UUID)
    assert comment.concept_id == concept.id
    assert comment.user_id == user.id
    assert comment.content == "New comment"
    assert comment.user.display_name == "Test User"
    assert comment.created_at is not None
    assert comment.deleted_at is None


@pytest.mark.asyncio
async def test_create_comment_concept_not_found(
    db_session: AsyncSession, user: User
) -> None:
    """Test creating comment for non-existent concept."""
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")
    service = CommentService(db_session, user_id=user.id)
    comment_in = CommentCreate(content="Test comment")

    with pytest.raises(ConceptNotFoundError):
        await service.create_comment(fake_id, comment_in)


# ============ Delete Comment Tests ============


@pytest.mark.asyncio
async def test_delete_comment(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test soft-deleting a comment."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="To delete",
    )
    db_session.add(comment)
    await db_session.flush()
    comment_id = comment.id

    service = CommentService(db_session, user_id=user.id)
    await service.delete_comment(comment_id)

    # Verify the comment has deleted_at set
    await db_session.refresh(comment)
    assert comment.deleted_at is not None


@pytest.mark.asyncio
async def test_delete_comment_removes_from_list(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that deleted comment doesn't appear in list."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="To delete",
    )
    db_session.add(comment)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    await service.delete_comment(comment.id)

    comments = await service.get_comments(concept.id)
    assert len(comments) == 0


@pytest.mark.asyncio
async def test_delete_comment_not_owner(
    db_session: AsyncSession, concept: Concept, user: User, other_user: User
) -> None:
    """Test that users cannot delete others' comments."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="User's comment",
    )
    db_session.add(comment)
    await db_session.flush()

    # Service initialized with other_user trying to delete user's comment
    service = CommentService(db_session, user_id=other_user.id)

    with pytest.raises(NotCommentOwnerError):
        await service.delete_comment(comment.id)


@pytest.mark.asyncio
async def test_delete_comment_not_found(
    db_session: AsyncSession, user: User
) -> None:
    """Test deleting non-existent comment."""
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")
    service = CommentService(db_session, user_id=user.id)

    with pytest.raises(CommentNotFoundError):
        await service.delete_comment(fake_id)


@pytest.mark.asyncio
async def test_delete_already_deleted_comment(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that already deleted comment returns not found."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Already deleted",
        deleted_at=datetime.now(),
    )
    db_session.add(comment)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)

    with pytest.raises(CommentNotFoundError):
        await service.delete_comment(comment.id)

# ======== Resolve/Unresolve Comment Tests ========

@pytest.mark.asyncio
async def test_resolve_comment_happy_path(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test we can successfully resolve a top level comment."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="A top level comment",
    )
    db_session.add(comment)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    await service.resolve_comment(comment_id=comment.id)

    # Verify the comment has resolved_at and resolved_by have been set
    await db_session.refresh(comment)
    assert comment.resolved_at is not None
    assert comment.resolved_by == user.id

@pytest.mark.asyncio
async def test_unresolve_comment_happy_path(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test we can successfully unresolve a top level comment"""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="A top level comment",
        resolved_at=datetime.now(),
        resolved_by=user.id
    )

    db_session.add(comment)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    await service.unresolve_comment(comment_id=comment.id)

    # Verify resolution fields have been unset
    await db_session.refresh(comment)
    assert comment.resolved_at is None
    assert comment.resolved_by is None

@pytest.mark.asyncio
async def test_resolve_already_resolved_comment_does_not_update_fields(
    db_session: AsyncSession, concept: Concept, user: User, other_user: User
) -> None:
    """Test that resolving an already-resolved comment doesn't update resolution fields."""
    original_resolved_at = datetime(2024, 1, 1, 12, 0, 0)
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Already resolved comment",
        resolved_at=original_resolved_at,
        resolved_by=user.id
    )
    db_session.add(comment)
    await db_session.flush()

    # Try to resolve again with a different user
    service = CommentService(db_session, user_id=other_user.id)
    await service.resolve_comment(comment_id=comment.id)

    # Verify resolution fields remain unchanged
    await db_session.refresh(comment)
    assert comment.resolved_at == original_resolved_at
    assert comment.resolved_by == user.id  # Should still be the original user

@pytest.mark.asyncio
async def test_resolve_or_unresolve_comment_raises_error_if_not_top_level(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test an error is thrown if we attempt to resolve a comment that isn't top level."""
    parent = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="A top level comment",
    )

    db_session.add(parent)
    await db_session.flush()

    service = CommentService(db_session, user.id)
    reply_in = CommentCreate(content="Reply comment", parent_comment_id=parent.id)

    reply_comment = await service.create_comment(concept.id, reply_in)

    with pytest.raises(NotTopLevelCommentError):
        await service.resolve_comment(reply_comment.id)

    with pytest.raises(NotTopLevelCommentError):
        await service.unresolve_comment(reply_comment.id)

@pytest.mark.asyncio
async def test_resolve_or_unresolve_nonexistent_comment_returns_not_found(
    db_session: AsyncSession, user: User
) -> None:
    """Test resolve/unresolve a nonexistent comment returns not found"""
    service = CommentService(db_session, user_id=user.id)

    with pytest.raises(CommentNotFoundError):
        await service.resolve_comment(uuid.uuid7())

    with pytest.raises(CommentNotFoundError):
        await service.unresolve_comment(uuid.uuid7())

@pytest.mark.asyncio
async def test_resolve_or_unresolve_deleted_comment_returns_not_found(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test resolve/unresolve a deleted comment returns not found"""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Deleted comment",
        deleted_at=datetime.now()
    )
    db_session.add(comment)
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)

    with pytest.raises(CommentNotFoundError):
        await service.resolve_comment(comment.id)

    with pytest.raises(CommentNotFoundError):
        await service.unresolve_comment(comment.id)


# ============ Comment Threading Tests ============


@pytest.mark.asyncio
async def test_create_top_level_comment(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test creating a top-level comment with no parent."""
    service = CommentService(db_session, user_id=user.id)
    comment_in = CommentCreate(content="Top-level comment")

    comment = await service.create_comment(concept.id, comment_in)

    assert comment.parent_comment_id is None
    assert comment.content == "Top-level comment"


@pytest.mark.asyncio
async def test_create_reply_to_top_level_comment(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test creating a reply to a top-level comment."""
    # Create parent comment
    parent = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Parent comment",
    )
    db_session.add(parent)
    await db_session.flush()

    # Create reply
    service = CommentService(db_session, user_id=user.id)
    reply_in = CommentCreate(content="Reply comment", parent_comment_id=parent.id)

    reply = await service.create_comment(concept.id, reply_in)

    assert reply.parent_comment_id == parent.id
    assert reply.content == "Reply comment"
    assert reply.concept_id == concept.id


@pytest.mark.asyncio
async def test_reject_nested_reply(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that replies to replies are rejected (no nesting)."""
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

    # Try to create nested reply (should fail)
    service = CommentService(db_session, user_id=user.id)
    nested_reply_in = CommentCreate(
        content="Nested reply", parent_comment_id=first_reply.id
    )

    from taxonomy_builder.services.comment_service import InvalidParentCommentError

    with pytest.raises(InvalidParentCommentError) as exc_info:
        await service.create_comment(concept.id, nested_reply_in)

    assert "reply" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_reject_invalid_parent_comment_id(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that invalid parent_comment_id is rejected."""
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")
    service = CommentService(db_session, user_id=user.id)
    comment_in = CommentCreate(content="Test reply", parent_comment_id=fake_id)

    from taxonomy_builder.services.comment_service import InvalidParentCommentError

    with pytest.raises(InvalidParentCommentError):
        await service.create_comment(concept.id, comment_in)


@pytest.mark.asyncio
async def test_reject_deleted_parent_comment(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that replies to deleted comments are rejected."""
    # Create and delete parent comment
    parent = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Deleted parent",
        deleted_at=datetime.now(),
    )
    db_session.add(parent)
    await db_session.flush()

    # Try to reply to deleted comment
    service = CommentService(db_session, user_id=user.id)
    reply_in = CommentCreate(content="Reply to deleted", parent_comment_id=parent.id)

    from taxonomy_builder.services.comment_service import InvalidParentCommentError

    with pytest.raises(InvalidParentCommentError):
        await service.create_comment(concept.id, reply_in)
