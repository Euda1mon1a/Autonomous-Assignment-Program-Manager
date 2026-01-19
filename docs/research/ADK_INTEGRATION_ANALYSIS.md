# Comprehensive ADK Analysis: Skills Integration Strategy

> **Date:** 2026-01-19
> **Source:** PLAN_PARTY (10 probes) analysis of `docs/research/google-adk-typescript-exploration.md`
> **Authority:** Single source for ADK integration decisions
> **Reference:** [`docs/MASTER_PRIORITY_LIST.md`](../MASTER_PRIORITY_LIST.md)

---

## Executive Summary

Google's Agent Development Kit (ADK) for TypeScript offers significant capabilities that both overlap and complement our existing MCP-based agent infrastructure. After deploying 10 PLAN_PARTY probes analyzing the ADK exploration document against our 90-skill ecosystem, this document provides a **complete disposition matrix** for skill integration decisions.

**Key Strategic Finding:** ADK's strongest value proposition is **systematic agent evaluation** (tool trajectory scoring, semantic equivalence, safety checks), NOT agent runtime replacement. Our MCP infrastructure is mature, HIPAA-compliant, and deeply integrated. ADK patterns should be **extracted and adapted**, not wholesale adopted.

---

## Reference Context

### MASTER_PRIORITY_LIST.md Alignment

| Priority Item | ADK Relevance | Impact |
|--------------|---------------|--------|
| **#8 MCP Tool Placeholders** | ADK evaluation could validate MCP tool accuracy | MEDIUM |
| **#10 ACGME Compliance Gaps** | ADK safety evaluation patterns applicable | HIGH |
| **#6 Orphan Framework Code** | gRPC/EventBus could coordinate with ADK evaluation | LOW |
| **#9 GUI Mock Data** | ADK tools wrap same backend APIs | LOW |

### Current Infrastructure

| Component | Count | Maturity | ADK Interaction |
|-----------|-------|----------|-----------------|
| MCP Tools | 34+ | Production | Tools wrap same APIs as ADK |
| Skills | 90 | Documented | Evaluation patterns applicable |
| Agents | 8 types | Spawnable | ADK agents parallel, not replace |
| RAG Chunks | 67+ | Indexed | ADK docs can be indexed |

---

## PLAN_PARTY Probe Results

### Probe 1: CRITICAL_PATH
**Finding:** ADK evaluation framework is the critical value add. Agent runtime is redundant.
- 825 lines estimated for evaluation-only integration
- 6-day implementation timeline
- **Recommendation:** Extract evaluation patterns only

### Probe 2: RISK_MINIMAL
**Finding:** Project is migrating AWAY from ADK toward Claude SDK. Dual-agent complexity is risky.
- HIPAA/BAA concerns for Gemini in healthcare context
- Python MCP + TypeScript ADK = maintenance burden
- **Recommendation:** NO full ADK adoption; evaluation-only or defer

### Probe 3: PARALLEL_MAX
**Finding:** 6 parallel workstreams identified for ADK integration.
- Evaluation framework (standalone)
- Tool schema conversion (Pydantic to Zod)
- Agent bridge (MCP to ADK)
- Safety evaluation module
- Trajectory analyzer
- Response matcher
- **Recommendation:** Parallel development possible but scope carefully

### Probe 4: RESOURCE_MIN
**Finding:** Minimal viable integration requires only 3 new skills.
- `adk-agent-bridge` (ADK to MCP orchestration)
- `adk-evaluation` (systematic agent testing)
- `gemini-model-router` (optional model fallback)
- Total: ~825 lines
- **Recommendation:** Lean approach, 3 skills maximum

### Probe 5: QUALITY_GATE
**Finding:** ADK evaluation framework design is production-ready.
- Tool trajectory scoring (exact, in_order, any_order match modes)
- Response match scoring (ROUGE metric, 80% threshold)
- Semantic equivalence (LLM-as-judge)
- Safety evaluation (Vertex AI General AI Eval SDK)
- **Recommendation:** Adopt evaluation patterns, not runtime

### Probe 6: INCREMENTAL
**Finding:** 3-increment progressive adoption with feature flags.
- Increment 1: Evaluation framework only (no Gemini calls)
- Increment 2: Gemini for non-PHI tasks (code review, docs)
- Increment 3: Hybrid orchestration (post-BAA if applicable)
- **Recommendation:** Feature-flagged rollout, evaluation first

