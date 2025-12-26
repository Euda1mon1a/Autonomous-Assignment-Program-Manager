***REMOVED*** AI AGENT OPERATIONAL MODES
***REMOVED*** Safety Postures and Autonomy Levels for Medical Residency Scheduling

> **Version:** 1.0
> **Last Updated:** 2025-12-26
> **Purpose:** Define simplified mode framework for AI agents working with PHI and ACGME-regulated data
> **See Also:** [OPERATIONAL_MODES.md](OPERATIONAL_MODES.md) - Detailed technical specifications

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Mode Definitions](***REMOVED***mode-definitions)
3. [Mode Selection Decision Tree](***REMOVED***mode-selection-decision-tree)
4. [CLI Integration](***REMOVED***cli-integration)
5. [Default Mode by Context](***REMOVED***default-mode-by-context)
6. [Mode Escalation & De-escalation](***REMOVED***mode-escalation--de-escalation)
7. [Emergency Override Protocol](***REMOVED***emergency-override-protocol)
8. [Mode-Specific Prompt Prefixes](***REMOVED***mode-specific-prompt-prefixes)
9. [Safety Guardrails for Medical Data](***REMOVED***safety-guardrails-for-medical-data)

---

***REMOVED******REMOVED*** Overview

This framework provides **4 operational modes** that balance safety and autonomy for AI agents working with medical residency scheduling data containing PHI (Protected Health Information) and subject to ACGME regulations.

***REMOVED******REMOVED******REMOVED*** Design Philosophy

Based on Kai's maturity framing and Anthropic's safety patterns:

1. **Fail-Safe by Default**: Always start in read-only mode
2. **Explicit Escalation**: Higher-risk operations require explicit approval
3. **PHI Protection**: Never log, export, or leak Protected Health Information
4. **ACGME Compliance**: All changes must maintain regulatory compliance
5. **Audit Everything**: Complete trail for medical/military accountability

***REMOVED******REMOVED******REMOVED*** Mode Hierarchy (Low → High Risk)

```
Risk Level:  LOW ────────────> MEDIUM ────────────> HIGH ────────────> CRITICAL

Mode:        ANALYZE          PLAN              EXECUTE             MANAGE
             (read-only)      (write plans)     (propose code)      (auto-approve)

Default:     ✓ YES            No                No                  No
PHI Access:  Read-only        None              None (code only)    Read/Write
Approval:    Not required     Not required      Human required      Emergency only
```

***REMOVED******REMOVED******REMOVED*** Mode Mapping to Existing System

| New Mode (Simplified) | Maps to Existing Mode | Purpose |
|----------------------|----------------------|---------|
| **ANALYZE** | SAFE_AUDIT | Read-only analysis and compliance checks |
| **PLAN** | _(New)_ | Write planning docs, no code changes |
| **EXECUTE** | SUPERVISED_EXECUTION | Propose code changes via PR |
| **MANAGE** | EMERGENCY_OVERRIDE | Auto-approve low-risk changes (future) |

---

***REMOVED******REMOVED*** Mode Definitions

***REMOVED******REMOVED******REMOVED*** 1. ANALYZE Mode (Safest)

**Risk Level:** LOW
**Default Mode:** YES
**PHI Access:** Read-only
**Database Access:** Read-only

***REMOVED******REMOVED******REMOVED******REMOVED*** Purpose
Pure information gathering and compliance analysis. Maximum validation, zero modification risk. This is the **default mode** for all AI agents.

***REMOVED******REMOVED******REMOVED******REMOVED*** What You CAN Do
- ✅ Read code, documentation, configurations
- ✅ Analyze schedules for ACGME compliance
- ✅ Search codebase for patterns
- ✅ Generate reports and summaries
- ✅ Answer questions about architecture
- ✅ What-if scenario analysis (sandbox)
- ✅ Grep, glob, read files

***REMOVED******REMOVED******REMOVED******REMOVED*** What You CANNOT Do
- ❌ Edit any code files
- ❌ Write any files (except notes to `.claude/Scratchpad/`)
- ❌ Modify database
- ❌ Run tests that modify state
- ❌ Create PRs
- ❌ Git commits

