# Quick Migration Reference Card

> **Quick Reference for Skill Migration Procedures**
> **Use This For**: Fast lookups during migrations
> **Related Docs**: skills-migration-guide.md (comprehensive)

---

## One-Page Migration Checklists

### Adding Parallel Hints (2 minutes)

```bash
# 1. Edit SKILL.md frontmatter
vi .claude/skills/YOUR_SKILL/SKILL.md

# 2. Add this section under 'description:'
parallel_hints:
  can_parallel_with: [lint-monorepo, test-writer]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3

# 3. Test serial mode first
# [invoke skill 3 times]

# 4. Test parallel mode
# [invoke skill 3x concurrently]

# 5. Update SKILL_INDEX.md if needed
```

---

### Adding Model Tier (1 minute)

```yaml
# Edit SKILL.md frontmatter, add after 'description:'
model_tier: opus   # or haiku

# Decision guide:
# opus   = complex reasoning (code review, testing, analysis)
# haiku  = lightweight (linting, simple checks)
```

---

### Migration: Breaking Change (30 minutes)

```
1. CREATE MIGRATION GUIDE
   - Copy template from skills-migration-guide.md
   - Document old vs new API
   - Create 30-day deprecation timeline

2. VERSION BUMP
   - MAJOR: v1.x → v2.0.0
   - Update SKILL.md version field

3. BACKWARDS COMPATIBILITY LAYER (optional)
   - Add fallback logic to handle old API
   - Keep for 30+ days

4. TESTING
   - Test new API works
   - Test backwards compat layer (if present)
   - Test error messages

5. UPDATE DOCUMENTATION
   - Update SKILL.md with breaking change note
   - Update SKILL_INDEX.md version info
   - Link migration guide from both

6. CREATE PR
   - Title: "BREAKING: Add required parameter to {skill}"
   - Link migration guide in description
   - Explain why breaking change necessary
```

---

### Rollback Procedures

#### Issue: Parallel Hints Causing Deadlock

```bash
# IMMEDIATE (< 30 seconds)
1. Edit SKILL.md
2. Clear parallel permissions:
   parallel_hints:
     can_parallel_with: []
     must_serialize_with: [ALL]
     preferred_batch_size: 1
3. Test serial mode
4. Root cause analysis (offline)
```

#### Issue: Wrong Model Tier

```bash
# IMMEDIATE (< 30 seconds)
1. Edit SKILL.md
2. Change model_tier: opus → haiku (or vice versa)
3. Test and compare quality
4. Keep whichever works better
```

#### Issue: Breaking Change Breaks Everything

```bash
# IMMEDIATE (< 1 minute)
git checkout PREVIOUS_COMMIT -- .claude/skills/YOUR_SKILL/
git commit -m "Revert breaking change pending review"

# Then: Deploy compat layer and migrate properly
```

---

## Version Bump Decision Tree

```
┌─ Is interface/API changing?
│  └─ YES → MAJOR (v1.x → v2.0)
│  └─ NO → Continue
│
├─ Are we adding features?
│  └─ YES → MINOR (v1.x → v1.y)
│  └─ NO → Continue
│
├─ Are we refactoring?
│  └─ YES → MINOR (v1.x → v1.y)
│  └─ NO → Continue
│
└─ Bug fix or internal change?
   └─ YES → PATCH (v1.x → v1.x.z)
   └─ NO → No change needed
```

---

## Common Scenarios

### Scenario 1: "I added parallel_hints to my skill"

**Version**: v1.0 → v1.1 (MINOR)
**Effort**: 5 minutes
**Risk**: LOW

**Checklist:**
- [ ] Test serial mode (works?)
- [ ] Test parallel mode (works?)
- [ ] Update SKILL.md version: 1.1.0
- [ ] No other changes needed

---

### Scenario 2: "I added a required parameter"

**Version**: v1.5 → v2.0 (MAJOR - breaking!)
**Effort**: 30 minutes
**Risk**: MEDIUM

**Checklist:**
- [ ] Document old API (before)
- [ ] Document new API (after)
- [ ] Create migration guide
- [ ] Set 30-day deprecation
- [ ] Add compat layer (optional)
- [ ] Test new API works
- [ ] Update version: 2.0.0
- [ ] Create PR with migration link

---

### Scenario 3: "I refactored legacy → Kai pattern"

**Version**: v1.0 → v2.0 (MAJOR refactor, no API change)
**Effort**: 1-2 hours
**Risk**: LOW

