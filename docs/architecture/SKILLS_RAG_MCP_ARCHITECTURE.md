# Skills, RAG, and MCP Tools: Architecture Decision

**Last Updated:** 2026-01-22
**Status:** Decision Pending
**Owner:** Program Director

---

## Executive Summary

We have three overlapping mechanisms for AI knowledge/capability:

| Mechanism | What It Does | Context Cost | Reliability |
|-----------|--------------|--------------|-------------|
| **Skills** | Load full knowledge docs into context | HIGH (5-50K tokens) | 100% complete |
| **RAG** | Search & retrieve relevant chunks | LOW (500-2K tokens) | May miss things |
| **MCP Tools** | Execute logic, return results | MINIMAL | Deterministic |

**Decision needed:** Which skills should be wrapped as MCP tools to reduce context usage while maintaining reliability?

---

## How Each Works

### Skills (Current: 90+ skills)

**Location:** `.claude/skills/*/SKILL.md`

**Mechanism:**
```
User: /tamc-excel-scheduling
→ Full 43KB markdown loaded into Claude's context
→ Claude now "knows" all rotation patterns, faculty caps, edge cases
```

**Pros:**
- Guaranteed complete knowledge
- Preserves structure (workflows, checklists)
- Examples and patterns intact
- No retrieval failures

**Cons:**
- Uses significant context (5-50K tokens per skill)
- Multiple skills = context exhaustion
- Redundant loads if same skill needed repeatedly

---

### RAG (Current: 67+ documents indexed)

**Mechanism:**
```
Claude: rag_search("LDNF clinic day")
→ Semantic search over knowledge base
→ Returns top-k relevant chunks (~500-2000 tokens)
```

**Pros:**
- Low context cost
- Scales to large knowledge bases
- Good for fact lookups

**Cons:**
- May miss relevant info (retrieval failure)
- Loses document structure
- Query quality affects results
- Chunks may lack context

---

### MCP Tools (Current: 34+ tools)

**Mechanism:**
```
Claude: mcp__residency-scheduler__validate_schedule_tool(...)
→ Executes Python code on backend
→ Returns structured result
```

**Pros:**
- Zero context for logic (code lives in backend)
- Deterministic execution
- Can access database, external services
- Cacheable, testable

**Cons:**
- Requires implementation effort
- Logic changes need deployment
- Less flexible than natural language

---

## The Overlap Problem

