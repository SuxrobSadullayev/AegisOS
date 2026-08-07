#!/bin/sh
# Aegis IDE Surface Adapter (VS Code, Cursor, Windsurf, JetBrains)

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
ide_target="${1:-cursor}"
shift 1 || true

echo "<!-- Aegis IDE Surface Adapter Target: $ide_target -->"
echo ""

case "$ide_target" in
  cursor)
    echo "<!-- Format: .cursorrules -->"
    ;;
  windsurf)
    echo "<!-- Format: .windsurfrules -->"
    ;;
  vscode)
    echo "<!-- Format: .vscode/settings.json context prompt -->"
    ;;
  jetbrains)
    echo "<!-- Format: JetBrains AI Assistant rules -->"
    ;;
  *)
    echo "<!-- Format: Generic IDE rules -->"
    ;;
esac

"$BASE_DIR/runtime/generators/generator.sh" "$@"
