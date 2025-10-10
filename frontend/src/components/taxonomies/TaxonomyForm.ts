import { taxonomyApi } from '../../api/taxonomies'
import type { Taxonomy, TaxonomyCreate, TaxonomyUpdate } from '../../types/models'

export class TaxonomyForm {
  private container: HTMLElement
  private taxonomy?: Taxonomy
  private errors: Map<string, string> = new Map()

  constructor(container: HTMLElement, taxonomy?: Taxonomy) {
    this.container = container
    this.taxonomy = taxonomy
  }

  render(): void {
    const form = document.createElement('form')
    form.className = 'taxonomy-form'
    form.addEventListener('submit', (e) => this.handleSubmit(e))

    form.innerHTML = `
      <div class="form-group">
        <label for="id">ID</label>
        <input
          type="text"
          name="id"
          id="id"
          value="${this.taxonomy?.id || ''}"
          ${this.taxonomy ? 'readonly' : ''}
          required
        />
        <div class="error" data-field="id"></div>
      </div>

      <div class="form-group">
        <label for="name">Name</label>
        <input
          type="text"
          name="name"
          id="name"
          value="${this.taxonomy?.name || ''}"
          required
        />
        <div class="error" data-field="name"></div>
      </div>

      <div class="form-group">
        <label for="uri_prefix">URI Prefix</label>
        <input
          type="text"
          name="uri_prefix"
          id="uri_prefix"
          value="${this.taxonomy?.uri_prefix || ''}"
          required
        />
        <div class="error" data-field="uri_prefix"></div>
      </div>

      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          name="description"
          id="description"
        >${this.taxonomy?.description || ''}</textarea>
        <div class="error" data-field="description"></div>
      </div>

      <div class="form-actions">
        <button type="submit">${this.taxonomy ? 'Update' : 'Create'} Taxonomy</button>
      </div>
    `

    this.container.innerHTML = ''
    this.container.appendChild(form)
  }

  private async handleSubmit(event: Event): Promise<void> {
    event.preventDefault()
    this.clearErrors()

    const form = event.target as HTMLFormElement
    const formData = new FormData(form)

    const id = formData.get('id') as string
    const name = formData.get('name') as string
    const uri_prefix = formData.get('uri_prefix') as string
    const description = formData.get('description') as string

    // Validate
    if (!this.validate(id, name, uri_prefix)) {
      this.displayErrors()
      return
    }

    try {
      if (this.taxonomy) {
        // Update
        const updateData: TaxonomyUpdate = {
          name,
          uri_prefix,
          description: description || undefined,
        }
        await taxonomyApi.update(this.taxonomy.id, updateData)
        this.emitEvent('taxonomy-updated')
      } else {
        // Create
        const createData: TaxonomyCreate = {
          id,
          name,
          uri_prefix,
          description: description || undefined,
        }
        await taxonomyApi.create(createData)
        this.emitEvent('taxonomy-created')
        form.reset()
      }
      this.clearErrors()
    } catch (error) {
      this.errors.set('submit', error instanceof Error ? error.message : 'Unknown error')
      this.displayErrors()
    }
  }

  private validate(id: string, name: string, uri_prefix: string): boolean {
    this.errors.clear()

    if (!id) {
      this.errors.set('id', 'ID is required')
    } else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)) {
      this.errors.set('id', 'ID must be lowercase with hyphens (e.g., climate-health)')
    }

    if (!name) {
      this.errors.set('name', 'Name is required')
    }

    if (!uri_prefix) {
      this.errors.set('uri_prefix', 'URI prefix is required')
    } else if (!/^https?:\/\/.+/.test(uri_prefix)) {
      this.errors.set('uri_prefix', 'URI prefix must be a valid URL')
    }

    return this.errors.size === 0
  }

  private clearErrors(): void {
    this.errors.clear()
    this.container.querySelectorAll('.error').forEach((el) => {
      el.textContent = ''
    })
  }

  private displayErrors(): void {
    this.errors.forEach((message, field) => {
      const errorEl = this.container.querySelector(`.error[data-field="${field}"]`)
      if (errorEl) {
        errorEl.textContent = message
      }
    })
  }

  private emitEvent(eventName: string): void {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      detail: { taxonomy: this.taxonomy },
    })
    this.container.dispatchEvent(event)
  }
}
