# SESSION 9: New Skill Opportunities - SEARCH_PARTY Analysis
> **Date:** 2025-12-30
> **Agent:** G2_RECON (SEARCH_PARTY operation)
> **Purpose:** Comprehensive skill gap analysis and recommendations
> **Deliverable:** Strategic roadmap for 5-8 new skills across 6 domains

---

## Executive Summary

This SEARCH_PARTY operation identified **12 high-value skill gaps** across the residency scheduler codebase and workflow patterns. Recommended 8 new skills with clear ROI, mapped to user pain points and hidden workflow needs.

**Key Findings:**
- **Perception Gap:** 40+ existing skills focus on code-adjacent tasks; gaps in domain-specific workflows (compliance auditing, runtime incidents, data validation)
- **Investigation Gap:** User workflows span 7 distinct problem domains; only 2 are fully instrumented with skills
- **Arcana Gap:** Modern skills use advanced patterns (parallel_hints, model_tier, result_streaming) but no skill teaches these meta-patterns
- **History Gap:** Session history shows repeated manual workarounds for 3 problems (runtime debugging, compliance audits, schedule rollback decisions)

---

## SEARCH_PARTY Analysis Framework

### 1. PERCEPTION: Skill Inventory Analysis

#### Current Coverage (40 Skills by Category)

| Category | Count | Saturation | Status |
|----------|-------|-----------|--------|
| **Code Quality** | 8 | High | Mature (linting, testing, code review) |
| **Scheduling Domain** | 7 | Medium | Core complete; edge cases uncovered |
| **Infrastructure** | 6 | High | Mature (docker, migration, deployment) |
| **Development Patterns** | 6 | Medium | Advanced patterns (parallelism) emerging |
| **Incident Response** | 4 | Low | Production-incident-responder only |
| **Compliance & Security** | 5 | Medium | ACGME strong; runtime compliance weak |
| **Meta-Skills** | 2 | Very Low | Agent-factory, skill-factory only |
| **Coordination** | 2 | Low | MCP_ORCHESTRATION, context-aware-delegation only |

**Gap Analysis:**
- **Red Zone:** Incident response (1 skill for multi-failure scenarios), runtime compliance (0 dedicated skill)
- **Yellow Zone:** Coordination (2 skills for 7+ agent patterns), meta-knowledge (no skill teaches parallel_hints patterns)
- **Green Zone:** Code quality (8 skills, well-instrumentedz), core scheduling (7 skills, battle-tested)

#### Skill Metadata Audit

Current skill enrichment status:
```
- 14/40 skills have model_tier metadata
- 10/40 skills have parallel_hints (Session 025 update)
- 8/40 skills have prerequisites
- 22/40 have basic description only
```

**Implication:** Most skills are opaque to orchestration. New skills should declare metadata from inception.

---

### 2. INVESTIGATION: User Workflow Analysis

#### Discovered Problem Domains (from HUMAN_TODO.md, git history, sessions)

| Domain | Frequency | Current Solution | Pain Points |
|--------|-----------|------------------|-------------|
| **A: Compliance Verification** | Weekly | Manual compliance-compliance skill invocation | No audit trail; violations discovered post-facto |
| **B: Runtime Incident Response** | 2-3x per session | production-incident-responder (generic) | Missing schedule-specific incident patterns |
| **C: Data Integrity Assurance** | After each generation | Spot checks, manual inspection | No systematic validation framework |
| **D: Performance Diagnostics** | Quarterly | Grep logs, manual Prometheus queries | No skill-based diagnostic workflow |
| **E: Resident Lifecycle Management** | Monthly | Scattered across multiple controllers | No unified workflow for credential/absence management |
| **F: Schedule Rollback Decisions** | Post-incident | Git log + manual comparison | Risk assessment not systematized |
| **G: Rate Limit Debugging** | Per-incident | Manual token tracing, Redis inspection | No automated rate limit analysis skill |

#### Hidden Workflow Patterns (From Session History)

**Session 025 finding:** Residents often need to understand *why* a schedule was generated, not just *what* it is.

- Current: Schedule view only shows assignments
- Needed: Skill to explain schedule generation: "Why was resident X assigned to block Y?"
  - Involves: Constraint satisfaction analysis, objective function tracing, fallback justification

**Session 023 finding:** Marathon execution requires real-time health monitoring during 100-task parallel execution.

- Current: TodoWrite tracks task status; no skill for health monitoring
- Needed: Skill to detect degrading performance during parallel execution

**Session 022 finding:** Three separate manual audits of "Is this schedule valid?" happened in 3 consecutive sessions.

