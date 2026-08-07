# Layer 1: Modules — Prescriptive Domain Knowledge

## Purpose

The `modules/` directory contains **domain-specific engineering modules** loaded
on demand by the Aegis runtime. Every module is prescriptive ("do this"),
self-contained, and must comply with `core/contracts/module.md`.

## Structure

```
modules/
├── domains/
│   ├── languages/        # Python, TypeScript, Rust, C, C++
│   ├── engineering/      # Architecture, Testing, Security, Performance, Debugging, Refactoring, Review, Docs
│   └── platforms/        # Backend, Frontend, Linux, DevOps
├── standards/            # Cross-cutting standards (Naming, Formatting, Versioning)
└── workflows/            # Reusable task workflow recipes
```

## Dependency Rules

- **Allowed**: `modules/` → `core/contracts/`
- **Forbidden**: `modules/` → `runtime/`, `modules/` → `tools/`, `modules/` → `examples/`
