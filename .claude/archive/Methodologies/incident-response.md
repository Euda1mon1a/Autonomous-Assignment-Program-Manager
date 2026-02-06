# Incident Response Methodology

**Purpose:** Systematic approach to detecting, responding to, and recovering from production failures

---

## When to Use This Methodology

Apply when:
- System failures detected (Defense Level RED or BLACK)
- Critical ACGME violations discovered
- Database corruption suspected
- Multiple simultaneous failures
- Patient safety concerns

---

## Core Philosophy

> "In crisis, process beats panic. Follow the checklist."

### Incident Response vs Normal Operations

| Aspect | Normal | Incident |
|--------|--------|----------|
| **Decision Speed** | Deliberate | Immediate |
| **Risk Tolerance** | Low | Higher (controlled) |
| **Approval Process** | Standard | Streamlined |
| **Documentation** | Thorough | Real-time notes |
| **Communication** | Asynchronous | Synchronous |

---

## Detection and Alerting

### Automated Detection

```python
class IncidentDetector:
    """
    Continuous monitoring for incident conditions.

    Triggers:
    - Defense level escalates to RED or BLACK
    - Critical ACGME violations detected
    - Database integrity check fails
    - API health check fails repeatedly
    - Utilization exceeds 100%
    """

    def check_incident_conditions(self):
        incidents = []

        # Check defense level
        defense_level = get_current_defense_level()
        if defense_level in ["RED", "BLACK"]:
            incidents.append({
                "severity": "critical",
                "type": "defense_escalation",
                "level": defense_level,
                "trigger": f"Defense level reached {defense_level}",
                "auto_activate_response": True
            })

        # Check ACGME violations
        compliance = check_acgme_compliance()
        if compliance.critical_violations > 0:
            incidents.append({
                "severity": "critical",
                "type": "acgme_violation",
                "count": compliance.critical_violations,
                "details": compliance.violations,
                "auto_activate_response": True
            })

        # Check database health
        db_health = check_database_integrity()
        if not db_health.healthy:
            incidents.append({
                "severity": "critical",
                "type": "database_failure",
                "details": db_health.errors,
                "auto_activate_response": True
            })

        # Check API health
        api_health = check_api_health()
        if api_health.consecutive_failures > 3:
            incidents.append({
                "severity": "high",
                "type": "api_degradation",
                "failures": api_health.consecutive_failures,
                "auto_activate_response": False  # May be temporary
            })

        # Check utilization
        utilization = get_system_utilization()
        if utilization.average > 1.0:
            incidents.append({
                "severity": "critical",
                "type": "over_capacity",
                "utilization": utilization.average,
                "trigger": "System over 100% capacity",
                "auto_activate_response": True
            })

        return incidents
```

### Alert Escalation

```python
class AlertEscalation:
    """
    Escalate alerts based on severity and duration.
    """

    escalation_matrix = {
        "critical": {
            "immediate": ["on_call_admin", "program_director"],
            "if_unacked_15min": ["hospital_admin"],
            "if_unacked_1hour": ["acgme_contact"]
        },
        "high": {
            "immediate": ["on_call_admin"],
            "if_unacked_1hour": ["program_director"]
        },
        "medium": {
            "immediate": ["admin_team"],
            "if_unacked_4hours": ["on_call_admin"]
        }
    }

    def escalate(self, incident):
        severity = incident.severity
        elapsed = (datetime.now() - incident.detected_at).total_seconds() / 60

        recipients = []

        # Immediate notification
        recipients.extend(self.escalation_matrix[severity]["immediate"])

        # Time-based escalation
        for threshold, contacts in self.escalation_matrix[severity].items():
            if threshold.startswith("if_unacked"):
                threshold_minutes = parse_minutes(threshold)
                if elapsed > threshold_minutes and not incident.acknowledged:
                    recipients.extend(contacts)

        return send_alerts(recipients, incident)
```

---

## Initial Response

### OODA Loop

**Observe → Orient → Decide → Act**

