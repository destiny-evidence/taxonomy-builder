"""Tests for the CommentService."""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.comment import Comment
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.user import User
from taxonomy_builder.schemas.comment import CommentCreate
from taxonomy_builder.services.comment_service import (
    CommentNotFoundError,
    CommentService,
    ConceptNotFoundError,
    NotCommentOwnerError,
)
from tests.factories import (
    CommentFactory,
    ConceptFactory,
    ConceptSchemeFactory,
    UserFactory,
    flush,
)


@pytest.fixture
async def scheme(db_session: AsyncSession) -> ConceptScheme:
    """Create a concept scheme for testing."""
    return await flush(
        db_session,
        ConceptSchemeFactory.create(
            title="Test Scheme",
            uri="http://example.org/concepts",
        ),
    )


@pytest.fixture
async def concept(db_session: AsyncSession, scheme: ConceptScheme) -> Concept:
    """Create a concept for testing."""
    return await flush(
        db_session,
        ConceptFactory.create(scheme=scheme, pref_label="Test Concept"),
    )


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a user for testing."""
    return await flush(
        db_session,
        UserFactory.create(
            keycloak_user_id="test-keycloak-id",
            email="test@example.com",
            display_name="Test User",
        ),
    )


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create another user for testing."""
    return await flush(
        db_session,
        UserFactory.create(
            keycloak_user_id="other-keycloak-id",
            email="other@example.com",
            display_name="Other User",
        ),
    )


# ============ List Comments Tests ============


@pytest.mark.asyncio
async def test_list_comments_empty(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test listing comments when none exist."""
    service = CommentService(db_session, user_id=user.id)
    comments = await service.list_comments(concept.id)
    assert comments == []


@pytest.mark.asyncio
async def test_list_comments(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test listing comments for a concept."""
    CommentFactory.create(
        concept_id=concept.id,
        user=user,
        content="Test comment",
    )
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    comments = await service.list_comments(concept.id)

    assert len(comments) == 1
    assert comments[0].content == "Test comment"
    assert comments[0].user.display_name == "Test User"


@pytest.mark.asyncio
async def test_list_comments_excludes_deleted(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that soft-deleted comments are excluded."""
    CommentFactory.create(
        concept_id=concept.id,
        user=user,
        content="Active comment",
    )
    CommentFactory.create(
        concept_id=concept.id,
        user=user,
        content="Deleted comment",
        deleted_at=datetime.now(),
    )
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    comments = await service.list_comments(concept.id)

    assert len(comments) == 1
    assert comments[0].content == "Active comment"


@pytest.mark.asyncio
async def test_list_comments_ordered_by_created_at(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test comments are ordered by created_at ascending (oldest first)."""
    CommentFactory.create(
        concept_id=concept.id,
        user=user,
        content="First comment",
    )
    await db_session.flush()

    CommentFactory.create(
        concept_id=concept.id,
        user=user,
        content="Second comment",
    )
    await db_session.flush()

    service = CommentService(db_session, user_id=user.id)
    comments = await service.list_comments(concept.id)

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
        await service.list_comments(fake_id)

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
    comment = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="To delete",
        ),
    )
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
    comment = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="To delete",
        ),
    )

    service = CommentService(db_session, user_id=user.id)
    await service.delete_comment(comment.id)

    comments = await service.list_comments(concept.id)
    assert len(comments) == 0


@pytest.mark.asyncio
async def test_delete_comment_not_owner(
    db_session: AsyncSession, concept: Concept, user: User, other_user: User
) -> None:
    """Test that users cannot delete others' comments."""
    comment = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="User's comment",
        ),
    )

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
    comment = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="Already deleted",
            deleted_at=datetime.now(),
        ),
    )

    service = CommentService(db_session, user_id=user.id)

    with pytest.raises(CommentNotFoundError):
        await service.delete_comment(comment.id)


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
    parent = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="Parent comment",
        ),
    )

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
    parent = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="Parent comment",
        ),
    )

    # Create first reply
    first_reply = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="First reply",
            parent_comment_id=parent.id,
        ),
    )

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
    parent = await flush(
        db_session,
        CommentFactory.create(
            concept_id=concept.id,
            user=user,
            content="Deleted parent",
            deleted_at=datetime.now(),
        ),
    )

    # Try to reply to deleted comment
    service = CommentService(db_session, user_id=user.id)
    reply_in = CommentCreate(content="Reply to deleted", parent_comment_id=parent.id)

    from taxonomy_builder.services.comment_service import InvalidParentCommentError

    with pytest.raises(InvalidParentCommentError):
        await service.create_comment(concept.id, reply_in)
