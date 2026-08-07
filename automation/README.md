# Automation — Build, Lint, Test, and CI Scripts

## Purpose

The `automation/` directory contains **shell scripts and CI configurations** for
building, validating, and testing the Aegis framework itself.

## Design Goals

- Validate all Markdown files conform to the module standard.
- Test adapter output for correctness and format compliance.
- Provide CI integration for automated quality assurance.
- Keep all automation in POSIX-compliant shell scripts.

## Contents

| File/Directory | Purpose | Status |
|:---------------|:--------|:-------|
| `lint.sh` | Validates Markdown structure (required sections, formatting) | Planned |
| `test.sh` | Runs framework tests (adapter output, token counts) | Planned |
| `build.sh` | Assembles modules into agent configurations | Planned |
| `ci/` | CI pipeline configurations | Planned |

## Usage

```bash
# Validate all module structure
./automation/lint.sh

# Run framework tests
./automation/test.sh

# Build agent configurations
./automation/build.sh --agent claude --modules python,testing
```

## Future Improvements

- Pre-commit hooks for local validation.
- GitHub Actions workflow for automated CI.
- Token counting validation in lint step.
- Broken link detection across all Markdown files.
