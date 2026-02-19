"""Tests for the Comment model."""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
async def resolver_user(db_session: AsyncSession) -> User:
    """Create a resolver user for testing resolutions."""
    user = User(
        keycloak_user_id="resolver-keycloak-id",
        email="resolver@example.com",
        display_name="Resolver User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_comment(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test creating a comment."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="This is a test comment",
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.id is not None
    assert isinstance(comment.id, UUID)
    assert comment.concept_id == concept.id
    assert comment.user_id == user.id
    assert comment.content == "This is a test comment"
    assert comment.created_at is not None
    assert comment.updated_at is not None
    assert comment.deleted_at is None


@pytest.mark.asyncio
async def test_comment_id_is_uuidv7(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that comment IDs are UUIDv7."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="UUID test",
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.id.version == 7


@pytest.mark.asyncio
async def test_comment_soft_delete(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test soft deleting a comment by setting deleted_at."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="To be deleted",
    )
    db_session.add(comment)
    await db_session.flush()

    # Soft delete
    comment.deleted_at = datetime.now()
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.deleted_at is not None


@pytest.mark.asyncio
async def test_comment_user_relationship(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that comment has user relationship loaded."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Relationship test",
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.user is not None
    assert comment.user.id == user.id
    assert comment.user.display_name == "Test User"


@pytest.mark.asyncio
async def test_comment_content_required(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that content is required."""
    from sqlalchemy.exc import IntegrityError

    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content=None,  # type: ignore[arg-type]
    )
    db_session.add(comment)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_cascade_delete_with_concept(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that comments are deleted when concept is deleted."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="To be cascade deleted",
    )
    db_session.add(comment)
    await db_session.flush()
    comment_id = comment.id

    await db_session.delete(concept)
    await db_session.flush()

    result = await db_session.execute(select(Comment).where(Comment.id == comment_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cascade_delete_with_user(
    db_session: AsyncSession, concept: Concept, user: User
) -> None:
    """Test that comments are deleted when user is deleted."""
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="To be cascade deleted with user",
    )
    db_session.add(comment)
    await db_session.flush()
    comment_id = comment.id

    await db_session.delete(user)
    await db_session.flush()

    result = await db_session.execute(select(Comment).where(Comment.id == comment_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_add_resolution_to_parent_comment(
    db_session: AsyncSession, concept: Concept, user: User, resolver_user: User
) -> None:
    """Test adding a resolution to a parent comment."""
    # Create a top-level comment (no parent_comment_id)
    top_level_comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="This is a top-level comment",
    )
    db_session.add(top_level_comment)
    await db_session.flush()
    await db_session.refresh(top_level_comment)

    assert top_level_comment.parent_comment_id is None
    assert top_level_comment.resolved_at is None
    assert top_level_comment.resolved_by is None

    # Add a resolution to the top-level comment
    top_level_comment.resolved_at = datetime.now()
    top_level_comment.resolved_by = resolver_user.id
    await db_session.flush()
    await db_session.refresh(top_level_comment)

    assert top_level_comment.resolved_at is not None
    assert isinstance(top_level_comment.resolved_at, datetime)
    assert top_level_comment.resolved_by == resolver_user.id


@pytest.mark.asyncio
async def test_remove_resolution_from_comment(
    db_session: AsyncSession, concept: Concept, user: User, resolver_user: User
) -> None:
    """Test removing a resolution from a comment."""
    # Create a parent comment
    comment = Comment(
        concept_id=concept.id,
        user_id=user.id,
        content="Comment with resolution",
        resolved_at=datetime.now(),
        resolved_by=resolver_user.id
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.resolved_at is not None
    assert comment.resolved_by == resolver_user.id

    # Remove the resolution by setting fields to None
    comment.resolved_at = None
    comment.resolved_by = None
    await db_session.flush()
    await db_session.refresh(comment)

    # Verify the resolution has been removed
    assert comment.resolved_at is None
    assert comment.resolved_by is None


