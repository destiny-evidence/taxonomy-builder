import { describe, it, expect } from 'vitest'
import { taxonomyApi } from '../../src/api/taxonomies'

describe('Taxonomy API Client', () => {
  it('should export API methods', () => {
    expect(taxonomyApi).toBeDefined()
    expect(typeof taxonomyApi.create).toBe('function')
    expect(typeof taxonomyApi.list).toBe('function')
    expect(typeof taxonomyApi.get).toBe('function')
    expect(typeof taxonomyApi.update).toBe('function')
    expect(typeof taxonomyApi.delete).toBe('function')
  })

  // Note: We'll add integration tests that actually call the API once the backend is running
  // For now, we verify the API client structure is correct
})
