import { describe, it, expect } from 'vitest'
import { conceptApi } from '../../src/api/concepts'

describe('Concept API Client', () => {
  it('should export API methods', () => {
    expect(conceptApi).toBeDefined()
    expect(typeof conceptApi.create).toBe('function')
    expect(typeof conceptApi.list).toBe('function')
    expect(typeof conceptApi.get).toBe('function')
    expect(typeof conceptApi.update).toBe('function')
    expect(typeof conceptApi.delete).toBe('function')
  })

  it('should export relationship management methods', () => {
    expect(typeof conceptApi.addBroader).toBe('function')
    expect(typeof conceptApi.removeBroader).toBe('function')
  })
})
