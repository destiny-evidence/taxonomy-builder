import { schemeApi } from '../../api/schemes'
import type { ConceptScheme, ConceptSchemeCreate, ConceptSchemeUpdate } from '../../types/models'

export class SchemeForm {
  private container: HTMLElement
  private taxonomyId: string
  private scheme?: ConceptScheme
  private errors: Map<string, string> = new Map()

  constructor(container: HTMLElement, taxonomyId: string, scheme?: ConceptScheme) {
    this.container = container
    this.taxonomyId = taxonomyId
    this.scheme = scheme
  }

  render(): void {
    const form = document.createElement('form')
    form.className = 'scheme-form'
    form.addEventListener('submit', (e) => this.handleSubmit(e))

    form.innerHTML = `
      <div class="form-group">
        <label for="id">ID</label>
        <input
          type="text"
          name="id"
          id="id"
          value="${this.scheme?.id || ''}"
          ${this.scheme ? 'readonly' : ''}
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
          value="${this.scheme?.name || ''}"
          required
        />
        <div class="error" data-field="name"></div>
      </div>

      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          name="description"
          id="description"
        >${this.scheme?.description || ''}</textarea>
        <div class="error" data-field="description"></div>
      </div>

      <div class="form-actions">
        <button type="submit">${this.scheme ? 'Update' : 'Create'} Scheme</button>
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
    const description = formData.get('description') as string

    if (!this.validate(id, name)) {
      this.displayErrors()
      return
    }

    try {
      if (this.scheme) {
        const updateData: ConceptSchemeUpdate = {
          name,
          description: description || undefined,
        }
        await schemeApi.update(this.scheme.id, updateData)
        this.emitEvent('scheme-updated')
      } else {
        const createData: ConceptSchemeCreate = {
          id,
          name,
          description: description || undefined,
        }
        await schemeApi.create(this.taxonomyId, createData)
        this.emitEvent('scheme-created')
        form.reset()
      }
      this.clearErrors()
    } catch (error) {
      this.errors.set('submit', error instanceof Error ? error.message : 'Unknown error')
      this.displayErrors()
    }
  }

  private validate(id: string, name: string): boolean {
    this.errors.clear()

    if (!id) {
      this.errors.set('id', 'ID is required')
    } else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)) {
      this.errors.set('id', 'ID must be lowercase with hyphens')
    }

    if (!name) {
      this.errors.set('name', 'Name is required')
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
      detail: { scheme: this.scheme },
    })
    this.container.dispatchEvent(event)
  }
}
