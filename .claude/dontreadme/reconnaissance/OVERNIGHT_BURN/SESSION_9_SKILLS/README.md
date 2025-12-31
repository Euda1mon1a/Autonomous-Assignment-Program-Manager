# SESSION 9: Skills Model Tier Guide - SEARCH_PARTY Report

> **Operation Type:** G2_RECON - SEARCH_PARTY
> **Report Date:** 2025-12-30
> **Classification:** Operational Intelligence

---

## Mission Summary

Create comprehensive documentation for model tier (Haiku, Sonnet, Opus) selection when executing AI agent skills. Provide a deterministic, algorithmic approach to tier selection with clear examples, cost analysis, and implementation guidelines.

---

## SEARCH_PARTY Lenses Applied

### 1. PERCEPTION: Current Tier Usage
**Finding:** 94% of skills currently assigned to Opus, only 6% to Haiku, 0% to Sonnet
- Indicates over-reliance on most expensive model
- Missed cost optimization opportunity
- No tier differentiation strategy

### 2. INVESTIGATION: Task-to-Tier Mapping
**Finding:** Clear mapping exists from task domains/dependencies to optimal tier
- Linting/routing → Haiku (fast, cheap)
- Standard development → Sonnet (balanced)
- Security/complex reasoning → Opus (powerful)
- Current assignments don't follow this pattern

### 3. ARCANA: Model Capability Differences
**Finding:** Each tier has distinct capabilities and cost profiles
- Haiku: Fast (500ms), cheap (1x), limited reasoning
- Sonnet: Balanced (2-3s), moderate (4-5x), good reasoning
- Opus: Slow (5-10s), expensive (10-12x), excellent reasoning
- One-size-fits-all Opus approach wastes resources

### 4. HISTORY: Tier Selection Evolution
**Finding:** Complexity scoring formula exists but not applied systematically
- Formula documented in Session 025 artifacts
- Formula: `(Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)`
- Tiers: 0-5→Haiku, 6-12→Sonnet, 13+→Opus
- Never operationalized as systematic tier assignment

### 5. INSIGHT: Cost vs Capability Philosophy
**Finding:** Three viable philosophies with different trade-offs
- Cost-First: 70% savings, lower quality
- Balanced (recommended): 50-60% savings, optimized quality
- Quality-First: 0% savings, excellent quality
- Balanced approach balances budget and quality constraints

