***REMOVED*** SESSION 9: New Skills Implementation Guide
> **For:** Developers implementing P1-P2 skills
> **Reference:** `skills-new-recommendations.md` for full context
> **Date:** 2025-12-30

---

***REMOVED******REMOVED*** Quick Start (15 minutes)

***REMOVED******REMOVED******REMOVED*** 1. Choose Your Skill

Pick one of these in priority order:

1. **SCHEDULE_VALIDATOR** (easiest, 24 hours)
2. **COMPLIANCE_AUDITOR** (medium, 40 hours)
3. **RATE_LIMIT_FORENSICS** (medium, 16 hours)
4. **SCHEDULE_EXPLAINER** (hard, 32 hours)
5. **SOLVER_DIAGNOSTICIAN** (hard, 40 hours)
6. **RUNTIME_INCIDENT_COMMANDER** (hardest, 48 hours)

***REMOVED******REMOVED******REMOVED*** 2. Create Directory Structure

```bash
mkdir -p .claude/skills/SKILL_NAME/{Workflows,Reference,Examples,Templates}
touch .claude/skills/SKILL_NAME/SKILL.md
touch .claude/skills/SKILL_NAME/README.md
```

***REMOVED******REMOVED******REMOVED*** 3. Copy SKILL.md Template

See **Appendix A** below.

***REMOVED******REMOVED******REMOVED*** 4. Define Workflows

Each workflow is a `.md` file with clear steps. Start with stub headings:

```
***REMOVED******REMOVED*** Workflow 1: Validate Core Functionality
***REMOVED******REMOVED******REMOVED*** Step 1: Gather Input
***REMOVED******REMOVED******REMOVED*** Step 2: Load Data
***REMOVED******REMOVED******REMOVED*** Step 3: Check Rules
***REMOVED******REMOVED******REMOVED*** Step 4: Report Results
```

***REMOVED******REMOVED******REMOVED*** 5. Create Examples

Add 3-5 example scenarios showing skill in action:

```
***REMOVED*** Scenario 1: Happy Path
Input: Valid schedule
Expected: "Schedule is valid"

***REMOVED*** Scenario 2: Error Case
Input: Schedule with violations
Expected: "X violations detected: ..."
```

---

***REMOVED******REMOVED*** SKILL.md Template (Copy-Paste Ready)

```yaml
---
skill_name: YOUR_SKILL_NAME
purpose: "One sentence describing what this skill does"
version: 1.0
created_date: 2025-12-30
last_updated: 2025-12-30
status: active

metadata:
  model_tier: haiku|sonnet|opus  ***REMOVED*** See complexity score table below
  complexity_score: X            ***REMOVED*** 0-5 simple, 6-12 moderate, 13+ complex
  estimated_tokens: X-Y          ***REMOVED*** e.g., "5000-8000"
  execution_time: "X-Y minutes"  ***REMOVED*** e.g., "2-5 minutes"

parallel_hints:
  can_parallel_with:
    - code-review
    - test-writer
    ***REMOVED*** Add others that don't conflict
  must_serialize_with:
    - safe-schedule-generation
    ***REMOVED*** Add skills that must run alone
  preferred_batch_size: 1        ***REMOVED*** Usually 1 for domain skills

prerequisites:
  - Database access (read-only)  ***REMOVED*** e.g.
  - Redis access                 ***REMOVED*** e.g.

workflows: X                      ***REMOVED*** Count of .md files in Workflows/
examples: Y                       ***REMOVED*** Count of scenarios

author: "YOUR_NAME"
---

***REMOVED*** Skill Name Here

***REMOVED******REMOVED*** Quick Start

```
"When should I use this skill?"
→ When you need to [fill in use case]

"What does it do?"
→ [Describe in 2-3 sentences]

