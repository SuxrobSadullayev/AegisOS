# Layer 3: Evaluation — Objective Framework Metrics

## Purpose

The `evaluation/` directory contains tools and test suites for **objectively measuring**
the effectiveness of the Aegis framework.

## Structure

| Directory | Purpose |
|:----------|:--------|
| `benchmarks/` | Standardized agent benchmark tasks |
| `metrics/` | Objective metric definitions and calculation scripts |
| `regression/` | Automated regression tests for framework output |

## Dependency Rules

- **Allowed**: `evaluation/` → `runtime/`, `evaluation/` → `core/`
