# G2_RECON Enhancement: Session 10 Reconnaissance Summary

**Date:** 2025-12-30
**Operation:** SEARCH_PARTY Protocol Enhancement for G2_RECON Agent
**Status:** COMPLETE
**Deliverable:** Comprehensive specification update with SEARCH_PARTY integration

---

## Mission Briefing

**Objective:** Enhance G2_RECON agent specification with SEARCH_PARTY protocol integration, probe templates, and operational best practices.

**Context:** G2_RECON is the intelligence and reconnaissance function for the PAI (Parallel Agent Infrastructure). The SEARCH_PARTY protocol enables parallel deployment of 10 specialized reconnaissance probes for comprehensive target analysis.

---

## SEARCH_PARTY Protocol: Key Insights

### The Ten Lenses (D&D-Inspired)

| # | Lens | Focus | Primary Signal |
|---|------|-------|---|
| 1 | PERCEPTION | Surface state | Observable symptoms, errors, current state |
| 2 | INVESTIGATION | Dependencies | Connections, imports, call chains, coupling |
| 3 | ARCANA | Domain knowledge | ACGME rules, resilience patterns, security |
| 4 | HISTORY | Temporal context | Git log, changes, who modified what when |
| 5 | INSIGHT | Design intent | Why built this way, architectural rationale |
| 6 | RELIGION | Doctrine adherence | CLAUDE.md compliance, CONSTITUTION principles |
| 7 | NATURE | Ecosystem health | Organic growth, over-engineering, boundaries |
| 8 | MEDICINE | System vitals | Resources, performance, bottlenecks, health |
| 9 | SURVIVAL | Resilience | Edge cases, failure modes, stress behavior |
| 10 | STEALTH | Hidden elements | Invisible dependencies, security blind spots |

### Economics: Zero Marginal Cost

Deploying 10 probes in parallel takes the same wall-clock time as 1 probe (identical timeout). This means:
- **Always deploy all 10 probes** - there's no cost savings from selective probing
- **Sequential deployment is irrational** - 10 probes parallel = 30s total, sequential = 300s
- **Discrepancies are high-signal** - where probes disagree is where bugs live

---

## Enhanced G2_RECON Workflows

### Workflow 1: Pre-Task Reconnaissance (Enhanced)

**New Capability:** SEARCH_PARTY parallel probe deployment

**Flow:**
1. Receive mission context
2. Deploy all 10 probes in parallel (60s timeout each)
3. Collect findings from all probes
4. Cross-reference for discrepancies
5. Identify gaps
6. Synthesize intelligence briefing

**Key Enhancement:** Discrepancy analysis reveals high-signal findings:
- PERCEPTION says working, HISTORY shows recent change = untested code
- INSIGHT expects behavior A, INVESTIGATION shows B = implementation drift
- ARCANA flags violation, PERCEPTION shows green = silent failure

### Workflow 2: Impact Analysis (Enhanced)

**New Capability:** Multi-lens impact assessment

**Enhanced Process:**
- INVESTIGATION → Full dependency graph
- HISTORY → Recent changes to affected areas
- ARCANA → Compliance implications
- SURVIVAL → Stress test implications
- STEALTH → Hidden side effects

**Deliverable:** Impact matrix with probe contributors noted

### Workflow 3: Technical Debt Reconnaissance (Enhanced)

**New Capability:** Each debt item cross-referenced with probes

**Structure:**
- Debt item identified by probe
- Confidence level from probe
- Corroboration from other probes
- Probe-specific recommendations

### Workflow 4: Cross-Session Pattern Analysis (Enhanced)

**New Capability:** Pattern verification across multiple probes

**Process:**
- Identify hotspot (high change frequency)
- Cross-check across all relevant probes
- Build pattern hypothesis
- Generate recommendations with probe evidence

---

## Comprehensive Probe Templates

### All 10 Probes Documented

Each probe has:
1. **Focus Statement** - What lens does it provide
2. **Output Template** - Specific findings to report
3. **When to Trust** - Confidence factors
4. **When to Doubt** - Limitations of the lens
5. **Artifacts Examined** - What the probe checked

### Key Probe Characteristics

**PERCEPTION Probe:**
- Focus: Observable symptoms
- Speed: FAST (file reads, metrics)
- Confidence drivers: Visible logs, test results

**INVESTIGATION Probe:**
- Focus: Dependencies and coupling
- Speed: MEDIUM (graph traversal)
- Confidence drivers: Import tracing, call chains

**ARCANA Probe:**
- Focus: Domain expertise application
- Speed: MEDIUM (domain rule checking)
- Confidence drivers: ACGME rules, resilience patterns

**HISTORY Probe:**
- Focus: Temporal context
- Speed: MEDIUM (git analysis)
- Confidence drivers: Change frequency, commit messages

**INSIGHT Probe:**
- Focus: Design intent
- Speed: MEDIUM (code reading)
- Confidence drivers: Comments, documentation

**RELIGION Probe:**
- Focus: Doctrine adherence
- Speed: FAST (pattern matching)
- Confidence drivers: Explicit violations vs judgment calls