"What's the output?"
→ [Describe expected results]
```

***REMOVED******REMOVED*** How It Works

[Brief explanation of approach, 5-10 sentences]

***REMOVED******REMOVED*** Workflows

This skill includes [X] workflows:

1. **Workflow Name** - [One sentence]
   - File: `Workflows/01-name.md`

[Repeat for each workflow]

***REMOVED******REMOVED*** When NOT to Use

- ❌ When [case A], use [other skill] instead
- ❌ When [case B], try [other skill] instead

***REMOVED******REMOVED*** Common Patterns

[2-3 examples of typical usage patterns]

***REMOVED******REMOVED*** See Also

- [Related skill]
- [Related documentation]

***REMOVED******REMOVED*** Implementation Notes

[Any caveats, performance characteristics, or architectural notes]
```

---

***REMOVED******REMOVED*** Complexity Score Reference Table

Use this table to assign `complexity_score` and `model_tier`:

```
Complexity   Model    Base Score  Example Skill
─────────────────────────────────────────────────────
Very Simple  haiku    0-3         Format converter
Simple       haiku    4-5         Single rule validator
Moderate     sonnet   6-9         Multi-step analysis
Complex      sonnet   10-12       Constraint solver
Hard         opus     13-18       Diagnosis engine
Very Hard    opus     19+         Multi-system reasoning
```

***REMOVED******REMOVED******REMOVED*** Scoring Algorithm

```
complexity_score =
  base_for_domain(4-8) +
  (num_domains × 3) +
  (num_dependencies × 2) +
  (execution_time_minutes × 0.5) +
  (risk_level × 2)
```

**Example: SCHEDULE_VALIDATOR**
```
Domain base: 4 (validation)
+ Domains: 2 (structure, temporal) = +6
+ Dependencies: 1 (DB) = +2
+ Execution: 2 minutes = +1
+ Risk: Low = 0
= Total: 13 → opus territory (but haiku acceptable for pure rule-checking)
→ Actually: sonnet (balance between pure rules and some judgment)
```

---

***REMOVED******REMOVED*** Workflow File Format

Each workflow is a `.md` file following this structure:

```markdown
***REMOVED*** Workflow: Descriptive Name

> **Use when:** Context for this workflow
> **Typical time:** X-Y minutes
> **Prerequisites:** Any required setup

***REMOVED******REMOVED*** Overview

[2-3 sentence explanation of what this workflow does]

***REMOVED******REMOVED*** Steps

***REMOVED******REMOVED******REMOVED*** Step 1: [Action Description]

[Detailed explanation]

```
Example:
- Query database for active schedule assignments
- Filter for [specific criteria]
- Load into memory for analysis
```

***REMOVED******REMOVED******REMOVED*** Step 2: [Next Action]

[Continue...]

***REMOVED******REMOVED*** Expected Output

[What the user should see if successful]

***REMOVED******REMOVED*** Error Cases

- **If X happens:** Do Y
- **If A fails:** Try B

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Happy Path
[Describe input and expected output]

***REMOVED******REMOVED******REMOVED*** Example 2: Edge Case
[Different scenario]

***REMOVED******REMOVED*** Performance Notes

[Any optimization tips, caching strategies, or limitations]

***REMOVED******REMOVED*** Related Workflows

[List other workflows in this skill that often follow this one]
```

---

***REMOVED******REMOVED*** Example Scenario File

Create `Examples/scenario-001-name.md`:

```markdown
***REMOVED*** Scenario 1: [Descriptive Title]

**Context:** [Setup - what state is the system in?]

**Input:**
```
[Show concrete input data]
```

**Expected Output:**
```
[Show expected result]
```

**Why This Matters:**
[Explain why this is an important test case]

**Variations:**
- What if [variation A]? → Result would be [outcome A]
- What if [variation B]? → Result would be [outcome B]
```

---

***REMOVED******REMOVED*** Parallel Safety Checklist

Before declaring skill safe for parallelization, verify:

***REMOVED******REMOVED******REMOVED*** Skill doesn't:
- [ ] Acquire database locks
- [ ] Write to shared files
- [ ] Modify Redis state
- [ ] Start background jobs
- [ ] Access exclusive resources (solver, scheduler)