***REMOVED******REMOVED******REMOVED******REMOVED*** Allowed Tools
```
Read, Grep, Glob, WebFetch, BashOutput (read-only commands)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Use Cases
- Compliance audits
- Schedule analysis
- Codebase exploration
- Research and investigation
- Security audits
- Documentation review
- Training and orientation

***REMOVED******REMOVED******REMOVED******REMOVED*** Entry Command
```bash
***REMOVED*** Default mode - no command needed
aapm --mode=ANALYZE

***REMOVED*** Alternative syntax
aapm mode analyze
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Prompt Prefix
```
[ANALYZE] Reviewing schedule for ACGME compliance...
```

---

***REMOVED******REMOVED******REMOVED*** 2. PLAN Mode (Low Risk)

**Risk Level:** LOW
**Default Mode:** NO
**PHI Access:** None
**Database Access:** None

***REMOVED******REMOVED******REMOVED******REMOVED*** Purpose
Create planning documents, specifications, and task lists. Write to planning directories only. No code changes, no database access.

***REMOVED******REMOVED******REMOVED******REMOVED*** What You CAN Do
- ✅ All ANALYZE mode capabilities
- ✅ Write to `.claude/` directory (plans, notes, scratchpad)
- ✅ Write to `docs/` directory (documentation)
- ✅ Create task lists and specifications
- ✅ Draft architecture proposals
- ✅ Write test plans
- ✅ Create meeting notes

***REMOVED******REMOVED******REMOVED******REMOVED*** What You CANNOT Do
- ❌ Edit source code (`backend/`, `frontend/`)
- ❌ Modify database
- ❌ Create PRs
- ❌ Git commits
- ❌ Run code changes

***REMOVED******REMOVED******REMOVED******REMOVED*** Allowed Tools
```
Read, Grep, Glob, WebFetch, Write (limited to .claude/ and docs/)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Allowed Write Paths
```
.claude/Scratchpad/
.claude/History/
.claude/Telemetry/
docs/planning/
docs/architecture/
docs/research/
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Use Cases
- Sprint planning
- Architecture design
- Research documentation
- Investigation notes
- Task breakdown
- Meeting notes
- Specification drafting

***REMOVED******REMOVED******REMOVED******REMOVED*** Entry Command
```bash
aapm --mode=PLAN
aapm mode plan
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Prompt Prefix
```
[PLAN] Creating architecture proposal in docs/planning/...
```

---

***REMOVED******REMOVED******REMOVED*** 3. EXECUTE Mode (Standard Risk)

**Risk Level:** MEDIUM
**Default Mode:** NO (in Web), YES (in CLI/IDE)
**PHI Access:** None (code changes only)
**Database Access:** None (local dev DB only)

***REMOVED******REMOVED******REMOVED******REMOVED*** Purpose
Propose and implement code changes with human oversight. All changes go through PR review. This is the **standard working mode** for development tasks.

***REMOVED******REMOVED******REMOVED******REMOVED*** What You CAN Do
- ✅ All ANALYZE and PLAN capabilities
- ✅ Edit source code
- ✅ Write tests
- ✅ Run tests and linters
- ✅ Create git commits
- ✅ Create PRs (require human approval)
- ✅ Local development operations

***REMOVED******REMOVED******REMOVED******REMOVED*** What You CANNOT Do
- ❌ Push directly to `origin/main`
- ❌ Merge PRs without human approval
- ❌ Modify production database
- ❌ Deploy to production
- ❌ Bypass code review

***REMOVED******REMOVED******REMOVED******REMOVED*** Required Workflow
```
1. Create feature branch from origin/main
2. Make code changes + tests
3. Run linters and tests locally
4. Commit to feature branch
5. Push to GitHub
6. Create PR → Wait for human review
7. Address review comments
8. Human approves and merges
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Allowed Tools
```
All tools: Read, Write, Edit, Grep, Glob, Bash, Git operations
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Guardrails
- **PR Required**: All changes must go through pull request
- **Tests Must Pass**: CI must pass before merge
- **No Force Push**: Never `git push --force` to main/master
- **PHI Protection**: Never commit PHI or real names
- **Linting Required**: Code must pass `ruff` (Python) and `eslint` (TS)

***REMOVED******REMOVED******REMOVED******REMOVED*** Use Cases
- Feature implementation
- Bug fixes
- Refactoring
- Test writing
- Documentation updates
- Dependency updates

***REMOVED******REMOVED******REMOVED******REMOVED*** Entry Command
```bash
***REMOVED*** CLI/IDE default mode for code work
aapm --mode=EXECUTE
aapm mode execute
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Prompt Prefix
```
[EXECUTE] Implementing feature X, creating PR for review...
```

