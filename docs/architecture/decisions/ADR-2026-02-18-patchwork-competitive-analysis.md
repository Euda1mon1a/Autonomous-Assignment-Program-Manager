# ADR: Patchwork Competitive Analysis

**Date:** 2026-02-18
**Status:** REFERENCE
**Context:** Patchwork (NHS) launched an AI-driven roster builder solving the same hard/soft constraint scheduling problem as AAPM.

---

## Context

Patchwork is an enterprise workforce management platform serving the NHS. They recently rolled out an AI-powered preference-based rostering tool that automatically generates clinician schedules respecting individual shift preferences and staffing requirements. This is the same core problem AAPM solves for military medical residency scheduling.

## Patchwork's Approach

| Feature | Patchwork | Notes |
|---------|-----------|-------|
| **Constraint types** | Hard (compliance, minimum staffing) + soft (clinician preferences) | Claims ~98% negative preference satisfaction |
| **Self-rostering** | Clinicians input preferences directly | Residents see how schedules align with their inputs |
| **Transparency** | Shows impact of different preference levels | Constraint transparency layer |
| **Workflow** | Leave requests, shift swaps, exception reporting | Audit trail for deviations |
| **Target** | NHS (large hospital networks) | Enterprise SaaS |

## How AAPM Compares

### Where AAPM is ahead

| Capability | AAPM | Patchwork |
|-----------|------|-----------|
| **Constraint formalism** | Formal constraint classes with typed parameters | Simple hard/soft buckets |
| **Solver diversity** | 4 production solvers with auto-selection | Unknown (likely single solver) |
| **Explainability** | Per-decision alternatives + confidence scores | Preference satisfaction % only |
| **Resilience** | Full resilience framework (N-1/N-2, circuit breakers) | Not mentioned |
| **ACGME compliance** | Native 80-hour, 1-in-7, supervision rules | NHS-specific compliance only |

### Ideas to borrow from Patchwork

1. **Self-rostering flow** — Let residents input shift preferences directly through the UI, not just coordinators. AAPM currently generates schedules top-down; Patchwork's bottom-up preference input is a better UX.

2. **Negative preference satisfaction metric** — "98% of unwanted shifts avoided" is a concrete, measurable goal. AAPM should track and report this.

3. **Structured exception reporting** — When the generated schedule deviates from preferences or has manual overrides, log and surface those deviations clearly. Useful for audit trails.

4. **Constraint transparency layer** — Show users *why* a scheduling decision was made ("Dr. Smith got Friday call because they were the only PGY-3 available who hadn't exceeded 80 hours").

## Decision

**No code changes.** Patchwork validates AAPM's problem space but doesn't introduce techniques AAPM hasn't already considered. The four "ideas to borrow" above should be evaluated when building AAPM's preference input UI and reporting features.

## What NOT to copy

- Patchwork's SaaS model (AAPM is self-hosted for OPSEC)
- Their simple hard/soft constraint model (AAPM's formal constraint classes are more powerful)
- NHS-specific compliance rules (AAPM targets ACGME/military)
