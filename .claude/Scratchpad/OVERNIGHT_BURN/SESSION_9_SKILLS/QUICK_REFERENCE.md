# Skills Documentation Quick Reference

**Session:** G2_RECON SEARCH_PARTY - Skills Documentation Templates
**Created:** 2025-12-30
**Purpose:** Fast lookup guide for skill documentation standards

---

## Tier Selection Matrix

```
Choose based on skill complexity and use frequency:

                    LOW              MEDIUM             HIGH
Complexity    └─────────────────────────────────────┘

Low           MINIMAL             MINIMAL           STANDARD
Use           (SKILL.md           (SKILL.md         (SKILL.md +
Frequency     only)               + patterns)       Reference)

Medium        MINIMAL             STANDARD          STANDARD
Use           (SKILL.md)          (SKILL.md +       (SKILL.md +
Frequency     single bullet       Workflows/)       Workflows +
              examples                              Reference)

High          STANDARD            STANDARD          MATURE
Use           (SKILL.md +         (SKILL.md +       (SKILL.md +
Frequency     Reference)          Workflows +       Workflows +
              clear patterns      Reference)        Reference +
                                                    Examples)

Complex       STANDARD            MATURE            MATURE
Multi-                            (Multi-phase      (Complete
Tool          (SKILL.md +         orchestration)    system with
              Reference +                           all tiers)
              clear flows)
```

**Decision Tree:**
- Does this skill orchestrate 3+ tools? → MATURE or STANDARD
- Does this skill have 3+ distinct workflows? → STANDARD or MATURE
- Does this skill require reference material? → STANDARD (minimum)
- Is this a single-purpose skill? → MINIMAL (SKILL.md only)

---

## SKILL.md Required Sections Checklist

**All skills must include:**

- [ ] YAML frontmatter with name, description, model_tier, parallel_hints
- [ ] H1 title matching skill name
- [ ] 1-paragraph overview
- [ ] "When This Skill Activates" (5-8 bullet points)
- [ ] "Integration with Other Skills" section
- [ ] "Escalation Rules" (when to involve humans)
- [ ] "Version & Maintenance" (creation date, last update)

**Strongly recommended (if applicable):**

- [ ] "How This Skill Works" (phases/steps)
- [ ] "Common Use Cases" (2-4 scenarios)
- [ ] "Best Practices" (3-5 practices)
- [ ] "Troubleshooting" (3-5 common issues)
- [ ] "Limitations & Known Issues"

---

## Directory Templates

### Minimal (SKILL.md only)
```
skill-name/
└── SKILL.md
```
**Examples:** code-quality-monitor, pdf, changelog-generator

### Standard (SKILL.md + supporting docs)
```
skill-name/
├── SKILL.md
├── patterns.md          (reference material)
└── reference.md         (detailed info)
```
**Examples:** test-writer, automated-code-fixer, lint-monorepo

### Mature (Full structure with subdir organization)
```
skill-name/
├── SKILL.md
├── Workflows/
│   ├── workflow-1.md
│   ├── workflow-2.md
│   └── error-handling.md
├── Reference/
│   ├── guide.md
│   ├── patterns.md
│   └── tool-index.md
└── Examples/
    ├── scenario-1.md
    └── scenario-2.md
```
**Examples:** MCP_ORCHESTRATION, RESILIENCE_SCORING, docker-containerization

---

## Frontmatter Template (Copy/Paste)

```yaml
---
name: skill-name
description: Single-sentence purpose (60-80 characters for discoverability)
model_tier: haiku|opus
parallel_hints:
  can_parallel_with: [skill1, skill2, skill3]
  must_serialize_with: [skill1]
  preferred_batch_size: 3
---
```

**Notes:**
- `name`: Exact skill identifier (lowercase, hyphens for multi-word)
- `model_tier`: haiku (fast, simple) or opus (complex reasoning)
- `can_parallel_with`: Skills that can run simultaneously
- `must_serialize_with`: Skills that must run sequentially
- `preferred_batch_size`: Optimal concurrent invocations

---

## Common Section Templates

### When This Skill Activates
```markdown
## When This Skill Activates

This skill triggers in these scenarios:

- Condition 1 (specific event or error)
- Condition 2 (detected problem)
- Condition 3 (user explicit request)
- Condition 4 (detected threshold violation)
- Condition 5 (audit/validation finding)
```

### Integration with Other Skills
```markdown
## Integration with Other Skills

### Required Skills
- **skill1**: Why required + interaction pattern
- **skill2**: Why required + interaction pattern

### Complementary Skills
- **skill1**: How they work together
- **skill2**: When to use together

### Dependent Skills
- **skill1**: What they use from this skill
- **skill2**: What they depend on from this
```

### Escalation Rules
```markdown
## Escalation Rules

**Escalate to human when:**

1. Escalation condition 1 (business decision needed)
2. Escalation condition 2 (security concern)
3. Escalation condition 3 (unclear requirements)

**Can handle autonomously:**

1. Autonomous task 1 (fully deterministic)
2. Autonomous task 2 (well-defined rules)
3. Autonomous task 3 (safe to execute)
```

### Version & Maintenance
```markdown
## Version & Maintenance

- **Created:** YYYY-MM-DD
- **Last Updated:** YYYY-MM-DD
- **Maintainer(s):** skill-category or maintainer-name
- **Status:** Active | Experimental | Deprecated
- **Next Review:** YYYY-MM-DD (Next scheduled update)
```

---

## Quality Checklist (Quick)

### Before Committing Skill Documentation

