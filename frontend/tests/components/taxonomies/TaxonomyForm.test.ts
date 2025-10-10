import { describe, it, expect, beforeEach, vi } from 'vitest'
import { TaxonomyForm } from '../../../src/components/taxonomies/TaxonomyForm'
import type { Taxonomy } from '../../../src/types/models'

vi.mock('../../../src/api/taxonomies', () => ({
  taxonomyApi: {
    create: vi.fn(),
    update: vi.fn(),
  },
}))

import { taxonomyApi } from '../../../src/api/taxonomies'

describe('TaxonomyForm', () => {
  let container: HTMLElement

  beforeEach(() => {
    container = document.createElement('div')
    document.body.appendChild(container)
    vi.clearAllMocks()
  })

  afterEach(() => {
    document.body.removeChild(container)
  })

  it('should render form fields', () => {
    const form = new TaxonomyForm(container)
    form.render()

    expect(container.querySelector('input[name="id"]')).toBeTruthy()
    expect(container.querySelector('input[name="name"]')).toBeTruthy()
    expect(container.querySelector('input[name="uri_prefix"]')).toBeTruthy()
    expect(container.querySelector('textarea[name="description"]')).toBeTruthy()
    expect(container.querySelector('button[type="submit"]')).toBeTruthy()
  })

  it('should validate required fields on submit', async () => {
    const form = new TaxonomyForm(container)
    form.render()

    // Remove HTML5 validation for test
    const formEl = container.querySelector('form') as HTMLFormElement
    formEl.noValidate = true

    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement
    submitBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(container.textContent).toContain('required')
    expect(taxonomyApi.create).not.toHaveBeenCalled()
  })

  it('should validate ID format (lowercase with hyphens)', async () => {
    const form = new TaxonomyForm(container)
    form.render()

    const idInput = container.querySelector('input[name="id"]') as HTMLInputElement
    idInput.value = 'Invalid-ID'

    const nameInput = container.querySelector('input[name="name"]') as HTMLInputElement
    nameInput.value = 'Test'

    const uriInput = container.querySelector('input[name="uri_prefix"]') as HTMLInputElement
    uriInput.value = 'http://example.org/test/'

    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement
    submitBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(container.textContent).toMatch(/lowercase|hyphen|invalid/i)
    expect(taxonomyApi.create).not.toHaveBeenCalled()
  })

  it('should validate URI format', async () => {
    const form = new TaxonomyForm(container)
    form.render()

    const idInput = container.querySelector('input[name="id"]') as HTMLInputElement
    idInput.value = 'test-taxonomy'

    const nameInput = container.querySelector('input[name="name"]') as HTMLInputElement
    nameInput.value = 'Test'

    const uriInput = container.querySelector('input[name="uri_prefix"]') as HTMLInputElement
    uriInput.value = 'not-a-valid-uri'

    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement
    submitBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(container.textContent).toMatch(/uri|invalid/i)
    expect(taxonomyApi.create).not.toHaveBeenCalled()
  })

  it('should submit valid data to API', async () => {
    const createdTaxonomy: Taxonomy = {
      id: 'test-taxonomy',
      name: 'Test Taxonomy',
      uri_prefix: 'http://example.org/test/',
      created_at: '2025-01-01T00:00:00Z',
    }
    vi.mocked(taxonomyApi.create).mockResolvedValue(createdTaxonomy)

    const form = new TaxonomyForm(container)
    form.render()

    const idInput = container.querySelector('input[name="id"]') as HTMLInputElement
    idInput.value = 'test-taxonomy'

    const nameInput = container.querySelector('input[name="name"]') as HTMLInputElement
    nameInput.value = 'Test Taxonomy'

    const uriInput = container.querySelector('input[name="uri_prefix"]') as HTMLInputElement
    uriInput.value = 'http://example.org/test/'

    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement
    submitBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(taxonomyApi.create).toHaveBeenCalledWith({
      id: 'test-taxonomy',
      name: 'Test Taxonomy',
      uri_prefix: 'http://example.org/test/',
    })
  })

  it('should clear form after successful submission', async () => {
    const createdTaxonomy: Taxonomy = {
      id: 'test-taxonomy',
      name: 'Test Taxonomy',
      uri_prefix: 'http://example.org/test/',
      created_at: '2025-01-01T00:00:00Z',
    }
    vi.mocked(taxonomyApi.create).mockResolvedValue(createdTaxonomy)

    const form = new TaxonomyForm(container)
    form.render()

    const idInput = container.querySelector('input[name="id"]') as HTMLInputElement
    idInput.value = 'test-taxonomy'

    const nameInput = container.querySelector('input[name="name"]') as HTMLInputElement
    nameInput.value = 'Test Taxonomy'

    const uriInput = container.querySelector('input[name="uri_prefix"]') as HTMLInputElement
    uriInput.value = 'http://example.org/test/'

    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement
    submitBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(idInput.value).toBe('')
    expect(nameInput.value).toBe('')
    expect(uriInput.value).toBe('')
  })

  it('should emit success event after creation', async () => {
    const createdTaxonomy: Taxonomy = {
      id: 'test-taxonomy',
      name: 'Test Taxonomy',
      uri_prefix: 'http://example.org/test/',
      created_at: '2025-01-01T00:00:00Z',
    }
    vi.mocked(taxonomyApi.create).mockResolvedValue(createdTaxonomy)

    const form = new TaxonomyForm(container)
    form.render()

    const successHandler = vi.fn()
    container.addEventListener('taxonomy-created', successHandler)

    const idInput = container.querySelector('input[name="id"]') as HTMLInputElement
    idInput.value = 'test-taxonomy'

    const nameInput = container.querySelector('input[name="name"]') as HTMLInputElement
    nameInput.value = 'Test Taxonomy'

    const uriInput = container.querySelector('input[name="uri_prefix"]') as HTMLInputElement
    uriInput.value = 'http://example.org/test/'

    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement
    submitBtn.click()

    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(successHandler).toHaveBeenCalled()
  })
})