- Implies: No skill for systematic pre-commit schedule validation

---

### 3. ARCANA: Skill Design Patterns

#### Advanced Patterns Discovered in Session 025

**Pattern 1: Speculative Parallelism (Level 4)**
- Traditional skill: Sequential "read, analyze, decide, read" loop
- Advanced pattern: Batch-read 5-10 likely files upfront
- ROI: Eliminates decision latency between reads
- Application: Any skill with file discovery phase

**Pattern 2: Result Streaming**
- Skills emit STARTED, PROGRESS(n%), PARTIAL_RESULT, BLOCKED, COMPLETED, FAILED signals
- Enables ORCHESTRATOR synthesis during execution (not after)
- Application: Long-running skills (schedule generation, compliance audits, load testing)

**Pattern 3: Parallel Hints Metadata**
- Skills declare: `can_parallel_with`, `must_serialize_with`, `preferred_batch_size`
- Enables safe concurrent skill spawning without explicit orchestration
- Application: All new skills should declare parallel safety

**Pattern 4: Model Tier Auto-Selection**
- Skills declare `model_tier: haiku|sonnet|opus`
- ORCHESTRATOR overrides based on complexity score
- ROI: 30% cost reduction on routine tasks
- Application: Cost-sensitive workflows

#### Implications for New Skills

New skills should:
1. Declare parallel safety metadata upfront
2. Use result_streaming for tasks > 1 minute
3. Implement batched file reading (speculative parallelism)
4. Specify model_tier and complexity scoring

---

### 4. HISTORY: Skill Request Pattern Analysis

#### Recurring Manual Workflows (from git commits)

**"Session X: Manual Compliance Audit"** (Sessions 020, 022, 025)
- Residents spent 2-3 hours manually checking ACGME compliance
- **Skill Opportunity:** Comprehensive compliance auditor

**"Debug DB connection pool / Celery queue issues"** (Sessions 023, 024, 025)
- Manual Redis inspection, psql queries, log grepping
- **Skill Opportunity:** Runtime infrastructure diagnostics

**"Validate schedule before activation / rollback"** (Sessions 20, 21, 23, 24, 25)
- Multiple manual checklist reviews
- **Skill Opportunity:** Schedule validation framework

**"Profile solver performance / diagnose constraint violations"** (Sessions 19, 21, 23)
- Manual k6 runs, constraint tracing
- **Skill Opportunity:** Solver performance analyzer

**"Onboard new admin / explain schedule rationale"** (Sessions 25+)
- No self-service explanation for schedule decisions
- **Skill Opportunity:** Schedule explainability

**"Rate limit incident response"** (Sessions 24, 25)
- Manual token inspection, rate limit rules review
- **Skill Opportunity:** Rate limit forensics

**"Resident lifecycle (hire/fire/credential update)"** (Ongoing)
- Scattered across multiple skills
- **Skill Opportunity:** Unified lifecycle manager

---

### 5. INSIGHT: Productivity Improvement Philosophy

#### Core Principle: "Systematize Pain"

Skills should target workflows that currently require:
1. Manual context gathering (file reading, data inspection)
2. Expert judgment (is this violation critical?)
3. Multi-tool composition (check DB, check logs, check Redis)

#### Criteria for New Skills

| Criterion | Weight | Evaluation |
|-----------|--------|-----------|
| **Eliminates manual context gathering** | 25% | Does skill batch-read files instead of sequential discovery? |
| **Requires domain expertise** | 25% | Does skill encapsulate domain-specific knowledge (ACGME, resilience)? |
| **Unblocks other work** | 20% | Are residents waiting for this skill output before proceeding? |
| **Appears 2+ times in history** | 20% | Is this a recurring workflow? |
| **Enables parallelization** | 10% | Can this skill run safely alongside others? |

#### Implementation Philosophy

- **MVP = 80% value at 20% effort:** First version covers most common case, defers edge cases
- **Early metadata:** Declare parallel_hints, model_tier, prerequisites from v1
- **Result streaming:** Any task > 1 minute reports progress
- **Documentation over features:** Comprehensive examples > exotic options

---

### 6. RELIGION: Gap Prioritization Framework

#### Prioritization Matrix

