# Layer 0: Core — Immutable Framework Foundation

## Purpose

The `core/` directory contains the **Core Foundation (Layer 0)** of Aegis.
These files represent the immutable operating system, engines, workflows, and
contracts of the framework. All other layers depend on `core/`, but `core/`
depends on nothing.

## Subdirectory Structure

| Directory | Purpose | Stability |
|:----------|:--------|:----------|
| `kernel/` | Immutable operating rules (`constitution.md`) | 🔒 Frozen (Major version change) |
| `engines/` | First-class functional engines (`truth-engine.md`, `reasoning-engine.md`, `quality-engine.md`) | 🔒 Frozen |
| `workflow/` | Universal 10-step engineering workflow (`workflow.md`) | 🔒 Frozen |
| `contracts/` | Module interface contracts (`module.md`) | 🔒 Frozen |

## Dependency Rules

- **Dependencies**: NONE. `core/` must not import or depend on any other directory.
- **Inward Flow**: `modules/`, `runtime/`, `evaluation/`, `tools/`, and `examples/` all depend on `core/`.

## Token Budget

All files in `core/` combined MUST remain under **4,000 tokens** total.
