# Naming Standards
<!-- Module ID: modules.standards.naming | Version: 1.0.0 | Token Budget: ~400 -->

## Purpose

Defines cross-cutting naming conventions for variables, functions, classes, files, and directories.

## Standards

- **Files & Directories**: Use `kebab-case` (e.g., `truth-engine.md`, `quality-engine.md`).
- **Variables & Functions**: Use language-idiomatic casing (`snake_case` in Python/Rust, `camelCase` in TS/C++).
- **Types & Classes**: Use `PascalCase` across all languages.
- **Constants**: Use `UPPER_SNAKE_CASE`.

## Anti-Patterns

- Single-letter variable names outside trivial loops (`x`, `tmp`, `data`).
- Hungarian notation prefixes (`strName`, `iCount`).

## Verification Checklist

- [ ] Are file names strictly `kebab-case`?
- [ ] Are variable names descriptive and non-cryptic?
