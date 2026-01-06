# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development approach

### Write tests first

We do TDD. That counts double for an agent. Write tests, think about the
interface they test and refine the interface before moving on to write the code
to make the test pass.

### Commit regularly with simple commit messages

Commit after each implementation of a feature or fix of a bug. Keep commit messages short and describe rationale. Don't include unnecessary lists.

### Prefer a new commit over --amend

We can always squash commits later, but using --amend is more likely to cause trouble for ourselves.

## Project Overview

Taxonomy Builder is a web-based tool for creating and managing SKOS vocabularies. The data model follows the SKOS hierarchy: **Project → Concept Scheme → Concept**. Concepts support polyhierarchy through broader/narrower relationships (DAG structure, not strict tree).

## Development Commands

### Backend (Python/FastAPI)

```bash
cd backend

# Install dependencies
uv sync --all-extras

# Run development server
uv run uvicorn taxonomy_builder.main:app --reload

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/test_api/test_concepts.py

# Run single test
uv run pytest tests/test_api/test_concepts.py::test_create_concept -v

# Lint
uv run ruff check src tests

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

### Frontend (Preact/TypeScript)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Type check
npm run typecheck

# Build
npm run build
```

### Database

```bash
# Start PostgreSQL (creates both main and test databases)
docker compose up -d

# Database URLs (configured via TAXONOMY_DATABASE_URL env var)
# Main: postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder
# Test: postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_test
```

## Architecture

### Backend Structure

```
backend/src/taxonomy_builder/
├── main.py              # FastAPI app, lifespan, router registration
├── database.py          # DatabaseSessionManager (async sessions with auto-commit)
├── config.py            # Pydantic settings (TAXONOMY_ env prefix)
├── models/              # SQLAlchemy models (Project, ConceptScheme, Concept, ConceptBroader)
├── schemas/             # Pydantic schemas for API request/response
├── services/            # Business logic layer
└── api/                 # FastAPI routers
```

**Key patterns:**

- `DatabaseSessionManager` handles session lifecycle with auto-commit on success, rollback on error
- Services receive `AsyncSession` as dependency, use `session.flush()` for persistence within request
- Tests use transaction rollback for isolation (see `conftest.py`)
- Concept `uri` is a computed property from `scheme.uri + identifier`

### Frontend Structure

```
frontend/src/
├── api/                 # Typed API client functions
├── state/               # Preact Signals for reactive state
├── components/          # UI components (common/, layout/, tree/, concepts/, etc.)
├── pages/               # Route pages (ProjectsPage, ProjectDetailPage, SchemeDetailPage)
└── types/models.ts      # TypeScript interfaces matching backend schemas
```

**Key patterns:**

- State management uses `@preact/signals` (signals, computed)
- Tree view handles DAG by showing concepts under all their parents with multi-parent indicators
- `renderTree` computed signal transforms backend tree data into render nodes with path-based identity

### API Routes

| Endpoint | Description |
|----------|-------------|
| `/api/projects` | Project CRUD |
| `/api/projects/{id}/schemes` | List/create schemes for project |
| `/api/schemes/{id}` | Scheme CRUD |
| `/api/schemes/{id}/concepts` | List/create concepts for scheme |
| `/api/schemes/{id}/tree` | Get hierarchical tree (DAG) |
| `/api/concepts/{id}` | Concept CRUD |
| `/api/concepts/{id}/broader` | Add broader relationship |
| `/api/concepts/{id}/broader/{bid}` | Remove broader relationship |

## Testing

Backend tests use `pytest-asyncio` with session-scoped event loop. The `db_session` fixture provides transaction isolation - use `flush()` not `commit()` in tests.

Frontend uses Vitest with jsdom for component testing.
