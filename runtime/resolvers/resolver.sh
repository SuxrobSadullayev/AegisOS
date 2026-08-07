#!/bin/sh
# Aegis Runtime Module Resolver
# Resolves domain modules based on task flags or workspace file inspection.

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

resolve_modules() {
  input_flags="${1:-}"
  resolved=""

  # Keyword / flag matching
  case "$input_flags" in
    *python*) resolved="$resolved modules/domains/languages/python/standards.md" ;;
    *typescript*|*ts*) resolved="$resolved modules/domains/languages/typescript/standards.md" ;;
    *rust*) resolved="$resolved modules/domains/languages/rust/standards.md" ;;
    *c*) resolved="$resolved modules/domains/languages/c/standards.md" ;;
    *cpp*) resolved="$resolved modules/domains/languages/cpp/standards.md" ;;
    *backend*) resolved="$resolved modules/domains/platforms/backend/standards.md" ;;
    *frontend*) resolved="$resolved modules/domains/platforms/frontend/standards.md" ;;
    *security*) resolved="$resolved modules/domains/engineering/security/standards.md" ;;
    *testing*) resolved="$resolved modules/domains/engineering/testing/standards.md" ;;
    *architecture*) resolved="$resolved modules/domains/engineering/architecture/standards.md" ;;
    *) ;;
  esac

  echo "$resolved"
}

if [ "${1:-}" = "--help" ]; then
  echo "Usage: $0 [module-keywords...]" >&2
  exit 0
fi

resolve_modules "$*"
