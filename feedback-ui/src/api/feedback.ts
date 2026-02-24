import { api } from "./client";

export function postFeedback(
  projectId: string,
  body: string
): Promise<{ status: string }> {
  return api.post(`/feedback/ui/${projectId}`, { body });
}
