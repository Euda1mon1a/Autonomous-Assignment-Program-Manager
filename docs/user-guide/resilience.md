# Schedule Resilience Features

> **Last Updated:** 2025-12-16

Learn how the Residency Scheduler helps your program survive faculty shortages, PCS season, and other challenging periods.

---

## Overview

The resilience framework helps you:
- **Prepare** for faculty shortages before they happen
- **Monitor** schedule health with early warning alerts
- **Respond** with pre-planned contingency schedules
- **Recover** sustainably after crisis periods

---

## Key Concepts

### The 80% Rule

**Never schedule faculty above 80% of their capacity.**

Why? When utilization is too high, small problems (sick days, emergencies) cause massive cascading failures. The 20% buffer absorbs normal variability.

| Utilization | What Happens |
|-------------|--------------|
| 50% | Comfortable buffer, handles anything |
| 80% | Maximum sustainable utilization |
| 90% | Small problems become big ones |
| 95%+ | Cascade failures, burnout, errors |

The system automatically warns you when faculty utilization approaches 80%.

---

### Coverage Levels

The system monitors overall schedule coverage and displays color-coded alerts:

| Level | Coverage | Meaning |
|-------|----------|---------|
| **GREEN** | 95%+ | Normal operations |
| **YELLOW** | 85-94% | Monitor closely, consider reducing optional activities |
| **ORANGE** | 70-84% | Consolidate services, implement contingency plans |
| **RED** | 50-69% | Essential services only, all hands on clinical |
| **BLACK** | Below 50% | Escalate to leadership, consider service limitations |

---

## Dashboard Widgets

### Coverage Health

Shows current coverage percentage with trend indicators:
- Upward arrow: Coverage improving
- Downward arrow: Coverage declining (investigate)
- Stable: No change

### Vulnerability Alerts

Identifies "single points of failure":
- Faculty members whose absence would leave critical slots uncovered
- Services with no backup coverage
- Time periods with minimal redundancy

##***REMOVED*** Workload

Shows utilization for each faculty member:
- Green: Under 70% (comfortable)
- Yellow: 70-80% (acceptable)
- Red: Over 80% (needs attention)

---

## Contingency Schedules

### What Are They?

Pre-computed backup schedules that can be activated instantly during a crisis, without needing to rebuild from scratch.

### Available Scenarios

| Scenario | When to Use |
|----------|-------------|
| **1 Faculty Loss** | Single unexpected absence |
| **2 Faculty Loss** | Multiple absences or PCS overlap |
| **PCS Season (50%)** | Half of faculty unavailable |
| **Holiday Skeleton** | Minimal staffing periods |
| **Essential Only** | Severe shortage, clinical priority |

### Activating a Contingency Schedule

1. Go to **Schedule > Contingency Plans**
2. Select the appropriate scenario
3. Review the proposed changes
4. Click **Activate** to apply

The system tracks which contingency plan is active and for how long.

---

## Activity Priority (Load Shedding)

When you can't do everything, the system helps you decide what to cut first based on this priority order:

| Priority | Category | Examples | When to Cut |
|----------|----------|----------|-------------|
| 1 (Never) | Patient Safety | ICU, OR, Trauma | Never cut |
| 2 | ACGME Requirements | Required rotations | Only in extreme crisis |
| 3 | Continuity | Follow-up clinics | Can defer temporarily |
| 4 | Core Education | Didactics | Reduce during shortages |
| 5 | Research | Protected time | First discretionary cut |
| 6 | Admin | Meetings, committees | First to cut |
| 7 | Optional Education | Conferences, electives | First to cut |

### Using Load Shedding

1. Go to **Schedule > Load Management**
2. See current capacity vs. demand
3. Review suggested activities to suspend
4. Approve or modify the recommendations

---

## N-1/N-2 Analysis

### What Is It?

**N-1 Analysis**: Can your schedule survive if any single faculty member is unavailable?

**N-2 Analysis**: Can your schedule survive if any two faculty members are unavailable?

### Viewing the Analysis

1. Go to **Schedule > Vulnerability Analysis**
2. See which faculty members are "critical" (single points of failure)
3. See which pairs of absences would cause coverage failures

### Using the Results

- **High vulnerability**: Consider cross-training or hiring
- **Critical pairs**: Don't schedule both faculty for leave at the same time
- **Protected periods**: Ensure extra coverage during high-risk times

---

#***REMOVED*** Stress Tracking

### Allostatic Load

The system tracks cumulative stress indicators to prevent burnout:

- Consecutive weekend calls
- Night shifts in past month
- Absorbed schedule changes
- Holidays worked this year

### Warning Levels

| Load Score | Status | Action |
|------------|--------|--------|
| Low | Healthy | Normal scheduling |
| Medium | Watch | Avoid adding stressors |
| High | Warning | Schedule protective time |
| Critical | Urgent | Immediate intervention |

### Viewing Stress Metrics

1. Go to **People > Faculty Workload**
2. Sort by stress/workload indicators
3. Click on a faculty member for detailed breakdown

---

## Recovery Guidelines

After a shortage period ends:

1. **Verify sustainable capacity** - Don't just reach threshold; exceed it
2. **Restore gradually** - Critical services first, then discretionary
3. **Monitor for relapse** - Extra check-ins for 30 days
4. **Conduct retrospective** - What triggered the crisis? How to prevent?

### Recovery Checklist

- [ ] Coverage back above 95%
- [ ] All contingency plans deactivated
- [ ] Faculty workloads normalized
- [ ] Suspended activities restored
- [ ] Lessons learned documented

---

## Tips for Program Coordinators

### Proactive Planning

1. **Review vulnerability analysis monthly** - Know your single points of failure
2. **Keep contingency schedules updated** - Refresh when faculty changes
3. **Cross-train where possible** - Reduce dependency on specific individuals
4. **Build relationships with backup coverage** - Know who to call in emergencies

### During Shortages

1. **Communicate early** - Warn stakeholders before crisis hits
2. **Use pre-planned responses** - Don't improvise under stress
3. **Track decisions** - Document what was cut and why
4. **Protect your own capacity** - You can't help others if burned out

### After Recovery

1. **Document lessons learned** - What worked? What didn't?
2. **Update contingency plans** - Incorporate new knowledge
3. **Recognize contributions** - Thank those who stepped up
4. **Address root causes** - Can we prevent this next time?

---

## Related Documentation

- [Dashboard Overview](./dashboard.md) - Understanding the main dashboard
- [Schedule Generation](./schedule-generation.md) - Creating schedules
- [Compliance Monitoring](./compliance.md) - ACGME compliance features
- [Resilience Framework (Technical)](../RESILIENCE_FRAMEWORK.md) - Detailed technical documentation
