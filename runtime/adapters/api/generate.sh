#!/bin/sh
# Aegis API Surface Adapter (OpenAI, Anthropic, Gemini, OpenRouter, Azure OpenAI)

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
api_target="${1:-openai}"
shift 1 || true

# Generate raw context prompt text
raw_context="$("$BASE_DIR/runtime/generators/generator.sh" "$@")"
json_context="$(python3 -c 'import sys, json; print(json.dumps(sys.stdin.read()))' << EOF
$raw_context
EOF
)"

case "$api_target" in
  anthropic)
    cat << EOF
{
  "model": "claude-3-5-sonnet-20241022",
  "system": $json_context,
  "messages": []
}
EOF
    ;;
  openai|azure|openrouter)
    cat << EOF
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": $json_context
    }
  ]
}
EOF
    ;;
  gemini)
    cat << EOF
{
  "systemInstruction": {
    "parts": [
      {
        "text": $json_context
      }
    ]
  }
}
EOF
    ;;
  *)
    cat << EOF
{
  "system_prompt": $json_context
}
EOF
    ;;
esac
