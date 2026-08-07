# Software Architecture Standards
<!-- Module ID: modules.domains.engineering.architecture | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines architectural standards including layered separation of concerns, inward-only dependencies, and Architectural Decision Records (ADRs).

## Standards

- **Layered Architecture**: Systems MUST separate Presentation, Application, Domain, and Infrastructure concerns.
- **Inward Dependencies**: High-level policies MUST NOT depend on low-level details.
- **ADR Obligation**: Major architectural changes MUST be documented via ADR.

## Anti-Patterns

- **Big Ball of Mud**: Tightly coupled, unlayered spaghetti code.
- **Circular Package Imports**: Package A imports B, B imports A.

## Verification Checklist

- [ ] Are dependencies pointing strictly inward toward core domains?
- [ ] Is an ADR created for new architectural decisions?
