# Universal Engineering Workflow Specification
<!-- Token budget: ~550 tokens | Version: 1.0.0 | Classification: Layer 0 Core Workflow -->

The Workflow Engine defines the mandatory 10-step sequence for all software engineering
tasks performed by agents under Aegis. It integrates the Constitution, Truth Engine,
Reasoning Engine, and Quality Engine into an uninterrupted execution pipeline.

---

## 1. The 10-Step Execution Pipeline

```
Understand ──▶ Analyze ──▶ Plan ──▶ Identify Risks ──▶ Implement
                                                          │
Deliver ◀── Self-Critique ◀── Test ◀── Optimize ◀── Review ┘
```

| Step | Phase Name | Primary Responsibility | Mandatory Binding |
|:-----|:-----------|:-----------------------|:------------------|
| **1** | `Understand` | Parse user requirements, identify constraints and ambiguities | `Reasoning.L1` |
| **2** | `Analyze` | Perform problem decomposition and gather codebase context | `Truth.Level_3+` |
| **3** | `Plan` | Formulate step-by-step implementation plan with milestones | `Reasoning.Plan` |
| **4** | `Identify Risks` | Conduct threat modeling, performance risk, and regression analysis | `Reasoning.Risk` |
| **5** | `Implement` | Execute code modifications adhering to language/domain standards | `Constitution.C01-C07` |
| **6** | `Review` | Conduct multi-dimensional code review across 8 gates | `Quality.Gates_1-8` |
| **7** | `Optimize` | Profile and refactor allocations, complexity, or readability bottlenecks | `Quality.Perf_Gate` |
| **8** | `Test` | Run unit, integration, and edge-case regression tests | `Quality.Test_Gate` |
| **9** | `Self-Critique` | Perform final verification checklist audit | `Quality.All_Pass` |
| **10** | `Deliver` | Output final artifact with summary, test results, and diffs | `Workflow.Complete` |

---

## 2. Phase Transition Invariants

- **W-01 (No Step Skipping)**: Steps 1 through 4 MUST execute prior to Step 5 (`Implement`). Jumping directly to implementation is prohibited.
- **W-02 (Quality Gate Blocking)**: Step 10 (`Deliver`) MUST NOT execute unless Step 9 (`Self-Critique`) verifies 100% PASS across all Quality Engine gates.
- **W-03 (Re-Analysis Trigger)**: If Step 8 (`Test`) fails, execution MUST loop back to Step 2 (`Analyze`) or Step 3 (`Plan`).

---

## 3. Evaluation & Verification Checklist

- [ ] Have Steps 1–4 executed prior to code modification?
- [ ] Are all 8 Quality Engine review gates PASS before Step 10 delivery?
- [ ] Did any test failure trigger re-analysis rather than silent patch work?
