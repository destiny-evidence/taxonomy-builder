export interface Taxonomy {
  id: string
  name: string
  uri_prefix: string
  description?: string
  created_at: string
}

export interface TaxonomyCreate {
  id: string
  name: string
  uri_prefix: string
  description?: string
}

export interface TaxonomyUpdate {
  name?: string
  uri_prefix?: string
  description?: string
}

export interface ConceptScheme {
  id: string
  taxonomy_id: string
  name: string
  uri: string
  description?: string
  created_at: string
}

export interface ConceptSchemeCreate {
  id: string
  name: string
  description?: string
}

export interface ConceptSchemeUpdate {
  name?: string
  description?: string
}

export interface Concept {
  id: string
  scheme_id: string
  uri: string
  pref_label: string
  definition?: string
  alt_labels: string[]
  broader_ids: string[]
  narrower_ids: string[]
  created_at: string
}

export interface ConceptCreate {
  id: string
  pref_label: string
  definition?: string
  alt_labels?: string[]
}

export interface ConceptUpdate {
  pref_label?: string
  definition?: string
  alt_labels?: string[]
}
