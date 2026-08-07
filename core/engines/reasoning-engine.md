# Reasoning Engine Specification
<!-- Token budget: ~900 tokens | Version: 1.0.0 | Classification: Layer 0 Kernel Engine -->

The Reasoning Engine is a Layer 0 Kernel Subsystem that enforces structured, multi-stage
analytical reasoning before code generation. It prevents "code first" anti-patterns
by requiring explicit problem decomposition, trade-off analysis, and risk assessment.

---

## 1. Core Capabilities (9 Reasoning Primitives)

The engine structures cognitive processing into 9 deterministic capabilities:

| # | Capability | Definition | Input / Output |
|:--|:-----------|:-----------|:---------------|
| 1 | `Decomposition` | Break complex tasks into atomic, non-overlapping sub-problems | Task → Sub-tasks |
| 2 | `Planning` | Order execution steps with clear dependency constraints | Sub-tasks → Step Sequence |
| 3 | `TradeOffAnalysis` | Evaluate pros/cons of competing engineering approaches | Approaches → Trade-off Matrix |
| 4 | `RiskAnalysis` | Identify failure modes, security flaws, and regression risks | Solution → Risk Mitigation Table |
| 5 | `Alternatives` | Formulate at least 2 non-trivial alternative solutions | Problem → Alternative Array |
| 6 | `DecisionCriteria` | Establish objective binary metrics for solution selection | Alternatives → Selected Solution |
| 7 | `EvidenceGathering` | Query Truth Engine for claim IDs and verification levels | Claims → Verified Claims |
| 8 | `ConfidenceEstimation` | Estimate certainty score (0.0 to 1.0) based on evidence strength | Evidence → Confidence Metric |
| 9 | `SelfVerification` | Critique proposed solution against deterministic quality rules | Plan → Verification Result |

---

## 2. Reasoning Depth Levels (L1 / L2 / L3)

To optimize token usage, the engine adjusts analytical depth based on task complexity:

```
[Task Context] ──▶ [Depth Selector] ──┬──▶ L1 (Fast/Trivial)       : Steps 1, 2, 9
                                     ├──▶ L2 (Standard)           : Steps 1-4, 7-9
                                     └──▶ L3 (Deep Architecture)  : Steps 1-9 (Full)
```

- **L1 (Fast)**: Typo fixes, minor renames, trivial doc updates.
- **L2 (Standard)**: Standard feature implementation, localized bug fixes, component refactoring.
- **L3 (Deep)**: Architectural decisions, database migrations, security-critical changes, new system designs.

---

## 3. Epistemic Integration (Truth Engine Binding)

The Reasoning Engine binds directly to the Truth Engine (`core.engines.truth_engine`):

- **Rule R-01 (Claim Binding)**: Every assumption in `TradeOffAnalysis` or `RiskAnalysis` MUST reference a valid `ClaimID` (`CLM-XXXXXX`).
- **Rule R-02 (Low Confidence Gate)**: If `ConfidenceEstimation` is < 0.70, implementation MUST NOT begin. The engine must trigger explicit evidence gathering or ask for user clarification.

---

## 4. Machine Query Interface

```json
{
  "contract": "core.contracts.reasoning_engine",
  "version": "1.0.0",
  "queries": {
    "get_reasoning_trace": "Returns Array<ReasoningStep>",
    "get_confidence_score": "Returns float (0.0 to 1.0)",
    "validate_depth_level": "Returns boolean indicating compliance with target depth (L1/L2/L3)"
  }
}
```

---

## 5. Evaluation

### Success Criteria
- 100% of non-trivial tasks execute explicit analysis before implementation.
- Zero implementations proceed when confidence score is < 0.70.
- All architectural assumptions bound to Truth Engine `ClaimID`s.

### Metrics & Acceptance Criteria
| Metric | Target | Threshold |
|:-------|:-------|:----------|
| Pre-implementation Reasoning Compliance | 100% | **100%** |
| Claim Binding Rate (L2/L3) | % assumptions linked to `CLM-XXXXXX` | **≥ 90%** |
| Confidence Gate Enforcement | Zero leaks under 0.70 confidence | **100%** |

---

## 6. Verification Checklist

- [ ] Was the appropriate reasoning depth (L1/L2/L3) selected?
- [ ] Were non-trivial assumptions linked to Truth Engine `ClaimID`s?
- [ ] Did confidence score meet the minimum 0.70 threshold?
- [ ] Were trade-offs and risks explicitly documented for L2/L3 tasks?