#### Phase 1: Observe (0-5 minutes)

**Gather facts, don't jump to conclusions**

```python
def observe_incident(incident_id):
    """
    Collect all relevant information.

    What to gather:
    - Current system state
    - Recent changes
    - Error logs
    - Affected services
    - User impact
    """
    observation = {
        "timestamp": datetime.now(),
        "observer": get_current_user(),
        "incident_id": incident_id
    }

    # System state
    observation["system_state"] = {
        "defense_level": get_current_defense_level(),
        "utilization": get_system_utilization(),
        "coverage_rate": get_coverage_rate(),
        "acgme_status": check_acgme_compliance(),
        "database_health": check_database_integrity(),
        "api_health": check_api_health()
    }

    # Recent changes
    observation["recent_changes"] = get_recent_changes(hours=24)

    # Error logs
    observation["errors"] = get_recent_errors(minutes=30)

    # Affected services
    observation["affected_services"] = identify_affected_services()

    # User impact
    observation["user_impact"] = {
        "users_affected": count_affected_users(),
        "severity": assess_user_impact()
    }

    return observation
```

#### Phase 2: Orient (5-10 minutes)

**Understand what's happening and why**

```python
def orient_to_incident(observation):
    """
    Analyze observations and form hypotheses.

    Questions:
    - What broke?
    - Why did it break?
    - What's the root cause?
    - What's the blast radius?
    """
    orientation = {
        "timestamp": datetime.now(),
        "observation_id": observation.id
    }

    # Identify failure mode
    orientation["failure_mode"] = classify_failure(observation)

    # Form hypotheses
    orientation["hypotheses"] = [
        generate_hypothesis(observation, evidence)
        for evidence in observation.errors
    ]

    # Assess blast radius
    orientation["blast_radius"] = {
        "people_affected": len(observation.system_state.affected_people),
        "rotations_affected": len(observation.system_state.affected_rotations),
        "dates_affected": len(observation.system_state.affected_dates),
        "contained": is_blast_radius_contained(observation)
    }

    # Identify root cause (best guess)
    orientation["suspected_root_cause"] = rank_hypotheses(orientation.hypotheses)[0]

    return orientation
```

#### Phase 3: Decide (10-15 minutes)

**Choose response strategy**

```python
def decide_response(orientation):
    """
    Select response strategy based on situation.

    Options:
    - Immediate mitigation (stop bleeding)
    - Rollback (undo recent change)
    - Failover (switch to backup system)
    - Controlled shutdown (prevent further damage)
    """
    decision = {
        "timestamp": datetime.now(),
        "orientation_id": orientation.id
    }

    root_cause = orientation.suspected_root_cause

    # Decision tree
    if root_cause.type == "recent_change":
        decision["strategy"] = "rollback"
        decision["action"] = f"Restore from backup: {get_latest_backup().file}"
        decision["expected_recovery_time"] = "10-30 minutes"

    elif root_cause.type == "database_corruption":
        decision["strategy"] = "restore"
        decision["action"] = "Restore database from latest backup"
        decision["expected_recovery_time"] = "30-60 minutes"

    elif root_cause.type == "over_capacity":
        decision["strategy"] = "load_shedding"
        decision["action"] = "Activate sacrifice hierarchy"
        decision["expected_recovery_time"] = "immediate"

    elif root_cause.type == "mass_absence":
        decision["strategy"] = "static_fallback"
        decision["action"] = "Activate pre-computed fallback schedule"
        decision["expected_recovery_time"] = "5-10 minutes"

    else:
        decision["strategy"] = "investigate"
        decision["action"] = "Continue investigation, implement temporary mitigation"
        decision["expected_recovery_time"] = "unknown"

    # Risk assessment
    decision["risks"] = assess_response_risks(decision.strategy)

    # Approval needed?
    decision["requires_approval"] = decision.risks.high_impact

    return decision
```

#### Phase 4: Act (15+ minutes)

**Execute response plan**

