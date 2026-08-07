# Python Engineering Standards
<!-- Module ID: modules.domains.languages.python | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines Python-specific engineering standards, PEP 8 idioms, typing, and safety practices.

## Standards

- **Type Hints**: Public functions and methods MUST include explicit type annotations (PEP 484).
- **PEP 8 Compliance**: Code MUST comply with PEP 8 formatting (Black / Ruff).
- **Virtual Environments**: Dependencies MUST be managed via `pyproject.toml` and lockfiles.

## Anti-Patterns

- **Mutable Default Arguments**: `def foo(data=[])`.
- **Bare Except**: `except:` catching `BaseException` silently.

## Verification Checklist

- [ ] Are type annotations present on public functions?
- [ ] Are default arguments immutable (`None`)?
