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
  const [filter, setFilter] = useState<"all" | "unresolved" | "resolved">("unresolved");

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

  const filteredComments = comments
    .filter((comment) => {
      if (filter === "all") return true;
      if (filter === "resolved") return comment.resolved_at;
      return !comment.resolved_at;
    })
    .sort((a, b) => {
      if (a.resolved_at && !b.resolved_at) return 1;
      if (!a.resolved_at && b.resolved_at) return -1;
      return 0;
    });

  // Reset UI state and load comments when concept changes
  useEffect(() => {
    setIsExpanded(false);
    setNewComment("");
    setError(null);
    loadComments();
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

  async function handleResolve(commentId: string) {
    setLoading(true);
    try {
      await commentsApi.resolve(commentId);
      await loadComments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to resolve comment");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleUnresolve(commentId: string) {
    setLoading(true);
    try {
      await commentsApi.unresolve(commentId);
      await loadComments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to unresolve comment");
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

          <div class="comments-section__filter">
            {(["all", "unresolved", "resolved"] as const).map((option) => (
              <button
                key={option}
                type="button"
                class={`comments-section__filter-option ${filter === option ? "comments-section__filter-option--active" : ""}`}
                onClick={() => setFilter(option)}
              >
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </button>
            ))}
          </div>

          {filteredComments.length > 0 ? (
            <div class="comments-section__list">
              {filteredComments.map((comment) => (
                <div key={comment.id} class={`comments-section__thread ${comment.resolved_at ? "comments-section__thread--resolved" : ""}`}>
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

                  {/* Reply and Resolve buttons - at bottom of thread */}
                  {!replyingTo && (
                    <div class="comments-section__thread-actions">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setReplyingTo(comment.id)}
                        disabled={loading}
                      >
                        Reply
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => comment.resolved_at ? handleUnresolve(comment.id) : handleResolve(comment.id)}
                        disabled={loading}
                      >
                        {comment.resolved_at ? "Unresolve" : "Resolve"}
                      </Button>
                      {comment.resolver && (
                        <span class="comments-section__resolved-info">
                          Resolved by {comment.resolver.display_name} {formatRelativeTime(comment.resolved_at!)}
                        </span>
                      )}
                    </div>
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