### Probe 7: DOMAIN_EXPERT
**Finding:** COORD_TOOLING owns ADK (80%), COORD_FRONTEND supports (15%).
- TypeScript skills owned by COORD_FRONTEND
- Evaluation framework owned by COORD_TOOLING
- Backend integration owned by COORD_PLATFORM
- **Recommendation:** Clear ownership boundaries

### Probe 8: PRECEDENT
**Finding:** Existing patterns from skill-factory, agent-factory, MCP integration applicable.
- `skill-factory` pattern for creating ADK skills
- `spawn-agent` pattern for ADK agent lifecycle
- MCP tool wrapping pattern for ADK to backend
- **Recommendation:** Follow established patterns, don't reinvent

### Probe 9: ADVERSARIAL
**Finding:** 15 critical risks identified.
1. Dual-agent complexity (Python + TypeScript)
2. HIPAA/BAA concerns for Gemini
3. Secret sprawl (3 new credential types)
4. Schema drift (Pydantic to Zod)
5. Test infrastructure duplication
6. Model cost uncertainty (Gemini pricing)
7. Latency increase (additional API calls)
8. Error surface expansion
9. Debugging complexity
10. Documentation maintenance burden
11. Onboarding complexity for new agents
12. Dependency management (npm + pip)
13. CI/CD pipeline expansion
14. Monitoring/observability gaps
15. Rollback complexity for hybrid failures
- **Recommendation:** DELAY full ADK adoption; evaluation patterns only

### Probe 10: SYNTHESIS
**Finding:** 70-20-10 hybrid strategy recommended.
- 70% MCP for domain-specific scheduling/compliance
- 20% ADK evaluation for systematic testing
- 10% Gemini for post-production learning (non-PHI)
- **Recommendation:** Hybrid approach with clear boundaries

---

## Current agent-adk Implementation

The `agent-adk/` directory already contains a working prototype:

### Structure
```
agent-adk/
├── src/
│   ├── agents/
│   │   └── schedule-agent.ts    # 2 agents: ScheduleAssistant, ComplianceChecker
│   ├── tools/
│   │   └── schedule-tools.ts    # 5 tools wrapping backend API
│   └── evaluation/
│       ├── criteria.ts          # Tool trajectory + response match scoring
│       └── test-cases.ts        # 10 test cases across 4 categories
├── tests/
│   └── agent.eval.test.ts       # Vitest evaluation test suite
└── package.json                 # @google/adk ^0.2.0, zod ^3.23.0
```

### Existing Agents
| Agent | Model | Purpose |
|-------|-------|---------|
| ScheduleAssistant | gemini-2.5-flash | General scheduling, ACGME compliance, swaps |
| ComplianceChecker | gemini-2.5-flash | Deep ACGME analysis (80-hour, 1-in-7, supervision) |

### Existing Tools
| Tool | Backend Endpoint | Status |
|------|------------------|--------|
| get_schedule | GET /schedules/{id} | Working |
| validate_acgme_compliance | POST /compliance/validate | Working |
| find_swap_matches | POST /swap/matches | Working |
| check_utilization | GET /resilience/utilization | Working |
| run_contingency_analysis | POST /resilience/contingency | Working |

### Existing Evaluation Framework
| Metric | Threshold | Mode |
|--------|-----------|------|
| Tool Trajectory Score | 0.9 (90%) | exact, contains, any |
| Response Match Score | 0.8 (80%) | ROUGE-based |

---

## Skills Disposition Matrix

### Tier 1: INCORPORATE IMMEDIATELY

These capabilities should be adopted in the next sprint. They are proven patterns, low-risk, and high-value.

| Capability | Source | Action | Effort | Rationale |
|------------|--------|--------|--------|-----------|
| **Tool Trajectory Scoring** | ADK evaluation/criteria.ts | Extract to `agent-evaluation` skill | 2-3 days | Systematic agent testing, no Gemini dependency |
| **Response Match Scoring** | ADK evaluation/criteria.ts | Add to `code-review` skill | 1-2 days | ROUGE-based quality metrics |
| **Test Case Framework** | ADK evaluation/test-cases.ts | Extend `test-scenario-framework` | 2-3 days | 10 test case patterns ready |
| **Zod Schema Patterns** | ADK tools/schedule-tools.ts | Document for TypeScript skills | 1 day | Type-safe tool definitions |
| **Evaluation Criteria YAML** | New pattern | Add to skill metadata | 1 day | Standardized pass/fail thresholds |

