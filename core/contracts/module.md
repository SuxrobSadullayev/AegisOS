# Aegis Module Contract Specification
<!-- Token budget: ~450 tokens | Version: 1.0.0 | Classification: Layer 0 Core Contract -->

The Module Contract defines the mandatory interface, structural schema, and compliance
rules for all Tier 2 Domain Modules (`modules/domains/`), Standards (`modules/standards/`),
and Workflows (`modules/workflows/`).

---

## 1. Required Metadata & Structure

Every module MUST declare metadata in its header HTML comment and include all 6 required sections:

```markdown
# [Module Name]
<!-- Module ID: domain.category.name | Version: X.Y.Z | Token Budget: ~XXXX -->

## Purpose
One paragraph explaining what this module does and why it exists.

## Standards
Engineering standards, patterns, or protocols.

## Anti-Patterns
Pitfalls to avoid, root causes, and recommended alternatives.

## Verification Checklist
Deterministic binary (pass/fail) items for automated checking.

## Examples
Realistic, concrete examples (no trivial foo/bar snippets).

## Evaluation
### Success Criteria
### Failure Modes
### Metrics & Acceptance Criteria
```

---

## 2. Compliance Invariants

- **M-01 (Self-Containment)**: Every module MUST operate independently without hard dependencies on other domain modules.
- **M-02 (Token Budget Declaration)**: Modules MUST declare token budget (Target: < 3,000 tokens for Tier 2 modules).
- **M-03 (Objective Evaluation)**: Every module MUST specify binary metrics and acceptance criteria.
- **M-04 (Factuality)**: Technical claims MUST comply with Truth Engine evidence levels.

---

## 3. Verification Checklist

- [ ] Does the module contain all 6 required ATX headers?
- [ ] Is token budget declared and under 3,000 tokens?
- [ ] Are evaluation metrics objective and binary?
- [ ] Are examples concrete and non-trivial?
