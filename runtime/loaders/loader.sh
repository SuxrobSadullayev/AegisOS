#!/bin/sh
# Aegis Runtime Context Loader
# Reads static files from core/, modules/, and knowledge/ layers.

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

load_file() {
  file_path="$1"
  if [ -f "$BASE_DIR/$file_path" ]; then
    cat "$BASE_DIR/$file_path"
    echo ""
    echo ""
  else
    echo "Warning: File $file_path not found" >&2
  fi
}

load_core() {
  load_file "core/kernel/constitution.md"
  load_file "core/engines/truth-engine.md"
  load_file "core/engines/reasoning-engine.md"
  load_file "core/engines/quality-engine.md"
  load_file "core/workflow/workflow.md"
  load_file "core/contracts/module.md"
}

case "${1:-all}" in
  core)
    load_core
    ;;
  file)
    shift
    for f in "$@"; do
      load_file "$f"
    done
    ;;
  all)
    load_core
    ;;
  *)
    echo "Usage: $0 [core|file <path>|all]" >&2
    exit 1
    ;;
esac
