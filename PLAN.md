# Taxonomy Builder - Setup Plan

This document outlines the step-by-step plan for initializing the taxonomy-builder application.

## Project Structure

```
taxonomy-builder/
├── backend/                 # Python/FastAPI backend
│   ├── src/
│   │   └── taxonomy_builder/
│   │       ├── __init__.py
│   │       ├── main.py      # FastAPI app entry point
│   │       ├── api/         # API routes
│   │       ├── models/      # Data models (SKOS concepts, schemes, taxonomies)
│   │       ├── services/    # Business logic
│   │       └── db/          # Database/storage layer
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py      # pytest fixtures
│   │   └── test_*.py        # Test modules
│   ├── pyproject.toml       # Python dependencies and project config
│   └── README.md
├── frontend/                # TypeScript frontend
│   ├── src/
│   │   ├── main.ts
│   │   ├── api/             # API client
│   │   ├── components/      # UI components
│   │   ├── visualization/   # Taxonomy visualization
│   │   └── types/           # TypeScript types
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts       # Build tool config
│   └── README.md
├── .tool-versions           # asdf version definitions
├── CLAUDE.md
├── REQUIREMENTS.md
├── PLAN.md                  # This file
└── README.md
```

## Setup Steps

### Phase 1: Backend Initialization ✓

1. **Initialize uv project** ✓
   - Create `backend/` directory
   - Run `uv init --app` in backend directory
   - This creates initial `pyproject.toml` and basic structure

2. **Configure Python dependencies** ✓
   - Add FastAPI and uvicorn for the web framework
   - Add RDFLib for SKOS/RDF handling
   - Add pytest and pytest-asyncio for testing
   - Add httpx for testing API endpoints
   - Add ruff for linting and formatting
   - Add mypy for type checking
   - Consider SQLite or PostgreSQL for storage (start with SQLite)

3. **Create backend directory structure** ✓
   - `src/taxonomy_builder/` - main package
   - `src/taxonomy_builder/api/` - API routes
   - `src/taxonomy_builder/models/` - SKOS models (Taxonomy, ConceptScheme, Concept)
   - `src/taxonomy_builder/services/` - business logic
   - `src/taxonomy_builder/db/` - database layer
   - `tests/` - test directory

4. **Set up FastAPI application (TDD)** ✓
   - Write test for basic FastAPI app startup
   - Write test for health check endpoint
   - Make tests fail (expected - no implementation yet)
   - Create `main.py` with basic FastAPI app
   - Configure CORS for frontend integration
   - Implement health check endpoint
   - Make tests pass
   - Refactor for clarity

5. **Configure development tooling** ✓
   - Configure ruff in `pyproject.toml`
   - Set up pytest configuration
   - Add pre-commit hooks (optional but recommended)

### Phase 2: Taxonomy CRUD (TDD)

6. **Create Taxonomy - Test First** ✓

   **Testing Strategy**: Both unit tests (service layer) and integration tests (API layer)

   **Unit Tests** (`tests/test_taxonomy_service.py`): ✓
   - `test_create_taxonomy_returns_taxonomy()` - Service returns created taxonomy
   - `test_create_taxonomy_with_valid_id()` - ID is user-provided string
   - `test_create_taxonomy_validates_uri_prefix()` - URI prefix format validation
   - `test_create_taxonomy_stores_in_repository()` - Verify storage interaction
   - `test_create_taxonomy_rejects_duplicate_id()` - Business rule: IDs must be unique
   - `test_create_taxonomy_id_format_validation()` - ID must be valid slug (lowercase, hyphens)

   **Integration Tests** (`tests/test_taxonomy_api.py`): ✓
   - `test_post_taxonomy_returns_201_created()` - HTTP status code
   - `test_post_taxonomy_returns_created_taxonomy()` - Response structure
   - `test_post_taxonomy_validates_required_fields()` - 422 for missing id/name/uri_prefix
   - `test_post_taxonomy_validates_uri_prefix_format()` - 422 for invalid URI format
   - `test_post_taxonomy_rejects_duplicate_id()` - 409 Conflict for duplicate ID

   **Implementation**: ✓
   - Pydantic models: `TaxonomyCreate`, `Taxonomy` with validation
   - `InMemoryTaxonomyRepository` with `save()`, `exists()` methods
   - `TaxonomyService.create_taxonomy()` with business logic
   - API route `POST /api/taxonomies`
   - 16 tests passing, all code passes ruff checks

   **Data Models**:
   - `TaxonomyCreate` (input): id, name, uri_prefix, description (optional)
   - `Taxonomy` (output): id, name, uri_prefix, description, created_at

   **Notes**:
   - ID is user-provided slug (e.g., "climate-health-2024")
   - Later phases may use internal primary keys for persistence, but externally we use the slug

