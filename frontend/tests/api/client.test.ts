import { describe, it, expect } from 'vitest'
import { client } from '../../src/api/client'

describe('API Client', () => {
  it('should export a client instance', () => {
    expect(client).toBeDefined()
    expect(typeof client.get).toBe('function')
    expect(typeof client.post).toBe('function')
    expect(typeof client.put).toBe('function')
    expect(typeof client.delete).toBe('function')
  })
})
