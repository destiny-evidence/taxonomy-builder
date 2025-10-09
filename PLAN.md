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

6. **Create Taxonomy - Test First**
   - Write test: POST /api/taxonomies creates a taxonomy
   - Write test: Response includes generated ID and URI prefix
   - Make tests fail (no implementation)
   - Define Taxonomy Pydantic model (name, URI prefix, description)
   - Implement POST /api/taxonomies endpoint
   - Add basic in-memory storage (upgrade to SQLite later)
   - Make tests pass
   - Refactor

7. **List & Get Taxonomy - Test First**
   - Write test: GET /api/taxonomies returns list
   - Write test: GET /api/taxonomies/{id} returns specific taxonomy
   - Write test: GET /api/taxonomies/{id} returns 404 if not found
   - Make tests fail
   - Implement endpoints
   - Make tests pass
   - Refactor

8. **Update & Delete Taxonomy - Test First**
   - Write test: PUT /api/taxonomies/{id} updates taxonomy
   - Write test: DELETE /api/taxonomies/{id} removes taxonomy
   - Write test: Both return 404 if not found
   - Make tests fail
   - Implement endpoints
   - Make tests pass
   - Refactor

### Phase 3: ConceptScheme CRUD (TDD)

9. **Create ConceptScheme - Test First**
   - Write test: POST /api/taxonomies/{taxonomy_id}/schemes creates scheme
   - Write test: ConceptScheme has name, URI (generated from taxonomy prefix)
   - Make tests fail
   - Define ConceptScheme Pydantic model
   - Implement endpoint
   - Make tests pass
   - Refactor

10. **ConceptScheme CRUD - Test First**
    - Write tests: GET, PUT, DELETE for concept schemes
    - Write test: Schemes are scoped to taxonomy
    - Make tests fail
    - Implement endpoints
    - Make tests pass
    - Refactor

### Phase 4: Concept CRUD & Hierarchy (TDD)

11. **Create Concept - Test First**
    - Write test: POST /api/schemes/{scheme_id}/concepts creates concept
    - Write test: Concept has prefLabel, URI (from taxonomy prefix)
    - Make tests fail
    - Define Concept Pydantic model
    - Implement endpoint
    - Make tests pass
    - Refactor

12. **Concept Hierarchy - Test First**
    - Write test: Add broader/narrower relationships
    - Write test: GET concept includes hierarchy info
    - Write test: Prevent circular relationships
    - Make tests fail
    - Implement relationship management
    - Make tests pass
    - Refactor

13. **Concept CRUD & Search - Test First**
    - Write tests: GET, PUT, DELETE for concepts
    - Write test: Search concepts by prefLabel
    - Make tests fail
    - Implement endpoints
    - Make tests pass
    - Refactor

### Phase 5: Persistence Layer (TDD)

14. **SQLite Storage - Test First**
    - Write tests for database operations (create, read, update, delete)
    - Write test for data persistence across app restarts
    - Make tests fail
    - Implement SQLite storage layer
    - Migrate from in-memory to SQLite
    - Make tests pass
    - Refactor

15. **SKOS Serialization - Test First**
    - Write test: Export taxonomy as SKOS/Turtle
    - Write test: Validate SKOS structure with RDFLib
    - Make tests fail
    - Implement SKOS export using RDFLib
    - Make tests pass
    - Refactor

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
    - CSS framework (optional - consider Tailwind or vanilla CSS)

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