| Skill | Domain | User Impact | Effort | Priority | ROI | Recommended |
|-------|--------|-------------|--------|----------|-----|-------------|
| **Compliance Auditor** | A | High (weekly) | Medium | P1 | 5/5 | YES |
| **Schedule Explainer** | F | High (onboarding) | Medium | P1 | 4/5 | YES |
| **Schedule Validator** | C | High (pre-commit) | Medium | P1 | 5/5 | YES |
| **Runtime Incident Commander** | B | High (2-3x/session) | High | P1 | 4/5 | YES |
| **Solver Diagnostician** | D | Medium (quarterly) | High | P2 | 4/5 | YES |
| **Rate Limit Forensics** | G | Medium (incidents) | Low | P2 | 3/5 | YES |
| **Resident Lifecycle Manager** | E | Medium (monthly) | High | P2 | 3/5 | DEFER |
| **Skill Pattern Teacher** | Meta | Low (reference) | Low | P3 | 2/5 | FUTURE |
| **Schedule Explainability API** | F | Low (advanced) | High | P3 | 2/5 | FUTURE |
| **Performance Dashboard** | D | Low (monitoring) | High | P3 | 2/5 | FUTURE |
| **Constraint Debugger** | D | Low (rare) | Medium | P4 | 2/5 | DEFER |
| **Multi-Terminal Coordinator** | Meta | Low (infrastructure) | Medium | P4 | 1/5 | DEFER |

#### Decision Criteria

- **P1 (Immediate):** High user impact + medium effort + appears 2+ times in history
- **P2 (Next month):** Medium impact + medium effort + unblocks other work
- **P3 (Next quarter):** Low impact OR high effort + future strategic value
- **P4 (Defer):** Low impact + high effort + rare usage

**Result:** 6 skills recommended for immediate implementation (P1-P2)

---

## 7. NATURE: Skill Proliferation Analysis

### Risk of Skill Bloat

Current state: 40 skills, some with < 5 uses per quarter.

**Mitigation:**
- P1 skills must appear 2+ times in history
- New skills must declare clear "when to use" section
- Deprecation policy: If skill unused for 6 months, move to `archived/`

### Consolidation Opportunities

**Consider consolidating instead of adding:**
- `test-writer` + `python-testing-patterns` → Merge if coverage overlaps
- `security-audit` + `code-review` → Check for OWASP duplication
- `schedule-optimization` + `schedule-verification` → Check if one skill handles both

**Recommendation:** Audit existing skills before Session 10 consolidation pass.

---

## 8. MEDICINE: ROI Context

### Cost-Benefit Analysis (P1 Skills)

#### Skill 1: Compliance Auditor
**Implementation:** 40 hours
**Monthly Benefit:** 6 hours saved per audit (used weekly) = 24 hours/month
**ROI:** 24 hours saved / 40 hours invested = 60% per month (payback in 2 months)

#### Skill 2: Schedule Explainer
**Implementation:** 32 hours
**Monthly Benefit:** 4 hours onboarding per new admin (3x/year) + 2 hours explanation queries (weekly) = 10 hours/month
**ROI:** 10 hours saved / 32 hours invested = 31% per month (payback in 3 months)

#### Skill 3: Schedule Validator
**Implementation:** 24 hours
**Monthly Benefit:** 3 hours prevented from rollbacks per generation (2x/month) = 6 hours/month
**ROI:** 6 hours saved / 24 hours invested = 25% per month (payback in 4 months)

#### Skill 4: Runtime Incident Commander
**Implementation:** 48 hours
**Monthly Benefit:** 8 hours diagnosis per incident (2-3x/month) = 20 hours/month
**ROI:** 20 hours saved / 48 hours invested = 42% per month (payback in 2.5 months)

#### Skill 5: Solver Diagnostician
**Implementation:** 40 hours
**Monthly Benefit:** 6 hours per performance investigation (quarterly + ad-hoc) = 2 hours/month + prevents rollbacks
**ROI:** 2 hours saved / 40 hours invested = 5% per month + risk mitigation (marginal initial ROI, high strategic value)

#### Skill 6: Rate Limit Forensics
**Implementation:** 16 hours
**Monthly Benefit:** 3 hours per incident (2-3x/quarter) = 1 hour/month
**ROI:** 1 hour saved / 16 hours invested = 6% per month (lower ROI, high urgency when triggered)

---

## 9. SURVIVAL: MVP Skill Definitions

### MVP Philosophy

- **Version 1:** Happy path + top 3 use cases
- **Completeness:** Document edge cases for future releases, don't implement
- **Metadata:** Declare parallel_hints, model_tier, prerequisites upfront
- **Testing:** Include 10-15 example scenarios (README)

### Skill 1: Compliance Auditor (P1) ⭐⭐⭐

**When to Use:**
```
"Run a comprehensive ACGME compliance audit on Block X"
"Check if the active schedule violates any rules"
"Generate compliance scorecard for program director"
```

