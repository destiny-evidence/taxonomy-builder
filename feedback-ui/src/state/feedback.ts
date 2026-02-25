import { computed, signal } from "@preact/signals";
import { feedbackApi, type FeedbackRead } from "../api/feedback";
import { currentProjectId, selectedVersion } from "./vocabulary";
import { route } from "../router";

/** All own feedback for the current project. */
export const ownFeedback = signal<FeedbackRead[]>([]);

export const feedbackLoading = signal(false);
export const feedbackError = signal<string | null>(null);

/** Feedback for the currently routed entity + version. */
export const currentEntityFeedback = computed(() => {
  const { entityId } = route.value;
  const version = selectedVersion.value;
  if (!entityId || !version) return [];
  return ownFeedback.value.filter(
    (fb) => fb.entity_id === entityId && fb.snapshot_version === version
  );
});

/** Count of own feedback for a given entity + version. */
export function feedbackCountForEntity(
  entityId: string,
  version: string
): number {
  return ownFeedback.value.filter(
    (fb) => fb.entity_id === entityId && fb.snapshot_version === version
  ).length;
}

/** Load all own feedback for the current project. */
export async function loadOwnFeedback(): Promise<void> {
  const projectId = currentProjectId.value;
  if (!projectId) return;

  try {
    feedbackLoading.value = true;
    feedbackError.value = null;
    ownFeedback.value = await feedbackApi.listMine(projectId);
  } catch (e) {
    feedbackError.value =
      e instanceof Error ? e.message : "Failed to load feedback";
  } finally {
    feedbackLoading.value = false;
  }
}

/** Submit new feedback and add to local state. */
export async function submitFeedback(
  entityType: string,
  entityId: string,
  entityLabel: string,
  feedbackType: string,
  content: string
): Promise<FeedbackRead> {
  const projectId = currentProjectId.value;
  const version = selectedVersion.value;
  if (!projectId || !version) {
    throw new Error("No project or version selected");
  }

  const created = await feedbackApi.create(projectId, {
    snapshot_version: version,
    entity_type: entityType,
    entity_id: entityId,
    entity_label: entityLabel,
    feedback_type: feedbackType,
    content,
  });

  ownFeedback.value = [created, ...ownFeedback.value];
  return created;
}

/** Delete own feedback and remove from local state. */
export async function deleteFeedback(feedbackId: string): Promise<void> {
  await feedbackApi.deleteOwn(feedbackId);
  ownFeedback.value = ownFeedback.value.filter((fb) => fb.id !== feedbackId);
}
