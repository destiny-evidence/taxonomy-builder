import { TaxonomyList } from './components/taxonomies/TaxonomyList'
import { TaxonomyForm } from './components/taxonomies/TaxonomyForm'
import { SchemeList } from './components/schemes/SchemeList'
import { SchemeForm } from './components/schemes/SchemeForm'
import { ConceptList } from './components/concepts/ConceptList'
import { ConceptForm } from './components/concepts/ConceptForm'
import { RelationshipManager } from './components/concepts/RelationshipManager'
import { conceptApi } from './api/concepts'
import type { Taxonomy, ConceptScheme, Concept } from './types/models'

export class App {
  private container: HTMLElement
  private selectedTaxonomy?: Taxonomy
  private selectedScheme?: ConceptScheme
  private selectedConcept?: Concept
  private allConcepts: Concept[] = []

  constructor(container: HTMLElement) {
    this.container = container
  }

  render(): void {
    this.container.innerHTML = `
      <div class="app">
        <header>
          <h1>Taxonomy Builder</h1>
          <div class="breadcrumb">
            <span class="breadcrumb-item active" data-nav="taxonomies">Taxonomies</span>
            ${this.selectedTaxonomy ? `<span class="breadcrumb-sep">›</span><span class="breadcrumb-item ${!this.selectedScheme ? 'active' : ''}" data-nav="schemes">${this.selectedTaxonomy.name}</span>` : ''}
            ${this.selectedScheme ? `<span class="breadcrumb-sep">›</span><span class="breadcrumb-item ${!this.selectedConcept ? 'active' : ''}" data-nav="concepts">${this.selectedScheme.name}</span>` : ''}
            ${this.selectedConcept ? `<span class="breadcrumb-sep">›</span><span class="breadcrumb-item active">${this.selectedConcept.pref_label}</span>` : ''}
          </div>
        </header>

        <main>
          <div class="layout">
            <aside class="sidebar">
              <div id="sidebar-content"></div>
            </aside>
            <section class="main-content">
              <div id="main-view"></div>
            </section>
          </div>
        </main>
      </div>
    `

    // Setup breadcrumb navigation
    this.container.querySelectorAll('[data-nav]').forEach((el) => {
      el.addEventListener('click', () => {
        const nav = el.getAttribute('data-nav')
        if (nav === 'taxonomies') {
          this.selectedTaxonomy = undefined
          this.selectedScheme = undefined
          this.selectedConcept = undefined
          this.render()
        } else if (nav === 'schemes') {
          this.selectedScheme = undefined
          this.selectedConcept = undefined
          this.render()
        } else if (nav === 'concepts') {
          this.selectedConcept = undefined
          this.render()
        }
      })
    })

    this.renderView()
  }

  private renderView(): void {
    const sidebar = this.container.querySelector('#sidebar-content') as HTMLElement
    const main = this.container.querySelector('#main-view') as HTMLElement

    if (!sidebar || !main) return

    if (!this.selectedTaxonomy) {
      this.renderTaxonomyView(sidebar, main)
    } else if (!this.selectedScheme) {
      this.renderSchemeView(sidebar, main)
    } else if (!this.selectedConcept) {
      this.renderConceptView(sidebar, main)
    } else {
      this.renderConceptDetailView(sidebar, main)
    }
  }

  private renderTaxonomyView(sidebar: HTMLElement, main: HTMLElement): void {
    sidebar.innerHTML = '<div class="sidebar-empty">Select a taxonomy to view its schemes</div>'

    main.innerHTML = `
      <div class="view-header">
        <h2>Taxonomies</h2>
        <button class="create-btn">+ New Taxonomy</button>
      </div>
      <div id="form-container" style="display: none;"></div>
      <div id="list-container"></div>
    `

    const createBtn = main.querySelector('.create-btn') as HTMLButtonElement
    const formContainer = main.querySelector('#form-container') as HTMLElement
    const listContainer = main.querySelector('#list-container') as HTMLElement

    createBtn.addEventListener('click', () => {
      formContainer.style.display = formContainer.style.display === 'none' ? 'block' : 'none'
      if (formContainer.style.display === 'block') {
        const form = new TaxonomyForm(formContainer)
        form.render()
      }
    })

    formContainer.addEventListener('taxonomy-created', () => {
      formContainer.style.display = 'none'
      list.render()
    })

    const list = new TaxonomyList(listContainer)
    list.render()

    listContainer.addEventListener('click', async (e) => {
      const item = (e.target as HTMLElement).closest('[data-taxonomy-id]')
      if (item) {
        const id = item.getAttribute('data-taxonomy-id') as string
        // Fetch full taxonomy data
        const taxonomies = await list['taxonomies'] // Access private field
        this.selectedTaxonomy = taxonomies.find((t: Taxonomy) => t.id === id)
        this.render()
      }
    })
  }

