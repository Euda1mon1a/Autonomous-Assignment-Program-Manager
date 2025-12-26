# Personal AI Infrastructure (PAI) - Residency Scheduler

> **Purpose:** Comprehensive guide to the AI-powered development infrastructure
> **Audience:** Developers, administrators, and AI agents
> **Status:** Production-ready PAI based on Kai Patterns

---

## Table of Contents

1. [What is PAI?](#what-is-pai)
2. [Why PAI Matters](#why-pai-matters)
3. [Architecture at a Glance](#architecture-at-a-glance)
4. [Key Components](#key-components)
5. [How It Works](#how-it-works)
6. [Core Principles](#core-principles)
7. [Common Tasks](#common-tasks-quick-reference)
8. [Maintenance & Evolution](#maintenance--evolution)
9. [Getting Started](#getting-started-for-new-developers)
10. [Advanced Topics](#advanced-topics)

---

## What is PAI?

**Personal AI Infrastructure (PAI)** is a structured framework that enables AI agents (like Claude) to operate autonomously, make consistent decisions, and continuously improve their performance on the Residency Scheduler project.

**In Simple Terms:**
Think of PAI as the "operating system" for AI agents working on this codebase. Just as an OS provides processes, file systems, and security boundaries for programs, PAI provides:
- **Constitution**: Foundational rules (what AI can/cannot do)
- **Skills**: Reusable capabilities (how AI performs tasks)
- **Agents**: Specialized personas (who does what)
- **History**: Institutional memory (learning from past operations)
- **Hooks**: Automated workflows (triggering actions at key moments)

**Based On:** [Kai Patterns](https://github.com/gptscript-ai/claude-kai) - A proven framework for organizing AI-assisted development

---

## Why PAI Matters

### The Problem Without PAI

**Before PAI**, working with AI on complex codebases meant:
- ❌ **Inconsistent behavior**: AI makes different decisions each time
- ❌ **No institutional memory**: Same mistakes repeated
- ❌ **Context overload**: Re-explaining architecture every conversation
- ❌ **Safety concerns**: No guardrails on dangerous operations
- ❌ **Knowledge loss**: Learnings from one session lost in the next

### The Solution With PAI

**With PAI**, AI agents:
- ✅ **Follow consistent rules**: CONSTITUTION.md enforces safety and compliance
- ✅ **Learn from history**: Past incidents inform future decisions
- ✅ **Execute complex workflows**: Skills encode best practices
- ✅ **Specialize by role**: SCHEDULER vs. ARCHITECT vs. QA_TESTER
- ✅ **Improve continuously**: MetaUpdater detects patterns and proposes fixes

### Real-World Impact

**Example 1: Schedule Generation**
- **Before:** "Generate a schedule" → AI tries, fails ACGME rules, manual fix
- **After:** AI uses `schedule-optimization` skill → Checks N-1 contingency → Backs up database → Generates compliant schedule → Documents rationale in History

**Example 2: Incident Response**
- **Before:** Solver timeout → Manual investigation → One-off fix → Problem recurs
- **After:** AI documents incident → MetaUpdater detects pattern → Proposes constraint pruning → Updates CONSTITUTION → Problem prevented

**Example 3: Code Quality**
- **Before:** AI suggests code → No tests → Breaks in production
- **After:** AI uses `test-writer` skill → Generates comprehensive tests → Runs CI checks → Code review before merge

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESIDENCY SCHEDULER                         │
│                    (Main Application)                           │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │
                    ┌────────────┴────────────┐
                    │   PERSONAL AI           │
                    │   INFRASTRUCTURE (PAI)  │
                    └─────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  CONSTITUTION │      │     AGENTS    │      │    SKILLS     │
│               │      │               │      │               │
│ - Rules       │      │ - SCHEDULER   │      │ - schedule-   │
│ - Policies    │      │ - ARCHITECT   │      │   optimization│
│ - Constraints │      │ - RESILIENCE_ │      │ - swap-       │
│ - Safety      │      │   ENGINEER    │      │   management  │
│   Levels      │      │ - QA_TESTER   │      │ - acgme-      │
└───────────────┘      └───────────────┘      │   compliance  │
        │                        │             └───────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│    HISTORY    │      │     HOOKS     │      │   SCRATCHPAD  │
│               │      │               │      │               │
│ - scheduling/ │      │ - post-       │      │ - Temp files  │
│ - swaps/      │      │   schedule-   │      │ - Debug notes │
│ - compliance/ │      │   generation  │      │ - Experiments │
│ - resilience/ │      │ - post-swap-  │      │ - Drafts      │
│ - incidents/  │      │   execution   │      │ (7-day auto-  │
│               │      │ - post-       │      │  cleanup)     │
│ (Permanent)   │      │   compliance  │      └───────────────┘
└───────────────┘      └───────────────┘
        │                        │
        └────────────┬───────────┘
                     ▼
              ┌─────────────┐
              │ METAUPDATER │
              │             │
              │ - Pattern   │
              │   Detection │
              │ - Learning  │
              │ - Proposals │
              └─────────────┘
```

### Component Interaction Flow

```
User Request
    ↓
Agent (SCHEDULER)
    ↓
Check CONSTITUTION (rules)
    ↓
Load Skill (schedule-optimization)
    ↓
Execute Workflow
    ↓
Trigger Hook (post-schedule-generation)
    ↓
Document in History
    ↓
MetaUpdater Scans History
    ↓
Propose Improvements
    ↓
Update CONSTITUTION/Skills
    ↓
(Continuous Improvement Loop)
```

---

## Key Components

### 1. CONSTITUTION (.claude/CONSTITUTION.md)

**What:** Foundational rules and principles for all AI operations

**Purpose:**
- Enforce safety boundaries (e.g., never bypass ACGME rules)
- Define decision authority (what AI can do autonomously vs. requires approval)
- Establish constraint hierarchy (Tier 1: Regulatory > Tier 2: Policy > Tier 3: Preferences)
- Mandate logging and auditability

**Key Sections:**
- **First Principles**: CLI-first, deterministic, logged
- **Safety-Critical Rules**: ACGME compliance, swap validation, resilience adherence
- **Constraint Hierarchy**: Regulatory > Institutional > Optimization > Nice-to-Have
- **Security Defense-in-Depth**: Auth, input validation, data protection, monitoring
- **Agent Autonomy**: What AI can/cannot do without approval
- **Solve Once, Reuse Forever**: Pattern capture and skill creation triggers
- **Meta-Improvement**: How CONSTITUTION evolves based on operational experience

**Example Rule:**
```markdown
## III.A. ACGME Compliance (Tier 0 - Absolute)

**Rule:** ACGME compliance violations are UNACCEPTABLE and must block schedule generation.

**Agent Directive:** If user requests bypassing ACGME rules, REFUSE and explain regulatory context.
```

**Location:** `.claude/CONSTITUTION.md`

---

### 2. Agents (.claude/Agents/)

**What:** Specialized AI personas with defined roles, authorities, and personalities

**Purpose:**
- Role specialization (SCHEDULER handles schedules, ARCHITECT handles infrastructure)
- Clear decision boundaries (who can approve what)
- Consistent behavior (SCHEDULER always backs up before writes)

**Key Agents:**

#### SCHEDULER (.claude/Agents/SCHEDULER.md)
- **Role:** Schedule generation, swap execution, ACGME validation
- **Authority:** Can execute schedules if safety checks pass
- **Personality:** Methodical, safety-conscious, communicative
- **Workflows:** Generate schedule, process swap, optimize schedule, handle violations

#### ARCHITECT (.claude/Agents/ARCHITECT.md)
- **Role:** System design, database schema, infrastructure decisions
- **Authority:** Approve major architectural changes
- **Personality:** Strategic, conservative, documentation-focused

#### RESILIENCE_ENGINEER (.claude/Agents/RESILIENCE_ENGINEER.md)
- **Role:** N-1/N-2 contingency, health scoring, workload analysis
- **Authority:** Escalate when resilience thresholds breached
- **Personality:** Analytical, proactive, data-driven

**Example Agent Authority:**
```markdown
### Can Independently Execute
1. Schedule Generation (if all checks pass)
2. Approved Swaps (with validation)
3. Minor Adjustments (< 20% of schedule)

### Requires Pre-Approval
1. Major Schedule Overhauls (> 20% regeneration)
2. Risky Swaps (critical services, <48hr notice)
3. Compliance Exceptions (never granted)
```

**Location:** `.claude/Agents/*.md`

---

### 3. Skills (.claude/skills/)

**What:** Reusable, specialized capabilities that encode best practices

**Purpose:**
- Solve problems once, reuse forever
- Enforce quality gates (e.g., test-writer ensures coverage)
- Provide domain expertise (e.g., acgme-compliance knows regulatory rules)
- Enable complex workflows (e.g., safe-schedule-generation: backup → validate → execute → verify)

**Key Skills:**

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| **schedule-optimization** | Multi-objective scheduling with OR-Tools | Generating or optimizing schedules |
| **swap-management** | Swap validation, auto-matching, execution | Processing swap requests |
| **safe-schedule-generation** | Mandatory backup before writes | ANY schedule write operation |
| **acgme-compliance** | Real-time ACGME validation | Validating schedules or swaps |
| **test-writer** | Generate comprehensive test suites | Writing new code (ensure coverage) |
| **systematic-debugger** | Explore-plan-debug-fix workflow | Complex debugging (avoid premature fixes) |
| **database-migration** | Alembic migration expertise | Modifying database schema |
| **security-audit** | HIPAA, OPSEC/PERSEC compliance | Reviewing auth, data handling |

**Skill Structure:**
```markdown
# SKILL.md - [Skill Name]

## Purpose
One-sentence description

## When to Activate
- Trigger 1
- Trigger 2

## Prerequisites
- Required tools
- Required permissions

## Workflow
1. Step 1
2. Step 2
3. Validation

## Guardrails
- Safety check 1
- Safety check 2

## Examples
[Concrete examples]
```

**Location:** `.claude/skills/*/SKILL.md`

---

### 4. History (.claude/History/)

**What:** Permanent audit trail for schedule operations, compliance decisions, and incidents

**Purpose:**
- Institutional memory (why decisions were made)
- Pattern detection (MetaUpdater finds recurring issues)
- ACGME audit compliance (6-10 year lookback requirement)
- Debugging context (what happened during incident X)

**Structure:**
```
.claude/History/
├── scheduling/        # Schedule generation records (1 year retention)
├── swaps/             # Swap execution records (1 year retention)
├── compliance/        # ACGME audits (forever retention)
├── resilience/        # Health assessments (2 year retention)
└── incidents/         # Postmortems (forever retention)
```

**Entry Example:**
```markdown
# Schedule Generation - Block 10 (July-August 2025)

**Summary:** Generated 2-month schedule for 12 residents with 3 leave requests.

## Rationale
- Relaxed "preferred clinic day" constraint for PGY1-03 due to conflict with orientation.
- Applied N-1 contingency: FAC-PD scheduled for TDY Aug 10-20.

## Outcome
✅ ACGME compliance: 0 violations
✅ Coverage: 100% (all 122 blocks assigned)
✅ Fairness: Call distribution variance 0.8σ (target: < 1σ)
```

**Templates:** See `.claude/History/*/TEMPLATE.md` for structured entry formats

**Location:** `.claude/History/`
**Documentation:** `.claude/History/README.md`

---

### 5. Hooks (.claude/Hooks/)

**What:** Automated workflows triggered after specific operations

**Purpose:**
- Enforce post-operation validation (e.g., compliance check after schedule generation)
- Automate follow-up tasks (e.g., notify residents after swap)
- Trigger dependent processes (e.g., recalculate resilience after schedule change)

**Available Hooks:**

| Hook | Trigger | Actions |
|------|---------|---------|
| **post-schedule-generation** | After schedule commit | - ACGME compliance audit<br>- Resilience health calculation<br>- Notification to residents<br>- History entry creation |
| **post-swap-execution** | After swap commit | - Revalidate ACGME compliance<br>- Update fairness metrics<br>- Check for cascade effects<br>- Document in History |
| **post-compliance-audit** | After compliance scan | - Log violations<br>- Alert if thresholds breached<br>- Update dashboard<br>- Escalate if critical |

**Hook Example:**
```markdown
# Post-Schedule-Generation Hook

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
- If notification fails → retry 3x, then manual alert
```

**Location:** `.claude/Hooks/*.md`

---

### 6. Scratchpad (.claude/Scratchpad/)

**What:** Temporary workspace for experiments, debugging, and working notes

**Purpose:**
- Allow messy, iterative work without polluting permanent storage
- Capture in-progress thinking and hypotheses
- Provide space for failed experiments (learning from what doesn't work)
- Auto-cleanup prevents permanent clutter

**Characteristics:**
- **Temporary:** 7-day auto-cleanup (configurable)
- **Not committed:** Added to `.gitignore` (prevents accidental commits)
- **Informal:** No structure required (unlike History)
- **Promotion:** Finalized work moves to History or docs/

**Use Cases:**
- Debugging notes during incident investigation
- Experiment design and results
- Meeting notes and action items
- Draft documentation before formalization
- Quick calculations and scratch work

**Example:**
```markdown
# Scratchpad/2025-08-15_14-30_debug_solver_timeout.md

## Problem
Solver timing out on Block 11. Why?

## Observations
- Constraint count: 1247 (vs. 987 in Block 10)
- New constraints: N95 Fit (180), Flu Vax (80)
- Hypothesis: Over-constrained problem

## Test
Relaxed N95 to soft → solved in 6m ✅

## Conclusion
Credential requirements should be soft constraints with penalties.

## Next
- Create PR to reclassify
- Document in History after fix deployed
```

**Location:** `.claude/Scratchpad/`
**Documentation:** `.claude/Scratchpad/README.md`

---

### 7. MetaUpdater (Conceptual Agent)

**What:** Pattern detection and continuous improvement agent

**Purpose:**
- Scan History for recurring patterns
- Identify optimization opportunities
- Propose CONSTITUTION amendments
- Update skills based on learnings

**How It Works:**
1. **Daily Scan:** Review new History entries
2. **Pattern Detection:** Identify recurring issues (e.g., 3 solver timeouts in 30 days)
3. **Root Cause Analysis:** Why is this happening?
4. **Propose Solution:** Suggest code fix, skill update, or CONSTITUTION amendment
5. **Validation:** Test proposal in development environment
6. **Approval:** Human reviews and approves change
7. **Deployment:** Update applied, pattern monitoring continues

**Example Workflow:**
```
MetaUpdater scans History
    ↓
Detects: 3 solver timeout incidents in 90 days
    ↓
Root Cause: Constraint catalog growing unsustainably
    ↓
Proposes: Add max constraint density rule to CONSTITUTION
    ↓
Human Approves
    ↓
CONSTITUTION updated: "Max 15:1 constraint-to-block ratio"
    ↓
Skill updated: Pre-flight check validates constraint count
    ↓
Pattern breaks: No more timeout incidents
```

**Location:** Conceptual (implemented via periodic review process)

---

## How It Works

### Example Workflow: Schedule Generation

**User Request:** "Generate Block 10 schedule for July-August"

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Agent Selection                                          │
│    User request → SCHEDULER agent activated                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CONSTITUTION Check                                       │
│    ✓ Operation allowed (schedule generation in scope)      │
│    ✓ Safety rules loaded (ACGME compliance mandatory)      │
│    ✓ Constraint hierarchy defined (Tier 1 > 2 > 3 > 4)     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Skill Activation                                         │
│    - Load: schedule-optimization                            │
│    - Load: safe-schedule-generation (mandatory backup)      │
│    - Load: acgme-compliance (validation)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Pre-Flight Checks (from safe-schedule-generation)        │
│    ✓ Database backup created                                │
│    ✓ Resilience health ≥ 0.7                                │
│    ✓ N-1 contingency validated                              │
│    ✓ Constraint catalog loaded (987 constraints)            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Schedule Generation                                      │
│    - OR-Tools CP-SAT solver launched                        │
│    - Progress monitoring (every 5%)                         │
│    - Solver kill-switch active (30-min timeout)             │
│    ✓ Solution found in 4m 32s                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Post-Generation Validation                               │
│    ✓ ACGME validator: 0 violations                          │
│    ✓ Coverage: 100% (all 122 blocks assigned)               │
│    ✓ Fairness: Call variance 0.8σ (< 1σ target)             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Hook Execution (post-schedule-generation)                │
│    - Resilience health recalculated: 0.83                   │
│    - Notifications sent to 12 residents                     │
│    - Dashboard updated                                      │
│    - Calendar integrations synced                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. History Documentation                                    │
│    Created: .claude/History/scheduling/2025-07-15_block10   │
│    _gen001.md                                               │
│    - Generation ID, timestamp, parameters                   │
│    - Solver statistics, outcome, rationale                  │
│    - ACGME compliance, coverage, fairness metrics           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. MetaUpdater Scan (periodic)                              │
│    - Analyze solve time trend (baseline: 4m 30s)            │
│    - Check for patterns (constraint count growth?)          │
│    - Update skill knowledge (successful generation logged)  │
└─────────────────────────────────────────────────────────────┘
```

**Result:** Compliant schedule generated, documented, and monitored for continuous improvement.

---

## Core Principles

### 1. Solve Once, Reuse Forever

**Problem:** Same task performed repeatedly (e.g., "write tests for this code")

**PAI Solution:**
- First time: AI figures it out manually
- Second time: AI recognizes pattern
- Third time: AI creates **skill** (e.g., `test-writer`)
- Forever: AI uses skill automatically (quality guaranteed)

**Benefits:**
- Consistent quality (no reinventing wheel)
- Faster execution (no rethinking)
- Captured expertise (skill documents best practices)

**Example:**
```
Request: "Write tests for swap validator"
    ↓
First time: AI manually writes tests (takes 10 minutes)
    ↓
Pattern detected: "This is the 3rd test suite request"
    ↓
Create test-writer skill with:
- Test pyramid structure (70% unit, 20% integration, 10% E2E)
- Edge case coverage (happy path, error cases, ACGME scenarios)
- Naming convention (test_<function>_<scenario>_<result>)
    ↓
Future requests: AI uses test-writer skill (takes 2 minutes, higher quality)
```

---

### 2. Progressive Disclosure

**Problem:** Complex system with steep learning curve

**PAI Solution:**
- **Layer 1 (Surface):** Common tasks quick reference (see below)
- **Layer 2 (Details):** Component READMEs (History/README.md, Scratchpad/README.md)
- **Layer 3 (Deep Dive):** Full documentation (CONSTITUTION.md, Agent/*.md, skills/*/SKILL.md)

**Benefits:**
- New developers: Get productive in hours (not days)
- Experienced developers: Access deep knowledge when needed
- AI agents: Load context incrementally (avoid overload)

**Example:**
```
New developer wants to generate schedule:
    ↓
Layer 1: Quick reference says "Use SCHEDULER agent with schedule-optimization skill"
    ↓
Layer 2: History/scheduling/README.md shows template and examples
    ↓
Layer 3: SCHEDULER.md explains full workflow, safety checks, escalation rules
```

---

### 3. Defense in Depth (Safety)

**Problem:** Single point of failure can cause catastrophic errors

**PAI Solution:** Multiple independent safety layers

**Example: Schedule Generation Safety**
1. **CONSTITUTION:** Defines ACGME compliance as non-negotiable
2. **Agent:** SCHEDULER enforces backup before writes
3. **Skill:** safe-schedule-generation validates pre-conditions
4. **Hook:** post-schedule-generation validates post-conditions
5. **History:** Documents rationale for audit trail

**Result:** Even if one layer fails, others prevent disaster

---

### 4. Institutional Memory (Learning)

**Problem:** Organizations forget lessons from past incidents

**PAI Solution:**
- **History:** Permanent record of what happened and why
- **MetaUpdater:** Scans History for patterns
- **Skills/CONSTITUTION:** Updates encode learnings

**Example:**
```
Month 1: Solver timeout incident
    ↓
History entry documents root cause (over-constrained problem)
    ↓
Month 2: Another solver timeout (same root cause)
    ↓
MetaUpdater detects pattern
    ↓
Proposes: Add constraint density limit to CONSTITUTION
    ↓
Month 3+: No more timeouts (pattern broken by preventive rule)
```

---

### 5. Explicit Over Implicit

**Problem:** Assumptions cause misunderstandings and errors

**PAI Solution:** Everything is written down

**Examples:**
- **Agent authority:** Explicitly listed (can/cannot do)
- **Constraint hierarchy:** Explicitly tiered (Regulatory > Policy > Preferences)
- **Decision rationale:** Explicitly documented (why, not just what)
- **Safety rules:** Explicitly enforced (CONSTITUTION)

**Benefit:** AI and humans have shared understanding (no surprises)

---

## Common Tasks Quick Reference

### For Developers

**Generate a schedule:**
```bash
# 1. Activate SCHEDULER agent
# 2. Load schedule-optimization skill
# 3. Command: "Generate Block 10 schedule for July-August"
# AI will:
#   - Backup database
#   - Validate pre-conditions
#   - Run solver
#   - Validate ACGME compliance
#   - Document in History
```

**Process a swap request:**
```bash
# 1. Activate SCHEDULER agent
# 2. Load swap-management skill
# 3. Command: "Process swap S12345"
# AI will:
#   - Validate safety checks
#   - Check ACGME compliance
#   - Execute if approved
#   - Document in History
```

**Debug an incident:**
```bash
# 1. Activate systematic-debugger skill
# 2. Create Scratchpad entry for notes
# 3. Workflow: Explore → Plan → Debug → Fix
# 4. Document final solution in History/incidents/
```

**Write tests for new code:**
```bash
# 1. Load test-writer skill
# 2. Command: "Write tests for backend/app/services/swap_executor.py"
# AI will:
#   - Generate unit tests (70%)
#   - Generate integration tests (20%)
#   - Generate E2E tests (10%)
#   - Ensure coverage ≥ 80%
```

**Create a database migration:**
```bash
# 1. Load database-migration skill
# 2. Command: "Add middle_name field to Person model"
# AI will:
#   - Update model
#   - Generate Alembic migration
#   - Test migration up/down
#   - Document in commit message
```

**Review ACGME compliance:**
```bash
# 1. Load acgme-compliance skill
# 2. Command: "Audit Block 10 for ACGME violations"
# AI will:
#   - Check 80-hour rule (all residents)
#   - Check 1-in-7 rule (all residents)
#   - Check supervision ratios
#   - Generate compliance report
#   - Document in History/compliance/
```

---

### For AI Agents

**Before any operation:**
1. Check CONSTITUTION for applicable rules
2. Load relevant agent persona (SCHEDULER, ARCHITECT, etc.)
3. Load required skills
4. Execute workflow with safety checks
5. Document outcome in History
6. Trigger appropriate hooks

**When creating new patterns:**
1. Detect: "Have I done this 3+ times?"
2. Extract: Generalize solution beyond specific instance
3. Document: Create skill or update CONSTITUTION
4. Test: Verify pattern works in multiple contexts
5. Deploy: Make available for future use

**When encountering errors:**
1. Create Scratchpad entry for investigation
2. Use systematic-debugger workflow
3. Document root cause
4. Implement fix
5. Promote Scratchpad notes to History incident entry
6. Update skills/CONSTITUTION to prevent recurrence

---

## Maintenance & Evolution

### Daily Operations

**AI Agents:**
- Execute tasks using skills
- Document outcomes in History
- Create Scratchpad entries for active work
- Follow CONSTITUTION rules

**Automated:**
- Scratchpad cleanup (delete files >7 days old)
- Hook execution (post-operation workflows)
- Monitoring alerts (ACGME violations, resilience health)

### Weekly Reviews

**Responsibilities:**
- Review new History entries (patterns emerging?)
- Check Scratchpad (anything to promote to History?)
- Validate hook execution (all triggers working?)
- Monitor skill usage (which skills most valuable?)

### Monthly Reviews

**MetaUpdater Activities:**
- Scan History for recurring patterns
- Identify optimization opportunities
- Propose CONSTITUTION amendments
- Update skills based on learnings

**Human Activities:**
- Review and approve MetaUpdater proposals
- Archive old History entries (past retention period)
- Assess PAI effectiveness (metrics: incident recurrence, solve time trends)
- Train new team members on PAI

### Quarterly Reviews

**Strategic Assessment:**
- Are agents operating within authority boundaries?
- Is CONSTITUTION up-to-date with regulations?
- Are skills reducing repetitive work?
- Is History providing value for audits?

**Improvement Planning:**
- Identify gaps in skill coverage
- Propose new agents (if specialization needed)
- Update retention policies
- Refine hook workflows

---

### Amendment Process

**When to Amend CONSTITUTION:**
1. Recurring issues (same problem 3+ times)
2. False positives (safety rules block legitimate ops)
3. False negatives (safety rules miss actual risks)
4. New regulations (ACGME changes)
5. Post-incident reviews (gaps identified)

**Amendment Procedure:**
1. **Propose:** Document problem and proposed change
2. **Impact Analysis:** Assess effects on code and workflows
3. **Review:** 7-day stakeholder feedback period
4. **Approve:** Explicit human approval required
5. **Deploy:** Update CONSTITUTION, version increment
6. **Communicate:** Notify all agents and developers

**Amendment Template:**
```markdown
## Amendment Proposal: [Title]

### Current Rule
[Quote existing rule]

### Problem
[Why current rule is insufficient]

### Proposed Change
[New rule text]

### Impact
- Affects: [Systems/processes]
- Breaking Changes: [Yes/No]
- Migration Path: [If applicable]

### Rationale
[Why this improves system]
```

---

## Getting Started (For New Developers)

### Day 1: Orientation

**Read these documents (in order):**
1. `README.md` - Project overview
2. `CLAUDE.md` - Development guidelines
3. `docs/PERSONAL_INFRASTRUCTURE.md` - This document
4. `.claude/CONSTITUTION.md` - Foundational rules

**Understand:**
- What PAI is and why it exists
- How agents, skills, and History work together
- Where to find information (progressive disclosure)

---

### Day 2: Hands-On Practice

**Task 1: Explore History**
```bash
# Find all schedule generation records
ls .claude/History/scheduling/

# Read a sample entry
cat .claude/History/scheduling/2025-07-15_block10_gen001.md

# Understand what was generated and why
```

**Task 2: Review an Agent**
```bash
# Read SCHEDULER agent definition
cat .claude/Agents/SCHEDULER.md

# Note:
# - What can SCHEDULER do autonomously?
# - What requires approval?
# - What are the safety protocols?
```

**Task 3: Examine a Skill**
```bash
# Read schedule-optimization skill
cat .claude/skills/schedule-optimization/SKILL.md

# Note:
# - When is this skill activated?
# - What are the prerequisites?
# - What is the workflow?
```

---

### Day 3: Execute a Task

**Guided Exercise: Generate a Test Schedule**
```bash
# 1. Activate SCHEDULER agent (via AI interface)
# 2. Command: "Generate a test schedule for 3 residents, 1 week (Block 0)"
# 3. Observe:
#    - Skills loaded (schedule-optimization, safe-schedule-generation)
#    - Safety checks (backup, resilience validation)
#    - Solver execution
#    - ACGME validation
#    - History entry creation
# 4. Review History entry: .claude/History/scheduling/[DATE]_block0_test.md
```

**Reflection:**
- How did PAI guide the AI through this task?
- What safety checks prevented errors?
- How would you find this record 6 months from now?

---

### Week 1: Independent Work

**Your First Pull Request:**
1. Pick a task from backlog
2. Use AI with appropriate agent/skills
3. Follow CONSTITUTION rules
4. Write tests (test-writer skill)
5. Document in Scratchpad (working notes)
6. Submit PR
7. After merge, promote Scratchpad notes to History (if applicable)

**Mentorship:**
- Ask questions in team chat
- Pair program with experienced developer
- Review other PRs to learn patterns

---

## Advanced Topics

### Custom Skill Creation

**When to create a new skill:**
- Task performed 3+ times
- Multi-step workflow requiring coordination
- Domain expertise needed (ACGME, security, etc.)
- Error-prone task requiring guardrails

**Skill Creation Workflow:**
1. **Identify Pattern:** "I've done this 3 times - time for a skill"
2. **Define Scope:** What does this skill do? When should it activate?
3. **Document Workflow:** Step-by-step procedure
4. **Add Guardrails:** Safety checks to prevent errors
5. **Create Examples:** Concrete use cases
6. **Test:** Verify skill works in multiple contexts
7. **Deploy:** Add to `.claude/skills/[skill-name]/SKILL.md`

**Template:**
```markdown
# SKILL.md - [Skill Name]

## Purpose
[One sentence]

## When to Activate
- Trigger 1
- Trigger 2

## Prerequisites
- Tool 1
- Permission 2

## Workflow
1. Step 1
2. Step 2
3. Validation

## Guardrails
- Safety check 1
- Safety check 2

## Examples
### Example 1: [Scenario]
[Concrete walkthrough]

### Example 2: [Scenario]
[Concrete walkthrough]
```

---

### Agent Customization

**When to create a new agent:**
- Distinct role not covered by existing agents
- Specialized decision authority needed
- Different personality/approach required

**Agent Creation Workflow:**
1. **Define Role:** What is this agent responsible for?
2. **Set Authority Boundaries:** What can it do autonomously vs. requiring approval?
3. **Define Personality:** How should it communicate and behave?
4. **List Skills:** Which skills does this agent use?
5. **Escalation Rules:** When/how does it escalate to humans or other agents?
6. **Create Charter:** Document in `.claude/Agents/[AGENT_NAME].md`

**Example:**
```markdown
# QA_TESTER Agent

## Charter
**Role:** Quality assurance, adversarial testing, edge case discovery
**Authority:** Can flag issues, cannot merge code without review
**Personality:** Skeptical, thorough, systematic

## Skills Access
- test-writer (full access)
- systematic-debugger (full access)
- code-review (read only)

## Escalation Rules
- Critical bugs → Immediate escalation to ARCHITECT
- Security issues → Escalate to security-audit skill + human review
```

---

### History Analysis Techniques

**Query Patterns:**

**Find all incidents in date range:**
```bash
find .claude/History/incidents/ -name "2025-08-*.md"
```

**Extract all decision rationales (for learning):**
```bash
grep -r "Rationale:" .claude/History/ -A 3 > decisions.txt
```

**Identify recurring constraint conflicts:**
```bash
grep -r "Conflict:" .claude/History/scheduling/ | \
  cut -d: -f3 | sort | uniq -c | sort -rn
```

**Timeline reconstruction (all ops on specific date):**
```bash
find .claude/History/ -name "2025-08-15*.md" \
  -exec echo "=== {} ===" \; \
  -exec cat {} \;
```

**Performance trend analysis:**
```bash
grep -r "Solve Time:" .claude/History/scheduling/ | \
  awk '{print $NF}' | sort -n
```

---

### Integration with External Systems

**MCP Server Integration:**
- PAI agents can use MCP tools (34+ scheduling tools available)
- Skills can compose MCP tool calls
- History documents MCP tool usage for audit trail

**CI/CD Integration:**
- Pre-commit hooks enforce CONSTITUTION rules (secret scanning, linting)
- CI pipeline validates skill adherence (test coverage, ACGME compliance)
- Post-deploy hooks trigger History entry creation

**Monitoring Integration:**
- Prometheus metrics track PAI operations
- Grafana dashboards visualize skill usage, agent activity
- Alerts trigger when CONSTITUTION rules violated

---

## Appendix: PAI Philosophy

### Why We Built This

Traditional software development with AI assistance suffers from:
- **Context Amnesia:** Every conversation starts from scratch
- **Inconsistent Behavior:** AI makes different decisions each time
- **No Learning:** Same mistakes repeated
- **Safety Gaps:** No guardrails on dangerous operations
- **Knowledge Silos:** Expertise trapped in individual developers

PAI solves these problems by treating AI infrastructure as **first-class architecture**.

### Design Principles

1. **Explicit over Implicit:** Write everything down (CONSTITUTION, agents, skills)
2. **Safety First:** Multiple independent layers (defense in depth)
3. **Learn from History:** Institutional memory via permanent audit trail
4. **Solve Once, Reuse Forever:** Capture solutions as reusable skills
5. **Progressive Disclosure:** Surface → Details → Deep Dive
6. **Continuous Improvement:** MetaUpdater detects patterns and proposes fixes

### Inspired By

- **Kai Patterns:** Framework for organizing AI-assisted development
- **ACGME Regulations:** Tiered constraint hierarchies (regulatory > policy > preferences)
- **Site Reliability Engineering:** Defense in depth, blameless postmortems
- **Knowledge Management:** Capture, codify, reuse
- **Quality Systems (ISO 9001):** Document processes, measure, improve

---

## Related Documentation

**Core PAI:**
- `.claude/CONSTITUTION.md` - Foundational rules
- `.claude/History/README.md` - Audit trail system
- `.claude/Scratchpad/README.md` - Temporary workspace

**Agents:**
- `.claude/Agents/SCHEDULER.md` - Schedule generation agent
- `.claude/Agents/ARCHITECT.md` - System design agent
- `.claude/Agents/RESILIENCE_ENGINEER.md` - Resilience monitoring agent

**Skills:**
- `.claude/skills/schedule-optimization/SKILL.md`
- `.claude/skills/swap-management/SKILL.md`
- `.claude/skills/acgme-compliance/SKILL.md`
- `.claude/skills/test-writer/SKILL.md`

**Project Documentation:**
- `README.md` - Project overview
- `CLAUDE.md` - Development guidelines
- `docs/architecture/SOLVER_ALGORITHM.md` - Scheduling engine
- `docs/development/DEBUGGING_WORKFLOW.md` - Debugging methodology

---

**Version:** 1.0.0
**Last Updated:** 2025-12-26
**Maintained By:** All agents and developers (collaborative)

---

## Feedback & Contribution

PAI is a living system. If you:
- Find gaps in documentation
- Identify new patterns worth capturing
- Discover inefficiencies in workflows
- Have ideas for new skills or agents

**Please:**
1. Create Scratchpad entry with your idea
2. Discuss with team
3. Propose amendment (if CONSTITUTION change)
4. Create PR with updates
5. Document rationale in History

**Remember:** PAI improves through use. Your contributions make the system better for everyone.

---

**Welcome to the Personal AI Infrastructure. Let's build great software together.**