```python
def execute_response(decision):
    """
    Carry out the chosen response strategy.

    Steps:
    1. Confirm approval (if needed)
    2. Create recovery point (backup)
    3. Execute action
    4. Verify recovery
    5. Document
    """
    execution = {
        "timestamp": datetime.now(),
        "decision_id": decision.id
    }

    # Step 1: Approval
    if decision.requires_approval:
        approval = request_approval(decision, from_user=decision.approver)
        if not approval.granted:
            execution["status"] = "aborted"
            execution["reason"] = approval.denial_reason
            return execution

    # Step 2: Create recovery point
    execution["recovery_point"] = create_backup(f"incident_{decision.incident_id}")

    # Step 3: Execute
    try:
        result = execute_strategy(decision.strategy, decision.action)
        execution["result"] = result
        execution["status"] = "success" if result.succeeded else "failed"

    except Exception as e:
        execution["status"] = "failed"
        execution["error"] = str(e)
        execution["rollback_required"] = True

    # Step 4: Verify
    if execution["status"] == "success":
        verification = verify_recovery()
        execution["verification"] = verification

        if not verification.recovered:
            execution["status"] = "partial"
            execution["next_action"] = "Escalate to next strategy"

    # Step 5: Document
    log_incident_action(execution)

    return execution
```

---

## Investigation

### Root Cause Analysis (5 Whys)

```python
def five_whys_analysis(incident):
    """
    Iteratively ask "why" to find root cause.

    Example:
    Problem: Schedule generation failed
    Why 1: Solver timeout
    Why 2: Too many constraints to satisfy
    Why 3: New constraint added without testing
    Why 4: No pre-commit validation
    Why 5: Constraint preflight skill not enforced
    Root Cause: Missing process enforcement
    """
    whys = []
    current_problem = incident.symptom

    for i in range(5):
        why = {
            "level": i + 1,
            "question": f"Why did '{current_problem}' happen?",
            "answer": investigate_cause(current_problem)
        }

        whys.append(why)
        current_problem = why["answer"]

        # Stop if we've reached a true root cause
        if is_root_cause(current_problem):
            break

    return {
        "symptom": incident.symptom,
        "whys": whys,
        "root_cause": whys[-1]["answer"] if whys else "Unknown",
        "actionable": is_actionable(whys[-1]["answer"] if whys else None)
    }
```

### Fishbone Diagram (Ishikawa)

```python
def fishbone_analysis(incident):
    """
    Analyze potential root causes across categories.

    Categories:
    - People: Human error, training, communication
    - Process: Procedures, workflows, approvals
    - Technology: Software bugs, infrastructure, dependencies
    - Environment: External factors, load, timing
    """
    fishbone = {
        "problem": incident.symptom,
        "categories": {}
    }

    # People
    fishbone["categories"]["people"] = [
        "Insufficient training on new feature",
        "Misunderstood constraint behavior",
        "Did not follow validation procedure"
    ]

    # Process
    fishbone["categories"]["process"] = [
        "Constraint preflight not enforced",
        "No peer review before merge",
        "Insufficient testing coverage"
    ]

    # Technology
    fishbone["categories"]["technology"] = [
        "Constraint propagation bug",
        "Solver timeout too aggressive",
        "Database connection pool exhausted"
    ]

    # Environment
    fishbone["categories"]["environment"] = [
        "Deployed during peak usage",
        "Concurrent schedule generation requests",
        "Backup process running (resource contention)"
    ]

    # Rank by likelihood
    ranked = rank_causes_by_evidence(fishbone.categories, incident.evidence)

    return {
        "fishbone": fishbone,
        "most_likely": ranked[0],
        "action_items": generate_action_items(ranked)
    }
```

---

## Remediation

### Mitigation Strategies

#### 1. Rollback

**When to use:** Recent change caused failure

