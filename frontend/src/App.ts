import { TaxonomyList } from './components/taxonomies/TaxonomyList'
import { TaxonomyForm } from './components/taxonomies/TaxonomyForm'
import { SchemeList } from './components/schemes/SchemeList'
import { SchemeForm } from './components/schemes/SchemeForm'
import { ConceptList } from './components/concepts/ConceptList'
import { ConceptForm } from './components/concepts/ConceptForm'

export class App {
  private container: HTMLElement
  private currentView: 'taxonomies' | 'schemes' | 'concepts' = 'taxonomies'
  private selectedTaxonomyId?: string
  private selectedSchemeId?: string

  constructor(container: HTMLElement) {
    this.container = container
  }

  render(): void {
    this.container.innerHTML = `
      <div class="app">
        <header>
          <h1>Taxonomy Builder</h1>
          <nav>
            <button class="nav-btn" data-view="taxonomies">Taxonomies</button>
            <button class="nav-btn" data-view="schemes" ${!this.selectedTaxonomyId ? 'disabled' : ''}>Schemes</button>
            <button class="nav-btn" data-view="concepts" ${!this.selectedSchemeId ? 'disabled' : ''}>Concepts</button>
          </nav>
        </header>

        <main>
          <div id="view-container"></div>
        </main>
      </div>
    `

    // Set up navigation
    this.container.querySelectorAll('.nav-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const view = (e.target as HTMLElement).getAttribute('data-view') as
          | 'taxonomies'
          | 'schemes'
          | 'concepts'
        if (view) this.navigateTo(view)
      })
    })

    this.renderCurrentView()
  }

  private navigateTo(view: 'taxonomies' | 'schemes' | 'concepts'): void {
    this.currentView = view
    this.renderCurrentView()
  }

  private renderCurrentView(): void {
    const viewContainer = this.container.querySelector('#view-container') as HTMLElement

    if (!viewContainer) return

    viewContainer.innerHTML = ''

    switch (this.currentView) {
      case 'taxonomies':
        this.renderTaxonomiesView(viewContainer)
        break
      case 'schemes':
        if (this.selectedTaxonomyId) {
          this.renderSchemesView(viewContainer, this.selectedTaxonomyId)
        }
        break
      case 'concepts':
        if (this.selectedSchemeId) {
          this.renderConceptsView(viewContainer, this.selectedSchemeId)
        }
        break
    }
  }

  private renderTaxonomiesView(container: HTMLElement): void {
    container.innerHTML = `
      <div class="view-header">
        <h2>Taxonomies</h2>
        <button class="create-btn">Create Taxonomy</button>
      </div>
      <div id="taxonomy-form-container" style="display: none;"></div>
      <div id="taxonomy-list-container"></div>
    `

    const createBtn = container.querySelector('.create-btn') as HTMLButtonElement
    const formContainer = container.querySelector('#taxonomy-form-container') as HTMLElement
    const listContainer = container.querySelector('#taxonomy-list-container') as HTMLElement

    createBtn.addEventListener('click', () => {
      formContainer.style.display = 'block'
      const form = new TaxonomyForm(formContainer)
      form.render()
    })

    formContainer.addEventListener('taxonomy-created', () => {
      formContainer.style.display = 'none'
      list.render()
    })

    const list = new TaxonomyList(listContainer)
    list.render()

    // Handle taxonomy selection
    listContainer.addEventListener('click', (e) => {
      const item = (e.target as HTMLElement).closest('[data-taxonomy-id]')
      if (item) {
        this.selectedTaxonomyId = item.getAttribute('data-taxonomy-id') as string
        this.navigateTo('schemes')
      }
    })
  }

  private renderSchemesView(container: HTMLElement, taxonomyId: string): void {
    container.innerHTML = `
      <div class="view-header">
        <h2>Concept Schemes</h2>
        <button class="back-btn">← Back to Taxonomies</button>
        <button class="create-btn">Create Scheme</button>
      </div>
      <div id="scheme-form-container" style="display: none;"></div>
      <div id="scheme-list-container"></div>
    `

    const backBtn = container.querySelector('.back-btn') as HTMLButtonElement
    const createBtn = container.querySelector('.create-btn') as HTMLButtonElement
    const formContainer = container.querySelector('#scheme-form-container') as HTMLElement
    const listContainer = container.querySelector('#scheme-list-container') as HTMLElement

    backBtn.addEventListener('click', () => this.navigateTo('taxonomies'))

    createBtn.addEventListener('click', () => {
      formContainer.style.display = 'block'
      const form = new SchemeForm(formContainer, taxonomyId)
      form.render()
    })

    formContainer.addEventListener('scheme-created', () => {
      formContainer.style.display = 'none'
      list.render()
    })

    const list = new SchemeList(listContainer, taxonomyId)
    list.render()

    // Handle scheme selection
    listContainer.addEventListener('click', (e) => {
      const item = (e.target as HTMLElement).closest('[data-scheme-id]')
      if (item) {
        this.selectedSchemeId = item.getAttribute('data-scheme-id') as string
        this.navigateTo('concepts')
      }
    })
  }

  private renderConceptsView(container: HTMLElement, schemeId: string): void {
    container.innerHTML = `
      <div class="view-header">
        <h2>Concepts</h2>
        <button class="back-btn">← Back to Schemes</button>
        <button class="create-btn">Create Concept</button>
      </div>
      <div id="concept-form-container" style="display: none;"></div>
      <div id="concept-list-container"></div>
    `

    const backBtn = container.querySelector('.back-btn') as HTMLButtonElement
    const createBtn = container.querySelector('.create-btn') as HTMLButtonElement
    const formContainer = container.querySelector('#concept-form-container') as HTMLElement
    const listContainer = container.querySelector('#concept-list-container') as HTMLElement

    backBtn.addEventListener('click', () => this.navigateTo('schemes'))

    createBtn.addEventListener('click', () => {
      formContainer.style.display = 'block'
      const form = new ConceptForm(formContainer, schemeId)
      form.render()
    })

    formContainer.addEventListener('concept-created', () => {
      formContainer.style.display = 'none'
      list.render()
    })

    const list = new ConceptList(listContainer, schemeId)
    list.render()
  }
}
