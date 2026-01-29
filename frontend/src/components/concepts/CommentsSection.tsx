import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { commentsApi } from "../../api/comments";
import { ApiError } from "../../api/client";
import type { Comment } from "../../types/models";
import "./CommentsSection.css";

interface CommentsSectionProps {
  conceptId: string;
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function CommentsSection({ conceptId }: CommentsSectionProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  async function loadComments() {
    try {
      setError(null);
      const data = await commentsApi.listForConcept(conceptId);
      setComments(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load comments");
      }
    }
  }

  useEffect(() => {
    if (isExpanded) {
      loadComments();
    }
  }, [conceptId, isExpanded]);

  // Reset expansion when concept changes
  useEffect(() => {
    setIsExpanded(false);
    setComments([]);
    setNewComment("");
    setError(null);
  }, [conceptId]);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (!newComment.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await commentsApi.create(conceptId, { content: newComment.trim() });
      setNewComment("");
      await loadComments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to add comment");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(commentId: string) {
    setLoading(true);
    try {
      await commentsApi.delete(commentId);
      await loadComments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to delete comment");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div class="comments-section">
      <button
        class="comments-section__toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        type="button"
      >
        <span class={`comments-section__arrow ${isExpanded ? "comments-section__arrow--expanded" : ""}`}>
          &#9658;
        </span>
        <span class="comments-section__toggle-text">
          Comments {comments.length > 0 && `(${comments.length})`}
        </span>
      </button>

      {isExpanded && (
        <div class="comments-section__content">
          {error && <div class="comments-section__error">{error}</div>}

          {comments.length > 0 ? (
            <div class="comments-section__list">
              {comments.map((comment) => (
                <div key={comment.id} class="comments-section__comment">
                  <div class="comments-section__comment-header">
                    <span class="comments-section__author">
                      {comment.user.display_name}
                    </span>
                    <span class="comments-section__time">
                      {formatRelativeTime(comment.created_at)}
                    </span>
                    {comment.can_delete && (
                      <button
                        class="comments-section__delete"
                        onClick={() => handleDelete(comment.id)}
                        disabled={loading}
                        title="Delete comment"
                        type="button"
                      >
                        &times;
                      </button>
                    )}
                  </div>
                  <p class="comments-section__comment-content">{comment.content}</p>
                </div>
              ))}
            </div>
          ) : (
            <p class="comments-section__empty">No comments yet</p>
          )}

          <form class="comments-section__form" onSubmit={handleSubmit}>
            <textarea
              class="comments-section__input"
              value={newComment}
              onInput={(e) => setNewComment((e.target as HTMLTextAreaElement).value)}
              placeholder="Add a comment..."
              rows={2}
              disabled={loading}
            />
            <Button
              type="submit"
              size="sm"
              disabled={loading || !newComment.trim()}
            >
              {loading ? "Posting..." : "Post"}
            </Button>
          </form>
        </div>
      )}
    </div>
  );
}