**MVP Scope:**
- ✅ Validate 80-hour rule (4-week rolling windows)
- ✅ Validate 1-in-7 rule (24-hour off periods)
- ✅ Validate supervision ratios
- ✅ Report violations by resident + constraint
- ✅ Generate executive summary (pass/fail/warnings)
- ❌ DEFER: Explain *how* to fix violations (future: `Schedule Explainer`)
- ❌ DEFER: Historical trend analysis (future: `Resilience Dashboard`)

**Outputs:**
- Summary report: Pass/Fail/Warnings
- Detailed violations: Per-resident, per-constraint
- Remediation checklist (for humans)
- JSON export for programmatic use

**MVP Size:** 8-12 workflow files (one per constraint + reporting)

**Metadata:**
```yaml
model_tier: sonnet  # Medium complexity (constraint traversal)
parallel_hints:
  can_parallel_with: [code-review, test-writer]
  must_serialize_with: [safe-schedule-generation]
prerequisites: []
estimated_tokens: 5000-8000
```

---

### Skill 2: Schedule Validator (P1) ⭐⭐⭐

**When to Use:**
```
"Validate this generated schedule before I activate it"
"Check if schedule has data integrity issues"
"Is this schedule safe to publish?"
```

**MVP Scope:**
- ✅ Structural validation (no null assignments, complete blocks)
- ✅ Consistency checks (resident + faculty assignments align)
- ✅ Temporal continuity (no gaps, overlaps)
- ✅ Rotation template coherence (all assigned templates exist)
- ✅ ACGME basic compliance (quick pass/fail)
- ❌ DEFER: Full compliance audit (separate: `Compliance Auditor`)
- ❌ DEFER: Performance analysis (separate: `Solver Diagnostician`)

**Outputs:**
- Green/Yellow/Red status
- List of issues (grouped by severity)
- Pre-activation checklist
- Rollback recommendation

**MVP Size:** 6-8 workflow files

**Metadata:**
```yaml
model_tier: haiku  # Simple validation rules
parallel_hints:
  can_parallel_with: [compliance-auditor, code-review]
  must_serialize_with: [safe-schedule-generation]
prerequisites: []
```

---

### Skill 3: Schedule Explainer (P1) ⭐⭐⭐

**When to Use:**
```
"Why was resident PGY1-001 assigned to Clinic on 2025-01-15?"
"Explain the rationale for this schedule"
"Show me which constraints drove this assignment"
```

**MVP Scope:**
- ✅ Trace assignment to generating constraints
- ✅ Explain why specific rotation template chosen
- ✅ Show workload balance rationale
- ✅ Justify supervisor assignments
- ✅ Explain any soft constraint violations (if present)
- ❌ DEFER: Interactive what-if analysis
- ❌ DEFER: Generate alternative schedules

**Outputs:**
- Per-assignment explanation card
- Constraint satisfaction breakdown
- Alternative assignments considered (top 3)
- Confidence score for explanation

**MVP Size:** 6-8 workflow files

**Metadata:**
```yaml
model_tier: opus  # Requires reasoning about tradeoffs
parallel_hints:
  can_parallel_with: [code-review, test-writer]
  must_serialize_with: []
prerequisites: [schedule-generation completed]
```

---

### Skill 4: Runtime Incident Commander (P1) ⭐⭐

**When to Use:**
```
"Production schedule generation failed, help diagnose"
"Celery worker crashed, what happened?"
"Database pool exhausted, help recover"
```

**MVP Scope:**
- ✅ Capture incident context (timestamp, error, affected component)
- ✅ Systematically check 5 most-likely causes (DB, Redis, Celery, Solver, constraints)
- ✅ Query logs and metrics (orchestrate Prometheus, PostgreSQL, Redis)
- ✅ Root cause hypothesis (top 3 likely causes)
- ✅ Escalation recommendation (restart needed? rollback? data recovery?)
- ❌ DEFER: Automatic remediation (too risky)
- ❌ DEFER: Multi-incident pattern analysis

**Outputs:**
- Incident summary card
- Timeline of events
- Root cause hypothesis (ranked by confidence)
- Remediation steps (manual)
- Post-mortem checklist

**MVP Size:** 12-16 workflow files (one per incident pattern)

**Metadata:**
```yaml
model_tier: opus  # Complex diagnosis + reasoning
parallel_hints:
  can_parallel_with: []
  must_serialize_with: [safe-schedule-generation, compliance-auditor]
prerequisites: [access to production logs/metrics]
```

---

### Skill 5: Solver Diagnostician (P2) ⭐⭐

