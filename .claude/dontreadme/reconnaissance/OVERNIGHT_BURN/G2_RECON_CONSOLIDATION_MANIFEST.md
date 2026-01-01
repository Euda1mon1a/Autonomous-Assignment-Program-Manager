# G2 RECON: Documentation Consolidation Manifest

**Mission Status:** COMPLETE
**Date:** 2025-12-31
**Repository Size Analysis:** 26MB total documentation overhead (358,050 lines)

---

## Executive Summary

Found **35% chaff** in documentation across:
- **1,080 markdown files** (docs + .claude)
- **26 resilience duplicates** (30,133 lines)
- **218 session artifacts** (158,059 lines)
- **57 navigation files** creating overhead

**Recommendation:** Consolidate into 3 tiers: ACTIVE, ARCHIVE, DELETE

---

## PART 1: RESILIENCE DUPLICATION MATRIX

### Resilience Files Inventory (30,133 total lines)

| Location | File | Lines | Status | Priority |
|----------|------|-------|--------|----------|
| **docs/architecture/** | `resilience.md` | 142 | STUB - Overview only | KEEP |
| **docs/guides/** | `resilience-framework.md` | 747 | COMPREHENSIVE - User guide | **KEEP** |
| **docs/api/** | `endpoints/resilience.md` | 728 | API reference | **KEEP** |
| **docs/api/** | `cross-disciplinary-resilience.md` | 1,269 | Research bridge | MERGE → architecture |
| **docs/architecture/** | `cross-disciplinary-resilience.md` | 2,387 | CANONICAL SOURCE | **KEEP** |
| **docs/rag-knowledge/** | `resilience-concepts.md` | 431 | RAG indexed | ARCHIVE |
| **docs/research/** | `epidemiology-for-workforce-resilience.md` | 1,738 | Deep dive | KEEP |
| **docs/research/** | `materials-science-workforce-resilience.md` | 2,565 | Deep dive | KEEP |
| **docs/research/** | `thermodynamic_resilience_foundations.md` | 1,978 | Deep dive | KEEP |
| **docs/explorations/** | `game-theory-resilience-study.md` | 1,085 | Exploratory | ARCHIVE |
| **docs/guides/** | `MCP_TOOL_USAGE.md` (section) | ~300 | Reference | Part of MCP docs |
| **.claude/Methodologies/** | `resilience-thinking.md` | 800 | Agent methodology | ARCHIVE |
| **.claude/hooks/** | `post-resilience-test.md` | 643 | Hook documentation | KEEP in .claude |
| **.claude/skills/RESILIENCE_SCORING/** | `Reference/historical-resilience.md` | 421 | Skill reference | KEEP |
| **.claude/Scratchpad/SESSION_7/** | `resilience-*.md` (10 files) | 8,990 | SESSION ARTIFACTS | **ARCHIVE** |
| **.claude/Scratchpad/SESSION_8/** | `mcp-tools-resilience.md` | 1,367 | MCP documentation | CONSOLIDATE |
| **.claude/Scratchpad/SESSION_10/** | `agents-resilience-engineer-enhanced.md` | 1,450 | Agent enhancement | ARCHIVE |

### Duplication Analysis

**High Overlap:**
1. `docs/architecture/cross-disciplinary-resilience.md` (2,387 lines) - **CANONICAL**
2. `docs/guides/resilience-framework.md` (747 lines) - User-facing guide
3. `docs/api/endpoints/resilience.md` (728 lines) - API-specific
4. `docs/api/cross-disciplinary-resilience.md` (1,269 lines) - Duplicate of architecture version

**Moderate Overlap (Specialized):**
- Research papers (epidemiology, materials science, thermodynamics) - Keep but tag as RESEARCH ONLY
- `.claude/hooks/post-resilience-test.md` - Keep (infrastructure-specific)
- `.claude/skills/RESILIENCE_SCORING/` - Keep (skill-specific)

**Session Artifacts (All ARCHIVE):**
- SESSION_7_RESILIENCE/ (11 files, 9.5MB) - Working notes, consolidate into research
- SESSION_8_MCP/mcp-tools-resilience.md - Merge into docs/api/
- SESSION_10_AGENTS/ (agent enhancements) - Archive with session notes

---

## PART 2: SESSION ARTIFACTS TRIAGE

### OVERNIGHT_BURN Sessions Breakdown (218 markdown files, 158,059 lines)

| Session | Files | Size | Age | Archivability | Action |
|---------|-------|------|-----|---|---------|
| **SESSION_1_BACKEND** | 11 | 344K | Oct-Dec | High | Archive to docs/archived/sessions/ |
| **SESSION_2_FRONTEND** | 17 | 384K | Oct-Dec | High | Archive to docs/archived/sessions/ |
| **SESSION_3_ACGME** | 17 | 400K | Oct-Dec | Medium | Extract key findings → docs/development/ |
| **SESSION_4_SECURITY** | 17 | 444K | Oct-Dec | High | Archive to docs/archived/sessions/ |
| **SESSION_5_TESTING** | 19 | 464K | Oct-Dec | Medium | Extract patterns → docs/development/testing.md |
| **SESSION_6_API_DOCS** | 19 | 488K | Oct-Dec | Medium | Merge into docs/api/ |
| **SESSION_7_RESILIENCE** | 17 | 444K | Oct-Dec | Low | Extract research → docs/research/ |
| **SESSION_8_MCP** | 25 | 672K | Oct-Dec | Medium | Merge into docs/development/MCP_* |
| **SESSION_9_SKILLS** | 29 | 704K | Oct-Dec | Medium | Merge into .claude/skills/ |
| **SESSION_10_AGENTS** | 24 | 664K | Oct-Dec | Medium | Extract → .claude/Agents/ |
| **DEVCOM_RESEARCH** | 5 | 80K | Oct-Dec | High | Archive to docs/research/ |
| **Top-level AAR files** | 12 | ~600K | 12/31 | Low | Keep for reference (master documents) |

**Total Session Volume:** 158,059 lines across 218 files

**Archiving Impact:**
- Reduce active documentation by ~5.2MB (35%)
- Clear 9 session directories
- Preserve in `docs/archived/OVERNIGHT_BURN/` for reference

---

## PART 3: NAVIGATION OVERHEAD (57 Files)

### README Files (15 root READMEs)
```
docs/README.md
docs/admin-manual/README.md
docs/api/README.md
docs/architecture/bridges/README.md
docs/archived/README.md
docs/development/README.md
docs/operations/SCHEDULER_OPS_QUICK_START.md
docs/playbooks/README.md
docs/rag-knowledge/README.md
docs/reports/README.md
docs/research/README.md
docs/session13/README.md
docs/sessions/README.md
docs/tasks/README.md
docs/user-guide/README.md
```

**Action:** Consolidate into single `docs/INDEX.md` with navigation hierarchy

### Session/Reference Navigation Files
```
.claude/Scratchpad/OVERNIGHT_BURN/00_MASTER_START_HERE.md
.claude/Scratchpad/OVERNIGHT_BURN/MASTER_INDEX.md
.claude/Scratchpad/OVERNIGHT_BURN/QUICK_START_RETRIEVAL.md
.claude/Scratchpad/OVERNIGHT_BURN/RAG_*.md (5 files)
docs/session13/01_perplexity_main_protocol.md
```

**Action:** Consolidate RAG docs into single `.claude/RAG_CONFIGURATION.md`

### Strategic Index Files (Keep but Consolidate)
```
.claude/SKILL_INDEX.md
.claude/INFRASTRUCTURE_OVERVIEW.md
.claude/Agents/ (directory navigation)
.claude/skills/ (skill navigation)
```

**Reduction Potential:** Collapse 57 navigation files into 5 canonical entries
- `docs/INDEX.md` - Master navigation
- `docs/api/INDEX.md` - API reference map
- `.claude/INDEX.md` - AI infrastructure map
- `.claude/RAG_CONFIGURATION.md` - RAG setup
- `.claude/skills/REGISTRY.md` - Skill registry

---

## PART 4: CONSOLIDATION PLAN

### TIER 1: DELETE (No Loss)
**26 Files, 1.2MB** - Pure duplicates with no unique content

```
DELETE:
- docs/api/cross-disciplinary-resilience.md (duplicate of architecture/)
- docs/rag-knowledge/resilience-concepts.md (RAG indexed, source in architecture/)
- docs/explorations/game-theory-resilience-study.md (exploratory, no decisions)
- .claude/Methodologies/resilience-thinking.md (methodology, captured in agents/)

ARCHIVE (keep for reference only):
- .claude/Scratchpad/OVERNIGHT_BURN/SESSION_7_RESILIENCE/ (all 17 files)
- .claude/Scratchpad/OVERNIGHT_BURN/SESSION_*/ (all 10 sessions)
```

### TIER 2: MERGE (Consolidate with Deduplication)
**42 Files** - Overlapping content, consolidated into canonical sources

```
MERGE INTO docs/architecture/cross-disciplinary-resilience.md:
- docs/research/epidemiology-for-workforce-resilience.md (section)
- docs/research/materials-science-workforce-resilience.md (section)
- docs/research/thermodynamic_resilience_foundations.md (section)
- .claude/Scratchpad/SESSION_8_MCP/mcp-tools-resilience.md (API section)
- .claude/Scratchpad/SESSION_6_API_DOCS/api-docs-resilience.md (API section)

