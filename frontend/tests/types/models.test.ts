import { describe, it, expect } from 'vitest'
import type {
  Taxonomy,
  TaxonomyCreate,
  ConceptScheme,
  Concept,
} from '../../src/types/models'

describe('Type Definitions', () => {
  it('should define Taxonomy interface matching API', () => {
    const taxonomy: Taxonomy = {
      id: 'climate-health',
      name: 'Climate & Health',
      uri_prefix: 'http://example.org/climate/',
      created_at: '2025-01-01T00:00:00Z',
    }

    expect(taxonomy.id).toBe('climate-health')
    expect(taxonomy.name).toBe('Climate & Health')
    expect(taxonomy.uri_prefix).toBe('http://example.org/climate/')
    expect(taxonomy.created_at).toBe('2025-01-01T00:00:00Z')
  })

  it('should allow optional description field in Taxonomy', () => {
    const withDescription: Taxonomy = {
      id: 'test',
      name: 'Test',
      uri_prefix: 'http://example.org/test/',
      description: 'A test taxonomy',
      created_at: '2025-01-01T00:00:00Z',
    }

    const withoutDescription: Taxonomy = {
      id: 'test',
      name: 'Test',
      uri_prefix: 'http://example.org/test/',
      created_at: '2025-01-01T00:00:00Z',
    }

    expect(withDescription.description).toBe('A test taxonomy')
    expect(withoutDescription.description).toBeUndefined()
  })

  it('should define TaxonomyCreate without created_at', () => {
    const create: TaxonomyCreate = {
      id: 'new-taxonomy',
      name: 'New Taxonomy',
      uri_prefix: 'http://example.org/new/',
    }

    expect(create.id).toBe('new-taxonomy')
    expect('created_at' in create).toBe(false)
  })

  it('should define ConceptScheme with taxonomy_id and uri', () => {
    const scheme: ConceptScheme = {
      id: 'intervention',
      taxonomy_id: 'climate-health',
      name: 'Intervention',
      uri: 'http://example.org/climate/intervention',
      created_at: '2025-01-01T00:00:00Z',
    }

    expect(scheme.taxonomy_id).toBe('climate-health')
    expect(scheme.uri).toBe('http://example.org/climate/intervention')
  })

  it('should define Concept with SKOS properties', () => {
    const concept: Concept = {
      id: 'heat-warning',
      scheme_id: 'intervention',
      uri: 'http://example.org/climate/heat-warning',
      pref_label: 'Heat Warning System',
      definition: 'A system to warn people about heat waves',
      alt_labels: ['Heat Alert', 'Heat Advisory'],
      broader_ids: ['early-warning'],
      narrower_ids: ['extreme-heat-warning'],
      created_at: '2025-01-01T00:00:00Z',
    }

    expect(concept.pref_label).toBe('Heat Warning System')
    expect(concept.alt_labels).toHaveLength(2)
    expect(concept.broader_ids).toContain('early-warning')
    expect(concept.narrower_ids).toContain('extreme-heat-warning')
  })

  it('should allow empty arrays for Concept relationships', () => {
    const concept: Concept = {
      id: 'root-concept',
      scheme_id: 'intervention',
      uri: 'http://example.org/climate/root-concept',
      pref_label: 'Root Concept',
      alt_labels: [],
      broader_ids: [],
      narrower_ids: [],
      created_at: '2025-01-01T00:00:00Z',
    }

    expect(concept.alt_labels).toEqual([])
    expect(concept.broader_ids).toEqual([])
    expect(concept.narrower_ids).toEqual([])
  })
})
