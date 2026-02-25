import { useSignal } from "@preact/signals";
import { Badge, feedbackTypeLabel, statusVariant } from "./Badge";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { deleteFeedback } from "../../state/feedback";
import type { FeedbackRead } from "../../api/feedback";
import "./FeedbackCard.css";

interface FeedbackCardProps {
  feedback: FeedbackRead;
}

export function FeedbackCard({ feedback }: FeedbackCardProps) {
  const confirmOpen = useSignal(false);
  const deleting = useSignal(false);

  async function handleDelete() {
    try {
      deleting.value = true;
      await deleteFeedback(feedback.id);
    } catch {
      // Error handling deferred — card remains if delete fails
    } finally {
      deleting.value = false;
      confirmOpen.value = false;
    }
  }

  const date = new Date(feedback.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div class="feedback-card">
      <div class="feedback-card__header">
        <span class="feedback-card__date">{date}</span>
        <Badge label={feedbackTypeLabel(feedback.feedback_type)} />
        <Badge
          label={feedback.status}
          variant={statusVariant(feedback.status)}
        />
      </div>
      <div class="feedback-card__content">{feedback.content}</div>

      {feedback.response && (
        <div class="feedback-card__response">
          <div class="feedback-card__response-author">
            {feedback.response.author} responded
          </div>
          <div class="feedback-card__response-content">
            {feedback.response.content}
          </div>
        </div>
      )}

      {feedback.can_delete && (
        <div class="feedback-card__actions">
          <button
            class="feedback-card__delete-btn"
            onClick={() => (confirmOpen.value = true)}
            disabled={deleting.value}
          >
            {deleting.value ? "Deleting..." : "Delete"}
          </button>
        </div>
      )}

      <ConfirmDialog
        open={confirmOpen.value}
        title="Delete this feedback?"
        message="This will permanently remove this feedback item."
        onConfirm={handleDelete}
        onCancel={() => (confirmOpen.value = false)}
      />
    </div>
  );
}
