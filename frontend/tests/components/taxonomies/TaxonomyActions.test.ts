import { describe, it, expect, beforeEach, vi } from 'vitest'
import { TaxonomyActions } from '../../../src/components/taxonomies/TaxonomyActions'
import type { Taxonomy } from '../../../src/types/models'

vi.mock('../../../src/api/taxonomies', () => ({
  taxonomyApi: {
    delete: vi.fn(),
  },
}))

import { taxonomyApi } from '../../../src/api/taxonomies'

describe('TaxonomyActions', () => {
  let container: HTMLElement
  const mockTaxonomy: Taxonomy = {
    id: 'test-taxonomy',
    name: 'Test Taxonomy',
    uri_prefix: 'http://example.org/test/',
    created_at: '2025-01-01T00:00:00Z',
  }

  beforeEach(() => {
    container = document.createElement('div')
    document.body.appendChild(container)
    vi.clearAllMocks()
  })

  afterEach(() => {
    document.body.removeChild(container)
  })

  it('should render edit and delete buttons', () => {
    const actions = new TaxonomyActions(container, mockTaxonomy)
    actions.render()

    expect(container.querySelector('button.edit-btn')).toBeTruthy()
    expect(container.querySelector('button.delete-btn')).toBeTruthy()
  })

  it('should emit edit event when edit button clicked', () => {
    const actions = new TaxonomyActions(container, mockTaxonomy)
    actions.render()

    const editHandler = vi.fn()
    container.addEventListener('taxonomy-edit', editHandler)

    const editBtn = container.querySelector('button.edit-btn') as HTMLButtonElement
    editBtn.click()

    expect(editHandler).toHaveBeenCalled()
  })

  it('should show confirmation before delete', () => {
    const actions = new TaxonomyActions(container, mockTaxonomy)
    actions.render()

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)

    const deleteBtn = container.querySelector('button.delete-btn') as HTMLButtonElement
    deleteBtn.click()

    expect(confirmSpy).toHaveBeenCalledWith(
      expect.stringContaining('Test Taxonomy')
    )
    expect(taxonomyApi.delete).not.toHaveBeenCalled()

    confirmSpy.mockRestore()
  })

  it('should delete taxonomy when confirmed', async () => {
    vi.mocked(taxonomyApi.delete).mockResolvedValue(undefined as never)

    const actions = new TaxonomyActions(container, mockTaxonomy)
    actions.render()

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    const deleteBtn = container.querySelector('button.delete-btn') as HTMLButtonElement
    deleteBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(taxonomyApi.delete).toHaveBeenCalledWith('test-taxonomy')

    confirmSpy.mockRestore()
  })

  it('should emit delete event after successful deletion', async () => {
    vi.mocked(taxonomyApi.delete).mockResolvedValue(undefined as never)

    const actions = new TaxonomyActions(container, mockTaxonomy)
    actions.render()

    const deleteHandler = vi.fn()
    container.addEventListener('taxonomy-deleted', deleteHandler)

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    const deleteBtn = container.querySelector('button.delete-btn') as HTMLButtonElement
    deleteBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(deleteHandler).toHaveBeenCalled()

    confirmSpy.mockRestore()
  })
})