```
┌─────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE SOURCES                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   SKILLS              RAG                 MCP TOOLS          │
│   ┌─────────┐        ┌─────────┐         ┌─────────┐        │
│   │ Full    │        │ Chunks  │         │ Encoded │        │
│   │ Docs    │◄──────►│ from    │◄───────►│ Logic   │        │
│   │         │        │ Docs    │         │         │        │
│   └─────────┘        └─────────┘         └─────────┘        │
│       │                   │                   │              │
│       │         OVERLAP ZONE                  │              │
│       │    ┌──────────────────────┐          │              │
│       └───►│  Same knowledge in   │◄─────────┘              │
│            │  3 different forms   │                          │
│            └──────────────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Example: ACGME Compliance**
- `/acgme-compliance` skill = 600 lines of rules
- RAG has those rules indexed
- `validate_schedule_tool` encodes same rules in Python

**Current state:** All three exist, somewhat redundant.

---

## Decision Framework: When to Wrap a Skill as MCP Tool

### Wrap as MCP Tool When:

| Criterion | Rationale |
|-----------|-----------|
| **Logic is deterministic** | Rules don't need interpretation |
| **Frequently called** | Amortize implementation cost |
| **High context cost** | Save tokens for other things |
| **Needs DB access** | MCP can query, skills can't |
| **Validation/checking** | Pass/fail is computable |
| **Output is structured** | JSON > natural language |

### Keep as Skill When:

| Criterion | Rationale |
|-----------|-----------|
| **Teaching patterns** | Examples need full context |
| **Complex workflows** | Multi-phase guidance |
| **Judgment required** | Can't encode in code |
| **Rarely used** | Not worth implementation |
| **Rapidly evolving** | Markdown easier to update |
| **Human-facing output** | Natural language needed |

---

## Skill-to-MCP Wrapping Candidates

### Tier 1: High Priority (Wrap Soon)

| Skill | Current Size | MCP Tool Candidate | Rationale |
|-------|--------------|-------------------|-----------|
| `/acgme-compliance` | 15KB | `validate_acgme_rules` | Deterministic rule checking |
| `/schedule-validator` | 8KB | `validate_schedule_comprehensive` | Structured validation |
| `/constraint-preflight` | 12KB | `verify_constraint_registration` | Checklist is automatable |
| `/swap-analyzer` | 6KB | `analyze_swap_safety` | Compatibility is computable |

### Tier 2: Medium Priority (Consider)

| Skill | Current Size | MCP Tool Candidate | Rationale |
|-------|--------------|-------------------|-----------|
| `/tamc-cpsat-constraints` | 20KB | `get_constraint_definition` | Lookup specific constraints |
| `/rosetta-stone` | 8KB | `translate_format` | Field mappings are fixed |
| `/safe-schedule-generation` | 10KB | `preflight_check` | Checklist automatable |

### Tier 3: Keep as Skill (Don't Wrap)

| Skill | Size | Reason to Keep |
|-------|------|----------------|
| `/tamc-excel-scheduling` | 43KB | Complex workflows, many examples |
| `/SCHEDULING` | 10KB | Multi-phase orchestration |
| `/schedule-optimization` | 25KB | Solver debugging needs full context |
| `/swap-management` | 30KB | Emergency protocols need judgment |

---

## Proposed Architecture (Post-Decision)

```
┌─────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LAYER 1: MCP TOOLS (Deterministic)                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ validate_acgme_rules()     - 80hr, 1-in-7, etc.    │    │
│  │ validate_schedule()        - Coverage, conflicts    │    │
│  │ analyze_swap_safety()      - Compatibility check    │    │
│  │ verify_constraints()       - Registration check     │    │
│  │ translate_format()         - xlsx/xml/db mapping    │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↑                                   │
│                     Call first                               │
│                          │                                   │
│  LAYER 2: RAG (Fact Lookup)                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ rag_search("supervision ratio PGY-1")              │    │
│  │ rag_search("FMIT call rules")                      │    │
│  │ rag_search("Block 10 faculty schedule")            │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↑                                   │
│                If MCP doesn't cover it                       │
│                          │                                   │
│  LAYER 3: SKILLS (Full Context)                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ /tamc-excel-scheduling  - Complex workflows        │    │
│  │ /SCHEDULING             - Multi-phase orchestration │    │
│  │ /schedule-optimization  - Solver debugging         │    │
│  │ /swap-management        - Emergency protocols      │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↑                                   │
│              Only when full context needed                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Approach

### Phase 1: Audit (1 week)
- [ ] Inventory all skills with token counts
- [ ] Map skill → existing MCP tool coverage
- [ ] Identify gaps where skill logic isn't in MCP

### Phase 2: Prioritize (Decision meeting)
- [ ] Review Tier 1 candidates
- [ ] Estimate implementation effort
- [ ] Decide which to wrap first

### Phase 3: Implement (Iterative)
- [ ] Wrap highest-value skills as MCP tools
- [ ] Update skills to reference MCP tools
- [ ] Deprecate redundant skill sections

### Phase 4: Optimize (Ongoing)
- [ ] Monitor context usage
- [ ] Track MCP tool call patterns
- [ ] Adjust based on actual usage

---

## Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| Avg context per session | <50K tokens | Prevent exhaustion |
| MCP tool coverage | >80% of validations | Reduce skill loads |
| RAG retrieval accuracy | >90% | Catch gaps |
| Skill loads per session | <3 | Reserve for complex tasks |

---

## Open Questions

1. **Should RAG auto-load skills?** If confidence is low, load full skill?
2. **Skill versioning?** MCP tools need deployment; skills are instant. How to sync?
3. **Hybrid approach?** Skill loads, but delegates to MCP for validation?
4. **Cost tracking?** Can we measure context cost per skill?

---

## Next Steps

1. Add to Master Priority List for decision
2. Schedule architecture review meeting
3. Prototype one Tier 1 wrapping (e.g., constraint-preflight)
4. Measure context savings

---

*This document is for human decision-making. The actual wrapping work will be tracked in MASTER_PRIORITY_LIST.md.*
