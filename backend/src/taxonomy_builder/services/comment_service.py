"""Comment service for business logic."""

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.comment import Comment
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.schemas.comment import CommentCreate


class ConceptNotFoundError(Exception):
    """Raised when a concept is not found."""

    def __init__(self, concept_id: UUID) -> None:
        self.concept_id = concept_id
        super().__init__(f"Concept with id '{concept_id}' not found")


class CommentNotFoundError(Exception):
    """Raised when a comment is not found."""

    def __init__(self, comment_id: UUID) -> None:
        self.comment_id = comment_id
        super().__init__(f"Comment with id '{comment_id}' not found")


class NotCommentOwnerError(Exception):
    """Raised when user tries to delete someone else's comment."""

    def __init__(self, comment_id: UUID, user_id: UUID) -> None:
        self.comment_id = comment_id
        self.user_id = user_id
        super().__init__("Cannot delete another user's comment")

class NotTopLevelCommentError(Exception):
    """
    Raised when user tries perform an action that is restricted
    to top-level comments on a reply comment.
    """

    def __init__(self, comment_id: UUID, action: str) -> None:
        self.comment_id = comment_id
        super().__init__(f"'{action}' can only be performed on top-level comments")


class InvalidParentCommentError(Exception):
    """Raised when parent comment is invalid for threading."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CommentService:
    """Service for managing comments on concepts."""

    def __init__(self, db: AsyncSession, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    async def _get_concept(self, concept_id: UUID) -> Concept:
        """Get a concept by ID or raise ConceptNotFoundError."""
        result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        concept = result.scalar_one_or_none()
        if concept is None:
            raise ConceptNotFoundError(concept_id)
        return concept

    async def _get_comment(self, comment_id: UUID) -> Comment:
        """Get a non-deleted comment by ID with user loaded."""
        result = await self.db.execute(
            select(Comment)
            .where(Comment.id == comment_id)
            .where(Comment.deleted_at.is_(None))
            .options(selectinload(Comment.user))
        )
        comment = result.scalar_one_or_none()
        if comment is None:
            raise CommentNotFoundError(comment_id)
        return comment

    async def _validate_parent_comment(self, parent_comment_id: UUID) -> Comment:
        """Validate that parent comment exists and is a top-level comment.

        Raises:
            InvalidParentCommentError: If parent doesn't exist, is deleted, or is itself a reply.
        """
        # Fetch parent comment (will raise CommentNotFoundError if not found or deleted)
        try:
            parent = await self._get_comment(parent_comment_id)
        except CommentNotFoundError:
            raise InvalidParentCommentError(
                f"Parent comment with id '{parent_comment_id}' not found or was deleted"
            )

        # Ensure parent is a top-level comment (no nested replies allowed)
        if parent.parent_comment_id is not None:
            raise InvalidParentCommentError(
                "Cannot reply to a reply. Replies are only allowed on top-level comments."
            )

        return parent

    async def get_comments(self, concept_id: UUID) -> list[Comment]:
        """Get all non-deleted comments for a concept, ordered by created_at.

        Args:
            concept_id: The ID of the concept to list comments for
        """
        await self._get_concept(concept_id)

        query = (
            select(Comment)
            .where(Comment.concept_id == concept_id)
            .where(Comment.deleted_at.is_(None))
            .options(selectinload(Comment.user))
            .order_by(Comment.created_at)
        )

        result = await self.db.execute(query)
        all_comments = list(result.scalars().all())

        return all_comments

    async def list_comment_threads(
            self, concept_id: UUID, resolved: bool | None = None
    ) -> tuple[list[Comment], dict[UUID, list[Comment]]]:
        """List comment threads for a concept, ordered by created_at

        Args:
            concept_id: The ID of the concept to list comments for
            resolved: If True, return only resolved comments.
                      If False, return only unresolved comments.
                      If None (default), return all comments.
        """
        all_comments = await self.get_comments(concept_id=concept_id)

        def _should_include(comment: Comment):
            """Helper function for comment filtering."""
            if resolved is None:
                return True

            if resolved and comment.resolved_at:
                return True

            if not resolved and not comment.resolved_at:
                return True

            return False

        # Separate top-level comments from replies
        top_level = []
        replies_by_parent = defaultdict(list)

        for comment in all_comments:
            if comment.parent_comment_id is None:
                if _should_include(comment):
                    top_level.append(comment)
            else:
                replies_by_parent[comment.parent_comment_id].append(comment)

        if resolved is None:
            return top_level, replies_by_parent

        present_top_level_comments = set(comment.id for comment in top_level)
        filtered_replies_by_parent = {parent_id: replies for parent_id, replies in replies_by_parent.items() if parent_id in present_top_level_comments}

        return top_level, filtered_replies_by_parent









    async def create_comment(
        self, concept_id: UUID, comment_in: CommentCreate
    ) -> Comment:
        """Create a new comment on a concept."""
        await self._get_concept(concept_id)

        # Validate parent comment if provided
        if comment_in.parent_comment_id is not None:
            await self._validate_parent_comment(comment_in.parent_comment_id)

        comment = Comment(
            concept_id=concept_id,
            user_id=self.user_id,
            content=comment_in.content,
            parent_comment_id=comment_in.parent_comment_id,
        )
        self.db.add(comment)
        await self.db.flush()

        # Re-fetch with user relationship loaded
        return await self._get_comment(comment.id)

    async def delete_comment(self, comment_id: UUID) -> None:
        """Soft-delete a comment (only if user owns it)."""
        comment = await self._get_comment(comment_id)

        if comment.user_id != self.user_id:
            raise NotCommentOwnerError(comment_id, self.user_id)

        comment.deleted_at = datetime.now()
        await self.db.flush()

    async def resolve_comment(self, comment_id: UUID) -> None:
        """
        Resolve a comment (only if it is a top level comment).

        If the comment is already resolved, do not update the resolution fields.
        """
        comment = await self._get_comment(comment_id)

        if comment.parent_comment_id:
            raise NotTopLevelCommentError(comment_id=comment.id, action="resolve")

        # Only set resolution fields if not already resolved
        if comment.resolved_at is None:
            comment.resolved_at = datetime.now()
            comment.resolved_by = self.user_id

        await self.db.flush()

    async def unresolve_comment(self, comment_id: UUID) -> None:
        """Unresolve a comment (only if it is a top level comment)."""
        comment = await self._get_comment(comment_id)

        if comment.parent_comment_id:
            raise NotTopLevelCommentError(comment_id=comment.id, action="unresolve")

        comment.resolved_at = None
        comment.resolved_by = None

        await self.db.flush()
