#!/bin/bash
set -e

# Setup a new worktree for parallel development
#
# Usage: ./dev/setup-worktree.sh <branch-name> [base-branch]
#
# This script:
#   1. Creates a git worktree in ../taxonomy-<branch-name>
#   2. Creates a dedicated database
#   3. Runs migrations and seeds data
#   4. Configures Caddy routing for <branch-name>.localdev
#
# Prerequisites:
#   - docker compose up -d (database and proxy running)
#   - dnsmasq configured to resolve *.localdev to 127.0.0.1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -z "$1" ]; then
    echo "Usage: $0 <branch-name> [base-branch]"
    echo ""
    echo "Examples:"
    echo "  $0 feature-x              # Create worktree for existing branch"
    echo "  $0 feature-y main         # Create new branch from main"
    exit 1
fi

BRANCH="$1"
BASE_BRANCH="${2:-}"

# Sanitize branch name for paths/domains (hyphens) and database (underscores)
SAFE_NAME=$(echo "${BRANCH//[^a-zA-Z0-9-]/-}" | tr '[:upper:]' '[:lower:]')
WORKTREE_PATH="$(dirname "$REPO_ROOT")/taxonomy-${SAFE_NAME}"
DB_NAME="taxonomy_builder_${SAFE_NAME//-/_}"

# Compute port offset from branch name hash (0-99)
HASH=$(echo "$BRANCH" | md5sum | cut -c1-4)
PORT_OFFSET=$((16#$HASH % 100))
BACKEND_PORT=$((8000 + PORT_OFFSET))
FRONTEND_PORT=$((3000 + PORT_OFFSET))

echo "Setting up worktree for branch: $BRANCH"
echo "  Worktree path: $WORKTREE_PATH"
echo "  Database: $DB_NAME"
echo "  Backend port: $BACKEND_PORT"
echo "  Frontend port: $FRONTEND_PORT"
echo "  URL: http://${SAFE_NAME}.localdev"
echo ""

# 1. Create worktree
if [ -d "$WORKTREE_PATH" ]; then
    echo "Worktree already exists at $WORKTREE_PATH"
else
    echo "Creating worktree..."
    if [ -n "$BASE_BRANCH" ]; then
        # Create new branch from base
        git -C "$REPO_ROOT" worktree add -b "$BRANCH" "$WORKTREE_PATH" "$BASE_BRANCH"
    else
        # Use existing branch
        git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" "$BRANCH"
    fi
fi

# 2. Create database
echo "Creating database..."
docker exec taxonomy-builder-db-1 psql -U taxonomy -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "  Database already exists"

# 3. Run migrations
echo "Running migrations..."
cd "$WORKTREE_PATH/backend"
TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/$DB_NAME" \
    uv run alembic upgrade head

# 4. Seed data
echo "Seeding database..."
TAXONOMY_DATABASE_URL="postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/$DB_NAME" \
    uv run seed-db

# 5. Create Caddy config
CADDY_CONFIG="$REPO_ROOT/dev/caddy/sites/${SAFE_NAME}.caddy"
echo "Creating Caddy config at $CADDY_CONFIG..."
cat > "$CADDY_CONFIG" << EOF
http://${SAFE_NAME}.localdev {
	reverse_proxy /api/* host.docker.internal:${BACKEND_PORT}
	reverse_proxy host.docker.internal:${FRONTEND_PORT}
}
EOF

# 6. Reload Caddy
echo "Reloading Caddy..."
docker compose -f "$REPO_ROOT/docker-compose.yml" exec proxy caddy reload -c /etc/caddy/Caddyfile 2>/dev/null || echo "  Caddy not running (start with: docker compose up -d)"

echo ""
echo "Worktree ready!"
echo ""
echo "To start development:"
echo "  cd $WORKTREE_PATH"
echo ""
echo "  # Terminal 1 - Backend"
echo "  cd backend"
echo "  TAXONOMY_DATABASE_URL=\"postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/$DB_NAME\" \\"
echo "    uv run uvicorn taxonomy_builder.main:app --reload --port $BACKEND_PORT"
echo ""
echo "  # Terminal 2 - Frontend"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev -- --port $FRONTEND_PORT"
echo ""
echo "Then visit: http://${SAFE_NAME}.localdev"