***REMOVED******REMOVED******REMOVED*** Skill is safe if:
- ✅ Read-only database access
- ✅ Reads from cache/Redis (no writes)
- ✅ No file I/O beyond reading
- ✅ Idempotent (running twice = running once)

***REMOVED******REMOVED******REMOVED*** Document conflicts:
```yaml
must_serialize_with:
  - safe-schedule-generation  ***REMOVED*** Reason: Both write assignments
  - COMPLIANCE_AUDITOR        ***REMOVED*** Reason: Both read assignment table
```

---

***REMOVED******REMOVED*** Testing Your Skill

***REMOVED******REMOVED******REMOVED*** Smoke Test (5 min)

1. Can someone new understand README in 5 minutes?
2. Are all workflow files linked?
3. Do all examples make sense?

***REMOVED******REMOVED******REMOVED*** Functional Test (10 min)

1. Can you run each workflow end-to-end?
2. Does output match examples?
3. Do error cases handle gracefully?

***REMOVED******REMOVED******REMOVED*** Integration Test (15 min)

1. Can this skill be called from `.claude/commands/`?
2. Does it work alongside parallel skills?
3. Can ORCHESTRATOR invoke it?

---

***REMOVED******REMOVED*** Quick-Invoke Command

After implementing skill, create `.claude/commands/YOUR_SKILL.md`:

```markdown
***REMOVED*** YOUR_SKILL_NAME

Run skill: YOUR_SKILL_NAME

**When to use:**
[Copy from SKILL.md purpose section]

**Quick examples:**

Example 1:
"Run this"

Example 2:
"Run that"

**See also:**
- `.claude/skills/YOUR_SKILL_NAME/README.md` - Full documentation
- Other related commands

[End with:]
Run: `/project:YOUR_SKILL_NAME [args]`
```

---

***REMOVED******REMOVED*** Documentation Checklist

Before submitting skill for review:

- [ ] SKILL.md created with all metadata
- [ ] README.md complete (< 500 words, clear examples)
- [ ] All workflow files exist and are linked
- [ ] 3-5 example scenarios provided
- [ ] Reference docs created (rules, patterns, taxonomy)
- [ ] parallel_hints correctly declared
- [ ] model_tier justified via complexity score
- [ ] Quick-invoke command created
- [ ] Tested against 3+ scenarios
- [ ] Cross-links to related skills added
- [ ] No TODO placeholders (complete or defer explicitly)

---

***REMOVED******REMOVED*** Common Mistakes (Avoid These)

***REMOVED******REMOVED******REMOVED*** Mistake 1: Incomplete Metadata

❌ Bad:
```yaml
metadata:
  complexity_score: 10  ***REMOVED*** Missing model_tier, tokens, time
```

✅ Good:
```yaml
metadata:
  model_tier: sonnet
  complexity_score: 10
  estimated_tokens: 8000-12000
  execution_time: "5-10 minutes"
```

***REMOVED******REMOVED******REMOVED*** Mistake 2: Vague Workflows

❌ Bad:
```
***REMOVED******REMOVED*** Workflow 1: Validate Schedule
[No steps, just paragraph description]
```

✅ Good:
```
***REMOVED******REMOVED*** Workflow 1: Validate Schedule
***REMOVED******REMOVED******REMOVED*** Step 1: Load assignments from database
***REMOVED******REMOVED******REMOVED*** Step 2: Check each assignment against rules
***REMOVED******REMOVED******REMOVED*** Step 3: Aggregate violations
***REMOVED******REMOVED******REMOVED*** Step 4: Generate report
```

***REMOVED******REMOVED******REMOVED*** Mistake 3: No Parallel Hints

❌ Bad:
```yaml
parallel_hints: {}  ***REMOVED*** Empty
```

✅ Good:
```yaml
parallel_hints:
  can_parallel_with: [code-review, test-writer]
  must_serialize_with: [safe-schedule-generation]
  preferred_batch_size: 1
```