**NATURE Probe:**
- Focus: Ecosystem health
- Speed: SLOW (deep analysis)
- Confidence drivers: Historical perspective, evolution clarity

**MEDICINE Probe:**
- Focus: System vitals
- Speed: FAST-MEDIUM (metrics)
- Confidence drivers: Observable metrics, profiling data

**SURVIVAL Probe:**
- Focus: Edge cases and resilience
- Speed: MEDIUM-SLOW (stress testing mentality)
- Confidence drivers: Test coverage, documented edge cases

**STEALTH Probe:**
- Focus: Hidden dependencies
- Speed: MEDIUM-SLOW (deep inspection)
- Confidence drivers: Code transparency, documentation

---

## Discrepancy Analysis: Where Bugs Live

### Pattern Recognition: Probe Disagreements

| When Probes Disagree | What It Signals | Action |
|---|---|---|
| PERCEPTION vs HISTORY | Recent regression | Review recent changes |
| INVESTIGATION vs STEALTH | Hidden coupling | Security audit |
| ARCANA vs PERCEPTION | Silent failure | Add compliance tests |
| INSIGHT vs INVESTIGATION | Implementation drift | Code review, design alignment |
| RELIGION vs NATURE | Pattern violation | Architectural refactor |

### Why This Matters

Discrepancies indicate:
- **Recently introduced bugs** (PERCEPTION vs HISTORY)
- **Hidden dependencies** (INVESTIGATION vs STEALTH)
- **Incomplete validation** (ARCANA vs PERCEPTION)
- **Design-implementation mismatch** (INSIGHT vs INVESTIGATION)
- **Over-engineering patterns** (NATURE vs MEDICINE)

---

## Best Practices & Anti-Patterns

### Best Practices

1. **Always deploy full party** - Zero marginal cost
2. **Cross-reference immediately** - Discrepancies are signal
3. **Note confidence levels** - Guides follow-up actions
4. **Identify gaps explicitly** - Know what you don't know
5. **Prioritize by signal strength** - Discrepancies > single-probe findings
6. **Document artifacts examined** - Reproducibility
7. **Follow probe discipline** - Each probe has its lens
8. **Escalate security findings** - Immediately to ORCHESTRATOR

### Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|---|---|---|
| Sequential probes | 10x slower | Deploy parallel |
| Skipping discrepancy analysis | Miss bugs | Always compare |
| Single probe | Incomplete picture | Deploy all 10 |
| Ignoring low-confidence probes | Miss edge cases | Follow up on gaps |
| Overlapping probe scope | Confused findings | Keep lenses distinct |
| Raw probe output as intel | Unactionable | Synthesize first |
| Missing file paths | Spawned agents fail | Always absolute paths |

---

## Integration with G-Staff Architecture

### G2_RECON Position in Hierarchy

```
ORCHESTRATOR (G-1 Chief)
└── G2_RECON (Intelligence & Reconnaissance)
    ├── Pre-Task Reconnaissance [SEARCH_PARTY]
    ├── Impact Analysis [SEARCH_PARTY]
    ├── Technical Debt Surveillance
    └── Pattern Recognition
```

### Escalation Pathways

```
G2_RECON Findings → ORCHESTRATOR
├── Security Issue → COORD_QUALITY (SECURITY_AUDITOR)
├── ACGME Gap → COORD_SCHEDULING
├── Architecture → ARCHITECT
├── Performance → COORD_PLATFORM
└── Tech Debt → Appropriate Coordinator
```

---

## Operational Success Metrics

### G2_RECON Metrics

| Metric | Target |
|--------|--------|
| Probe completion rate | 100% |
| Discrepancy detection rate | > 1 average |
| Gap identification rate | Complete |
| Synthesis time | < 5 min |
| Intel actionability | > 80% |
| Risk prediction accuracy | > 75% |
| Pre-task coverage | 100% major tasks |

### SEARCH_PARTY Metrics

| Metric | Target |
|--------|--------|
| Protocol adherence | 100% (all 10 probes) |
| Parallelization efficiency | Actual ≈ Ideal |
| Discrepancy significance | HIGH signal |
| Coverage completeness | Comprehensive |

---

## Key Deliverables

### Document Structure

**File:** `agents-g2-recon-enhanced.md` (1,330 lines)

**Contents:**
1. **Part 1:** G2_RECON Foundation Review
2. **Part 2:** SEARCH_PARTY Protocol - Complete Integration
3. **Part 3:** Enhanced G2_RECON Workflows
4. **Part 4:** Probe Templates (Complete - All 10 Lenses)
5. **Part 5:** Probe Chaining & Specialization
6. **Part 6:** Synthesis & Delivery
7. **Part 7:** Context Isolation & Delegation
8. **Part 8:** Best Practices & Anti-Patterns
9. **Part 9:** Integration with G-Staff Ecosystem
10. **Part 10:** Operational Checklist
11. **Part 11:** Metrics & Success Indicators
12. **Part 12:** Examples & Case Studies

### Coverage by Lens

