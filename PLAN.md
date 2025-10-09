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

16. **Initialize Vite + TypeScript project**
    - Run `npm create vite@latest frontend -- --template vanilla-ts` in project root
    - Navigate to `frontend/` directory
    - Run `npm install` to install base dependencies
    - Verify dev server works: `npm run dev`
    - This creates:
      - `package.json` with Vite scripts
      - `tsconfig.json` with TypeScript config
      - `vite.config.ts` for Vite configuration
      - `src/main.ts` - entry point
      - `index.html` - main HTML file
      - `src/style.css` - base styles

17. **Configure TypeScript strict mode**
    - Update `tsconfig.json`:
      ```json
      {
        "compilerOptions": {
          "target": "ES2020",
          "useDefineForClassFields": true,
          "module": "ESNext",
          "lib": ["ES2020", "DOM", "DOM.Iterable"],
          "skipLibCheck": true,
          "strict": true,
          "noUnusedLocals": true,
          "noUnusedParameters": true,
          "noFallthroughCasesInSwitch": true,
          "moduleResolution": "bundler",
          "allowImportingTsExtensions": true,
          "resolveJsonModule": true,
          "isolatedModules": true,
          "noEmit": true,
          "esModuleInterop": true,
          "forceConsistentCasingInFileNames": true
        },
        "include": ["src"]
      }
      ```

18. **Install additional dependencies**
    - Testing: `npm install -D vitest @vitest/ui jsdom @testing-library/dom @testing-library/user-event`
    - HTTP client: `npm install ky` (modern fetch wrapper)
    - Visualization: `npm install d3 @types/d3`
    - Dev tools: `npm install -D @types/node`
    - Create `vitest.config.ts`:
      ```typescript
      import { defineConfig } from 'vitest/config'

      export default defineConfig({
        test: {
          environment: 'jsdom',
          globals: true,
        },
      })
      ```

19. **Configure linting and formatting**
    - Install ESLint: `npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin`
    - Install Prettier: `npm install -D prettier eslint-config-prettier`
    - Create `.eslintrc.json`:
      ```json
      {
        "parser": "@typescript-eslint/parser",
        "extends": [
          "eslint:recommended",
          "plugin:@typescript-eslint/recommended",
          "prettier"
        ],
        "plugins": ["@typescript-eslint"],
        "env": {
          "browser": true,
          "es2020": true
        },
        "rules": {
          "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
        }
      }
      ```
    - Create `.prettierrc`:
      ```json
      {
        "semi": false,
        "singleQuote": true,
        "trailingComma": "es5",
        "printWidth": 100
      }
      ```
    - Update `package.json` scripts:
      ```json
      {
        "scripts": {
          "dev": "vite",
          "build": "tsc && vite build",
          "preview": "vite preview",
          "test": "vitest",
          "test:ui": "vitest --ui",
          "lint": "eslint src --ext ts,tsx",
          "format": "prettier --write src"
        }
      }
      ```

20. **Create frontend directory structure**
    - Create directories:
      ```
      frontend/src/
      ├── api/              # API client
      │   ├── client.ts     # Base HTTP client
      │   ├── taxonomies.ts # Taxonomy API methods
      │   ├── schemes.ts    # ConceptScheme API methods
      │   └── concepts.ts   # Concept API methods
      ├── components/       # UI components
      │   ├── taxonomies/   # Taxonomy management
      │   ├── schemes/      # Scheme management
      │   ├── concepts/     # Concept management
      │   └── shared/       # Shared components (forms, buttons, etc.)
      ├── visualization/    # D3.js visualization
      │   └── hierarchy.ts  # Taxonomy hierarchy visualization
      ├── types/            # TypeScript types
      │   └── models.ts     # Domain models (Taxonomy, ConceptScheme, Concept)
      ├── utils/            # Utilities
      │   └── dom.ts        # DOM helpers
      └── main.ts           # Entry point
      ```
    - Create `tests/` directory structure mirroring `src/`:
      ```
      frontend/tests/
      ├── api/
      ├── components/
      ├── visualization/
      └── utils/
      ```

