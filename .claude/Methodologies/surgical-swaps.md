# Surgical Swaps Methodology

**Purpose:** Execute minimal-impact schedule changes that preserve system stability

---

## When to Use This Methodology

Apply when:
- Processing swap requests
- Making manual schedule adjustments
- Correcting violations
- Rebalancing workload
- Accommodating absences

---

## Core Philosophy

> "Change as little as necessary, as much as required."

### Surgical vs Brute Force

| Approach | Surgical | Brute Force |
|----------|----------|-------------|
| **Changes** | 1-3 assignments | Entire schedule regeneration |
| **Risk** | Low | High |
| **Speed** | Seconds | Minutes to hours |
| **Validation** | Simple | Complex |
| **Reversibility** | Easy (rollback) | Hard (requires backup) |

**Prefer surgical changes for:**
- Individual swap requests
- Single violation corrections
- Minor workload adjustments

**Use brute force only when:**
- Multiple interconnected violations
- Major constraint changes
- Schedule is fundamentally broken

---

## Minimal Change Principle

### Definition

**The smallest set of modifications that achieves the goal while maintaining all constraints.**

### Measurement

```python
def calculate_change_impact(original, modified):
    """
    Quantify the magnitude of a schedule change.

    Metrics:
    - Assignments modified (count)
    - People affected (count)
    - Dates affected (count)
    - Constraint deltas (changes in violation counts)
    - Ripple effects (secondary changes required)
    """
    return {
        "assignments_modified": count_diff(original.assignments, modified.assignments),
        "people_affected": len(set(a.person for a in get_changed_assignments())),
        "dates_affected": len(set(a.date for a in get_changed_assignments())),
        "constraint_delta": {
            "acgme_80_hour": modified.violations["80h"] - original.violations["80h"],
            "fairness_gini": modified.gini - original.gini,
            # ... other constraints
        },
        "ripple_effects": count_secondary_changes(modified)
    }
```

**Goal:** Minimize `assignments_modified` while achieving objective

### Example: One-to-One Swap

**Objective:** Accommodate Dr. Smith's request to swap clinic on Thursday

**Option A: Direct Swap (Surgical)**
```python
# Change exactly 2 assignments
change_assignment("ASG-001", from_person="Smith", to_person="Jones")
change_assignment("ASG-002", from_person="Jones", to_person="Smith")

impact = {
    "assignments_modified": 2,
    "people_affected": 2,
    "ripple_effects": 0
}
```

**Option B: Regenerate Week (Brute Force)**
```python
# Regenerate all assignments for the week
regenerate_schedule(start="2026-03-10", end="2026-03-16")

impact = {
    "assignments_modified": 56,  # 28 assignments × 2 sessions
    "people_affected": 15,
    "ripple_effects": unknown
}
```

**Choose A:** Same outcome, 28× fewer changes

---

## Impact Assessment Framework

### Pre-Change Analysis

Before making any change, assess:

#### 1. Direct Impact

**Question:** What assignments will be modified?

```python
def assess_direct_impact(proposed_change):
    """
    Identify assignments that will be changed.
    """
    return {
        "primary_changes": [
            {"assignment": "ASG-001", "field": "person", "old": "Smith", "new": "Jones"},
            {"assignment": "ASG-002", "field": "person", "old": "Jones", "new": "Smith"}
        ],
        "count": 2
    }
```

#### 2. Constraint Impact

**Question:** Which constraints are affected?

```python
def assess_constraint_impact(proposed_change):
    """
    Determine which constraints need revalidation.
    """
    affected_constraints = []

    # Check which constraints involve changed assignments
    for constraint in all_constraints:
        if constraint.involves(proposed_change.assignments):
            before = constraint.evaluate(current_schedule)
            after = constraint.evaluate(schedule_with_change)

            affected_constraints.append({
                "constraint": constraint.name,
                "before_violations": before.violations,
                "after_violations": after.violations,
                "delta": after.violations - before.violations,
                "improves": after.violations < before.violations
            })

    return affected_constraints
```

#### 3. Ripple Effects

**Question:** What secondary changes are triggered?

