import { api } from "./client";
import type { ChangeEvent } from "../types/models";

export async function getSchemeHistory(
  schemeId: string,
  limit?: number,
  offset?: number
): Promise<ChangeEvent[]> {
  const params = new URLSearchParams();
  if (limit !== undefined) params.set("limit", String(limit));
  if (offset !== undefined) params.set("offset", String(offset));
  const query = params.toString();
  return api.get(`/schemes/${schemeId}/history${query ? `?${query}` : ""}`);
}

export async function getConceptHistory(
  conceptId: string
): Promise<ChangeEvent[]> {
  return api.get(`/concepts/${conceptId}/history`);
}
