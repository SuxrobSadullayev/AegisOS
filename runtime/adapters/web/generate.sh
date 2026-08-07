#!/bin/sh
# Aegis Web Surface Adapter (ChatGPT Web, Gemini Web, Claude Web)

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
web_target="${1:-chatgpt}"
shift 1 || true

echo "================================================================================"
echo "AEGIS AI OPERATING SYSTEM CONTEXT PAYLOAD (TARGET: $web_target)"
echo "Paste the following content into your custom instructions or initial prompt block:"
echo "================================================================================"
echo ""

"$BASE_DIR/runtime/generators/generator.sh" "$@"
