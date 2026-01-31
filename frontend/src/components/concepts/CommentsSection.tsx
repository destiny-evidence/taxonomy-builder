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
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState("");
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

  // Load comments on mount and when concept changes
  useEffect(() => {
    loadComments();
    setIsExpanded(false);
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

  async function handleReplySubmit(e: Event, parentId: string) {
    e.preventDefault();
    if (!replyContent.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await commentsApi.create(conceptId, {
        content: replyContent.trim(),
        parent_comment_id: parentId,
      });
      setReplyContent("");
      setReplyingTo(null);
      await loadComments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to post reply");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleCancelReply() {
    setReplyingTo(null);
    setReplyContent("");
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
                <div key={comment.id} class="comments-section__thread">
                  {/* Top-level comment */}
                  <div class="comments-section__comment">
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

                  {/* Replies */}
                  {comment.replies && comment.replies.length > 0 && (
                    <div class="comments-section__replies">
                      {comment.replies.map((reply) => (
                        <div key={reply.id} class="comments-section__comment comments-section__reply">
                          <div class="comments-section__comment-header">
                            <span class="comments-section__author">
                              {reply.user.display_name}
                            </span>
                            <span class="comments-section__time">
                              {formatRelativeTime(reply.created_at)}
                            </span>
                            {reply.can_delete && (
                              <button
                                class="comments-section__delete"
                                onClick={() => handleDelete(reply.id)}
                                disabled={loading}
                                title="Delete reply"
                                type="button"
                              >
                                &times;
                              </button>
                            )}
                          </div>
                          <p class="comments-section__comment-content">{reply.content}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Inline reply form */}
                  {replyingTo === comment.id && (
                    <form
                      class="comments-section__reply-form"
                      onSubmit={(e) => handleReplySubmit(e, comment.id)}
                    >
                      <div class="comments-section__reply-indicator">
                        Replying in thread
                      </div>
                      <textarea
                        class="comments-section__input"
                        value={replyContent}
                        onInput={(e) => setReplyContent((e.target as HTMLTextAreaElement).value)}
                        placeholder="Write a reply..."
                        rows={2}
                        disabled={loading}
                        autoFocus
                      />
                      <div class="comments-section__reply-actions">
                        <Button
                          type="submit"
                          size="sm"
                          disabled={loading || !replyContent.trim()}
                        >
                          {loading ? "Posting..." : "Reply"}
                        </Button>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={handleCancelReply}
                          disabled={loading}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  )}

                  {/* Reply button - at bottom of thread */}
                  {!replyingTo && (
                    <button
                      class="comments-section__reply-btn"
                      onClick={() => setReplyingTo(comment.id)}
                      disabled={loading}
                      type="button"
                    >
                      Reply
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p class="comments-section__empty">No comments yet</p>
          )}

          {/* Hide main comment form when replying */}
          {!replyingTo && (
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
          )}
        </div>
      )}
    </div>
  );
}