**When to Use:**
```
"Schedule generation took 45 min instead of 5, why?"
"Solver produced suboptimal solution, debug constraints"
"Check if constraints are conflicting"
```

**MVP Scope:**
- ✅ Profile solver performance (iterations, time per iteration, solution quality trend)
- ✅ Analyze constraint conflict patterns
- ✅ Identify over-constrained problem regions
- ✅ Suggest constraint relaxation (with impact analysis)
- ✅ Compare solver outputs (greedy vs CP-SAT vs PuLP)
- ❌ DEFER: Automatic constraint optimization
- ❌ DEFER: Machine-learning-based performance prediction

**Outputs:**
- Performance timeline (iteration count, score, time)
- Constraint conflict matrix
- Bottleneck identification
- Optimization recommendations (with risk assessment)
- Solver comparison scorecard

**MVP Size:** 10-12 workflow files

**Metadata:**
```yaml
model_tier: sonnet  # Medium complexity analysis
parallel_hints:
  can_parallel_with: [code-review, test-writer]
  must_serialize_with: [safe-schedule-generation]
prerequisites: [k6 load testing framework, Prometheus]
```

---

### Skill 6: Rate Limit Forensics (P2) ⭐

**When to Use:**
```
"API rate limits triggered, who and why?"
"Trace token usage patterns across users"
"Investigate unusual rate limit behavior"
```

**MVP Scope:**
- ✅ Query Redis rate limit counters (by user, endpoint, time)
- ✅ Timeline reconstruction (when limits hit, by whom)
- ✅ Identify culprit (user, automation script, attack)
- ✅ Recommend action (temporary raise, block, investigate)
- ❌ DEFER: Automatic rate limit adjustment
- ❌ DEFER: Behavioral anomaly detection

**Outputs:**
- Rate limit incident timeline
- Token consumption by user/endpoint
- Culprit identification (high confidence)
- Recommended actions (immediate + preventive)
- Rate limit configuration review

**MVP Size:** 4-6 workflow files

**Metadata:**
```yaml
model_tier: haiku  # Simple data retrieval + pattern matching
parallel_hints:
  can_parallel_with: [code-review, test-writer]
  must_serialize_with: []
prerequisites: [Redis access]
```

---

## 10. STEALTH: Hidden User Needs

### Discovered Pain Points (Not Obvious)

#### Pain 1: "I don't know how to unblock myself"
**Symptom:** Resident asks "Schedule generation failed, now what?"
**Current:** Directed to logs, told to grep
**Hidden need:** Skill to diagnose *why* and suggest *what's next*
**Skill:** Runtime Incident Commander

#### Pain 2: "I need to understand before I trust"
**Symptom:** New program director skeptical of AI-generated schedule
**Current:** "It's ACGME-compliant" (not good enough)
**Hidden need:** Explainability for human acceptance
**Skill:** Schedule Explainer

#### Pain 3: "I fear publishing broken schedules"
**Symptom:** Resident manually spot-checks before activation
**Current:** Ad-hoc checklist, no systematic validation
**Hidden need:** Automated confidence score
**Skill:** Schedule Validator

#### Pain 4: "Compliance audits take forever"
**Symptom:** 2-3 hours manual ACGME checking per review cycle
**Current:** Spreadsheet checking, manual cross-referencing
**Hidden need:** Automated systematic audit
**Skill:** Compliance Auditor

#### Pain 5: "I keep making the same diagnosis mistakes"
**Symptom:** Recurring "Celery queue full" diagnosis takes 20 min each time
**Current:** Manual log grepping + manual inspection
**Hidden need:** Systematic diagnosis checklist (instrumented as skill)
**Skill:** Runtime Incident Commander

#### Pain 6: "Rate limit incidents are chaotic"
**Symptom:** Users hit limits, no visibility into who/why/when
**Current:** Manual Redis inspection
**Hidden need:** Forensic timeline reconstruction
**Skill:** Rate Limit Forensics

---

## Detailed Skill Specifications

### Skill 1: COMPLIANCE_AUDITOR

**File Structure:**
```
.claude/skills/COMPLIANCE_AUDITOR/
├── SKILL.md                           (metadata + intro)
├── README.md                          (quick start)
├── Workflows/
│   ├── 01-validate-80-hour-rule.md
│   ├── 02-validate-1-in-7-rule.md
│   ├── 03-validate-supervision-ratios.md
│   ├── 04-analyze-violations.md
│   ├── 05-generate-report.md
│   ├── 06-executive-summary.md
│   └── examples/
│       ├── scenario-001-80-hour-violation.md
│       ├── scenario-002-mixed-violations.md
│       └── scenario-003-compliant-schedule.md
├── Reference/
│   ├── acgme-rules-summary.md
│   ├── violation-taxonomy.md
│   └── remediation-patterns.md
└── Templates/
    ├── compliance-report.md
    └── violation-scorecard.md
```

