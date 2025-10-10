import { client } from './client'
import type { ConceptScheme, ConceptSchemeCreate, ConceptSchemeUpdate } from '../types/models'

export const schemeApi = {
  create: (taxonomyId: string, data: ConceptSchemeCreate) =>
    client.post(`api/taxonomies/${taxonomyId}/schemes`, { json: data }).json<ConceptScheme>(),

  list: (taxonomyId: string) =>
    client.get(`api/taxonomies/${taxonomyId}/schemes`).json<ConceptScheme[]>(),

  get: (id: string) => client.get(`api/schemes/${id}`).json<ConceptScheme>(),

  update: (id: string, data: ConceptSchemeUpdate) =>
    client.put(`api/schemes/${id}`, { json: data }).json<ConceptScheme>(),

  delete: (id: string) => client.delete(`api/schemes/${id}`),
}