---

***REMOVED******REMOVED******REMOVED*** 4. MANAGE Mode (Future/Experimental)

**Risk Level:** HIGH (Emergency) or LOW (Automated maintenance)
**Default Mode:** NO
**PHI Access:** Read/Write (emergency only)
**Database Access:** Full (emergency only)

***REMOVED******REMOVED******REMOVED******REMOVED*** Purpose
**Two sub-modes:**

1. **MANAGE:EMERGENCY** - Emergency operations with approval gates bypassed
2. **MANAGE:AUTO** - Automated low-risk maintenance (future, not implemented)

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 4a. MANAGE:EMERGENCY Sub-Mode

**Maps to:** EMERGENCY_OVERRIDE mode (see [OPERATIONAL_MODES.md](OPERATIONAL_MODES.md))

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** When to Use
- Resident hospitalized, shift starts in < 4 hours
- Urgent military deployment (< 24 hour notice)
- Mass casualty event requiring immediate coverage
- Critical system failure during active scheduling

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** Requirements
- **PD Approval Required**: Program Director must authorize
- **Justification Required**: Document reason for emergency
- **Time Limited**: 4-hour maximum duration
- **Maximum Audit**: Every action logged
- **Post-Review Required**: All actions reviewed within 24 hours

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** Entry Command
```bash
aapm emergency declare \
  --reason="PGY2-01 hospitalized, inpatient call 12/26 PM uncovered" \
  --approved-by="Dr.ProgramDirector"

***REMOVED*** Alternative
aapm --mode=MANAGE:EMERGENCY --emergency-reason="..." --approved-by="PD"
```

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** Prompt Prefix
```
⚠️  [MANAGE:EMERGENCY] EMERGENCY MODE ACTIVE - Filling critical coverage gap...
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 4b. MANAGE:AUTO Sub-Mode (Future)

**Status:** NOT YET IMPLEMENTED - Placeholder for future automation

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** Planned Use Cases
- Automated dependency updates (Dependabot-style)
- Auto-fix linting errors
- Auto-regenerate documentation
- Auto-update test snapshots

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** Planned Guardrails
- Scope limits (only approved file patterns)
- Test pass required before merge
- Size limits (< 100 lines changed)
- Automated rollback on CI failure
- Human override always available

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** Future Entry Command
```bash
***REMOVED*** Not yet implemented
aapm --mode=MANAGE:AUTO --task="update-dependencies"
```

---

***REMOVED******REMOVED*** Mode Selection Decision Tree

***REMOVED******REMOVED******REMOVED*** Quick Selection Guide

```
What are you doing?
│
├─ Just reading/analyzing?
│  └─> ANALYZE (default, always safe)
│
├─ Writing plans/docs only?
│  └─> PLAN (low risk, no code changes)
│
├─ Writing code for a PR?
│  └─> EXECUTE (standard development mode)
│
└─ Emergency requiring immediate action?
   │
   ├─ Do you have PD approval?
   │  └─> YES: MANAGE:EMERGENCY
   │  └─> NO: Get approval first or use EXECUTE
   │
   └─ Can it wait for PR review?
      └─> YES: Use EXECUTE instead
