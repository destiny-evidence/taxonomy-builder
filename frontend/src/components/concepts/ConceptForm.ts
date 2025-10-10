import { conceptApi } from '../../api/concepts'
import type { Concept, ConceptCreate, ConceptUpdate } from '../../types/models'

export class ConceptForm {
  private container: HTMLElement
  private schemeId: string
  private concept?: Concept
  private errors: Map<string, string> = new Map()

  constructor(container: HTMLElement, schemeId: string, concept?: Concept) {
    this.container = container
    this.schemeId = schemeId
    this.concept = concept
  }

  render(): void {
    const form = document.createElement('form')
    form.className = 'concept-form'
    form.addEventListener('submit', (e) => this.handleSubmit(e))

    const altLabelsValue = this.concept?.alt_labels?.join(', ') || ''

    form.innerHTML = `
      <div class="form-group">
        <label for="id">ID</label>
        <input
          type="text"
          name="id"
          id="id"
          value="${this.concept?.id || ''}"
          ${this.concept ? 'readonly' : ''}
          required
        />
        <div class="error" data-field="id"></div>
      </div>

      <div class="form-group">
        <label for="pref_label">Preferred Label</label>
        <input
          type="text"
          name="pref_label"
          id="pref_label"
          value="${this.concept?.pref_label || ''}"
          required
        />
        <div class="error" data-field="pref_label"></div>
      </div>

      <div class="form-group">
        <label for="definition">Definition</label>
        <textarea
          name="definition"
          id="definition"
        >${this.concept?.definition || ''}</textarea>
        <div class="error" data-field="definition"></div>
      </div>

      <div class="form-group">
        <label for="alt_labels">Alternative Labels (comma-separated)</label>
        <input
          type="text"
          name="alt_labels"
          id="alt_labels"
          value="${altLabelsValue}"
        />
        <div class="error" data-field="alt_labels"></div>
      </div>

      <div class="form-actions">
        <button type="submit">${this.concept ? 'Update' : 'Create'} Concept</button>
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
    const pref_label = formData.get('pref_label') as string
    const definition = formData.get('definition') as string
    const alt_labels_str = formData.get('alt_labels') as string

    const alt_labels = alt_labels_str
      ? alt_labels_str
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
      : []

    if (!this.validate(id, pref_label)) {
      this.displayErrors()
      return
    }

    try {
      if (this.concept) {
        const updateData: ConceptUpdate = {
          pref_label,
          definition: definition || undefined,
          alt_labels,
        }
        await conceptApi.update(this.concept.id, updateData)
        this.emitEvent('concept-updated')
      } else {
        const createData: ConceptCreate = {
          id,
          pref_label,
          definition: definition || undefined,
          alt_labels,
        }
        await conceptApi.create(this.schemeId, createData)
        this.emitEvent('concept-created')
        form.reset()
      }
      this.clearErrors()
    } catch (error) {
      this.errors.set('submit', error instanceof Error ? error.message : 'Unknown error')
      this.displayErrors()
    }
  }

  private validate(id: string, pref_label: string): boolean {
    this.errors.clear()

    if (!id) {
      this.errors.set('id', 'ID is required')
    } else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)) {
      this.errors.set('id', 'ID must be lowercase with hyphens')
    }

    if (!pref_label) {
      this.errors.set('pref_label', 'Preferred label is required')
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
      detail: { concept: this.concept },
    })
    this.container.dispatchEvent(event)
  }
}
