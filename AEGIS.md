# AEGIS AI FRAMEWORK
<!-- Version: 0.1.0 | Last Updated: 2025-08-07 -->

> **Aegis** is an agent-agnostic AI engineering framework that upgrades the
> reasoning quality of LLM-based coding agents through structured context,
> engineering workflows, reusable knowledge, strict quality gates, and
> modular prompts.

---

## Loading Protocol

This file is the **root manifest**. When an agent reads this file, it should
load the Constitutional Core (Tier 1) and selectively load Domain Modules
(Tier 2) based on the current task.

### Tier 1 — Constitutional Core (Always Load)

These files define non-negotiable behavioral standards:

| File | Purpose |
|:-----|:--------|
| [core/constitution.md](core/constitution.md) | Behavioral rules — the operating system for agent conduct |
| [core/truth-policy.md](core/truth-policy.md) | Epistemic discipline — fact vs inference vs hypothesis vs unknown |
| [core/reasoning.md](core/reasoning.md) | Structured reasoning protocols |
| [core/workflow.md](core/workflow.md) | The 10-step engineering workflow |
| [core/quality-gates.md](core/quality-gates.md) | Deterministic and semantic quality gates |

### Tier 2 — Domain Modules (Load On Demand)

Load only the modules relevant to the current task:

| Module | When to Load |
|:-------|:-------------|
| [modules/architecture/](modules/architecture/) | Designing systems, making architectural decisions |
| [modules/languages/python/](modules/languages/python/) | Writing or reviewing Python code |
| [modules/languages/typescript/](modules/languages/typescript/) | Writing or reviewing TypeScript code |
| [modules/languages/rust/](modules/languages/rust/) | Writing or reviewing Rust code |
| [modules/languages/c/](modules/languages/c/) | Writing or reviewing C code |
| [modules/languages/cpp/](modules/languages/cpp/) | Writing or reviewing C++ code |
| [modules/backend/](modules/backend/) | API design, databases, server-side logic |
| [modules/frontend/](modules/frontend/) | UI components, state management, accessibility |
| [modules/testing/](modules/testing/) | Writing tests, test strategy decisions |
| [modules/security/](modules/security/) | Security review, threat modeling, secure coding |
| [modules/performance/](modules/performance/) | Profiling, optimization, benchmarking |
| [modules/debugging/](modules/debugging/) | Systematic debugging, root cause analysis |
| [modules/refactoring/](modules/refactoring/) | Code restructuring, technical debt reduction |
| [modules/code-review/](modules/code-review/) | Reviewing code, providing feedback |
| [modules/documentation/](modules/documentation/) | Writing or improving documentation |
| [modules/git/](modules/git/) | Version control workflows, commit standards |
| [modules/devops/](modules/devops/) | CI/CD, Docker, Kubernetes, deployment |
| [modules/linux/](modules/linux/) | System administration, shell scripting |

### Tier 3 — Templates & Knowledge (Reference As Needed)

| Resource | Purpose |
|:---------|:--------|
| [templates/prompts/](templates/prompts/) | Structured prompt templates for common tasks |
| [templates/checklists/](templates/checklists/) | Pre/post implementation checklists |
| [templates/decision-trees/](templates/decision-trees/) | Decision frameworks for technology and architecture |
| [knowledge/](knowledge/) | Persistent knowledge base: best practices, anti-patterns, case studies |
| [examples/](examples/) | Complete worked examples |

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

## Engineering Workflow

For every engineering task, follow this sequence:

```
Understand → Analyze → Plan → Identify Risks → Implement → Review → Optimize → Test → Self-Critique → Deliver
```

See [core/workflow.md](core/workflow.md) for the complete protocol.

---

## Self-Review Criteria

Every generated artifact must be reviewed against these 10 dimensions:

| # | Dimension | Question |
|:--|:----------|:---------|
| 1 | Correctness | Does it work as intended? Are edge cases handled? |
| 2 | Consistency | Does it follow established patterns and conventions? |
| 3 | Completeness | Are all requirements addressed? Is anything missing? |
| 4 | Maintainability | Can another engineer understand and modify this easily? |
| 5 | Security | Are there any vulnerabilities? Is input validated? |
| 6 | Performance | Are there unnecessary allocations, loops, or I/O? |
| 7 | Readability | Is the code/document clear without extensive comments? |
| 8 | Reusability | Can components be reused in other contexts? |
| 9 | Modularity | Are concerns properly separated? |
| 10 | Scalability | Will this work as the system grows? |

---

## Compatibility

Aegis works with any LLM agent that reads context files:

- Claude Code / Claude Desktop → via `adapters/claude/`
- Gemini CLI / Gemini App → via `adapters/gemini/`
- Cursor → via `adapters/cursor/`
- Windsurf → via `adapters/windsurf/`
- OpenAI Codex / ChatGPT → via `adapters/codex/`
- Kiro, OpenCode, Qwen Code → via `adapters/generic/`
- Any future agent → via `adapters/generic/`

See [adapters/README.md](adapters/README.md) for setup instructions.
