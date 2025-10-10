import { taxonomyApi } from '../../api/taxonomies'
import type { Taxonomy } from '../../types/models'

export class TaxonomyActions {
  private container: HTMLElement
  private taxonomy: Taxonomy

  constructor(container: HTMLElement, taxonomy: Taxonomy) {
    this.container = container
    this.taxonomy = taxonomy
  }

  render(): void {
    const actions = document.createElement('div')
    actions.className = 'taxonomy-actions'

    const editBtn = document.createElement('button')
    editBtn.className = 'edit-btn'
    editBtn.textContent = 'Edit'
    editBtn.addEventListener('click', () => this.handleEdit())

    const deleteBtn = document.createElement('button')
    deleteBtn.className = 'delete-btn'
    deleteBtn.textContent = 'Delete'
    deleteBtn.addEventListener('click', () => this.handleDelete())

    actions.appendChild(editBtn)
    actions.appendChild(deleteBtn)

    this.container.innerHTML = ''
    this.container.appendChild(actions)
  }

  private handleEdit(): void {
    const event = new CustomEvent('taxonomy-edit', {
      bubbles: true,
      detail: { taxonomy: this.taxonomy },
    })
    this.container.dispatchEvent(event)
  }

  private async handleDelete(): Promise<void> {
    const confirmed = confirm(`Are you sure you want to delete "${this.taxonomy.name}"?`)

    if (!confirmed) {
      return
    }

    try {
      await taxonomyApi.delete(this.taxonomy.id)
      const event = new CustomEvent('taxonomy-deleted', {
        bubbles: true,
        detail: { taxonomy: this.taxonomy },
      })
      this.container.dispatchEvent(event)
    } catch (error) {
      alert(
        `Failed to delete taxonomy: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  }
}
