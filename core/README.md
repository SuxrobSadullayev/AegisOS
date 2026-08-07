# Core — Constitutional Core (Tier 1)

## Purpose

The `core/` directory contains the **Constitutional Core** of the Aegis framework.
These files are **always loaded** into every agent session, regardless of task type.
They define the fundamental behavioral standards, epistemic discipline, and engineering
workflow that every agent must follow.

## Design Goals

- Establish non-negotiable behavioral rules for all agent interactions.
- Enforce epistemic rigor: separate facts from inferences from hypotheses.
- Provide a structured reasoning protocol that prevents "code first, think later" patterns.
- Define a complete engineering workflow from understanding through delivery.
- Specify deterministic and semantic quality gates.

## Contents

| File | Purpose | Status |
|:-----|:--------|:-------|
| `constitution.md` | Immutable operating rules — 7 mandatory, 5 recommended | ✅ Complete |
| `truth-engine.md` | Truth Engine — 5 epistemic categories for claim classification | Planned |
| `reasoning-engine.md` | Reasoning Engine — 9 structured reasoning capabilities | Planned |
| `workflow.md` | The 10-step engineering workflow | Planned |
| `quality-engine.md` | Quality Engine — 8 independent review gates | Planned |

## Token Budget

All files in `core/` combined must remain under **4,000 tokens**. This ensures
the Constitutional Core can fit within any agent's context window alongside the
actual task at hand.

## Loading Behavior

Agents reading `AEGIS.md` are instructed to load all files in `core/` at the
start of every session. These files are not optional.

## Future Improvements

- Token usage tracking and optimization.
- Version-specific core variants for different context window sizes.
- Localization support for non-English engineering teams.
