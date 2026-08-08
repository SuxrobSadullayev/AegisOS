<div align="center">

# 🛡️ Aegis AI Operating System

**Production-Grade, AI-Native Operating System & Multi-Agent Execution Framework for Autonomous Coding Agents**

*Interactive REPL Shell · Multi-Agent Event Bus · Process Sandbox Isolation · Supply Chain Security · Epistemic Truth Engine · 12 Quality Gates*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.3.0--production-green.svg)](CHANGELOG.md)
[![Build Status](https://img.shields.io/badge/tests-418%2B%20passed-brightgreen.svg)](runtime/tests/)

</div>

---

## 📖 What is Aegis AI OS?

**Aegis AI Operating System** is a secure, interactive, zero-external-dependency AI Operating System designed to coordinate autonomous AI agents, execute LLM coding workflows, and enforce security policies.

Unlike traditional wrappers, Aegis operates as a **Layer 0 Kernel Engine** that enforces deterministic execution pipelines, Default DENY permission models, subprocess sandbox isolation, HMAC digital signature verification, multi-agent event bus routing, and epistemic claim validation without modifying model weights.

---

## ✨ What Can Aegis Do?

- **🤖 Multi-Agent Orchestration:** Coordinate specialized AI agents (e.g. Code Generator, Security Auditor, Quality Inspector) over a secure, priority-based event bus with circular delegation protection.
- **⚡ Interactive REPL & CLI:** High-performance terminal chat shell with slash commands (`/status`, `/session`, `/plugins`, `/provider`) and single-shot task execution.
- **🛡️ Process Sandbox Isolation:** Execute third-party plugins and untrusted code in isolated Python worker subprocesses with Default DENY filesystem, network, and subprocess restrictions.
- **📦 Plugin Marketplace & Supply Chain Security:** Package, verify, publish, install, update, and rollback `.aegis-plugin` bundles with SHA-256 integrity hashes and HMAC-SHA256 digital signatures.
- **🌐 Multi-Provider Model Gateway:** Seamless provider routing across **Google Gemini**, **Anthropic Claude**, **OpenAI**, **OpenRouter**, and **Mock** providers with exponential backoff retries and zero secret leakage.
- **🔒 Centralized Secret Redaction:** Guarantees zero secret leakage by masking API keys, JWT tokens, and credentials across logs, error tracebacks, snapshots, and `repr()` strings.
- **🧠 Epistemic Truth Engine:** Verify AI reasoning claims using DAG evidence hierarchies (Level 0–5) and automatic cascade invalidation.
- **📊 Production Observability & Audit:** Structured JSONL logging (`runtime.jsonl`), immutable security audit logging (`audit.jsonl`), and p50/p95/p99 latency telemetry.

---

## 🚀 Installation & Quick Start

### Installation

Aegis is built with **zero external Python dependencies** (Python 3.12+ standard library only). No `pip install` or complex setup required!

```bash
# 1. Clone the Aegis repository
git clone https://github.com/SuxrobSadullayev/AegisOS.git
cd AegisOS

# 2. Make the aegis CLI executable
chmod +x aegis

# 3. Verify installation
./aegis --version
```

---

## ⚙️ Configuration & Environment Setup

Aegis enforces a strict 4-level **Config Precedence**:

$$\text{CLI Arguments} \;\succ\; \text{Environment Variables} \;\succ\; \text{Config File } (\text{\textasciitilde}/.\text{aegis}/\text{config.yaml}) \;\succ\; \text{Safe Defaults}$$

### Setting API Keys

Set environment variables for your target LLM provider:

```bash
# Google Gemini
export GEMINI_API_KEY="your-gemini-api-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# OpenRouter
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

*Note: If no API key is set, Aegis gracefully runs in offline MOCK mode for testing.*

### Configuration File (`~/.aegis/config.yaml`)

```yaml
# Aegis AI OS Configuration File
provider: mock
model: gemini-1.5-pro
reasoning_depth: L2
temperature: 0.7
max_tokens: 4096
max_retries: 3
confidence_threshold: 0.70
verbose: false
debug_mode: false
```

---

## 🎯 Running Tasks & Interactive REPL

### 1. Interactive Chat Shell

Launch the interactive Aegis REPL shell:

```bash
# Start interactive shell
./aegis

# Start chat with a specific provider and session ID
./aegis chat --provider gemini --session SESS_DEV_001
```

#### Interactive Slash Commands

Inside the REPL shell, use slash commands:
- `/help` — Show available commands
- `/status` — Display runtime status, provider, active session & metrics
- `/session [id]` — Switch or view persistent sessions
- `/plugins` — List discovered and active plugins
- `/provider [name]` — Switch LLM provider (`mock`, `gemini`, `claude`, `openai`, `openrouter`)
- `/clear` — Clear terminal screen
- `/exit` — Exit interactive REPL

### 2. Single-Shot Task Execution

Execute standalone prompts directly from your terminal:

```bash
# Single task execution
./aegis --task "Review Python backend security architecture"

# Execution with verbose stage event tracking
./aegis --task "Design database schema" --verbose

# Specify target LLM provider and reasoning depth (L1=Fast, L2=Standard, L3=Deep)
./aegis --task "Optimize C++ memory pool" --provider gemini --reasoning-depth L3
```

---

## 🌐 Supported LLM Providers

Aegis includes a built-in provider router supporting:

| Provider | `--provider` | Environment Variable | Default Model |
| :--- | :--- | :--- | :--- |
| **Mock** (Offline Default) | `mock` | N/A | `mock-v1` |
| **Google Gemini** | `gemini` | `GEMINI_API_KEY` | `gemini-1.5-pro` |
| **Anthropic Claude** | `claude` | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| **OpenAI** | `openai` | `OPENAI_API_KEY` | `gpt-4o` |
| **OpenRouter** | `openrouter` | `OPENROUTER_API_KEY` | `anthropic/claude-3.5-sonnet` |

---

## 🔌 AI-Native Plugin Subsystem & SDK

Create and manage custom Aegis plugins with Default DENY security:

```bash
# Plugin SDK CLI Commands
./aegis plugin create <name>     # Generate new plugin template
./aegis plugin validate <path>   # Validate plugin manifest schema
./aegis plugin test <path>       # Run plugin test harness
./aegis plugin package <path>    # Package plugin into .aegis-plugin bundle
./aegis plugin list              # List all installed plugins
./aegis plugin enable <id>       # Enable plugin
./aegis plugin disable <id>      # Disable plugin
```

---

## 🤖 Multi-Agent Coordination System

Aegis includes a multi-agent orchestration engine featuring deterministic agent selection, capability matching, and task coordination:

```bash
./aegis agents                   # List all registered AI agents
./aegis agent info <agent_id>    # Display agent descriptor & capabilities
./aegis events                   # View multi-agent event bus telemetry
./aegis tasks                    # View task coordinator metrics
```

```bash
# Run Multi-Agent Coordination Demo
python3 runtime/examples/agents_demo.py
```

---

## 📦 Plugin Marketplace & Package Registry

Aegis features a supply chain security marketplace for plugin distribution:

```bash
./aegis marketplace search <query>    # Search registry for plugins
./aegis marketplace install <package> # Install .aegis-plugin bundle
./aegis marketplace verify <package>  # Verify package SHA-256 & digital signature
./aegis marketplace rollback <id> <v> # Atomic rollback to a previous version
./aegis marketplace publish <path>    # Publish plugin package to registry
./aegis marketplace block <id>        # Blacklist / block malicious plugin
```

```bash
# Run Marketplace Demo
python3 runtime/examples/marketplace_demo.py
```

---

## 🔒 Security & Data Safety Model

- **Default DENY Permissions:** Plugins and agents require explicit permission tokens (`FILESYSTEM_READ`, `FILESYSTEM_WRITE`, `NETWORK_OUTBOUND`, `PROCESS_EXECUTE`, `SECRET_ACCESS`).
- **Subprocess Sandbox:** Untrusted code runs in isolated worker processes with execution timeouts and memory boundaries.
- **Zero Secret Leakage:** API keys and credentials are redacted across logs, stack traces, and `repr()` calls.
- **Zip Bomb & Traversal Guard:** Package decompression limits (max 50MB, max 100 files) and `..` path traversal blocking.
- **Circular Delegation Defense:** Maximum delegation depth (depth 5) prevents infinite multi-agent task loops.

---

## 🧪 Testing & Validation

Run the complete test suite (**418+ tests passing**):

```bash
# Execute full unit, security, multi-agent, and marketplace test suite
python3 -m unittest discover -s runtime/tests -p "test_*.py"

# Run Aegis Module Contract Validator
./tools/validators/validate-modules.sh

# Run Aegis Markdown Linter
./tools/linters/lint-markdown.sh
```

---

## 🏛️ System Architecture Details

```
                                USER REQUEST / REPL CHAT
                                           │
                                           ▼
                                CLI Engine (`./aegis`)
                                           │
                                           ▼
                            Config Precedence Manager
                      (CLI > Env > ~/.aegis/config.yaml > Default)
                                           │
                                           ▼
                            Session Manager (Multi-Turn Memory)
                                           │
                                           ▼
                            Intent Resolver Stage
                                           │
                                           ▼
                            Task Planner Stage ──► Task Coordinator ──► Multi-Agent Event Bus
                                           │
                                           ▼
                            Knowledge Loader Stage
                                           │
                                           ▼
                            Reasoning Engine Stage (L1 / L2 / L3)
                                           │
                                           ▼
                            Truth Engine Stage (Claim DAG)
                                           │
                                           ▼
                            Plugin Hooks & Capability Registry
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
                            Session Persistence & Observability Audit
                                           │
                                           ▼
                                FINAL RESPONSE / REPL DISPLAY
```

---

## 📂 Repository Structure

```
AegisOS/
├── aegis                      # Main Aegis AI OS CLI Executable
├── modules/                   # Standards & Domain Definitions
├── plugins/                   # Registered Aegis Plugins
├── runtime/
│   ├── src/                   # Aegis Kernel Subsystems
│   │   ├── agents.py          # Multi-Agent Coordination & AgentRegistry
│   │   ├── cli.py             # CLI Entrypoint & REPL Chat Shell
│   │   ├── composer.py        # PromptComposer & Layer 0 Kernel
│   │   ├── config.py          # Config Precedence & Zero-Dep Parser
│   │   ├── epistemic.py       # Epistemic Truth Engine
│   │   ├── event_bus.py       # Secure Multi-Agent Event Bus
│   │   ├── gateway.py         # Model Gateway & Provider Router
│   │   ├── marketplace.py     # Supply Chain Marketplace & Package Registry
│   │   ├── observability.py   # Logging, Tracing, Metrics & Audit
│   │   ├── orchestrator.py    # RuntimeOrchestrator Machine
│   │   ├── plugin.py          # Plugin Architecture v2.0.0
│   │   ├── quality.py         # Quality Engine & Auto-Repair
│   │   ├── reasoning.py       # L1-L3 Reasoning Engine
│   │   ├── sandbox.py         # Subprocess Process Sandbox Isolation
│   │   └── session.py         # Persistent Session Manager
│   ├── tests/                 # 418+ Unit, Integration & Security Tests
│   └── examples/              # Subsystem Demos
└── tools/                     # Code Contract Validators & Linters
```

---

## 📄 License

[MIT License](LICENSE) — free to use, modify, and distribute.
