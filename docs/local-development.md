# Local Development Setup

This guide covers setting up the development environment, especially when working with multiple git worktrees simultaneously.

## Quick Start

```bash
# Start the database
docker compose up -d

# Backend
cd backend
uv sync --all-extras
uv run alembic upgrade head
uv run seed-db  # Optional: populate with sample data
uv run uvicorn taxonomy_builder.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:3000.

## Working with Multiple Worktrees

When working on multiple features in parallel, each worktree needs its own database and server ports to avoid conflicts.

### Database Setup per Worktree

Each worktree should use its own database. Create a unique database for each branch:

```bash
# Connect to postgres and create a new database
docker exec -it taxonomy-builder-postgres-1 psql -U taxonomy -d postgres

# In psql:
CREATE DATABASE taxonomy_builder_feature_x;
\q
```

Then set the database URL when running the backend:

```bash
# Option 1: Full URL
TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_feature_x" \
  uv run alembic upgrade head

TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_feature_x" \
  uv run uvicorn taxonomy_builder.main:app --reload --port 8001

# Option 2: Using components
TAXONOMY_DB_NAME=taxonomy_builder_feature_x \
TAXONOMY_DB_HOST=localhost \
TAXONOMY_DB_USER=taxonomy \
TAXONOMY_DB_PASSWORD=taxonomy \
  uv run uvicorn taxonomy_builder.main:app --reload --port 8001
```

### Port Assignment per Worktree

Use different ports for each worktree:

| Worktree | Backend Port | Frontend Port |
|----------|--------------|---------------|
| main     | 8000         | 3000          |
| feature-1| 8001         | 3001          |
| feature-2| 8002         | 3002          |

Frontend:
```bash
npm run dev -- --port 3001
```

Backend:
```bash
uv run uvicorn taxonomy_builder.main:app --reload --port 8001
```

### Configuring Frontend to Use Different Backend

When using non-default ports, configure the frontend's API proxy:

```bash
# Edit frontend/vite.config.ts temporarily, or use env var:
VITE_API_BASE="http://localhost:8001/api" npm run dev -- --port 3001
```

### Branch Indicator

The UI includes a branch indicator in the header showing the current git branch name with a color unique to that branch. This helps identify which worktree/branch you're looking at when running multiple instances.

## Seed Data

Populate your database with sample data for testing:

```bash
cd backend

# Using default database
uv run seed-db

# Using custom database
TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_feature_x" \
  uv run seed-db
```

The seed data includes:
- **Evidence Synthesis Taxonomy** project with:
  - Study Design Types scheme (hierarchical concepts like RCTs, Systematic Reviews)
  - Risk of Bias Domains scheme
- **Demo Taxonomy** project with:
  - Colors scheme (simple warm/cool color hierarchy)

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `TAXONOMY_DATABASE_URL` | Full database URL | `postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder` |
| `TAXONOMY_DB_HOST` | Database host (if not using URL) | - |
| `TAXONOMY_DB_NAME` | Database name (if not using URL) | - |
| `TAXONOMY_DB_USER` | Database user (if not using URL) | - |
| `TAXONOMY_DB_PASSWORD` | Database password (if not using URL) | - |
| `TAXONOMY_KEYCLOAK_URL` | Keycloak server URL | `http://localhost:8080` |
| `TAXONOMY_KEYCLOAK_REALM` | Keycloak realm | `taxonomy-builder` |
| `TAXONOMY_KEYCLOAK_CLIENT_ID` | Keycloak client ID | `taxonomy-builder-api` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE` | API base URL | `/api` (proxied) |
| `VITE_KEYCLOAK_URL` | Keycloak server URL | `http://localhost:8080` |
| `VITE_KEYCLOAK_REALM` | Keycloak realm | `taxonomy-builder` |
| `VITE_KEYCLOAK_CLIENT_ID` | Keycloak client ID | `taxonomy-builder-app` |

## Convenience Script

For managing multiple worktrees, you might want to create a helper script. Here's an example:

```bash
#!/bin/bash
# save as: scripts/dev.sh

BRANCH=$(git rev-parse --abbrev-ref HEAD)
HASH=$(echo "$BRANCH" | md5sum | cut -c1-4)
PORT_OFFSET=$((16#$HASH % 100))

BACKEND_PORT=$((8000 + PORT_OFFSET))
FRONTEND_PORT=$((3000 + PORT_OFFSET))
DB_NAME="taxonomy_builder_${BRANCH//[^a-zA-Z0-9]/_}"

echo "Branch: $BRANCH"
echo "Database: $DB_NAME"
echo "Backend: http://localhost:$BACKEND_PORT"
echo "Frontend: http://localhost:$FRONTEND_PORT"

# Create database if needed
docker exec taxonomy-builder-postgres-1 psql -U taxonomy -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || true

# Run migrations
TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/$DB_NAME" \
  uv run alembic upgrade head

# Seed data
TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/$DB_NAME" \
  uv run seed-db
```

## Tips

1. **Use tmux or a terminal multiplexer** to manage multiple terminal sessions per worktree.

2. **Browser profiles** - Use different browser profiles or incognito windows for each worktree to avoid session/cookie conflicts.

3. **Git worktree commands**:
   ```bash
   # Create a worktree for a feature branch
   git worktree add ../taxonomy-feature-x feature-x

   # List worktrees
   git worktree list

   # Remove a worktree
   git worktree remove ../taxonomy-feature-x
   ```

4. **Database cleanup** - Periodically clean up databases from old branches:
   ```sql
   -- List all taxonomy databases
   SELECT datname FROM pg_database WHERE datname LIKE 'taxonomy_builder%';

   -- Drop unused database
   DROP DATABASE taxonomy_builder_old_feature;
   ```