***REMOVED******REMOVED******REMOVED*** Mistake 4: Examples Without Context

❌ Bad:
```
***REMOVED******REMOVED*** Example 1
Input: [complex JSON blob]
Output: [complex JSON blob]
```

✅ Good:
```
***REMOVED******REMOVED*** Example 1: Valid Schedule with No Violations
**Scenario:** Block 10 with all residents properly assigned
**Input:** Schedule for Feb 1-15
**Expected:** "✅ Schedule is valid (0 violations)"
**Why:** Demonstrates happy path
```

***REMOVED******REMOVED******REMOVED*** Mistake 5: Over-Promising in MVP

❌ Bad:
```
This skill will:
- Validate ACGME compliance (80-hour, 1-in-7, supervision)
- Suggest fixes
- Predict future violations
- Auto-rollback if needed
```

✅ Good:
```
MVP (v1) covers:
- ✅ Validate 80-hour rule
- ✅ Validate 1-in-7 rule
- ✅ Validate supervision ratios
- ❌ DEFER: Suggest fixes (future: Schedule Explainer)
- ❌ DEFER: Predict violations (future: Resilience Dashboard)
```

---

***REMOVED******REMOVED*** Integration Checklist (Session 10)

When submitting skill to main repository:

- [ ] SKILL.md exists in `.claude/skills/SKILL_NAME/`
- [ ] README.md is < 500 words, compelling
- [ ] All workflows are documented and exemplified
- [ ] Parallel safety is verified
- [ ] Model tier is justified
- [ ] Cross-references to related skills are complete
- [ ] Quick-invoke command exists in `.claude/commands/`
- [ ] Registered in `.claude/skills/CORE/SKILL.md`
- [ ] No merge conflicts with other PR branches
- [ ] PR description references this SEARCH_PARTY analysis
- [ ] Ready for skill-factory validation

---

***REMOVED******REMOVED*** Template Copy-Paste Blocks

***REMOVED******REMOVED******REMOVED*** Parallel Hints Block (Safe Skills)

```yaml
parallel_hints:
  can_parallel_with:
    - code-review
    - test-writer
    - security-audit
    - automated-code-fixer
  must_serialize_with:
    - safe-schedule-generation
  preferred_batch_size: 1
```

***REMOVED******REMOVED******REMOVED*** Parallel Hints Block (Exclusive Skills)

```yaml
parallel_hints:
  can_parallel_with: []
  must_serialize_with:
    - safe-schedule-generation
    - COMPLIANCE_AUDITOR
    - SCHEDULE_VALIDATOR
  preferred_batch_size: 1
```

***REMOVED******REMOVED******REMOVED*** Metadata Block (Haiku Skill)

```yaml
metadata:
  model_tier: haiku
  complexity_score: 5
  estimated_tokens: 2000-3000
  execution_time: "1-2 minutes"
```

***REMOVED******REMOVED******REMOVED*** Metadata Block (Sonnet Skill)

```yaml
metadata:
  model_tier: sonnet
  complexity_score: 10
  estimated_tokens: 5000-8000
  execution_time: "5-10 minutes"
```

***REMOVED******REMOVED******REMOVED*** Metadata Block (Opus Skill)

```yaml
metadata:
  model_tier: opus
  complexity_score: 18
  estimated_tokens: 12000-20000
  execution_time: "10-20 minutes"
```

---

***REMOVED******REMOVED*** Reference: Skills by Implementation Difficulty

***REMOVED******REMOVED******REMOVED*** Easiest First (If Starting)

1. **RATE_LIMIT_FORENSICS** (16 hours)
   - Straightforward data retrieval from Redis
   - Simple timeline reconstruction
   - No complex reasoning required

2. **SCHEDULE_VALIDATOR** (24 hours)
   - Clear validation rules
   - Deterministic output (pass/fail)
   - No ambiguity in results

3. **COMPLIANCE_AUDITOR** (40 hours)
   - Well-documented ACGME rules
   - Spreadsheet-like analysis
   - Some edge case handling needed