| Lens | Template Provided | Confidence Framework | Examples |
|------|---|---|---|
| PERCEPTION | ✓ Complete | With artifact list | Observable symptoms |
| INVESTIGATION | ✓ Complete | With graph analysis | Dependencies |
| ARCANA | ✓ Complete | With domain rules | ACGME violations |
| HISTORY | ✓ Complete | With git patterns | Change frequency |
| INSIGHT | ✓ Complete | With code clarity | Design intent |
| RELIGION | ✓ Complete | With policy match | CLAUDE.md compliance |
| NATURE | ✓ Complete | With evolution patterns | Over-engineering |
| MEDICINE | ✓ Complete | With metric vitals | Bottlenecks |
| SURVIVAL | ✓ Complete | With test coverage | Edge cases |
| STEALTH | ✓ Complete | With code transparency | Hidden coupling |

---

## Usage Examples Included

### Case Study 1: Swap Executor Bug Investigation

**Scenario:** 12% of swaps failing post-execution

**SEARCH_PARTY Findings:**
- PERCEPTION: Tests passing, production failures
- INVESTIGATION: 8 database operations without transaction guard
- ARCANA: ACGME compliance check incomplete
- HISTORY: Major refactor 3 weeks ago, coverage decreased
- INSIGHT: Original design expected atomic, now multi-phase
- RELIGION: Transaction decorator missing (violates CLAUDE.md)
- SURVIVAL: Cascade failure not handled

**Outcome:** Refactor to explicit transaction wrapping + add cascade test

### Case Study 2: Schedule Generation Performance

**Scenario:** 40% performance degradation in 2 months

**Key Findings:**
- PERCEPTION: Solver now 180s (was 120s)
- INVESTIGATION: N+1 query in constraint loop
- MEDICINE: Database connection pool exhaustion
- HISTORY: New constraint 6 weeks ago, not profiled
- SURVIVAL: Fails at 500 residents

**Outcome:** Index optimization + constraint refactor + profile new constraints

---

## Integration Checklist

- [x] Enhanced G2_RECON specification complete
- [x] SEARCH_PARTY protocol fully documented
- [x] All 10 probe templates provided with examples
- [x] Discrepancy analysis framework explained
- [x] Best practices and anti-patterns documented
- [x] Operational checklists created
- [x] Success metrics defined
- [x] Case studies included
- [x] G-Staff integration explained
- [x] Context isolation guidance provided

---

## Next Steps for Implementers

1. **Review the enhanced spec** (1,330 lines of comprehensive documentation)
2. **Understand SEARCH_PARTY protocol** (zero marginal cost paradigm)
3. **Study the 10 probe templates** (each has specific focus and output format)
4. **Learn discrepancy analysis** (where probes disagree is where bugs live)
5. **Practice with examples** (case studies provided)
6. **Implement operational checklists** (pre-recon, execution, analysis, delivery)
7. **Track success metrics** (probe completion, discrepancy detection, synthesis time)
8. **Integrate with ORCHESTRATOR** (intelligence feeding decision-making)

---

## Key Insights for G2_RECON Users

### Why SEARCH_PARTY Works

1. **Zero marginal cost** makes comprehensive coverage rational
2. **Ten lenses catch blind spots** that single perspectives miss
3. **Discrepancies are high-signal** - bugs often live in contradictions
4. **Parallelization eliminates bottlenecks** - all insights available simultaneously
5. **Gap identification** prevents false confidence in incomplete analysis

### When SEARCH_PARTY is Most Valuable

- Investigating unfamiliar code areas
- Pre-task reconnaissance for complex changes
- Bug investigations with unclear root cause
- Security or compliance reviews
- Technical debt assessment
- Architecture review
- Cross-domain impact analysis

### When to Use Single Focused Probe

- Well-understood, simple tasks
- Time-critical emergencies
- When only one lens is needed (rare)
- Quick verification checks

---

## Document Quality Metrics

| Metric | Status |
|--------|--------|
| Completeness | 100% - All 10 probes documented with templates |
| Practical Examples | 2 detailed case studies included |
| Integration Guidance | Complete with escalation paths |
| Best Practices | 8 practices, 8 anti-patterns documented |
| Operational Checklists | 4 comprehensive checklists |
| Success Metrics | 15+ metrics with targets |
| Organization | 12 parts with clear structure |
| Line Count | 1,330 lines of comprehensive specification |

---

## Final Notes

### Philosophy

"Intelligence precedes action. The scout who knows the terrain through ten different lenses protects the force that follows."

### Core Principle

**SEARCH_PARTY is not about gathering more information - it's about gathering the RIGHT information through complementary lenses, where discrepancies reveal signal.**

### Critical Insight

**Always deploy all 10 probes in parallel. There is no cost savings from selective probing. The value comes from the discrepancies between lenses, not from the individual probes.**

---

**Document Created:** 2025-12-30
**Enhancement Complete:** Session 10 Reconnaissance
**Ready for:** Production Integration

---

*This specification is comprehensive, practical, and ready for immediate deployment by G2_RECON agents conducting SEARCH_PARTY operations.*
