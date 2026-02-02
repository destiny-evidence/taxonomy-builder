#!/bin/bash
set -e

# Check if 1Password CLI is installed
if ! command -v op &> /dev/null; then
    echo "Error: 1Password CLI (op) is not installed."
    echo "Install it from: https://developer.1password.com/docs/cli/get-started/"
    exit 1
fi

# Check if we can access the required secret
OP_SECRET_REF="op://Evidence Data Platforms/DNSimple API Token/password"
if ! op read "$OP_SECRET_REF" &> /dev/null; then
    echo "Error: Cannot access 1Password secret."
    echo "Make sure you're signed in to 1Password CLI (run 'op signin')"
    echo "and have access to: $OP_SECRET_REF"
    exit 1
fi

echo "1Password access verified. Starting docker-compose..."

# Run docker-compose with DNSIMPLE_KEY injected from 1Password
cd "$(dirname "$0")/.."
DNSIMPLE_KEY="$OP_SECRET_REF" op run -- docker compose -f docker-compose.yml -f docker-compose.fef.yml up -d "$@"