```

***REMOVED******REMOVED******REMOVED*** Detailed Decision Matrix

| Question | ANALYZE | PLAN | EXECUTE | MANAGE:EMERGENCY |
|----------|---------|------|---------|------------------|
| Modifying code? | ❌ | ❌ | ✅ | ✅ |
| Writing documentation? | ❌* | ✅ | ✅ | ❌ |
| Creating PRs? | ❌ | ❌ | ✅ | ❌ |
| Accessing production DB? | Read-only | ❌ | ❌ | ✅ |
| Bypassing approval? | N/A | N/A | ❌ | ✅ |
| Time-limited? | No | No | No | Yes (4h max) |
| Post-review required? | No | No | Yes (PR) | Yes (24h) |

*Can write to `.claude/Scratchpad/` for notes

***REMOVED******REMOVED******REMOVED*** Risk Assessment Questions

Before escalating from ANALYZE:

1. **Do I need to modify files?**
   - No → Stay in ANALYZE
   - Yes, docs/plans only → Use PLAN
   - Yes, code → Use EXECUTE

2. **Is this an emergency?**
   - No → Use EXECUTE with normal PR flow
   - Yes → Check if MANAGE:EMERGENCY criteria met

3. **Can I wait for review?**
   - Yes → Use EXECUTE (standard flow)
   - No + PD approval → MANAGE:EMERGENCY
   - No + no approval → Cannot proceed

---

***REMOVED******REMOVED*** CLI Integration

***REMOVED******REMOVED******REMOVED*** Command Syntax

```bash
***REMOVED*** Explicit mode setting
aapm --mode=ANALYZE    ***REMOVED*** Read-only analysis
aapm --mode=PLAN       ***REMOVED*** Planning and documentation
aapm --mode=EXECUTE    ***REMOVED*** Code changes via PR
aapm --mode=MANAGE:EMERGENCY --emergency-reason="..." --approved-by="PD"

***REMOVED*** Alternative syntax (same as OPERATIONAL_MODES.md)
aapm mode analyze
aapm mode plan
aapm mode execute
aapm emergency declare --reason="..." --approved-by="PD"

***REMOVED*** Check current mode
aapm mode status

***REMOVED*** Mode history
aapm mode history --hours=24
```

***REMOVED******REMOVED******REMOVED*** Mode-Aware Commands

Some commands automatically trigger mode transitions:

| Command | Triggers Mode | Reason |
|---------|---------------|--------|
| `aapm audit` | ANALYZE | Read-only operation |
| `aapm analyze` | ANALYZE | Read-only operation |
| `aapm plan --write` | PLAN | Writing planning docs |
| `aapm code implement` | EXECUTE | Code changes |
| `aapm test write` | EXECUTE | Writing tests |
| `aapm emergency declare` | MANAGE:EMERGENCY | Emergency authorization |

---

***REMOVED******REMOVED*** Default Mode by Context

AI agents should detect their environment and default to the appropriate mode:

***REMOVED******REMOVED******REMOVED*** Environment Detection

```python
def detect_default_mode() -> str:
    """Detect appropriate default mode based on context."""

    ***REMOVED*** Check interface type
    interface = detect_interface()  ***REMOVED*** "web", "cli", "ide"

    ***REMOVED*** Check git context
    branch = run_command("git branch --show-current")

    ***REMOVED*** Decision logic
    if interface == "web":
        return "ANALYZE"  ***REMOVED*** Web is always read-only by default

    elif interface in ["cli", "ide"]:
        if branch in ["main", "master"]:
            ***REMOVED*** On main branch - be cautious
            return "ANALYZE"
        elif branch.startswith("claude/") or branch.startswith("feature/"):
            ***REMOVED*** On feature branch - ready to code
            return "EXECUTE"
        else:
            return "ANALYZE"

    else:
        ***REMOVED*** Unknown environment - be safe
        return "ANALYZE"
```

***REMOVED******REMOVED******REMOVED*** Context-Based Defaults

| Context | Default Mode | Rationale |
|---------|--------------|-----------|
| **Web Interface** | ANALYZE | No file system access, suggestions only |
| **CLI on main branch** | ANALYZE | Protect main branch from accidental edits |
| **CLI on feature branch** | EXECUTE | Ready for development work |
| **IDE Extension** | EXECUTE | Developers expect code editing |
| **Unknown** | ANALYZE | Fail-safe default |

***REMOVED******REMOVED******REMOVED*** Override Defaults

Users can always override the default:

```bash
***REMOVED*** Force EXECUTE mode even on main branch (not recommended)
aapm --mode=EXECUTE --force