21. **Set up API base URL configuration**
    - Create `src/config.ts`:
      ```typescript
      export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      ```
    - Create `.env.development`:
      ```
      VITE_API_BASE_URL=http://localhost:8000
      ```
    - Create `.env.production`:
      ```
      VITE_API_BASE_URL=/api
      ```
    - Add `.env*` to `.gitignore` (except `.env.example`)

22. **Configure Vite proxy for development**
    - Update `vite.config.ts`:
      ```typescript
      import { defineConfig } from 'vite'

      export default defineConfig({
        server: {
          proxy: {
            '/api': {
              target: 'http://localhost:8000',
              changeOrigin: true,
            },
          },
        },
      })
      ```
    - This allows frontend to call `/api/taxonomies` instead of `http://localhost:8000/api/taxonomies`

23. **Verify setup**
    - Run `npm run lint` - should pass with no errors
    - Run `npm run format` - should format all files
    - Run `npm run test` - should run with 0 tests (no tests yet)
    - Run `npm run dev` - should start dev server
    - Commit initial frontend setup

### Phase 7: Frontend Implementation (TDD)

**Overview**: Build frontend incrementally following TDD. Start with type definitions, then API client, then UI components.

24. **Define TypeScript Types - Test First**

    **Part A: Domain Models**

    1. Create `src/types/models.ts` with TypeScript interfaces matching backend:
       ```typescript
       export interface Taxonomy {
         id: string
         name: string
         uri_prefix: string
         description?: string
         created_at: string
       }

       export interface TaxonomyCreate {
         id: string
         name: string
         uri_prefix: string
         description?: string
       }

       export interface TaxonomyUpdate {
         name?: string
         uri_prefix?: string
         description?: string
       }

       // Similar for ConceptScheme and Concept
       ```
    2. Write validation tests in `tests/types/models.test.ts`:
       - `test_taxonomy_interface_matches_api()` - Verify structure
       - `test_optional_fields_work()` - description can be undefined
    3. Run tests (RED)
    4. Ensure types compile with `npm run build`
    5. Run tests (GREEN)

    **Part B: API Response Types**

    1. Create `src/types/api.ts`:
       ```typescript
       export interface ApiError {
         detail: string
       }

       export interface ApiResponse<T> {
         data?: T
         error?: ApiError
       }
       ```
    2. Write type tests
    3. Run tests (RED → GREEN)

25. **Build API Client - Test First**

    **Part A: Base HTTP Client**

    1. Write tests for `src/api/client.ts` in `tests/api/client.test.ts`:
       - `test_get_request_returns_data()` - GET request succeeds
       - `test_post_request_sends_json()` - POST sends correct body
       - `test_put_request_updates()` - PUT sends updates
       - `test_delete_request_succeeds()` - DELETE works
       - `test_404_error_handling()` - Handles 404 responses
       - `test_409_error_handling()` - Handles 409 conflicts
       - `test_422_validation_error()` - Handles validation errors
       - `test_network_error_handling()` - Handles network failures
    2. Run tests (RED)
    3. Implement base client using `ky`:
       ```typescript
       import ky from 'ky'
       import { API_BASE_URL } from '../config'

       export const client = ky.create({
         prefixUrl: API_BASE_URL,
         headers: {
           'Content-Type': 'application/json',
         },
       })
       ```
    4. Implement error handling wrapper
    5. Run tests (GREEN)
    6. Refactor

    **Part B: Taxonomy API Client**

    1. Write tests for `src/api/taxonomies.ts` in `tests/api/taxonomies.test.ts`:
       - `test_create_taxonomy_posts_to_api()` - POST /api/taxonomies
       - `test_create_taxonomy_returns_created()` - Returns Taxonomy object
       - `test_list_taxonomies_gets_from_api()` - GET /api/taxonomies
       - `test_get_taxonomy_by_id()` - GET /api/taxonomies/{id}
       - `test_update_taxonomy_puts_to_api()` - PUT /api/taxonomies/{id}
       - `test_delete_taxonomy_calls_api()` - DELETE /api/taxonomies/{id}
       - `test_handles_duplicate_id_error()` - 409 → error message
       - `test_handles_not_found_error()` - 404 → error message
    2. Run tests (RED)
    3. Implement taxonomy API client:
       ```typescript
       import { client } from './client'
       import type { Taxonomy, TaxonomyCreate, TaxonomyUpdate } from '../types/models'

       export const taxonomyApi = {
         create: (data: TaxonomyCreate) =>
           client.post('api/taxonomies', { json: data }).json<Taxonomy>(),
         list: () =>
           client.get('api/taxonomies').json<Taxonomy[]>(),
         get: (id: string) =>
           client.get(`api/taxonomies/${id}`).json<Taxonomy>(),
         update: (id: string, data: TaxonomyUpdate) =>
           client.put(`api/taxonomies/${id}`, { json: data }).json<Taxonomy>(),
         delete: (id: string) =>
           client.delete(`api/taxonomies/${id}`),
       }
       ```
    4. Run tests (GREEN)
    5. Refactor

    **Part C: ConceptScheme & Concept API Clients**

    1. Write tests for `src/api/schemes.ts` following same pattern
    2. Write tests for `src/api/concepts.ts` including relationship endpoints:
       - `test_add_broader_relationship()` - POST /api/concepts/{id}/broader/{broader_id}
       - `test_remove_broader_relationship()` - DELETE /api/concepts/{id}/broader/{broader_id}
    3. Run tests (RED)
    4. Implement scheme and concept API clients
    5. Run tests (GREEN)
    6. Refactor