7. **List Taxonomies - Test First** ✓

   **Part A: GET /api/taxonomies (list all)** ✓

   1. Write unit tests for `TaxonomyService.list_taxonomies()`: ✓
      - `test_list_taxonomies_returns_all()` - Returns all taxonomies
      - `test_list_taxonomies_returns_empty_list()` - Returns [] when none exist
   2. Write integration tests for GET /api/taxonomies: ✓
      - `test_get_taxonomies_returns_200_and_empty_list()` - Returns 200 with []
      - `test_get_taxonomies_returns_created_taxonomies()` - Returns all created items
   3. Run tests (RED) ✓
   4. Add `get_all()` to TaxonomyRepository ✓
   5. Implement `TaxonomyService.list_taxonomies()` ✓
   6. Add GET /api/taxonomies endpoint ✓
   7. Run tests (GREEN) ✓
   8. Refactor ✓

   **Part B: GET /api/taxonomies/{id} (get by ID)** ✓

   1. Write unit tests for `TaxonomyService.get_taxonomy(id)`: ✓
      - `test_get_taxonomy_by_id_returns_taxonomy()` - Finds and returns taxonomy
      - `test_get_taxonomy_by_id_raises_when_not_found()` - Raises ValueError
   2. Write integration tests for GET /api/taxonomies/{id}`: ✓
      - `test_get_taxonomy_by_id_returns_200()` - Returns 200 with taxonomy
      - `test_get_taxonomy_by_id_returns_404_when_not_found()` - Returns 404
   3. Run tests (RED) ✓
   4. Add `get_by_id()` to TaxonomyRepository ✓
   5. Implement `TaxonomyService.get_taxonomy(id)` - raises ValueError if not found ✓
   6. Add GET /api/taxonomies/{id} endpoint - catches ValueError → 404 ✓
   7. Run tests (GREEN) ✓
   8. Refactor ✓

   **Implementation**: ✓
   - Added `get_all()` and `get_by_id()` to repository
   - `TaxonomyService.list_taxonomies()` and `get_taxonomy(id)` methods
   - API routes `GET /api/taxonomies` and `GET /api/taxonomies/{id}`
   - 27 tests passing, all code passes ruff checks

   **Response Models**:
   - List endpoint returns `list[Taxonomy]`
   - Get endpoint returns single `Taxonomy`
   - 404 response: `{"detail": "Taxonomy with ID 'x' not found"}`

8. **Update & Delete Taxonomy - Test First** ✓

   **Part A: PUT /api/taxonomies/{id} (update)** ✓

   1. Write unit tests for `TaxonomyService.update_taxonomy(id, data)`: ✓
      - `test_update_taxonomy_returns_updated_taxonomy()` - Updates and returns taxonomy
      - `test_update_taxonomy_raises_when_not_found()` - Raises ValueError if not found
      - `test_update_taxonomy_allows_partial_updates()` - Can update just name, uri_prefix, or description
   2. Write integration tests for PUT /api/taxonomies/{id}: ✓
      - `test_put_taxonomy_returns_200()` - Returns 200 with updated taxonomy
      - `test_put_taxonomy_updates_fields()` - Verify fields are actually updated
      - `test_put_taxonomy_returns_404_when_not_found()` - Returns 404
   3. Run tests (RED) ✓
   4. Add `TaxonomyUpdate` Pydantic model with optional fields ✓
   5. Add `update()` to TaxonomyRepository ✓
   6. Implement `TaxonomyService.update_taxonomy(id, data)` ✓
   7. Add PUT /api/taxonomies/{id} endpoint - catches ValueError → 404 ✓
   8. Run tests (GREEN) ✓
   9. Refactor ✓

   **Part B: DELETE /api/taxonomies/{id} (delete)** ✓

   1. Write unit tests for `TaxonomyService.delete_taxonomy(id)`: ✓
      - `test_delete_taxonomy_removes_taxonomy()` - Deletes successfully
      - `test_delete_taxonomy_raises_when_not_found()` - Raises ValueError if not found
   2. Write integration tests for DELETE /api/taxonomies/{id}: ✓
      - `test_delete_taxonomy_returns_204()` - Returns 204 No Content
      - `test_delete_taxonomy_actually_deletes()` - Verify taxonomy is gone
      - `test_delete_taxonomy_returns_404_when_not_found()` - Returns 404
   3. Run tests (RED) ✓
   4. Add `delete()` to TaxonomyRepository ✓
   5. Implement `TaxonomyService.delete_taxonomy(id)` ✓
   6. Add DELETE /api/taxonomies/{id} endpoint - catches ValueError → 404 ✓
   7. Run tests (GREEN) ✓
   8. Refactor ✓

   **Implementation**: ✓
   - Added `TaxonomyUpdate` Pydantic model with optional fields
   - Added `update()` and `delete()` to repository
   - `TaxonomyService.update_taxonomy()` and `delete_taxonomy()` methods
   - API routes `PUT /api/taxonomies/{id}` and `DELETE /api/taxonomies/{id}`
   - 38 tests passing, all code passes ruff checks

   **Data Models**:
   - `TaxonomyUpdate`: All fields optional (name, uri_prefix, description)
   - ID cannot be changed via update
   - Update endpoint returns updated `Taxonomy`
   - Delete endpoint returns 204 No Content on success

### Phase 3: ConceptScheme CRUD (TDD)

**Overview**: ConceptSchemes are collections of concepts within a taxonomy. Each scheme belongs to a taxonomy and inherits its URI prefix.

9. **Create ConceptScheme - Test First** ✓

   **Part A: POST /api/taxonomies/{taxonomy_id}/schemes (create)** ✓

   1. Write unit tests for `ConceptSchemeService.create_scheme()`: ✓
      - `test_create_scheme_returns_scheme()` - Creates and returns scheme
      - `test_create_scheme_requires_valid_taxonomy()` - Raises ValueError if taxonomy not found
      - `test_create_scheme_rejects_duplicate_id()` - Raises ValueError for duplicate ID within taxonomy
      - `test_create_scheme_generates_uri()` - URI uses taxonomy's uri_prefix + scheme id
   2. Write integration tests for POST /api/taxonomies/{taxonomy_id}/schemes: ✓
      - `test_post_scheme_returns_201()` - Returns 201 with created scheme
      - `test_post_scheme_returns_404_for_invalid_taxonomy()` - Returns 404
      - `test_post_scheme_returns_409_for_duplicate()` - Returns 409 Conflict
   3. Run tests (RED) ✓
   4. Create `ConceptScheme` and `ConceptSchemeCreate` Pydantic models ✓
   5. Add `ConceptSchemeRepository` with save/exists methods ✓
   6. Implement `ConceptSchemeService.create_scheme()` ✓
   7. Add POST /api/taxonomies/{taxonomy_id}/schemes endpoint ✓
   8. Run tests (GREEN) ✓
   9. Refactor ✓

   **Data Models**: ✓
   - `ConceptSchemeCreate`: id, name, description (optional)
   - `ConceptScheme`: id, taxonomy_id, name, uri, description, created_at
   - URI format: `{taxonomy.uri_prefix}{scheme.id}`

10. **List & Get ConceptScheme - Test First** ✓

    **Part A: GET /api/taxonomies/{taxonomy_id}/schemes (list)** ✓

    1. Write unit tests for `ConceptSchemeService.list_schemes(taxonomy_id)`: ✓
       - `test_list_schemes_returns_all_for_taxonomy()` - Returns only schemes for that taxonomy
       - `test_list_schemes_requires_valid_taxonomy()` - Raises ValueError if taxonomy not found
       - `test_list_schemes_returns_empty_list()` - Returns [] when none exist
    2. Write integration tests for GET /api/taxonomies/{taxonomy_id}/schemes: ✓
       - `test_get_schemes_returns_200()` - Returns 200 with list
       - `test_get_schemes_filters_by_taxonomy()` - Only returns schemes for specified taxonomy
       - `test_get_schemes_returns_404_for_invalid_taxonomy()` - Returns 404
    3. Run tests (RED) ✓
    4. Add `get_by_taxonomy()` to ConceptSchemeRepository ✓
    5. Implement `ConceptSchemeService.list_schemes()` ✓
    6. Add GET /api/taxonomies/{taxonomy_id}/schemes endpoint ✓
    7. Run tests (GREEN) ✓
    8. Refactor ✓

    **Part B: GET /api/schemes/{scheme_id} (get by ID)** ✓

    1. Write unit tests for `ConceptSchemeService.get_scheme(scheme_id)`: ✓
       - `test_get_scheme_returns_scheme()` - Returns requested scheme
       - `test_get_scheme_raises_when_not_found()` - Raises ValueError
    2. Write integration tests for GET /api/schemes/{scheme_id}`: ✓
       - `test_get_scheme_returns_200()` - Returns 200 with scheme
       - `test_get_scheme_returns_404_when_not_found()` - Returns 404
    3. Run tests (RED) ✓
    4. Add `get_by_id()` to ConceptSchemeRepository ✓
    5. Implement `ConceptSchemeService.get_scheme()` ✓
    6. Add GET /api/schemes/{scheme_id} endpoint ✓
    7. Run tests (GREEN) ✓
    8. Refactor ✓

