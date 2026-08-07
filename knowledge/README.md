# Layer 1: Knowledge — Descriptive Experience Base

## Purpose

The `knowledge/` directory contains a **descriptive knowledge base** of real-world
engineering wisdom, patterns, anti-patterns, case studies, and lessons learned.
Unlike `modules/` (which are prescriptive standards), `knowledge/` captures
experience and evidence ("what was learned").

## Structure

| Directory | Purpose |
|:----------|:--------|
| `practices/` | Proven engineering practices across domains |
| `patterns/` | Reusable architectural and implementation patterns |
| `anti-patterns/` | Common pitfalls with root cause analysis |
| `case-studies/` | Real-world post-mortems and engineering retrospectives |

## Dependency Rules

- **Allowed**: Completely independent.
- **Forbidden**: No dependencies on `runtime/`, `tools/`, or `examples/`.
