# Anthropic Skills Open Standard - Exploration & Implementation

> **Created:** 2025-12-20
> **Status:** Exploration / Prototype
> **Purpose:** Research and implement automated code fixing with strict quality gates

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What Are Anthropic Skills?](#what-are-anthropic-skills)
3. [Skills Open Standard](#skills-open-standard)
4. [Implemented Skills](#implemented-skills)
5. [Strict Quality Parameters](#strict-quality-parameters)
6. [The "IT Guy" Concept](#the-it-guy-concept)
7. [MCP Integration for Production Incidents](#mcp-integration-for-production-incidents)
8. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
9. [Future Directions](#future-directions)

---

## Executive Summary

This document explores Anthropic's Skills Open Standard and how it can be leveraged to create an automated "IT helper" for this codebase. The goal is to have LLM assistance that:

1. **Has strict parameters** - Only fixes code when quality gates pass
2. **Can fix things on the fly** - Automated detection and remediation
3. **Knows when to escalate** - Doesn't break things trying to fix them
4. **Follows project standards** - Adheres to CLAUDE.md guidelines

---

## What Are Anthropic Skills?

**Skills** are reusable modules that extend Claude's capabilities with specialized knowledge and procedures. Think of them as "packages of expertise" that Claude automatically loads when relevant.

### Key Characteristics

| Feature | Description |
|---------|-------------|
| **Folders of Instructions** | Directory with `SKILL.md` + supporting files |
| **Model-Invoked** | Claude decides when to use, not user-triggered |
| **Progressive Disclosure** | Only loads what's needed to save context |
| **Portable** | Works across Claude Code, Claude.ai, API |

### Three-Level Architecture

```
Level 1: Metadata (~100 tokens)
├── Name + Description in system prompt
├── Loaded at startup
└── Used to decide when to activate

Level 2: Core Instructions
├── Full SKILL.md content
├── Loaded when skill activates
└── Main procedures and rules

Level 3+: Supporting Files
├── reference.md, examples.md
├── Scripts, templates
└── Loaded on-demand
```

### Directory Structure

```
.claude/skills/
├── automated-code-fixer/
│   ├── SKILL.md          # Core skill definition
│   ├── reference.md      # Detailed fix patterns
│   └── examples.md       # Common fix scenarios
│
└── code-quality-monitor/
    └── SKILL.md          # Quality gate enforcement
```

---

## Skills Open Standard

### What Was Released (December 18, 2025)

Anthropic published **Agent Skills as an open standard** at **agentskills.io**.

### Why This Matters

1. **Open Format** - Any AI platform can adopt the SKILL.md format
2. **Platform Neutral** - Works with Microsoft, OpenAI, Cursor, etc.
3. **Ecosystem Growth** - Prebuilt skills from Canva, Notion, Figma, Atlassian
4. **No Vendor Lock-in** - Skills are portable across platforms

### Adoption Pattern

Similar to how Anthropic donated MCP to the Linux Foundation (December 2025), Skills follows the pattern:

```
Solve real problems → Release openly → Drive adoption through usefulness
```

### SKILL.md Format

```markdown
---
name: skill-name
description: Brief description (max 1024 chars)
allowed-tools: Read, Grep, Glob  # Optional restrictions
---

# Skill Name

Instructions for Claude to follow...
```

---

## Implemented Skills

### 1. automated-code-fixer

**Purpose:** Automated IT helper for detecting and fixing code issues.

**Triggers:**
- Test failures
- Linting errors
- Type-checking errors
- Security vulnerabilities
- Build failures

**Strict Quality Gates:**

| Gate | Requirement | Action on Fail |
|------|-------------|----------------|
| Test Validation | All tests pass | Block fix |
| Linting | Zero errors | Block fix |
| Type Safety | mypy passes | Block fix |
| Security | No new vulnerabilities | Block fix |
| Architecture | Follow layered pattern | Block fix |

**Escalation Rules:**
- Database/migration changes
- ACGME compliance logic
- Authentication code
- Unclear requirements
- >30 minute fixes

### 2. code-quality-monitor

**Purpose:** Proactive health monitoring and quality enforcement.

**Triggers:**
- Before commits
- During PR reviews
- Code health validation
- Multiple edits made

**Quality Standards:**

```
Python Backend:
├── Test Coverage: >= 80% (critical: 70%)
├── Type Coverage: 100% public APIs
├── Complexity: <= 10 cyclomatic
├── Function Length: <= 50 lines
└── File Length: <= 500 lines

TypeScript Frontend:
├── Type Safety: No 'any'
├── Test Coverage: >= 75%
├── Component Size: <= 200 lines
└── Hook Complexity: <= 5 deps
```

---

## Strict Quality Parameters

### The "Stop If Not Passing" Philosophy

The key insight is that **LLM fixes should only proceed when quality gates pass**. This prevents:

1. Cascading failures from bad fixes
2. Technical debt from quick patches
3. Security vulnerabilities from hasty changes
4. Test rot from skipping validation

### Quality Gate Hierarchy

```
Gate 1: MUST PASS (Blocking)
├── All tests pass
├── No linting errors
├── No type errors
└── No critical security issues

Gate 2: SHOULD PASS (Warning)
├── Coverage >= 70%
├── No new complexity
├── Documentation updated
└── No TODOs without tickets

Gate 3: NICE TO HAVE (Info)
├── Coverage >= 80%
├── All functions documented
├── No magic numbers
└── Consistent naming
```

### Validation Commands

```bash
# Quick validation
pytest --tb=short && ruff check app/ && mypy app/

# Comprehensive validation
pytest --cov=app --cov-fail-under=70
ruff check app/ tests/
black --check app/ tests/
mypy app/ --python-version 3.11
bandit -r app/ -ll
```

---

## The "IT Guy" Concept

### What We're Building

An automated assistant that acts like a skilled IT support person:

1. **Monitors for Issues** - Watches for failures and problems
2. **Diagnoses Root Causes** - Doesn't just fix symptoms
3. **Applies Safe Fixes** - Only when confident
4. **Escalates When Needed** - Knows its limits
5. **Documents Everything** - Leaves clear trails

### Workflow

```
Issue Detected
     ↓
Diagnose Root Cause
     ↓
Can fix safely? ──No──→ Escalate to Human
     ↓ Yes
Apply Fix
     ↓
Run Quality Gates
     ↓
Gates Pass? ──No──→ Revert & Escalate
     ↓ Yes
Commit Fix with Report
```

### Escalation Decision Tree

```
Is the fix...
├── Changing database models? → ESCALATE
├── Touching auth/security? → ESCALATE
├── Affecting ACGME logic? → ESCALATE
├── Requiring new dependencies? → ESCALATE
├── Taking > 30 minutes? → ESCALATE
├── Unclear on requirements? → ESCALATE
└── Otherwise → PROCEED with fix
```

### Rollback Protocol

If a fix causes additional failures:

1. Immediately revert changes
2. Document what went wrong
3. Escalate to human with full context
4. Do not attempt to fix the fix

---

## MCP Integration for Production Incidents

### The Missing Piece: Acting on Live Systems

Skills handle code-level issues, but what about production system failures? That's where **MCP (Model Context Protocol)** comes in. This project already has a comprehensive MCP server with 13 resilience tools.

### Implemented Skill: production-incident-responder

**Purpose:** Crisis response for production system failures using MCP tools.

**Triggers:**
- Production health check fails
- ACGME compliance violations
- Utilization exceeds 80% threshold
- Coverage gaps identified
- Circuit breaker trips
- Defense level escalates to ORANGE+

### MCP Resilience Tools Available

| Tool | Industry Pattern | Purpose |
|------|-----------------|---------|
| `check_utilization_threshold_tool` | Queuing Theory | 80% threshold monitoring |
| `get_defense_level_tool` | Nuclear Safety | 5-level graduated response |
| `run_contingency_analysis_resilience_tool` | Power Grid | N-1/N-2 vulnerability |
| `get_static_fallbacks_tool` | AWS/Cloud | Pre-computed backups |
| `execute_sacrifice_hierarchy_tool` | Triage | Load shedding |
| `analyze_homeostasis_tool` | Biology | Feedback loop health |
| `calculate_blast_radius_tool` | Nuclear/Cloud | Failure containment |
| `analyze_hub_centrality_tool` | Network Theory | Single point failures |
| `check_mtf_compliance_tool` | Military | DRRS readiness |

### How Skills + MCP Work Together

```
Production Issue Detected
         ↓
production-incident-responder skill activates
         ↓
Connects to MCP Server
         ↓
Queries Resilience Tools
├── check_utilization_threshold_tool → Current load
├── get_defense_level_tool → Severity assessment
├── run_contingency_analysis_resilience_tool → Impact analysis
└── get_static_fallbacks_tool → Available responses
         ↓
Generates Incident Report
         ↓
Severity Assessment
├── GREEN/YELLOW → Automated monitoring, recommendations
├── ORANGE → HUMAN APPROVAL REQUIRED for mitigations
└── RED/BLACK → Emergency escalation, documentation
         ↓
Execute Response (with approval)
├── Activate fallback schedules
├── Execute sacrifice hierarchy
├── Generate compliance documentation
└── Monitor recovery
```

### Defense Levels (Nuclear Safety Pattern)

| Level | Color | Actions Available |
|-------|-------|-------------------|
| 1 | GREEN | Normal operations, continuous monitoring |
| 2 | YELLOW | Warning state, suspend optional activities |
| 3 | ORANGE | Critical, suspend admin/research |
| 4 | RED | Emergency, suspend non-clinical education |
| 5 | BLACK | Catastrophic, essential services only |

### Example: Faculty Absence Crisis

```
1. DETECT (Automated)
   MCP: check_utilization_threshold_tool
   Result: Utilization at 85% (above 80% threshold)
   → Defense Level: ORANGE

2. DIAGNOSE (Automated)
   MCP: run_contingency_analysis_resilience_tool
   Result: N-1 resilience FAILED
   → 8 coverage gaps, 2 ACGME violations predicted

3. RESPOND (Human Approval Required)
   MCP: get_static_fallbacks_tool(scenario="dual_absence")
   MCP: execute_sacrifice_hierarchy_tool(simulate_only=true)

   Options presented:
   a) Activate fallback schedule
   b) Suspend optional education (free 4 blocks)
   c) Request external coverage

4. RECOVER (Automated monitoring)
   MCP: analyze_homeostasis_tool
   → Monitor until equilibrium restored
```

### MCP Server Setup

```bash
# Start MCP server
cd mcp-server
pip install -e .
python -m scheduler_mcp.server

# Configure in Claude Desktop
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "/path/to/mcp-server"
    }
  }
}
```

### Key Principle: Human-in-the-Loop for Critical Decisions

The production-incident-responder skill **never** executes critical actions without human approval:

| Action | Approval Required |
|--------|-------------------|
| Monitoring, analysis, simulation | No |
| Swap facilitation (single) | No |
| Fallback schedule activation | **YES** |
| Load shedding execution | **YES** |
| External staffing request | **YES** |
| Circuit breaker override | **YES** |

---

## Integration with Existing Infrastructure

### Slash Commands (User-Invoked)

The project already has these in `.claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/run-tests` | Execute pytest test suite |
| `/lint-fix` | Auto-format with Black/Ruff |
| `/health-check` | System health validation |
| `/check-compliance` | ACGME compliance verification |
| `/db-migrate` | Database migration help |
| `/review-pr` | PR review assistance |

### Skills (Model-Invoked)

Skills complement commands by being automatic:

| Feature | Slash Commands | Skills |
|---------|----------------|--------|
| Invocation | User types `/command` | Claude decides automatically |
| Use Case | Explicit actions | Background intelligence |
| Discovery | `/help` shows list | Loaded at startup |
| Best For | Specific tasks | Recurring patterns |

### Working Together

```
User: "Fix the failing tests"

Claude thinks: This involves code fixing → activate automated-code-fixer skill

Skill provides:
- Quality gate rules
- Fix patterns
- Escalation criteria

Claude uses: /run-tests command to validate

Result: Structured fix with quality assurance
```

---

## Future Directions

### Near-Term (Next Sprint)

1. **Test the Skills** - Run through common fix scenarios
2. **Tune Thresholds** - Adjust quality gates based on reality
3. **Add More Patterns** - Document project-specific fixes
4. **Hook Integration** - Consider pre-commit hooks

### Medium-Term (Next Quarter)

1. **Session Start Hook** - Auto-run health check on new sessions
2. **CI/CD Integration** - Skills inform GitHub Actions
3. **Metrics Dashboard** - Track fix success rates
4. **Team Skills** - Shared skills for common patterns

### Long-Term (Future)

1. **Learning from Fixes** - Skill improves from history
2. **Proactive Suggestions** - Suggest fixes before failures
3. **Cross-Repo Skills** - Portable skills across projects
4. **Enterprise Integration** - Connect with issue trackers

---

## Resources

### Official Documentation
- [Agent Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Introducing Agent Skills - Anthropic Blog](https://www.anthropic.com/news/skills)
- [Agent Skills Open Standard - agentskills.io](https://agentskills.io)

### Reference Implementations
- [github.com/anthropics/skills](https://github.com/anthropics/skills) - Official examples
- [github.com/MattKilmer/claude-autofix-bot](https://github.com/MattKilmer/claude-autofix-bot) - Slack bot example
- [github.com/travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) - Community list

### Project Files
- `.claude/skills/automated-code-fixer/` - IT helper skill
- `.claude/skills/code-quality-monitor/` - Quality gate skill
- `.claude/commands/` - Existing slash commands
- `CLAUDE.md` - Project guidelines

---

## Summary

Anthropic Skills provide a powerful way to add automated intelligence to development workflows. By implementing:

1. **automated-code-fixer** - Safe, gated code fixes for development
2. **code-quality-monitor** - Proactive health enforcement
3. **production-incident-responder** - Crisis response via MCP for live systems

We get an "IT guy" that:
- Fixes code issues when it's safe
- Responds to production incidents via MCP
- Escalates when it's not safe to proceed
- Never compromises quality
- Follows project standards
- Maintains human-in-the-loop for critical decisions

### Complete Architecture

```
Development Issues                Production Issues
       ↓                                 ↓
automated-code-fixer              production-incident-responder
       ↓                                 ↓
Quality Gates (5 gates)           MCP Server (13 tools)
       ↓                                 ↓
Fix or Escalate                   Analyze → Respond → Recover
       ↓                                 ↓
code-quality-monitor              Human Approval for Critical Actions
```

The Skills Open Standard + MCP integration means this investment is portable and future-proof.