11. **Update & Delete ConceptScheme - Test First** ✓

    **Part A: PUT /api/schemes/{scheme_id} (update)** ✓

    1. Write unit tests for `ConceptSchemeService.update_scheme()`: ✓
       - `test_update_scheme_returns_updated()` - Updates and returns scheme
       - `test_update_scheme_raises_when_not_found()` - Raises ValueError
       - `test_update_scheme_allows_partial_updates()` - Can update name or description
    2. Write integration tests for PUT /api/schemes/{scheme_id}: ✓
       - `test_put_scheme_returns_200()` - Returns 200 with updated scheme
       - `test_put_scheme_returns_404_when_not_found()` - Returns 404
    3. Run tests (RED) ✓
    4. Create `ConceptSchemeUpdate` Pydantic model ✓
    5. Add `update()` to ConceptSchemeRepository ✓
    6. Implement `ConceptSchemeService.update_scheme()` ✓
    7. Add PUT /api/schemes/{scheme_id} endpoint ✓
    8. Run tests (GREEN) ✓
    9. Refactor ✓

    **Part B: DELETE /api/schemes/{scheme_id} (delete)** ✓

    1. Write unit tests for `ConceptSchemeService.delete_scheme()`: ✓
       - `test_delete_scheme_removes_scheme()` - Deletes successfully
       - `test_delete_scheme_raises_when_not_found()` - Raises ValueError
       - `test_delete_scheme_cascades_to_concepts()` - Deletes all concepts in scheme (future)
    2. Write integration tests for DELETE /api/schemes/{scheme_id}: ✓
       - `test_delete_scheme_returns_204()` - Returns 204 No Content
       - `test_delete_scheme_returns_404_when_not_found()` - Returns 404
    3. Run tests (RED) ✓
    4. Add `delete()` to ConceptSchemeRepository ✓
    5. Implement `ConceptSchemeService.delete_scheme()` ✓
    6. Add DELETE /api/schemes/{scheme_id} endpoint ✓
    7. Run tests (GREEN) ✓
    8. Refactor ✓

    **Implementation**: ✓
    - Added `ConceptScheme`, `ConceptSchemeCreate`, and `ConceptSchemeUpdate` Pydantic models
    - Added `InMemoryConceptSchemeRepository` with all CRUD methods
    - `ConceptSchemeService` with dependency on TaxonomyService for validation
    - API routes for all ConceptScheme operations
    - 64 tests passing (26 new ConceptScheme tests), all code passes ruff checks

    **API Routes Summary**: ✓
    - POST /api/taxonomies/{taxonomy_id}/schemes - Create scheme (201)
    - GET /api/taxonomies/{taxonomy_id}/schemes - List schemes for taxonomy (200)
    - GET /api/schemes/{scheme_id} - Get scheme by ID (200/404)
    - PUT /api/schemes/{scheme_id} - Update scheme (200/404)
    - DELETE /api/schemes/{scheme_id} - Delete scheme (204/404)

