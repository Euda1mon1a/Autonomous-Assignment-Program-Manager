# Agent Skills Reference

> **Complete reference for AI Agent Skills in the Residency Scheduler**
>
> Last Updated: 2025-12-23

---

## Overview

Agent Skills are packaged domain expertise that AI assistants (Claude Code, OpenAI Codex, GitHub Copilot, etc.) can use to perform specialized tasks. Skills follow the [Agent Skills specification](https://agentskills.io) for cross-agent compatibility.

### How Skills Work

```
User: "Is this code secure?"
       │
       ▼
┌──────────────────────────────────────┐
│  AI Agent detects "security" keyword │
│  Loads security-audit skill          │
│  Applies skill procedures            │
│  Returns security analysis           │
└──────────────────────────────────────┘
```

Skills provide:
- **Domain Knowledge**: Specialized procedures and best practices
- **Activation Context**: When the skill should be used
- **Integration Points**: How the skill connects with tools and other skills
- **Escalation Rules**: When to ask for human help

---

## Skills Directory

All skills are located in `.claude/skills/`:

```
.claude/skills/
├── acgme-compliance/           # ACGME regulatory compliance
│   ├── SKILL.md
│   ├── thresholds.md
│   └── exceptions.md
├── automated-code-fixer/       # Auto-fix code issues
│   ├── SKILL.md
│   ├── reference.md
│   └── examples.md
├── code-quality-monitor/       # Quality gate enforcement
│   └── SKILL.md
├── code-review/                # Code review procedures
│   └── SKILL.md
├── database-migration/         # Alembic migration expertise
│   └── SKILL.md
├── pr-reviewer/                # Pull request review
│   └── SKILL.md
├── production-incident-responder/  # Crisis response
│   └── SKILL.md
├── schedule-optimization/      # Multi-objective optimization
│   └── SKILL.md
├── security-audit/             # Security auditing
│   └── SKILL.md
├── swap-management/            # Shift swap workflows
│   └── SKILL.md
└── test-writer/                # Test generation
    └── SKILL.md
```

---

## Skills Reference

### Domain-Specific Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `acgme-compliance` | ACGME regulatory expertise | Schedule validation, compliance checks |
| `schedule-optimization` | Multi-objective optimization | Schedule generation, workload balancing |
| `swap-management` | Shift swap workflows | Swap requests, partner matching |

### Development Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `code-review` | Code review procedures | Reviewing generated code, quality checks |
| `automated-code-fixer` | Auto-fix code issues | Test failures, linting errors |
| `code-quality-monitor` | Quality gate enforcement | Pre-commit validation, PR checks |
| `test-writer` | Test generation | Writing pytest/Jest tests |
| `database-migration` | Alembic migration expertise | Schema changes, migrations |
| `pr-reviewer` | Pull request review | PR validation, merge decisions |
| `security-audit` | Security auditing | HIPAA, OPSEC/PERSEC compliance |

### Operations Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `production-incident-responder` | Crisis response | System failures, emergency coverage |

---

## Detailed Skill Documentation

### acgme-compliance

**Purpose**: Expert knowledge of ACGME regulations for medical residency scheduling.

**Activates When**:
- Validating schedule compliance
- Checking resident work hours
- Verifying supervision ratios
- Answering ACGME-related questions

**Key Rules Enforced**:
| Rule | Requirement |
|------|-------------|
| 80-Hour Rule | Max 80 hours/week averaged over 4 weeks |
| 1-in-7 Rule | One 24-hour period off every 7 days |
| Supervision | PGY-1: 2:1, PGY-2/3: 4:1 faculty ratio |

**Integration**: Works with MCP tool `validate_acgme_compliance`

---

### automated-code-fixer

**Purpose**: Automatically detect and fix code issues with strict quality controls.

**Activates When**:
- Test failures detected
- Linting errors reported
- Type-checking errors found
- Build failures encountered

**Quality Gates**:
1. All tests must pass after fix
2. Linting must pass (ruff, black)
3. Type checking must pass (mypy)
4. No security issues introduced
5. Architecture compliance maintained

**Escalation Triggers**:
- Fix requires model/migration changes
- Fix affects ACGME compliance logic
- Multiple interdependent failures

---

### code-quality-monitor

**Purpose**: Proactive code health monitoring and quality gate enforcement.

**Activates When**:
- Before committing changes
- During PR reviews
- When validating code health

**Standards Enforced**:
| Metric | Target | Critical |
|--------|--------|----------|
| Test Coverage | >= 80% | >= 70% |
| Type Coverage | 100% public APIs | >= 90% |
| Cyclomatic Complexity | <= 10 | <= 15 |

---

### code-review

**Purpose**: Structured code review for AI-generated implementations.

**Activates When**:
- Reviewing Claude-generated code
- Auditing for vulnerabilities
- Validating against project standards
- Before committing significant changes

**Review Focus Areas**:
1. Code Quality (structure, naming, DRY)
2. Security & Safety (validation, auth, OWASP)
3. Performance (algorithms, queries, async)
4. Maintainability (tests, types, docs)
5. Standards Compliance (CLAUDE.md rules)

**Output Format**:
- CRITICAL: Must fix before merge
- WARNING: Should fix
- INFO: Nice to have
- GOOD: Well-implemented patterns

---

### database-migration

**Purpose**: Safe database schema evolution using Alembic migrations.

**Activates When**:
- Adding new database models
- Modifying existing fields
- Creating foreign key relationships
- Renaming/dropping columns

**Core Principle**: NEVER modify models without creating a migration.

**Migration Patterns**:
- Adding nullable columns (safe)
- Adding non-nullable columns (requires default)
- Adding indexes
- Adding foreign keys
- Renaming columns
- Dropping columns (dangerous)

**Safety Checklist**:
- [ ] Review autogenerated migration
- [ ] Test upgrade: `alembic upgrade head`
- [ ] Test downgrade: `alembic downgrade -1`
- [ ] Verify data integrity
- [ ] Commit migration with model change

---

### pr-reviewer

**Purpose**: Comprehensive pull request review with quality gates.

**Activates When**:
- Reviewing open PRs
- Creating PR descriptions
- Validating changes before merge

**Review Categories**:
1. Code Quality (architecture, types, docs)
2. Testing (coverage, edge cases)
3. Security (secrets, validation, auth)
4. Architecture (patterns, async, schemas)
5. Documentation (PR description, comments)

**Decision Matrix**:
| Gate | Pass | Block |
|------|------|-------|
| Tests | All pass | Any failure |
| Linting | 0 errors | Any error |
| Security | No issues | Any vulnerability |
| Coverage | >= 70% | < 60% |

**GitHub CLI Integration**:
```bash
gh pr view <number>
gh pr checks <number>
gh pr review <number> --approve
gh pr merge <number> --squash
```

---

### production-incident-responder

**Purpose**: Crisis response for production system failures.

**Activates When**:
- Health check fails
- ACGME violations detected
- Utilization exceeds 80%
- Coverage gaps identified
- Defense level escalates

**Response Protocol**:
1. DETECTION (automated monitoring)
2. DIAGNOSIS (root cause analysis)
3. RESPONSE (human approval required for RED/BLACK)
4. RECOVERY (homeostasis monitoring)

**MCP Tool Integration**:
- `check_utilization_threshold_tool`
- `get_defense_level_tool`
- `run_contingency_analysis_resilience_tool`
- `execute_sacrifice_hierarchy_tool`

---

### schedule-optimization

**Purpose**: Multi-objective schedule optimization using constraint programming.

**Activates When**:
- Generating new schedules
- Optimizing existing schedules
- Balancing workload distribution
- Resolving conflicts

**Optimization Objectives**:
| Type | Objectives |
|------|------------|
| Hard (P0) | ACGME compliance, qualifications, no double-booking |
| Soft | Fairness (0.25), preferences (0.20), continuity (0.20), resilience (0.20), efficiency (0.15) |

**Uses**: Google OR-Tools CP-SAT solver

---

### security-audit

**Purpose**: Security auditing for healthcare and military contexts.

**Activates When**:
- Auth/authz code changes
- PHI data handling
- Military schedule data
- API endpoint review
- Pre-deployment checks

**Security Domains**:
1. HIPAA Compliance (access control, audit logging, encryption)
2. OPSEC/PERSEC (never commit real names, schedules, TDY data)
3. OWASP Top 10 (injection, auth, crypto, etc.)

**Never Commit**:
| Data Type | Risk |
|-----------|------|
| Resident/Faculty Names | PERSEC |
| Schedule Assignments | OPSEC |
| TDY/Deployment Data | OPSEC |

---

### swap-management

**Purpose**: Expert procedures for managing schedule swaps.

**Activates When**:
- Processing swap requests
- Finding compatible partners
- Resolving conflicts
- Emergency coverage

**Swap Types**:
1. One-to-One (direct exchange)
2. Absorb (give away shift)
3. Three-Way (circular exchange)

**Validation Checklist**:
- [ ] Both parties consent
- [ ] Qualifications verified
- [ ] 80-hour limit maintained
- [ ] 1-in-7 day off preserved
- [ ] Supervision ratios valid

---

### test-writer

**Purpose**: Generate comprehensive test suites for Python and TypeScript.

**Activates When**:
- New code without tests
- Coverage below threshold
- Bug fix needs regression test
- Complex logic needs coverage

**Test Categories**:
1. Unit Tests (single function/method)
2. Service Tests (business logic)
3. API Tests (HTTP endpoints)
4. Integration Tests (database operations)

**Coverage Requirements**:
| Layer | Target | Minimum |
|-------|--------|---------|
| Services | 90% | 80% |
| Controllers | 85% | 75% |
| Models | 80% | 70% |

**Frameworks**:
- Python: pytest with async support
- TypeScript: Jest + React Testing Library

---

## Creating Custom Skills

### Step 1: Create Directory

```bash
mkdir -p .claude/skills/my-skill
```

### Step 2: Create SKILL.md

```markdown
---
name: my-skill
description: Brief description for skill matching
---

# My Skill

Detailed instructions...

## When This Skill Activates
- Condition 1
- Condition 2

## Procedures
1. Step one
2. Step two

## Escalation Rules
**Escalate to human when:**
1. Condition A
2. Condition B
```

### Step 3: Add Supporting Files (Optional)

- `reference.md` - Detailed procedures
- `examples.md` - Example scenarios
- `thresholds.md` - Configurable values

### Step 4: Test

Ask Claude about the skill topic and verify it activates.

---

## Skill Specification

Skills follow the [Agent Skills Specification](https://agentskills.io):

### SKILL.md Format

```yaml
---
name: skill-name          # Required: kebab-case identifier
description: Brief desc   # Required: Used for skill matching
---

# Skill Title

[Markdown content with procedures, rules, examples]
```

### Progressive Loading

- **At startup**: Only frontmatter loaded (~100 tokens)
- **On activation**: Full markdown content loaded
- **Benefits**: Fast startup, low memory, context-efficient

### Cross-Agent Compatibility

Skills work with:
- Claude Code (Web, CLI, IDE)
- OpenAI Codex
- GitHub Copilot
- Google Antigravity
- Any MCP-compatible client

---

## Integration with MCP Tools

Many skills integrate with MCP (Model Context Protocol) tools:

| Skill | Primary MCP Tools |
|-------|-------------------|
| acgme-compliance | `validate_acgme_compliance` |
| production-incident-responder | `check_utilization_threshold_tool`, `get_defense_level_tool` |
| swap-management | `analyze_swap_compatibility`, `validate_swap` |
| schedule-optimization | `generate_schedule`, `optimize_schedule` |

See `mcp-server/` for tool implementations.

---

## Best Practices

### Skill Design

1. **Clear activation triggers**: Description should match user queries
2. **Structured procedures**: Step-by-step workflows
3. **Escalation rules**: Define when to ask humans
4. **Integration points**: Connect with tools and other skills

### Skill Maintenance

1. **Version control**: Skills evolve with codebase
2. **Team alignment**: Shared standards across developers
3. **Documentation**: Keep SKILL.md current
4. **Testing**: Verify skill activation with example queries

---

## Related Documentation

- [AI Agent User Guide](../guides/AI_AGENT_USER_GUIDE.md) - Complete agent setup
- [AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md) - Git and workflow rules
- [CLAUDE.md](../../CLAUDE.md) - Project guidelines
- [Agent Skills Specification](https://agentskills.io) - External spec
