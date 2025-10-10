import { client } from './client'
import type { Concept, ConceptCreate, ConceptUpdate } from '../types/models'

export const conceptApi = {
  create: (schemeId: string, data: ConceptCreate) =>
    client.post(`api/schemes/${schemeId}/concepts`, { json: data }).json<Concept>(),

  list: (schemeId: string) => client.get(`api/schemes/${schemeId}/concepts`).json<Concept[]>(),

  get: (id: string) => client.get(`api/concepts/${id}`).json<Concept>(),

  update: (id: string, data: ConceptUpdate) =>
    client.put(`api/concepts/${id}`, { json: data }).json<Concept>(),

  delete: (id: string) => client.delete(`api/concepts/${id}`),

  addBroader: (conceptId: string, broaderId: string) =>
    client.post(`api/concepts/${conceptId}/broader/${broaderId}`).json<Concept>(),

  removeBroader: (conceptId: string, broaderId: string) =>
    client.delete(`api/concepts/${conceptId}/broader/${broaderId}`).json<Concept>(),
}
