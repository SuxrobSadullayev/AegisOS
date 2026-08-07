# Templates — Reusable Templates (Tier 3)

## Purpose

The `templates/` directory contains **reusable templates** for common engineering
tasks. These are not loaded in bulk — agents reference specific templates when
performing relevant tasks.

## Design Goals

- Provide structured, fill-in-the-blank templates for engineering activities.
- Ensure consistency across projects and teams.
- Keep each template under 1,500 tokens for efficient context usage.

## Contents

| Directory | Purpose | Status |
|:----------|:--------|:-------|
| `prompts/` | Structured prompt templates for analyze, implement, review, debug, refactor, document | Planned |
| `checklists/` | Pre/post implementation, security review, and deployment checklists | Planned |
| `decision-trees/` | Structured decision frameworks for technology and architecture choices | Planned |

## Usage

Templates are referenced by agents when performing specific tasks. For example,
when an agent is asked to debug an issue, it can load `templates/prompts/debug.md`
to follow a structured debugging protocol.

## Future Improvements

- Template versioning for backward compatibility.
- Custom template generation based on project type.
- Template validation and linting.