**Checklist:**
- [ ] Create Kai structure
- [ ] Move SKILL.md to SKILL.md (keep same)
- [ ] Extract Workflows/*.md
- [ ] Create Reference/*.md
- [ ] Test interface unchanged
- [ ] Test all dependencies work
- [ ] Update SKILL_INDEX.md: pattern=kai
- [ ] Update version: 2.0.0
- [ ] Note: "v2.0.0 - Refactored to Kai pattern"

---

## CLI Commands Reference

### Git Operations

```bash
# Create feature branch
git checkout -b skill/upgrade-{skillname}

# Check what changed
git diff .claude/skills/YOUR_SKILL/

# View version in git
git log --oneline .claude/skills/YOUR_SKILL/SKILL.md | head -5

# Revert single skill to previous version
git checkout PREVIOUS_COMMIT -- .claude/skills/YOUR_SKILL/
```

### Search Operations

```bash
# Find all invocations of a skill
grep -r "invoke_skill.*YOUR_SKILL" .

# Find dependencies
grep -r "dependencies:" .claude/skills/YOUR_SKILL/

# Check for version references
grep -r "version:" .claude/skills/YOUR_SKILL/

# Monitor for breaking changes
git log -p .claude/skills/YOUR_SKILL/ | grep -A5 "breaking\|required"
```

---

## Decision Trees

### When to Use Parallel Hints

```
Will this skill ever be invoked multiple times?
├─ NO  → Don't add parallel_hints (keep sequential)
├─ YES → Continue
└── Can instances run independently (no shared state)?
    ├─ NO  → Don't add parallel_hints (risk of conflicts)
    └─ YES → Add parallel_hints
             └─ can_parallel_with: [safe_skills_only]
             └─ must_serialize_with: [state-dependent_skills]
```

### When to Add Model Tier

```
Does this skill do heavy reasoning?
├─ NO (simple logic/filtering)
│  └─ model_tier: haiku
└─ YES (complex analysis/generation)
   └─ Does it need 1+ hour of thinking?
      ├─ NO  → model_tier: opus
      └─ YES → model_tier: opus (or mark as complex)
```

---

## One-Liners for Common Tasks

```bash
# List all skills
ls -1 .claude/skills/*/SKILL.md | wc -l

# List versioned skills
grep -l "^version:" .claude/skills/*/SKILL.md

# Find skills with parallel_hints
grep -l "parallel_hints:" .claude/skills/*/SKILL.md

# Find skills with model_tier
grep -l "model_tier:" .claude/skills/*/SKILL.md

# Check for breaking changes in last N commits
git log -N --oneline | grep -i "breaking\|breaking change"

# List all dependencies
grep -h "dependencies:" .claude/skills/*/SKILL.md | sort | uniq

# Find which skills depend on {skill}
grep -r "dependencies:.*YOUR_SKILL" .claude/skills/
```

---

## Rollback Decision Matrix

| Scenario | Immediate Action | Full Fix | Time | Risk |
|----------|---|---|---|---|
| Parallel hints broken | Clear parallel config | Redesign concurrency | < 1 min | LOW |
| Wrong model_tier | Switch tier value | Profile and optimize | < 1 min | LOW |
| Breaking change broke tests | Revert commit | Implement compat layer | < 5 min | MEDIUM |
| Output format wrong | Check schema version | Versioning implementation | < 5 min | LOW |
| Dependency version mismatch | Check versions | Document constraints | < 10 min | MEDIUM |

---

## File Locations

```
Skill Registry:
  .claude/SKILL_INDEX.md                    (authoritative index)
  .claude/skills/*/SKILL.md                 (individual skills)

Documentation:
  .claude/Scratchpad/.../skills-migration-guide.md  (comprehensive)
  .claude/Scratchpad/.../QUICK_MIGRATION_REFERENCE.md (this file)

Core Infrastructure:
  .claude/skills/CORE/SKILL.md              (versioning rules)
  .claude/skills/startup/SKILL.md           (session init)
  CLAUDE.md                                 (project guidelines)
```

---

## Quick Links

**Need detailed procedures?** → See skills-migration-guide.md
**Want full analysis?** → See SEARCH_PARTY_RECONNAISSANCE_REPORT.md
**Just need quick answer?** → You're reading it!

---

## Emergency Contacts (In-Code Documentation)

```python
# If you need to know:
# - All skills in system → SKILL_INDEX.md (complete registry)
# - How skill routing works → CORE/SKILL.md section "Routing Logic"
# - What version a skill is → .claude/skills/{name}/SKILL.md (line 1)
# - How to migrate → skills-migration-guide.md
# - Exactly what changed → git log -p .claude/skills/
```

---

**Last Updated**: 2025-12-30
**Format**: Quick Reference Card
**Purpose**: Fast lookups during skill migrations

