# Testing Standards
<!-- Module ID: modules.domains.engineering.testing | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines test strategy, test pyramid (Unit → Integration → E2E), and test quality guidelines.

## Standards

- **Test Pyramid**: Emphasize fast, deterministic unit tests over slow E2E tests.
- **Independence**: Tests MUST NOT depend on execution order or shared state.
- **Edge Cases**: Unit test suites MUST explicitly cover boundary conditions and error paths.

## Anti-Patterns

- **Flaky Tests**: Tests relying on non-deterministic sleeps or network calls.
- **Test Logic Duplication**: Re-implementing complex business logic in test assertions.

## Verification Checklist

- [ ] Are unit tests isolated and independent?
- [ ] Are error paths and edge cases covered?
