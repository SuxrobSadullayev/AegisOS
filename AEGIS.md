# AEGIS AI FRAMEWORK
<!-- Version: 0.2.0 | Last Updated: 2025-08-07 -->

> **Aegis** is an agent-agnostic AI engineering framework that upgrades the
> reasoning quality of LLM-based coding agents through structured context,
> engineering workflows, reusable knowledge, strict quality gates, and
> modular prompts.

---

## Loading Protocol & Execution Pipeline

Aegis processes context through a 4-stage execution pipeline:

```
Knowledge Layer (core/, modules/, knowledge/)
       │
       ▼
Runtime Loader (runtime/loaders/)
       │
       ▼
Module Resolver (runtime/resolvers/)
       │
       ▼
Prompt Generator (runtime/generators/)
       │
       ▼
Adapter Transformer (runtime/adapters/)
       │
       ▼
Target AI Agent
```

### Layer 0 — Core (Always Loaded)

These files define non-negotiable operating rules, engines, and contracts:

| File | Purpose |
|:-----|:--------|
| [core/kernel/constitution.md](core/kernel/constitution.md) | Immutable operating rules — the OS for agent conduct |
| [core/engines/truth-engine.md](core/engines/truth-engine.md) | Truth Engine — 5 epistemic categories for claim classification |
| [core/engines/reasoning-engine.md](core/engines/reasoning-engine.md) | Reasoning Engine — 9 structured reasoning capabilities |
| [core/workflow/workflow.md](core/workflow/workflow.md) | The 10-step universal engineering workflow |
| [core/engines/quality-engine.md](core/engines/quality-engine.md) | Quality Engine — 8 independent review gates |
| [core/contracts/module.md](core/contracts/module.md) | Standard interface contract for all Aegis modules |

### Layer 1 — Domain Modules & Knowledge (Loaded On Demand)

| Directory | Purpose |
|:----------|:--------|
| [modules/domains/languages/](modules/domains/languages/) | Language-specific engineering standards (Python, TS, Rust, C, C++) |
| [modules/domains/engineering/](modules/domains/engineering/) | Engineering disciplines (Architecture, Testing, Security, Performance, Debugging, Refactoring, Review, Docs) |
| [modules/domains/platforms/](modules/domains/platforms/) | Platform domain standards (Backend, Frontend, Linux, DevOps) |
| [modules/standards/](modules/standards/) | Cross-cutting engineering standards (Naming, Formatting, Versioning) |
| [modules/workflows/](modules/workflows/) | Reusable task workflow recipes |
| [knowledge/](knowledge/) | Descriptive knowledge base (Practices, Patterns, Anti-Patterns, Case Studies) |

### Layer 2 — Runtime & Tooling (Execution & Validation)

| Directory | Purpose |
|:----------|:--------|
| [runtime/](runtime/) | Execution pipeline: Loaders, Resolvers, Generators, Adapters |
| [evaluation/](evaluation/) | Framework benchmarks, metrics, and regression testing |
| [tools/](tools/) | Development tools: Validators, Linters, Scaffolding |
| [examples/](examples/) | End-to-end usage examples and integrations |

---

## Absolute Rules

These rules override all other instructions:

1. **Never invent technical facts.** If something cannot be verified, say so explicitly.
2. **Never fabricate APIs, version numbers, or library interfaces.**
3. **Never pretend certainty.** Always separate: Fact → Inference → Hypothesis → Unknown.
4. **Always reason before coding.** Never start implementation without analysis.
5. **Always explain important decisions.** Silent choices create maintenance debt.
6. **Prefer correctness over confidence.** A correct "I don't know" beats a confident wrong answer.
7. **Prefer maintainability over cleverness.** Code is read far more than it is written.
8. **Prefer explicitness over magic.** Hidden behavior creates hidden bugs.

---

## Compatibility

Aegis works with any LLM agent via model-specific adapters in `runtime/adapters/`:

- Claude Code / Claude Desktop → via `runtime/adapters/claude/`
- Gemini CLI / Gemini App → via `runtime/adapters/gemini/`
- Cursor → via `runtime/adapters/cursor/`
- Windsurf → via `runtime/adapters/windsurf/`
- OpenAI Codex / ChatGPT → via `runtime/adapters/codex/`
- Kiro → via `runtime/adapters/kiro/`
- Qwen Code → via `runtime/adapters/qwen/`
- Generic / Future Agents → via `runtime/adapters/generic/`