26. **Create Taxonomy Management UI - Test First**

    **Part A: Taxonomy List Component**

    1. Write tests for `src/components/taxonomies/TaxonomyList.ts` in `tests/components/taxonomies/TaxonomyList.test.ts`:
       - `test_renders_empty_state()` - Shows "No taxonomies" message
       - `test_renders_taxonomy_list()` - Displays taxonomies in list
       - `test_displays_taxonomy_properties()` - Shows id, name, uri_prefix
       - `test_loading_state_shown()` - Shows loading indicator during fetch
       - `test_error_state_shown()` - Shows error message on API failure
       - `test_click_taxonomy_navigates()` - Clicking taxonomy shows details
    2. Run tests (RED)
    3. Implement `TaxonomyList` class:
       ```typescript
       export class TaxonomyList {
         private container: HTMLElement
         private taxonomies: Taxonomy[] = []

         constructor(container: HTMLElement) {
           this.container = container
         }

         async render() {
           this.container.innerHTML = '<div class="loading">Loading...</div>'
           try {
             this.taxonomies = await taxonomyApi.list()
             this.renderList()
           } catch (error) {
             this.renderError(error)
           }
         }

         private renderList() {
           // Render taxonomy list
         }
       }
       ```
    4. Run tests (GREEN)
    5. Refactor

    **Part B: Create Taxonomy Form**

    1. Write tests for `src/components/taxonomies/TaxonomyForm.ts` in `tests/components/taxonomies/TaxonomyForm.test.ts`:
       - `test_renders_form_fields()` - Renders id, name, uri_prefix, description inputs
       - `test_validates_required_fields()` - Shows errors for missing fields
       - `test_validates_id_format()` - Validates slug format (lowercase-with-hyphens)
       - `test_validates_uri_format()` - Validates URI prefix format
       - `test_submits_valid_data()` - Calls API with form data
       - `test_shows_duplicate_error()` - Shows error for 409 response
       - `test_clears_form_on_success()` - Resets form after successful create
       - `test_emits_success_event()` - Dispatches custom event on success
    2. Run tests (RED)
    3. Implement `TaxonomyForm` class with validation
    4. Run tests (GREEN)
    5. Refactor

    **Part C: Edit & Delete Taxonomy**

    1. Write tests for edit functionality:
       - `test_form_populates_with_existing_data()` - Loads taxonomy for editing
       - `test_id_field_readonly_in_edit_mode()` - ID cannot be changed
       - `test_update_calls_put_endpoint()` - Calls PUT /api/taxonomies/{id}
    2. Write tests for delete functionality:
       - `test_delete_button_shows_confirmation()` - Confirms before delete
       - `test_delete_calls_api()` - Calls DELETE endpoint
       - `test_delete_removes_from_list()` - Updates UI after delete
    3. Run tests (RED)
    4. Implement edit and delete features
    5. Run tests (GREEN)
    6. Refactor

