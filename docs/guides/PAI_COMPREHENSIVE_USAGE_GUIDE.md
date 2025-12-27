***REMOVED*** Personal AI Infrastructure (PAI) - Comprehensive Usage Guide

> **Author:** Claude Code
> **Created:** 2025-12-27
> **Audience:** You (the primary developer/administrator)
> **Purpose:** Master guide for leveraging PAI to its full potential

---

***REMOVED******REMOVED*** Table of Contents

1. [Executive Summary](***REMOVED***1-executive-summary)
2. [What is PAI?](***REMOVED***2-what-is-pai)
3. [Architecture Deep Dive](***REMOVED***3-architecture-deep-dive)
4. [The CONSTITUTION: Your AI's Operating Rules](***REMOVED***4-the-constitution-your-ais-operating-rules)
5. [Agents: Specialized AI Personas](***REMOVED***5-agents-specialized-ai-personas)
6. [Skills: Reusable Expertise Packages](***REMOVED***6-skills-reusable-expertise-packages)
7. [History: Institutional Memory](***REMOVED***7-history-institutional-memory)
8. [Scratchpad: Your Thinking Space](***REMOVED***8-scratchpad-your-thinking-space)
9. [Hooks: Automated Post-Operation Workflows](***REMOVED***9-hooks-automated-post-operation-workflows)
10. [MetaUpdater: Continuous Improvement](***REMOVED***10-metaupdater-continuous-improvement)
11. [The CLI: Your Command Center](***REMOVED***11-the-cli-your-command-center)
12. [MCP Tools Integration](***REMOVED***12-mcp-tools-integration)
13. [Practical Workflows](***REMOVED***13-practical-workflows)
14. [Best Practices](***REMOVED***14-best-practices)
15. [Troubleshooting](***REMOVED***15-troubleshooting)
16. [Advanced Techniques](***REMOVED***16-advanced-techniques)
17. [Quick Reference](***REMOVED***17-quick-reference)

---

***REMOVED******REMOVED*** 1. Executive Summary

**PAI (Personal AI Infrastructure)** is the "operating system" for AI agents working on your Residency Scheduler codebase. It provides:

- **Consistency**: AI makes the same decisions every time via the CONSTITUTION
- **Memory**: Past decisions and incidents are permanently recorded in History
- **Expertise**: 34 skills encode domain knowledge (ACGME, scheduling, security)
- **Safety**: Multi-layer guardrails prevent catastrophic errors
- **Learning**: MetaUpdater detects patterns and proposes improvements

**The Bottom Line**: Instead of re-explaining context every conversation, PAI ensures AI agents already know your rules, your patterns, and your history.

---

***REMOVED******REMOVED*** 2. What is PAI?

***REMOVED******REMOVED******REMOVED*** 2.1 The Problem PAI Solves

Without PAI, working with AI on complex codebases means:

| Problem | Impact |
|---------|--------|
| **Context Amnesia** | Every conversation starts from scratch |
| **Inconsistent Behavior** | Different decisions for the same situation |
| **No Learning** | Same mistakes repeated across sessions |
| **Safety Gaps** | No guardrails on dangerous operations |
| **Knowledge Silos** | Expertise trapped in individual sessions |

***REMOVED******REMOVED******REMOVED*** 2.2 The PAI Solution

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSONAL AI INFRASTRUCTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│   │ CONSTITUTION│  │   AGENTS    │  │   SKILLS    │             │
│   │ (Rules)     │  │ (Personas)  │  │ (Expertise) │             │
│   └─────────────┘  └─────────────┘  └─────────────┘             │
│          │               │               │                       │
│          └───────────────┼───────────────┘                       │
│                          │                                       │
│                          ▼                                       │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│   │   HISTORY   │  │   HOOKS     │  │ SCRATCHPAD  │             │
│   │ (Memory)    │  │ (Triggers)  │  │ (Workspace) │             │
│   └─────────────┘  └─────────────┘  └─────────────┘             │
│          │               │               │                       │
│          └───────────────┼───────────────┘                       │
│                          │                                       │
│                          ▼                                       │
│                  ┌─────────────┐                                 │
│                  │ METAUPDATER │                                 │
│                  │ (Learning)  │                                 │
│                  └─────────────┘                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** 2.3 Key Principle: Solve Once, Reuse Forever

When you solve a problem:
1. **First time**: AI figures it out manually
2. **Second time**: AI recognizes the pattern
3. **Third time**: AI creates a **skill**
4. **Forever after**: AI uses the skill automatically

---

***REMOVED******REMOVED*** 3. Architecture Deep Dive

***REMOVED******REMOVED******REMOVED*** 3.1 Directory Structure

```
.claude/
├── CONSTITUTION.md           ***REMOVED*** Foundational rules (non-negotiable)
├── SKILL_INDEX.md            ***REMOVED*** Complete skill registry
├── INFRASTRUCTURE_OVERVIEW.md ***REMOVED*** Architecture documentation
│
├── Agents/                   ***REMOVED*** Specialized AI personas
│   ├── SCHEDULER.md          ***REMOVED*** Schedule generation
│   ├── ARCHITECT.md          ***REMOVED*** System design
│   ├── RESILIENCE_ENGINEER.md ***REMOVED*** Health monitoring
│   ├── QA_TESTER.md          ***REMOVED*** Quality assurance
│   ├── META_UPDATER.md       ***REMOVED*** Continuous improvement
│   └── ORCHESTRATOR.md       ***REMOVED*** Multi-agent coordination
│
├── skills/                   ***REMOVED*** Reusable expertise packages
│   ├── SCHEDULING/           ***REMOVED*** Kai-pattern (advanced)
│   ├── COMPLIANCE_VALIDATION/
│   ├── RESILIENCE_SCORING/
│   ├── acgme-compliance/     ***REMOVED*** Legacy-pattern (simple)
│   ├── test-writer/
│   ├── security-audit/
│   └── ... (34 total skills)
│
├── History/                  ***REMOVED*** Permanent audit trail
│   ├── scheduling/           ***REMOVED*** Schedule generation records
│   ├── swaps/                ***REMOVED*** Swap execution records
│   ├── compliance/           ***REMOVED*** ACGME audits
│   ├── resilience/           ***REMOVED*** Health assessments
│   └── incidents/            ***REMOVED*** Postmortems
│
├── Scratchpad/               ***REMOVED*** Temporary workspace (7-day cleanup)
│
├── Hooks/                    ***REMOVED*** Post-operation triggers
│   ├── post-schedule-generation.md
│   ├── post-swap-execution.md
│   ├── post-compliance-audit.md
│   └── post-resilience-test.md
│
└── Methodologies/            ***REMOVED*** Thinking frameworks
    ├── constraint-propagation.md
    ├── resilience-thinking.md
    ├── surgical-swaps.md
    └── incident-response.md
```

***REMOVED******REMOVED******REMOVED*** 3.2 Component Interaction Flow

```
User Request: "Generate Block 10 schedule"
                    │
                    ▼
            ┌───────────────┐
            │ 1. Agent      │ SCHEDULER activated
            │    Selection  │
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ 2. CONSTITUTION│ Check rules:
            │    Check      │ - ACGME mandatory
            │               │ - Backup required
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ 3. Skill      │ Load:
            │    Activation │ - schedule-optimization
            │               │ - safe-schedule-generation
            │               │ - acgme-compliance
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ 4. Execution  │ - Create backup
            │               │ - Run CP-SAT solver
            │               │ - Validate compliance
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ 5. Hook       │ post-schedule-generation:
            │    Trigger    │ - Recalculate resilience
            │               │ - Send notifications
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ 6. History    │ Document in:
            │    Recording  │ History/scheduling/
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ 7. MetaUpdater│ Periodic scan:
            │    Analysis   │ - Detect patterns
            │               │ - Propose improvements
            └───────────────┘
```

---

***REMOVED******REMOVED*** 4. The CONSTITUTION: Your AI's Operating Rules

***REMOVED******REMOVED******REMOVED*** 4.1 What is the CONSTITUTION?

The CONSTITUTION (`.claude/CONSTITUTION.md`) is the foundational rulebook that **all AI agents must follow**. It defines:

- **First Principles**: CLI-first, deterministic, logged
- **Safety-Critical Rules**: ACGME compliance, swap validation
- **Constraint Hierarchy**: What takes priority
- **Agent Autonomy**: What AI can/cannot do
- **Error Handling**: How to recover from failures

***REMOVED******REMOVED******REMOVED*** 4.2 The Constraint Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONSTRAINT HIERARCHY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIER 1: REGULATORY (Absolute - Never Violate)                  │
│  ├── ACGME 80-hour rule                                         │
│  ├── ACGME 1-in-7 day off                                       │
│  ├── Supervision ratios                                         │
│  └── Credentialing requirements                                 │
│                                                                  │
│  TIER 2: INSTITUTIONAL POLICY (Hard - Waiver Required)          │
│  ├── Local work hour limits                                     │
│  ├── Clinical coverage requirements                             │
│  ├── Specialty-specific rules                                   │
│  └── Call schedule patterns                                     │
│                                                                  │
│  TIER 3: OPTIMIZATION (Soft - Can Be Violated)                  │
│  ├── Fairness (equal shift distribution)                        │
│  ├── Continuity (minimize rotations)                            │
│  ├── Learning opportunities                                     │
│  └── Personal preferences                                       │
│                                                                  │
│  TIER 4: NICE-TO-HAVE (Lowest Priority)                         │
│  ├── Preferred clinic days                                      │
│  ├── Social events                                              │
│  └── Commute optimization                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** 4.3 Key CONSTITUTION Rules for You

| Rule | What It Means |
|------|---------------|
| **CLI-First** | All code must be runnable from command line, no interactive prompts |
| **ACGME Tier 0** | AI will REFUSE to bypass ACGME rules, even if you ask |
| **Backup Mandatory** | Database writes require backup first (safe-schedule-generation skill) |
| **Logging Required** | All significant operations are logged for audit |
| **Rollback Ready** | Every change must be reversible |

***REMOVED******REMOVED******REMOVED*** 4.4 How to Modify the CONSTITUTION

1. Identify the gap (recurring issue, false positive/negative)
2. Draft an amendment proposal
3. Impact analysis (what will change?)
4. 7-day review period
5. Explicit approval required
6. Version increment and changelog

**Template:**
```markdown
***REMOVED******REMOVED*** Amendment Proposal: [Title]

***REMOVED******REMOVED******REMOVED*** Current Rule
[Quote existing rule]

***REMOVED******REMOVED******REMOVED*** Problem
[Why current rule is insufficient]

***REMOVED******REMOVED******REMOVED*** Proposed Change
[New rule text]

***REMOVED******REMOVED******REMOVED*** Impact
- Affects: [Systems/processes]
- Breaking Changes: [Yes/No]
```

---

***REMOVED******REMOVED*** 5. Agents: Specialized AI Personas

***REMOVED******REMOVED******REMOVED*** 5.1 What Are Agents?

Agents are **specialized AI personas** with defined roles, authorities, and personalities. Each agent has:

- **Charter**: What they're responsible for
- **Personality**: How they behave
- **Decision Authority**: What they can do autonomously vs. requiring approval
- **Skills Access**: Which skills they can use
- **Escalation Rules**: When to ask for help

***REMOVED******REMOVED******REMOVED*** 5.2 Available Agents

| Agent | Role | Key Skills |
|-------|------|------------|
| **SCHEDULER** | Schedule generation, swaps, ACGME validation | schedule-optimization, swap-management |
| **ARCHITECT** | System design, database schema, infrastructure | database-migration, fastapi-production |
| **RESILIENCE_ENGINEER** | N-1/N-2 contingency, health scoring | RESILIENCE_SCORING |
| **QA_TESTER** | Quality assurance, adversarial testing | test-writer, systematic-debugger |
| **META_UPDATER** | Pattern detection, continuous improvement | All skills (read-only) |
| **ORCHESTRATOR** | Multi-agent coordination | CORE, MCP_ORCHESTRATION |

***REMOVED******REMOVED******REMOVED*** 5.3 SCHEDULER Agent Deep Dive

The SCHEDULER is your most-used agent. Here's how it works:

**Personality:**
- Methodical & systematic
- Safety-conscious (backs up before writes)
- Communicative (explains constraints)
- Adaptive (degrades gracefully)

**Can Independently Execute:**
- Schedule generation (if safety checks pass)
- Approved swaps (with validation)
- Minor adjustments (<20% of schedule)

**Requires Approval:**
- Major schedule overhauls (>20%)
- Risky swaps (critical services, <48hr notice)
- Compliance exceptions (never granted)

**Forbidden Actions:**
- Violate ACGME rules
- Bypass safety checks
- Skip database backup

***REMOVED******REMOVED******REMOVED*** 5.4 How to Invoke an Agent

Agents are invoked implicitly based on your request:

```
You: "Generate Block 10 schedule for July-August"
      → SCHEDULER agent activated

You: "What if FAC-PD is unavailable for 2 weeks?"
      → RESILIENCE_ENGINEER agent activated

You: "Review the swap validator code for bugs"
      → QA_TESTER agent activated
```

Or explicitly reference an agent:

```
You: "As ARCHITECT, design the credential dashboard schema"
```

---

***REMOVED******REMOVED*** 6. Skills: Reusable Expertise Packages

***REMOVED******REMOVED******REMOVED*** 6.1 What Are Skills?

Skills are **packaged expertise** that encode best practices for specific tasks. They contain:

- **Purpose**: What the skill does
- **When to Activate**: Trigger conditions
- **Prerequisites**: Required tools/permissions
- **Workflow**: Step-by-step procedure
- **Guardrails**: Safety checks
- **Examples**: Concrete usage scenarios

***REMOVED******REMOVED******REMOVED*** 6.2 Skill Types

| Type | Pattern | Structure | Use Case |
|------|---------|-----------|----------|
| **Kai Pattern** | Advanced | SKILL.md + Workflows/ + Reference/ | Complex domain operations |
| **Legacy Pattern** | Simple | SKILL.md only | Targeted single tasks |

***REMOVED******REMOVED******REMOVED*** 6.3 The 34 Skills (Grouped by Tier)

**Tier 1: Core Scheduling (Kai Pattern)**
- `SCHEDULING` - Full schedule generation workflow
- `COMPLIANCE_VALIDATION` - Systematic ACGME auditing
- `RESILIENCE_SCORING` - Health metrics and N-1/N-2 analysis
- `SWAP_EXECUTION` - Swap lifecycle management
- `MCP_ORCHESTRATION` - Multi-tool workflows
- `ORCHESTRATION_DEBUGGING` - Agent/tool troubleshooting

**Tier 2: Domain-Specific**
- `acgme-compliance` - ACGME reference knowledge
- `schedule-optimization` - Solver algorithms
- `swap-management` - Swap matching
- `safe-schedule-generation` - Mandatory backup
- `schedule-verification` - Human review checklist

**Tier 3: Development**
- `test-writer` - Generate pytest/Jest tests
- `code-review` - Quality and security review
- `automated-code-fixer` - Fix tests/lint/types
- `lint-monorepo` - Ruff + ESLint
- `systematic-debugger` - Explore-plan-debug-fix
- `constraint-preflight` - Verify constraints registered

**Tier 4: Infrastructure**
- `database-migration` - Alembic expertise
- `docker-containerization` - Docker/compose
- `fastapi-production` - API patterns
- `frontend-development` - Next.js/React
- `react-typescript` - TypeScript patterns

**Tier 5: Workflow**
- `pr-reviewer` - Pull request review
- `changelog-generator` - Release notes
- `solver-control` - Monitor/abort solvers

**Tier 6: Emergency**
- `production-incident-responder` - Crisis response

**Tier 7: Security**
- `security-audit` - HIPAA, OPSEC/PERSEC

**Tier 8: Utilities**
- `pdf` - PDF generation
- `xlsx` - Excel import/export
- `test-scenario-framework` - E2E test scenarios

***REMOVED******REMOVED******REMOVED*** 6.4 How Skills Are Activated

Skills activate **automatically** based on your request:

| You Say | Skill Activated |
|---------|-----------------|
| "Is the schedule compliant?" | `acgme-compliance` |
| "Find someone to swap with" | `swap-management` |
| "Write tests for this" | `test-writer` |
| "Production is down!" | `production-incident-responder` |
| "Generate Block 10 schedule" | `SCHEDULING` + `safe-schedule-generation` |

***REMOVED******REMOVED******REMOVED*** 6.5 Creating Custom Skills

**When to Create a Skill:**
- Task performed 3+ times
- Multi-step workflow requiring coordination
- Domain expertise needed
- Error-prone task requiring guardrails

**Template:**
```markdown
***REMOVED*** SKILL.md - [Skill Name]

***REMOVED******REMOVED*** Purpose
One-sentence description.

***REMOVED******REMOVED*** When to Activate
- Trigger 1
- Trigger 2

***REMOVED******REMOVED*** Prerequisites
- Required tool
- Required permission

***REMOVED******REMOVED*** Workflow
1. Step 1
2. Step 2
3. Validation

***REMOVED******REMOVED*** Guardrails
- Safety check 1
- Safety check 2

***REMOVED******REMOVED*** Examples
***REMOVED******REMOVED******REMOVED*** Example 1: [Scenario]
[Concrete walkthrough]
```

---

***REMOVED******REMOVED*** 7. History: Institutional Memory

***REMOVED******REMOVED******REMOVED*** 7.1 What is History?

History (`.claude/History/`) is the **permanent audit trail** for all significant operations. Unlike logs (transient, technical), History is:

- **Human-readable**: Written in markdown
- **Decision-focused**: Documents *why*, not just *what*
- **Audit-compliant**: Sufficient detail for ACGME audits
- **Pattern-detectable**: Enables MetaUpdater to find recurring issues
- **Searchable**: Structured format for grep/search

***REMOVED******REMOVED******REMOVED*** 7.2 Directory Structure

```
.claude/History/
├── scheduling/         ***REMOVED*** Schedule generation (1-year retention)
│   ├── TEMPLATE.md
│   └── 2025-07-15_block10_gen001.md
├── swaps/              ***REMOVED*** Swap execution (1-year retention)
│   ├── TEMPLATE.md
│   └── 2025-08-03_swap_s12345.md
├── compliance/         ***REMOVED*** ACGME audits (FOREVER retention)
│   └── 2025-07-31_monthly_audit.md
├── resilience/         ***REMOVED*** Health assessments (2-year retention)
│   └── 2025-07-20_n1_analysis.md
└── incidents/          ***REMOVED*** Postmortems (FOREVER retention)
    ├── TEMPLATE.md
    └── 2025-08-05_solver_timeout.md
```

***REMOVED******REMOVED******REMOVED*** 7.3 Writing History Entries

**Good Entry:**
```markdown
***REMOVED*** Schedule Generation - Block 10 (July-August 2025)

**Summary:** Generated 2-month schedule for 12 residents with 3 leave requests.

***REMOVED******REMOVED*** Context
Annual schedule generation for Block 10. PGY-1 cohort includes 4 new residents.

***REMOVED******REMOVED*** Rationale
- Relaxed "preferred clinic day" constraint for PGY1-03 due to orientation conflict.
- Applied N-1 contingency: FAC-PD scheduled for TDY Aug 10-20.

***REMOVED******REMOVED*** Outcome
✅ ACGME compliance: 0 violations
✅ Coverage: 100% (all 122 blocks assigned)
✅ Fairness: Call distribution variance 0.8σ

***REMOVED******REMOVED*** Impact
- 12 residents notified via email
- Dashboard updated
```

**Bad Entry:**
```markdown
***REMOVED*** thing
ran solver. worked. done.
```

***REMOVED******REMOVED******REMOVED*** 7.4 Querying History

```bash
***REMOVED*** Find all schedule generations in July 2025
ls .claude/History/scheduling/2025-07-*.md

***REMOVED*** Find all ACGME violations
grep -r "ACGME.*VIOLATED" .claude/History/compliance/

***REMOVED*** Find all swaps involving a specific resident
grep -r "PGY2-01" .claude/History/swaps/ -l

***REMOVED*** Find all decision rationales (for learning)
grep -r "Rationale:" .claude/History/ -A 3

***REMOVED*** Timeline analysis (all operations on a specific date)
find .claude/History/ -name "2025-08-15*.md"
```

***REMOVED******REMOVED******REMOVED*** 7.5 Retention Policy

| Category | Retention | Rationale |
|----------|-----------|-----------|
| Scheduling | 1 academic year | Pattern analysis |
| Swaps | 1 academic year | Fairness metrics |
| Compliance | **Forever** | ACGME audits (6-10 year lookback) |
| Resilience | 2 years | Trend analysis |
| Incidents | **Forever** | Long-term improvements |

---

***REMOVED******REMOVED*** 8. Scratchpad: Your Thinking Space

***REMOVED******REMOVED******REMOVED*** 8.1 What is Scratchpad?

Scratchpad (`.claude/Scratchpad/`) is a **temporary workspace** for messy, iterative work. It's your whiteboard; History is your filing cabinet.

| Aspect | Scratchpad | History |
|--------|------------|---------|
| **Permanence** | 7-day auto-cleanup | Permanent |
| **Audience** | Yourself (current session) | Future reviewers, auditors |
| **Formality** | Informal notes | Structured documentation |
| **Git** | NOT committed | Committed |

***REMOVED******REMOVED******REMOVED*** 8.2 When to Use Scratchpad

**Use Scratchpad for:**
1. **Debugging notes** during investigation
2. **Experiment design** and results
3. **Brainstorming** and design drafts
4. **Meeting notes** and action items
5. **Quick calculations** and scratch work

**Example:**
```markdown
***REMOVED*** Scratchpad/2025-08-15_14-30_debug_solver_timeout.md

***REMOVED******REMOVED*** Problem
Solver timing out on Block 11. Investigating why.

***REMOVED******REMOVED*** Observations
- Constraint count: 1247 (vs. 987 in Block 10)
- New constraints: N95 Fit (180), Flu Vax (80)

***REMOVED******REMOVED*** Hypothesis
Over-constrained problem.

***REMOVED******REMOVED*** Test
Relaxed N95 to soft → solved in 6m ✅

***REMOVED******REMOVED*** Conclusion
Credential requirements should be soft constraints.

***REMOVED******REMOVED*** Next Steps
- [ ] Create PR to reclassify
- [ ] Document in History after fix deployed
```

***REMOVED******REMOVED******REMOVED*** 8.3 Promoting Scratchpad to History

When work is finalized, promote to History:

1. Copy content to History using template
2. Clean up formatting
3. Add context for future readers
4. Commit to git
5. Delete Scratchpad file (or let auto-cleanup handle it)

---

***REMOVED******REMOVED*** 9. Hooks: Automated Post-Operation Workflows

***REMOVED******REMOVED******REMOVED*** 9.1 What Are Hooks?

Hooks (`.claude/Hooks/`) define **automated actions** triggered after specific operations. They ensure consistent follow-up.

***REMOVED******REMOVED******REMOVED*** 9.2 Available Hooks

| Hook | Trigger | Actions |
|------|---------|---------|
| `post-schedule-generation` | After schedule commit | ACGME audit, resilience recalc, notifications |
| `post-swap-execution` | After swap commit | Revalidate compliance, update fairness |
| `post-compliance-audit` | After compliance scan | Log violations, alert if thresholds breached |
| `post-resilience-test` | After resilience test | Update dashboard, escalate if health low |

***REMOVED******REMOVED******REMOVED*** 9.3 Hook Structure

```markdown
***REMOVED*** Post-Schedule-Generation Hook

**Trigger:** Schedule successfully committed to database

**Actions:**
1. Run ACGME compliance validator on full schedule
2. Calculate resilience health score (N-1, N-2, utilization)
3. Generate fairness metrics (call distribution, weekend variance)
4. Send notification emails to affected residents
5. Create History entry documenting generation
6. Update dashboard statistics

**Guardrails:**
- If compliance violations found → rollback + escalate
- If resilience health < 0.7 → flag for review
```

---

***REMOVED******REMOVED*** 10. MetaUpdater: Continuous Improvement

***REMOVED******REMOVED******REMOVED*** 10.1 What is MetaUpdater?

MetaUpdater is a **conceptual agent** that scans History for patterns and proposes improvements. It's the "learning" component of PAI.

***REMOVED******REMOVED******REMOVED*** 10.2 How MetaUpdater Works

```
History Scan (Daily/Weekly/Monthly)
        │
        ▼
┌─────────────────────────┐
│ Pattern Detection       │
│ - Same issue 3+ times?  │
│ - Same constraint fail? │
│ - Same incident type?   │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Root Cause Analysis     │
│ - Why recurring?        │
│ - What's the fix?       │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Propose Solution        │
│ - Code fix?             │
│ - Skill update?         │
│ - CONSTITUTION amend?   │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Human Approval          │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Deploy & Monitor        │
└─────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** 10.3 Example MetaUpdater Workflow

**Pattern Detected:** 3 solver timeout incidents in 90 days

**Root Cause:** Constraint catalog growing unsustainably

**Proposed Solution:**
1. Add max constraint density rule to CONSTITUTION
2. Update skill to pre-flight check constraint count

**After Approval:**
- CONSTITUTION updated: "Max 15:1 constraint-to-block ratio"
- Skill updated: Pre-flight validates constraint count
- Pattern breaks: No more timeout incidents

---

***REMOVED******REMOVED*** 11. The CLI: Your Command Center

***REMOVED******REMOVED******REMOVED*** 11.1 What is the CLI?

The CLI (`cli/aapm`) is a unified command-line interface for all scheduling operations. It routes to skills and triggers hooks.

***REMOVED******REMOVED******REMOVED*** 11.2 Available Commands

```bash
***REMOVED*** Schedule operations
aapm schedule generate 2026-03-12 2026-04-08
aapm schedule-audit

***REMOVED*** Swap operations
aapm swap execute SWP-001
aapm swap find-matches PGY2-01

***REMOVED*** Resilience operations
aapm resilience health
aapm resilience n1-test
aapm resilience identify-critical

***REMOVED*** Incident response
aapm incident respond

***REMOVED*** Skill management
aapm skill-update

***REMOVED*** Testing
aapm test
```

***REMOVED******REMOVED******REMOVED*** 11.3 How CLI Routing Works

```
aapm schedule generate 2026-03-12 2026-04-08
        │
        ▼
CLI routes to: safe-schedule-generation skill
        │
        ▼
Skill executes:
1. Verify backup exists
2. Call MCP tool: generate_schedule
3. Validate results
        │
        ▼
Hook triggered: post-schedule-generation
        │
        ▼
Data captured and written to History
```

---

***REMOVED******REMOVED*** 12. MCP Tools Integration

***REMOVED******REMOVED******REMOVED*** 12.1 What Are MCP Tools?

MCP (Model Context Protocol) tools are **backend API wrappers** that let AI agents take action. PAI has 36+ MCP tools.

***REMOVED******REMOVED******REMOVED*** 12.2 Key MCP Tools

| Tool | Purpose |
|------|---------|
| `generate_schedule` | Create new schedule |
| `validate_acgme_compliance` | Check ACGME rules |
| `execute_swap` | Process swap request |
| `analyze_swap_candidates` | Find swap matches |
| `check_resilience_health` | Get health score |
| `run_contingency_analysis_resilience_tool` | N-1/N-2 simulation |
| `detect_conflicts` | Find schedule conflicts |

***REMOVED******REMOVED******REMOVED*** 12.3 MCP Tool Safety

**Database-modifying tools require:**
1. Recent backup (< 2 hours)
2. User confirmation
3. Rollback readiness

**Read-only tools are always safe:**
- `validate_acgme_compliance`
- `analyze_swap_candidates`
- `check_resilience_health`

---

***REMOVED******REMOVED*** 13. Practical Workflows

***REMOVED******REMOVED******REMOVED*** 13.1 Generate a Schedule

```
You: "Generate Block 10 schedule for July-August"

PAI Flow:
1. SCHEDULER agent activates
2. CONSTITUTION check: ACGME mandatory, backup required
3. Skills loaded: schedule-optimization, safe-schedule-generation
4. Pre-flight: Backup created, resilience health ≥ 0.7
5. Solver runs (OR-Tools CP-SAT, 30min timeout)
6. Validation: 0 ACGME violations, 100% coverage
7. Hook: Resilience recalculated, residents notified
8. History: Entry created in scheduling/
```

***REMOVED******REMOVED******REMOVED*** 13.2 Process a Swap Request

```
You: "Execute swap between PGY2-01 and PGY2-03 for Aug 20"

PAI Flow:
1. SCHEDULER agent activates
2. Skills loaded: swap-management, SWAP_EXECUTION
3. Validation:
   - Both parties exist and active
   - ACGME simulation shows no violations
   - Credentials verified
   - Coverage maintained
4. Execute: Atomic database transaction
5. Notification: Email both parties
6. Rollback window: 24 hours active
7. History: Entry created in swaps/
```

***REMOVED******REMOVED******REMOVED*** 13.3 Debug an Issue

```
You: "The solver is timing out on Block 11"

PAI Flow:
1. Load systematic-debugger skill
2. Create Scratchpad entry for notes
3. Phase 1: Exploration (read code, logs)
4. Phase 2: Hypothesis generation
5. Phase 3: Testing hypotheses
6. Phase 4: Implement fix
7. Promote Scratchpad to History (if incident)
```

***REMOVED******REMOVED******REMOVED*** 13.4 Respond to Production Incident

```
You: "Production database is down!"

PAI Flow:
1. production-incident-responder skill activates
2. incident-response methodology loaded
3. OODA Loop: Observe → Orient → Decide → Act
4. Root cause analysis (5 Whys)
5. Mitigation executed
6. Recovery verified
7. Postmortem documented in History/incidents/
```

---

***REMOVED******REMOVED*** 14. Best Practices

***REMOVED******REMOVED******REMOVED*** 14.1 For Daily Work

| Do | Don't |
|----|-------|
| Check History before operations | Start from scratch every session |
| Use Scratchpad for debugging | Lose investigation notes |
| Trigger hooks consistently | Skip post-operation validation |
| Route through CLI when possible | Bypass safety checks |

***REMOVED******REMOVED******REMOVED*** 14.2 For Pattern Development

| Do | Don't |
|----|-------|
| Create skill after 3rd repetition | Reinvent the wheel |
| Document rationale in History | Only record what happened |
| Update CONSTITUTION when needed | Let false positives persist |
| Test skills in multiple contexts | Deploy untested patterns |

***REMOVED******REMOVED******REMOVED*** 14.3 For Safety

| Do | Don't |
|----|-------|
| Backup before database writes | Skip safe-schedule-generation |
| Validate ACGME after changes | Trust solver output blindly |
| Use role-based identifiers | Use real names in History |
| Never delete compliance logs | Prune without checking retention |

---

***REMOVED******REMOVED*** 15. Troubleshooting

***REMOVED******REMOVED******REMOVED*** 15.1 Skills Not Loading

**Symptoms:** Agent doesn't use skill knowledge

**Fixes:**
1. Check skill is in `.claude/skills/` (not `skills/`)
2. Verify `SKILL.md` has correct frontmatter
3. Description must match your query keywords

***REMOVED******REMOVED******REMOVED*** 15.2 History Not Writing

**Symptoms:** No History entry created

**Fixes:**
1. Check directory exists: `ls .claude/History/`
2. Check write permissions: `chmod -R u+w .claude/History/`
3. Verify hook is triggering

***REMOVED******REMOVED******REMOVED*** 15.3 MCP Tools Not Available

**Symptoms:** "Tool not found" errors

**Fixes:**
1. Start MCP server: `cd mcp-server && python -m scheduler_mcp.server`
2. Verify server health: `curl http://localhost:5000/health`
3. Check Claude Code config

***REMOVED******REMOVED******REMOVED*** 15.4 Solver Timing Out

**Symptoms:** Schedule generation takes >30 minutes

**Fixes:**
1. Check constraint count (target: ≤15:1 ratio to blocks)
2. Reclassify hard constraints to soft
3. Use solver-control skill to abort if needed

---

***REMOVED******REMOVED*** 16. Advanced Techniques

***REMOVED******REMOVED******REMOVED*** 16.1 Multi-Agent Parallel Debugging

For complex bugs, run multiple Claude sessions:

```
Terminal 1: "Investigate why residents are being double-booked"
Terminal 2: "Analyze work hour calculation for off-by-one errors"
Terminal 3: "Review recent scheduler commits for regressions"
```

Synthesize findings across sessions.

***REMOVED******REMOVED******REMOVED*** 16.2 History Analysis for Patterns

```bash
***REMOVED*** Find recurring constraint conflicts
grep -r "Conflict:" .claude/History/scheduling/ | \
  cut -d: -f3 | sort | uniq -c | sort -rn | head -10

***REMOVED*** Performance trend analysis
grep -r "Solve Time:" .claude/History/scheduling/ | \
  awk '{print $NF}' | sort -n

***REMOVED*** Decision rationale extraction
grep -r "Rationale:" .claude/History/ -A 3
```

***REMOVED******REMOVED******REMOVED*** 16.3 Custom Agent Creation

When to create:
- Distinct role not covered by existing agents
- Specialized decision authority needed
- Different personality required

Template:
```markdown
***REMOVED*** [AGENT_NAME] Agent

***REMOVED******REMOVED*** Charter
**Role:** [Description]
**Authority:** [What can it do?]
**Personality:** [How does it behave?]

***REMOVED******REMOVED*** Skills Access
- skill-1 (full access)
- skill-2 (read only)

***REMOVED******REMOVED*** Escalation Rules
- Condition → Escalate to [AGENT]
```

***REMOVED******REMOVED******REMOVED*** 16.4 Skill Composition

Chain skills for complex workflows:

```
Schedule Generation Workflow:
1. safe-schedule-generation (backup)
2. SCHEDULING (generate)
3. COMPLIANCE_VALIDATION (validate)
4. RESILIENCE_SCORING (check health)
5. schedule-verification (human review)

Swap Request Workflow:
1. swap-management (find candidates)
2. SWAP_EXECUTION (validate + execute)
3. COMPLIANCE_VALIDATION (post-swap check)
4. RESILIENCE_SCORING (health impact)
```

---

***REMOVED******REMOVED*** 17. Quick Reference

***REMOVED******REMOVED******REMOVED*** 17.1 Key Files

| File | Purpose |
|------|---------|
| `.claude/CONSTITUTION.md` | Foundational rules |
| `.claude/SKILL_INDEX.md` | Complete skill registry |
| `.claude/Agents/SCHEDULER.md` | Schedule agent spec |
| `.claude/History/README.md` | History system docs |
| `.claude/Scratchpad/README.md` | Scratchpad docs |
| `docs/PERSONAL_INFRASTRUCTURE.md` | PAI overview |

***REMOVED******REMOVED******REMOVED*** 17.2 Common Commands

```bash
***REMOVED*** CLI
aapm schedule generate <start> <end>
aapm swap execute <swap-id>
aapm resilience n1-test

***REMOVED*** History queries
grep -r "ACGME.*VIOLATED" .claude/History/
find .claude/History/ -name "2025-08-*.md"

***REMOVED*** Scratchpad
vim .claude/Scratchpad/$(date +%Y-%m-%d_%H-%M)_debug_issue.md
```

***REMOVED******REMOVED******REMOVED*** 17.3 Skill Selection Decision Tree

```
User Request
    │
    ├── Explicit skill named? ─YES─> Invoke named skill
    │                          │
    │                          NO
    │                          │
    ├── Production emergency? ─YES─> production-incident-responder
    │                          │
    │                          NO
    │                          │
    ├── Database write? ───────YES─> safe-schedule-generation + [target]
    │                          │
    │                          NO
    │                          │
    ├── Match intent keywords ─────> Use Intent Mapping
    │                          │
    │                          NO MATCH
    │                          │
    └── General Claude capabilities
```

***REMOVED******REMOVED******REMOVED*** 17.4 Defense-in-Depth Levels

| Level | Color | Utilization | Action |
|-------|-------|-------------|--------|
| Safe | GREEN | ≤ 80% | Normal operations |
| Caution | YELLOW | 80-85% | Log warning, alert coordinators |
| Warning | ORANGE | 85-90% | Block new assignments, escalate |
| Critical | RED | 90-95% | Activate N-1 contingency |
| Emergency | BLACK | > 95% | Activate N-2, load shedding |

---

***REMOVED******REMOVED*** Appendix A: PAI Component Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PAI ECOSYSTEM MAP                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐         governs         ┌─────────────┐                │
│  │ CONSTITUTION│ ───────────────────────>│   AGENTS    │                │
│  └─────────────┘                          └─────────────┘                │
│         │                                        │                       │
│         │ defines rules for                      │ use                   │
│         ▼                                        ▼                       │
│  ┌─────────────┐         invoke         ┌─────────────┐                 │
│  │   SKILLS    │<────────────────────────│    CLI      │                │
│  └─────────────┘                          └─────────────┘                │
│         │                                        │                       │
│         │ execute                                │ routes to             │
│         ▼                                        ▼                       │
│  ┌─────────────┐                          ┌─────────────┐               │
│  │  MCP TOOLS  │                          │   HOOKS     │               │
│  └─────────────┘                          └─────────────┘               │
│         │                                        │                       │
│         │ modify                                 │ trigger               │
│         ▼                                        ▼                       │
│  ┌─────────────┐         documented in   ┌─────────────┐                │
│  │  DATABASE   │ ────────────────────────>│   HISTORY   │               │
│  └─────────────┘                          └─────────────┘                │
│                                                  │                       │
│                                                  │ scanned by            │
│                                                  ▼                       │
│                                           ┌─────────────┐               │
│                                           │ METAUPDATER │               │
│                                           └─────────────┘               │
│                                                  │                       │
│                                                  │ proposes updates to   │
│                                                  ▼                       │
│                                           ┌─────────────┐               │
│                                           │ CONSTITUTION│               │
│                                           │   SKILLS    │               │
│                                           └─────────────┘               │
│                                                                          │
│  ┌─────────────┐                                                        │
│  │ SCRATCHPAD  │ ─── promotes to ───> HISTORY                           │
│  └─────────────┘                                                        │
│                                                                          │
│  ┌─────────────┐                                                        │
│  │METHODOLOGIES│ ─── guide ───> AGENTS during complex tasks             │
│  └─────────────┘                                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** Appendix B: Intent-to-Skill Mapping

| You Say | Primary Skill | Secondary Skills |
|---------|---------------|------------------|
| "generate schedule" | SCHEDULING | safe-schedule-generation, COMPLIANCE_VALIDATION |
| "optimize schedule" | SCHEDULING | schedule-optimization |
| "validate compliance" | COMPLIANCE_VALIDATION | - |
| "check ACGME" | acgme-compliance | COMPLIANCE_VALIDATION |
| "execute swap" | SWAP_EXECUTION | COMPLIANCE_VALIDATION |
| "find swap candidates" | swap-management | SWAP_EXECUTION |
| "check resilience" | RESILIENCE_SCORING | - |
| "what if resident absent?" | RESILIENCE_SCORING | - |
| "write tests" | test-writer | python-testing-patterns |
| "review code" | code-review | security-audit |
| "fix tests" | automated-code-fixer | test-writer |
| "debug issue" | systematic-debugger | ORCHESTRATION_DEBUGGING |
| "create migration" | database-migration | - |
| "create api endpoint" | fastapi-production | test-writer |
| "production down" | production-incident-responder | systematic-debugger |
| "security audit" | security-audit | code-review |
| "review pr" | pr-reviewer | code-review |

---

***REMOVED******REMOVED*** Appendix C: Further Reading

| Document | Location | Purpose |
|----------|----------|---------|
| CONSTITUTION | `.claude/CONSTITUTION.md` | Foundational rules |
| Skill Index | `.claude/SKILL_INDEX.md` | Complete skill registry |
| Infrastructure Overview | `.claude/INFRASTRUCTURE_OVERVIEW.md` | Architecture |
| AI Agent User Guide | `docs/guides/AI_AGENT_USER_GUIDE.md` | Interface comparison |
| Solver Algorithm | `docs/architecture/SOLVER_ALGORITHM.md` | Scheduling engine |
| Cross-Disciplinary Resilience | `docs/architecture/cross-disciplinary-resilience.md` | Resilience framework |

---

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Maintained By:** Claude Code

---

*PAI is your AI operating system. Use it well, and AI becomes a consistent, knowledgeable partner rather than a stateless tool.*
