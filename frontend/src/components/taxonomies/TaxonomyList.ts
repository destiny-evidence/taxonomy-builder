import { taxonomyApi } from '../../api/taxonomies'
import type { Taxonomy } from '../../types/models'

export class TaxonomyList {
  private container: HTMLElement
  private taxonomies: Taxonomy[] = []

  constructor(container: HTMLElement) {
    this.container = container
  }

  async render(): Promise<void> {
    this.container.innerHTML = '<div class="loading">Loading...</div>'

    try {
      this.taxonomies = await taxonomyApi.list()
      this.renderList()
    } catch (error) {
      this.renderError(error)
    }
  }

  private renderList(): void {
    if (this.taxonomies.length === 0) {
      this.container.innerHTML = '<div class="empty-state">No taxonomies</div>'
      return
    }

    const list = document.createElement('div')
    list.className = 'taxonomy-list'

    this.taxonomies.forEach((taxonomy) => {
      const item = this.createTaxonomyItem(taxonomy)
      list.appendChild(item)
    })

    this.container.innerHTML = ''
    this.container.appendChild(list)
  }

  private createTaxonomyItem(taxonomy: Taxonomy): HTMLElement {
    const item = document.createElement('div')
    item.className = 'taxonomy-item'
    item.setAttribute('data-taxonomy-id', taxonomy.id)

    const title = document.createElement('h3')
    title.textContent = taxonomy.name

    const id = document.createElement('div')
    id.className = 'taxonomy-id'
    id.textContent = taxonomy.id

    const uri = document.createElement('div')
    uri.className = 'taxonomy-uri'
    uri.textContent = taxonomy.uri_prefix

    if (taxonomy.description) {
      const description = document.createElement('div')
      description.className = 'taxonomy-description'
      description.textContent = taxonomy.description
      item.appendChild(description)
    }

    item.appendChild(title)
    item.appendChild(id)
    item.appendChild(uri)

    return item
  }

  private renderError(error: unknown): void {
    const message = error instanceof Error ? error.message : 'Unknown error'
    this.container.innerHTML = `<div class="error">Error: ${message}</div>`
  }
}