### 6. RELIGION: Automated Tier Selection
**Finding:** Tier selection can and should be automated
- Rule-based constraints (security, compliance → Opus)
- Complexity score determinism
- Hard boundaries (Haiku can't do security, Opus wastes on linting)
- Soft boundaries (some tasks work on 2+ tiers)

### 7. NATURE: Tier Boundaries
**Finding:** Clear hard boundaries exist, soft boundaries task-dependent
- Haiku: Cannot handle multi-step reasoning or security analysis
- Sonnet: Cannot handle security audits or novel algorithm design
- Opus: Wasteful for linting, formatting, simple routing
- Overlap zones where context matters

### 8. MEDICINE: Task Complexity Context
**Finding:** ACGME/compliance tasks need higher tiers than general development
- ACGME rule explanation → Haiku
- Schedule validation → Sonnet
- Full compliance audit → Opus
- Context and scope determine tier more than task type

### 9. SURVIVAL: Fallback Tier Handling
**Finding:** Predictable escalation chain prevents failures
- Haiku → Sonnet → Opus (upgrade when task too complex)
- Haiku successes can be reused, reducing cost
- Robust error detection enables smart escalation
- Human escalation only when even Opus struggles

### 10. STEALTH: Misaligned Tier Detection
**Finding:** Misalignment patterns are detectable and actionable
- Under-provisioned: Vague output, incomplete reasoning
- Over-provisioned: Overcomplicated solutions, unnecessary documentation
- Automated detection possible using complexity scoring
- Monthly audits can maintain alignment

---

## Key Findings

### 1. Complexity Scoring Formula
```
Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)

0-5   → Haiku (Scout)
6-12  → Sonnet (Strategist)
13+   → Opus (Architect)
```

### 2. Current vs Optimal Tier Distribution

**Current:**
- Haiku: 6% (2 skills)
- Sonnet: 0% (0 skills)
- Opus: 94% (32 skills)

**Recommended:**
- Haiku: 30% (10 skills) - Linting, routing, reference
- Sonnet: 55% (18 skills) - Standard development
- Opus: 15% (5 skills) - Complex reasoning, security

### 3. Cost Savings Potential
- Current approach: All Opus = 100% cost baseline
- Recommended approach: Mixed tiers = 40-50% cost
- Savings: **50-60% reduction** in model operational costs

---

## Deliverables

### Primary Document
📄 **`skills-model-tier-guide.md`** (9,200+ words)

Complete comprehensive guide covering:
- Model tier definitions and capabilities
- Complexity scoring algorithm with formula and examples
- Decision trees for tier selection
- Current tier usage analysis
- Task-to-tier mapping framework
- Capability comparison matrices
- Cost vs capability philosophy
- Automated tier selection algorithms
- Tier boundary definitions
- Domain-specific context (ACGME, security, testing)
- Fallback and error handling strategies
- Misalignment detection and correction
- Cost optimization strategies with 60-70% savings roadmap
- Implementation guidelines and checklists
- Reference tables and appendices

---

## Implementation Roadmap

### Phase 1: Immediate (Week 1)
**Action:** Bulk tier assignment by skill category
- Linting/formatting → Haiku
- Standard development → Sonnet
- Security/complex → Opus
- **Cost savings:** 50-60%
- **Effort:** Low

### Phase 2: Week 2
**Action:** Complexity score all remaining unassigned skills
- Apply formula to each skill
- Document rationale
- **Cost savings:** Additional 10-15%

### Phase 3: Week 3
**Action:** Implement tier escalation system
- Smart fallback chain
- Error detection
- **Cost savings:** Additional 10-20%

### Phase 4: Week 4
**Action:** Deploy monitoring and optimization
- Track actual usage
- Monthly audits
- **Cost savings:** Additional 5-10%

**Total Projected Savings: 60-70%**

---

## Quick Reference

### Tier Selection at a Glance

| Tier | Speed | Cost | Best For | Complexity |
|------|-------|------|----------|-----------|
| Haiku | 500ms | 1x | Linting, routing, reference | 0-5 |
| Sonnet | 2-3s | 4-5x | Standard development, code generation | 6-12 |
| Opus | 5-10s | 10-12x | Security, complex reasoning, incidents | 13+ |

### When to Use Each Tier

**Haiku:**
- Lint and format code
- Route decisions/task selection
- Reference lookups (ACGME rules)
- Simple text transformations
- Classification tasks

**Sonnet:**
- Create API endpoints
- Build React components
- Write tests
- Database migrations
- Code review (logic, patterns)
- Standard schedule operations

**Opus:**
- Security audits
- ACGME compliance validation
- Production incident response
- Complex debugging
- Architectural design
- Novel algorithms

---

## Files in This Directory

```
SESSION_9_SKILLS/
├── README.md                          (this file - summary)
└── skills-model-tier-guide.md         (9,200+ word guide)
```

---

## Status

| Item | Status |
|------|--------|
| Complexity scoring formula | Documented |
| Tier definitions | Complete |
| Decision trees | Provided |
| Current usage analysis | Complete (94% Opus, 6% Haiku, 0% Sonnet) |
| Task mapping | Complete |
| Cost analysis | Complete (50-70% savings potential) |
| Implementation guide | Complete with checklists |
| Ready for deployment | YES |

---

**Report Date:** 2025-12-30
**Operation:** G2_RECON SEARCH_PARTY
**Status:** COMPLETE AND ACTIONABLE