**Total Effort: 7-10 days**

### Tier 2: UPON FURTHER REVIEW

These capabilities require additional investigation, architectural decisions, or external factors before adoption.

| Capability | Source | Blocking Question | Review Criteria |
|------------|--------|-------------------|-----------------|
| **Gemini Model Router** | ADK + Vertex AI | HIPAA/BAA status for healthcare data? | Requires legal/compliance review |
| **Multi-Agent Orchestration** | ADK Runner/Session | Does Claude SDK roadmap obsolete this? | Wait for Anthropic Q1 2026 announcements |
| **Semantic Equivalence (LLM-as-judge)** | ADK evaluation | Which judge model (Claude vs Gemini)? | Cost/accuracy analysis needed |
| **Safety Evaluation** | Vertex AI General AI Eval SDK | Enterprise licensing required? | Procurement review |
| **TypeScript Agent Layer** | ADK proposed structure | Frontend team capacity? | COORD_FRONTEND availability |
| **Hybrid Python/TypeScript Bridge** | Integration pattern | Maintenance burden acceptable? | 6-month cost projection |
| **FunctionTool Migration** | FastMCP to ADK | Performance regression risk? | Benchmark comparison |
| **Cloud Run Deployment** | ADK production path | GCP vs AWS alignment? | Infrastructure strategy review |

**Review Timeline: Q1 2026 (after Anthropic SDK roadmap clarity)**

### Tier 3: UNLIKELY TO BE HELPFUL

These capabilities are redundant, risky, or misaligned with project direction. They should be skipped unless circumstances change.

| Capability | Source | Reason to Skip | Circumstance to Revisit |
|------------|--------|----------------|-------------------------|
| **Full Gemini Agent Runtime** | ADK agents/ | HIPAA/BAA concerns, Claude SDK direction | GCP signs healthcare BAA |
| **Complete TypeScript Migration** | ADK proposal | Python backend, dual-runtime complexity | Complete frontend rewrite approved |
| **Vertex AI Enterprise Deployment** | ADK production | Enterprise licensing, GCP lock-in | Organization standardizes on GCP |
| **Tool Registry Duplication** | ADK proposal | MCP tools already comprehensive (34+) | Tool count exceeds 100 |
| **Evaluation Dashboard UI** | Potential feature | Not core scheduling functionality | Product requests analytics |
| **gRPC ADK Bridge** | Orphan framework | gRPC unused, complexity overhead | High-frequency agent communication needed |
| **n8n ADK Integration** | Workflow expansion | ChatOps working, additional integration | n8n deprecation |
| **ADK CLI Mode** | npm run cli | MCP CLI already functional | Developer experience feedback |

---

## Gemini Post-Production Learning Uses

Since MCP is available to all agents, Gemini can be leveraged for **post-production learning** scenarios where PHI is not involved:

### Sanctioned Uses (No PHI, Post-Production)

| Use Case | Data Type | Gemini Model | MCP Bridge |
|----------|-----------|--------------|------------|
| **Code Review Analysis** | Source code (no config secrets) | gemini-2.5-flash | N/A (direct) |
| **Documentation Generation** | Technical specs | gemini-2.5-pro | `rag_search` for context |
| **Test Case Generation** | Schema definitions | gemini-2.5-flash | `validate_schedule_tool` for validation |
| **Pattern Recognition** | Anonymized metrics | gemini-2.5-pro | `analyze_swap_candidates_tool` patterns |
| **Skill Optimization** | Skill usage telemetry | gemini-2.5-flash | N/A (analytics only) |
| **Error Classification** | Sanitized stack traces | gemini-2.5-flash | `check_circuit_breakers_tool` correlation |

### Prohibited Uses (PHI Risk)