***REMOVED******REMOVED******REMOVED*** Medium Difficulty

4. **SCHEDULE_EXPLAINER** (32 hours)
   - Requires understanding constraint satisfaction
   - Needs reasoning about tradeoffs
   - Some ambiguity (multiple valid explanations)

***REMOVED******REMOVED******REMOVED*** Hardest Last (If Experienced)

5. **SOLVER_DIAGNOSTICIAN** (40 hours)
   - Performance analysis + optimization
   - Requires solver algorithm knowledge
   - Complex multi-step diagnosis

6. **RUNTIME_INCIDENT_COMMANDER** (48 hours)
   - Covers 5+ sub-domains
   - Requires systems reasoning
   - High impact if done right

---

***REMOVED******REMOVED*** Need Help?

***REMOVED******REMOVED******REMOVED*** Check These Files

- `skills-new-recommendations.md` - Full analysis, detailed specs
- `.claude/docs/ADDING_A_SKILL.md` - Generic skill creation guide
- `.claude/skills/CORE/SKILL.md` - Registry + examples
- `.claude/skills/acgme-compliance/SKILL.md` - Real example to copy from

***REMOVED******REMOVED******REMOVED*** Pattern Examples to Copy From

- **Simple workflow:** Look at `security-audit` (straightforward validation)
- **Complex workflow:** Look at `MCP_ORCHESTRATION` (multi-step composition)
- **Parallel-safe skill:** Look at `code-review` (read-only, idempotent)
- **Exclusive skill:** Look at `safe-schedule-generation` (exclusive resource access)

---

***REMOVED******REMOVED*** Appendix: Skill Checklist Template

Use this checklist for each skill you implement:

```markdown
***REMOVED*** [ ] SKILL_NAME Implementation Checklist

***REMOVED******REMOVED*** Phase 1: Foundation (Week 1)
- [ ] Directory structure created
- [ ] SKILL.md with complete metadata
- [ ] README.md (< 500 words)
- [ ] Workflow stubs (empty files, clear names)
- [ ] Example scenario list (stubs)

***REMOVED******REMOVED*** Phase 2: Core (Week 2)
- [ ] Implement workflows 1-2 (happy path)
- [ ] Write 3-5 complete scenarios
- [ ] Create Reference docs (rules, patterns)
- [ ] Verify parallel_hints accuracy
- [ ] Test manually on 3+ scenarios

***REMOVED******REMOVED*** Phase 3: Polish (Week 3)
- [ ] Cross-references to other skills
- [ ] Integration test with related skills
- [ ] Performance tuning notes
- [ ] Error handling documented
- [ ] README review (clarity, examples)

***REMOVED******REMOVED*** Phase 4: Submit (Week 4)
- [ ] Quick-invoke command created
- [ ] Registered in CORE/SKILL.md
- [ ] PR description references analysis
- [ ] Documentation complete (no TODOs)
- [ ] Ready for merge
```

---

***REMOVED******REMOVED*** Success Criteria for MVP Release

A skill is "done" (v1.0) when:

1. **Functional:** Can execute happily-path workflow end-to-end
2. **Documented:** README is clear, examples are compelling
3. **Safe:** Parallel hints declared, serialization rules defined
4. **Tested:** Works on 3+ representative scenarios
5. **Integrated:** Quick-invoke command exists, registered in CORE
6. **Discoverable:** Can be found via skill search/browsing

**NOT required for v1:**
- ❌ All edge cases handled (document for v1.1)
- ❌ Full error recovery (ok to fail with helpful message)
- ❌ Advanced options (defer to v2)
- ❌ Performance optimization (ok if slow, improve later)

---

**Ready to build?**

1. Choose your skill (pick an easiest one first)
2. Create directory structure
3. Copy SKILL.md template
4. Follow workflow file format
5. Add 3-5 examples
6. Test on real data
7. Submit for review

**Questions:** Reference `skills-new-recommendations.md` section on that skill's detailed spec.

