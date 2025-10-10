import { describe, it, expect } from 'vitest'
import { schemeApi } from '../../src/api/schemes'

describe('ConceptScheme API Client', () => {
  it('should export API methods', () => {
    expect(schemeApi).toBeDefined()
    expect(typeof schemeApi.create).toBe('function')
    expect(typeof schemeApi.list).toBe('function')
    expect(typeof schemeApi.get).toBe('function')
    expect(typeof schemeApi.update).toBe('function')
    expect(typeof schemeApi.delete).toBe('function')
  })
})
