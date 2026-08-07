#!/bin/sh
# Aegis Runtime Prompt Generator
# Assembles Layer 0 Core and Layer 1 Domain Modules into a canonical prompt payload.

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

generate_prompt() {
  modules="${1:-}"

  # 1. Load Layer 0 Core
  "$BASE_DIR/runtime/loaders/loader.sh" core

  # 2. Resolve and load Layer 1 Domain Modules if provided
  if [ -n "$modules" ]; then
    resolved_paths="$("$BASE_DIR/runtime/resolvers/resolver.sh" "$modules")"
    for path in $resolved_paths; do
      if [ -f "$BASE_DIR/$path" ]; then
        echo "---"
        echo "# Domain Module: $path"
        cat "$BASE_DIR/$path"
        echo ""
      fi
    done
  fi
}

generate_prompt "$*"
