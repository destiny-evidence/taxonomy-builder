import { schemeApi } from '../../api/schemes'
import type { ConceptScheme } from '../../types/models'

export class SchemeList {
  private container: HTMLElement
  private taxonomyId: string
  private schemes: ConceptScheme[] = []

  constructor(container: HTMLElement, taxonomyId: string) {
    this.container = container
    this.taxonomyId = taxonomyId
  }

  async render(): Promise<void> {
    this.container.innerHTML = '<div class="loading">Loading...</div>'

    try {
      this.schemes = await schemeApi.list(this.taxonomyId)
      this.renderList()
    } catch (error) {
      this.renderError(error)
    }
  }

  private renderList(): void {
    if (this.schemes.length === 0) {
      this.container.innerHTML = '<div class="empty-state">No schemes</div>'
      return
    }

    const list = document.createElement('div')
    list.className = 'scheme-list'

    this.schemes.forEach((scheme) => {
      const item = this.createSchemeItem(scheme)
      list.appendChild(item)
    })

    this.container.innerHTML = ''
    this.container.appendChild(list)
  }

  private createSchemeItem(scheme: ConceptScheme): HTMLElement {
    const item = document.createElement('div')
    item.className = 'scheme-item'
    item.setAttribute('data-scheme-id', scheme.id)

    const title = document.createElement('h3')
    title.textContent = scheme.name

    const id = document.createElement('div')
    id.className = 'scheme-id'
    id.textContent = scheme.id

    const uri = document.createElement('div')
    uri.className = 'scheme-uri'
    uri.textContent = scheme.uri

    item.appendChild(title)
    item.appendChild(id)
    item.appendChild(uri)

    if (scheme.description) {
      const description = document.createElement('div')
      description.className = 'scheme-description'
      description.textContent = scheme.description
      item.appendChild(description)
    }

    return item
  }

  private renderError(error: unknown): void {
    const message = error instanceof Error ? error.message : 'Unknown error'
    this.container.innerHTML = `<div class="error">Error: ${message}</div>`
  }
}
