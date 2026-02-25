import { api } from "./client";

export interface FeedbackCreate {
  snapshot_version: string;
  entity_type: string;
  entity_id: string;
  entity_label: string;
  feedback_type: string;
  content: string;
}

export interface FeedbackRead {
  id: string;
  project_id: string;
  snapshot_version: string;
  entity_type: string;
  entity_id: string;
  entity_label: string;
  feedback_type: string;
  content: string;
  status: "open" | "responded" | "resolved" | "declined";
  response: { author: string; content: string; created_at: string } | null;
  created_at: string;
  can_delete: boolean;
}

export const feedbackApi = {
  create(projectId: string, data: FeedbackCreate): Promise<FeedbackRead> {
    return api.post(`/feedback/${projectId}`, data);
  },

  listMine(
    projectId: string,
    params?: { version?: string; entity_type?: string }
  ): Promise<FeedbackRead[]> {
    const query = new URLSearchParams();
    if (params?.version) query.set("version", params.version);
    if (params?.entity_type) query.set("entity_type", params.entity_type);
    const qs = query.toString();
    return api.get(`/feedback/${projectId}/mine${qs ? `?${qs}` : ""}`);
  },

  deleteOwn(feedbackId: string): Promise<void> {
    return api.delete(`/feedback/${feedbackId}`);
  },
};
