import { api } from "./client";
import type { CoreOntology } from "../types/models";

export const ontologyApi = {
  get: () => api.get<CoreOntology>("/ontology"),
};