27. **Build ConceptScheme Management - Test First**

    **Part A: Scheme List Component**

    1. Write tests for `src/components/schemes/SchemeList.ts`:
       - `test_renders_schemes_for_taxonomy()` - Shows schemes for selected taxonomy
       - `test_empty_state_for_new_taxonomy()` - Shows "No schemes" message
       - `test_displays_scheme_properties()` - Shows id, name, uri, description
       - `test_click_scheme_shows_concepts()` - Navigates to concept view
    2. Run tests (RED)
    3. Implement `SchemeList` component
    4. Run tests (GREEN)
    5. Refactor

    **Part B: Create Scheme Form**

    1. Write tests for `src/components/schemes/SchemeForm.ts`:
       - `test_requires_taxonomy_context()` - Must be associated with taxonomy
       - `test_validates_scheme_id_format()` - Slug validation
       - `test_submits_to_correct_endpoint()` - POST /api/taxonomies/{taxonomy_id}/schemes
       - `test_shows_generated_uri()` - Displays computed URI from taxonomy prefix
    2. Run tests (RED)
    3. Implement `SchemeForm` component
    4. Run tests (GREEN)
    5. Refactor

    **Part C: Edit & Delete Scheme**

    1. Write tests for edit/delete (similar pattern to taxonomies)
    2. Run tests (RED)
    3. Implement edit and delete
    4. Run tests (GREEN)
    5. Refactor

28. **Implement Concept Management - Test First**

    **Part A: Concept List Component**

    1. Write tests for `src/components/concepts/ConceptList.ts`:
       - `test_renders_concepts_for_scheme()` - Shows concepts for selected scheme
       - `test_displays_concept_properties()` - Shows pref_label, definition, alt_labels
       - `test_displays_hierarchy_indicators()` - Shows broader/narrower counts
       - `test_click_concept_shows_details()` - Shows detail view
    2. Run tests (RED)
    3. Implement `ConceptList` component
    4. Run tests (GREEN)
    5. Refactor

    **Part B: Create Concept Form**

    1. Write tests for `src/components/concepts/ConceptForm.ts`:
       - `test_requires_scheme_context()` - Must be associated with scheme
       - `test_validates_pref_label_required()` - prefLabel is required
       - `test_handles_alt_labels_array()` - Multiple alt labels supported
       - `test_definition_optional()` - Definition not required
       - `test_submits_to_correct_endpoint()` - POST /api/schemes/{scheme_id}/concepts
    2. Run tests (RED)
    3. Implement `ConceptForm` component
    4. Run tests (GREEN)
    5. Refactor

    **Part C: Hierarchy Relationship Management**

    1. Write tests for `src/components/concepts/RelationshipManager.ts`:
       - `test_shows_current_broader_concepts()` - Lists broader concepts
       - `test_shows_current_narrower_concepts()` - Lists narrower concepts
       - `test_add_broader_concept_selector()` - Dropdown to select broader concept
       - `test_add_broader_calls_api()` - POST /api/concepts/{id}/broader/{broader_id}
       - `test_remove_broader_calls_api()` - DELETE /api/concepts/{id}/broader/{broader_id}
       - `test_prevents_self_reference()` - Cannot add self as broader
       - `test_shows_cycle_error()` - Displays error for cycle detection
       - `test_bidirectional_update()` - Shows relationship from both sides
    2. Run tests (RED)
    3. Implement `RelationshipManager` component
    4. Run tests (GREEN)
    5. Refactor