```python
def rollback_to_previous_state(incident):
    """
    Restore system to known-good state.

    Steps:
    1. Identify good state (backup or git commit)
    2. Stop incoming requests (maintenance mode)
    3. Restore database / code
    4. Verify restoration
    5. Resume operations
    """
    # Find good state
    if incident.caused_by_database_change:
        good_state = get_latest_backup(before=incident.detected_at)
    elif incident.caused_by_code_change:
        good_state = get_git_commit(before=incident.detected_at)
    else:
        good_state = None

    if not good_state:
        return {
            "success": False,
            "error": "No known-good state found",
            "recommendation": "Try alternative mitigation"
        }

    # Execute rollback
    enable_maintenance_mode()
    restore_result = restore_from_state(good_state)
    verify_result = verify_system_health()

    if verify_result.healthy:
        disable_maintenance_mode()
        return {
            "success": True,
            "restored_to": good_state,
            "downtime_minutes": calculate_downtime(incident)
        }
    else:
        return {
            "success": False,
            "error": "Restoration failed verification",
            "next_action": "Escalate"
        }
```

#### 2. Load Shedding

**When to use:** Over capacity

```python
def shed_load(incident):
    """
    Reduce load to restore stability.

    Methods:
    - Activate sacrifice hierarchy
    - Defer non-critical rotations
    - Reduce resident assignments
    - Request external support
    """
    from .sacrifice_hierarchy import SacrificeHierarchy

    hierarchy = SacrificeHierarchy()

    # Calculate capacity deficit
    current_capacity = get_current_capacity()
    required_capacity = get_required_capacity()
    deficit = required_capacity - current_capacity

    # Shed load
    sacrificed = hierarchy.apply_sacrifice(deficit)

    return {
        "success": True,
        "capacity_freed": len(sacrificed.sacrificed_assignments),
        "rotations_deferred": [a.rotation for a in sacrificed.sacrificed_assignments],
        "critical_rotations_maintained": sacrificed.critical_rotations_maintained,
        "action": "Notify affected people of changes"
    }
```

#### 3. Failover

**When to use:** Primary system failed, backup available

```python
def failover_to_backup(incident):
    """
    Switch to backup system.

    For scheduler:
    - Activate static fallback schedule
    - Switch to read-only mode
    - Use cached data
    """
    if incident.type == "schedule_generation_failure":
        # Activate pre-computed fallback
        fallback = load_static_fallback_schedule()

        return {
            "success": True,
            "failover_target": "static_fallback_schedule",
            "coverage_rate": fallback.coverage_rate,
            "limitations": "Not optimized for current personnel"
        }

    elif incident.type == "database_failure":
        # Switch to read-only cached mode
        enable_read_only_mode()
        use_cached_data()

        return {
            "success": True,
            "failover_target": "read_only_cache",
            "limitations": "No writes allowed until database restored"
        }
```

#### 4. Controlled Shutdown

**When to use:** Cannot safely continue, prevent further damage

```python
def controlled_shutdown(incident):
    """
    Gracefully shut down to prevent cascading failures.

    Steps:
    1. Stop accepting new requests
    2. Complete in-flight operations
    3. Save state
    4. Shut down services
    5. Alert users
    """
    # Stop new requests
    enable_maintenance_mode(message="System undergoing emergency maintenance")

    # Complete in-flight
    wait_for_pending_operations(timeout=300)  # 5 minutes

    # Save state
    emergency_backup = create_backup("emergency_shutdown")

    # Shutdown
    stop_services()

    # Alert
    send_incident_notification(
        severity="critical",
        message="Scheduler in emergency maintenance",
        eta="Unknown - investigating"
    )

    return {
        "success": True,
        "backup_created": emergency_backup.file,
        "services_stopped": ["api", "celery", "scheduler"],
        "next_action": "Investigate and fix root cause before restart"
    }
```

---

## Post-Mortem

### Post-Incident Review Template

