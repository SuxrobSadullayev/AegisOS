<div align="center">

# 🛡️ Aegis AI Operating System

**Extensible, AI-Native Runtime Engine & Reasoning Framework for Coding Agents**

*Deterministic Pipeline · AI-Native Plugin Architecture · Epistemic Truth Verification · Quality Gates · Multi-Turn Persistence*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0--production-green.svg)](CHANGELOG.md)
[![Build Status](https://img.shields.io/badge/tests-159%20passed-brightgreen.svg)](runtime/tests/)

</div>

---

## 📖 What is Aegis AI OS?

Aegis is an **extensible, production-grade AI Operating System and Reasoning Framework** designed to enhance the reasoning depth, architectural safety, and execution accuracy of LLM-based coding agents without modifying underlying model weights.

---

## 🏛️ System Architecture

```
                                USER REQUEST
                                     │
                                     ▼
                               CLI (`./aegis`)
                                     │
                                     ▼
                            Session Manager (Multi-Turn)
                                     │
                                     ▼
                            Intent Resolver Stage
                                     │
                                     ▼
                            Task Planner Stage
                                     │
                                     ▼
                            Knowledge Loader Stage
                                     │
                                     ▼
                            Reasoning Engine Stage
                                     │
                                     ▼
                            Truth Engine Stage (Claim DAG)
                                     │
                                     ▼
                            Plugin Hooks & Capabilities
                                     │
                                     ▼
                            Prompt Composer Stage (Layer 0 Kernel)
                                     │
                                     ▼
                            Model Gateway Stage (Provider Router)
                                     │
                                     ▼
                            Quality Engine Stage (12 Gates)
                                     │
                                     ▼
                            Auto Repair Stage (Max 3 Retries)
                                     │
                                     ▼
                            Session Persistence & Checkpoint
                                     │
                                     ▼
                               FINAL RESPONSE
```

---

## 🚀 CLI Usage & Executable Guide

Aegis provides a command-line executable (`./aegis`) for task execution, multi-turn session persistence, and plugin management:

```bash
# Execute a single task prompt with mock provider
./aegis --task "Review Python backend security architecture"

# Execute task with verbose pipeline event tracking
./aegis --task "Design database schema for auth service" --verbose

# Specify target LLM provider (mock, gemini, claude, openai, openrouter)
./aegis --task "Optimize C++ memory pool" --provider gemini

# Multi-turn session execution (preserves context across consecutive turns)
./aegis --task "Turn 1: Create Python backend project" --session SESS_DEV_001
./aegis --task "Turn 2: Add OAuth2 authentication" --session SESS_DEV_001

# List all active and persistent session snapshots
./aegis --list-sessions

# Plugin Management Shorthands
./aegis --plugins
./aegis --plugin-info aegis.capability.python

# Aegis Executable Version & Help
./aegis --version
./aegis --help
```

---

## 🔌 AI-Native Plugin Subsystem (v2.0.0)

Aegis features an **extensible Plugin Operating System Architecture**:

- **AI-Native Capability Registry**: Dynamic registration for `commands`, `validators`, `reasoners`, `quality_rules`, `knowledge_modules`, `prompts`, `templates`, `agents`, `tools`, `model_providers`.
- **Kahn DAG Dependency Resolution**: Topological sort with circular dependency detection and SemVer constraint matching.
- **12+ Pipeline Extension Hooks**: Hook execution at key pipeline stages (`before_intent`, `after_intent`, `before_reasoning`, `after_reasoning`, `before_truth`, `after_truth`, `before_quality`, `after_quality`, `before_generation`, `after_generation`, `before_delivery`, `after_delivery`).
- **Default DENY Security & Capability Tokens**: Explicit permissions required (`FILESYSTEM_READ`, `FILESYSTEM_WRITE`, `NETWORK_OUTBOUND`, `SECRET_ACCESS`, `PIPELINE_MODIFY`, `MEMORY_WRITE`, `PROCESS_EXECUTE`, `RUNTIME_MODIFY`).
- **Transactional Hot Reload**: Atomic instance swap preserving execution state without corruption.
- **Layer 0 Kernel Priority**: Immutable Kernel rules take precedence over plugin prompt contributions.

### Aegis Plugin SDK Commands

```bash
# Create a new plugin scaffolding template
./aegis plugin create <plugin_name>

# Validate manifest schema and version compatibility
./aegis plugin validate <plugin_path>

# Run plugin isolation unit test harness
./aegis plugin test <plugin_path>

# Bundle plugin into a .aegis-plugin.zip package
./aegis plugin package <plugin_path>

# List all discovered plugins and their states
./aegis plugin list

# Inspect detailed plugin metadata and capabilities
./aegis plugin info <plugin_id>

# Dynamically enable or disable plugins
./aegis plugin enable <plugin_id>
./aegis plugin disable <plugin_id>
```

---

## 🧠 Core Engines & Subsystems

### 1. Truth Engine (`runtime/src/epistemic.py`)
- Epistemic claim graph DAG supporting states: `UNKNOWN`, `HYPOTHESIS`, `INFERENCE`, `VERIFIED_FACT`, `INVALIDATED`, `SUSPECT`.
- **Level 0–5 Evidence Hierarchy**: Claims cannot transition to `VERIFIED_FACT` without Level 4 (Specification) or Level 5 (Execution) evidence.
- Automatic **Cascade Invalidation**: Invalidating an upstream claim automatically marks downstream dependent claims as `SUSPECT`.

### 2. Reasoning Engine (`runtime/src/reasoning.py`)
- Dynamic strategy registry allowing custom reasoning algorithms.
- Enforces depth controls (`L1_FAST`, `L2_STANDARD`, `L3_DEEP`).

### 3. Quality Engine & Auto Repair (`runtime/src/quality.py`)
- 12 deterministic validation gates: Hallucination, Prompt Injection Residue, Formatting, Incomplete Answer, Low Confidence, Architecture Violation, Contract Violation, Secret Leakage, etc.
- **Automated Auto-Repair Loop**: Hardened to a maximum retry limit of 3. Gracefully halts and saves session trace if repair fails.

### 4. Session & Memory Manager (`runtime/src/session.py`)
- Multi-turn conversation history tracking, token window pruning, and crash-resilient disk snapshots (`runtime/sessions/`).
- Permission-gated memory access requiring explicit `MEMORY_WRITE` token permissions.

---

## 🧪 Testing & Validation

Run the complete test suite (159 tests passing):

```bash
# Execute unit and integration tests
python3 -m unittest discover -s runtime/tests -p "test_*.py"

# Run Aegis Module Contract Validator
./tools/validators/validate-modules.sh

# Run Aegis Markdown Linter
./tools/linters/lint-markdown.sh

# Run Aegis Plugin Architecture Demo
python3 -m runtime.examples.plugin_demo
```

---

## 📂 Directory Structure

```
Aegis AI Framework/
├── aegis                      # Main CLI Executable script
├── core/                      # Layer 0: Core Foundation & Contracts
├── modules/                   # Layer 1: Domain Modules & Standards
├── plugins/                   # Registered Aegis Plugins
│   ├── python_capability_plugin/
│   └── security_capability_plugin/
├── runtime/
│   ├── src/                   # Aegis Runtime Kernel Subsystems
│   │   ├── cli.py             # CLI Entrypoint & Plugin SDK CLI
│   │   ├── composer.py        # PromptComposer & Layer 0 Enforcer
│   │   ├── config.py          # ConfigManager & Core Types
│   │   ├── epistemic.py       # Epistemic Graph Store (Truth Engine)
│   │   ├── gateway.py         # Model Gateway & Provider Router
│   │   ├── knowledge.py       # Knowledge Loader Subsystem
│   │   ├── orchestrator.py    # RuntimeOrchestrator Machine
│   │   ├── plugin.py          # Plugin Architecture Subsystem v2.0.0
│   │   ├── quality.py         # Quality Engine & Auto Repair
│   │   ├── reasoning.py       # Reasoning Engine Subsystem
│   │   └── session.py         # Session & Memory Manager
│   ├── tests/                 # Test Suite (159 Unit & Integration Tests)
│   └── examples/              # Subsystem Demos & Examples
└── tools/                     # Code Validators and Linters
```

---

## 📄 License

[MIT License](LICENSE) — free to use, modify, and distribute.
