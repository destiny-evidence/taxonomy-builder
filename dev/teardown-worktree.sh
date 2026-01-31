#!/bin/bash
set -e

# Teardown a worktree and clean up associated resources
#
# Usage: ./dev/teardown-worktree.sh <branch-name> [--keep-db]
#
# This script:
#   1. Removes the git worktree
#   2. Drops the database (unless --keep-db)
#   3. Removes the Caddy config
#   4. Reloads Caddy

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

KEEP_DB=false
BRANCH=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-db)
            KEEP_DB=true
            shift
            ;;
        *)
            BRANCH="$1"
            shift
            ;;
    esac
done

if [ -z "$BRANCH" ]; then
    echo "Usage: $0 <branch-name> [--keep-db]"
    echo ""
    echo "Options:"
    echo "  --keep-db    Don't drop the database"
    echo ""
    echo "Current worktrees:"
    git -C "$REPO_ROOT" worktree list
    exit 1
fi

# Sanitize branch name (lowercase for PostgreSQL)
SAFE_NAME=$(echo "${BRANCH//[^a-zA-Z0-9-]/_}" | tr '[:upper:]' '[:lower:]')
WORKTREE_PATH="$(dirname "$REPO_ROOT")/taxonomy-${SAFE_NAME}"
DB_NAME="taxonomy_builder_${SAFE_NAME//-/_}"

echo "Tearing down worktree for branch: $BRANCH"
echo ""

# 1. Remove Caddy config first (so reload doesn't fail)
CADDY_CONFIG="$REPO_ROOT/dev/caddy/sites/${SAFE_NAME}.caddy"
if [ -f "$CADDY_CONFIG" ]; then
    echo "Removing Caddy config..."
    rm "$CADDY_CONFIG"

    # Reload Caddy
    echo "Reloading Caddy..."
    docker compose -f "$REPO_ROOT/docker-compose.yml" exec proxy caddy reload -c /etc/caddy/Caddyfile 2>/dev/null || true
else
    echo "No Caddy config found at $CADDY_CONFIG"
fi

# 2. Remove worktree
if [ -d "$WORKTREE_PATH" ]; then
    echo "Removing worktree at $WORKTREE_PATH..."
    git -C "$REPO_ROOT" worktree remove "$WORKTREE_PATH" --force
else
    echo "No worktree found at $WORKTREE_PATH"
fi

# 3. Drop database
if [ "$KEEP_DB" = true ]; then
    echo "Keeping database $DB_NAME (--keep-db specified)"
else
    echo "Dropping database $DB_NAME..."
    docker exec taxonomy-builder-db-1 psql -U taxonomy -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || echo "  Could not drop database (is docker running?)"
fi

echo ""
echo "Teardown complete."
echo ""
echo "Note: The branch '$BRANCH' still exists. To delete it:"
echo "  git branch -d $BRANCH"
