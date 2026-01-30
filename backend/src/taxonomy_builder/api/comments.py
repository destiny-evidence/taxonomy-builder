"""Comment API endpoints."""

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
    NotCommentOwnerError,
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
) -> list[dict]:
    """List all comments for a concept."""
    try:
        comments = await service.list_comments(concept_id)
        return [
            {
                "id": comment.id,
                "concept_id": comment.concept_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "user": {
                    "id": comment.user.id,
                    "display_name": comment.user.display_name,
                },
                "can_delete": comment.user_id == service.user_id,
            }
            for comment in comments
        ]
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
