# Contributing to Aegis AI Framework

Thank you for your interest in contributing to Aegis! This document provides
guidelines and standards for contributions.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Module Standards](#module-standards)
- [Writing Guidelines](#writing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Quality Checklist](#quality-checklist)

---

## Code of Conduct

- Be respectful and constructive in all interactions.
- Prioritize correctness over speed.
- Never fabricate technical information.
- Welcome feedback and iterate gracefully.

---

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates.
2. Use a clear, descriptive title.
3. Provide context: which module, what behavior was expected, what happened.
4. Include your agent/tool version if relevant.

### Suggesting Improvements

1. Open an issue with the `[Enhancement]` prefix.
2. Describe the problem the improvement solves.
3. Propose a specific solution, not just the problem.
4. Reference existing modules or patterns where applicable.

### Adding or Modifying Modules

1. Fork the repository.
2. Create a feature branch: `git checkout -b module/module-name`.
3. Follow the [Module Standards](#module-standards) below.
4. Submit a pull request with a clear description.

---

## Module Standards

Every module **must** follow this internal structure:

```markdown
# Module Name

## Purpose
One paragraph explaining what this module does and why it exists.

## Design Goals
- Bullet list of specific engineering goals this module achieves.

## Standards
The actual engineering standards, patterns, or protocols.

## Anti-Patterns
What to avoid and why. Each anti-pattern should include:
- Name
- Why it is harmful
- What to do instead

## Examples
Concrete, realistic examples demonstrating correct usage.
Examples must be:
- Complete (runnable or clearly illustrative)
- Realistic (not trivial "foo/bar" examples)
- Annotated (explain why the example is correct)

## Checklist
Quick-reference checklist for the module's domain.

## Future Improvements
Planned enhancements with brief rationale.
```

### Required Properties

| Property | Requirement |
|:---------|:------------|
| Self-contained | Module must work independently without requiring other modules |
| Token-conscious | Tier 2 modules should target < 3,000 tokens |
| Factually accurate | Every claim must be verifiable; mark uncertainties explicitly |
| Agent-agnostic | No agent-specific syntax or assumptions |

---

## Writing Guidelines

### Tone

- Professional but approachable.
- Assertive when stating standards ("Use X", not "You might want to consider X").
- Humble when uncertain ("This may vary depending on..." rather than false certainty).

### Formatting

- Use ATX-style headers (`#`, `##`, `###`).
- Use tables for structured comparisons.
- Use code blocks with language identifiers for all code examples.
- Use bullet lists for enumerated items.
- Keep lines under 100 characters where practical.

### Technical Accuracy

- Never invent APIs, library names, or version numbers.
- Cite sources for non-obvious claims.
- Mark inference with "likely", "typically", or "in most cases".
- Mark hypothesis with "hypothesis:", "possibly", or "it may be that".
- Mark unknowns explicitly: "This has not been verified."

---

## Pull Request Process

1. **Ensure all checks pass**: Run `./automation/lint.sh` before submitting.
2. **One module per PR**: Keep changes focused and reviewable.
3. **Write a clear PR description**:
   - What module is being added/changed
   - Why the change is needed
   - What was tested
4. **Self-review against the quality checklist** below before requesting review.
5. **Address all review feedback** before merging.

---

## Quality Checklist

Before submitting, verify your contribution against these 10 dimensions:

- [ ] **Correctness** — Are all technical claims accurate and verifiable?
- [ ] **Consistency** — Does it follow the module structure and writing style?
- [ ] **Completeness** — Are all required sections present?
- [ ] **Maintainability** — Can another contributor easily update this?
- [ ] **Security** — Does it promote secure practices? No dangerous examples?
- [ ] **Performance** — Is it within token budget targets?
- [ ] **Readability** — Is it clear without excessive explanation?
- [ ] **Reusability** — Can this be used across different projects?
- [ ] **Modularity** — Does it avoid unnecessary coupling to other modules?
- [ ] **Scalability** — Will this structure work as the framework grows?

---

## Questions?

If you are unsure about anything, open an issue with the `[Question]` prefix.
We would rather answer questions early than review incorrect implementations.