- [ ] YAML frontmatter complete
- [ ] All required sections present
- [ ] At least 2 concrete examples
- [ ] Integration relationships documented
- [ ] Escalation rules clear
- [ ] No relative paths (all absolute)
- [ ] No broken links
- [ ] Version dates accurate
- [ ] 60-80 char description (no jargon)

### For Mature Skills Only

- [ ] Workflows/ directory with 2+ documented workflows
- [ ] Reference/ directory with detailed material
- [ ] Examples/ directory with real scenarios
- [ ] Error handling documentation
- [ ] Performance/security considerations (if applicable)

---

## Workflow Document Template (Minimal)

```markdown
# [Workflow Name]

## Overview
What this workflow does and when to use it.

## Phases

### Phase 1: [Name]
**Duration:** Estimate
**Activity:** What happens

Steps:
1. Step 1
2. Step 2

Outputs:
- Output 1
- Output 2

### Phase 2: [Name]
[Continue...]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Failure Modes
| Mode | Symptom | Recovery |
|------|---------|----------|
| Mode 1 | What user sees | How to fix |

## Related Workflows
- [Other workflow](#)
```

---

## File Path Standards

**Absolute paths only:**

✓ `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/services/schedule.py`
✓ `/app/models/assignment.py`
✗ `../../../backend/app/models.py` (relative, fragile)

**When referencing files:**

- Backend: `/backend/app/[module]/[file].py`
- Frontend: `/frontend/src/[module]/[file].ts[x]`
- Infrastructure: `/docker-compose.yml`, `/.github/workflows/`

---

## Documentation Update Frequency

| Task | Frequency | Effort |
|------|-----------|--------|
| Create new SKILL.md | Per new skill | 1-2 hours |
| Add/update Workflows/ | As needed | 2-3 hours |
| Update for API change | As needed | 15-30 min |
| Link validation | Monthly | 10-15 min |
| Full quarterly audit | Q-start | 2-3 hours |
| Deprecation process | Rarely | 30-45 min |

**Maintenance Owner:** Assign to skill category maintainer or AI agent

---

## Audit Commands

```bash
# Find skills missing SKILL.md
find .claude/skills -maxdepth 1 -type d ! -name "managed" ! -name "CORE" -exec bash -c \
  '[[ ! -f "$1/SKILL.md" ]] && echo "$1"' _ {} \;

# Find outdated documentation (>90 days)
find .claude/skills -name "*.md" -mtime +90

# Check for broken internal links
grep -r "\[.*\](#" .claude/skills/ | grep -v "^Binary"

# Find skills without integration sections
grep -L "Integration with Other Skills" .claude/skills/*/SKILL.md

# Count documentation tier distribution
find .claude/skills -name "SKILL.md" -exec bash -c \
  '[[ -d "$(dirname $1)/Workflows" ]] && echo "mature"; [[ -f "$(dirname $1)/reference.md" ]] && echo "standard"; echo "basic"' _ {} \; | sort | uniq -c
```

---

## Integration Relationships Map

**Core Infrastructure Skills:**
- startup → everything else (prerequisite)
- MCP_ORCHESTRATION ↔ production-incident-responder (co-dependent)
- database-migration ↔ automated-code-fixer (blocking relationship)

**Code Quality Skills:**
- test-writer → code-review (test verification)
- code-review ↔ automated-code-fixer (QA gate)
- lint-monorepo → all code changes (pre-commit)

**Deployment Skills:**
- constraint-preflight → safe-schedule-generation (validation before write)
- safe-schedule-generation → production-incident-responder (fallback if failure)

**System Operations:**
- docker-containerization ↔ security-audit (layered security)
- production-incident-responder → systematic-debugger (incident response)

---

## Common Mistakes to Avoid

❌ **Relative paths**: `../../backend/app/models.py` → Use absolute paths
❌ **Vague activation triggers**: "When needed" → Use specific conditions
❌ **No escalation rules**: Unclear when to call humans → Always define boundaries
❌ **Orphaned integrations**: "Works with everything" → List specific relationships
❌ **Missing version info**: Don't know if docs are current → Always timestamp
❌ **Dead code examples**: Examples don't run → Test before publishing
❌ **Workflow ambiguity**: "Do stuff then validate" → Explicit phases with outputs
❌ **No troubleshooting**: Users can't fix errors → Include 3+ common issues

---

## Implementation Priority

### Week 1 (Baseline)
1. Ensure all 44 skills have complete SKILL.md
2. Fix missing frontmatter (2 skills)
3. Establish quarterly maintenance schedule

### Week 2 (Enrichment)
1. Upgrade 10 basic skills to standard tier
2. Create missing integration sections
3. Add missing escalation rules

### Week 3 (Optimization)
1. Create cross-skill integration matrix
2. Add automated link checking to CI/CD
3. Update discovery mechanisms

### Week 4 (Polish)
1. Review and approve all changes
2. Document maintenance procedures
3. Train team on new templates

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Skills with SKILL.md | 42/44 (95%) | 44/44 (100%) |
| With integration section | 35/44 (80%) | 44/44 (100%) |
| With escalation rules | 38/44 (86%) | 44/44 (100%) |
| Standard tier or better | 13/44 (30%) | 25/44 (57%) |
| Mature tier | 3/44 (7%) | 12/44 (27%) |
| Updated <90 days | 32/44 (73%) | 40/44 (91%) |
| Average discovery time | 10-15 min | 2-3 min |
| Developer satisfaction | Unknown | 4.0/5.0 |

---

**For detailed information, see:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Scratchpad/OVERNIGHT_BURN/SESSION_9_SKILLS/skills-documentation-templates.md`