```python
def assess_ripple_effects(proposed_change):
    """
    Identify cascading changes required to maintain constraints.

    Example:
    - Swap changes supervision ratio
    - Requires adding/removing another person
    - That person's workload changes
    - May affect fairness constraint
    """
    ripples = []

    # Check supervision ratio
    for affected_session in proposed_change.affected_sessions:
        current_ratio = calculate_supervision_ratio(affected_session)
        new_ratio = calculate_supervision_ratio(affected_session, with_change=proposed_change)

        if new_ratio.violates_requirement:
            ripples.append({
                "type": "supervision_adjustment",
                "session": affected_session,
                "action": "Add 1 faculty" if new_ratio < required else "Remove 1 faculty",
                "additional_changes": 1
            })

    # Check workload balance
    for person in proposed_change.affected_people:
        new_utilization = calculate_utilization(person, with_change=proposed_change)

        if new_utilization > 0.80:
            ripples.append({
                "type": "utilization_violation",
                "person": person,
                "utilization": new_utilization,
                "action": "Reduce assignments by 1-2",
                "additional_changes": 2
            })

    return ripples
```

#### 4. Reversibility

**Question:** Can this change be undone easily?

```python
def assess_reversibility(proposed_change):
    """
    Determine difficulty of rolling back the change.
    """
    if proposed_change.type == "one_to_one_swap":
        return {
            "reversible": True,
            "method": "Re-swap same assignments",
            "complexity": "trivial",
            "time": "< 1 minute"
        }

    elif proposed_change.type == "chain_swap":
        return {
            "reversible": True,
            "method": "Reverse entire chain",
            "complexity": "moderate",
            "time": "5 minutes",
            "requires_tracking": True
        }

    elif proposed_change.type == "regeneration":
        return {
            "reversible": True,
            "method": "Restore from backup",
            "complexity": "high",
            "time": "10-30 minutes",
            "requires_backup": True
        }
```

### Impact Scoring

```python
def calculate_impact_score(assessment):
    """
    Combine all factors into single risk score.

    Lower is better (less impact).
    """
    score = 0

    # Direct changes
    score += assessment.direct_impact.count * 1.0

    # Constraint violations introduced
    score += sum(c.delta for c in assessment.constraint_impact if c.delta > 0) * 10.0

    # Ripple effects
    score += len(assessment.ripple_effects) * 5.0

    # Reversibility penalty
    if not assessment.reversibility.reversible:
        score += 50.0
    elif assessment.reversibility.complexity == "high":
        score += 20.0

    return score
```

**Decision Rule:**
- Score < 10: Safe, proceed
- Score 10-50: Review carefully, get approval if >30
- Score > 50: Reconsider approach, may be too risky

---

## Ripple Effect Analysis

### Dependency Graph

```python
class ScheduleDependencyGraph:
    """
    Model how assignments affect each other through constraints.

    Nodes: Assignments
    Edges: Constraint dependencies
    """

    def build_graph(self, schedule):
        graph = networkx.DiGraph()

        # Add nodes (assignments)
        for assignment in schedule.assignments:
            graph.add_node(assignment.id, data=assignment)

        # Add edges (dependencies)
        for constraint in schedule.constraints:
            affected = constraint.get_affected_assignments()

            # Create edges between all pairs affected by same constraint
            for a1, a2 in combinations(affected, 2):
                graph.add_edge(a1.id, a2.id, constraint=constraint.name)

        return graph

    def find_ripple_effects(self, graph, changed_assignment):
        """
        BFS from changed assignment to find all affected assignments.
        """
        visited = set()
        queue = [changed_assignment]
        ripples = []

        while queue:
            current = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            # Find neighbors (assignments affected by same constraints)
            for neighbor in graph.neighbors(current):
                edge_data = graph.get_edge_data(current, neighbor)

                ripples.append({
                    "assignment": neighbor,
                    "via_constraint": edge_data["constraint"],
                    "distance": len(visited)  # Hops from original change
                })

                queue.append(neighbor)

        return ripples
```

### Containment Strategies

#### Strategy 1: Constraint Isolation

**If change only affects local constraints, ripple is contained**

```python
# Example: Swap within same rotation on same date
# Only affects:
# - Those 2 people's workload
# - That rotation's coverage (same people, just swapped)
# Does NOT affect:
# - Other rotations
# - Other dates
# - Supervision ratios (same people count)
```

#### Strategy 2: Barrier Placement

**Use constraint boundaries as firewalls**

```python
# Example: Workload balance constraint has weekly scope
# Changes within a week don't ripple to other weeks
# Use week boundaries as barriers
```

#### Strategy 3: Dampening

**Absorb ripple with slack capacity**

