#!/bin/bash
set -e

# Setup a new worktree for parallel development
#
# Usage: ./dev/setup-worktree.sh <branch-name> [base-branch]
#
# Environment:
#   DEV_DOMAIN - Domain for Caddy routing (e.g., fef.dev). If not set, uses localhost ports.
#
# This script:
#   1. Creates a git worktree in ../taxonomy-<branch-name>
#   2. Creates a dedicated database
#   3. Runs migrations and seeds data
#   4. Configures Caddy routing (if DEV_DOMAIN is set)
#   5. Creates VS Code tasks/launch configs
#
# Prerequisites:
#   - docker compose up -d (database running)
#   - If using DEV_DOMAIN: dnsmasq configured to resolve *.$DEV_DOMAIN to 127.0.0.1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# DEV_DOMAIN can be set to enable subdomain routing (e.g., fef.dev)
# If not set, worktrees are accessed via localhost:PORT
DEV_DOMAIN="${DEV_DOMAIN:-}"

if [ -z "$1" ]; then
    echo "Usage: $0 <branch-name> [base-branch]"
    echo ""
    echo "Examples:"
    echo "  $0 feature-x              # Create worktree for existing branch"
    echo "  $0 feature-y main         # Create new branch from main"
    echo ""
    echo "Environment:"
    echo "  DEV_DOMAIN=fef.dev $0 feature-x   # Use subdomain routing"
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

# Set Keycloak URL based on DEV_DOMAIN
if [ -n "$DEV_DOMAIN" ]; then
    KEYCLOAK_URL="https://keycloak.${DEV_DOMAIN}"
else
    KEYCLOAK_URL="http://localhost:8080"
fi

echo "Setting up worktree for branch: $BRANCH"
echo "  Worktree path: $WORKTREE_PATH"
echo "  Database: $DB_NAME"
echo "  Backend port: $BACKEND_PORT"
echo "  Frontend port: $FRONTEND_PORT"
echo "  Keycloak: $KEYCLOAK_URL"
if [ -n "$DEV_DOMAIN" ]; then
    echo "  URL: https://${SAFE_NAME}.${DEV_DOMAIN}"
else
    echo "  URL: http://localhost:${FRONTEND_PORT}"
fi
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

# 5. Create Caddy config (only if DEV_DOMAIN is set)
if [ -n "$DEV_DOMAIN" ]; then
    CADDY_CONFIG="$REPO_ROOT/dev/caddy/sites/${SAFE_NAME}.caddy"
    echo "Creating Caddy config at $CADDY_CONFIG..."
    cat > "$CADDY_CONFIG" << EOF
https://${SAFE_NAME}.${DEV_DOMAIN} {
	reverse_proxy /api/* host.docker.internal:${BACKEND_PORT}
	reverse_proxy host.docker.internal:${FRONTEND_PORT}
}
EOF

    # 6. Reload Caddy
    echo "Reloading Caddy..."
    docker compose -f "$REPO_ROOT/docker-compose.yml" -f "$REPO_ROOT/docker-compose.fef.yml" exec proxy caddy reload -c /etc/caddy/Caddyfile 2>/dev/null || echo "  Caddy not running"
fi

# 7. Create VS Code configuration
VSCODE_DIR="$WORKTREE_PATH/.vscode"
echo "Creating VS Code configuration..."
mkdir -p "$VSCODE_DIR"

cat > "$VSCODE_DIR/tasks.json" << EOF
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Backend",
      "type": "shell",
      "command": "uv run uvicorn taxonomy_builder.main:app --reload --port ${BACKEND_PORT}",
      "options": {
        "cwd": "\${workspaceFolder}/backend",
        "env": {
          "TAXONOMY_DATABASE_URL": "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/${DB_NAME}",
          "TAXONOMY_KEYCLOAK_URL": "${KEYCLOAK_URL}"
        }
      },
      "isBackground": true,
      "problemMatcher": [],
      "presentation": {
        "group": "dev",
        "reveal": "always"
      }
    },
    {
      "label": "Frontend",
      "type": "shell",
      "command": "npm run dev -- --port ${FRONTEND_PORT}",
      "options": {
        "cwd": "\${workspaceFolder}/frontend",
        "env": {
          "VITE_KEYCLOAK_URL": "${KEYCLOAK_URL}",
          "VITE_API_TARGET": "http://localhost:${BACKEND_PORT}"
        }
      },
      "isBackground": true,
      "problemMatcher": [],
      "presentation": {
        "group": "dev",
        "reveal": "always"
      }
    },
    {
      "label": "Dev Servers",
      "dependsOn": ["Backend", "Frontend"],
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "problemMatcher": []
    }
  ]
}
EOF

cat > "$VSCODE_DIR/launch.json" << EOF
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend (Debug)",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["taxonomy_builder.main:app", "--reload", "--port", "${BACKEND_PORT}"],
      "cwd": "\${workspaceFolder}/backend",
      "env": {
        "TAXONOMY_DATABASE_URL": "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/${DB_NAME}",
        "TAXONOMY_KEYCLOAK_URL": "${KEYCLOAK_URL}"
      },
      "console": "integratedTerminal"
    }
  ]
}
EOF

echo ""
echo "Worktree ready!"
echo ""
echo "Open in VS Code:"
echo "  code $WORKTREE_PATH"
echo ""
echo "Then run 'Tasks: Run Build Task' (Cmd+Shift+B) to start both servers."
echo ""
if [ -n "$DEV_DOMAIN" ]; then
    echo "Visit: https://${SAFE_NAME}.${DEV_DOMAIN}"
else
    echo "Visit: http://localhost:${FRONTEND_PORT}"
    echo ""
    echo "Note: For subdomain routing, set DEV_DOMAIN (internal only):"
    echo "  DEV_DOMAIN=fef.dev $0 $BRANCH"
fi
