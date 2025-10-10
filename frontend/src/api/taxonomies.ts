import { client } from './client'
import type { Taxonomy, TaxonomyCreate, TaxonomyUpdate } from '../types/models'

export const taxonomyApi = {
  create: (data: TaxonomyCreate) => client.post('api/taxonomies', { json: data }).json<Taxonomy>(),

  list: () => client.get('api/taxonomies').json<Taxonomy[]>(),

  get: (id: string) => client.get(`api/taxonomies/${id}`).json<Taxonomy>(),

  update: (id: string, data: TaxonomyUpdate) =>
    client.put(`api/taxonomies/${id}`, { json: data }).json<Taxonomy>(),

  delete: (id: string) => client.delete(`api/taxonomies/${id}`),
}
