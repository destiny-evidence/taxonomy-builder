import { api } from "./client";
import type { PublishedVersion, PublishedVersionCreate } from "../types/models";

export type ExportFormat = "ttl" | "xml" | "jsonld";

export async function publishVersion(
  schemeId: string,
  data: PublishedVersionCreate
): Promise<PublishedVersion> {
  return api.post(`/schemes/${schemeId}/versions`, data);
}

export async function listVersions(
  schemeId: string
): Promise<PublishedVersion[]> {
  return api.get(`/schemes/${schemeId}/versions`);
}

export async function getVersion(versionId: string): Promise<PublishedVersion> {
  return api.get(`/versions/${versionId}`);
}

export function getVersionExportUrl(versionId: string, format: ExportFormat): string {
  return `/api/versions/${versionId}/export?format=${format}`;
}
