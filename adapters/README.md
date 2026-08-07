# Adapters — Agent-Specific Configuration Generators

## Purpose

The `adapters/` directory contains **shell scripts** that assemble Aegis modules
into agent-specific configuration files. Each adapter reads from the canonical
Aegis source (core, modules, templates) and emits a file in the format expected
by a specific LLM agent.

## Design Goals

- Maintain a single source of truth for all engineering standards.
- Support every major LLM coding agent through format-specific adapters.
- Allow selective module inclusion based on project needs.
- Keep generated output within agent-specific token limits.

## Supported Agents

| Adapter | Agent(s) | Output File | Status |
|:--------|:---------|:------------|:-------|
| `claude/` | Claude Code, Claude Desktop | `CLAUDE.md` | Planned |
| `gemini/` | Gemini CLI, Gemini App | `AGENTS.md` | Planned |
| `cursor/` | Cursor | `.cursorrules` | Planned |
| `windsurf/` | Windsurf | `.windsurfrules` | Planned |
| `codex/` | OpenAI Codex, ChatGPT | `codex.md` | Planned |
| `generic/` | Kiro, OpenCode, Qwen Code, any future agent | `AGENT_CONTEXT.md` | Planned |

## Usage

```bash
# Generate configuration for your agent
./adapters/claude/generate.sh [--modules python,testing,security] > CLAUDE.md

# The --modules flag is optional. Without it, only the core is included.
# With it, specified domain modules are appended.
```

## How Adapters Work

1. **Read** — Adapter reads `core/` files (always included).
2. **Select** — Based on `--modules` flag, selects domain modules.
3. **Transform** — Applies agent-specific formatting (if needed).
4. **Emit** — Outputs a single file to stdout.

## Future Improvements

- Auto-detection of project type and languages for automatic module selection.
- Token counting to warn when output exceeds agent context limits.
- Interactive module selection mode.
- Watch mode for automatic regeneration on module changes.
