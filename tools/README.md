# Layer 3: Tools — Framework Development Tools

## Purpose

The `tools/` directory contains **development and verification tooling** for Aegis
contributors and maintainers.

## Structure

| Directory | Purpose |
|:----------|:--------|
| `validators/` | Module structure and contract compliance validators |
| `linters/` | Markdown formatting and convention linters |
| `scaffolding/` | New module template generators |

## Dependency Rules

- **Allowed**: `tools/` → `core/contracts/`
- **Forbidden**: `core/` or `modules/` MUST NOT depend on `tools/`.