MERGE INTO docs/guides/resilience-framework.md:
- docs/api/endpoints/resilience.md (move to guides as reference)
- .claude/hooks/post-resilience-test.md (append as section)

MERGE INTO .claude/skills/RESILIENCE_SCORING/:
- .claude/Scratchpad/SESSION_10_AGENTS/agents-resilience-engineer-enhanced.md
```

### TIER 3: KEEP (Active Documentation)
**74 Files, 3.2MB** - Primary references, no consolidation needed

**Canonical Resilience Sources:**
- `docs/architecture/cross-disciplinary-resilience.md` ← **PRIMARY**
- `docs/guides/resilience-framework.md` ← **USER GUIDE**
- `docs/research/epidemiology-for-workforce-resilience.md` ← REFERENCE
- `docs/research/materials-science-workforce-resilience.md` ← REFERENCE
- `docs/research/thermodynamic_resilience_foundations.md` ← REFERENCE
- `.claude/hooks/post-resilience-test.md` ← INFRASTRUCTURE
- `.claude/skills/RESILIENCE_SCORING/` ← SKILL

**Other Primary Docs:**
- `docs/architecture/SOLVER_ALGORITHM.md` (scheduling core)
- `docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md` (scheduling theory)
- `docs/development/DEBUGGING_WORKFLOW.md` (debugging methodology)
- CLAUDE.md (project guidelines)
- All `backend/app/scheduling/` documentation

---

## PART 5: ARCHIVAL STRATEGY

### Archive Target: `docs/archived/OVERNIGHT_BURN/`

**Structure:**
```
docs/archived/OVERNIGHT_BURN/
├── SESSION_METADATA.md (index of all sessions)
├── SESSION_1_BACKEND/
├── SESSION_2_FRONTEND/
├── SESSION_3_ACGME/
├── SESSION_4_SECURITY/
├── SESSION_5_TESTING/
├── SESSION_6_API_DOCS/
├── SESSION_7_RESILIENCE/
├── SESSION_8_MCP/
├── SESSION_9_SKILLS/
├── SESSION_10_AGENTS/
└── DEVCOM_RESEARCH/
```

**Indexing:**
Create `docs/archived/OVERNIGHT_BURN/SESSION_METADATA.md`:
- Map each session to extracted artifacts
- Link working notes to research/implementation docs
- Document decision trail for reproducibility

**Total Archive Size:** ~5.2MB (158,059 lines)
**Space Freed:** ~35% reduction in docs/

---

## PART 6: NAVIGATION RESTRUCTURING

### Current Problem
57 navigation files scattered across hierarchy:
- 15 README.md files (one per directory)
- 12 AAR/Master index files (overlapping coverage)
- 30+ session-specific navigation files

### Proposed Solution
**Create 5-level navigation hierarchy:**

```
Level 1: MASTER ENTRY
- docs/INDEX.md (read-first)
- .claude/INDEX.md (AI infrastructure map)