### Phase 4: Concept CRUD & Hierarchy (TDD)

**Overview**: Concepts are individual nodes in a taxonomy with SKOS properties (prefLabel, definition, etc.) and hierarchical relationships (broader/narrower).

12. **Create Concept - Test First** ✓

    **Part A: POST /api/schemes/{scheme_id}/concepts (create)** ✓

    1. Write unit tests for `ConceptService.create_concept()`:
       - `test_create_concept_returns_concept()` - Creates and returns concept
       - `test_create_concept_requires_valid_scheme()` - Raises ValueError if scheme not found
       - `test_create_concept_rejects_duplicate_id()` - Raises ValueError for duplicate ID within scheme
       - `test_create_concept_generates_uri()` - URI uses scheme's taxonomy uri_prefix + concept id
       - `test_create_concept_validates_pref_label()` - prefLabel is required
    2. Write integration tests for POST /api/schemes/{scheme_id}/concepts:
       - `test_post_concept_returns_201()` - Returns 201 with created concept
       - `test_post_concept_returns_404_for_invalid_scheme()` - Returns 404
       - `test_post_concept_returns_409_for_duplicate()` - Returns 409 Conflict
    3. Run tests (RED)
    4. Create `Concept` and `ConceptCreate` Pydantic models
    5. Add `ConceptRepository` with save/exists methods
    6. Implement `ConceptService.create_concept()`
    7. Add POST /api/schemes/{scheme_id}/concepts endpoint
    8. Run tests (GREEN)
    9. Refactor

    **Data Models**:
    - `ConceptCreate`: id, pref_label, definition (optional), alt_labels (optional list)
    - `Concept`: id, scheme_id, uri, pref_label, definition, alt_labels, broader_ids, narrower_ids, created_at
    - URI format: `{scheme.taxonomy.uri_prefix}{concept.id}`
    - Initially, broader_ids and narrower_ids are empty arrays