***REMOVED*** Drop to ANALYZE mode while on feature branch
aapm --mode=ANALYZE
```

---

***REMOVED******REMOVED*** Mode Escalation & De-escalation

***REMOVED******REMOVED******REMOVED*** Escalation Rules

```
ANALYZE ──(write docs)──> PLAN ──(write code)──> EXECUTE ──(emergency)──> MANAGE:EMERGENCY
   ▲                        │                        │                          │
   │                        │                        │                          │
   └────────────────────────┴────────────────────────┴──────────────────────────┘
                    (auto de-escalate after operation completes)
```

***REMOVED******REMOVED******REMOVED*** Automatic De-escalation

The system automatically returns to a safer mode after operations complete:

| From Mode | Trigger | To Mode | Timing |
|-----------|---------|---------|--------|
| PLAN | Task complete | ANALYZE | Immediate |
| EXECUTE | PR created | ANALYZE | After push |
| EXECUTE | Session timeout | ANALYZE | 2 hours |
| MANAGE:EMERGENCY | Emergency resolved | ANALYZE | Immediate |
| MANAGE:EMERGENCY | Timeout | ANALYZE | 4 hours (hard limit) |

***REMOVED******REMOVED******REMOVED*** Manual De-escalation

```bash
***REMOVED*** Return to safe mode anytime
aapm mode analyze

***REMOVED*** Cancel emergency mode
aapm emergency resolve
```

***REMOVED******REMOVED******REMOVED*** Escalation Approval Gates

| Transition | Approval Required | Validator |
|------------|-------------------|-----------|
| ANALYZE → PLAN | No | Auto-approved |
| ANALYZE → EXECUTE | No (but PR requires review) | Auto-approved |
| PLAN → EXECUTE | No (but PR requires review) | Auto-approved |
| Any → MANAGE:EMERGENCY | **YES** | Program Director |

---

***REMOVED******REMOVED*** Emergency Override Protocol

***REMOVED******REMOVED******REMOVED*** Emergency Declaration Checklist

Before declaring MANAGE:EMERGENCY mode, verify **ALL** of the following:

- [ ] **True Emergency**: Patient safety, critical coverage, or ACGME violation imminent
- [ ] **Time-Critical**: < 24 hours to respond, cannot wait for normal approval
- [ ] **Authorization**: Program Director available and has approved
- [ ] **Justification**: Clear, documented reason for emergency status
- [ ] **No Alternatives**: Normal EXECUTE mode with fast-track PR not viable

***REMOVED******REMOVED******REMOVED*** Emergency Scenarios

***REMOVED******REMOVED******REMOVED******REMOVED*** ✅ Valid Emergencies

1. Resident hospitalized, shift starts in < 4 hours
2. Urgent military deployment (< 24 hour notice)
3. Family emergency requiring immediate leave
4. Mass casualty event requiring all-hands activation
5. System failure during critical scheduling period

***REMOVED******REMOVED******REMOVED******REMOVED*** ❌ NOT Emergencies (Use EXECUTE Instead)

1. Planned vacation (days/weeks notice)
2. Conference attendance (scheduled in advance)
3. Preference changes (not urgent)
4. Administrative convenience
5. Missed deadline (poor planning ≠ emergency)

***REMOVED******REMOVED******REMOVED*** Emergency Workflow

```bash
***REMOVED*** 1. Declare emergency (requires PD approval)
aapm emergency declare \
  --reason="PGY2-01 hospitalized, inpatient call 12/26 PM uncovered" \
  --approved-by="Dr.ProgramDirector"

***REMOVED*** 2. Perform emergency operations (no approval gates)
aapm emergency assign --block="2025-12-26-PM" --person="PGY3-02"

***REMOVED*** 3. Resolve emergency when complete
aapm emergency resolve

