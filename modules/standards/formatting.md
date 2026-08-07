# Formatting Standards
<!-- Module ID: modules.standards.formatting | Version: 1.0.0 | Token Budget: ~400 -->

## Purpose

Defines layout, indentation, line length, and Markdown formatting rules.

## Standards

- **Line Length**: Keep lines under 100 characters where practical.
- **Indentation**: 2 spaces for Markdown/JSON/YAML; 4 spaces for Python/Rust/C.
- **Markdown Headers**: Use ATX-style (`#`, `##`, `###`).
- **Code Blocks**: Always include explicit language identifier tags.

## Anti-Patterns

- Trailing whitespace at end of lines.
- Unlabeled code blocks (``` without language tag).

## Verification Checklist

- [ ] Are all code fences labeled with a language tag?
- [ ] Is trailing whitespace eliminated?