```python
def dampen_ripple(ripple_effect):
    """
    Use available slack to absorb changes without propagating.

    Example:
    - Ripple would increase person's utilization
    - If person has slack (utilization < 80%), absorb it
    - No further changes needed
    """
    if ripple_effect.person.utilization < 0.75:
        return {
            "absorbed": True,
            "new_utilization": ripple_effect.person.utilization + ripple_effect.delta,
            "further_ripples": []
        }
    else:
        return {
            "absorbed": False,
            "action_required": "Find alternative or propagate further"
        }
```

---

## Swap Candidate Selection

### Compatibility Criteria

```python
def find_compatible_swap_candidates(initiator, target_assignment):
    """
    Find people who could swap with initiator for target assignment.

    Criteria:
    1. Credential match
    2. No schedule conflicts
    3. ACGME compliance maintained
    4. Improves or maintains fairness
    """
    candidates = []

    for person in all_people:
        if person == initiator:
            continue

        # Check credential match
        if not person.has_credentials_for(target_assignment.rotation):
            continue

        # Check schedule conflicts
        if person.is_assigned_at(target_assignment.date, target_assignment.session):
            continue

        # Simulate swap
        temp_schedule = schedule.copy()
        temp_schedule.swap(initiator, person, target_assignment)

        # Check ACGME compliance
        compliance = check_acgme_compliance(temp_schedule)
        if not compliance.passed:
            continue

        # Calculate fairness impact
        current_gini = calculate_gini(schedule)
        new_gini = calculate_gini(temp_schedule)

        candidates.append({
            "person": person,
            "credential_match": True,
            "no_conflicts": True,
            "acgme_compliant": True,
            "fairness_delta": new_gini - current_gini,
            "improves_fairness": new_gini < current_gini
        })

    return sorted(candidates, key=lambda c: c["fairness_delta"])
```

### Ranking Algorithm

```python
def rank_swap_candidates(candidates, preferences):
    """
    Score candidates based on multiple criteria.

    Criteria:
    - Fairness improvement (high weight)
    - Minimal ripple effects (high weight)
    - Preference satisfaction (medium weight)
    - Reciprocity (did they swap with us before?) (low weight)
    """
    scored = []

    for candidate in candidates:
        score = 0

        # Fairness (0-10 points)
        if candidate.improves_fairness:
            score += 10 * abs(candidate.fairness_delta)

        # Ripple effects (0-10 points)
        ripple_count = len(assess_ripple_effects(candidate.swap).ripple_effects)
        score += max(0, 10 - ripple_count * 2)  # Fewer ripples = higher score

        # Preference (0-5 points)
        if candidate.person in preferences.preferred_partners:
            score += 5

        # Reciprocity (0-3 points)
        if candidate.person in swap_history.past_partners:
            score += 3

        scored.append({
            "candidate": candidate,
            "score": score,
            "rank": None  # Will be assigned after sorting
        })

    # Sort by score (descending)
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Assign ranks
    for i, item in enumerate(scored):
        item["rank"] = i + 1

    return scored
```

---

## Validation and Rollback

### Pre-Execution Validation

```python
def validate_swap_before_execution(swap):
    """
    Final validation before committing swap to database.

    Gates:
    1. Backup exists
    2. All constraints satisfied
    3. User confirmation received
    4. Rollback window defined
    """
    validations = []

    # Gate 1: Backup
    latest_backup = get_latest_backup()
    if not latest_backup or latest_backup.age_minutes > 120:
        validations.append({
            "gate": "backup",
            "passed": False,
            "error": "No recent backup found",
            "action": "Create backup before proceeding"
        })
    else:
        validations.append({
            "gate": "backup",
            "passed": True,
            "backup_file": latest_backup.file
        })

    # Gate 2: Constraints
    temp_schedule = schedule.copy()
    temp_schedule.apply_swap(swap)

    for constraint in critical_constraints:
        result = constraint.evaluate(temp_schedule)

        validations.append({
            "gate": f"constraint_{constraint.name}",
            "passed": result.violations == 0,
            "violations": result.violations,
            "details": result.details
        })

    # Gate 3: User confirmation
    validations.append({
        "gate": "user_confirmation",
        "passed": swap.confirmed_by is not None,
        "confirmed_by": swap.confirmed_by,
        "confirmed_at": swap.confirmed_at
    })

    # Gate 4: Rollback window
    validations.append({
        "gate": "rollback_window",
        "passed": True,
        "window_hours": 24,
        "deadline": datetime.now() + timedelta(hours=24)
    })

    all_passed = all(v["passed"] for v in validations)

    return {
        "validated": all_passed,
        "gates": validations,
        "safe_to_proceed": all_passed
    }
```

