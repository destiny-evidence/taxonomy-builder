import { api } from "./client";

export interface FeedbackItem {
  id: string;
  project_id: string;
  body: string;
  user_id: string | null;
  created_at: string;
}

export function getFeedback(projectId: string): Promise<FeedbackItem[]> {
  return api.get(`/feedback/ui/${projectId}`);
}

export function postFeedback(
  projectId: string,
  body: string
): Promise<{ status: string }> {
  return api.post(`/feedback/ui/${projectId}`, { body });
}

export function deleteFeedback(projectId: string): Promise<void> {
  return api.delete(`/feedback/ui/${projectId}`);
}
