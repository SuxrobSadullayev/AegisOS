# Versioning Standards
<!-- Module ID: modules.standards.versioning | Version: 1.0.0 | Token Budget: ~400 -->

## Purpose

Defines Semantic Versioning (SemVer 2.0.0) rules for Aegis components and managed projects.

## Standards

- **MAJOR**: Incompatible API or structural breaking changes.
- **MINOR**: Backward-compatible new functionality or modules.
- **PATCH**: Backward-compatible bug fixes or minor refactoring.

## Anti-Patterns

- Breaking public interfaces in MINOR or PATCH releases.
- Unpinned or ambiguous dependency ranges.

## Verification Checklist

- [ ] Does breaking contract change trigger a MAJOR version bump?
- [ ] Is version number updated in header comments and CHANGELOG.md?
