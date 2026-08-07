<div align="center">

# 🛡️ Aegis AI Framework

**Upgrade the reasoning quality of any LLM-based coding agent.**

*Structured context · Engineering workflows · Quality gates · Modular prompts*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-orange.svg)](CHANGELOG.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## What is Aegis?

Aegis is an **agent-agnostic AI engineering framework** that improves how LLM-based coding agents reason, plan, code, debug, and review — without modifying model weights.

It works by providing **structured context** that teaches agents to think like senior engineers: analyze before coding, plan before implementing, review before delivering.

### What Aegis Is

- ✅ An **engineering framework** — structured modules with clear interfaces
- ✅ **Agent-agnostic** — works with Claude, Gemini, GPT, Cursor, Windsurf, Codex, and any future agent
- ✅ **Zero-dependency** — pure Markdown and POSIX shell scripts, nothing to install
- ✅ **Modular** — adopt one module or all of them, no all-or-nothing commitment
- ✅ **Production-grade** — designed for real engineering teams, not demos

### What Aegis Is Not

- ❌ Not a prompt collection or "awesome prompts" list
- ❌ Not a fine-tuning dataset
- ❌ Not a chatbot personality
- ❌ Not an SDK or runtime library

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/aegis-ai-framework.git
cd aegis-ai-framework
```

### 2. Generate Agent Configuration

Choose your agent and run the adapter:

```bash
# For Claude Code / Claude Desktop
./adapters/claude/generate.sh > CLAUDE.md

# For Gemini CLI / Gemini App
./adapters/gemini/generate.sh > .agents/AGENTS.md

# For Cursor
./adapters/cursor/generate.sh > .cursorrules

# For Windsurf
./adapters/windsurf/generate.sh > .windsurfrules

# For any other agent
./adapters/generic/generate.sh > AGENT_CONTEXT.md
```

### 3. Start Working

The agent will automatically read the generated context file and operate with Aegis's engineering discipline.

---

## Architecture

Aegis uses a **3-tier loading model** designed to respect token budgets:

```
┌─────────────────────────────────────────────────────────┐
│                    AEGIS.md (Root Manifest)              │
│               Entry point for all agents                 │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
│   TIER 1: CORE  │ │ TIER 2: DOMAIN│ │ TIER 3: TEMPLATES│
│  Always Loaded  │ │  On Demand    │ │  Referenced       │
│                 │ │               │ │                   │
│ • Constitution  │ │ • Architecture│ │ • Prompts         │
│ • Truth Policy  │ │ • Languages   │ │ • Checklists      │
│ • Reasoning     │ │ • Security    │ │ • Decision Trees  │
│ • Workflow      │ │ • Testing     │ │ • Knowledge Base  │
│ • Quality Gates │ │ • DevOps      │ │ • Examples         │
│                 │ │ • ...12 more  │ │                   │
│  ~4K tokens     │ │ ~3K per module│ │ ~1.5K per template│
└─────────────────┘ └───────────────┘ └──────────────────┘
```

### Tier 1 — Constitutional Core

Always loaded into every agent session. Defines non-negotiable behavioral rules, epistemic standards, reasoning protocols, engineering workflow, and quality gates.

### Tier 2 — Domain Modules

Loaded on demand based on the current task. Each module covers a specific engineering domain (architecture, testing, security, etc.) with standards, anti-patterns, checklists, and examples.

### Tier 3 — Templates & Knowledge

Referenced as needed. Includes structured prompt templates, pre/post implementation checklists, decision frameworks, and a persistent knowledge base.

---

## Project Structure

```
aegis/
├── AEGIS.md                 # Root manifest (agent entry point)
├── README.md                # This file
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # How to contribute
├── CHANGELOG.md             # Version history
│
├── core/                    # Tier 1: Constitutional Core
├── modules/                 # Tier 2: Domain Modules
│   ├── architecture/        │   ├── testing/
│   ├── security/            │   ├── performance/
│   ├── debugging/           │   ├── refactoring/
│   ├── code-review/         │   ├── documentation/
│   ├── git/                 │   ├── devops/
│   ├── linux/               │   ├── backend/
│   ├── frontend/            │   └── languages/
│
├── templates/               # Tier 3: Reusable Templates
├── adapters/                # Agent-specific config generators
├── knowledge/               # Persistent knowledge base
├── evaluation/              # Benchmarks & self-review
├── automation/              # Build, lint, test scripts
└── examples/                # Complete worked examples
```

---

## Supported Agents

| Agent | Adapter | Output Format |
|:------|:--------|:--------------|
| Claude Code / Claude Desktop | `adapters/claude/` | `CLAUDE.md` |
| Gemini CLI / Gemini App | `adapters/gemini/` | `AGENTS.md` |
| Cursor | `adapters/cursor/` | `.cursorrules` |
| Windsurf | `adapters/windsurf/` | `.windsurfrules` |
| OpenAI Codex / ChatGPT | `adapters/codex/` | `codex.md` |
| Kiro, OpenCode, Qwen Code | `adapters/generic/` | `AGENT_CONTEXT.md` |
| Any future agent | `adapters/generic/` | `AGENT_CONTEXT.md` |

---

## Engineering Principles

Aegis is built on these foundational principles:

1. **Reason before coding** — analyze the problem before writing solutions
2. **Correctness over confidence** — a correct "I don't know" beats a wrong answer
3. **Maintainability over cleverness** — code is read far more than written
4. **Explicitness over magic** — hidden behavior creates hidden bugs
5. **Facts over assumptions** — separate fact, inference, hypothesis, and unknown
6. **Quality gates are non-negotiable** — deterministic checks before semantic review
7. **Modularity by default** — every component should be independently usable
8. **Incremental adoption** — teams can adopt one module at a time

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Priority Areas
- New domain modules
- Language-specific engineering standards
- Adapter improvements
- Real-world examples and case studies
- Benchmark development

---

## Roadmap

| Phase | Status | Modules |
|:------|:-------|:--------|
| Phase 1: Foundation | 🔨 In Progress | Core modules (constitution, truth policy, reasoning, workflow, quality gates) |
| Phase 2: Engineering Disciplines | ⏳ Planned | Architecture, testing, security, performance, debugging, refactoring, code review, documentation, git, devops |
| Phase 3: Languages | ⏳ Planned | Python, TypeScript, Rust, C, C++ |
| Phase 4: Domains | ⏳ Planned | Backend, frontend, Linux |
| Phase 5: Templates | ⏳ Planned | Prompts, checklists, decision trees |
| Phase 6: Infrastructure | ⏳ Planned | Adapters, knowledge base, evaluation, automation |
| Phase 7: Examples | ⏳ Planned | Complete worked examples |

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.

---

<div align="center">

**Aegis** — *Because better context creates better code.*

</div>
