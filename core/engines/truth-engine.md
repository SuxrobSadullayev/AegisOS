# Truth Engine Specification
<!-- Token budget: ~880 tokens | Version: 1.1.0 | Classification: Layer 0 Kernel Engine -->

The Truth Engine is a Layer 0 Kernel Subsystem responsible for tracking internal
claim states, managing claim dependency graphs (DAG), enforcing evidence lifecycle
transitions, and eliminating hallucinations through deterministic verification rules.

---

## 1. Decoupled Architecture

The Truth Engine operates exclusively within the Kernel Epistemic Registry.
It separates internal machine-readable claim tracking from user-facing presentation.

```
┌─────────────────────────────────────────────────────────────┐
│ Kernel Epistemic Registry (Internal Claim Graph DAG)        │
│ Claim States: UNKNOWN | HYPOTHESIS | INFERENCE | VERIFIED   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Machine-Readable API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Adapter Presentation Layer                                  │
│ Converts internal state to target format (Silent/Annotated) │
└──────────────────────────────┴──────────────────────────────┘
```

- **Internal Epistemic State**: In-memory Directed Acyclic Graph (DAG) using immutable `ClaimID`s.
- **External Presentation**: Clean prose by default. Epistemic annotations (`[CLM-XXXXXX]`) are rendered only in debug modes.

---

## 2. Claim Identity & Dependency Graph (DAG)

### Claim Identity Schema
Every claim receives an immutable, globally unique ID: `CLM-<SEQ_6>` (e.g., `CLM-000042`).

```json
{
  "claim_id": "CLM-000042",
  "statement": "PostgreSQL connection pool size exceeding 20 causes latency spikes",
  "state": "INFERENCE",
  "evidence_refs": ["EVD-000104"],
  "depends_on_claim_ids": ["CLM-000012"]
}
```

### Cascade Invalidation Algorithm
Claims are linked in a Directed Acyclic Graph ($G = (V, E)$).

- **Rule C-01 (Cascade Propagation)**: If an upstream claim $C_u$ transitions to `INVALIDATED` or `SUSPECT`, all descendant claims $C_d$ depending on $C_u$ transition to `SUSPECT` automatically.
- **Rule C-02 (Cycle Prohibition)**: Circular dependency insertion ($C_A \to C_B \to C_A$) is strictly prohibited during graph edge creation.

---

## 3. Epistemic State Machine

Claims progress through a deterministic state machine:

```
UNKNOWN ──(Level 1+)──▶ HYPOTHESIS ──(Level 2+)──▶ INFERENCE ──(Level 3+)──▶ VERIFIED_FACT
   │                       │                          │                         │
   └───────────────────────┴───────────┬──────────────┴─────────────────────────┘
                                       │ Counter-Evidence / Expired Evidence
                                       ▼
                                  INVALIDATED / SUSPECT
```

### Transition Invariants

- **T-01 (Sequential Promotion)**: `HYPOTHESIS` → `INFERENCE` requires Level 2+ evidence. `INFERENCE` → `VERIFIED_FACT` requires Level 3+ evidence.
- **T-02 (Direct Verification Guard)**: `HYPOTHESIS` → `VERIFIED_FACT` is forbidden without Level 4 or Level 5 evidence.
- **T-03 (Immediate Demotion)**: Any claim MUST transition to `INVALIDATED` when counter-evidence with Level ≥ current evidence level is introduced.
- **T-04 (Terminal Invalidation)**: `INVALIDATED` claims cannot be re-promoted. A new claim ID must be instantiated.

---

## 4. Evidence Hierarchy & Lifecycle

### Evidence Hierarchy (Levels 0–5)

| Level | Identifier | Source | Verification Capacity | Minimum State Target |
|:------|:-----------|:-------|:----------------------|:---------------------|
| **5** | `EXECUTION` | Direct CLI / Test / Tool Execution | 100% Deterministic | `VERIFIED_FACT` |
| **4** | `SPECIFICATION` | Official Language Spec / RFC / Doc | High Precision | `VERIFIED_FACT` |
| **3** | `CODE_INSPECTION` | Workspace Codebase / AST / Config | High Precision | `VERIFIED_FACT` |
| **2** | `DEDUCTION` | Deductive chain from Level 3+ facts | Mathematical Logic | `INFERENCE` |
| **1** | `PARAMETRIC` | LLM Parametric Memory | Probabilistic | `HYPOTHESIS` |
| **0** | `UNSUBSTANTIATED` | User Assertion / Speculative Prompt | Speculative | `UNKNOWN` |

### Evidence Lifecycle States

Evidence states trigger automatic claim re-evaluation:

- `ACTIVE`: Valid evidence. Claim retains current state.
- `EXPIRED`: File modified or session TTL elapsed. Claim demoted to `HYPOTHESIS`.
- `SUPERSEDED`: Higher-level evidence introduced. Claim re-evaluated.
- `CONTRADICTED`: Counter-evidence found. Claim transitions immediately to `INVALIDATED`.
- `DEPRECATED`: Underlying spec outdated. Claim transitions to `SUSPECT`.
- `UNAVAILABLE`: Resource or tool missing. Claim demoted to `HYPOTHESIS`.

---

## 5. Runtime Query Interface

Machine-readable JSON interface for runtime components:

```json
{
  "contract": "core.contracts.truth_engine",
  "version": "1.1.0",
  "queries": {
    "get_unverified_hypotheses": "Returns Array<Claim> where state == 'HYPOTHESIS'",
    "get_weak_assumptions": "Returns Array<Claim> where state == 'INFERENCE' and evidence_level < 3",
    "get_claim_dependents": "Returns Array<Claim> where depends_on_claim_ids includes target_id",
    "validate_claim_chain": "Returns boolean indicating whether all prerequisite claims are VERIFIED_FACT"
  }
}
```

---

## 6. Evaluation

### Success Criteria
- Zero claims promoted to `VERIFIED_FACT` without Level 3+ evidence.
- 100% cascade invalidation across DAG when upstream claims are invalidated.
- Zero presentation label pollution in standard adapter outputs.

### Metrics & Acceptance Criteria
| Metric | Target | Acceptance Threshold |
|:-------|:-------|:---------------------|
| Unsubstantiated Promotion Rate | 0.0 | **0.0 (Zero Tolerance)** |
| DAG Invalidation Cascade Accuracy | % of dependent claims updated | **100%** |
| Runtime Query Latency | Milliseconds to resolve claim graph | **< 5ms** |

---

## 7. Verification Checklist

- [ ] Does every claim possess an immutable `ClaimID` (`CLM-XXXXXX`)?
- [ ] Are claims linked via Directed Acyclic Graph (DAG) without cycles?
- [ ] Does upstream claim invalidation trigger automatic downstream cascade?
- [ ] Does evidence `EXPIRED`/`UNAVAILABLE` status demote claims to `HYPOTHESIS`?
- [ ] Are internal claim states decoupled from user-facing presentation?
