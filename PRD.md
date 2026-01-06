# Taxonomy Builder - Product Requirements Document

## Overview

This project is a web-based taxonomy management tool for creating, editing, and maintaining SKOS vocabularies used within an evidence data platform. It enables domain experts and information professionals to build and curate taxonomies that support tagging, classification, and faceted search across living evidence repositories.

## Problem Statement

Living evidence repositories require well-structured taxonomies to organize and retrieve evidence effectively. Currently, there is no purpose-built tool for:

- Creating and maintaining SKOS-compliant taxonomies
- Connecting internal vocabularies to established external standards (MeSH, SNOMED, Cochrane, etc.)
- Collaboratively reviewing and versioning taxonomy changes
- Exporting taxonomies in standard formats for integration with evidence platforms

## Users

**Primary users:**

- **Domain experts** — Subject matter experts who understand the taxonomy content but may have limited technical background. They need an intuitive interface for defining concepts and relationships.
- **Librarians and taxonomists** — Information professionals with expertise in classification systems. They ensure taxonomies follow best practices and maintain consistency with external standards.

## Core Concepts

The application organizes taxonomies within a hierarchical structure:

```
Project → Concept Scheme → Concept
```

| Term | Description |
|------|-------------|
| Project | A container grouping related concept schemes (e.g., per evidence repository) |
| Concept Scheme | A taxonomy or vocabulary as a whole (SKOS) |
| Concept | An individual term/idea within a scheme (SKOS)
| prefLabel | The preferred/canonical label for a concept |
| altLabel | Alternative labels, synonyms, abbreviations |
| definition | Formal definition of the concept |
| scopeNote | Usage guidance and scope clarification |
| broader/narrower | Hierarchical parent-child relationships |
| related | Associative relationships within a scheme |
| exactMatch/closeMatch | Mappings to external vocabularies |

## Functional Requirements

### MVP (Phase 1)

#### Project Management

- Create, edit, and delete projects
- Define project metadata (name, description)
- List and navigate concept schemes within a project

#### Concept Scheme Management

- Create, edit, and delete concept schemes within a project
- Define scheme metadata (title, description, publisher, version)
- View scheme as hierarchical tree and flat list

#### Concept Management

- Create, edit, and delete concepts within a scheme
- Assign prefLabel (required) and altLabels
- Add definitions and scope notes
- Establish broader/narrower hierarchical relationships
- Create related associations between concepts
- Drag-and-drop reordering within hierarchy

#### Import/Export

- Import existing taxonomies from SKOS RDF files (RDF/XML, Turtle, JSON-LD)
- Export schemes in SKOS RDF formats
- Validate SKOS compliance on import/export

#### Version History

- Track all changes with timestamps and user attribution
- View change history for schemes and individual concepts
- Compare versions side-by-side
- Revert to previous versions

#### Authentication

- Microsoft Entra External ID integration (aligned with evidence repository SSO)
- Role-based permissions (viewer, editor, reviewer, admin)

*Note: Authentication is required for MVP but should be implemented after core taxonomy management functionality is working.*

### Phase 2

#### External Vocabulary Integration

- Search and browse external vocabularies (MeSH, SNOMED, ICD, Cochrane)
- Create exactMatch/closeMatch mappings to external concepts
- Display external concept metadata inline

#### Extended Import

- Import from CSV/spreadsheet formats
- Bulk import with field mapping

#### API Access

- REST API for programmatic taxonomy access
- API documentation and authentication

#### Review Workflow

- Draft/published states for concept schemes
- Submit changes for review
- Approve or request changes with comments
- Publish approved changes

### Future Considerations

- Multi-language label support
- Taxonomy visualization and graph views
- Concept usage analytics (where concepts are applied in evidence platform)
- Automated mapping suggestions to external vocabularies

## Non-Functional Requirements

### Usability

- Intuitive interface for non-technical users
- Keyboard navigation for efficient editing
- Responsive design for various screen sizes

### Performance

- Support taxonomies ranging from <20 to 500+ concepts
- Tree navigation remains responsive at scale
- Search across concepts returns results within 500ms

### Integration

- Decoupled from evidence platform database (export-based integration)
- Standard SKOS RDF output for interoperability

## Technology Stack

### Backend

| Component | Technology | Notes |
|-----------|------------|-------|
| Language | Python 3.14 | Type hints throughout, native UUIDv7 |
| Framework | FastAPI | Aligns with evidence repository |
| Database | PostgreSQL | Version history, JSON support |
| ORM | SQLAlchemy 2.0 | Async support, type-safe queries |
| Migrations | Alembic | Schema versioning |
| RDF/SKOS | RDFLib | Parse and serialize SKOS formats |
| Testing | pytest | With pytest-asyncio |

### Frontend

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Preact | ~3KB, React-compatible API |
| Language | TypeScript | Strict mode |
| Build | Vite | Fast dev server, optimized builds |
| Testing | Vitest | Vite-native test runner |

### Infrastructure

| Component | Technology | Notes |
|-----------|------------|-------|
| Containers | Docker | Multi-stage builds |
| Auth | Microsoft Entra External ID | Aligned with evidence repository |

## Success Metrics

- Time to create a new concept (target: <30 seconds)
- Time to publish a reviewed change (target: <2 minutes)
- SKOS validation pass rate on export (target: 100%)
- User satisfaction score from domain experts

## Open Questions

1. Are there existing taxonomies to migrate into the application?
2. What are the specific evidence platform integration points for exported taxonomies?
3. Should concepts support custom metadata fields beyond SKOS standard properties?
4. Should access control be scoped to projects (different teams access different projects)?

## Appendix: External Vocabularies

Vocabularies anticipated for mapping:

**Medical/Health:**

- MeSH (Medical Subject Headings)
- SNOMED CT
- ICD (International Classification of Diseases)

**Research/Academic:**

- PICO (Population, Intervention, Comparison, Outcome)
- Cochrane taxonomy
