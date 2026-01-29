import { api } from "./client";
import type { Comment, CommentCreate } from "../types/models";

export const commentsApi = {
  listForConcept: (conceptId: string) =>
    api.get<Comment[]>(`/concepts/${conceptId}/comments`),

  create: (conceptId: string, data: CommentCreate) =>
    api.post<Comment>(`/concepts/${conceptId}/comments`, data),

  delete: (commentId: string) => api.delete(`/comments/${commentId}`),
};