13. **List & Get Concept - Test First** ✓

    **Part A: GET /api/schemes/{scheme_id}/concepts (list)** ✓

    1. Write unit tests for `ConceptService.list_concepts(scheme_id)`:
       - `test_list_concepts_returns_all_for_scheme()` - Returns only concepts for that scheme
       - `test_list_concepts_requires_valid_scheme()` - Raises ValueError if scheme not found
       - `test_list_concepts_returns_empty_list()` - Returns [] when none exist
    2. Write integration tests for GET /api/schemes/{scheme_id}/concepts:
       - `test_get_concepts_returns_200()` - Returns 200 with list
       - `test_get_concepts_filters_by_scheme()` - Only returns concepts for specified scheme
       - `test_get_concepts_returns_404_for_invalid_scheme()` - Returns 404
    3. Run tests (RED)
    4. Add `get_by_scheme()` to ConceptRepository
    5. Implement `ConceptService.list_concepts()`
    6. Add GET /api/schemes/{scheme_id}/concepts endpoint
    7. Run tests (GREEN)
    8. Refactor

    **Part B: GET /api/concepts/{concept_id} (get by ID)** ✓

    1. Write unit tests for `ConceptService.get_concept(concept_id)`:
       - `test_get_concept_returns_concept()` - Returns requested concept
       - `test_get_concept_raises_when_not_found()` - Raises ValueError
       - `test_get_concept_includes_relationships()` - Returns broader_ids and narrower_ids
    2. Write integration tests for GET /api/concepts/{concept_id}:
       - `test_get_concept_returns_200()` - Returns 200 with concept
       - `test_get_concept_returns_404_when_not_found()` - Returns 404
    3. Run tests (RED)
    4. Add `get_by_id()` to ConceptRepository
    5. Implement `ConceptService.get_concept()`
    6. Add GET /api/concepts/{concept_id} endpoint
    7. Run tests (GREEN)
    8. Refactor

14. **Update & Delete Concept - Test First** ✓

    **Part A: PUT /api/concepts/{concept_id} (update)** ✓

    1. Write unit tests for `ConceptService.update_concept()`:
       - `test_update_concept_returns_updated()` - Updates and returns concept
       - `test_update_concept_raises_when_not_found()` - Raises ValueError
       - `test_update_concept_allows_partial_updates()` - Can update prefLabel, definition, altLabels
    2. Write integration tests for PUT /api/concepts/{concept_id}:
       - `test_put_concept_returns_200()` - Returns 200 with updated concept
       - `test_put_concept_returns_404_when_not_found()` - Returns 404
    3. Run tests (RED)
    4. Create `ConceptUpdate` Pydantic model
    5. Add `update()` to ConceptRepository
    6. Implement `ConceptService.update_concept()`
    7. Add PUT /api/concepts/{concept_id} endpoint
    8. Run tests (GREEN)
    9. Refactor

    **Part B: DELETE /api/concepts/{concept_id} (delete)** ✓

    1. Write unit tests for `ConceptService.delete_concept()`:
       - `test_delete_concept_removes_concept()` - Deletes successfully
       - `test_delete_concept_raises_when_not_found()` - Raises ValueError
       - `test_delete_concept_updates_relationships()` - Removes from broader/narrower of related concepts
    2. Write integration tests for DELETE /api/concepts/{concept_id}:
       - `test_delete_concept_returns_204()` - Returns 204 No Content
       - `test_delete_concept_returns_404_when_not_found()` - Returns 404
    3. Run tests (RED)
    4. Add `delete()` to ConceptRepository
    5. Implement `ConceptService.delete_concept()` with relationship cleanup
    6. Add DELETE /api/concepts/{concept_id} endpoint
    7. Run tests (GREEN)
    8. Refactor

