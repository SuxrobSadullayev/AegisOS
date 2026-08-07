#!/bin/sh
# Aegis Universal Target Adapter Router
# Routes prompt payload generation across surfaces: CLI, IDE, Web, API, MCP.

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

surface="${1:-cli}"
target="${2:-generic}"

if [ $# -ge 2 ]; then
  shift 2
elif [ $# -ge 1 ]; then
  shift 1
fi

case "$surface" in
  cli)
    case "$target" in
      claude) "$BASE_DIR/runtime/adapters/claude/generate.sh" "$@" ;;
      gemini) "$BASE_DIR/runtime/adapters/gemini/generate.sh" "$@" ;;
      codex)  "$BASE_DIR/runtime/adapters/codex/generate.sh" "$@" ;;
      kiro)   "$BASE_DIR/runtime/adapters/kiro/generate.sh" "$@" ;;
      qwen)   "$BASE_DIR/runtime/adapters/qwen/generate.sh" "$@" ;;
      *)      "$BASE_DIR/runtime/generators/generator.sh" "$@" ;;
    esac
    ;;
  ide)
    "$BASE_DIR/runtime/adapters/ide/generate.sh" "$target" "$@"
    ;;
  api)
    "$BASE_DIR/runtime/adapters/api/generate.sh" "$target" "$@"
    ;;
  mcp)
    "$BASE_DIR/runtime/adapters/mcp/generate.sh" "$@"
    ;;
  web)
    "$BASE_DIR/runtime/adapters/web/generate.sh" "$target" "$@"
    ;;
  *)
    echo "Usage: $0 <surface: cli|ide|api|mcp|web> <target: claude|gemini|vscode|cursor|openai|anthropic|mcp> [modules...]" >&2
    exit 1
    ;;
esac
