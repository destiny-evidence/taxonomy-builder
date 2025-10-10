import { conceptApi } from '../../api/concepts'
import type { Concept } from '../../types/models'

export class RelationshipManager {
  private container: HTMLElement
  private concept: Concept
  private allConcepts: Concept[]

  constructor(container: HTMLElement, concept: Concept, allConcepts: Concept[]) {
    this.container = container
    this.concept = concept
    this.allConcepts = allConcepts
  }

  render(): void {
    const manager = document.createElement('div')
    manager.className = 'relationship-manager'

    manager.innerHTML = `
      <h4>Hierarchical Relationships</h4>

      <div class="broader-section">
        <h5>Broader Concepts</h5>
        <div class="broader-list" data-section="broader"></div>
        <div class="add-broader">
          <select name="broader-select">
            <option value="">Add broader concept...</option>
          </select>
          <button type="button" class="add-broader-btn">Add</button>
        </div>
      </div>

      <div class="narrower-section">
        <h5>Narrower Concepts</h5>
        <div class="narrower-list" data-section="narrower"></div>
      </div>
    `

    this.container.innerHTML = ''
    this.container.appendChild(manager)

    this.renderBroaderList()
    this.renderNarrowerList()
    this.populateBroaderSelect()

    const addBtn = manager.querySelector('.add-broader-btn') as HTMLButtonElement
    addBtn.addEventListener('click', () => this.handleAddBroader())
  }

  private renderBroaderList(): void {
    const listEl = this.container.querySelector('[data-section="broader"]') as HTMLElement

    if (this.concept.broader_ids.length === 0) {
      listEl.innerHTML = '<div class="empty">No broader concepts</div>'
      return
    }

    listEl.innerHTML = ''
    this.concept.broader_ids.forEach((broaderId) => {
      const broader = this.allConcepts.find((c) => c.id === broaderId)
      if (broader) {
        const item = this.createRelationshipItem(broader, 'broader')
        listEl.appendChild(item)
      }
    })
  }

  private renderNarrowerList(): void {
    const listEl = this.container.querySelector('[data-section="narrower"]') as HTMLElement

    if (this.concept.narrower_ids.length === 0) {
      listEl.innerHTML = '<div class="empty">No narrower concepts</div>'
      return
    }

    listEl.innerHTML = ''
    this.concept.narrower_ids.forEach((narrowerId) => {
      const narrower = this.allConcepts.find((c) => c.id === narrowerId)
      if (narrower) {
        const item = this.createRelationshipItem(narrower, 'narrower')
        listEl.appendChild(item)
      }
    })
  }

  private createRelationshipItem(concept: Concept, type: 'broader' | 'narrower'): HTMLElement {
    const item = document.createElement('div')
    item.className = 'relationship-item'

    const label = document.createElement('span')
    label.textContent = concept.pref_label

    item.appendChild(label)

    if (type === 'broader') {
      const removeBtn = document.createElement('button')
      removeBtn.textContent = 'Remove'
      removeBtn.className = 'remove-btn'
      removeBtn.addEventListener('click', () => this.handleRemoveBroader(concept.id))
      item.appendChild(removeBtn)
    }

    return item
  }

  private populateBroaderSelect(): void {
    const select = this.container.querySelector(
      'select[name="broader-select"]'
    ) as HTMLSelectElement

    // Filter out concepts that would create cycles
    const availableConcepts = this.allConcepts.filter((c) => {
      if (c.id === this.concept.id) return false // Can't be broader than self
      if (this.concept.broader_ids.includes(c.id)) return false // Already broader
      if (c.broader_ids.includes(this.concept.id)) return false // Would create cycle
      return true
    })

    availableConcepts.forEach((concept) => {
      const option = document.createElement('option')
      option.value = concept.id
      option.textContent = concept.pref_label
      select.appendChild(option)
    })
  }

  private async handleAddBroader(): Promise<void> {
    const select = this.container.querySelector(
      'select[name="broader-select"]'
    ) as HTMLSelectElement
    const broaderId = select.value

    if (!broaderId) return

    try {
      await conceptApi.addBroader(this.concept.id, broaderId)
      this.emitEvent('relationship-updated')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error'
      if (message.toLowerCase().includes('cycle')) {
        alert('Cannot add relationship: would create a cycle')
      } else {
        alert(`Failed to add relationship: ${message}`)
      }
    }
  }

  private async handleRemoveBroader(broaderId: string): Promise<void> {
    try {
      await conceptApi.removeBroader(this.concept.id, broaderId)
      this.emitEvent('relationship-updated')
    } catch (error) {
      alert(
        `Failed to remove relationship: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  }

  private emitEvent(eventName: string): void {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      detail: { concept: this.concept },
    })
    this.container.dispatchEvent(event)
  }
}
