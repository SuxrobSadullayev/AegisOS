# Layer 2: Runtime — Context Execution Pipeline

## Purpose

The `runtime/` directory contains the **context execution pipeline** of Aegis.
It handles reading knowledge, resolving task-relevant modules, building prompts,
managing token budgets, and transforming outputs into model-specific formats.

## Execution Pipeline

```
loaders/ ──▶ resolvers/ ──▶ generators/ ──▶ adapters/
(Read)       (Select)       (Assemble)      (Transform)
```

| Component | Directory | Responsibility |
|:----------|:----------|:---------------|
| Context Loader | `loaders/` | Read static files from `core/`, `modules/`, `knowledge/` |
| Module Resolver | `resolvers/` | Select relevant modules based on task and project metadata |
| Prompt Generator | `generators/` | Assemble prompt components, enforce token budget limits |
| Adapter Transformer | `adapters/` | Convert canonical output to target agent formats (Claude, Gemini, Cursor, etc.) |

## Dependency Rules

- **Allowed**: `runtime/` → `core/`, `runtime/` → `modules/`, `runtime/` → `knowledge/`
- **Forbidden**: `core/` or `modules/` MUST NOT depend on `runtime/`.
