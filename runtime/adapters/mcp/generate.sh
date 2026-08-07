#!/bin/sh
# Aegis MCP (Model Context Protocol) Surface Adapter

set -eu

BASE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"

raw_context="$("$BASE_DIR/runtime/generators/generator.sh" "$@")"
json_context="$(python3 -c 'import sys, json; print(json.dumps(sys.stdin.read()))' << EOF
$raw_context
EOF
)"

cat << EOF
{
  "jsonrpc": "2.0",
  "method": "prompts/get",
  "result": {
    "description": "Aegis AI Operating System Kernel Context Payload",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": $json_context
        }
      }
    ]
  }
}
EOF
