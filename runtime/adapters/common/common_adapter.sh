#!/bin/sh
# Aegis Common Adapter Logic

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"

generate_canonical_context() {
  modules="${1:-}"
  "$BASE_DIR/runtime/generators/generator.sh" "$modules"
}