15. **Concept Hierarchy Relationships - Test First** ✓

    **Part A: POST /api/concepts/{concept_id}/broader/{broader_id} (add broader)** ✓

    1. Write unit tests for `ConceptService.add_broader()`:
       - `test_add_broader_creates_bidirectional_link()` - Updates both concepts
       - `test_add_broader_raises_for_invalid_concepts()` - Raises ValueError if either not found
       - `test_add_broader_prevents_self_reference()` - Raises ValueError if concept_id == broader_id
       - `test_add_broader_prevents_cycles()` - Raises ValueError if would create cycle
    2. Write integration tests for POST /api/concepts/{concept_id}/broader/{broader_id}:
       - `test_post_broader_returns_200()` - Returns 200 with updated concept
       - `test_post_broader_returns_404_for_invalid_concept()` - Returns 404
       - `test_post_broader_returns_400_for_cycle()` - Returns 400 Bad Request
    3. Run tests (RED)
    4. Implement `ConceptService.add_broader()` with cycle detection
    5. Add POST /api/concepts/{concept_id}/broader/{broader_id} endpoint
    6. Run tests (GREEN)
    7. Refactor

    **Part B: DELETE /api/concepts/{concept_id}/broader/{broader_id} (remove broader)** ✓

    1. Write unit tests for `ConceptService.remove_broader()`:
       - `test_remove_broader_removes_bidirectional_link()` - Updates both concepts
       - `test_remove_broader_raises_for_invalid_concepts()` - Raises ValueError if either not found
       - `test_remove_broader_handles_nonexistent_relationship()` - No error if relationship doesn't exist
    2. Write integration tests for DELETE /api/concepts/{concept_id}/broader/{broader_id}:
       - `test_delete_broader_returns_200()` - Returns 200 with updated concept
       - `test_delete_broader_returns_404_for_invalid_concept()` - Returns 404
    3. Run tests (RED)
    4. Implement `ConceptService.remove_broader()`
    5. Add DELETE /api/concepts/{concept_id}/broader/{broader_id} endpoint
    6. Run tests (GREEN)
    7. Refactor

    **API Routes Summary**:
    - POST /api/schemes/{scheme_id}/concepts - Create concept (201)
    - GET /api/schemes/{scheme_id}/concepts - List concepts for scheme (200)
    - GET /api/concepts/{concept_id} - Get concept by ID (200/404)
    - PUT /api/concepts/{concept_id} - Update concept (200/404)
    - DELETE /api/concepts/{concept_id} - Delete concept (204/404)
    - POST /api/concepts/{concept_id}/broader/{broader_id} - Add broader relationship (200/404/400)
    - DELETE /api/concepts/{concept_id}/broader/{broader_id} - Remove broader relationship (200/404)

    **Cycle Detection**: Use depth-first search to detect cycles when adding broader relationships

    **Implementation**: ✓
    - Added `Concept`, `ConceptCreate`, and `ConceptUpdate` Pydantic models
    - Added `InMemoryConceptRepository` with all CRUD methods
    - `ConceptService` with dependency on ConceptSchemeService for validation
    - Implemented bidirectional relationship management with cycle detection
    - API routes for all Concept operations including hierarchy relationships
    - 105 tests passing (41 new Concept tests), all code passes ruff checks

### Phase 5: Persistence Layer (TDD)

**Overview**: Migrate from in-memory storage to SQLite for data persistence. Keep the repository abstraction intact.