***REMOVED*** 4. System schedules post-emergency review (within 24 hours)
```

***REMOVED******REMOVED******REMOVED*** Emergency Safeguards

Even in emergency mode, these remain enforced:

1. **ACGME Compliance**: Cannot violate work hour rules
2. **Automatic Backup**: Full backup before any change
3. **Audit Trail**: Every action logged with justification
4. **Time Limit**: 4-hour hard cutoff
5. **Post-Review**: Program Director review within 24 hours

***REMOVED******REMOVED******REMOVED*** Emergency De-escalation

Emergency mode automatically ends when:

- User runs `aapm emergency resolve`
- 4-hour timeout expires
- Program Director terminates emergency
- System detects emergency condition resolved

---

***REMOVED******REMOVED*** Mode-Specific Prompt Prefixes

AI agents **MUST** include mode indicators in all responses to clearly communicate their current operational posture.

***REMOVED******REMOVED******REMOVED*** Prefix Format

```
[MODE_NAME] Description of current action...
```

***REMOVED******REMOVED******REMOVED*** Examples by Mode

***REMOVED******REMOVED******REMOVED******REMOVED*** ANALYZE Mode
```
[ANALYZE] Reviewing schedule for ACGME compliance...
[ANALYZE] Searching codebase for scheduling algorithms...
[ANALYZE] Analyzing workload distribution across residents...
[ANALYZE] Found 3 coverage gaps in next week's schedule.
```

***REMOVED******REMOVED******REMOVED******REMOVED*** PLAN Mode
```
[PLAN] Creating architecture proposal in docs/planning/...
[PLAN] Writing task breakdown to .claude/Scratchpad/sprint-plan.md...
[PLAN] Documenting test strategy in docs/planning/test-plan.md...
```

***REMOVED******REMOVED******REMOVED******REMOVED*** EXECUTE Mode
```
[EXECUTE] Implementing swap request feature in backend/app/services/swap.py...
[EXECUTE] Writing tests for ACGME validation in tests/test_acgme.py...
[EXECUTE] Running pytest... All tests passed ✓
[EXECUTE] Creating PR: "feat: Add swap request validation" → origin/main
[EXECUTE] PR created: https://github.com/user/repo/pull/123
[EXECUTE] Waiting for human review before merge...
```

***REMOVED******REMOVED******REMOVED******REMOVED*** MANAGE:EMERGENCY Mode
```
⚠️  [MANAGE:EMERGENCY] EMERGENCY MODE ACTIVE
⚠️  [MANAGE:EMERGENCY] Duration: 4 hours (expires 14:30 UTC)
⚠️  [MANAGE:EMERGENCY] Filling critical coverage gap for hospitalized resident...
⚠️  [MANAGE:EMERGENCY] Creating backup... ✓
⚠️  [MANAGE:EMERGENCY] Executing assignment without approval gate...
⚠️  [MANAGE:EMERGENCY] ACGME validation passed ✓
⚠️  [MANAGE:EMERGENCY] Notifying Program Director of emergency action...
```

***REMOVED******REMOVED******REMOVED*** Mode Transition Alerts

```
[ANALYZE → PLAN] Escalating to PLAN mode to write architecture docs...
[PLAN → ANALYZE] De-escalating to ANALYZE mode (task complete).

[ANALYZE → EXECUTE] Escalating to EXECUTE mode to implement feature...
[EXECUTE → ANALYZE] De-escalating to ANALYZE mode (PR created, awaiting review).

[ANALYZE → MANAGE:EMERGENCY] Escalating to EMERGENCY mode (PD approval verified)...
⚠️  [MANAGE:EMERGENCY] EMERGENCY MODE ACTIVE - 4 hour time limit
[MANAGE:EMERGENCY → ANALYZE] De-escalating to ANALYZE mode (emergency resolved).
```

***REMOVED******REMOVED******REMOVED*** Approval Gate Indicators

When approval is required (PR review, emergency authorization):

```
[EXECUTE] 🔒 PULL REQUEST REVIEW REQUIRED
  PR: ***REMOVED***123 "feat: Add swap validation"
  Target: origin/main
  Status: Awaiting human review
  CI: ✓ Passing

  Cannot merge until approved by human reviewer.

