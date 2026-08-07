# Aegis Module Contract
<!-- Token budget: ~220 | Version: 1.0.0 | Tier 1 Core Contract -->

Mandatory interface schema for all Tier 2 Domain Modules (`modules/domains/`),
Standards (`modules/standards/`), and Workflows (`modules/workflows/`).

## Required Structure

Modules MUST declare header metadata and include all 6 sections:

```markdown
# [Module Name]
<!-- Module ID: domain.category.name | Version: X.Y.Z | Token Budget: ~XXXX -->
## Purpose
## Standards
## Anti-Patterns
## Verification Checklist
## Examples
## Evaluation
### Success Criteria
### Failure Modes
### Metrics & Acceptance Criteria
```

## Compliance Invariants

- **M-01 (Self-Containment)**: Operate independently without hard cross-module dependencies.
- **M-02 (Token Budget)**: Declare budget (Target: < 3,000 tokens for Tier 2 modules).
- **M-03 (Objective Evaluation)**: Specify binary metrics and acceptance criteria.
- **M-04 (Factuality)**: Claims MUST comply with Truth Engine evidence levels.

## Verification Checklist

- [ ] Contains all 6 required ATX headers?
- [ ] Token budget declared and under 3,000 tokens?
- [ ] Evaluation metrics objective and binary?
