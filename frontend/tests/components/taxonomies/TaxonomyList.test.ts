import { describe, it, expect, beforeEach, vi } from 'vitest'
import { TaxonomyList } from '../../../src/components/taxonomies/TaxonomyList'
import type { Taxonomy } from '../../../src/types/models'

// Mock the API
vi.mock('../../../src/api/taxonomies', () => ({
  taxonomyApi: {
    list: vi.fn(),
  },
}))

import { taxonomyApi } from '../../../src/api/taxonomies'

describe('TaxonomyList', () => {
  let container: HTMLElement

  beforeEach(() => {
    container = document.createElement('div')
    document.body.appendChild(container)
    vi.clearAllMocks()
  })

  afterEach(() => {
    document.body.removeChild(container)
  })

  it('should render empty state when no taxonomies exist', async () => {
    vi.mocked(taxonomyApi.list).mockResolvedValue([])

    const list = new TaxonomyList(container)
    await list.render()

    expect(container.textContent).toContain('No taxonomies')
  })

  it('should show loading state during fetch', () => {
    vi.mocked(taxonomyApi.list).mockReturnValue(new Promise(() => {}))

    const list = new TaxonomyList(container)
    list.render()

    expect(container.textContent).toContain('Loading')
  })

  it('should render taxonomy list with properties', async () => {
    const taxonomies: Taxonomy[] = [
      {
        id: 'climate-health',
        name: 'Climate & Health',
        uri_prefix: 'http://example.org/climate/',
        created_at: '2025-01-01T00:00:00Z',
      },
    ]
    vi.mocked(taxonomyApi.list).mockResolvedValue(taxonomies)

    const list = new TaxonomyList(container)
    await list.render()

    expect(container.textContent).toContain('Climate & Health')
    expect(container.textContent).toContain('climate-health')
    expect(container.textContent).toContain('http://example.org/climate/')
  })

  it('should render multiple taxonomies', async () => {
    const taxonomies: Taxonomy[] = [
      {
        id: 'climate-health',
        name: 'Climate & Health',
        uri_prefix: 'http://example.org/climate/',
        created_at: '2025-01-01T00:00:00Z',
      },
      {
        id: 'biodiversity',
        name: 'Biodiversity',
        uri_prefix: 'http://example.org/bio/',
        created_at: '2025-01-01T00:00:00Z',
      },
    ]
    vi.mocked(taxonomyApi.list).mockResolvedValue(taxonomies)

    const list = new TaxonomyList(container)
    await list.render()

    expect(container.textContent).toContain('Climate & Health')
    expect(container.textContent).toContain('Biodiversity')
  })

  it('should show error state on API failure', async () => {
    vi.mocked(taxonomyApi.list).mockRejectedValue(new Error('Network error'))

    const list = new TaxonomyList(container)
    await list.render()

    expect(container.textContent).toContain('Error')
  })

  it('should make taxonomy items clickable', async () => {
    const taxonomies: Taxonomy[] = [
      {
        id: 'climate-health',
        name: 'Climate & Health',
        uri_prefix: 'http://example.org/climate/',
        created_at: '2025-01-01T00:00:00Z',
      },
    ]
    vi.mocked(taxonomyApi.list).mockResolvedValue(taxonomies)

    const list = new TaxonomyList(container)
    await list.render()

    const items = container.querySelectorAll('[data-taxonomy-id]')
    expect(items.length).toBe(1)
    expect(items[0].getAttribute('data-taxonomy-id')).toBe('climate-health')
  })
})
