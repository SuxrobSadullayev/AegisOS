# Knowledge — Persistent Knowledge Base

## Purpose

The `knowledge/` directory contains a **persistent, curated knowledge base** of
engineering wisdom. Unlike modules (which define standards), knowledge files
capture lessons learned, case studies, and real-world patterns from practice.

## Design Goals

- Accumulate engineering wisdom over time.
- Provide concrete, experience-based guidance beyond theoretical standards.
- Make knowledge searchable and categorized.
- Enable agents to learn from past decisions.

## Contents

| Directory | Purpose | Status |
|:----------|:--------|:-------|
| `best-practices/` | Proven engineering practices across domains | Planned |
| `anti-patterns/` | Common mistakes with root cause analysis | Planned |
| `case-studies/` | Real-world examples of engineering decisions | Planned |
| `lessons-learned/` | Post-mortem insights and retrospective knowledge | Planned |

## Usage

Knowledge files are referenced on demand. Agents can search the knowledge base
when encountering unfamiliar patterns or when a decision requires historical
context.

## Future Improvements

- Tagging system for cross-referencing knowledge entries.
- Automatic knowledge extraction from code review sessions.
- Community-contributed case studies.
- RAG integration for semantic knowledge retrieval.
