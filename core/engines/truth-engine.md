# Truth Engine Specification
<!-- Token budget: ~850 tokens | Version: 1.0.0 | Tier 1 Core Engine -->

The Truth Engine is Layer 0 Kernel Subsystem responsible for tracking epistemic
claim states, enforcing evidence thresholds, and eliminating hallucinations
through deterministic state transitions.

---

## 1. System Architecture & Decoupling

The Truth Engine operates strictly inside the Kernel Epistemic Registry.
It decouples internal claim tracking from external user presentation.

```
┌─────────────────────────────────────────────────────────────┐
│ Kernel Epistemic Registry (Internal Claim Graph)            │
│ Claim States: UNKNOWN | HYPOTHESIS | INFERENCE | VERIFIED   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Machine-Readable API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Adapter Presentation Layer                                  │
│ Converts internal state to target format (Silent/Annotated) │
└─────────────────────────────────────────────────────────────┘
```

- **Internal Epistemic State**: Maintained as an in-memory dependency graph.
- **External Presentation**: Adapters render clean prose by default. Debug
  annotations are applied only when explicitly configured by runtime.

---

## 2. Epistemic State Machine

Claims progress through a deterministic state machine based on evidence strength:

```
UNKNOWN ──(Level 1+)──▶ HYPOTHESIS ──(Level 2+)──▶ INFERENCE ──(Level 3+)──▶ VERIFIED_FACT
   │                       │                          │                         │
   └───────────────────────┴───────────┬──────────────┴─────────────────────────┘
                                       │ Counter-Evidence
                                       ▼
                                  INVALIDATED
```

### State Definitions

- `UNKNOWN`: Unassessed or unverified claim.
- `HYPOTHESIS`: Speculative assertion requiring empirical or deductive proof.
- `INFERENCE`: Logical deduction derived from established facts.
- `VERIFIED_FACT`: Indisputable claim backed by static code, docs, or execution.
- `INVALIDATED`: Refuted claim discredited by counter-evidence.

### State Transition Invariants

- **T-01 (Sequential Promotion)**: `HYPOTHESIS` → `INFERENCE` requires Level 2+ evidence. `INFERENCE` → `VERIFIED_FACT` requires Level 3+ evidence.
- **T-02 (Direct Verification Guard)**: `HYPOTHESIS` → `VERIFIED_FACT` is forbidden without Level 4 or Level 5 evidence.
- **T-03 (Immediate Demotion)**: Any claim MUST transition to `INVALIDATED` when counter-evidence with Level ≥ current evidence level is introduced.
- **T-04 (Terminal Invalidation)**: `INVALIDATED` claims cannot be re-promoted. A new claim ID must be instantiated.

---

## 3. Evidence Hierarchy Model

Evidence is categorized into 6 deterministic strength levels:

| Level | Identifier | Source | Verification Capacity | Minimum State Target |
|:------|:-----------|:-------|:----------------------|:---------------------|
| **5** | `EXECUTION` | Direct CLI / Test / Tool Execution | 100% Deterministic | `VERIFIED_FACT` |
| **4** | `SPECIFICATION` | Official Language Spec / RFC / Doc | High Precision | `VERIFIED_FACT` |
| **3** | `CODE_INSPECTION` | Workspace Codebase / AST / Config | High Precision | `VERIFIED_FACT` |
| **2** | `DEDUCTION` | Deductive chain from Level 3+ facts | Mathematical Logic | `INFERENCE` |
| **1** | `PARAMETRIC` | LLM Parametric Memory | Probabilistic | `HYPOTHESIS` |
| **0** | `UNSUBSTANTIATED` | User Assertion / Speculative Prompt | Speculative | `UNKNOWN` |

### Minimum Evidence Thresholds

- `HYPOTHESIS`: Requires minimum Level 1 evidence.
- `INFERENCE`: Requires minimum Level 2 evidence derived from Level 3+ facts.
- `VERIFIED_FACT`: Requires minimum Level 3 (Code), Level 4 (Doc), or Level 5 (Tool Execution).

---

## 4. Runtime Query Interface

The Truth Engine exposes a machine-readable JSON API for runtime evaluation:

```json
{
  "contract": "core.contracts.truth_engine",
  "queries": {
    "get_unverified_hypotheses": "Returns Array<Claim> where state == 'HYPOTHESIS'",
    "get_weak_assumptions": "Returns Array<Claim> where state == 'INFERENCE' and evidence_level < 3",
    "validate_claim_chain": "Returns boolean indicating whether all prerequisite claims are VERIFIED_FACT"
  }
}
```

---

## 5. Evaluation

### Success Criteria

- Zero claims promoted to `VERIFIED_FACT` without Level 3+ evidence.
- 100% of invalidated claims immediately isolated from reasoning chains.
- Zero presentation label pollution in standard adapter outputs.

### Failure Modes

- **Silent Fabrication**: Promoting Level 1 memory claims directly to `VERIFIED_FACT`.
- **State Deadlock**: Hypotheses locked without empirical verification pathways.
- **Stale Evidence**: Retaining Level 3 `VERIFIED_FACT` status after underlying workspace files change.

### Metrics & Acceptance Criteria

| Metric | Target | Acceptance Threshold |
|:-------|:-------|:---------------------|
| Unsubstantiated Promotion Rate | 0.0 | **0.0 (Zero Tolerance)** |
| Epistemic Graph Integrity | % of valid state transitions | **100%** |
| Runtime Query Latency | Milliseconds to resolve claim graph | **< 5ms** |

### Regression Risks

- Over-caution: Refusing to produce inferences when Level 3 code evidence is available.
- Mitigation: Resolvers must auto-trigger static inspection tools when Level 1 claims arise.

---

## 6. Verification Checklist

- [ ] Are internal claim states decoupled from user-facing presentation?
- [ ] Is every `VERIFIED_FACT` backed by Level 3, 4, or 5 evidence?
- [ ] Are direct `HYPOTHESIS` → `VERIFIED_FACT` transitions guarded by Level 4/5 proof?
- [ ] Does counter-evidence immediately trigger `INVALIDATED` state?
- [ ] Are runtime query interfaces JSON-Schema compliant?
