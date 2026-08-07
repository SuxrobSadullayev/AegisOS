<div align="center">

# 🛡️ Aegis AI Framework

**Upgrade the reasoning quality of any LLM-based coding agent.**

*Structured context · Engineering workflows · Quality gates · Modular prompts*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0--alpha-orange.svg)](CHANGELOG.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## What is Aegis?

Aegis is an **agent-agnostic AI engineering framework** that improves how LLM-based coding agents reason, plan, code, debug, and review — without modifying model weights.

---

## Architecture (7 Frozen Layers)

```
aegis/
├── core/                    # Layer 0: Immutable Foundation (Kernel, Engines, Workflow, Contracts)
├── modules/                 # Layer 1: Prescriptive Domain Modules & Standards
├── knowledge/               # Layer 1: Descriptive Knowledge Base & Patterns
├── runtime/                 # Layer 2: Context Execution Pipeline (Loaders, Resolvers, Generators, Adapters)
├── evaluation/              # Layer 3: Objective Metrics & Benchmarks
├── tools/                   # Layer 3: Framework Development & Validation Tools
└── examples/                # Layer 4: End-to-End Demonstrations & Integrations
```

### Execution Pipeline

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
Target AI Agent (Claude, Gemini, GPT, Cursor, Windsurf, Codex, Kiro, Qwen)
```

---

## Supported Agents

- Claude Code / Claude Desktop (`runtime/adapters/claude/`)
- Gemini CLI / Gemini App (`runtime/adapters/gemini/`)
- Cursor (`runtime/adapters/cursor/`)
- Windsurf (`runtime/adapters/windsurf/`)
- OpenAI Codex / ChatGPT (`runtime/adapters/codex/`)
- Kiro (`runtime/adapters/kiro/`)
- Qwen Code (`runtime/adapters/qwen/`)
- Generic / Future LLM Agents (`runtime/adapters/generic/`)

---

## Aegis Plugin Architecture Subsystem v2.0.0

Aegis includes an AI-native Plugin Architecture Subsystem that transforms Aegis into an extensible AI Operating System.

### Key Capabilities

- **AI-Native Capability Registry**: Dynamic registration for `commands`, `validators`, `reasoners`, `quality_rules`, `knowledge_modules`, `prompts`, `templates`, `agents`, `tools`, `model_providers`.
- **Deterministic Dependency Graph**: Kahn's topological sort algorithm with circular dependency detection and SemVer constraint matching.
- **Transactional Hot Reload**: Atomic instance swap preserving execution state without corruption.
- **Pipeline Hook Dispatcher**: 12+ extension hooks across the 10-stage execution pipeline (`before_intent`, `after_intent`, `before_reasoning`, `after_reasoning`, `before_truth`, `after_truth`, `before_quality`, `after_quality`, `before_generation`, `after_generation`, `before_delivery`, `after_delivery`).
- **Default DENY Security & Capabilities**: Capability tokens with explicit permission checks (`FILESYSTEM_READ`, `FILESYSTEM_WRITE`, `NETWORK_OUTBOUND`, `SECRET_ACCESS`, `PIPELINE_MODIFY`, `MEMORY_WRITE`, etc.).
- **Kernel Priority**: Layer 0 Kernel context always maintains top priority over plugin prompt contributions.

### Aegis Plugin SDK CLI Commands

```bash
# Create a new plugin template
python3 -m runtime.src.cli plugin create <plugin_name>

# Validate plugin manifest schema and compatibility
python3 -m runtime.src.cli plugin validate <plugin_path>

# Run plugin isolation unit test harness
python3 -m runtime.src.cli plugin test <plugin_path>

# Package plugin into .aegis-plugin.zip archive
python3 -m runtime.src.cli plugin package <plugin_path>

# List all discovered plugins and their states
python3 -m runtime.src.cli plugin list

# View detailed plugin metadata and capabilities
python3 -m runtime.src.cli plugin info <plugin_id>

# Enable / Disable plugins dynamically
python3 -m runtime.src.cli plugin enable <plugin_id>
python3 -m runtime.src.cli plugin disable <plugin_id>
```

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.

