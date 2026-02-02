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
uv run seed-db  # Optional: populate with sample data
uv run uvicorn taxonomy_builder.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

The app will be available at <http://localhost:3000>.

## Internal Setup (fef.dev)

Internal contributors with 1Password access can use HTTPS with real certificates:

```bash
# Start with fef.dev domain and HTTPS
./dev/start.sh

# Or manually:
docker compose -f docker-compose.yml -f docker-compose.fef.yml up -d
```

This requires:

- 1Password CLI with access to the DNSimple API token

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
3. Run migrations and seed data
4. Create VS Code tasks.json and launch.json
5. (Internal only) Configure Caddy routing if `DEV_DOMAIN` is set

### External Contributors

Each worktree runs on different ports. Access via `localhost:PORT`:

```bash
./dev/setup-worktree.sh feature-x
# Output shows: Visit: http://localhost:3042 (port varies by branch)
```

### Internal Contributors

With `DEV_DOMAIN` set, each worktree gets its own subdomain:

```bash
DEV_DOMAIN=fef.dev ./dev/setup-worktree.sh feature-x
# Output shows: Visit: https://feature-x.fef.dev
```

### Branch Indicator

The UI includes a branch indicator in the header showing the current git branch name with a color unique to that branch. This helps identify which worktree/branch you're looking at when running multiple instances.

## DNS Setup (Internal)

Configure dnsmasq to resolve `*.fef.dev` to `127.0.0.1`:

**macOS (with Homebrew):**

```bash
brew install dnsmasq

# Configure wildcard resolution
echo "address=/fef.dev/127.0.0.1" >> $(brew --prefix)/etc/dnsmasq.conf

# Start dnsmasq
sudo brew services start dnsmasq

# Tell macOS to use dnsmasq for .fef.dev
sudo mkdir -p /etc/resolver
echo "nameserver 127.0.0.1" | sudo tee /etc/resolver/fef.dev
```

**Linux (systemd-resolved):**

```bash
# Add to /etc/systemd/resolved.conf.d/fef.conf:
[Resolve]
DNS=127.0.0.1
Domains=~fef.dev

# Or use dnsmasq directly
sudo apt install dnsmasq
echo "address=/fef.dev/127.0.0.1" | sudo tee /etc/dnsmasq.d/fef.conf
sudo systemctl restart dnsmasq
```

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

### Scripts

| Variable | Description | Default |
|----------|-------------|---------|
| `DEV_DOMAIN` | Domain for Caddy routing | (none - uses localhost ports) |

## Tips

1. **Use VS Code tasks** - The setup script creates `.vscode/tasks.json` with pre-configured tasks. Press `Cmd+Shift+B` to start both servers.

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
