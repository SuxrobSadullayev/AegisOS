#!/bin/sh
# Aegis Module Scaffolding Tool
# Generates a new Tier 2 domain module complying with core/contracts/module.md

set -eu

if [ $# -lt 2 ]; then
  echo "Usage: $0 <category> <name>" >&2
  echo "Example: $0 engineering security" >&2
  exit 1
fi

cat=$1
name=$2
target_dir="modules/domains/$cat/$name"

mkdir -p "$target_dir"

cat << EOF > "$target_dir/standards.md"
# $name Standards
<!-- Module ID: modules.domains.$cat.$name | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines $name standards and best practices.

## Standards

- Standard 1

## Anti-Patterns

- Anti-Pattern 1

## Verification Checklist

- [ ] Check 1

## Examples

\`\`\`
Example
\`\`\`

## Evaluation
### Success Criteria
### Failure Modes
### Metrics & Acceptance Criteria
EOF

echo "✅ Created new module at $target_dir/standards.md"