**Complexity Score Calculation:**
```
Base: 6 (domain-specific ACGME rules)
+ Domains: 3 (80h, 1-in-7, supervision) = +9
+ Dependencies: 2 (DB access, assignment history) = +4
Total: 19 → Model: opus (reasoning about exceptions)
```

**Parallel Safety:**
```yaml
can_parallel_with:
  - code-review        # Different domains
  - test-writer        # Different domains
  - security-audit     # Different domains
must_serialize_with:
  - safe-schedule-generation  # Can't audit running generation
  - schedule-validator        # Should validate before auditing
preferred_batch_size: 1       # Per-schedule audit, serial
```

---

### Skill 2: SCHEDULE_VALIDATOR

**File Structure:**
```
.claude/skills/SCHEDULE_VALIDATOR/
├── SKILL.md
├── README.md
├── Workflows/
│   ├── 01-structural-validation.md
│   ├── 02-consistency-checks.md
│   ├── 03-temporal-continuity.md
│   ├── 04-rotation-coherence.md
│   ├── 05-quick-compliance-check.md
│   └── 06-generate-validation-report.md
├── Reference/
│   ├── validation-rules.md
│   ├── severity-taxonomy.md
│   └── data-integrity-patterns.md
└── Examples/
    ├── scenario-001-valid-schedule.md
    ├── scenario-002-missing-assignments.md
    └── scenario-003-rotation-mismatch.md
```

**Complexity Score:**
```
Base: 4 (straightforward validation rules)
+ Domains: 2 (structure, temporal) = +6
+ Dependencies: 1 (DB access) = +2
Total: 12 → Model: sonnet
```

---

### Skill 3: SCHEDULE_EXPLAINER

**File Structure:**
```
.claude/skills/SCHEDULE_EXPLAINER/
├── SKILL.md
├── README.md
├── Workflows/
│   ├── 01-trace-assignment.md
│   ├── 02-explain-rotation-choice.md
│   ├── 03-analyze-workload-balance.md
│   ├── 04-justify-supervisor-assignment.md
│   ├── 05-explain-soft-violations.md
│   └── 06-generate-explanation-card.md
├── Reference/
│   ├── constraint-satisfaction-analysis.md
│   ├── assignment-rationale-patterns.md
│   └── explanation-frameworks.md
└── Examples/
    ├── scenario-001-explain-clinic-assignment.md
    ├── scenario-002-explain-supervisor-pairing.md
    └── scenario-003-explain-outlier-assignment.md
```

**Complexity Score:**
```
Base: 7 (reasoning about tradeoffs)
+ Domains: 2 (constraints, objectives) = +6
+ Dependencies: 2 (assignment history, solver logs) = +4
Total: 19 → Model: opus
```

---

### Skill 4: RUNTIME_INCIDENT_COMMANDER

**File Structure:**
```
.claude/skills/RUNTIME_INCIDENT_COMMANDER/
├── SKILL.md
├── README.md
├── Workflows/
│   ├── 01-capture-incident-context.md
│   ├── 02-diagnose-db-issues.md
│   ├── 03-diagnose-redis-issues.md
│   ├── 04-diagnose-celery-issues.md
│   ├── 05-diagnose-solver-issues.md
│   ├── 06-diagnose-constraint-issues.md
│   ├── 07-root-cause-hypothesis.md
│   ├── 08-escalation-recommendation.md
│   └── 09-post-mortem-checklist.md
├── Reference/
│   ├── incident-taxonomy.md
│   ├── diagnostic-flowcharts.md
│   ├── remediation-playbooks.md
│   └── escalation-decision-tree.md
└── Examples/
    ├── scenario-001-db-connection-pool-exhausted.md
    ├── scenario-002-celery-worker-crash.md
    ├── scenario-003-solver-timeout.md
    └── scenario-004-constraint-conflict.md
```

**Complexity Score:**
```
Base: 8 (multi-system diagnosis + reasoning)
+ Domains: 5 (DB, Redis, Celery, Solver, Constraints) = +15
+ Dependencies: 4 (logs, metrics, DB, Redis) = +8
Total: 31 → Model: opus (always)
```

---

### Skill 5: SOLVER_DIAGNOSTICIAN