| Use Case | Risk | Alternative |
|----------|------|-------------|
| Schedule generation | Contains resident names/assignments | MCP tools + Claude |
| ACGME validation | Contains work hours by individual | MCP tools + Claude |
| Swap recommendations | Contains personnel preferences | MCP tools + Claude |
| Resilience analysis with names | Contains individual coverage gaps | MCP tools + Claude |
| Leave/absence processing | Contains deployment/TDY data | MCP tools + Claude |

### Implementation Pattern

```typescript
// Post-production learning example (no PHI)
const learningResult = await geminiModel.generateContent({
  contents: [{
    role: 'user',
    parts: [{
      text: `Analyze these anonymized scheduling patterns for optimization opportunities:
             ${JSON.stringify(anonymizedPatterns)}`
    }]
  }]
});

// Feed insights back to MCP for validation
const mcpValidation = await mcp_validate_schedule_tool({
  optimizations: learningResult.suggestions,
  validateOnly: true
});
```

---

## MCP Availability Matrix

All agents have access to MCP tools. This table shows which ADK capabilities are **redundant** vs **additive**:

| ADK Capability | MCP Equivalent | Verdict |
|----------------|----------------|---------|
| get_schedule | `validate_schedule_by_id_tool` | REDUNDANT |
| validate_acgme_compliance | `validate_schedule_tool` | REDUNDANT |
| find_swap_matches | `analyze_swap_candidates_tool` | REDUNDANT |
| check_utilization | `check_utilization_threshold_tool` | REDUNDANT |
| run_contingency_analysis | `run_contingency_analysis_tool` | REDUNDANT |
| Tool Trajectory Scoring | No equivalent | **ADDITIVE** |
| Response Match Scoring | No equivalent | **ADDITIVE** |
| Semantic Equivalence | No equivalent | **ADDITIVE** |
| Safety Evaluation | Partial (`check_mtf_compliance_tool`) | **ADDITIVE** |
| Evaluation Test Framework | `test-scenario-framework` skill | OVERLAPPING |

**Conclusion:** ADK tools are redundant; ADK evaluation patterns are additive.

---

## New Skills Recommended

Based on Tier 1 analysis, these skills should be created:

### 1. `agent-evaluation` (NEW - P1)

**Purpose:** Systematic agent output scoring using ADK evaluation patterns

**Structure:**
```yaml
name: agent-evaluation
description: Score agent outputs using tool trajectory and response match metrics
model_tier: any
triggers:
  - "evaluate agent"
  - "score agent output"
  - "trajectory analysis"
evaluation_metrics:
  tool_trajectory_score:
    threshold: 0.9
    modes: [exact, in_order, any_order]
  response_match_score:
    threshold: 0.8
    penalty_per_forbidden: 0.2
```

**Effort:** 2-3 days
**Owner:** COORD_TOOLING

### 2. `trajectory-analyzer` (NEW - P2)

**Purpose:** Tool call sequence validation and optimization

**Structure:**
```yaml
name: trajectory-analyzer
description: Validate tool call sequences against expected patterns
model_tier: haiku
triggers:
  - "analyze trajectory"
  - "tool sequence check"
  - "call pattern validation"
```

**Effort:** 2 days
**Owner:** COORD_TOOLING

### 3. `response-matcher` (NEW - P3)

**Purpose:** Semantic equivalence checking for agent outputs

**Structure:**
```yaml
name: response-matcher
description: Compare agent responses for semantic equivalence
model_tier: sonnet
triggers:
  - "match response"
  - "semantic comparison"
  - "output equivalence"
```

**Effort:** 1-2 days
**Owner:** COORD_TOOLING

---

## Existing Skills to Enhance

### `code-review` (UPGRADE)

**Current:** Security, performance, quality checks
**Enhancement:** Add ADK response match scoring for review quality
**Effort:** 1-2 days

### `test-scenario-framework` (UPGRADE)

**Current:** 20+ pre-built scenarios
**Enhancement:** Add tool trajectory evaluation to scenario validation
**Effort:** 2-3 days

### `systematic-debugger` (UPGRADE)

**Current:** Explore-plan-debug-fix workflow
**Enhancement:** Add step-by-step evaluation tracing
**Effort:** 1-2 days

---

## Implementation Roadmap

### Phase 1: Evaluation Framework (Week 1-2)

