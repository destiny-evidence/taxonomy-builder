# Local Development Setup

This guide covers setting up the development environment, especially when working with multiple git worktrees simultaneously.

## Quick Start (External Contributors)

```bash
# Start the database and Keycloak
docker compose up -d

# Backend
cd backend
uv sync --all-extras
uv run alembic upgrade head
uv run seed-db  # Optional: populate with sample data + published files
uv run uvicorn taxonomy_builder.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev

# Feedback UI (in another terminal, optional)
cd feedback-ui
npm install
npm run dev
```

The app will be available at <http://localhost:3000>.
The feedback UI will be at <http://localhost:3001/feedback/>.

## Internal Setup (fef.dev)

Internal contributors with 1Password access can use HTTPS with real certificates.

**One-time setup:**

```bash
cp dev/config.local.example dev/config.local
# Edit dev/config.local and uncomment OP_SECRET_REF and DEV_DOMAIN
```

**Starting services:**

```bash
./dev/start.sh
```

This requires:

- 1Password CLI (`op`) with access to the DNSimple API token

This will create a user with username `user` and password `user` for development.

With Caddy running, the feedback UI is accessible at `https://<branch>.fef.dev/feedback/` alongside the main app. Caddy routes `/feedback/*` to the feedback UI dev server, `/api/*` to the backend, and `/published/*` to the local blob storage.

## Working with Multiple Worktrees

When working on multiple features in parallel, use the provided scripts to set up isolated environments for each branch.

### Setup Scripts

```bash
# Set up a new worktree (creates worktree, database, VS Code config)
./dev/setup-worktree.sh feature-x

# Or create a new branch from main
./dev/setup-worktree.sh feature-y main

# Tear down when done
./dev/teardown-worktree.sh feature-x
./dev/teardown-worktree.sh feature-y --keep-db  # Keep the database
```

The setup script will:

1. Create a git worktree at `../taxonomy-<branch>`
2. Create a dedicated database
3. Run migrations and seed data (including published reader files)
4. Create VS Code tasks.json and launch.json
5. (Internal only) Configure Caddy routing if `DEV_DOMAIN` is set

### External Contributors

Each worktree runs on different ports. Access via `localhost:PORT`:

```bash
./dev/setup-worktree.sh feature-x
# Output shows: Visit: http://localhost:3042 (port varies by branch)
#               Feedback UI: http://localhost:4042/feedback/
```

### Internal Contributors

With `DEV_DOMAIN` configured in `dev/config.local`, each worktree gets its own subdomain:

```bash
./dev/setup-worktree.sh feature-x
# Output shows: Visit: https://feature-x.fef.dev
#               Feedback UI: https://feature-x.fef.dev/feedback/
```

### Branch Indicator

The UI includes a branch indicator in the header showing the current git branch name with a color unique to that branch. This helps identify which worktree/branch you're looking at when running multiple instances.

## DNS Setup (Internal)

The `fef.dev` domain already resolves to `127.0.0.1` globally (no local DNS setup required).

Verify it works:

```bash
ping test.fef.dev  # Should resolve to 127.0.0.1
```

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

The seed command also publishes each project as v1.0 and writes reader JSON files to the blob storage directory (`.blob-storage/` by default). Set `TAXONOMY_BLOB_FILESYSTEM_ROOT` to control where files are written. The worktree setup script points this to the shared `<repo-root>/.blob-storage/` so Caddy can serve them at `/published/*`.

## Environment Variables

### Backend

| Variable                         | Description                            | Default                                                                  |
| -------------------------------- | -------------------------------------- | ------------------------------------------------------------------------ |
| `TAXONOMY_DATABASE_URL`          | Full database URL                      | `postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder` |
| `TAXONOMY_DB_HOST`               | Database host (if not using URL)       | -                                                                        |
| `TAXONOMY_DB_NAME`               | Database name (if not using URL)       | -                                                                        |
| `TAXONOMY_DB_USER`               | Database user (if not using URL)       | -                                                                        |
| `TAXONOMY_DB_PASSWORD`           | Database password (if not using URL)   | -                                                                        |
| `TAXONOMY_KEYCLOAK_URL`          | Keycloak server URL                    | `http://localhost:8080`                                                  |
| `TAXONOMY_KEYCLOAK_REALM`        | Keycloak realm                         | `taxonomy-builder`                                                       |
| `TAXONOMY_KEYCLOAK_CLIENT_ID`    | Keycloak client ID                     | `taxonomy-builder-api`                                                   |
| `TAXONOMY_BLOB_FILESYSTEM_ROOT`  | Directory for published reader files   | `./.blob-storage`                                                        |

### Frontend

| Variable                  | Description         | Default                 |
| ------------------------- | ------------------- | ----------------------- |
| `VITE_API_BASE`           | API base URL        | `/api` (proxied)        |
| `VITE_KEYCLOAK_URL`       | Keycloak server URL | `http://localhost:8080` |
| `VITE_KEYCLOAK_REALM`     | Keycloak realm      | `taxonomy-builder`      |
| `VITE_KEYCLOAK_CLIENT_ID` | Keycloak client ID  | `taxonomy-builder-app`  |

### Feedback UI

| Variable                  | Description                | Default                 |
| ------------------------- | -------------------------- | ----------------------- |
| `VITE_API_BASE`           | API base URL               | `/api` (proxied)        |
| `VITE_KEYCLOAK_URL`       | Keycloak server URL        | `http://localhost:8080` |
| `VITE_KEYCLOAK_REALM`     | Keycloak realm             | `taxonomy-builder`      |
| `VITE_KEYCLOAK_CLIENT_ID` | Keycloak client ID         | `taxonomy-builder-ui`   |
| `VITE_BASE`               | Base path                  | `/feedback/`            |
| `VITE_API_TARGET`         | Backend proxy target (dev) | `http://localhost:8000` |

### Scripts (dev/config.local)

| Variable        | Description                                | Default                       |
| --------------- | ------------------------------------------ | ----------------------------- |
| `OP_SECRET_REF` | 1Password reference for DNSimple API token | (none)                        |
| `DEV_DOMAIN`    | Domain for Caddy routing (e.g., `fef.dev`) | (none - uses localhost ports) |

## Tips

1. **Use VS Code tasks** - The setup script creates `.vscode/tasks.json` with pre-configured tasks. Press `Cmd+Shift+B` to start all servers (backend, frontend, feedback UI).

2. **Database cleanup** - List and clean up databases from old branches:

   ```bash
   # List all taxonomy databases
   docker exec taxonomy-builder-db-1 psql -U taxonomy -d postgres \
     -c "SELECT datname FROM pg_database WHERE datname LIKE 'taxonomy_builder%';"

   # Drop unused database
   docker exec taxonomy-builder-db-1 psql -U taxonomy -d postgres \
     -c "DROP DATABASE taxonomy_builder_old_feature;"
   ```

3. **List worktrees**:

   ```bash
   git worktree list
   ```
