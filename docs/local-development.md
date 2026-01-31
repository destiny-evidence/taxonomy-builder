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

When working on multiple features in parallel, use the provided scripts to set up isolated environments for each branch.

### Quick Setup with Scripts

```bash
# Set up a new worktree (creates worktree, database, Caddy config)
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
4. Configure Caddy routing (if using DNS-based routing)
5. Print the commands to start the backend and frontend

### Branch Indicator

The UI includes a branch indicator in the header showing the current git branch name with a color unique to that branch. This helps identify which worktree/branch you're looking at when running multiple instances.

### DNS-based Routing (Recommended)

For the best experience, set up local DNS so each worktree gets its own URL:
- `http://main.localdev` → main worktree
- `http://feature-x.localdev` → feature-x worktree

#### One-time DNS Setup

Configure dnsmasq to resolve `*.localdev` to `127.0.0.1`:

**macOS (with Homebrew):**
```bash
brew install dnsmasq

# Configure wildcard resolution
echo "address=/localdev/127.0.0.1" >> $(brew --prefix)/etc/dnsmasq.conf

# Start dnsmasq
sudo brew services start dnsmasq

# Tell macOS to use dnsmasq for .localdev
sudo mkdir -p /etc/resolver
echo "nameserver 127.0.0.1" | sudo tee /etc/resolver/localdev
```

**Linux (systemd-resolved):**
```bash
# Add to /etc/systemd/resolved.conf.d/localdev.conf:
[Resolve]
DNS=127.0.0.1
Domains=~localdev

# Or use dnsmasq directly
sudo apt install dnsmasq
echo "address=/localdev/127.0.0.1" | sudo tee /etc/dnsmasq.d/localdev.conf
sudo systemctl restart dnsmasq
```

Verify it works:
```bash
ping test.localdev  # Should resolve to 127.0.0.1
```

The setup script automatically creates Caddy configs in `dev/caddy/sites/` (gitignored). To manually reload Caddy after editing configs:
```bash
docker compose exec proxy caddy reload -c /etc/caddy/Caddyfile
```

**Benefits:**
- Each worktree gets its own URL (easier to identify in browser tabs)
- No port numbers to remember
- Cookies are isolated per subdomain (no session conflicts)
- Works offline (no external DNS dependency)

### Manual Setup (Alternative)

If you prefer manual control, each worktree needs:
- Its own database
- Different ports for backend (8000+) and frontend (3000+)

```bash
# Create database
docker exec taxonomy-builder-db-1 psql -U taxonomy -d postgres \
  -c "CREATE DATABASE taxonomy_builder_feature_x;"

# Run backend on custom port
TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_feature_x" \
  uv run uvicorn taxonomy_builder.main:app --reload --port 8001

# Run frontend on custom port
npm run dev -- --port 3001
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

## Tips

1. **Use tmux or a terminal multiplexer** to manage multiple terminal sessions per worktree.

2. **Browser profiles** - With DNS-based routing, cookies are isolated per subdomain so this is less necessary. But different browser profiles can still help keep things organized.

3. **Database cleanup** - List and clean up databases from old branches:
   ```bash
   # List all taxonomy databases
   docker exec taxonomy-builder-db-1 psql -U taxonomy -d postgres \
     -c "SELECT datname FROM pg_database WHERE datname LIKE 'taxonomy_builder%';"

   # Drop unused database
   docker exec taxonomy-builder-db-1 psql -U taxonomy -d postgres \
     -c "DROP DATABASE taxonomy_builder_old_feature;"
   ```

4. **List worktrees**:
   ```bash
   git worktree list
   ```
