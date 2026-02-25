import { useSignal } from "@preact/signals";
import { getFeedbackTypes } from "../../constants/feedback-types";
import { submitFeedback } from "../../state/feedback";
import "./FeedbackForm.css";

interface FeedbackFormProps {
  entityType: string;
  entityId: string;
  entityLabel: string;
}

export function FeedbackForm({
  entityType,
  entityId,
  entityLabel,
}: FeedbackFormProps) {
  const types = getFeedbackTypes(entityType);
  const selectedType = useSignal(types[0]?.value ?? "");
  const content = useSignal("");
  const submitting = useSignal(false);
  const success = useSignal(false);
  const error = useSignal<string | null>(null);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    const trimmed = content.value.trim();
    if (!trimmed || !selectedType.value) return;

    try {
      submitting.value = true;
      error.value = null;
      await submitFeedback(
        entityType,
        entityId,
        entityLabel,
        selectedType.value,
        trimmed
      );
      content.value = "";
      selectedType.value = types[0]?.value ?? "";
      success.value = true;
      setTimeout(() => (success.value = false), 3000);
    } catch (e) {
      error.value =
        e instanceof Error ? e.message : "Failed to submit feedback";
    } finally {
      submitting.value = false;
    }
  }

  const charCount = content.value.length;
  const maxChars = 10000;

  return (
    <form class="feedback-form" onSubmit={handleSubmit}>
      {success.value && (
        <div class="feedback-form__success">Feedback submitted</div>
      )}
      {error.value && (
        <div class="feedback-form__error">{error.value}</div>
      )}
      <div class="feedback-form__field">
        <label class="feedback-form__label">Feedback type</label>
        <select
          class="feedback-form__select"
          value={selectedType.value}
          onChange={(e) =>
            (selectedType.value = (e.target as HTMLSelectElement).value)
          }
        >
          {types.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>
      <div class="feedback-form__field">
        <label class="feedback-form__label">Your feedback</label>
        <textarea
          class="feedback-form__textarea"
          value={content.value}
          onInput={(e) =>
            (content.value = (e.target as HTMLTextAreaElement).value)
          }
          maxLength={maxChars}
          placeholder="Describe your feedback..."
        />
      </div>
      <div class="feedback-form__footer">
        <span class="feedback-form__char-count">
          {charCount} / {maxChars}
        </span>
        <button
          type="submit"
          class="feedback-form__submit"
          disabled={submitting.value || !content.value.trim()}
        >
          {submitting.value ? "Submitting..." : "Submit"}
        </button>
      </div>
    </form>
  );
}
