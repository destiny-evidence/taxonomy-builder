#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Source local config if it exists
if [ -f "$SCRIPT_DIR/config.local" ]; then
    source "$SCRIPT_DIR/config.local"
fi

cd "$REPO_ROOT"

# If OP_SECRET_REF is set, use 1Password for HTTPS mode
if [ -n "$OP_SECRET_REF" ]; then
    # Check if 1Password CLI is installed
    if ! command -v op &> /dev/null; then
        echo "Error: 1Password CLI (op) is not installed."
        echo "Install it from: https://developer.1password.com/docs/cli/get-started/"
        echo ""
        echo "Or remove OP_SECRET_REF from dev/config.local to use localhost mode."
        exit 1
    fi

    # Check if we can access the required secret
    if ! op read "$OP_SECRET_REF" &> /dev/null; then
        echo "Error: Cannot access 1Password secret."
        echo "Make sure you're signed in to 1Password CLI (run 'op signin')"
        echo "and have access to: $OP_SECRET_REF"
        echo ""
        echo "Or remove OP_SECRET_REF from dev/config.local to use localhost mode."
        exit 1
    fi

    echo "1Password access verified. Starting with HTTPS (fef.dev mode)..."
    DNSIMPLE_KEY="$OP_SECRET_REF" op run -- docker compose -f docker-compose.yml -f docker-compose.fef.yml up -d "$@"
else
    echo "Starting in localhost mode (no HTTPS)..."
    docker compose up -d "$@"
fi