⚠️  [MANAGE:EMERGENCY] 🔒 PROGRAM DIRECTOR APPROVAL REQUIRED
  Operation: Emergency coverage assignment
  Justification: PGY2-01 hospitalized, shift in 3 hours
  Approver: Dr.ProgramDirector

  Cannot proceed without PD authorization.
```

---

***REMOVED******REMOVED*** Safety Guardrails for Medical Data

***REMOVED******REMOVED******REMOVED*** PHI Protection (Protected Health Information)

AI agents working with medical residency data **MUST** follow these PHI safeguards:

***REMOVED******REMOVED******REMOVED******REMOVED*** Never Log or Export

```
❌ NEVER:
  - Log real resident/faculty names
  - Export schedules with identifiable information
  - Include PHI in error messages
  - Commit PHI to git repository
  - Display PHI in prompts or responses (when possible)

✅ ALWAYS:
  - Use anonymized IDs (PGY1-01, FAC-02)
  - Sanitize data before logging
  - Check .gitignore for data files
  - Use role-based identifiers in documentation
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Data Sanitization

```python
***REMOVED*** Good - Anonymized
residents = ["PGY1-01", "PGY2-03", "PGY3-02"]
faculty = ["FAC-PD", "FAC-APD", "FAC-05"]

***REMOVED*** Bad - Real names (never commit this)
residents = ["John Smith", "Jane Doe"]  ***REMOVED*** ❌ PHI violation
```

***REMOVED******REMOVED******REMOVED*** ACGME Compliance Enforcement

All modes must maintain ACGME compliance:

```python
***REMOVED*** These rules are ALWAYS enforced, even in MANAGE:EMERGENCY
ACGME_RULES = {
    "80_hour_rule": "Maximum 80 hours/week, 4-week rolling average",
    "1_in_7_rule": "One 24-hour period off every 7 days",
    "supervision_ratios": {
        "PGY1": "1 faculty per 2 residents",
        "PGY2_3": "1 faculty per 4 residents"
    }
}

***REMOVED*** System will block operations that violate these rules
***REMOVED*** Even in emergency mode with approval gates bypassed
```

***REMOVED******REMOVED******REMOVED*** Audit Trail Requirements

All modes maintain audit logs (level varies by mode):

| Mode | Audit Level | What's Logged |
|------|-------------|---------------|
| ANALYZE | Standard | Read operations, queries, analysis requests |
| PLAN | Standard | Files written to .claude/ and docs/ |
| EXECUTE | Enhanced | Git commits, PR creation, code changes, test runs |
| MANAGE:EMERGENCY | **Maximum** | Every action, justification, approval, timestamps |

***REMOVED******REMOVED******REMOVED*** Security Best Practices

```bash
***REMOVED*** Before any operation, check:
1. Am I handling PHI? → Anonymize before logging
2. Am I modifying production data? → Require approval
3. Am I bypassing safety checks? → Document justification
4. Am I in the right mode for this task? → Escalate/de-escalate as needed
```

---

***REMOVED******REMOVED*** Integration with Existing Infrastructure

***REMOVED******REMOVED******REMOVED*** Files and Components

```
.claude/
├── MODES.md                      ***REMOVED*** This file (simplified framework)
├── OPERATIONAL_MODES.md          ***REMOVED*** Detailed technical specs
├── CONSTITUTION.md               ***REMOVED*** Agent behavioral rules
├── Agents/                       ***REMOVED*** Mode-aware agent definitions
│   ├── AUDITOR.md               ***REMOVED*** Compliance checking (ANALYZE mode)
│   ├── SCHEDULER.md             ***REMOVED*** Schedule generation (EXECUTE/EMERGENCY)
│   └── ORCHESTRATOR.md          ***REMOVED*** Multi-agent coordination
├── Constitutions/               ***REMOVED*** Mode constraint definitions
└── PromptTemplates/             ***REMOVED*** Mode-specific prompts

docs/
├── development/
│   ├── AI_RULES_OF_ENGAGEMENT.md  ***REMOVED*** Git and PR workflow
│   └── DEBUGGING_WORKFLOW.md      ***REMOVED*** Debugging methodology
└── admin-manual/
    └── ai-interface-guide.md      ***REMOVED*** Web vs CLI comparison
```

