# Session 039 Handoff: Mission Command Restructure

> **Date:** 2025-12-31
> **Status:** Ready for Implementation
> **Priority:** High - Architectural restructure of PAI agent hierarchy
> **Archive:** `.claude/dontreadme/archives/AGENT_SCHEMA_PRE_MISSION_COMMAND.md`

---

## Executive Summary

This session designed a **Mission Command** operating model for the PAI agent hierarchy. The goal is to enable "Plan, See, Do" workflow with delegated autonomy rather than rigid micromanagement.

**Key Insight:** If user invokes `/startupO`, they're doing complex work. The system should plan well, observe reality, and adapt - not require approval at every step.

---

## The Problem With Current Structure

1. **Model tiers are inconsistent** - G-Staff at haiku, Coordinators at opus (inverted)
2. **ARCHITECT misplaced** - Strategic role reports to tactical COORD_PLATFORM
3. **No clear command flow** - ORCHESTRATOR → everyone directly
4. **No adaptation mechanism** - Plan is static, no "See" phase

---

## Proposed: Mission Command Model

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **Commander's Intent** | ORCHESTRATOR gives objective, not step-by-step orders |
| **Delegated Autonomy** | Coordinators can spawn specialists without asking |
| **Standing Orders** | Pre-authorized patterns don't need escalation |
| **Escalate When Blocked** | Only surface issues that require strategic pivot |

### New Hierarchy

```
ORCHESTRATOR (opus) ─── Supreme Commander
    │
    ├── ARCHITECT (opus) ─── Deputy for Systems (exception: stays opus)
    │   ├── COORD_PLATFORM (sonnet) → DBA, BACKEND_ENGINEER, API_DEVELOPER
    │   ├── COORD_QUALITY (sonnet) → QA_TESTER, CODE_REVIEWER
    │   └── COORD_ENGINE (sonnet) → SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
    │
    └── SYNTHESIZER (opus) ─── Deputy for Operations (elevated from G-3)
        ├── COORD_OPS (sonnet) → RELEASE_MANAGER, META_UPDATER, TOOLSMITH
        ├── COORD_RESILIENCE (sonnet) → RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR
        ├── COORD_FRONTEND (sonnet) → FRONTEND_ENGINEER, UX_SPECIALIST
        └── COORD_INTEL (sonnet) → (intel specialists)

    G-Staff (Advisory, sonnet) ─── Advisors to ORCHESTRATOR
    │   G-1 PERSONNEL, G-2 RECON, G-4 CONTEXT, G-5 PLANNING, G-6 SIGNAL
    │
    IG (DELEGATION_AUDITOR) ─── Independent Oversight (sonnet)
    PAO (HISTORIAN) ─── Historical Record (sonnet)
```

### Model Tier Assignments

| Tier | Role | Agents |
|------|------|--------|
| **Opus** | Strategic decision-makers | ORCHESTRATOR, ARCHITECT, SYNTHESIZER |
| **Sonnet** | Tactical coordinators + advisors | All COORDs, G-Staff (advisory), IG, PAO |
| **Haiku** | Execution specialists | All specialists under coordinators |

### Key Changes

1. **SYNTHESIZER elevated** to sub-orchestrator (Deputy for Operations)
2. **ARCHITECT elevated** to sub-orchestrator (Deputy for Systems)
3. **G-Staff demoted** to advisory (sonnet) - they inform, don't command
4. **All Coordinators** to sonnet (tactical, not strategic)
5. **All Specialists** to haiku (execution)
6. **ARCHITECT exception** marked - stays opus for irreversible decisions

---

## Plan, See, Do Operating Model

### PLAN Phase

```
User gives intent → ORCHESTRATOR
    → G-5 PLANNING drafts approach (sonnet, advisory)
    → ARCHITECT validates feasibility (opus, if systems-related)
    → Output: Task breakdown with standing orders
```

### SEE Phase (During Execution)

```
Coordinators execute → spawn specialists as needed
    → G-2 RECON gathers intel if needed
    → SYNTHESIZER monitors cross-domain progress
    → Reality differs from plan? → Flag for adaptation
```

### DO Phase

```
If on track → Continue execution
If diverged → Coordinator adapts within authority
If blocked → Escalate to sub-orchestrator or ORCHESTRATOR
```

---

## Standing Orders Concept

Pre-authorized patterns that don't need escalation:

| Coordinator | Standing Orders |
|-------------|-----------------|
| COORD_OPS | Commit, PR, CHANGELOG for completed work |
| COORD_QUALITY | Run tests, lint, block if failing |
| COORD_PLATFORM | Schema changes with migration |
| COORD_ENGINE | Generate schedule with standard constraints |
| COORD_RESILIENCE | Compliance checks, security scans |
| COORD_FRONTEND | Component updates within design system |

### Escalation Triggers

| Escalate When | To Whom |
|---------------|---------|
| Tests failing, can't fix | COORD_QUALITY → ORCHESTRATOR |
| Security-sensitive changes | Any → SECURITY_AUDITOR |
| Architecture decision needed | Any → ARCHITECT |
| Cross-domain conflict | SYNTHESIZER → ORCHESTRATOR |
| Plan is fundamentally wrong | Any → ORCHESTRATOR |

---

## Implementation Steps

### Phase 1: Update Agent Specs

1. Update model tiers in all `.claude/Agents/*.md` files:
   - SYNTHESIZER: haiku → **opus** + mark as sub-orchestrator
   - All G-Staff: various → **sonnet** (advisory role)
   - All COORDs: opus → **sonnet**
   - All Specialists: sonnet → **haiku**
   - ARCHITECT: keep **opus** + add `Exception: true` marker

