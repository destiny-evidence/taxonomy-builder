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

- Write tests first. Make sure they fail in the expected way, then write enough code to make them pass.
- Once tests pass, re-visit the code and clean it up to improve readability and re-usabilty.

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

- **API Layer**: FastAPI backend providing RESTful endpoints for taxonomy management
- **Frontend**: TypeScript interface with visualization capabilities for taxonomy hierarchy
- **Smart Discovery**: Features to reveal lexically and semantically similar concepts
- **Visualization Engine**: Clear hierarchical display without overwhelming complexity

## Development Commands

*Note: This project is not yet initialized. The following commands will be available once the project setup is complete:*

### Backend (Python/FastAPI)

```bash
# Install dependencies
uv install

# Run development server
uv run fastapi dev

# Run tests
uv run pytest

# Code formatting and linting
uv run ruff format
uv run ruff check
```

### Frontend (TypeScript)

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

- All taxonomies must conform to SKOS standards for semantic web compatibility
- URI generation follows consistent patterns using taxonomy-specific prefixes
- Hierarchical relationships use SKOS broader/narrower properties
- Smart discovery features require semantic similarity algorithms
- Frontend visualization must balance detail with usability
- API design should support both individual concept operations and bulk taxonomy management

## Project Status

This is a greenfield project currently containing only requirements documentation. Initial setup tasks include:

1. Python project initialization with uv
2. FastAPI application structure
3. Frontend TypeScript project setup
4. Database/storage layer for SKOS data
5. Testing framework configuration
6. Development tooling (linting, formatting, type checking)