***REMOVED******REMOVED******REMOVED*** Mode Controller (To Be Implemented)

```python
***REMOVED*** .claude/mode_controller.py
class ModeController:
    """Enforce mode constraints at runtime."""

    MODES = ["ANALYZE", "PLAN", "EXECUTE", "MANAGE:EMERGENCY"]
    DEFAULT_MODE = "ANALYZE"

    def __init__(self):
        self.current_mode = self.detect_default_mode()
        self.mode_stack = [self.current_mode]

    def can_perform(self, operation: str) -> tuple[bool, str]:
        """Check if operation allowed in current mode."""
        constraints = MODE_CONSTRAINTS[self.current_mode]

        if operation in ["edit", "write"] and self.current_mode == "ANALYZE":
            return False, "Write operations not allowed in ANALYZE mode"

        if operation == "git_push_main" and self.current_mode != "MANAGE:EMERGENCY":
            return False, "Cannot push to main outside emergency mode"

        return True, "Operation allowed"

    def escalate(self, target_mode: str, justification: str = None):
        """Escalate to higher-risk mode."""
        if not self.is_valid_transition(self.current_mode, target_mode):
            raise ValueError(f"Invalid transition {self.current_mode} → {target_mode}")

        if target_mode == "MANAGE:EMERGENCY" and not justification:
            raise ValueError("Emergency mode requires justification")

        self.mode_stack.append(target_mode)
        self.current_mode = target_mode
        log_mode_transition(self.current_mode, target_mode, justification)
```

---

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Mode Capabilities Matrix

| Capability | ANALYZE | PLAN | EXECUTE | MANAGE:EMERGENCY |
|-----------|---------|------|---------|------------------|
| Read files | ✅ | ✅ | ✅ | ✅ |
| Search codebase | ✅ | ✅ | ✅ | ✅ |
| Write to .claude/ | ❌* | ✅ | ✅ | ❌ |
| Write to docs/ | ❌ | ✅ | ✅ | ❌ |
| Edit source code | ❌ | ❌ | ✅ | ✅ |
| Run tests | ✅ | ✅ | ✅ | ✅ |
| Git commit | ❌ | ❌ | ✅ | ✅ |
| Create PR | ❌ | ❌ | ✅ | ❌ |
| Merge PR | ❌ | ❌ | ❌** | ❌ |
| Access production DB | Read-only | ❌ | ❌ | Read/Write |
| Bypass approval | N/A | N/A | ❌ | ✅ |

*Can write to `.claude/Scratchpad/` only
**Requires human approval

***REMOVED******REMOVED******REMOVED*** Common Commands

```bash
***REMOVED*** Mode control
aapm --mode=ANALYZE          ***REMOVED*** Read-only (default)
aapm --mode=PLAN             ***REMOVED*** Planning/docs
aapm --mode=EXECUTE          ***REMOVED*** Code changes
aapm mode status             ***REMOVED*** Check current mode

***REMOVED*** Emergency (requires PD approval)
aapm emergency declare --reason="..." --approved-by="PD"
aapm emergency resolve

***REMOVED*** Automatic mode selection
aapm audit                   ***REMOVED*** → ANALYZE mode
aapm plan --write            ***REMOVED*** → PLAN mode
aapm code implement          ***REMOVED*** → EXECUTE mode
```

---

***REMOVED******REMOVED*** Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-26 | Initial creation - 4-mode simplified framework |

---

**See Also:**
- [OPERATIONAL_MODES.md](OPERATIONAL_MODES.md) - Detailed technical specifications
- [AI Rules of Engagement](../docs/development/AI_RULES_OF_ENGAGEMENT.md) - Git workflow and PR process
- [CONSTITUTION.md](CONSTITUTION.md) - Agent behavioral rules and ethics
- [CLAUDE.md](../CLAUDE.md) - Project guidelines and development standards

---

**End of MODES.md**