2. Update HIERARCHY.md with new structure

### Phase 2: Update Delegation Patterns

1. Add standing orders to each Coordinator spec
2. Add escalation triggers to each Coordinator spec
3. Update ORCHESTRATOR.md with Mission Command patterns
4. Update context-aware-delegation skill with new templates

### Phase 3: Test

1. Run a complex multi-domain task
2. Verify chain spawning works (Opus → Sonnet → Haiku)
3. Verify standing orders execute without escalation
4. Verify escalations reach appropriate level

---

## Technical Notes

### Task Tool Chain Spawning

Subagents CAN spawn further subagents:

```
ORCHESTRATOR → Task(COORD_OPS)
    → COORD_OPS uses Task(RELEASE_MANAGER)
        → RELEASE_MANAGER does work
        → Returns to COORD_OPS
    → COORD_OPS returns to ORCHESTRATOR
```

### Standing Orders via Prompt

When spawning, bake in autonomy:

```python
Task(
    model="sonnet",
    prompt="""
    ## Agent: COORD_OPS

    ## Standing Orders (execute without escalation)
    - Commit completed work with conventional format
    - Create PR with summary
    - Update CHANGELOG for user-facing changes

    ## Escalate If
    - Tests failing
    - Merge conflicts
    - Security-sensitive files

    ## Current Mission
    [specific task]
    """
)
```

### Limitations

- **No persistent agents** - each spawn is fresh
- **No automatic triggers** - user must start the chain
- **Context resets** - must pass context explicitly

---

## FIRST PRIORITY: Restore RAG Data

### RAG Database is Empty - Restore from Backup

The RAG vector store has 0 documents. **Backup exists with 62+ embedded chunks.**

**Backup file:** `backups/postgres/residency_scheduler_20251229_224927.sql.gz`

**Restore commands:**
```bash
# Extract rag_documents data from backup
gunzip -c backups/postgres/residency_scheduler_20251229_224927.sql.gz > /tmp/full_backup.sql

# Find and extract just the rag_documents COPY block
grep -n "COPY public.rag_documents" /tmp/full_backup.sql
# Note the line number, then extract that section

# Or restore full backup if needed (will overwrite other data):
# gunzip -c backups/postgres/residency_scheduler_20251229_224927.sql.gz | \
#   docker exec -i residency-scheduler-db psql -U scheduler -d residency_scheduler

# Verify after restore:
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*), doc_type FROM rag_documents GROUP BY doc_type;"
```

**Expected result:** ~62 chunks across doc_types (acgme_rules, scheduling_policy, swap_system, etc.)

### Blocked: Celery Init Task

The `initialize_embeddings` Celery task fails with:
```
sqlalchemy.exc.ProgrammingError: relation "export_jobs" does not exist
```

**Fix needed:** Run `alembic upgrade head` to add missing tables, then re-init if restore doesn't work.

### Uncommitted Files

From Session 038:
- `.claude/skills/governance/SKILL.md` (modified) - READY
- `.claude/Scratchpad/SESSION_038_HANDOFF.md` (new) - ARCHIVE
- `.claude/commands/governance.md` (new) - READY

---

## Rollback Plan

If Mission Command structure fails:

1. Read archive: `.claude/dontreadme/archives/AGENT_SCHEMA_PRE_MISSION_COMMAND.md`
2. Revert agent specs to original model tiers
3. Restore HIERARCHY.md to flat structure
4. Remove sub-orchestrator designations from ARCHITECT and SYNTHESIZER

---

## Questions to Resolve

1. **OPTIMIZATION_SPECIALIST** - Currently opus. Specialist or promote to Coordinator?
2. **FORCE_MANAGER** - Special Staff. Where does it fit?
3. **G-Staff advisory vs command** - Do they ever need to spawn agents?
4. **MEDCOM, DEVCOM_RESEARCH** - Special staff placement?

---

## Next Session Actions

### Priority 0: Infrastructure
1. [ ] **RESTORE RAG DATA** - See "FIRST PRIORITY" section above
2. [ ] Fix `export_jobs` migration if needed (`alembic upgrade head`)

### Priority 1: Mission Command Implementation
3. [ ] Update SYNTHESIZER.md: haiku → **opus**, add sub-orchestrator role
4. [ ] Update ARCHITECT.md: add `Exception: true`, document sub-orchestrator role
5. [ ] Update all G-Staff: → **sonnet** (advisory role)
6. [ ] Update all COORDs: opus → **sonnet**
7. [ ] Update all Specialists: → **haiku**
8. [ ] Update HIERARCHY.md with new structure

### Priority 2: Validation
9. [ ] Test chain spawning with real task (Opus → Sonnet → Haiku)
10. [ ] Verify standing orders work without escalation

### Priority 3: Cleanup
11. [ ] Commit Session 038 governance files
12. [ ] Archive SESSION_038_HANDOFF.md to `.claude/dontreadme/sessions/`

---

## Key Files

| File | Purpose |
|------|---------|
| `.claude/dontreadme/archives/AGENT_SCHEMA_PRE_MISSION_COMMAND.md` | Rollback reference |
| `.claude/Governance/HIERARCHY.md` | Current hierarchy (to update) |
| `.claude/Agents/*.md` | Agent specs (to update model tiers) |
| `.claude/skills/startupO/SKILL.md` | ORCHESTRATOR startup (to update) |

---

*Prepared for continuation. Mission Command restructure ready to implement.*