29. **Create Visualization Component - Test First**

    **Part A: Basic Hierarchy Rendering**

    1. Write tests for `src/visualization/HierarchyTree.ts`:
       - `test_renders_svg_container()` - Creates SVG element
       - `test_renders_tree_from_concepts()` - Converts flat concept list to tree
       - `test_positions_nodes_hierarchically()` - Uses D3 tree layout
       - `test_draws_links_between_nodes()` - Connects broader/narrower
       - `test_displays_concept_labels()` - Shows pref_label on nodes
    2. Run tests (RED)
    3. Implement basic D3 tree visualization:
       ```typescript
       import * as d3 from 'd3'
       import type { Concept } from '../types/models'

       export class HierarchyTree {
         private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>
         private width: number
         private height: number

         constructor(container: HTMLElement, width: number, height: number) {
           this.width = width
           this.height = height
           this.svg = d3.select(container)
             .append('svg')
             .attr('width', width)
             .attr('height', height)
         }

         render(concepts: Concept[]) {
           const root = this.buildHierarchy(concepts)
           const treeLayout = d3.tree().size([this.height, this.width])
           // ... render tree
         }

         private buildHierarchy(concepts: Concept[]): d3.HierarchyNode<Concept> {
           // Build tree from flat concept list using broader/narrower
         }
       }
       ```
    4. Run tests (GREEN)
    5. Refactor

    **Part B: Interactive Features**

    1. Write tests for interactivity:
       - `test_nodes_are_clickable()` - Click handler attached
       - `test_click_emits_event()` - Dispatches custom event with concept
       - `test_hover_highlights_path()` - Highlights path to root on hover
       - `test_zoom_and_pan_enabled()` - D3 zoom behavior works
    2. Run tests (RED)
    3. Implement click handlers and zoom
    4. Run tests (GREEN)
    5. Refactor

    **Part C: Collapsible Nodes**

    1. Write tests for collapse functionality:
       - `test_nodes_with_children_collapsible()` - Shows expand/collapse icon
       - `test_click_collapse_icon_hides_children()` - Collapses subtree
       - `test_collapsed_state_persisted()` - Remembers collapsed nodes
       - `test_expand_shows_children()` - Re-expands collapsed nodes
    2. Run tests (RED)
    3. Implement collapse/expand with animation
    4. Run tests (GREEN)
    5. Refactor

30. **Add Smart Discovery Features - Test First**

    **Part A: Concept Search**

    1. Write tests for `src/components/concepts/ConceptSearch.ts`:
       - `test_renders_search_input()` - Search box displayed
       - `test_filters_by_pref_label()` - Searches concept labels
       - `test_filters_by_definition()` - Searches definitions
       - `test_filters_by_alt_labels()` - Searches alternative labels
       - `test_highlights_search_results()` - Highlights matches in visualization
       - `test_clears_search()` - Clear button resets filter
    2. Run tests (RED)
    3. Implement search filtering
    4. Run tests (GREEN)
    5. Refactor

    **Part B: Similar Concept Highlighting**

    1. Write tests for similarity detection:
       - `test_finds_lexically_similar()` - Finds concepts with similar labels (Levenshtein distance)
       - `test_highlights_similar_concepts()` - Highlights in different color
       - `test_shows_similarity_score()` - Displays similarity percentage
       - `test_configurable_threshold()` - Adjustable similarity threshold
    2. Run tests (RED)
    3. Implement lexical similarity using string distance algorithm
    4. Run tests (GREEN)
    5. Refactor

    **Note**: Semantic similarity (using embeddings) is deferred to future phase

31. **Main Application Integration - Test First**

    **Part A: Application Shell**

    1. Write tests for `src/main.ts` / app initialization:
       - `test_renders_navigation()` - Shows taxonomy/scheme/concept nav
       - `test_taxonomy_view_default()` - Shows taxonomy list by default
       - `test_navigation_switches_views()` - Click nav changes active view
       - `test_breadcrumb_navigation()` - Shows current location (taxonomy > scheme > concept)
    2. Run tests (RED)
    3. Implement app shell with routing
    4. Run tests (GREEN)
    5. Refactor

    **Part B: State Management**

    1. Write tests for simple state manager:
       - `test_stores_selected_taxonomy()` - Tracks current taxonomy
       - `test_stores_selected_scheme()` - Tracks current scheme
       - `test_state_change_emits_event()` - Notifies listeners
       - `test_components_react_to_state()` - Components update on state change
    2. Run tests (RED)
    3. Implement simple pub/sub state manager (no external library)
    4. Run tests (GREEN)
    5. Refactor

32. **Styling and UX Polish**

    1. Create CSS files:
       - `src/styles/base.css` - Reset, typography, colors
       - `src/styles/components.css` - Component styles
       - `src/styles/visualization.css` - D3 tree styles
    2. Implement responsive layout (mobile-friendly)
    3. Add loading states and transitions
    4. Error message styling
    5. Accessibility (ARIA labels, keyboard navigation)

    **No tests required for styling** - manual testing in browser

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
