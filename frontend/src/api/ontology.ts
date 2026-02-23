import { api } from "./client";
import type { OntologyClass } from "../types/models";

export const ontologyApi = {
  listForProject: (projectId: string) =>
    api.get<OntologyClass[]>(`/projects/${projectId}/classes`),
};
