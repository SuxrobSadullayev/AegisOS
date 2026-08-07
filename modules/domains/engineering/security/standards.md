# Security Standards
<!-- Module ID: modules.domains.engineering.security | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines secure coding practices, threat modeling, and OWASP Top 10 mitigation guidelines.

## Standards

- **Input Validation**: All external input MUST be validated at trust boundaries.
- **Secret Management**: Zero hardcoded secrets, API keys, or credentials in source code.
- **Least Privilege**: Components MUST operate with the minimum required permissions.

## Anti-Patterns

- **Hardcoded Credentials**: Storing passwords or private keys in source files or git history.
- **SQL / Command Injection**: Concatenating raw user strings into SQL queries or shell executions.

## Verification Checklist

- [ ] Are all inputs validated and sanitized before processing?
- [ ] Are secrets loaded exclusively from environment variables or key vaults?
