# Template Composition Patterns

> **Version:** 1.0
> **Purpose:** Guidelines for composing complex multi-step templates

---

## Pattern 1: Sequential Workflow

For linear multi-step processes:

```
Step 1: [Prerequisite check]
  - Verify condition A
  - Verify condition B

Step 2: [Main action]
  - Action 1
  - Action 2

Step 3: [Validation]
  - Verify result A
  - Verify result B

Step 4: [Reporting]
  - Report status
```

**Used in:** Schedule generation, migration, execution workflows

---

## Pattern 2: Decision Tree

For conditional branches:

```
IF condition_A:
  Execute branch_A_template
ELSE IF condition_B:
  Execute branch_B_template
ELSE:
  Execute default_template
```

**Used in:** Escalation, approval workflows, error handling

---

## Pattern 3: Parallel Workflows

For independent concurrent operations:

```
Task 1: [Operation A]
Task 2: [Operation B]
Task 3: [Operation C]
(All run in parallel)

Sync Point: Gather results
Proceed only if all succeed
```

**Used in:** Multi-agent coordination, distributed checks

---

## Pattern 4: Cascading Checks

For validation hierarchies:

```
Level 1: Quick validation (< 5 seconds)
  - If FAIL → Reject
  - If PASS → Continue

Level 2: Standard validation (< 30 seconds)
  - If FAIL → Report with remediation
  - If PASS → Continue

Level 3: Deep validation (< 5 minutes)
  - If FAIL → Escalate
  - If PASS → Approve
```

**Used in:** Compliance checking, conflict resolution

---

## Pattern 5: Phased Execution

For long-running operations with checkpoints:

```
Phase 1: Preparation (${PREP_TIME}min)
  - Setup
  - Validation
  - Resource allocation

Phase 2: Execution (${EXEC_TIME}min)
  - Main operation
  - Checkpoint
  - Progress reporting

Phase 3: Validation (${VAL_TIME}min)
  - Result verification
  - Compliance check
  - Finalization

Phase 4: Reporting (${REPORT_TIME}min)
  - Status report
  - Metrics collection
  - Archival
```

**Used in:** Schedule generation, major deployments

---

## Pattern 6: Error Recovery

For robust error handling:

```
TRY:
  Execute main_template

CATCH error_type_1:
  Execute recovery_1_template
  Continue or escalate

CATCH error_type_2:
  Execute recovery_2_template
  Continue or escalate

FINALLY:
  Cleanup and reporting
```

**Used in:** All operational templates

---

## Pattern 7: Template Nesting

For reusable sub-templates:

```
Main Template
  ├─ Sub-template A
  │  └─ Sub-sub-template A1
  ├─ Sub-template B
  └─ Sub-template C
```

**Nesting Rules:**
- Max 3 levels deep
- Each level should be independently testable
- Clear input/output contracts

**Used in:** Complex planning, optimization

---

## Composition Best Practices

1. **Keep templates focused** - One responsibility per template
2. **Make boundaries clear** - Define start/end conditions
3. **Use consistent formatting** - Maintain readability
4. **Include timeout protection** - Prevent infinite loops
5. **Validate at each step** - Don't defer validation
6. **Provide escape hatches** - Manual override capability
7. **Document dependencies** - Show template relationships

---

*Last Updated: 2025-12-31*
