# Quality Engine Specification
<!-- Token budget: ~650 tokens | Version: 1.0.0 | Classification: Layer 0 Kernel Engine -->

The Quality Engine is a Layer 0 Kernel Subsystem that enforces multi-stage,
independent quality reviews before artifact delivery. It replaces subjective
"self-review" with deterministic pass/fail checklists across 8 engineering dimensions.

---

## 1. The 8 Independent Review Gates

```
[Candidate Output] ──▶ [Quality Engine Matrix] ──┬──▶ Gate 1: Architecture Review
                                                 ├──▶ Gate 2: Security Review
                                                 ├──▶ Gate 3: Performance Review
                                                 ├──▶ Gate 4: Maintainability Review
                                                 ├──▶ Gate 5: Readability Review
                                                 ├──▶ Gate 6: Testing Review
                                                 ├──▶ Gate 7: Documentation Review
                                                 └──▶ Gate 8: Consistency Review
```

| # | Review Gate | Scope | Deterministic Check | Threshold |
|:--|:------------|:------|:--------------------|:----------|
| 1 | `Architecture` | Modular boundaries, dependency direction | Zero inward-pointing dependency violations | Pass / Fail |
| 2 | `Security` | OWASP vulnerabilities, secret leaks, input validation | Zero unvalidated user inputs or exposed secrets | Pass / Fail |
| 3 | `Performance` | Algorithmic complexity, unnecessary I/O or loops | Zero $O(N^2)+$ loops on unbounded datasets | Pass / Fail |
| 4 | `Maintainability` | Coupling, cohesion, single responsibility | Zero functions exceeding 50 lines / classes over 300 | Pass / Fail |
| 5 | `Readability` | Naming clarity, explicit control flow | Zero magic numbers or misleading variable names | Pass / Fail |
| 6 | `Testing` | Coverage of edge cases and error branches | 100% error-handling path coverage | Pass / Fail |
| 7 | `Documentation` | Completeness of public API docstrings/spec | 100% public interfaces documented | Pass / Fail |
| 8 | `Consistency` | Adherence to project naming/formatting conventions | Zero lint or formatting rule violations | Pass / Fail |

---

## 2. Gate Execution & Enforcement

- **Rule Q-01 (All-or-Nothing Pass)**: All 8 gates MUST evaluate to `PASS` before delivery. A single `FAIL` halts release.
- **Rule Q-02 (Deterministic Over Intuitive)**: Reviewers MUST use explicit binary criteria. Subjective feedback ("looks fine") is prohibited.
- **Rule Q-03 (Automated Pre-Gate)**: Linters and automated test suites MUST be executed prior to semantic review gates.

---

## 3. Kernel Integration (Truth & Reasoning Binding)

- **Truth Engine Binding**: `Security` and `Architecture` gates MUST verify that underlying claims are in `VERIFIED_FACT` state.
- **Reasoning Engine Binding**: `Maintainability` gate MUST verify that reasoning confidence score was $\ge 0.70$.

---

## 4. Machine Query Interface

```json
{
  "contract": "core.contracts.quality_engine",
  "version": "1.0.0",
  "queries": {
    "evaluate_artifact": "Evaluates candidate against 8 gates, returns QualityReportObject",
    "get_gate_status": "Returns Enum<PASS, FAIL> for specified gate_id"
  }
}
```

---

## 5. Evaluation

### Metrics & Acceptance Criteria

| Metric | Target | Acceptance Threshold |
|:-------|:-------|:---------------------|
| Gate Pass Accuracy | % of delivered code passing all 8 gates | **100%** |
| Deterministic Check Coverage | Binary rules per gate | **≥ 5 rules / gate** |

---

## 6. Verification Checklist

- [ ] Have all 8 review gates evaluated to `PASS`?
- [ ] Are automated linters/tests passing prior to semantic review?
- [ ] Are zero secrets, unvalidated inputs, or $O(N^2)$ loops present?
- [ ] Is public API documentation 100% complete?