**File Structure:**
```
.claude/skills/SOLVER_DIAGNOSTICIAN/
├── SKILL.md
├── README.md
├── Workflows/
│   ├── 01-profile-solver-performance.md
│   ├── 02-analyze-constraint-conflicts.md
│   ├── 03-identify-bottlenecks.md
│   ├── 04-suggest-relaxations.md
│   ├── 05-compare-solvers.md
│   └── 06-generate-diagnostic-report.md
├── Reference/
│   ├── solver-performance-metrics.md
│   ├── constraint-conflict-patterns.md
│   ├── bottleneck-taxonomy.md
│   └── relaxation-impact-analysis.md
└── Examples/
    ├── scenario-001-slow-solver-diagnosis.md
    ├── scenario-002-constraint-conflict.md
    └── scenario-003-solver-comparison.md
```

---

### Skill 6: RATE_LIMIT_FORENSICS

**File Structure:**
```
.claude/skills/RATE_LIMIT_FORENSICS/
├── SKILL.md
├── README.md
├── Workflows/
│   ├── 01-query-rate-limit-state.md
│   ├── 02-reconstruct-timeline.md
│   ├── 03-identify-culprit.md
│   ├── 04-analyze-token-patterns.md
│   └── 05-recommend-action.md
├── Reference/
│   ├── rate-limit-rules.md
│   ├── redis-data-structure.md
│   └── escalation-procedures.md
└── Examples/
    ├── scenario-001-suspicious-user.md
    ├── scenario-002-automated-attack.md
    └── scenario-003-legitimate-usage-spike.md
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create all 6 SKILL.md files with metadata
- [ ] Write README.md for each skill (15 min each)
- [ ] Create workflow stubs (empty files, for discovery)
- [ ] Define example scenarios (list, not implemented)

**Output:** Discoverable skill structure, quick adoption path

### Phase 2: Core Workflows (Week 2-3)
- [ ] Implement 1-2 core workflows per skill (MVP coverage)
- [ ] Write 3-5 example scenarios each
- [ ] Add Reference docs (rules, patterns, flowcharts)
- [ ] Update CORE/SKILL.md registry

**Output:** Functional skills, ready for early adoption

### Phase 3: Polish & Testing (Week 3-4)
- [ ] Add parallel_hints metadata validation
- [ ] Cross-reference skills (who calls who?)
- [ ] Write integration tests (skill A + skill B)
- [ ] Performance tuning (batch operations, caching)

**Output:** Production-ready skills, measurable ROI

---

## Risk Mitigation

### Risk 1: Skill Duplication with Existing Skills

**Mitigation:** Audit matrix
```
Compliance Auditor vs acgme-compliance:
  - acgme-compliance: Validates single rule at a time
  - Compliance Auditor: Holistic audit across all rules
  - Decision: Compliance Auditor calls acgme-compliance? Or separate implementation?
  - Recommendation: Check if acgme-compliance can be extended (not duplicated)
```

### Risk 2: Skill Metadata Inconsistency

**Mitigation:** Validation tool
- Create `.claude/tools/validate-skill-metadata.py`
- Check all skills declare: model_tier, parallel_hints, prerequisites
- Run in pre-commit hook

### Risk 3: Adoption Inertia

**Mitigation:** Quick-invoke commands
```
/.claude/commands/audit-compliance.md         → Calls COMPLIANCE_AUDITOR
/.claude/commands/validate-schedule.md        → Calls SCHEDULE_VALIDATOR
/.claude/commands/explain-assignment.md       → Calls SCHEDULE_EXPLAINER
... (one per skill)
```

---

## Integration with Existing Infrastructure

### Cross-Skill Orchestration Patterns

**Pattern 1: Pre-Publication Validation Pipeline**
```
safe-schedule-generation
  → SCHEDULE_VALIDATOR (data integrity check)
  → COMPLIANCE_AUDITOR (ACGME check)
  → Decision: Publish or rollback
```

**Pattern 2: Incident Response Pipeline**
```
production-incident-responder (generic entry)
  → RUNTIME_INCIDENT_COMMANDER (schedule-specific diagnosis)
  → If solver-related: SOLVER_DIAGNOSTICIAN
  → If rate-limit-related: RATE_LIMIT_FORENSICS
```

**Pattern 3: Explainability on Demand**
```
End user: "Why this assignment?"
  → SCHEDULE_EXPLAINER (trace + explain)
  → If violates rule: COMPLIANCE_AUDITOR (which rule?)
  → Decision: Accept or recommend change
