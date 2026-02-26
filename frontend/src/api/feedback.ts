import { api } from "./client";
import type { FeedbackManagerRead } from "../types/models";

export interface FeedbackListParams {
  status?: string;
  entity_type?: string;
  feedback_type?: string;
  q?: string;
}

export const feedbackManagerApi = {
  listAll: (projectId: string, params?: FeedbackListParams) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.entity_type) query.set("entity_type", params.entity_type);
    if (params?.feedback_type) query.set("feedback_type", params.feedback_type);
    if (params?.q) query.set("q", params.q);
    const qs = query.toString();
    return api.get<FeedbackManagerRead[]>(
      `/feedback/${projectId}/all${qs ? `?${qs}` : ""}`,
    );
  },

  respond: (feedbackId: string, content: string) =>
    api.post<FeedbackManagerRead>(`/feedback/${feedbackId}/respond`, {
      content,
    }),

  resolve: (feedbackId: string, content?: string) =>
    api.post<FeedbackManagerRead>(`/feedback/${feedbackId}/resolve`, {
      content: content || null,
    }),

  decline: (feedbackId: string, content?: string) =>
    api.post<FeedbackManagerRead>(`/feedback/${feedbackId}/decline`, {
      content: content || null,
    }),

  counts: (projectIds: string[]) => {
    const query = projectIds.map((id) => `project_ids=${id}`).join("&");
    return api.get<Record<string, number>>(`/feedback/counts?${query}`);
  },
};
