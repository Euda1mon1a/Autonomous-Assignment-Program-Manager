# OPERATIONAL MODES SYSTEM
# Personal AI Infrastructure (PAI) - Mode Definitions and Control

> **Version:** 1.0
> **Last Updated:** 2025-12-26
> **Purpose:** Define operational postures for AI agents with varying risk/creativity profiles

---

## Table of Contents

1. [Overview](#overview)
2. [Mode Definitions](#mode-definitions)
3. [Mode Transitions](#mode-transitions)
4. [Mode-Specific Constraints](#mode-specific-constraints)
5. [CLI Integration](#cli-integration)
6. [Mode Indicators](#mode-indicators)
7. [Decision Trees](#decision-trees)
8. [Examples and Use Cases](#examples-and-use-cases)
9. [Emergency Procedures](#emergency-procedures)

---

## Overview

The Operational Modes system provides a structured framework for controlling AI agent behavior across different risk profiles and use cases. Each mode defines a specific posture that balances **safety** (risk mitigation) and **creativity** (exploration freedom).

### Design Principles

1. **Fail-Safe Defaults**: System defaults to SAFE_AUDIT mode (read-only)
2. **Explicit Escalation**: Higher-risk modes require human approval
3. **Automatic De-escalation**: Return to safe mode after operations complete
4. **Complete Audit Trail**: All mode transitions and operations are logged
5. **Time-Limited Authority**: High-risk modes expire automatically

### Risk/Creativity Matrix

```
Creativity ↑
    │
  H │   [EXPERIMENTAL_PLANNING]
    │           │
  M │   [SUPERVISED_EXECUTION]
    │           │
  L │   [SAFE_AUDIT] ──→ [EMERGENCY_OVERRIDE]
    │
    └───────────────────────────────────────→ Risk
        L           M                     H
```

---

## Mode Definitions

### 1. SAFE_AUDIT Mode

**Risk Level:** LOW
**Creativity Level:** LOW
**Default Mode:** YES

#### Purpose
Read-only operations for schedule review, compliance auditing, and what-if analysis. Maximum validation, zero modification risk.

#### Characteristics
- **Database Access:** Read-only
- **Schedule Modifications:** Prohibited
- **Validation Level:** Maximum (all rules enforced)
- **Approval Required:** No
- **Backup Required:** No
- **Rollback Capability:** N/A
- **Max Duration:** Unlimited
- **Audit Trail:** Standard logging

#### Enabled Agents
All agents operate in read-only mode:
- **AUDITOR**: Compliance checks, rule validation
- **ADVISOR**: Schedule analysis, recommendations
- **SCHEDULER**: What-if scenario planning (sandbox only)
- **SWAP_MATCHER**: Compatibility analysis (no execution)

#### Enabled Tools
- Read/query tools only:
  - `list_persons`, `get_person`
  - `list_assignments`, `get_assignment_metrics`
  - `validate_acgme_compliance`
  - `find_coverage_gaps`
  - `analyze_workload_distribution`
  - `simulate_swap` (analysis only, no execution)

#### Prohibited Tools
- All write operations:
  - `create_assignment`, `update_assignment`, `delete_assignment`
  - `execute_swap`, `approve_swap`, `rollback_swap`
  - `create_person`, `update_person`, `delete_person`

#### Use Cases
- Daily schedule review
- ACGME compliance audits
- Coverage gap identification
- Workload analysis
- What-if scenario exploration (sandbox)
- Training and orientation

#### Entry Conditions
- System startup (default)
- After completing SUPERVISED_EXECUTION operations
- After EMERGENCY_OVERRIDE timeout
- Explicit user command: `aapm mode safe-audit`

#### Exit Conditions
- User escalates to SUPERVISED_EXECUTION
- User switches to EXPERIMENTAL_PLANNING
- Emergency declaration triggers EMERGENCY_OVERRIDE

---

### 2. SUPERVISED_EXECUTION Mode

**Risk Level:** MEDIUM
**Creativity Level:** MEDIUM
**Default Mode:** NO

#### Purpose
Execute schedule modifications with human oversight. Pre-execution validation and rollback capability required for all changes.

#### Characteristics
- **Database Access:** Read + Write (with approval)
- **Schedule Modifications:** Allowed (with approval)
- **Validation Level:** High (pre-execution + post-execution checks)
- **Approval Required:** Yes (human-in-the-loop)
- **Backup Required:** Yes (automatic before changes)
- **Rollback Capability:** Mandatory (24-hour window)
- **Max Duration:** 2 hours per session
- **Audit Trail:** Enhanced (before/after snapshots)

#### Enabled Agents
- **SCHEDULER**: Schedule generation and modification
- **SWAP_EXECUTOR**: Execute approved swaps
- **AUDITOR**: Pre/post validation
- **ADVISOR**: Recommendation generation

#### Enabled Tools
- All read tools from SAFE_AUDIT
- Write tools with approval gates:
  - `execute_swap` (requires approval)
  - `create_assignment` (requires approval)
  - `update_assignment` (requires approval)
  - `approve_absence` (requires approval)
  - `assign_coverage` (requires approval)

#### Approval Workflow
```python
# Pre-execution validation
validation_result = await validate_operation(operation, params)
if not validation_result.passes:
    raise ValidationError(validation_result.violations)

# Human approval gate
approval = await request_human_approval(
    operation=operation,
    impact_analysis=validation_result.impact,
    rollback_plan=validation_result.rollback_plan
)

if not approval.granted:
    log_rejection(approval.reason)
    return OperationCancelled()

# Execute with backup
backup_id = await create_backup(affected_tables)
try:
    result = await execute_operation(operation, params)
    await validate_post_execution(result)
    log_success(operation, result, backup_id)
    return result
except Exception as e:
    await rollback_from_backup(backup_id)
    raise OperationFailed(e)
```

#### Use Cases
- Executing resident/faculty swaps
- Adjusting schedules for approved absences
- Filling coverage gaps
- Modifying rotation assignments
- Bulk schedule updates (with approval)

#### Entry Conditions
- User escalates from SAFE_AUDIT: `aapm mode supervised`
- Swap request submitted: `aapm swap request`
- Schedule modification requested: `aapm schedule modify`

#### Exit Conditions
- Operation completes successfully → return to SAFE_AUDIT
- Session timeout (2 hours) → return to SAFE_AUDIT
- User cancels operation → return to SAFE_AUDIT
- Critical error detected → return to SAFE_AUDIT + alert

---

### 3. EXPERIMENTAL_PLANNING Mode

**Risk Level:** LOW
**Creativity Level:** HIGH
**Default Mode:** NO

#### Purpose
Sandbox environment for algorithm testing, research, and unconstrained exploration. No production database access.

#### Characteristics
- **Database Access:** Sandbox only (isolated test DB)
- **Schedule Modifications:** Unrestricted (sandbox only)
- **Validation Level:** Optional (can disable for experiments)
- **Approval Required:** No (sandbox is isolated)
- **Backup Required:** No (test data)
- **Rollback Capability:** Full sandbox reset available
- **Max Duration:** Unlimited
- **Audit Trail:** Experimental log (separate from production)

#### Enabled Agents
All agents with `sandbox=true` flag:
- **SCHEDULER**: Algorithm experimentation
- **OPTIMIZER**: New optimization strategies
- **ADVISOR**: Novel recommendation algorithms
- **AUDITOR**: Custom rule testing

#### Enabled Tools
- All tools against test data:
  - Full CRUD operations (create/read/update/delete)
  - Constraint engine modifications
  - Custom solver configurations
  - Performance benchmarking
  - Stress testing

#### Sandbox Environment
```python
experimental_config = {
    "database": "postgresql://localhost/scheduler_sandbox",
    "redis": "redis://localhost:6380/1",  # Separate Redis DB
    "validation": "optional",  # Can disable ACGME rules
    "constraints": "mutable",  # Can modify constraint engine
    "data_source": "synthetic",  # Generated test data
    "isolation": "complete"  # No production access
}
```

#### Use Cases
- Testing new scheduling algorithms
- Exploring alternative constraint formulations
- Performance benchmarking (load testing)
- What-if scenario modeling
- Research and development
- Algorithm parameter tuning
- Custom optimization strategies

#### Entry Conditions
- User switches to experimental mode: `aapm mode experimental`
- Research task initiated: `aapm experiment --scenario="name"`
- Algorithm testing requested: `aapm test-algorithm --new-strategy`

#### Exit Conditions
- User switches to another mode
- Experiment completes
- User resets sandbox: `aapm sandbox reset`

#### Sandbox Safety Features
1. **Network Isolation**: Cannot access production database
2. **Credential Separation**: Different DB credentials (read-only to prod)
3. **Data Sanitization**: All production data anonymized before copy
4. **Resource Limits**: CPU/memory quotas to prevent runaway processes
5. **Audit Separation**: Experimental logs tagged and isolated

---

### 4. EMERGENCY_OVERRIDE Mode

**Risk Level:** HIGH
**Creativity Level:** LOW
**Default Mode:** NO

#### Purpose
Handle critical situations requiring immediate action without normal approval workflows. Time-limited authority for urgent coverage gaps.

#### Characteristics
- **Database Access:** Full read/write
- **Schedule Modifications:** Unrestricted (within ACGME bounds)
- **Validation Level:** Mandatory (ACGME rules enforced)
- **Approval Required:** No (bypasses normal gates)
- **Backup Required:** Yes (automatic + manual verification)
- **Rollback Capability:** Extended (72-hour window)
- **Max Duration:** 4 hours (hard limit)
- **Audit Trail:** Maximum (every action logged with justification)

#### Enabled Agents
- **SCHEDULER**: Emergency authority enabled
- **AUDITOR**: Continuous monitoring
- **ADVISOR**: Impact analysis

#### Enabled Tools
All tools with emergency authorization:
- Immediate swap execution (no approval wait)
- Direct assignment modifications
- Coverage gap filling
- Absence approval (with notification)
- Emergency contact notifications

#### Emergency Declaration
```python
emergency_declaration = {
    "declared_by": "user_id",
    "declared_at": "2025-12-26T10:30:00Z",
    "justification": "Resident hospitalized, inpatient call uncovered",
    "affected_blocks": ["2025-12-26-PM", "2025-12-27-AM"],
    "expires_at": "2025-12-26T14:30:00Z",  # 4 hours max
    "approval_authority": "Program_Director",
    "audit_level": "maximum"
}
```

#### Guardrails
Despite emergency status, the following remain enforced:
1. **ACGME Compliance**: Cannot violate work hour rules
2. **Backup Requirement**: Automatic backup before any change
3. **Audit Trail**: Complete logging of all actions
4. **Notification**: Program Director notified immediately
5. **Time Limit**: Hard 4-hour cutoff
6. **Post-Emergency Review**: Required within 24 hours

#### Use Cases
- Resident sudden illness/hospitalization
- Urgent military deployment (< 24 hours notice)
- Family emergency requiring immediate leave
- Mass casualty event requiring coverage
- System failure requiring manual intervention

#### Entry Conditions
- User declares emergency: `aapm emergency declare --reason="..."`
- Emergency approval granted by Program Director
- Critical alert from monitoring system

#### Exit Conditions
- Emergency resolved: `aapm emergency resolve`
- Time limit expires (4 hours) → automatic deactivation
- Program Director terminates emergency
- System detects emergency condition resolved

#### Post-Emergency Procedures
1. **Audit Review**: All actions reviewed by Program Director
2. **Documentation**: Incident report filed
3. **Validation**: ACGME compliance verified for all changes
4. **Notification**: Affected residents/faculty notified
5. **Debriefing**: Lessons learned documented

---

## Mode Transitions

### State Diagram

```
┌─────────────┐
│ SAFE_AUDIT  │◄─────── System Startup (DEFAULT)
└──────┬──────┘
       │
       ├──→ escalate ──→ ┌──────────────────────┐
       │                 │ SUPERVISED_EXECUTION │
       │                 └──────────┬───────────┘
       │                            │
       │         ┌──────────────────┘
       │         │ (auto de-escalate after completion)
       │         ↓
       │    ┌─────────────┐
       └──→ │ SAFE_AUDIT  │
            └──────┬──────┘
                   │
                   ├──→ experiment ──→ ┌────────────────────────┐
                   │                   │ EXPERIMENTAL_PLANNING  │
                   │                   └────────────┬───────────┘
                   │                                │
                   │         ┌──────────────────────┘
                   │         │ (manual exit)
                   │         ↓
                   │    ┌─────────────┐
                   └──→ │ SAFE_AUDIT  │
                        └──────┬──────┘
                               │
                               │ (emergency declared)
                               ↓
                        ┌───────────────────┐
                        │ EMERGENCY_OVERRIDE│
                        └──────────┬────────┘
                                   │
                                   │ (timeout or resolve)
                                   ↓
                            ┌─────────────┐
                            │ SAFE_AUDIT  │
                            └─────────────┘
```

### Transition Rules

#### SAFE_AUDIT → SUPERVISED_EXECUTION
- **Trigger**: User requests write operation
- **Approval**: Required (user must confirm escalation)
- **Validation**: Pre-flight checks pass
- **Command**: `aapm mode supervised` or `aapm swap execute`

#### SUPERVISED_EXECUTION → SAFE_AUDIT
- **Trigger**: Operation complete OR timeout OR cancellation
- **Approval**: Automatic (no approval needed to de-escalate)
- **Validation**: Post-execution checks logged
- **Command**: Automatic or `aapm mode safe-audit`

#### SAFE_AUDIT → EXPERIMENTAL_PLANNING
- **Trigger**: User starts experiment
- **Approval**: Not required (sandbox is isolated)
- **Validation**: Sandbox environment verified
- **Command**: `aapm mode experimental` or `aapm experiment start`

#### EXPERIMENTAL_PLANNING → SAFE_AUDIT
- **Trigger**: User exits experiment
- **Approval**: Not required
- **Validation**: None (sandbox is isolated)
- **Command**: `aapm mode safe-audit` or `aapm experiment stop`

#### SAFE_AUDIT → EMERGENCY_OVERRIDE
- **Trigger**: Emergency declared
- **Approval**: Required (Program Director or equivalent)
- **Validation**: Emergency justification reviewed
- **Command**: `aapm emergency declare --reason="..." --approved-by="PD"`

#### EMERGENCY_OVERRIDE → SAFE_AUDIT
- **Trigger**: Emergency resolved OR 4-hour timeout
- **Approval**: Automatic on timeout, manual on resolve
- **Validation**: Post-emergency audit scheduled
- **Command**: `aapm emergency resolve` or automatic timeout

### Transition Validation

Before any mode transition, the system validates:

```python
def validate_mode_transition(current_mode: str, target_mode: str, context: dict) -> bool:
    """Validate mode transition is allowed."""

    # Check if transition is permitted
    if not is_transition_allowed(current_mode, target_mode):
        raise InvalidTransition(f"Cannot transition {current_mode} → {target_mode}")

    # Check approval requirements
    if requires_approval(target_mode) and not context.get("approval_granted"):
        raise ApprovalRequired(f"{target_mode} requires approval")

    # Check preconditions
    if target_mode == "SUPERVISED_EXECUTION":
        if not verify_backup_capability():
            raise PreconditionFailed("Backup system unavailable")

    if target_mode == "EXPERIMENTAL_PLANNING":
        if not verify_sandbox_isolation():
            raise PreconditionFailed("Sandbox not properly isolated")

    if target_mode == "EMERGENCY_OVERRIDE":
        if not context.get("emergency_justification"):
            raise PreconditionFailed("Emergency justification required")
        if not context.get("pd_approval"):
            raise PreconditionFailed("Program Director approval required")

    # Log transition
    log_mode_transition(current_mode, target_mode, context)

    return True
```

---

## Mode-Specific Constraints

### Constraint Matrix

| Feature | SAFE_AUDIT | SUPERVISED | EXPERIMENTAL | EMERGENCY |
|---------|-----------|------------|--------------|-----------|
| **Write Operations** | ❌ | ✅ (approval) | ✅ (sandbox) | ✅ (unrestricted) |
| **Approval Required** | ❌ | ✅ | ❌ | ❌ |
| **Backup Required** | ❌ | ✅ | ❌ | ✅ |
| **Rollback Window** | N/A | 24 hours | N/A | 72 hours |
| **Max Duration** | Unlimited | 2 hours | Unlimited | 4 hours |
| **ACGME Validation** | ✅ | ✅ | Optional | ✅ |
| **Audit Trail** | Standard | Enhanced | Experimental | Maximum |
| **Production DB Access** | Read-only | Read/Write | ❌ | Read/Write |
| **Sandbox Access** | Read-only | ❌ | Read/Write | ❌ |
| **Tool Restrictions** | Read tools only | Write with gates | All tools | All tools |
| **Notification Level** | None | Standard | None | Immediate |
| **Post-Op Review** | None | Standard | None | Mandatory |

### Python Configuration

```python
MODE_CONSTRAINTS = {
    "SAFE_AUDIT": {
        "write_operations": False,
        "approval_required": False,
        "backup_required": False,
        "rollback_window_hours": None,
        "max_duration_hours": None,
        "acgme_validation": "enforced",
        "audit_level": "standard",
        "database_access": "read_only",
        "sandbox_access": "read_only",
        "tool_restrictions": ["write", "modify", "delete", "execute"],
        "notification_level": "none",
        "post_op_review": False,
        "risk_level": "low",
        "creativity_level": "low"
    },

    "SUPERVISED_EXECUTION": {
        "write_operations": True,
        "approval_required": True,
        "backup_required": True,
        "rollback_window_hours": 24,
        "max_duration_hours": 2,
        "acgme_validation": "enforced",
        "audit_level": "enhanced",
        "database_access": "read_write",
        "sandbox_access": "prohibited",
        "tool_restrictions": [],  # No restrictions, but approval gates active
        "notification_level": "standard",
        "post_op_review": True,
        "risk_level": "medium",
        "creativity_level": "medium"
    },

    "EXPERIMENTAL_PLANNING": {
        "write_operations": True,
        "approval_required": False,
        "backup_required": False,
        "rollback_window_hours": None,  # Full sandbox reset available
        "max_duration_hours": None,
        "acgme_validation": "optional",
        "audit_level": "experimental",
        "database_access": "prohibited",  # Production DB
        "sandbox_access": "read_write",
        "tool_restrictions": [],  # All tools allowed in sandbox
        "notification_level": "none",
        "post_op_review": False,
        "risk_level": "low",  # Sandboxed
        "creativity_level": "high"
    },

    "EMERGENCY_OVERRIDE": {
        "write_operations": True,
        "approval_required": False,  # Bypasses normal gates
        "backup_required": True,
        "rollback_window_hours": 72,
        "max_duration_hours": 4,
        "acgme_validation": "enforced",  # Still required!
        "audit_level": "maximum",
        "database_access": "read_write",
        "sandbox_access": "prohibited",
        "tool_restrictions": [],  # No restrictions
        "notification_level": "immediate",
        "post_op_review": True,  # Mandatory
        "risk_level": "high",
        "creativity_level": "low"
    }
}
```

### Runtime Enforcement

```python
class ModeEnforcer:
    """Enforce mode-specific constraints at runtime."""

    def __init__(self, current_mode: str):
        self.mode = current_mode
        self.constraints = MODE_CONSTRAINTS[current_mode]
        self.start_time = datetime.utcnow()

    def check_operation_allowed(self, operation: str) -> tuple[bool, str]:
        """Check if operation is allowed in current mode."""

        # Check write operations
        if operation in ["create", "update", "delete"] and not self.constraints["write_operations"]:
            return False, f"Write operations not allowed in {self.mode}"

        # Check tool restrictions
        if operation in self.constraints["tool_restrictions"]:
            return False, f"{operation} restricted in {self.mode}"

        # Check duration limit
        if self.constraints["max_duration_hours"]:
            elapsed_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
            if elapsed_hours > self.constraints["max_duration_hours"]:
                return False, f"{self.mode} duration limit exceeded ({elapsed_hours:.1f}h)"

        # Check database access
        if operation.startswith("db_") and self.constraints["database_access"] == "prohibited":
            return False, f"Production database access prohibited in {self.mode}"

        return True, "Operation allowed"

    def get_approval_gate(self, operation: str) -> Optional[ApprovalGate]:
        """Get approval gate for operation if required."""
        if not self.constraints["approval_required"]:
            return None

        return ApprovalGate(
            operation=operation,
            mode=self.mode,
            timeout_seconds=300,  # 5 minutes
            approver_role="Program_Director"
        )
```

---

## CLI Integration

### Mode Mapping to Commands

| CLI Command | Mode | Description |
|-------------|------|-------------|
| `aapm audit` | SAFE_AUDIT | Compliance checks and schedule review |
| `aapm analyze` | SAFE_AUDIT | Workload and coverage analysis |
| `aapm whatif` | SAFE_AUDIT | Scenario planning (sandbox) |
| `aapm swap request` | SUPERVISED_EXECUTION | Request and execute swaps |
| `aapm schedule modify` | SUPERVISED_EXECUTION | Modify schedule assignments |
| `aapm assign coverage` | SUPERVISED_EXECUTION | Fill coverage gaps |
| `aapm experiment` | EXPERIMENTAL_PLANNING | Algorithm testing and research |
| `aapm test-algorithm` | EXPERIMENTAL_PLANNING | Benchmark new strategies |
| `aapm emergency declare` | EMERGENCY_OVERRIDE | Handle urgent situations |

### Command Syntax

#### Mode Control Commands

```bash
# Check current mode
aapm mode status

# Explicitly set mode (with approval if needed)
aapm mode safe-audit
aapm mode supervised
aapm mode experimental
aapm mode emergency --reason="..." --approved-by="PD"

# Mode history
aapm mode history --hours=24
```

#### Mode-Aware Commands

```bash
# SAFE_AUDIT commands
aapm audit --date=2025-12-26
aapm analyze workload --period=week
aapm whatif --scenario="resident_absence" --person="PGY2-01"

# SUPERVISED_EXECUTION commands (triggers escalation)
aapm swap request --from="FAC-01" --to="FAC-02" --block="2025-12-26-PM"
aapm schedule modify --assignment=12345 --rotation="clinic"
aapm assign coverage --gap="2025-12-27-AM" --person="FAC-03"

# EXPERIMENTAL_PLANNING commands
aapm experiment start --scenario="algorithm_comparison"
aapm experiment run --test="new_constraint_strategy"
aapm sandbox reset

# EMERGENCY_OVERRIDE commands
aapm emergency declare --reason="Resident hospitalized" --approved-by="PD"
aapm emergency fill-gap --block="2025-12-26-PM" --person="FAC-05"
aapm emergency resolve
```

### Command Behavior by Mode

#### `aapm swap` command

```python
# SAFE_AUDIT mode
$ aapm swap analyze --from="FAC-01" --to="FAC-02" --block="2025-12-26-PM"
[SAFE_AUDIT] Analyzing swap compatibility...
✓ ACGME compliance: PASS
✓ Coverage maintained: PASS
✓ Credential match: PASS
Recommendation: Swap is viable
Note: Use 'aapm swap execute' to perform swap (requires escalation to SUPERVISED mode)

# SUPERVISED_EXECUTION mode
$ aapm swap execute --from="FAC-01" --to="FAC-02" --block="2025-12-26-PM"
[SUPERVISED_EXECUTION] Escalating from SAFE_AUDIT...
Creating backup... ✓
Pre-execution validation... ✓

APPROVAL REQUIRED:
  Operation: Execute swap
  From: FAC-01 (Dr. Smith)
  To: FAC-02 (Dr. Jones)
  Block: 2025-12-26 PM (Inpatient Call)
  Impact: 1 assignment modified, coverage maintained
  Rollback: 24-hour window

Approve? [y/N]: y

Executing swap... ✓
Post-execution validation... ✓
Notifying affected parties... ✓
De-escalating to SAFE_AUDIT... ✓

Swap completed successfully.
```

#### `aapm emergency` command

```bash
$ aapm emergency declare \
    --reason="PGY2-01 hospitalized, inpatient call uncovered 12/26 PM" \
    --approved-by="Dr.ProgramDirector"

[EMERGENCY_OVERRIDE] Emergency mode requested
Validating authorization... ✓
Program Director approval verified... ✓

EMERGENCY DECLARATION ACTIVE
  Duration: 4 hours (expires 2025-12-26 14:30:00 UTC)
  Justification: PGY2-01 hospitalized, inpatient call uncovered 12/26 PM
  Approved by: Dr.ProgramDirector
  Audit level: MAXIMUM

Emergency mode activated. All actions will be logged and reviewed.

# Now in EMERGENCY_OVERRIDE mode - can execute without approval gates
$ aapm emergency fill-gap --block="2025-12-26-PM" --person="PGY3-02"
[EMERGENCY_OVERRIDE] Filling coverage gap...
Creating backup... ✓
Executing assignment... ✓
Validating ACGME compliance... ✓
Notifying Program Director... ✓

Coverage gap filled. Emergency action logged.

$ aapm emergency resolve
[EMERGENCY_OVERRIDE] Resolving emergency...
Audit summary:
  - 1 assignment created
  - 0 ACGME violations
  - Total duration: 47 minutes

Post-emergency review scheduled for 2025-12-27 10:00:00 UTC
De-escalating to SAFE_AUDIT... ✓

Emergency resolved.
```

---

## Mode Indicators

### How Agents Communicate Current Mode

#### 1. Prompt Prefix

All agent responses include mode indicator in brackets:

```
[SAFE_AUDIT] Analyzing schedule for ACGME compliance...
[SUPERVISED_EXECUTION] Requesting approval for swap execution...
[EXPERIMENTAL_PLANNING] Testing new optimization strategy in sandbox...
[EMERGENCY_OVERRIDE] ⚠️  EMERGENCY MODE ACTIVE - Filling critical coverage gap...
```

#### 2. Tool Availability Changes

Agents display available tools based on current mode:

```python
# SAFE_AUDIT mode
Available commands:
  ✓ audit, analyze, whatif, list, get, validate
  ✗ execute, modify, delete, create, approve

# SUPERVISED_EXECUTION mode
Available commands:
  ✓ ALL (write operations require approval)

# EXPERIMENTAL_PLANNING mode
Available commands:
  ✓ ALL (sandbox only)
  ✗ Production database access

# EMERGENCY_OVERRIDE mode
Available commands:
  ✓ ALL (approval gates bypassed, max audit)
```

#### 3. CLI Status Display

```bash
$ aapm status

OPERATIONAL STATUS
┌──────────────────────────────────────────────────┐
│ Mode: SUPERVISED_EXECUTION                        │
│ Started: 2025-12-26 10:15:23 UTC                 │
│ Elapsed: 23 minutes                              │
│ Max Duration: 2 hours                            │
│ Auto-Deescalate: After current operation         │
└──────────────────────────────────────────────────┘

CONSTRAINTS
  Write Operations: ✓ Allowed (with approval)
  Approval Required: ✓ Yes
  Backup Required: ✓ Yes
  Rollback Window: 24 hours
  ACGME Validation: ✓ Enforced
  Audit Level: Enhanced

ACTIVE OPERATIONS
  1. Swap execution pending approval (2 minutes ago)
```

#### 4. Approval Gate Activation

When approval is required, agents display detailed gate information:

```
[SUPERVISED_EXECUTION] 🔒 APPROVAL GATE ACTIVATED

Operation: execute_swap
Details:
  - Swap Type: One-to-one
  - Requestor: FAC-01 (Dr. Smith)
  - Partner: FAC-02 (Dr. Jones)
  - Block: 2025-12-26 PM (Inpatient Call)

Pre-execution Validation:
  ✓ ACGME compliance maintained
  ✓ Coverage requirements met
  ✓ Credentials valid for both faculty
  ✓ No conflicting assignments

Impact Analysis:
  - Assignments modified: 2
  - Residents affected: 0
  - Faculty affected: 2
  - Coverage gaps created: 0

Rollback Plan:
  - Backup ID: backup_20251226_101523
  - Rollback window: 24 hours
  - Estimated rollback time: < 5 minutes

Risk Level: MEDIUM
Recommendation: APPROVE

Approve? [y/N]:
```

#### 5. Mode Transition Alerts

```
[SAFE_AUDIT → SUPERVISED_EXECUTION]
Escalating to SUPERVISED_EXECUTION mode:
  Reason: User requested write operation
  Approval: Required
  Duration: 2 hours max
  Auto-deescalate: Yes

Preparing SUPERVISED mode environment...
  ✓ Backup system verified
  ✓ Rollback capability confirmed
  ✓ Audit trail initialized
  ✓ Approval gates activated

Mode transition complete.
```

#### 6. Timeout Warnings

```
[SUPERVISED_EXECUTION] ⏰ SESSION TIMEOUT WARNING
Time remaining: 15 minutes
Auto-deescalate to SAFE_AUDIT at: 2025-12-26 12:15:23 UTC

To extend session, run: aapm mode extend --hours=2
```

#### 7. Emergency Mode Banner

```
╔══════════════════════════════════════════════════════════╗
║  ⚠️  EMERGENCY OVERRIDE MODE ACTIVE                      ║
║  Duration: 4 hours (expires 14:30:00 UTC)               ║
║  Approval gates: BYPASSED                               ║
║  Audit level: MAXIMUM                                   ║
║  All actions logged for post-emergency review           ║
╚══════════════════════════════════════════════════════════╝

[EMERGENCY_OVERRIDE] Ready for emergency operations.
```

---

## Decision Trees

### When to Use Each Mode

#### Decision Tree 1: Read vs Write Operations

```
START: What are you trying to do?
│
├─ Just reviewing/analyzing?
│  └─> USE: SAFE_AUDIT
│      Examples: Check ACGME compliance, analyze workload,
│                find coverage gaps, review schedules
│
└─ Need to modify schedule?
   │
   ├─ Is this production data?
   │  │
   │  ├─ YES: Is this an emergency?
   │  │  │
   │  │  ├─ YES: Is there < 24 hours to respond?
   │  │  │  │
   │  │  │  ├─ YES: Do you have PD approval?
   │  │  │  │  │
   │  │  │  │  ├─ YES → USE: EMERGENCY_OVERRIDE
   │  │  │  │  │   Examples: Resident hospitalized, urgent deployment,
   │  │  │  │  │             mass casualty event, critical coverage gap
   │  │  │  │  │
   │  │  │  │  └─ NO → GET APPROVAL FIRST, then EMERGENCY_OVERRIDE
   │  │  │  │
   │  │  │  └─ NO → USE: SUPERVISED_EXECUTION
   │  │  │      Examples: Planned swap, scheduled absence,
   │  │  │                routine schedule adjustment
   │  │  │
   │  │  └─ NO → USE: SUPERVISED_EXECUTION
   │  │      Examples: Swap requests, coverage assignments,
   │  │                rotation modifications, absence approvals
   │  │
   │  └─ NO (sandbox/test data) → USE: EXPERIMENTAL_PLANNING
   │      Examples: Algorithm testing, performance benchmarking,
   │                what-if scenarios, research, optimization tuning
   │
   └─ Not sure? → START WITH: SAFE_AUDIT
       Analyze first, then escalate if modifications needed
```

#### Decision Tree 2: Risk Assessment

```
START: How risky is this operation?
│
├─ No modifications? (Read-only)
│  └─> RISK: LOW → USE: SAFE_AUDIT
│
├─ Sandbox only? (No production impact)
│  └─> RISK: LOW → USE: EXPERIMENTAL_PLANNING
│
├─ Production modifications with approval?
│  │
│  ├─ Single assignment change?
│  │  └─> RISK: MEDIUM → USE: SUPERVISED_EXECUTION
│  │
│  ├─ Multiple related changes?
│  │  └─> RISK: MEDIUM-HIGH → USE: SUPERVISED_EXECUTION
│  │      (Consider breaking into smaller operations)
│  │
│  └─ Bulk schedule update?
│      └─> RISK: HIGH → USE: SUPERVISED_EXECUTION
│          (Require extra review before approval)
│
└─ Emergency without approval?
   └─> RISK: HIGH → USE: EMERGENCY_OVERRIDE
       (Only if justified and PD approved)
```

#### Decision Tree 3: Time Sensitivity

```
START: How urgent is this?
│
├─ No time pressure (can wait days/weeks)
│  └─> USE: SAFE_AUDIT → plan → SUPERVISED_EXECUTION
│      Approach: Analyze thoroughly, prepare plan, execute when approved
│
├─ Moderate urgency (hours to days)
│  └─> USE: SUPERVISED_EXECUTION
│      Approach: Request approval, wait for review, execute
│
├─ High urgency (minutes to hours)
│  │
│  ├─ Can you wait for approval? (even 5-10 minutes?)
│  │  │
│  │  ├─ YES → USE: SUPERVISED_EXECUTION (fast-track approval)
│  │  │
│  │  └─ NO → Is PD available for emergency declaration?
│  │     │
│  │     ├─ YES → USE: EMERGENCY_OVERRIDE
│  │     │
│  │     └─ NO → ESCALATE to senior leadership
│  │         (Cannot proceed without authorization)
│  │
│  └─ Is this actually an emergency?
│      ├─ Patient safety at risk? → YES: EMERGENCY_OVERRIDE
│      ├─ Critical coverage gap? → YES: EMERGENCY_OVERRIDE
│      ├─ ACGME violation imminent? → YES: EMERGENCY_OVERRIDE
│      └─ Just inconvenient? → NO: Use SUPERVISED_EXECUTION
```

#### Decision Tree 4: Creativity vs Control

```
START: What balance of creativity and control do you need?
│
├─ Maximum control, minimum risk
│  └─> USE: SAFE_AUDIT
│      When: Compliance audits, official reporting, training
│
├─ Balanced approach
│  └─> USE: SUPERVISED_EXECUTION
│      When: Production operations, standard workflows
│
├─ Maximum creativity, exploration encouraged
│  └─> USE: EXPERIMENTAL_PLANNING
│      When: Research, algorithm development, testing new ideas
│
└─ Need speed over process
   └─> USE: EMERGENCY_OVERRIDE
       When: True emergencies only (rare)
```

---

## Examples and Use Cases

### Example 1: Routine Swap Request

**Scenario:** Dr. Smith (FAC-01) wants to swap their Friday PM clinic with Dr. Jones (FAC-02).

**Mode Progression:**
1. **SAFE_AUDIT** - Analyze compatibility
2. **SUPERVISED_EXECUTION** - Execute swap with approval
3. **SAFE_AUDIT** - Return to default after completion

**Commands:**
```bash
# Step 1: Analyze swap in SAFE_AUDIT mode (default)
$ aapm swap analyze --from="FAC-01" --to="FAC-02" --block="2025-12-29-PM"
[SAFE_AUDIT] Analyzing swap compatibility...
✓ ACGME compliance: PASS
✓ Coverage maintained: PASS
✓ Credential match: PASS (both credentialed for clinic)
✓ Work hour limits: PASS (no violations)
Recommendation: Swap is viable

# Step 2: Execute swap (auto-escalates to SUPERVISED)
$ aapm swap execute --from="FAC-01" --to="FAC-02" --block="2025-12-29-PM"
[SAFE_AUDIT → SUPERVISED_EXECUTION] Escalating...
[SUPERVISED_EXECUTION] Creating backup... ✓
[SUPERVISED_EXECUTION] 🔒 APPROVAL GATE ACTIVATED
  Operation: execute_swap
  Impact: 2 assignments modified
  Rollback: 24-hour window
Approve? [y/N]: y

Executing swap... ✓
[SUPERVISED_EXECUTION → SAFE_AUDIT] De-escalating...
Swap completed successfully.
```

---

### Example 2: Emergency Coverage Gap

**Scenario:** PGY2 resident hospitalized at 0800, inpatient call shift starts at 1800 (10 hours to respond).

**Mode Progression:**
1. **EMERGENCY_OVERRIDE** - Immediate coverage assignment
2. **SAFE_AUDIT** - Return after emergency resolved

**Commands:**
```bash
# Step 1: Declare emergency (requires PD approval)
$ aapm emergency declare \
    --reason="PGY2-01 hospitalized, inpatient call 12/26 PM uncovered" \
    --approved-by="Dr.ProgramDirector"

[EMERGENCY_OVERRIDE] Emergency mode ACTIVE (4 hours max)
⚠️  All actions logged for post-emergency review

# Step 2: Find available coverage
$ aapm emergency find-coverage --block="2025-12-26-PM" --rotation="inpatient_call"
[EMERGENCY_OVERRIDE] Searching for available faculty/residents...
Available:
  1. PGY3-02 (credentialed, work hours OK, no conflicts)
  2. FAC-05 (credentialed, available)
Recommendation: PGY3-02 (resident coverage preferred)

# Step 3: Assign coverage (no approval gate)
$ aapm emergency assign --block="2025-12-26-PM" --person="PGY3-02"
[EMERGENCY_OVERRIDE] Creating backup... ✓
[EMERGENCY_OVERRIDE] Executing assignment... ✓
[EMERGENCY_OVERRIDE] Validating ACGME compliance... ✓
[EMERGENCY_OVERRIDE] Notifying PGY3-02 and PD... ✓
Coverage assigned. Emergency action logged.

# Step 4: Resolve emergency
$ aapm emergency resolve
[EMERGENCY_OVERRIDE] Emergency resolved after 47 minutes.
Post-emergency review scheduled for 2025-12-27 10:00:00 UTC.
[EMERGENCY_OVERRIDE → SAFE_AUDIT] De-escalating...
```

---

### Example 3: Algorithm Experimentation

**Scenario:** Testing a new constraint-based scheduling algorithm.

**Mode Progression:**
1. **EXPERIMENTAL_PLANNING** - Full sandbox access
2. **SAFE_AUDIT** - Exit experiment

**Commands:**
```bash
# Step 1: Switch to experimental mode
$ aapm mode experimental
[SAFE_AUDIT → EXPERIMENTAL_PLANNING] Switching to sandbox...
Verifying sandbox isolation... ✓
Loading synthetic test data... ✓
[EXPERIMENTAL_PLANNING] Ready for experimentation.

# Step 2: Run experiments
$ aapm experiment run --test="new_constraint_algorithm" --iterations=100
[EXPERIMENTAL_PLANNING] Running experiment...
Testing algorithm variations:
  - Baseline: 23.4s avg, 94% compliance
  - Variant A: 18.7s avg, 96% compliance ✓ IMPROVEMENT
  - Variant B: 31.2s avg, 92% compliance
  - Variant C: 15.3s avg, 98% compliance ✓ BEST

Recommendation: Use Variant C parameters
Results saved to: experiments/2025-12-26_constraint_test.json

# Step 3: Benchmark performance
$ aapm experiment benchmark --algorithm="variant_c" --load="high"
[EXPERIMENTAL_PLANNING] Running load test...
Simulating 1000 concurrent schedule requests...
  - P50 latency: 15.3s
  - P95 latency: 22.1s
  - P99 latency: 28.7s
  - Success rate: 100%
Results: PASS (meets SLA targets)

# Step 4: Exit experimental mode
$ aapm mode safe-audit
[EXPERIMENTAL_PLANNING → SAFE_AUDIT] Exiting sandbox...
Experimental logs saved to: logs/experimental/2025-12-26/
Sandbox data retained (use 'aapm sandbox reset' to clear)
```

---

### Example 4: ACGME Compliance Audit

**Scenario:** Monthly ACGME compliance review for GME office.

**Mode:** SAFE_AUDIT (no escalation needed)

**Commands:**
```bash
# Step 1: Run comprehensive audit
$ aapm audit --period="2025-12" --report-level="detailed"
[SAFE_AUDIT] Running ACGME compliance audit for December 2025...

80-HOUR RULE ANALYSIS:
  Total residents: 12
  Violations: 0
  Close calls (>75 hours): 2
    - PGY2-03: 76.5 hours (week of 12/15)
    - PGY3-01: 78.2 hours (week of 12/08)

1-IN-7 RULE ANALYSIS:
  Violations: 0
  Average days off per resident: 4.2 days/month

SUPERVISION RATIOS:
  PGY-1 coverage: 1:1.8 avg (target <1:2) ✓
  PGY-2/3 coverage: 1:3.6 avg (target <1:4) ✓

OVERALL COMPLIANCE: 100% ✓

# Step 2: Generate detailed report
$ aapm audit export --format="pdf" --output="acgme_report_2025-12.pdf"
[SAFE_AUDIT] Generating report...
Report saved: /home/user/reports/acgme_report_2025-12.pdf

# Step 3: What-if analysis for next month
$ aapm whatif --scenario="resident_deployment" --person="PGY3-02" --duration="30days"
[SAFE_AUDIT] Simulating scenario in sandbox...
Impact Analysis:
  - Coverage gaps created: 14 blocks (7 days)
  - Remaining residents: 11
  - Average hours per week: +6.4 hours (CONCERN: may approach 80-hour limit)
  - Supervision ratios: Maintained ✓

Recommendation: CAUTION - Request deployment delay or hire temp coverage
```

---

### Example 5: Supervised Bulk Schedule Update

**Scenario:** Updating all residents' clinic days after curriculum change.

**Mode:** SUPERVISED_EXECUTION (requires approval for bulk changes)

**Commands:**
```bash
# Step 1: Preview changes in SAFE_AUDIT
$ aapm schedule preview-bulk-update --rotation="clinic" --day="Thursday"
[SAFE_AUDIT] Previewing bulk update...
Affected assignments: 48
Affected residents: 12
Date range: 2025-01-02 to 2025-03-31

Changes:
  - Move all clinic days from Wednesday to Thursday
  - Affected blocks: 48 (24 weeks × 2 residents on clinic per week)
  - No conflicts detected
  - ACGME compliance maintained

# Step 2: Execute bulk update
$ aapm schedule execute-bulk-update --rotation="clinic" --day="Thursday"
[SAFE_AUDIT → SUPERVISED_EXECUTION] Escalating...
[SUPERVISED_EXECUTION] Creating backup... ✓
[SUPERVISED_EXECUTION] 🔒 APPROVAL GATE ACTIVATED
  Operation: bulk_schedule_update
  Affected assignments: 48
  Affected residents: 12
  Risk level: HIGH (bulk operation)
  Rollback: 24-hour window
  Validation: All pre-checks passed

⚠️  WARNING: This is a bulk operation affecting 48 assignments.
    Consider breaking into smaller batches if concerned.

Approve? [y/N]: y

Executing bulk update...
  [░░░░░░░░░░░░░░░░░░░░] 0/48
  [████████░░░░░░░░░░░░] 20/48
  [████████████████░░░░] 40/48
  [████████████████████] 48/48 ✓

Post-execution validation... ✓
Notifying 12 affected residents... ✓
[SUPERVISED_EXECUTION → SAFE_AUDIT] De-escalating...

Bulk update completed successfully.
48 assignments updated, 0 errors.
```

---

## Emergency Procedures

### Emergency Declaration Checklist

Before declaring emergency mode, verify ALL of the following:

- [ ] **True Emergency**: Patient safety, critical coverage, or ACGME violation imminent
- [ ] **Time-Critical**: < 24 hours to respond, cannot wait for normal approval
- [ ] **Authorization**: Program Director (or equivalent) available and informed
- [ ] **Justification**: Clear, documented reason for emergency status
- [ ] **Backup System**: Verified operational (automatic backup before changes)
- [ ] **Communication**: Affected parties will be notified immediately
- [ ] **Post-Review**: Understanding that all actions will be audited

### Emergency Scenarios (When to Use EMERGENCY_OVERRIDE)

#### ✅ **Valid Emergency Scenarios**

1. **Resident Sudden Illness/Hospitalization**
   - Timeline: < 4 hours to cover shift
   - Impact: Critical coverage gap (inpatient call, ER, ICU)
   - Action: Immediate coverage assignment

2. **Urgent Military Deployment**
   - Timeline: < 24 hours notice
   - Impact: Multiple shifts uncovered
   - Action: Rapid schedule reorganization

3. **Family Emergency (Death, Critical Illness)**
   - Timeline: Immediate leave required
   - Impact: Same-day coverage gap
   - Action: Emergency coverage assignment

4. **Mass Casualty Event**
   - Timeline: Immediate response needed
   - Impact: All-hands-on-deck activation
   - Action: Suspend normal schedule, emergency assignments

5. **System Failure During Critical Period**
   - Timeline: Normal approval process unavailable
   - Impact: Schedule cannot be accessed/modified
   - Action: Manual intervention required

#### ❌ **Invalid Emergency Scenarios (Use SUPERVISED Instead)**

1. **Planned Vacation** - Use normal approval process (days/weeks notice)
2. **Conference Attendance** - Schedule in advance (weeks notice)
3. **Preference Changes** - Not urgent (flexible timeline)
4. **Administrative Convenience** - Never justifies emergency mode
5. **Missed Deadline** - Poor planning ≠ emergency

### Emergency Mode Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ EMERGENCY DETECTION                                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Identify critical situation                             │
│ 2. Assess timeline (< 24 hours?)                           │
│ 3. Verify no alternatives                                  │
│ 4. Document justification                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ AUTHORIZATION                                               │
├─────────────────────────────────────────────────────────────┤
│ 1. Contact Program Director                                │
│ 2. Explain situation and urgency                           │
│ 3. Obtain verbal/written approval                          │
│ 4. Document approval in system                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ EMERGENCY DECLARATION                                       │
├─────────────────────────────────────────────────────────────┤
│ $ aapm emergency declare \                                  │
│     --reason="[justification]" \                            │
│     --approved-by="[PD name]"                               │
│                                                             │
│ System Response:                                            │
│ - Verify backup system operational                         │
│ - Activate emergency mode (4-hour limit)                   │
│ - Initialize maximum audit trail                           │
│ - Notify PD and affected parties                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ EMERGENCY OPERATIONS                                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Execute necessary changes (no approval gates)           │
│ 2. Maintain ACGME compliance (still enforced!)             │
│ 3. Document all actions and decisions                      │
│ 4. Monitor time remaining (max 4 hours)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ EMERGENCY RESOLUTION                                        │
├─────────────────────────────────────────────────────────────┤
│ $ aapm emergency resolve                                    │
│                                                             │
│ System Response:                                            │
│ - Generate audit summary                                   │
│ - Schedule post-emergency review (within 24 hours)         │
│ - De-escalate to SAFE_AUDIT mode                           │
│ - Archive emergency logs                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ POST-EMERGENCY REVIEW                                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Program Director reviews all actions                    │
│ 2. Verify ACGME compliance maintained                      │
│ 3. Document lessons learned                                │
│ 4. Update emergency procedures if needed                   │
│ 5. Close incident report                                   │
└─────────────────────────────────────────────────────────────┘
```

### Emergency Mode Safeguards

Even in emergency mode, the following safeguards remain active:

1. **ACGME Compliance Enforced**
   - Cannot violate 80-hour rule
   - Cannot violate 1-in-7 rule
   - Must maintain supervision ratios
   - System will block non-compliant changes

2. **Automatic Backup**
   - Full backup created before any modification
   - 72-hour rollback window (extended from normal 24h)
   - Backup verified before proceeding

3. **Maximum Audit Trail**
   - Every action logged with timestamp
   - User identity recorded
   - Justification captured
   - Before/after snapshots saved

4. **Time Limit Enforced**
   - Hard 4-hour maximum
   - Automatic de-escalation on timeout
   - Warning at 15 minutes remaining

5. **Mandatory Review**
   - Post-emergency review scheduled automatically
   - Program Director notification
   - All actions reviewed within 24 hours

### Emergency Mode Commands Reference

```bash
# Declare emergency
aapm emergency declare \
  --reason="Detailed justification" \
  --approved-by="Program Director name or ID"

# Check emergency status
aapm emergency status

# Find coverage options
aapm emergency find-coverage --block="YYYY-MM-DD-PERIOD"

# Assign coverage (no approval gate)
aapm emergency assign --block="YYYY-MM-DD-PERIOD" --person="ID"

# Execute swap (no approval gate)
aapm emergency swap --from="ID1" --to="ID2" --block="YYYY-MM-DD-PERIOD"

# Extend emergency duration (requires re-approval, max 4 hours total)
aapm emergency extend --hours=2 --approved-by="PD"

# Resolve emergency
aapm emergency resolve

# View emergency audit log
aapm emergency audit

# Generate emergency incident report
aapm emergency report --output="incident_report.pdf"
```

---

## Implementation Notes

### System Architecture Integration

The operational modes system integrates with existing PAI components:

```
┌─────────────────────────────────────────────────────────────┐
│ CLI (aapm)                                                  │
│ - Mode detection                                            │
│ - Command routing                                           │
│ - User prompts                                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Mode Controller (new)                                       │
│ - Mode state management                                     │
│ - Transition validation                                     │
│ - Constraint enforcement                                    │
│ - Approval gate coordination                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
            ┌───────────┼───────────┐
            ↓           ↓           ↓
    ┌───────────┐ ┌─────────┐ ┌──────────┐
    │ Agents    │ │ Tools   │ │ MCP      │
    │ (.claude/ │ │ (MCP    │ │ Server   │
    │  Agents/) │ │  tools) │ │          │
    └───────────┘ └─────────┘ └──────────┘
```

### File Locations

```
.claude/
├── OPERATIONAL_MODES.md          # This file
├── mode_controller.py            # Mode state management (to be created)
├── Agents/
│   ├── AUDITOR.md               # Includes mode-aware behavior
│   ├── SCHEDULER.md             # Includes mode-aware behavior
│   └── ...
└── Constitutions/
    └── mode_constraints.yaml    # Mode constraint definitions (to be created)
```

### Configuration File Example

`.claude/Constitutions/mode_constraints.yaml`:
```yaml
modes:
  SAFE_AUDIT:
    risk_level: low
    creativity_level: low
    write_operations: false
    approval_required: false
    backup_required: false
    rollback_window_hours: null
    max_duration_hours: null
    acgme_validation: enforced
    audit_level: standard
    database_access: read_only
    sandbox_access: read_only
    tool_restrictions:
      - write
      - modify
      - delete
      - execute
    notification_level: none
    post_op_review: false

  SUPERVISED_EXECUTION:
    risk_level: medium
    creativity_level: medium
    write_operations: true
    approval_required: true
    backup_required: true
    rollback_window_hours: 24
    max_duration_hours: 2
    acgme_validation: enforced
    audit_level: enhanced
    database_access: read_write
    sandbox_access: prohibited
    tool_restrictions: []
    notification_level: standard
    post_op_review: true

  # ... (other modes)

transitions:
  allowed:
    - from: SAFE_AUDIT
      to: SUPERVISED_EXECUTION
      approval_required: true
    - from: SUPERVISED_EXECUTION
      to: SAFE_AUDIT
      approval_required: false
    - from: SAFE_AUDIT
      to: EXPERIMENTAL_PLANNING
      approval_required: false
    # ... (other transitions)

  prohibited:
    - from: EXPERIMENTAL_PLANNING
      to: EMERGENCY_OVERRIDE
      reason: "Cannot escalate from sandbox to production emergency"
    - from: SUPERVISED_EXECUTION
      to: EMERGENCY_OVERRIDE
      reason: "Must return to SAFE_AUDIT before emergency declaration"
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-26 | Initial creation of operational modes system |

---

**End of OPERATIONAL_MODES.md**