```markdown
# Post-Incident Review: [Incident Title]

**Date:** YYYY-MM-DD
**Severity:** Critical / High / Medium
**Duration:** HH:MM (from detection to resolution)
**Impact:** [Number of people affected, rotations disrupted, etc.]

---

## Timeline

| Time | Event |
|------|-------|
| 14:30 | Incident detected (automated alert) |
| 14:32 | On-call admin acknowledged |
| 14:35 | Initial investigation started |
| 14:45 | Root cause identified (constraint bug) |
| 14:50 | Decision: Rollback to previous version |
| 14:55 | Rollback executed |
| 15:00 | System verified healthy |
| 15:05 | Incident resolved |

---

## What Happened

[Clear description of the incident]

Example:
Schedule generation began failing with "infeasible" status due to a newly added constraint that was over-constrained.

---

## Root Cause

[5 Whys or Fishbone results]

Example:
New constraint added without sufficient testing. The constraint was too restrictive and made the problem infeasible for typical schedules.

---

## Impact

- **Users affected:** 27 (all residents and faculty)
- **Rotations disrupted:** 0 (caught before deployment)
- **Duration:** 35 minutes (detection to resolution)
- **Data loss:** None
- **ACGME violations introduced:** None

---

## What Went Well

- Automated detection within 2 minutes
- Clear escalation path followed
- Rollback executed smoothly
- No data loss
- Documentation up to date

---

## What Went Wrong

- Constraint not tested before merge
- No pre-commit validation enforced
- Insufficient code review
- Lacked constraint unit tests

---

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Add constraint unit tests | Dev Team | 2025-12-30 | Open |
| Enforce constraint-preflight skill | Lead Dev | 2025-12-27 | Open |
| Update constraint documentation | Tech Writer | 2025-12-29 | Open |
| Add constraint complexity linter | Dev Team | 2026-01-05 | Open |

---

## Lessons Learned

1. **Prevention is cheaper than cure:** 5 minutes of testing > 35 minutes of incident
2. **Automate the checklist:** Human review missed the issue, automation would catch it
3. **Test in production-like conditions:** Local testing didn't expose constraint interaction

---

## Follow-Up

- [ ] Schedule follow-up review (1 week)
- [ ] Verify action items completed
- [ ] Update runbooks with lessons learned
- [ ] Share post-mortem with team
```

### Blame-Free Culture

```python
def conduct_post_mortem(incident):
    """
    Focus on system improvements, not individual blame.

    Questions to ask:
    - How did the system allow this to happen?
    - What process gaps existed?
    - How can we prevent recurrence?

    Questions to AVOID:
    - Who made the mistake?
    - Why didn't you catch this?
    - Whose fault is this?
    """
    return {
        "focus": "system_improvements",
        "tone": "blameless",
        "goal": "prevent_recurrence",
        "output": "actionable_items"
    }
```

---

## Quick Reference

### Incident Response Checklist

```
[ ] DETECT
    [ ] Automated monitoring triggered alert
    [ ] Alert escalated to on-call
    [ ] Incident acknowledged

[ ] OBSERVE (0-5 min)
    [ ] Gather system state
    [ ] Check recent changes
    [ ] Review error logs
    [ ] Assess user impact

[ ] ORIENT (5-10 min)
    [ ] Classify failure mode
    [ ] Form hypotheses
    [ ] Identify blast radius
    [ ] Determine suspected root cause

[ ] DECIDE (10-15 min)
    [ ] Select response strategy
    [ ] Assess risks
    [ ] Get approval (if needed)

[ ] ACT (15+ min)
    [ ] Create recovery point (backup)
    [ ] Execute strategy
    [ ] Verify recovery
    [ ] Document actions

[ ] RECOVER
    [ ] Verify system healthy
    [ ] Resume normal operations
    [ ] Monitor for recurrence

[ ] POST-MORTEM (within 48 hours)
    [ ] Write incident report
    [ ] Identify root cause
    [ ] Create action items
    [ ] Share lessons learned
```

---

## Related Documentation

- `.claude/Hooks/post-resilience-test.md` - Resilience monitoring
- `.claude/Methodologies/resilience-thinking.md` - Failure mode analysis
- `.claude/skills/production-incident-responder/SKILL.md` - Incident procedures
- `docs/admin-manual/DISASTER_RECOVERY.md` - Recovery procedures