  private renderSchemeView(sidebar: HTMLElement, main: HTMLElement): void {
    if (!this.selectedTaxonomy) return

    sidebar.innerHTML = `
      <div class="sidebar-section">
        <h3>Taxonomy</h3>
        <div class="taxonomy-info">
          <div class="info-label">Name</div>
          <div class="info-value">${this.selectedTaxonomy.name}</div>
          <div class="info-label">ID</div>
          <div class="info-value code">${this.selectedTaxonomy.id}</div>
          <div class="info-label">URI Prefix</div>
          <div class="info-value code">${this.selectedTaxonomy.uri_prefix}</div>
        </div>
      </div>
    `

    main.innerHTML = `
      <div class="view-header">
        <h2>Concept Schemes</h2>
        <button class="create-btn">+ New Scheme</button>
      </div>
      <div id="form-container" style="display: none;"></div>
      <div id="list-container"></div>
    `

    const createBtn = main.querySelector('.create-btn') as HTMLButtonElement
    const formContainer = main.querySelector('#form-container') as HTMLElement
    const listContainer = main.querySelector('#list-container') as HTMLElement

    createBtn.addEventListener('click', () => {
      formContainer.style.display = formContainer.style.display === 'none' ? 'block' : 'none'
      if (formContainer.style.display === 'block') {
        const form = new SchemeForm(formContainer, this.selectedTaxonomy!.id)
        form.render()
      }
    })

    formContainer.addEventListener('scheme-created', () => {
      formContainer.style.display = 'none'
      list.render()
    })

    const list = new SchemeList(listContainer, this.selectedTaxonomy.id)
    list.render()

    listContainer.addEventListener('click', async (e) => {
      const item = (e.target as HTMLElement).closest('[data-scheme-id]')
      if (item) {
        const id = item.getAttribute('data-scheme-id') as string
        const schemes = await list['schemes']
        this.selectedScheme = schemes.find((s: ConceptScheme) => s.id === id)
        this.render()
      }
    })
  }

  private renderConceptView(sidebar: HTMLElement, main: HTMLElement): void {
    if (!this.selectedScheme) return

    sidebar.innerHTML = `
      <div class="sidebar-section">
        <h3>Scheme</h3>
        <div class="scheme-info">
          <div class="info-label">Name</div>
          <div class="info-value">${this.selectedScheme.name}</div>
          <div class="info-label">ID</div>
          <div class="info-value code">${this.selectedScheme.id}</div>
        </div>
      </div>
    `

    main.innerHTML = `
      <div class="view-header">
        <h2>Concepts</h2>
        <button class="create-btn">+ New Concept</button>
      </div>
      <div id="form-container" style="display: none;"></div>
      <div id="list-container"></div>
    `

    const createBtn = main.querySelector('.create-btn') as HTMLButtonElement
    const formContainer = main.querySelector('#form-container') as HTMLElement
    const listContainer = main.querySelector('#list-container') as HTMLElement

    createBtn.addEventListener('click', () => {
      formContainer.style.display = formContainer.style.display === 'none' ? 'block' : 'none'
      if (formContainer.style.display === 'block') {
        const form = new ConceptForm(formContainer, this.selectedScheme!.id)
        form.render()
      }
    })

    formContainer.addEventListener('concept-created', () => {
      formContainer.style.display = 'none'
      list.render()
    })

    const list = new ConceptList(listContainer, this.selectedScheme.id)
    list.render()

    listContainer.addEventListener('click', async (e) => {
      const item = (e.target as HTMLElement).closest('[data-concept-id]')
      if (item) {
        const id = item.getAttribute('data-concept-id') as string
        const concepts = await list['concepts']
        this.selectedConcept = concepts.find((c: Concept) => c.id === id)
        this.allConcepts = concepts
        this.render()
      }
    })
  }

  private renderConceptDetailView(sidebar: HTMLElement, main: HTMLElement): void {
    if (!this.selectedConcept) return

    sidebar.innerHTML = `
      <div class="sidebar-section">
        <h3>Concept Details</h3>
        <div class="concept-info">
          <div class="info-label">Preferred Label</div>
          <div class="info-value">${this.selectedConcept.pref_label}</div>
          <div class="info-label">ID</div>
          <div class="info-value code">${this.selectedConcept.id}</div>
          ${this.selectedConcept.definition ? `
            <div class="info-label">Definition</div>
            <div class="info-value">${this.selectedConcept.definition}</div>
          ` : ''}
          ${this.selectedConcept.alt_labels.length > 0 ? `
            <div class="info-label">Alternative Labels</div>
            <div class="info-value">${this.selectedConcept.alt_labels.join(', ')}</div>
          ` : ''}
        </div>
      </div>
    `

    main.innerHTML = `
      <div class="view-header">
        <h2>Manage Relationships: ${this.selectedConcept.pref_label}</h2>
      </div>
      <div id="relationship-container"></div>
    `

    const relationshipContainer = main.querySelector('#relationship-container') as HTMLElement

    const manager = new RelationshipManager(
      relationshipContainer,
      this.selectedConcept,
      this.allConcepts
    )
    manager.render()

    relationshipContainer.addEventListener('relationship-updated', async () => {
      // Refresh the concept data
      const updated = await conceptApi.get(this.selectedConcept!.id)
      this.selectedConcept = updated
      // Refresh all concepts
      this.allConcepts = await conceptApi.list(this.selectedScheme!.id)
      this.render()
    })
  }
}