16. **SQLite Repository Implementation - Test First**

    **Part A: Database Schema & Setup**

    1. Design SQLite schema:
       - `taxonomies` table: id (TEXT PK), name, uri_prefix, description, created_at
       - `concept_schemes` table: id (TEXT PK), taxonomy_id (FK), name, uri, description, created_at
       - `concepts` table: id (TEXT PK), scheme_id (FK), uri, pref_label, definition, alt_labels (JSON), created_at
       - `concept_relationships` table: concept_id (FK), broader_id (FK), UNIQUE(concept_id, broader_id)
    2. Create database initialization script
    3. Write migration utility to convert in-memory data to SQLite

    **Part B: SQLite Taxonomy Repository**

    1. Write integration tests for `SQLiteTaxonomyRepository`:
       - `test_save_persists_to_database()` - Data survives repository recreation
       - `test_get_by_id_retrieves_from_database()` - Retrieves saved data
       - `test_update_modifies_database()` - Updates persist
       - `test_delete_removes_from_database()` - Deletions persist
       - `test_concurrent_access()` - Multiple repository instances work correctly
    2. Run tests (RED)
    3. Implement `SQLiteTaxonomyRepository` implementing `TaxonomyRepository` interface
    4. Update service to use SQLite repository (via dependency injection)
    5. Run tests (GREEN)
    6. Refactor

    **Part C: SQLite ConceptScheme & Concept Repositories**

    1. Write integration tests for `SQLiteConceptSchemeRepository`:
       - Same pattern as Taxonomy: save, get, update, delete, persistence
       - `test_get_by_taxonomy_filters_correctly()` - Retrieves only schemes for taxonomy
    2. Write integration tests for `SQLiteConceptRepository`:
       - Same pattern as Taxonomy: save, get, update, delete, persistence
       - `test_get_by_scheme_filters_correctly()` - Retrieves only concepts for scheme
       - `test_relationships_persist()` - broader/narrower relationships survive restart
    3. Run tests (RED)
    4. Implement `SQLiteConceptSchemeRepository` and `SQLiteConceptRepository`
    5. Update services to use SQLite repositories
    6. Run tests (GREEN)
    7. Refactor

    **Part D: Repository Factory & Configuration**

    1. Create repository factory to switch between in-memory and SQLite
    2. Add configuration for database file path
    3. Update main.py to use factory pattern
    4. Keep in-memory repositories for testing (faster)
    5. Use SQLite repositories for production

    **Database File**: `taxonomy_builder.db` in project root (configurable via env var)

17. **SKOS Export - Test First**

    **Part A: GET /api/taxonomies/{taxonomy_id}/export/turtle (export)**

    1. Write unit tests for `SkosExportService.export_taxonomy()`:
       - `test_export_creates_skos_concept_scheme()` - Creates skos:ConceptScheme for each scheme
       - `test_export_creates_skos_concepts()` - Creates skos:Concept for each concept
       - `test_export_includes_broader_narrower()` - Includes skos:broader and skos:narrower
       - `test_export_includes_labels()` - Includes skos:prefLabel and skos:altLabel
       - `test_export_includes_definitions()` - Includes skos:definition
    2. Write integration tests for GET /api/taxonomies/{taxonomy_id}/export/turtle:
       - `test_export_returns_turtle_content_type()` - Returns text/turtle
       - `test_export_returns_valid_rdf()` - Can be parsed by RDFLib
       - `test_export_returns_404_for_invalid_taxonomy()` - Returns 404
    3. Run tests (RED)
    4. Implement `SkosExportService` using RDFLib
    5. Add GET /api/taxonomies/{taxonomy_id}/export/turtle endpoint
    6. Run tests (GREEN)
    7. Refactor

    **Part B: Validation & Additional Formats**

    1. Write tests for SKOS validation:
       - `test_export_validates_against_skos_schema()` - Valid SKOS structure
       - `test_export_handles_empty_taxonomy()` - Returns valid RDF even if no schemes/concepts
    2. Write tests for JSON-LD export:
       - `test_export_jsonld_format()` - Returns JSON-LD when requested
    3. Run tests (RED)
    4. Implement validation and JSON-LD export
    5. Add GET /api/taxonomies/{taxonomy_id}/export/jsonld endpoint
    6. Run tests (GREEN)
    7. Refactor

    **SKOS Mapping**:
    - Taxonomy → `skos:Collection` (container for multiple ConceptSchemes)
    - ConceptScheme → `skos:ConceptScheme`
    - Concept → `skos:Concept`
    - concept.pref_label → `skos:prefLabel`
    - concept.alt_labels → `skos:altLabel`
    - concept.definition → `skos:definition`
    - broader relationship → `skos:broader` / `skos:narrower`

    **Export Endpoints**:
    - GET /api/taxonomies/{taxonomy_id}/export/turtle - Turtle format (text/turtle)
    - GET /api/taxonomies/{taxonomy_id}/export/jsonld - JSON-LD format (application/ld+json)

