#!/bin/sh
# Aegis Markdown Linter
# Checks for unlabeled opening code blocks across markdown files.

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== Aegis Markdown Linter ==="

# Check for opening code blocks without language specifier
unlabeled="$(grep -rn '^[[:space:]]*```[[:space:]]*$' "$BASE_DIR/modules/domains" "$BASE_DIR/modules/standards" || true)"

if [ -n "$unlabeled" ]; then
  echo "Warning: Found unlabeled opening code blocks in domain modules:"
  echo "$unlabeled"
else
  echo "✅ All code blocks in domain modules specify language tags."
fi
