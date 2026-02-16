"""Comment API endpoints."""

from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import (
    AuthenticatedUser,
    get_current_user,
)
from taxonomy_builder.database import get_db
from taxonomy_builder.schemas.comment import CommentCreate, CommentRead
from taxonomy_builder.services.comment_service import (
    CommentNotFoundError,
    CommentService,
    ConceptNotFoundError,
    InvalidParentCommentError,
    NotCommentOwnerError,
    NotTopLevelCommentError,
)

# Router for concept-scoped comment operations
concept_comments_router = APIRouter(prefix="/api/concepts", tags=["comments"])

# Router for direct comment operations
comments_router = APIRouter(prefix="/api/comments", tags=["comments"])


def get_comment_service(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CommentService:
    """Dependency that provides a CommentService with user context."""
    return CommentService(db, user_id=current_user.user.id)


@concept_comments_router.get(
    "/{concept_id}/comments", response_model=list[CommentRead]
)
async def list_comments(
    concept_id: UUID,
    service: CommentService = Depends(get_comment_service),
    resolved: bool | None = None,
) -> list[dict]:
    """List all comments for a concept, grouped by thread.

    Args:
        concept_id: The ID of the concept to list comments for
        resolved: If True, only show resolved comments.
                  If False, only show unresolved comments.
                  If None (default), show all comments.
    """
    try:
        # Helper function to format a comment
        def format_comment(comment):
            return {
                "id": comment.id,
                "concept_id": comment.concept_id,
                "user_id": comment.user_id,
                "parent_comment_id": comment.parent_comment_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "resolved_at": comment.resolved_at,
                "resolved_by": comment.resolved_by,
                "user": {
                    "id": comment.user.id,
                    "display_name": comment.user.display_name,
                },
                "can_delete": comment.user_id == service.user_id,
                "replies": [],
            }

        top_level, replies_by_parent = await service.list_comment_threads(
            concept_id=concept_id, resolved=resolved
        )

        # Build threaded structure
        threads = []
        for parent in top_level:
            parent_dict = format_comment(parent)
            # Add replies to parent
            parent_dict["replies"] = [
                format_comment(reply) for reply in replies_by_parent.get(parent.id, [])
            ]
            threads.append(parent_dict)

        return threads
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@concept_comments_router.post(
    "/{concept_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    concept_id: UUID,
    comment_in: CommentCreate,
    service: CommentService = Depends(get_comment_service),
) -> dict:
    """Create a new comment on a concept."""
    try:
        comment = await service.create_comment(concept_id, comment_in)
        return {
            "id": comment.id,
            "concept_id": comment.concept_id,
            "user_id": comment.user_id,
            "parent_comment_id": comment.parent_comment_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "user": {
                "id": comment.user.id,
                "display_name": comment.user.display_name,
            },
            "can_delete": True,  # User just created it, so they can delete
        }
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidParentCommentError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@comments_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    service: CommentService = Depends(get_comment_service),
) -> None:
    """Delete a comment (soft delete, only if user owns it)."""
    try:
        await service.delete_comment(comment_id)
    except CommentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotCommentOwnerError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@comments_router.post("/{comment_id}/resolve", status_code=status.HTTP_204_NO_CONTENT)
async def resolve_comment(
    comment_id: UUID,
    service: CommentService = Depends(get_comment_service)
) -> None:
    """Resolve a comment (only if it is a top level comment)."""
    try:
        await service.resolve_comment(comment_id)
    except CommentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotTopLevelCommentError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@comments_router.post("/{comment_id}/unresolve", status_code=status.HTTP_204_NO_CONTENT)
async def unresolve_comment(
    comment_id: UUID,
    service: CommentService = Depends(get_comment_service)
) -> None:
    """Unresolve a comment (only if it is a top level comment)."""
    try:
        await service.unresolve_comment(comment_id)
    except CommentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotTopLevelCommentError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
