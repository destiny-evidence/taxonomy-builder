import { conceptApi } from '../../api/concepts'
import type { Concept } from '../../types/models'

export class ConceptList {
  private container: HTMLElement
  private schemeId: string
  private concepts: Concept[] = []

  constructor(container: HTMLElement, schemeId: string) {
    this.container = container
    this.schemeId = schemeId
  }

  async render(): Promise<void> {
    this.container.innerHTML = '<div class="loading">Loading...</div>'

    try {
      this.concepts = await conceptApi.list(this.schemeId)
      this.renderList()
    } catch (error) {
      this.renderError(error)
    }
  }

  private renderList(): void {
    if (this.concepts.length === 0) {
      this.container.innerHTML = '<div class="empty-state">No concepts</div>'
      return
    }

    const list = document.createElement('div')
    list.className = 'concept-list'

    this.concepts.forEach((concept) => {
      const item = this.createConceptItem(concept)
      list.appendChild(item)
    })

    this.container.innerHTML = ''
    this.container.appendChild(list)
  }

  private createConceptItem(concept: Concept): HTMLElement {
    const item = document.createElement('div')
    item.className = 'concept-item'
    item.setAttribute('data-concept-id', concept.id)

    const label = document.createElement('h3')
    label.textContent = concept.pref_label

    const id = document.createElement('div')
    id.className = 'concept-id'
    id.textContent = concept.id

    const uri = document.createElement('div')
    uri.className = 'concept-uri'
    uri.textContent = concept.uri

    item.appendChild(label)
    item.appendChild(id)
    item.appendChild(uri)

    if (concept.definition) {
      const definition = document.createElement('div')
      definition.className = 'concept-definition'
      definition.textContent = concept.definition
      item.appendChild(definition)
    }

    if (concept.alt_labels.length > 0) {
      const altLabels = document.createElement('div')
      altLabels.className = 'concept-alt-labels'
      altLabels.textContent = `Alt: ${concept.alt_labels.join(', ')}`
      item.appendChild(altLabels)
    }

    const hierarchy = document.createElement('div')
    hierarchy.className = 'concept-hierarchy'
    hierarchy.textContent = `Broader: ${concept.broader_ids.length}, Narrower: ${concept.narrower_ids.length}`
    item.appendChild(hierarchy)

    return item
  }

  private renderError(error: unknown): void {
    const message = error instanceof Error ? error.message : 'Unknown error'
    this.container.innerHTML = `<div class="error">Error: ${message}</div>`
  }
}
