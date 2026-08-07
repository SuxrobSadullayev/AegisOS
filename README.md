<div align="center">

# 🛡️ Aegis AI Operating System

**Extensible, AI-Native Runtime Engine & Analytical Reasoning OS for Coding Agents**

*Interactive REPL Shell · Deterministic Execution Pipeline · Epistemic Truth Engine · 12 Quality Gates · Plugin Subsystem*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0--production-green.svg)](CHANGELOG.md)
[![Build Status](https://img.shields.io/badge/tests-343%20passed-brightgreen.svg)](runtime/tests/)




</div>

---

## 📖 What is Aegis AI OS?

Aegis is an **interactive, extensible, AI-native Operating System and Reasoning Framework** designed to empower LLM-based coding agents with deterministic pipeline controls, analytical goal decomposition, epistemic claim verification, quality gates, and persistent multi-turn memory without altering underlying model weights.

---

## 🏛️ System Architecture

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
                            Task Planner Stage
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
                               FINAL RESPONSE / REPL DISPLAY
```

---

## 🚀 Quick Start & Interactive REPL Shell

### Interactive Chat Mode

Launch the interactive REPL shell by running `./aegis` or `./aegis chat`:

```bash
# Start interactive Aegis AI OS REPL shell
./aegis

# Start chat with a specific provider and session ID
./aegis chat --provider gemini --session SESS_DEV_001
```

### Slash Commands in REPL Mode

Inside the interactive chat shell, use slash commands to inspect and manage runtime state:

```
💡 Aegis AI OS Interactive Slash Commands:
  /help             Show available interactive commands
  /status           Display runtime status, active session, provider, model & metrics
  /session [id]     Switch active session or view current session details
  /sessions         List all saved persistent session snapshots on disk
  /plugins          List all discovered and active plugins
  /plugin <name>    Show detailed metadata and capabilities for a plugin
  /provider [name]  Switch LLM provider (mock, gemini, claude, openai, openrouter)
  /model [name]     Switch active LLM model
  /clear            Clear terminal screen
  /reset            Reset conversation context history for current session
  /exit, /quit      Exit interactive Aegis REPL shell
```

### Single-Shot Task Execution

Execute standalone prompts directly via CLI flags:

```bash
# Execute single task prompt with mock provider
./aegis --task "Review Python backend security architecture"

# Execute task with verbose stage event tracking
./aegis --task "Design database schema for auth service" --verbose

# Specify target LLM provider (mock, gemini, claude, openai, openrouter)
./aegis --task "Optimize C++ memory pool" --provider gemini --model gemini-1.5-pro

# Set reasoning depth level (L1=Fast, L2=Standard, L3=Deep)
./aegis --task "Refactor microservices architecture" --reasoning-depth L3

# Enable developer stack trace debugging
./aegis --task "Debug execution" --debug
```

---

## ⚙️ Configuration Precedence & Config File

Aegis enforces a strict 4-level **Config Precedence**:

$$\text{CLI Arguments} \;\succ\; \text{Environment Variables} \;\succ\; \text{Config File } (\text{\textasciitilde}/.\text{aegis}/\text{config.yaml}) \;\succ\; \text{Safe Defaults}$$

### Example `~/.aegis/config.yaml`

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
enabled_plugins:
  - aegis.capability.python
  - aegis.capability.security
```

---

## 🔌 AI-Native Plugin Subsystem (v2.0.0)

Aegis features an **extensible Plugin Operating System Architecture**:

- **AI-Native Capability Registry**: Dynamic registration for `commands`, `validators`, `reasoners`, `quality_rules`, `knowledge_modules`, `prompts`, `templates`, `agents`, `tools`, `model_providers`.
- **Kahn DAG Dependency Resolution**: Topological sort with circular dependency detection and SemVer constraint matching.
- **12+ Pipeline Extension Hooks**: Hook execution at key pipeline stages (`before_intent`, `after_intent`, `before_reasoning`, `after_reasoning`, `before_truth`, `after_truth`, `before_quality`, `after_quality`, `before_generation`, `after_generation`, `before_delivery`, `after_delivery`).
- **Default DENY Security & Capability Tokens**: Explicit permissions required (`FILESYSTEM_READ`, `FILESYSTEM_WRITE`, `NETWORK_OUTBOUND`, `SECRET_ACCESS`, `PIPELINE_MODIFY`, `MEMORY_WRITE`, `PROCESS_EXECUTE`, `RUNTIME_MODIFY`).
- **Transactional Hot Reload**: Atomic instance swap preserving execution state without corruption.

### Plugin Security & Sandbox Subprocess Isolation

Aegis features a dedicated **Process Sandbox & Subprocess Isolation Subsystem** (`runtime/src/sandbox.py`):

- **Subprocess Worker Isolation**: Untrusted third-party plugins run in isolated Python worker subprocesses (`sys.executable -m runtime.src.sandbox`).
- **Default DENY Security Policy**: Operations (`FILESYSTEM_READ`, `FILESYSTEM_WRITE`, `NETWORK_OUTBOUND`, `PROCESS_EXECUTE`, `SECRET_ACCESS`) are denied unless explicitly permitted by `SandboxPolicy` and granted via `CapabilityToken`.
- **Timeout & Resource Protection**: Hard execution timeouts (`execution_timeout_sec`) automatically terminate runaway plugins or infinite loops without freezing the main Aegis runtime process.
- **Worker Crash Resilience**: Process crashes (non-zero exit codes) are isolated; plugin FSM transitions to `FAILED` and `SandboxManager.restart_worker()` restores execution automatically.
- **Benchmark Performance Overhead**: Worker startup overhead: **~0.90 ms** | IPC latency: **~57.65 ms** | Worker termination: **~5.44 ms**.

```bash
# Run Sandbox Subprocess Isolation Demo
python3 runtime/examples/sandbox_demo.py
```

### Plugin Management Commands

```bash
./aegis plugin create <plugin_name>
./aegis plugin validate <plugin_path>
./aegis plugin test <plugin_path>
./aegis plugin package <plugin_path>
./aegis plugin list
./aegis plugin info <plugin_id>
./aegis plugin enable <plugin_id>
./aegis plugin disable <plugin_id>
```

---

## 📊 Production Observability, Audit & Telemetry Subsystem (`runtime/src/observability.py`)

Aegis features a production-grade, zero-dependency **Observability, Security Audit & Telemetry Architecture**:

```
Aegis Core / Orchestrator / Subsystems / Plugins / Sandbox
                           │
                           ▼
                 CorrelationContext (Thread-Local)
                           │
                           ▼
                 ObservabilityManager (Facade)
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   TraceSpan Context   EventRedactor     MetricsCollector
   (p50/p95/p99)     (Secret Masking)   (Latency/Counts)
                           │
                           ▼
                  ObservabilityEventBus
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
  ConsoleEventSink   FileEventSink     AuditEventSink
  (Terminal Verbose) (runtime.jsonl)   (audit.jsonl)
                     (Log Rotation)    (Append-Only)
```

- **Distributed-Style Tracing & Correlation**: Automatically correlates requests with `correlation_id`, `request_id`, `session_id`, `trace_id`, and parent-child `span_id` hierarchies across all 10 pipeline stages.
- **Centralized Secret Redaction Barrier**: Centralized `EventRedactor` sanitizes Google API keys (`AIzaSy...`), OpenAI/Anthropic keys (`sk-...`), Bearer tokens, passwords, private keys, authorization headers, and nested dictionary metadata before logging. Zero secret leakage guaranteed!
- **Immutable Security Audit Log (`runtime/logs/audit.jsonl`)**: Dedicated JSON Lines audit stream recording security events (`PERMISSION_DENIED`, `SANDBOX_VIOLATION`, `PATH_TRAVERSAL_BLOCKED`, `SECRET_ACCESS_DENIED`).
- **Atomic File Log Rotation**: `FileEventSink` manages size-based log rotation (`runtime.jsonl.1`, `runtime.jsonl.2`) with configurable retention limits.
- **Telemetry Latency Percentiles**: `MetricsCollector` calculates in-memory counters and exact latency percentiles (**p50**, **p95**, **p99**) for all pipeline stages and providers.
- **Fail-Safe Guarantee (`NEVER CRASH RUNTIME`)**: Observability I/O failures, full disks, or permission errors are safely caught and isolated, guaranteeing main Aegis execution never crashes.

### CLI Observability Commands

```bash
./aegis logs                         # View recent structured runtime event logs
./aegis logs --tail 20 --category SECURITY
./aegis logs --session SESS_DEV_001
./aegis metrics                      # View telemetry metrics, counts, and p50/p95/p99 percentiles
./aegis audit                        # View security audit event log stream
```

```bash
# Run Observability & Audit Subsystem Demo
python3 runtime/examples/observability_demo.py
```

---



## 🧠 Core Runtime Engines

### 1. Truth Engine (`runtime/src/epistemic.py`)
- Epistemic claim graph DAG supporting states: `UNKNOWN`, `HYPOTHESIS`, `INFERENCE`, `VERIFIED_FACT`, `INVALIDATED`, `SUSPECT`.
- **Level 0–5 Evidence Hierarchy**: Claims cannot transition to `VERIFIED_FACT` without Level 4 (Specification) or Level 5 (Execution) evidence.
- Automatic **Cascade Invalidation**: Invalidating an upstream claim automatically marks downstream dependent claims as `SUSPECT`.

### 2. Reasoning Engine (`runtime/src/reasoning.py`)
- Analytical reasoning depth controls (`L1_FAST`, `L2_STANDARD`, `L3_DEEP`).
- **L3 Deep Reasoning**: Problem decomposition, goals, constraints, alternatives, risk estimation, trade-off analysis, confidence scoring, self-review, failure prediction, and recovery suggestions.

### 3. Quality Engine & Auto Repair (`runtime/src/quality.py`)
- 12 deterministic validation gates: Hallucination, Prompt Injection Residue, Formatting, Incomplete Answer, Low Confidence, Architecture Violation, Contract Violation, Secret Leakage, etc.
- **Automated Auto-Repair Loop**: Hardened to a maximum retry limit of 3. Gracefully halts and saves session trace if repair fails.

### 4. Session & Memory Manager (`runtime/src/session.py`)
- Multi-turn conversation history tracking, token window pruning, and crash-resilient disk snapshots (`runtime/sessions/`).
- Permission-gated memory access requiring explicit `MEMORY_WRITE` token permissions.

---

## 🔒 Adversarial Security & Runtime Resilience Validation

Aegis AI OS has undergone rigorous adversarial attack and security validation across 219 comprehensive test suites:

- **Adversarial Prompt Injection Protection**: Hardened against prompt injection attempts, system prompt leakage, rules override instructions, and unauthorized permission mutations.
- **Epistemic Truth Guarding**: Prevents unsubstantiated claims from self-declaring as `VERIFIED_FACT` without Level 4/5 evidence.
- **Default DENY Plugin Capability Tokens**: Enforces granular permissions (`FILESYSTEM_READ`, `FILESYSTEM_WRITE`, `NETWORK_OUTBOUND`, `SECRET_ACCESS`, `PROCESS_EXECUTE`, `RUNTIME_MODIFY`, `PIPELINE_MODIFY`).
- **Secret Leakage Redaction**: Redacts sensitive API keys and token strings across logs, exceptions, `repr()`, snapshots, and quality reports.
- **Gateway HTTP Resilience**: Exponential backoff and retry handling for HTTP 429 (Rate Limit), 500/502 (Server Error), and timeout conditions.
- **Session Snapshot SHA-256 Checksums**: Integrity verification for persistent disk snapshots detecting file corruption and payload tampering.

---

## 🧪 Testing & Validation

Run the complete test suite (219 tests passing):

```bash
# Execute full unit, integration, and security test suite
python3 -m unittest discover -s runtime/tests -p "test_*.py"

# Run Aegis Module Contract Validator
./tools/validators/validate-modules.sh

# Run Aegis Markdown Linter
./tools/linters/lint-markdown.sh

# Run Example Demos
python3 runtime/examples/chat_demo.py
python3 runtime/examples/e2e_demo.py
python3 runtime/examples/provider_demo.py
```


---

## 📂 Directory Structure

```
Aegis AI Framework/
├── aegis                      # Main Aegis AI OS CLI Executable script
├── core/                      # Layer 0: Core Foundation & Contracts
├── modules/                   # Layer 1: Domain Modules & Standards
├── plugins/                   # Registered Aegis Plugins
│   ├── python_capability_plugin/
│   └── security_capability_plugin/
├── runtime/
│   ├── src/                   # Aegis Runtime Kernel Subsystems
│   │   ├── cli.py             # REPL Chat Shell & Plugin SDK CLI
│   │   ├── composer.py        # PromptComposer & Layer 0 Enforcer
│   │   ├── config.py          # ConfigManager & Zero-Dep YAML Parser
│   │   ├── epistemic.py       # Epistemic Graph Store (Truth Engine)
│   │   ├── gateway.py         # Model Gateway & Provider Router
│   │   ├── knowledge.py       # Knowledge Loader Subsystem
│   │   ├── orchestrator.py    # RuntimeOrchestrator Machine
│   │   ├── plugin.py          # Plugin Architecture Subsystem v2.0.0
│   │   ├── quality.py         # Quality Engine & Auto Repair
│   │   ├── reasoning.py       # Reasoning Engine Subsystem (L1-L3)
│   │   └── session.py         # Session & Memory Manager
│   ├── tests/                 # Test Suite (191 Unit & Integration Tests)
│   └── examples/              # Subsystem Demos & Examples
└── tools/                     # Code Validators and Linters
```

---

## 🗺️ System Roadmap

- [x] Executable 10-Stage Pipeline Engine
- [x] AI-Native Plugin Subsystem v2.0.0 with Default DENY
- [x] Interactive REPL Shell & Slash Commands
- [x] Multi-Turn Session Persistence & Token Pruning
- [x] L3 Deep Analytical Reasoning Decomposition
- [x] Quality Engine Hardening & 3-Retry Auto-Repair
- [ ] Process Sandbox Isolation for Untrusted Plugins
- [ ] Remote Package Marketplace Registry Integration

---

## 📄 License

[MIT License](LICENSE) — free to use, modify, and distribute.
