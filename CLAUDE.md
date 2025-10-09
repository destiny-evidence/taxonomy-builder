# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a taxonomy-builder interface for creating taxonomies to support evidence repositories, built using SKOS (Simple Knowledge Organization System) standards. The application allows users to build hierarchical concept schemes with smart features for discovering related concepts.

## Technology Stack

- **Backend**: Python 3.14 with FastAPI
- **Frontend**: Vanilla TypeScript
- **Package Management**: uv (Python package manager)
- **Testing**: pytest (backend), frontend testing framework TBD

## Approach

- **TDD (Test-Driven Development)**: Follow the Red-Green-Refactor cycle strictly
  - RED: Write tests first, ensure they fail in the expected way
  - GREEN: Write minimum code to make tests pass
  - REFACTOR: Clean up code while keeping tests green
- **Incremental Development**: Build one feature at a time, completing full TDD cycle before moving on
- **Both Unit and Integration Tests**: Test at service layer (mocked dependencies) and API layer (full HTTP)

## Local setup

- asdf is used as a version manager for python and node

## Architecture

The system is designed around SKOS ConceptSchemes with these key components:

### Core Domain Concepts

- **Taxonomies**: Collections of multiple SKOS ConceptSchemes with URI prefixes
- **ConceptSchemes**: Hierarchical concept organizations (e.g., "Intervention", "Climate Impact", "Context", "Health Outcome")
- **Concepts**: Individual taxonomy nodes with hierarchical relationships
- **URI Management**: Each taxonomy includes a URI prefix for generating concept identifiers

### Application Structure

**Backend Layers** (Service-Repository Pattern):
- **API Layer** (`api/`): FastAPI routers handling HTTP requests/responses
- **Service Layer** (`services/`): Business logic, validation, raises ValueError on errors
- **Repository Layer** (`db/`): Data access abstraction (currently in-memory, will migrate to SQLite)
- **Models** (`models/`): Pydantic models for validation and serialization

**Error Handling Pattern**:
- Service layer raises `ValueError` for business logic errors
- API layer catches `ValueError` and converts to appropriate HTTP status (404, 409, etc.)
- Pydantic handles validation errors automatically (422 responses)

**Frontend** (not yet implemented):
- TypeScript interface with visualization capabilities for taxonomy hierarchy
- Smart Discovery: Features to reveal lexically and semantically similar concepts
- Visualization Engine: Clear hierarchical display without overwhelming complexity

## Development Commands

### Backend (Python/FastAPI)

```bash
# Install dependencies (from backend/ directory)
uv install

# Run development server
cd backend && uv run fastapi dev src/taxonomy_builder/main.py

# Run tests
cd backend && uv run pytest        # All tests
cd backend && uv run pytest -xvs   # Verbose, stop on first failure

# Code formatting and linting
uv run ruff format                 # Auto-format code
uv run ruff check                  # Check for issues
uv run ruff check --fix            # Auto-fix issues
```

### Frontend (TypeScript)

*Not yet implemented*

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build production
npm run build

# Run tests
npm run test

# Type checking
npm run typecheck

# Linting
npm run lint
```

## Key Implementation Considerations

**Data Models**:
- User-provided IDs are slugs (lowercase, hyphens, numbers only) - e.g., "climate-health-2024"
- IDs are immutable - cannot be changed via update
- URI prefixes must be valid URIs (http:// or https://)
- Timestamps use `datetime.now(UTC)` for consistency

**API Conventions**:
- POST returns 201 Created with created resource
- GET returns 200 OK (list or single resource)
- PUT returns 200 OK with updated resource
- DELETE returns 204 No Content
- 404 for resource not found
- 409 Conflict for duplicate IDs
- 422 Unprocessable Entity for validation errors

**SKOS Compliance** (future):
- All taxonomies must conform to SKOS standards for semantic web compatibility
- URI generation follows consistent patterns using taxonomy-specific prefixes
- Hierarchical relationships use SKOS broader/narrower properties

## Project Status

**Completed**:
- ✓ Backend initialization with uv and FastAPI
- ✓ Testing framework (pytest) with TDD workflow
- ✓ Development tooling (ruff for linting/formatting)
- ✓ Taxonomy CRUD API (Create, Read, Update, Delete)
  - POST /api/taxonomies (create)
  - GET /api/taxonomies (list all)
  - GET /api/taxonomies/{id} (get by ID)
  - PUT /api/taxonomies/{id} (update)
  - DELETE /api/taxonomies/{id} (delete)
- ✓ 38 tests passing (unit + integration)
- ✓ In-memory repository implementation

**In Progress**:
- ConceptScheme CRUD (Phase 3)

**Not Started**:
- Frontend TypeScript project
- SQLite persistence layer
- SKOS serialization/export
- Smart discovery features
