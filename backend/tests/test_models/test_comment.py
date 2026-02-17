"""Tests for the Comment model."""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.comment import Comment
from tests.factories import CommentFactory, ConceptFactory, UserFactory, flush


@pytest.mark.asyncio
async def test_create_comment(db_session: AsyncSession) -> None:
    """Test creating a comment."""
    concept = await flush(db_session, ConceptFactory.create())
    comment = await flush(
        db_session,
        CommentFactory.create(concept_id=concept.id, content="This is a test comment"),
    )

    assert comment.id is not None
    assert isinstance(comment.id, UUID)
    assert comment.concept_id == concept.id
    assert comment.user_id is not None
    assert comment.content == "This is a test comment"
    assert comment.created_at is not None
    assert comment.updated_at is not None
    assert comment.deleted_at is None


@pytest.mark.asyncio
async def test_comment_id_is_uuidv7(db_session: AsyncSession) -> None:
    """Test that comment IDs are UUIDv7."""
    concept = await flush(db_session, ConceptFactory.create())
    comment = await flush(
        db_session, CommentFactory.create(concept_id=concept.id)
    )

    assert comment.id.version == 7


@pytest.mark.asyncio
async def test_comment_soft_delete(db_session: AsyncSession) -> None:
    """Test soft deleting a comment by setting deleted_at."""
    concept = await flush(db_session, ConceptFactory.create())
    comment = await flush(
        db_session, CommentFactory.create(concept_id=concept.id, content="To be deleted")
    )

    # Soft delete
    comment.deleted_at = datetime.now()
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.deleted_at is not None


@pytest.mark.asyncio
async def test_comment_user_relationship(db_session: AsyncSession) -> None:
    """Test that comment has user relationship loaded."""
    concept = await flush(db_session, ConceptFactory.create())
    user = UserFactory.create(display_name="Test User")
    comment = await flush(
        db_session, CommentFactory.create(concept_id=concept.id, user=user)
    )

    assert comment.user is not None
    assert comment.user.id == user.id
    assert comment.user.display_name == "Test User"


@pytest.mark.asyncio
async def test_comment_content_required(db_session: AsyncSession) -> None:
    """Test that content is required."""
    from sqlalchemy.exc import IntegrityError

    concept = await flush(db_session, ConceptFactory.create())
    user = await flush(db_session, UserFactory.create())

    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content=None,  # type: ignore[arg-type]
    )
    db_session.add(comment)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_cascade_delete_with_concept(db_session: AsyncSession) -> None:
    """Test that comments are deleted when concept is deleted."""
    concept = await flush(db_session, ConceptFactory.create())
    comment = await flush(
        db_session, CommentFactory.create(concept_id=concept.id)
    )
    comment_id = comment.id

    await db_session.delete(concept)
    await db_session.flush()

    result = await db_session.execute(select(Comment).where(Comment.id == comment_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cascade_delete_with_user(db_session: AsyncSession) -> None:
    """Test that comments are deleted when user is deleted."""
    concept = await flush(db_session, ConceptFactory.create())
    user = UserFactory.create()
    comment = await flush(
        db_session, CommentFactory.create(concept_id=concept.id, user=user)
    )
    comment_id = comment.id

    await db_session.delete(user)
    await db_session.flush()

    result = await db_session.execute(select(Comment).where(Comment.id == comment_id))
    assert result.scalar_one_or_none() is None
