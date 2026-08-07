# Aegis Quickstart Setup Guide

## Step 1: Generate Adapter Context

```bash
# Generate CLAUDE.md for Claude Code
./runtime/adapters/claude/generate.sh python security > CLAUDE.md

# Generate AGENTS.md for Gemini CLI
./runtime/adapters/gemini/generate.sh python security > AGENTS.md
```

## Step 2: Start Agent Session

The agent will automatically read the generated context file and operate with Aegis's Layer 0 Kernel discipline.