| Task | Owner | Days | Dependency |
|------|-------|------|------------|
| Extract ADK evaluation criteria | COORD_TOOLING | 1 | None |
| Create `agent-evaluation` skill | COORD_TOOLING | 3 | Criteria extraction |
| Add evaluation_metrics to skill YAML schema | COORD_TOOLING | 1 | None |
| Upgrade `test-scenario-framework` | COORD_TOOLING | 3 | `agent-evaluation` |
| Documentation and RAG indexing | COORD_OPS | 1 | All above |

### Phase 2: Skill Upgrades (Week 3)

| Task | Owner | Days | Dependency |
|------|-------|------|------------|
| Upgrade `code-review` with response scoring | COORD_TOOLING | 2 | Phase 1 |
| Upgrade `systematic-debugger` with tracing | COORD_TOOLING | 2 | Phase 1 |
| Create `trajectory-analyzer` skill | COORD_TOOLING | 2 | Phase 1 |

### Phase 3: Post-Production Learning (Week 4+)

| Task | Owner | Days | Dependency |
|------|-------|------|------------|
| Define sanctioned Gemini use cases | COORD_PLATFORM | 1 | Compliance review |
| Create anonymization utilities | COORD_PLATFORM | 2 | Use case approval |
| Implement learning feedback loop | COORD_TOOLING | 3 | Anonymization |
| Create `response-matcher` skill | COORD_TOOLING | 2 | Phase 2 |

---

## Risk Mitigations

| Risk | Mitigation | Owner |
|------|------------|-------|
| HIPAA/PHI exposure via Gemini | Strict sanctioned use list, anonymization required | COORD_PLATFORM |
| Dual-runtime complexity | Evaluation patterns only, no TypeScript runtime | COORD_TOOLING |
| Schema drift (Pydantic to Zod) | Extract patterns, don't port implementations | COORD_TOOLING |
| Secret sprawl | No new credential types in Phase 1 | COORD_OPS |
| Test infrastructure duplication | Extend existing test-scenario-framework | COORD_TOOLING |
| Model cost uncertainty | Gemini only for post-production learning | COORD_PLATFORM |

---

## Verification Checklist

```bash
# After Phase 1
ls -la .claude/skills/agent-evaluation/SKILL.md
grep "evaluation_metrics" .claude/skills/*/SKILL.md | wc -l
# Expected: 3+ skills with evaluation_metrics

# After Phase 2
grep "trajectory" .claude/skills/test-scenario-framework/SKILL.md
grep "response_match" .claude/skills/code-review/SKILL.md

# After Phase 3
grep "gemini" .claude/skills/*/SKILL.md | wc -l
# Expected: 0-1 (minimal Gemini references, post-production only)
```

---

## Decision Summary

| Decision | Rationale |
|----------|-----------|
| **Extract evaluation patterns, not runtime** | MCP already comprehensive; ADK adds testing value |
| **3 new skills maximum** | RESOURCE_MIN probe recommendation |
| **Gemini for post-production learning only** | HIPAA/BAA concerns, Claude SDK primary |
| **COORD_TOOLING ownership** | 80% of ADK work is evaluation/tooling |
| **Feature-flagged rollout** | INCREMENTAL probe recommendation |
| **No full TypeScript migration** | Python backend, dual-runtime complexity |

---

## Files to Create

| File | Purpose | Priority |
|------|---------|----------|
| `.claude/skills/agent-evaluation/SKILL.md` | Tool trajectory + response match scoring | P1 |
| `.claude/skills/trajectory-analyzer/SKILL.md` | Tool call sequence validation | P2 |
| `.claude/skills/response-matcher/SKILL.md` | Semantic equivalence checking | P3 |

## Files to Update

| File | Change | Priority |
|------|--------|----------|
| `.claude/skills/code-review/SKILL.md` | Add response match scoring | P2 |
| `.claude/skills/test-scenario-framework/SKILL.md` | Add trajectory evaluation | P2 |
| `.claude/skills/systematic-debugger/SKILL.md` | Add evaluation tracing | P3 |
| `docs/MASTER_PRIORITY_LIST.md` | Add ADK integration as tracked item | P1 |

---

*This analysis synthesizes 10 PLAN_PARTY probe results against 90 existing skills and the Google ADK TypeScript exploration document. It provides a complete disposition matrix for ADK integration decisions aligned with MASTER_PRIORITY_LIST.md priorities.*
