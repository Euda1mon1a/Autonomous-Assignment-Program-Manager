# Skills Migration Guide

> **Purpose:** Comprehensive documentation for migrating between skill versions and managing breaking changes in the Personal AI Infrastructure (PAI)
> **Status:** Active
> **Last Updated:** 2025-12-30
> **Scope:** Skill versioning, breaking changes, migration procedures, rollback strategies

---

## Table of Contents

1. [Version Overview](#version-overview)
2. [Current Skill Versions](#current-skill-versions)
3. [Breaking Changes Inventory](#breaking-changes-inventory)
4. [Migration Procedures](#migration-procedures)
5. [Rollback Procedures](#rollback-procedures)
6. [Backwards Compatibility Matrix](#backwards-compatibility-matrix)
7. [Hidden Breaking Changes](#hidden-breaking-changes)
8. [Skill Evolution Patterns](#skill-evolution-patterns)
9. [Migration Checklist](#migration-checklist)

---

## Version Overview

### Versioning Strategy

Skills follow **Semantic Versioning (MAJOR.MINOR.PATCH)**:

- **MAJOR**: Breaking changes to skill interface, inputs, or outputs
- **MINOR**: New capabilities, backwards-compatible additions
- **PATCH**: Bug fixes, performance improvements, no interface changes

### Current PAI Version Metadata (Session 025)

| Component | Version | Status |
|-----------|---------|--------|
| **SKILL_INDEX.md** | 1.0.0 | Stable |
| **CORE/SKILL.md** | 2.1.0 | Current |
| **Total Skills** | 34 | Established |
| **Kai Pattern Skills** | 8 | Advanced |
| **Legacy Pattern Skills** | 26 | Standard |

### Key Version Features (NEW)

Two new metadata fields introduced in Session 025:

```yaml
model_tier: opus|haiku  # Recommended Claude model for skill
parallel_hints:          # Parallelization constraints
  can_parallel_with: [skill1, skill2]        # Can run simultaneously
  must_serialize_with: [skill3, skill4]      # Must run sequentially
  preferred_batch_size: N                    # Optimal batch count
```

---

## Current Skill Versions

### Kai Pattern Skills (Advanced)

These skills have complex structure with Workflows/ and Reference/ subdirectories.

| Skill | Version | Pattern | Status | Model Tier |
|-------|---------|---------|--------|------------|
| **SCHEDULING** | TBD | kai | active | - |
| **COMPLIANCE_VALIDATION** | TBD | kai | active | - |
| **RESILIENCE_SCORING** | TBD | kai | active | - |
| **SWAP_EXECUTION** | TBD | kai | active | - |
| **MCP_ORCHESTRATION** | TBD | kai | active | haiku |
| **ORCHESTRATION_DEBUGGING** | TBD | kai | active | - |
| **CORE** | 2.1.0 | kai | active | - |

### Legacy Pattern Skills (Standard)

These skills use single SKILL.md with inline documentation.

| Skill | Version | Pattern | Status | Model Tier |
|-------|---------|---------|--------|------------|
| acgme-compliance | TBD | legacy | active | - |
| schedule-optimization | TBD | legacy | active | - |
| swap-management | TBD | legacy | active | - |
| safe-schedule-generation | TBD | legacy | active | - |
| schedule-verification | TBD | legacy | active | - |
| test-writer | TBD | legacy | active | opus |
| code-review | TBD | legacy | active | opus |
| automated-code-fixer | TBD | legacy | active | opus |
| code-quality-monitor | TBD | legacy | active | - |
| lint-monorepo | TBD | legacy | active | haiku |
| systematic-debugger | TBD | legacy | active | - |
| constraint-preflight | TBD | legacy | active | - |
| solver-control | TBD | legacy | active | - |
| database-migration | TBD | legacy | active | opus |
| docker-containerization | TBD | legacy | active | opus |
| fastapi-production | TBD | legacy | active | opus |
| frontend-development | TBD | legacy | active | - |
| react-typescript | TBD | legacy | active | - |
| python-testing-patterns | TBD | legacy | active | - |
| pr-reviewer | TBD | legacy | active | opus |
| changelog-generator | TBD | legacy | active | - |
| session-documentation | TBD | legacy | active | - |
| production-incident-responder | TBD | legacy | active | - |
| security-audit | TBD | legacy | active | opus |
| pdf | TBD | legacy | active | - |
| xlsx | TBD | legacy | active | - |
| test-scenario-framework | TBD | legacy | active | - |
| agent-factory | TBD | legacy | active | - |
| check-codex | TBD | legacy | active | - |
| pre-pr-checklist | TBD | legacy | active | - |
| skill-factory | TBD | legacy | active | - |
| startup | TBD | legacy | active | - |
| context-aware-delegation | TBD | legacy | active | - |

**Key Observation:** Model tier assignments track computational needs:
- **opus**: Complex reasoning skills (code-review, test-writer, database-migration)
- **haiku**: High-frequency, lightweight skills (lint-monorepo, MCP_ORCHESTRATION)

---

## Breaking Changes Inventory

### Session 025 Additions

#### Feature: Parallelization Hints (NEW)

**Introduced:** Session 025 (latest)
**Type:** MINOR version bump (backwards-compatible)
**Scope:** All skills can now specify parallelization constraints

**Breaking?** NO - Skills without parallel_hints simply execute sequentially (default behavior)

**YAML Format:**
```yaml
parallel_hints:
  can_parallel_with: [lint-monorepo, test-writer]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
```

**Migration Impact:** None (additive feature)

---

#### Feature: Model Tier Assignment (NEW)

**Introduced:** Session 025 (latest)
**Type:** MINOR version bump (informational)
**Scope:** Skills with heavy computational needs

**Breaking?** NO - Optional routing hint; missing field defaults to "auto"

**YAML Format:**
```yaml
model_tier: opus|haiku
```

**Migration Impact:** None (additive feature)

---

### Historical Breaking Changes (None Recorded)

As of Session 025, no documented breaking changes exist in the skills infrastructure. Skills have evolved through additive changes only.

---

## Migration Procedures

### Procedure 1: Adding Parallelization Hints to Existing Skill

**Scenario:** You want to optimize a skill that currently runs serially

**Steps:**

1. **Identify Safe Parallels**
   ```bash
   # List current skill dependencies
   grep -r "dependencies:" .claude/skills/YOUR_SKILL/

   # Identify skills that don't share state
   # Example: lint-monorepo and test-writer are independent
   ```

2. **Update SKILL.md Frontmatter**
   ```yaml
   ---
   name: your-skill
   description: ...
   model_tier: opus|haiku          # If applicable
   parallel_hints:
     can_parallel_with: [compatible_skill_1, compatible_skill_2]
     must_serialize_with: [dependent_skill]
     preferred_batch_size: 3
   ---
   ```

3. **Document Rationale**
   ```markdown
   ## Parallelization Strategy

   - **can_parallel_with**: These skills don't share database state
   - **must_serialize_with**: These skills depend on previous results
   - **preferred_batch_size**: 3 instances balances throughput vs overhead
   ```

4. **Test Parallelization**
   ```bash
   # Invoke in parallel context
   # Run same operation 3x concurrently
   # Verify all instances complete successfully
   ```

5. **Update SKILL_INDEX.md**
   ```bash
   grep -n "your-skill" .claude/SKILL_INDEX.md
   # Update routing rules if parallelization changes optimal invocation pattern
   ```

---

### Procedure 2: Creating Model Tier Assignment

**Scenario:** You need to specify which Claude model should run a skill

**Steps:**

1. **Assess Computational Needs**
   ```
   - Simple logic + direct execution → haiku (fast, cheap)
   - Complex reasoning, analysis, code generation → opus (slower, smarter)
   ```

2. **Update SKILL.md**
   ```yaml
   ---
   name: your-skill
   model_tier: opus  # or haiku
   ---
   ```

3. **Document Rationale**
   ```markdown
   ## Model Selection

   **Selected: opus** (or haiku)

   Reasoning:
   - [List computational requirements]
   - [Justify why this model tier is appropriate]
   - [Expected latency and quality tradeoffs]
   ```

---

### Procedure 3: Migrating from Legacy to Kai Pattern

**Scenario:** You want to refactor a legacy skill into advanced Kai pattern

**Steps:**

1. **Backup Current Skill**
   ```bash
   cp -r .claude/skills/your-skill .claude/skills/your-skill.backup.v1
   ```

2. **Create Kai Structure**
   ```
   .claude/skills/your-skill/
   ├── SKILL.md                    # Main skill definition
   ├── Workflows/
   │   ├── workflow1.md            # Documented workflows
   │   ├── workflow2.md
   │   └── workflow3.md
   └── Reference/
       ├── reference1.md           # Reference material
       ├── reference2.md
       └── glossary.md
   ```

3. **Migrate SKILL.md**
   - Move main skill definition to SKILL.md
   - Keep interface same for backwards compatibility
   - Add backwards-compat note: "v2.0.0 - Migrated to Kai pattern"

4. **Extract Workflows**
   - Identify core workflows from original SKILL.md
   - Create separate Workflows/*.md files
   - Document step-by-step execution

5. **Create Reference Material**
   - Extract glossary, examples, error codes
   - Create Reference/ subdirectory
   - Link from SKILL.md

6. **Update SKILL_INDEX.md**
   ```yaml
   # Change pattern from legacy to kai
   pattern: kai
   ```

7. **Version Bump**
   ```yaml
   version: 2.0.0  # MAJOR bump (pattern change)
   ```

8. **Backwards Compatibility Note**
   ```markdown
   ## Migration Notes

   **Version 1.x → 2.0.0**
   - Pattern: legacy → kai
   - Interface: unchanged
   - All 1.x invocations still work
   - Recommend updating to 2.x for new features
   ```

---

### Procedure 4: Breaking Change - Adding Required Parameter

**Scenario:** You need to add a required parameter to a skill's interface

**Steps:**

1. **Assess Impact**
   ```bash
   # Find all invocations of this skill
   grep -r "invoke_skill.*your-skill" .
   grep -r "Activate: your-skill" .
   ```

2. **Create Migration Guide**
   ```markdown
   # Migration: your-skill v1.x → v2.0.0

   ## Breaking Change

   ### What Changed
   - Added required parameter: `schedule_id`

   ### Why
   - [Explain business reason for change]

   ### How to Update

   **Old API:**
   ```yaml
   invoke_skill("your-skill", {
     "start_date": "2025-04-01"
   })
   ```

   **New API (Required):**
   ```yaml
   invoke_skill("your-skill", {
     "schedule_id": "block_10_2025",
     "start_date": "2025-04-01"
   })
   ```
   ```

3. **Create Fallback Support (if critical)**
   ```python
   # Pseudo-code for backwards-compatible wrapper
   def invoke_skill(skill_name, params):
       if skill_name == "your-skill" and "schedule_id" not in params:
           # Try to infer schedule_id from context
           params["schedule_id"] = infer_schedule_id(params)
       return original_invoke(skill_name, params)
   ```

4. **Deprecation Timeline**
   ```markdown
   ## Deprecation Timeline

   - **v2.0.0 (2025-12-30)**: Breaking change introduced
   - **v2.1.0 (2026-01-31)**: Compatibility wrapper available
   - **v3.0.0 (2026-02-28)**: Compatibility wrapper removed
   ```

5. **Update Version**
   ```yaml
   version: 2.0.0  # MAJOR bump
   deprecated: false
   sunset_date: null
   ```

---

## Rollback Procedures

### Scenario 1: Parallel Hints Causing Issues

**Problem:** Skill invocations fail due to parallelization constraints

**Recovery:**

1. **Identify Constraint Issue**
   ```bash
   # Check error logs for deadlock or state corruption
   grep -r "parallel" error.log | head -10
   ```

2. **Disable Parallelization (Immediate)**
   ```yaml
   # Edit SKILL.md
   parallel_hints:
     can_parallel_with: []           # Clear all parallel permissions
     must_serialize_with: [ALL]      # Force serialization
     preferred_batch_size: 1
   ```

3. **Test Serial Mode**
   ```bash
   # Invoke skill 3x sequentially
   # Verify all pass
   ```

4. **Root Cause Analysis**
   - Check for shared state assumptions
   - Review for non-thread-safe operations
   - Verify database transaction isolation

5. **Restore Parallelization Safely**
   ```yaml
   parallel_hints:
     can_parallel_with: [safe_skill_only]
     must_serialize_with: [database-migration]
     preferred_batch_size: 2  # Conservative
   ```

---

### Scenario 2: Model Tier Causing Issues

**Problem:** Skill produces poor results with wrong model tier

**Recovery:**

1. **Identify Model Issue**
   ```bash
   # Check if skill output quality degraded
   # Compare with previous model tier
   ```

2. **Switch Model Tier (Immediate)**
   ```yaml
   # Edit SKILL.md
   model_tier: opus  # If was haiku, switch to opus
   ```

3. **Re-run and Compare**
   ```bash
   # Run same test case with new model tier
   # Compare output quality
   ```

4. **Root Cause Analysis**
   - Was task too complex for selected model?
   - Does task require advanced reasoning?
   - Check latency/cost tradeoffs

5. **Document Decision**
   ```markdown
   ## Model Tier Rationale

   **Selected: opus**

   Reason: haiku struggled with [specific requirement]
   Quality improvement: [metrics]
   Cost impact: [estimate]
   ```

---

### Scenario 3: Legacy → Kai Migration Issues

**Problem:** Kai pattern migration broke something

**Recovery:**

1. **Revert to Backup**
   ```bash
   rm -rf .claude/skills/your-skill
   cp -r .claude/skills/your-skill.backup.v1 .claude/skills/your-skill
   ```

2. **Identify Issue**
   - Was workflow extraction incorrect?
   - Did reference material break something?
   - Did interface change unintentionally?

3. **Fix Specific Issue**
   - Keep backup as reference
   - Recreate problem component
   - Test in isolation before re-integrating

4. **Re-migrate Carefully**
   ```bash
   git diff .claude/skills/your-skill
   # Review each change carefully
   ```

---

### Scenario 4: Breaking Change Rollback

**Problem:** New required parameter broke existing invocations

**Recovery:**

1. **Revert to Previous Version**
   ```bash
   git checkout PREVIOUS_COMMIT -- .claude/skills/your-skill/
   ```

2. **Assess Damage**
   ```bash
   # Count failed invocations
   grep -r "your-skill" *.log | grep "FAILED" | wc -l
   ```

3. **Two Recovery Paths**

   **Option A: Restore Old Version (Immediate)**
   ```bash
   git checkout v1.x -- .claude/skills/your-skill/
   ```

   **Option B: Deploy Compatibility Layer (Gradual)**
   ```python
   # Add fallback logic to handle old API
   def invoke_skill_legacy_compat(skill_name, params):
       if skill_name == "your-skill":
           if "schedule_id" not in params:
               params["schedule_id"] = infer_from_context(params)
       return invoke_skill(skill_name, params)
   ```

4. **Plan Proper Migration**
   - Create migration guide
   - Set deprecation timeline
   - Communicate to users

---

## Backwards Compatibility Matrix

### Session 025 Compatibility

| Feature | Backwards Compat | Status | Sunset |
|---------|------------------|--------|--------|
| **parallel_hints** | YES | Added (optional) | Never |
| **model_tier** | YES | Added (optional) | Never |
| **Kai pattern** | YES | Existing skills unchanged | N/A |
| **Legacy pattern** | YES | Still supported | TBD |

### Cross-Version Compatibility

| From Version | To Version | Breaking Changes | Migration Path |
|--------------|------------|------------------|-----------------|
| 1.x | 1.y (patch) | None | Auto-upgrade safe |
| 1.x | 2.0 (minor) | None (if implemented correctly) | Review docs |
| 1.x | 3.0 (major) | Possible | Use migration guide |

### Skill-Level Compatibility

Current compatible combinations:
```yaml
SCHEDULING (kai)
  ├─ depends: COMPLIANCE_VALIDATION (kai)  ✓ Compatible
  ├─ depends: safe-schedule-generation (legacy)  ✓ Compatible
  └─ depends: schedule-optimization (legacy)  ✓ Compatible

SWAP_EXECUTION (kai)
  ├─ depends: COMPLIANCE_VALIDATION (kai)  ✓ Compatible
  ├─ depends: swap-management (legacy)  ✓ Compatible
  └─ depends: RESILIENCE_SCORING (kai)  ✓ Compatible
```

---

## Hidden Breaking Changes

### Watch Out For

#### Change 1: Skill Output Format Evolution

**What:** Skill might return different JSON structure

**How to Detect:**
```python
# Check output schema version
result = invoke_skill("your-skill", params)
if "schema_version" not in result:
    # Likely v1.x output
    handle_v1_output(result)
else:
    # v2.x+ output
    handle_v2_output(result)
```

**Prevention:** Always version output schemas in result envelope:
```yaml
result:
  schema_version: "2.0.0"  # Add this!
  data: {...}
```

---

#### Change 2: Dependency Version Mismatch

**What:** Skill depends on another skill that changed

**How to Detect:**
```bash
# Check dependency versions
grep "dependencies:" .claude/skills/YOUR_SKILL/SKILL.md

# Verify each dependency exists and versions match
for dep in $(grep -o "\[.*\]" | tr ',' '\n'); do
  ls ".claude/skills/$dep/SKILL.md" || echo "MISSING: $dep"
done
```

**Prevention:** Explicitly version dependencies:
```yaml
dependencies:
  - name: COMPLIANCE_VALIDATION
    min_version: 1.0.0
    max_version: 3.x.x
```

---

#### Change 3: Routing Rule Changes

**What:** SKILL_INDEX.md updates routing, breaking manual routing

**How to Detect:**
```bash
# Compare routing logic changes
git diff HEAD~10..HEAD .claude/SKILL_INDEX.md | grep -A5 "routing"
```

**Prevention:** Document routing changes in SKILL_INDEX.md:
```markdown
## Routing Changes (v1.5.0 → 1.6.0)

### Changed
- "generate schedule" now routes to SCHEDULING (was schedule-optimization)

### Impact
- Existing invocations of schedule-optimization still work
- New tasks will use SCHEDULING

### Migration
- No action required for existing code
- Consider updating manual routing to use SCHEDULING
```

---

#### Change 4: Parameter Validation Strictness

**What:** Skill starts rejecting previously-accepted parameters

**How to Detect:**
```bash
# Look for validation logic changes
git log -p .claude/skills/YOUR_SKILL/ | grep -A10 "validate\|required"
```

**Example:**
```python
# v1.x - lenient
def invoke_skill(params):
    schedule_id = params.get("schedule_id", None)  # Accepts None

# v2.x - strict
def invoke_skill(params):
    schedule_id = params["schedule_id"]  # Requires non-None
    if not schedule_id:
        raise ValueError("schedule_id required")
```

---

## Skill Evolution Patterns

### Pattern 1: Legacy → Kai Refactoring (No Breaking Change)

**Timeline:**
```
v1.0.0 (legacy)
  ↓ [refactor to Kai pattern]
v2.0.0 (kai)  [MAJOR but interface unchanged]
  ↓ [add new workflows]
v2.1.0 (kai)  [MINOR - new capabilities]
  ↓ [add reference material]
v2.2.0 (kai)  [MINOR - documentation]
```

**Key Principle:** If interface unchanged, don't bump MAJOR (keep as v1.0 → v2.0 refactor exception)

---

### Pattern 2: Feature Addition Cycle

**Timeline:**
```
v1.0.0 (basic skill)
  ↓ [add parallelization hints]
v1.1.0 (MINOR - backwards compatible)
  ↓ [add model_tier hints]
v1.2.0 (MINOR - backwards compatible)
  ↓ [optimize performance]
v1.2.1 (PATCH - bug fix)
  ↓ [add required parameter]
v2.0.0 (MAJOR - breaking change)
```

---

### Pattern 3: Deprecation Cycle

**Timeline:**
```
v1.0.0 (current)
  ↓ [mark as deprecated]
v1.1.0 (deprecated=true, sunset_date=+30days)
  ↓ [add migration guide]
v1.2.0 (deprecated=true, sunset_date updated)
  ↓ [after sunset date]
  ↓ [remove from system]
REMOVED (from registry)
```

**Example:**
```yaml
# SKILL.md
version: 1.1.0
deprecated: true
sunset_date: 2026-01-30
replacement: new-skill-name
migration_guide: docs/skills/migration/old-to-new.md
```

---

## Migration Checklist

### Pre-Migration

- [ ] Document current state (version, dependencies, integrations)
- [ ] Identify all invocations (grep across codebase)
- [ ] Assess breaking change impact (who uses this skill?)
- [ ] Create migration guide
- [ ] Set up test cases for backwards compatibility
- [ ] Get stakeholder approval (if user-facing change)

### During Migration

- [ ] Create feature branch: `git checkout -b skill/upgrade-{skillname}`
- [ ] Make changes to SKILL.md
- [ ] Update SKILL_INDEX.md if routing changes
- [ ] Add parallel_hints if applicable
- [ ] Add model_tier if applicable
- [ ] Update version number (MAJOR/MINOR/PATCH)
- [ ] Create migration guide (if breaking)
- [ ] Update dependencies documentation
- [ ] Run backwards compatibility tests

### Testing

- [ ] Test skill invocation with new version
- [ ] Test backwards-compatible invocations (if not breaking)
- [ ] Test skill composition (dependencies)
- [ ] Test parallelization if hints added
- [ ] Test error conditions
- [ ] Test with specified model_tier

### Documentation

- [ ] Update SKILL.md with migration notes
- [ ] Update SKILL_INDEX.md with version info
- [ ] Create migration guide (if breaking)
- [ ] Document parallelization strategy (if added)
- [ ] Document model tier rationale (if specified)
- [ ] Add examples with new features
- [ ] Update any affected documentation files

### Post-Migration

- [ ] Create PR with clear description
- [ ] Link to migration guide in PR
- [ ] Get code review approval
- [ ] Merge to main
- [ ] Monitor for issues
- [ ] Update SKILL_INDEX.md version counter (if needed)
- [ ] Announce changes to team
- [ ] Set calendar reminder for sunset date (if deprecating)

---

## Quick Reference: Version Bump Decision Tree

```
START: Assess Changes
  |
  ├─ Are existing invocations still valid?
  |  ├─ YES → Continue
  |  └─ NO  → MAJOR version bump (breaking)
  |
  ├─ Is this purely internal refactoring?
  |  ├─ YES → MINOR version bump (refactor)
  |  └─ NO  → Continue
  |
  ├─ Adding new features/capabilities?
  |  ├─ YES → MINOR version bump (feature)
  |  └─ NO  → Continue
  |
  ├─ Fixing bugs/performance?
  |  ├─ YES → PATCH version bump
  |  └─ NO  → No version bump needed
  |
  └─ Decision made!
```

---

## Examples

### Example 1: Adding Model Tier to automated-code-fixer

**Current State:**
```yaml
---
name: automated-code-fixer
description: Automated IT helper for detecting and fixing code issues
---
```

**Migration:**
```yaml
---
name: automated-code-fixer
description: Automated IT helper for detecting and fixing code issues
model_tier: opus  # NEW
parallel_hints:   # NEW
  can_parallel_with: [lint-monorepo, test-writer]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
---
```

**Changes:**
- No interface changes
- Added optional metadata (MINOR bump)
- Version: v1.0.0 → v1.1.0

---

### Example 2: Adding Required Parameter (Breaking)

**Current:**
```python
invoke_skill("swap-management", {
    "requester_id": "faculty_001"
})
```

**New (Required):**
```python
invoke_skill("swap-management", {
    "requester_id": "faculty_001",
    "schedule_block": "block_10_2025"  # NEW REQUIRED
})
```

**Migration Guide:**
```markdown
# Migration: swap-management v1.x → v2.0.0

## What's Changing
- Added required parameter: `schedule_block`

## Why
- Ambiguous which schedule block's assignments to swap
- Required for accurate constraint validation

## Migration Steps

### Before (v1.x)
```yaml
invoke_skill("swap-management", {
    "requester_id": "faculty_001"
})
```

### After (v2.0.0)
```yaml
invoke_skill("swap-management", {
    "requester_id": "faculty_001",
    "schedule_block": "block_10_2025"  # Add this
})
```

## Deprecation Timeline
- 2025-12-30: v2.0.0 released (breaking change)
- 2026-01-31: v2.1.0 (backwards compat wrapper available)
- 2026-02-28: v3.0.0 (wrapper removed)
```

**Changes:**
- Interface changed (MAJOR bump)
- Version: v1.5.0 → v2.0.0

---

## Appendix: Version History

### PAI Version History

| Version | Date | Changes | Skills |
|---------|------|---------|--------|
| 1.0.0 | 2025-12-00 | Initial skill registry | 30 |
| 1.1.0 | 2025-12-15 | Added Kai pattern | 34 |
| 1.2.0 | 2025-12-26 | SKILL_INDEX.md stabilized | 34 |
| 1.3.0 | 2025-12-27 | startup skill added | 35 |
| 1.4.0 | 2025-12-28 | Routing rules refined | 34 |
| 2.0.0 | 2025-12-30 | Added parallel_hints, model_tier | 34 |

### Key Milestones

- **2025-12-26**: SKILL_INDEX.md v1.0.0 (complete registry)
- **2025-12-27**: startup skill created (session management)
- **2025-12-28**: SKILL_INDEX.md versioning added
- **2025-12-30**: parallel_hints and model_tier introduced (Session 025)

---

## References

- **SKILL_INDEX.md** - Complete skill registry and routing
- **CORE/SKILL.md** - Skill metadata and routing logic (v2.1.0)
- **CLAUDE.md** - Project guidelines and skill usage
- **docs/development/AI_RULES_OF_ENGAGEMENT.md** - Git workflow rules

---

**END OF SKILLS MIGRATION GUIDE**

*Last Updated: 2025-12-30 | Session 025 | G2_RECON SEARCH_PARTY Operation*