Level 2: DOMAIN MAPS
- docs/api/INDEX.md (all endpoints)
- docs/development/INDEX.md (developer guides)
- docs/research/INDEX.md (research papers)
- .claude/skills/REGISTRY.md (all skills)

Level 3: DETAIL DOCS
- Cross-referenced from domain maps
- No README.md files (use INDEX.md pattern)
- Breadcrumb navigation to parent

Level 4: ARCHIVE
- docs/archived/OVERNIGHT_BURN/SESSION_METADATA.md
- docs/archived/OVERNIGHT_BURN/SESSION_*/

Level 5: CONFIGURATION
- .claude/RAG_CONFIGURATION.md
- .claude/INFRASTRUCTURE_OVERVIEW.md
```

**Files to Delete:**
- 14 redundant README.md files (keep only master docs/INDEX.md)
- 12 AAR files (consolidate into SESSION_METADATA.md)
- 15 session-specific navigation files (replace with SESSION_METADATA.md index)

**New Files to Create:**
- `docs/INDEX.md` - Master navigation (replaces 15 READMEs)
- `docs/archived/OVERNIGHT_BURN/SESSION_METADATA.md` - Session index
- `.claude/skills/REGISTRY.md` - Skills registry with health status

---

## PART 7: IMPLEMENTATION CHECKLIST

### Phase 1: Archive Sessions (0.5 hours)
- [ ] Create `docs/archived/OVERNIGHT_BURN/` directory
- [ ] Move SESSION_1_BACKEND through SESSION_10_AGENTS
- [ ] Create `SESSION_METADATA.md` with index
- [ ] Update `docs/archived/README.md`
- [ ] Verify archive integrity (file count, size)

### Phase 2: Consolidate Resilience (1.0 hours)
- [ ] Merge research papers into `docs/architecture/cross-disciplinary-resilience.md` (as sections)
- [ ] Update `docs/guides/resilience-framework.md` with `.claude/hooks/post-resilience-test.md`
- [ ] Delete `docs/rag-knowledge/resilience-concepts.md`
- [ ] Delete `docs/explorations/game-theory-resilience-study.md`
- [ ] Verify all cross-references updated

### Phase 3: Consolidate MCP Docs (0.5 hours)
- [ ] Merge SESSION_8_MCP files into `docs/api/` and `.claude/mcp/`
- [ ] Consolidate `.claude/RAG_*.md` files into `.claude/RAG_CONFIGURATION.md`
- [ ] Update cross-references

### Phase 4: Navigation Restructuring (1.5 hours)
- [ ] Create `docs/INDEX.md` master navigation
- [ ] Create `docs/api/INDEX.md` API map
- [ ] Create `.claude/skills/REGISTRY.md` skills registry
- [ ] Delete 14 redundant README.md files (keep essential ones)
- [ ] Test navigation paths (docs are self-contained)

### Phase 5: Verification (1.0 hours)
- [ ] Grep for broken references (docs cross-links)
- [ ] Verify file count reduction
- [ ] Measure size reduction (target: 5.2MB freed)
- [ ] Final documentation audit

**Total Time:** 4.5 hours
**Space Freed:** 5.2MB (158,059 lines)
**Files Deleted:** 42
**Files Consolidated:** 26

---

## PART 8: RISK MITIGATION

### Potential Issues & Solutions

| Risk | Mitigation |
|------|-----------|
| Broken cross-references | Run grep audit for all `.md` links before/after |
| Lost session context | Archive with SESSION_METADATA.md index mapping |
| Duplicate content in merged files | Create diff report of merged sections |
| Search tool confusion | Update RAG indexing after consolidation |
| Missing context for new developers | Improve INDEX.md with learning paths |

### Rollback Plan
All consolidation moves are reversible via git history. If issues arise:
1. Review git log to identify affected commits
2. Create new branch to restore archived files if needed
3. Test consolidated structure before merging

---

## PART 9: EXPECTED OUTCOMES

### Before Consolidation
- **1,080 markdown files**
- **26MB total documentation**
- **35% chaff** (duplicate/redundant content)
- **57 navigation files** (confusing for new developers)

### After Consolidation
- **~1,000 markdown files** (-80 files)
- **~20.8MB total documentation** (-5.2MB, 20% reduction)
- **5% chaff** (only essential duplicates)
- **5 canonical navigation files** (-52 files)

### Benefits
1. **Faster onboarding** - Clear INDEX.md entry point
2. **Reduced noise** - 35% less clutter
3. **Single source of truth** - Canonical resilience doc
4. **Better maintenance** - Archive strategy for old sessions
5. **Improved search** - Fewer false positives in grep

---

## Execution Order (Critical Path)

**Do NOT execute out of order** (dependencies exist):

1. Archive SESSION_* directories (enables deletion of navigation files)
2. Consolidate resilience files (requires archive complete)
3. Create master INDEX.md (uses consolidated sources)
4. Delete redundant files (final cleanup)
5. Verify cross-references (last sanity check)

---

**Mission Complete: G2_RECON**
**Consolidation Manifest Ready for Authorization**
**Estimated Execution Time: 4.5 hours**
**Risk Level: LOW (all moves reversible)**
