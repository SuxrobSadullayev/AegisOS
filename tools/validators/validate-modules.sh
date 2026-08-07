#!/bin/sh
# Aegis Module Validator
# Validates that all domain modules conform to core/contracts/module.md

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
errors=0

echo "=== Aegis Module Contract Validator ==="

find "$BASE_DIR/modules" -name "*.md" -not -name "README.md" | while IFS= read -r f; do
  echo "Checking $f..."
  if ! grep -q "^# " "$f"; then
    echo "  FAIL: Missing main title in $f" >&2
    errors=$((errors + 1))
  fi
  if ! grep -q "## Purpose" "$f"; then
    echo "  FAIL: Missing Purpose section in $f" >&2
    errors=$((errors + 1))
  fi
done

echo "✅ All module files inspected."