### Phase 6: Frontend Initialization

16. **Initialize TypeScript project**
    - Create `frontend/` directory
    - Initialize npm/pnpm project
    - Set up Vite as build tool
    - Configure TypeScript with strict settings
    - Add ESLint and Prettier

17. **Install frontend dependencies**
    - Vite for development and building
    - TypeScript
    - Fetch API or axios for HTTP requests
    - D3.js or similar for visualization (tree/hierarchy layout)
    - NO CSS framework (vanilla CSS)

18. **Create frontend structure**
    - `src/main.ts` - entry point
    - `src/api/` - API client for backend
    - `src/components/` - UI components
    - `src/visualization/` - taxonomy visualization logic
    - `src/types/` - TypeScript type definitions
    - `index.html` - main HTML file

### Phase 7: Frontend Implementation (TDD)

19. **Build API client - Test First**
    - Write tests for API client methods
    - Test error handling and loading states
    - Make tests fail
    - Implement type-safe client for backend API
    - Make tests pass
    - Refactor

20. **Create taxonomy management UI - Test First**
    - Write tests for taxonomy list component
    - Write tests for create/edit/delete taxonomy forms
    - Make tests fail
    - Implement UI components
    - Make tests pass
    - Refactor

21. **Build concept scheme management - Test First**
    - Write tests for scheme components
    - Make tests fail
    - Implement add/edit/delete concept schemes UI
    - Make tests pass
    - Refactor

22. **Implement concept management - Test First**
    - Write tests for concept CRUD UI
    - Write tests for hierarchy relationship management
    - Make tests fail
    - Implement components
    - Make tests pass
    - Refactor

23. **Create visualization component - Test First**
    - Write tests for hierarchy rendering
    - Write tests for interactive navigation
    - Make tests fail
    - Implement tree/hierarchy visualization with D3.js
    - Add collapsible nodes
    - Make tests pass
    - Refactor

24. **Add smart discovery features - Test First**
    - Write tests for concept search
    - Write tests for highlighting similar concepts
    - Make tests fail
    - Implement search and similarity features
    - Make tests pass
    - Refactor

### Phase 8: Integration & Polish

25. **Integration testing**
    - Test frontend-backend integration
    - End-to-end testing (consider Playwright)

26. **Documentation**
    - Update README with setup instructions
    - API documentation (FastAPI auto-generated docs)
    - User guide for taxonomy building

27. **Development tooling**
    - Set up .tool-versions for asdf
    - Add development scripts to package.json and pyproject.toml
    - Consider Docker setup for deployment

## Technology Decisions

### Backend

- **Python 3.14** - Latest Python version
- **uv** - Fast, modern Python package manager
- **FastAPI** - Modern, fast web framework with auto-generated OpenAPI docs
- **RDFLib** - Python library for working with RDF/SKOS
- **Pydantic** - Data validation and serialization
- **pytest** - Testing framework
- **ruff** - Fast linter and formatter
- **SQLite** - Simple database to start (can migrate to PostgreSQL later)

### Frontend

- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **Vanilla TypeScript** - No framework overhead, full control
- **D3.js** - Powerful visualization library for hierarchies
- **Vitest** - Fast unit testing (integrates with Vite)

## TDD Workflow

Every feature follows the Red-Green-Refactor cycle:

1. **Red**: Write a failing test that describes the desired behavior
2. **Green**: Write the minimum code needed to make the test pass
3. **Refactor**: Clean up the code while keeping tests green

This approach ensures:

- All code is tested
- Tests validate actual requirements
- Design emerges from usage patterns
- Refactoring is safe with test coverage

## Next Steps

1. Start with Phase 1: Backend Initialization
2. **Strictly follow TDD**: Every feature starts with a failing test
3. Build incrementally: get basic CRUD working before adding smart features
4. Keep SKOS standards in mind throughout development
5. Refactor regularly to maintain code quality

## Open Questions

1. **Storage format**: Store as RDF/Turtle files, or relational database with SKOS export?
   - Recommendation: Start with SQLite for editing, export to Turtle/RDF for consumption
2. **Authentication**: Do we need user management?
   - Defer until requirements are clearer
3. **Semantic similarity**: What approach for finding similar concepts?
   - Phase 2 feature: consider spaCy or sentence-transformers
4. **Deployment**: Docker? Serverless? Traditional hosting?
   - Defer until MVP is working
