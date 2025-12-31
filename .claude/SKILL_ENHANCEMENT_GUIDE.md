# Skill Enhancement Guide

> **Last Updated:** 2025-12-31
> **Purpose:** Master reference for skill structure, enhancement patterns, and best practices

---

## Table of Contents

1. [Skill Architecture](#skill-architecture)
2. [YAML Frontmatter Specification](#yaml-frontmatter-specification)
3. [Enhancement Framework](#enhancement-framework)
4. [Parallel Hints Strategy](#parallel-hints-strategy)
5. [Skill Categories](#skill-categories)
6. [Quality Checklist](#quality-checklist)
7. [Integration Patterns](#integration-patterns)
8. [Escalation Rules](#escalation-rules)

---

## Skill Architecture

### Directory Structure

```
.claude/skills/
├── [skill-name]/
│   ├── SKILL.md                    # Main skill document
│   ├── Workflows/                  # (Optional) Workflow definitions
│   │   ├── workflow-1.md
│   │   └── workflow-2.md
│   └── Reference/                  # (Optional) Reference materials
│       ├── checklists.md
│       └── patterns.md
└── session-documentation.md        # Historical skill documentation
```

### Minimal Skill File

Every skill must have:

```yaml
---
name: skill-name
description: One-line description of what the skill does
model_tier: opus  # or haiku/sonnet for lighter skills
parallel_hints:
  can_parallel_with: [skill1, skill2]
  must_serialize_with: [skill3]
  preferred_batch_size: 3
---

# [Skill Name] Skill

Content here...
```

---

## YAML Frontmatter Specification

### Required Fields

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `name` | string | Skill identifier (kebab-case) | `code-review` |
| `description` | string | What the skill does (1-2 sentences) | `Review generated code for bugs...` |
| `model_tier` | enum | Minimum model capability | `opus` \| `sonnet` \| `haiku` |

### Optional But Recommended

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `parallel_hints.can_parallel_with` | array | Skills safe to run in parallel | `[test-writer, lint-monorepo]` |
| `parallel_hints.must_serialize_with` | array | Skills that require sequential execution | `[database-migration]` |
| `parallel_hints.preferred_batch_size` | number | Optimal concurrency level | `5` |
| `context_hints` | object | Context management guidance | See below |
| `escalation_triggers` | array | Conditions requiring human approval | `[auth-changes, schema-modifications]` |

### Context Hints Structure

```yaml
context_hints:
  max_file_context: 50    # Max files to read for context
  compression_level: 2     # 0=none, 1=light, 2=aggressive
  requires_git_context: true
  requires_db_context: false
```

### Escalation Triggers

```yaml
escalation_triggers:
  - pattern: "^backend/app/core/"
    reason: "Core infrastructure changes require review"
  - pattern: "^alembic/versions/"
    reason: "Database migrations need approval"
  - keyword: ["DROP", "DELETE", "TRUNCATE"]
    reason: "Destructive database operations"
```

---

## Enhancement Framework

### 10-Point Enhancement Checklist

Every skill should be enhanced with:

1. **Clear Activation Rules** - When does this skill trigger?
2. **Methodology Section** - Step-by-step process
3. **Integration Points** - How does this connect to other skills?
4. **Escalation Rules** - When to ask for human approval?
5. **Quick Reference Commands** - Copy-pasteable commands
6. **Common Patterns** - Real code examples showing good/bad practices
7. **Context Management** - How to handle context efficiently
8. **Parallel Hints** - Can this run in parallel with other skills?
9. **Error Handling** - What to do when something fails?
10. **Validation Checklist** - How to verify success?

### Enhancement Template

```markdown
---
name: [skill-name]
description: [Clear, actionable description]
model_tier: opus
parallel_hints:
  can_parallel_with: [compatible-skills]
  must_serialize_with: [requires-sequence]
  preferred_batch_size: [optimal-concurrency]
---

# [Skill Name] Skill

## When This Skill Activates

- Trigger condition 1
- Trigger condition 2
- Trigger condition 3

## Methodology

### Phase 1: [Name]
[Detailed steps...]

### Phase 2: [Name]
[Detailed steps...]

## Integration with Other Skills

### With skill-a
[How these skills interact]

### With skill-b
[How these skills interact]

## Escalation Rules

**Escalate to human when:**
1. [Condition 1]
2. [Condition 2]

## Quick Reference Commands

[Copy-paste ready commands]

## Common Patterns

### Pattern 1: Good Implementation
[Code example]

### Pattern 2: Common Mistake
[Code example and fix]

## Context Management

- **Input context size:** [expected size]
- **Compression strategy:** [how to compress if needed]
- **Required context:** [what must be in context]

## Validation Checklist

- [ ] [Validation 1]
- [ ] [Validation 2]
```

---

## Parallel Hints Strategy

### Compatibility Matrix

```
Legend:
✓ = Can run in parallel
- = Must run sequentially
```

### By Category

#### Safe to Parallelize
- `code-review` + `test-writer`
- `lint-monorepo` + `security-audit`
- `test-writer` + `dependency-auditor`
- `api-documenter` + `changelog-generator`

#### Must Serialize
- `database-migration` + any schema change
- `safe-schedule-generation` + `swap-execution`
- `schedule-verification` + `schedule-optimization`
- `compliance-validation` + any schedule change

### Preferred Batch Sizes

| Skill | Batch Size | Reason |
|-------|-----------|--------|
| code-review | 5 | Can review multiple files |
| test-writer | 3 | Complex test generation |
| lint-monorepo | 10 | Lightweight, no dependencies |
| database-migration | 1 | Must be sequential |
| security-audit | 2 | Requires careful attention |

---

## Skill Categories

### 1. Code Quality (5 skills)
- `code-review` - Comprehensive code review
- `test-writer` - Test generation
- `lint-monorepo` - Linting and formatting
- `code-quality-monitor` - Quality gates
- `automated-code-fixer` - Auto-fix issues

### 2. Security & Compliance (4 skills)
- `security-audit` - Security vulnerability assessment
- `acgme-compliance` - ACGME rule validation
- `dependency-auditor` - CVE detection
- `COMPLIANCE_VALIDATION` - Institutional compliance

### 3. Architecture & Design (5 skills)
- `constraint-preflight` - Constraint validation
- `api-documenter` - API documentation
- `database-migration` - Schema management
- `fastapi-production` - FastAPI best practices
- `context-aware-delegation` - Agent coordination

### 4. Testing & Validation (4 skills)
- `test-scenario-framework` - Test scenario management
- `schedule-verification` - Schedule validation
- `test-writer` - Test generation
- `coverage-reporter` - Coverage analysis

### 5. Deployment & Operations (4 skills)
- `docker-containerization` - Container management
- `deployment-validator` - Release validation
- `performance-profiler` - Performance analysis
- `incident-responder` - Production incident response

### 6. Scheduling Specific (6 skills)
- `schedule-optimization` - Solver optimization
- `safe-schedule-generation` - Safe schedule generation
- `SCHEDULING` - Schedule generation
- `schedule-verification` - Schedule validation
- `swap-analyzer` - Swap compatibility
- `resilience-monitor` - Resilience monitoring

---

## Quality Checklist

### Every Skill Must Have

- [ ] Clear YAML frontmatter with all required fields
- [ ] "When This Skill Activates" section
- [ ] At least 3 methodology phases or steps
- [ ] Integration points with 2+ other skills
- [ ] At least 2 escalation triggers
- [ ] Quick reference commands (copy-pasteable)
- [ ] 2+ good patterns and 2+ anti-patterns
- [ ] Context management guidance
- [ ] Validation checklist (5+ items)
- [ ] Parallel hints configured

### Enhanced Skills Should Have

- [ ] Detailed activation rules (not just bullet points)
- [ ] Phase-based methodology with numbered steps
- [ ] Error recovery procedures
- [ ] Context compression strategies
- [ ] Batching recommendations
- [ ] Performance notes
- [ ] Common failure modes documented
- [ ] Related skills integration matrix
- [ ] Human escalation decision tree
- [ ] Worked examples (not just templates)

---

## Integration Patterns

### Skill Chaining

Some skills naturally chain together. Document these patterns:

```yaml
# Example: Code generation workflow
chains:
  - name: "New Feature Implementation"
    steps:
      - code-review  # Review requirements
      - code-generation  # Generate implementation
      - test-writer  # Write tests
      - lint-monorepo  # Format code
      - security-audit  # Check security
      - pr-reviewer  # Prepare PR

  - name: "Database Migration"
    steps:
      - database-migration  # Create migration
      - test-writer  # Add tests
      - code-review  # Review changes
      - deployment-validator  # Validate deployment
```

### Skill Composition

Document how skills can be used together:

```
[Code Generation]
        ↓
    [Code Review]
    ↙         ↘
[Test Writer] [Security Audit]
    ↘         ↙
    [Lint & Format]
        ↓
    [PR Reviewer]
```

---

## Escalation Rules

### Decision Tree

```
Does change touch authentication?
├─ YES → Require security-audit + human approval
└─ NO → Continue

Does change modify database schema?
├─ YES → Require database-migration approval
└─ NO → Continue

Does change affect ACGME compliance?
├─ YES → Require acgme-compliance + human review
└─ NO → Continue

Does change involve cryptography?
├─ YES → Require security-audit + human approval
└─ NO → Continue

Does change add third-party dependencies?
├─ YES → Require dependency-auditor + human review
└─ NO → Automatic approval (if tests pass)
```

---

## Implementation Priority

### Phase 1: Core Enhancement (Current Session)
1. Enhance 6 core skills (code-review, test-writer, security-audit, database-migration, pr-reviewer, acgme-compliance)
2. Create prompt library with 15 categories
3. Create context management patterns

### Phase 2: New Skill Creation (If Time Permits)
1. Create 10 new specialized skills
2. Add workflow examples
3. Add reference materials

### Phase 3: Integration & Testing
1. Create skill validation test suite
2. Add skill composition patterns
3. Document skill usage metrics

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Enhanced skills | 10 | TBD |
| New skills created | 10 | TBD |
| Prompt library entries | 15+ | TBD |
| Context pattern docs | 5+ | TBD |
| Skill validation tests | 40+ | TBD |
| Integration examples | 10+ | TBD |
| Common patterns | 50+ | TBD |

---

## References

- **CLAUDE.md** - Project guidelines
- **AI_RULES_OF_ENGAGEMENT.md** - AI agent rules
- **SESSION_9_SKILLS.md** - Previous session findings
- **PROMPT_LIBRARY.md** - Prompt templates (created in this session)
- **CONTEXT_PATTERNS.md** - Context management (created in this session)

