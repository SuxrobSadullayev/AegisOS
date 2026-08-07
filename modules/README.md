# Modules — Domain Modules (Tier 2)

## Purpose

The `modules/` directory contains **domain-specific engineering modules** that are
loaded on demand based on the current task. Each module is a self-contained unit
covering a specific engineering discipline with standards, anti-patterns, checklists,
and examples.

## Design Goals

- Provide deep, actionable engineering guidance for specific domains.
- Maintain strict modularity — each module works independently.
- Respect token budgets — each module targets < 3,000 tokens.
- Cover the full spectrum of software engineering disciplines.

## Contents

| Module | Domain | Status |
|:-------|:-------|:-------|
| `architecture/` | Software architecture patterns, ADRs, anti-patterns | Planned |
| `languages/python/` | Python engineering standards | Planned |
| `languages/typescript/` | TypeScript engineering standards | Planned |
| `languages/rust/` | Rust engineering standards | Planned |
| `languages/c/` | C engineering standards | Planned |
| `languages/cpp/` | C++ engineering standards | Planned |
| `backend/` | API design, databases, authentication | Planned |
| `frontend/` | Component design, state management, accessibility | Planned |
| `testing/` | Testing strategy, unit/integration testing | Planned |
| `security/` | Threat modeling, secure coding, security review | Planned |
| `performance/` | Profiling, optimization, benchmarking | Planned |
| `debugging/` | Systematic debugging methodology | Planned |
| `refactoring/` | Safe refactoring patterns | Planned |
| `code-review/` | Code review protocol and checklists | Planned |
| `documentation/` | Documentation standards and templates | Planned |
| `git/` | Git workflow and commit standards | Planned |
| `devops/` | CI/CD, Docker, Kubernetes | Planned |
| `linux/` | System administration, shell scripting | Planned |

## Loading Behavior

Modules are loaded only when relevant to the current task. The adapter scripts
determine which modules to include based on:

1. **Project type** — backend, frontend, fullstack
2. **Languages in use** — detected from project files
3. **Task type** — debugging, review, implementation, etc.

## Module Structure

Every module follows the standard structure defined in [CONTRIBUTING.md](../CONTRIBUTING.md):

```
module-name/
├── README.md         # Module documentation
├── standards.md      # (or patterns.md, methodology.md, etc.)
├── anti-patterns.md  # Common mistakes and how to avoid them
├── checklist.md      # Quick-reference checklist
└── examples/         # Concrete, realistic examples
```

## Future Improvements

- Module dependency declarations for cross-cutting concerns.
- Automatic module selection based on file extension analysis.
- Community-contributed modules for additional domains.