### Post-Execution Verification

```python
def verify_swap_execution(swap_id):
    """
    Verify swap was applied correctly.

    Checks:
    1. Database committed
    2. Assignments swapped correctly
    3. No unexpected side effects
    4. Constraints still satisfied
    """
    swap = get_swap(swap_id)
    verifications = []

    # Check database state
    db_state = check_database_integrity()
    verifications.append({
        "check": "database_integrity",
        "passed": db_state.consistent,
        "details": db_state.details
    })

    # Check assignments
    for assignment in swap.assignments:
        current = get_assignment(assignment.id)

        verifications.append({
            "check": f"assignment_{assignment.id}",
            "passed": current.person == assignment.expected_person,
            "expected": assignment.expected_person,
            "actual": current.person
        })

    # Check constraints
    current_schedule = get_current_schedule()
    for constraint in critical_constraints:
        result = constraint.evaluate(current_schedule)

        verifications.append({
            "check": f"constraint_{constraint.name}",
            "passed": result.violations == 0,
            "violations": result.violations
        })

    all_passed = all(v["passed"] for v in verifications)

    return {
        "verified": all_passed,
        "checks": verifications,
        "safe_to_commit": all_passed
    }
```

### Rollback Procedure

```python
def rollback_swap(swap_id, reason):
    """
    Reverse a swap within rollback window.

    Steps:
    1. Verify rollback window still open
    2. Create backup of current state (in case rollback fails)
    3. Reverse all assignment changes
    4. Verify reversal successful
    5. Log rollback
    """
    swap = get_swap(swap_id)

    # Check rollback window
    if not swap.can_rollback:
        return {
            "success": False,
            "error": "Rollback window closed",
            "executed_at": swap.executed_at,
            "deadline": swap.rollback_deadline,
            "hours_elapsed": (datetime.now() - swap.executed_at).total_seconds() / 3600
        }

    # Backup current state (before rollback)
    backup = create_backup(f"pre_rollback_{swap_id}")

    try:
        # Reverse assignments
        for assignment in swap.assignments:
            revert_assignment(assignment, to_original=True)

        # Verify reversal
        verification = verify_rollback(swap)

        if verification.verified:
            # Mark swap as rolled back
            swap.status = "rolled_back"
            swap.rollback_reason = reason
            swap.rolled_back_at = datetime.now()
            save_swap(swap)

            return {
                "success": True,
                "swap_id": swap_id,
                "rolled_back_at": swap.rolled_back_at,
                "reason": reason,
                "verification": verification
            }
        else:
            # Rollback failed, restore from backup
            restore_from_backup(backup)
            raise Exception("Rollback verification failed")

    except Exception as e:
        # Restore from backup
        restore_from_backup(backup)

        return {
            "success": False,
            "error": str(e),
            "backup_restored": True
        }
```

---

## Quick Reference

### Surgical Swap Decision Tree

```
Request: User wants to swap assignment

1. Assess Impact
   - Direct changes: How many assignments?
   - Ripple effects: What secondary changes?
   - Impact score: < 10 (safe) or > 10 (risky)?

2. If Impact Score < 10 (SURGICAL)
   ├─> Find compatible candidates
   ├─> Rank by fairness + minimal ripple
   ├─> Select best match
   ├─> Validate (backup, constraints, confirmation)
   ├─> Execute swap
   └─> Verify + Set rollback window

3. If Impact Score > 10 (CONSIDER ALTERNATIVES)
   ├─> Can we reduce ripple? (adjust candidates)
   ├─> Can we defer? (wait for better timing)
   ├─> Is regeneration better? (if score > 50)
   └─> Escalate for approval

4. After Execution
   ├─> Verify success
   ├─> Monitor for 24 hours
   ├─> Allow rollback if issues
   └─> Log for audit
```

---

## Related Documentation

- `.claude/Hooks/post-swap-execution.md` - Swap logging
- `.claude/skills/swap-management/SKILL.md` - Swap procedures
- `.claude/Methodologies/constraint-propagation.md` - Constraint satisfaction
- `backend/app/services/swap_executor.py` - Implementation
