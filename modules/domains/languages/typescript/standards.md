# TypeScript Engineering Standards
<!-- Module ID: modules.domains.languages.typescript | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines TypeScript-specific type safety, strict mode, and async programming standards.

## Standards

- **Strict Mode**: `tsconfig.json` MUST enable `strict: true` and `noImplicitAny: true`.
- **Explicit Returns**: Exported functions MUST declare return types explicitly.
- **Async/Await**: Prefer `async/await` over raw promise chaining (`.then()`).

## Anti-Patterns

- **Any Escape Hatch**: Using `any` type to bypass type checking.
- **Unhandled Rejections**: Async calls without `try/catch` or error handling.

## Verification Checklist

- [ ] Is strict mode enabled?
- [ ] Are explicit return types declared on exported functions?