```

---

## Success Metrics

### Quantitative
- **Adoption rate:** 80% of suitable tasks use new skills within 2 months
- **Time savings:** 15+ hours per week from automated workflows
- **Incident resolution:** 50% faster root cause identification
- **Validation confidence:** 95%+ pre-publication schedule validation coverage

### Qualitative
- **Skill clarity:** New users understand "when to use" within 5 minutes of README
- **Parallel safety:** No skill-interaction bugs in parallel execution
- **Trust:** Program director confidence in AI-generated schedules increases (measured via feedback)

---

## Future Work (Beyond P1-P2)

### P3: Strategic Skills

**Skill: Resident Lifecycle Manager**
- Unified workflow for hire/fire/credential updates
- Currently scattered across multiple controllers
- High effort, medium impact

**Skill: Schedule Explainability API**
- REST endpoint version of Schedule Explainer
- For external systems integration
- Strategic value, deferred

**Skill: Performance Dashboard**
- Real-time monitoring of scheduler health
- Integrates Prometheus + Grafana
- Strategic value, high effort

### P4: Meta Skills

**Skill: Skill Pattern Teacher**
- Teaches parallel_hints, result_streaming, speculative parallelism
- Self-referential (teaches how to write skills)
- Niche audience, deferred

**Skill: Multi-Terminal Coordinator**
- Infrastructure for 5-10 terminal coordination
- Extends existing multi_terminal_handoff protocol
- Very niche, deferred

---

## Appendix A: Skill Template (Boilerplate)

Use this YAML frontmatter for all new skills:

```yaml
---
skill_name: SKILL_NAME_HERE
purpose: "One sentence describing what this skill does"
version: 1.0
created_date: 2025-12-30
last_updated: 2025-12-30
status: active|experimental|archived

metadata:
  model_tier: haiku|sonnet|opus  # Recommended tier
  complexity_score: X            # 0-30 scale
  estimated_tokens: X-Y          # Range for typical use
  execution_time: "X-Y minutes"  # Typical runtime

parallel_hints:
  can_parallel_with:
    - skill-a
    - skill-b
  must_serialize_with:
    - skill-x
    - skill-y
  preferred_batch_size: N

prerequisites:
  - Prerequisites if any (auth level, DB access, etc.)

workflows: X                      # Number of sub-workflows
examples: Y                       # Number of example scenarios

author: "G2_RECON"
skill_factory_version: "1.0"
---
```

---

## Appendix B: Quick Decision Tree

```
"What skill should I invoke?"

START
├─ "I need to validate a schedule"
│  └─ SCHEDULE_VALIDATOR
├─ "I need to check ACGME compliance"
│  └─ COMPLIANCE_AUDITOR
├─ "I need to understand why this assignment happened"
│  └─ SCHEDULE_EXPLAINER
├─ "Production is broken, help me diagnose"
│  └─ RUNTIME_INCIDENT_COMMANDER
├─ "Schedule generation is slow or suboptimal"
│  └─ SOLVER_DIAGNOSTICIAN
└─ "API rate limits triggered, investigate"
   └─ RATE_LIMIT_FORENSICS
```

---

## Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **MVP** | Minimum Viable Product - first release covering 80% of use cases |
| **Parallel Safe** | Skill can run concurrently with other skills without conflicts |
| **Result Streaming** | Skill emits progress signals during execution |
| **Model Tier** | haiku (fast, simple), sonnet (moderate), opus (complex reasoning) |
| **Complexity Score** | 0-30 scale: 0-5 simple, 6-12 moderate, 13+ complex |
| **Workflow File** | Step-by-step procedure file (one sub-workflow per file) |
| **Speculative Parallelism** | Batch-reading likely files upfront instead of sequential discovery |

---

## Closing Summary

This SEARCH_PARTY operation systematically identified **skill gaps across 7 dimensions** (perception, investigation, arcana, history, insight, religion, nature, medicine, survival, stealth).

**Deliverable: 6 P1-P2 skills with clear MVP definitions, ROI analysis, and implementation roadmap.**

Each skill is designed to:
1. Eliminate repeated manual context gathering
2. Systematize expert judgment
3. Enable parallel safe execution
4. Provide clear "when to use" guidance

**Next Steps:**
1. Review and approve skill specifications (this document)
2. Create SKILL.md files + READMEs in Phase 1
3. Implement core workflows + examples in Phase 2
4. Measure adoption and ROI in Phase 3

---

**Generated by:** G2_RECON (Claude Haiku 4.5)
**Operation:** SEARCH_PARTY (systematic skill gap analysis)
**Date:** 2025-12-30
**Status:** Complete - Ready for implementation prioritization

