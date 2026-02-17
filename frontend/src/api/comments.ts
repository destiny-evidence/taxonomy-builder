import { api } from "./client";
import type { Comment, CommentCreate } from "../types/models";

export const commentsApi = {
  listForConcept: (conceptId: string, resolved?: boolean) => {
    const params = resolved !== undefined ? `?resolved=${resolved}` : "";
    return api.get<Comment[]>(`/concepts/${conceptId}/comments${params}`);
  },

  create: (conceptId: string, data: CommentCreate) =>
    api.post<Comment>(`/concepts/${conceptId}/comments`, data),

  delete: (commentId: string) => api.delete(`/comments/${commentId}`),

  resolve: (commentId: string) => api.post(`/comments/${commentId}/resolve`, undefined),

  unresolve: (commentId: string) => api.post(`/comments/${commentId}/unresolve`, undefined)
};
