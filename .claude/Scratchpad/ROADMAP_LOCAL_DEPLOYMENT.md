# 6-Month Outcomes Roadmap

> **Document Type:** Operational Playbook
> **Audience:** Program Coordinator
> **Purpose:** Build evidence case for scheduler value through systematic data collection
> **Last Updated:** 2026-01-06

---

## Purpose

This document helps you answer one question: **Is the scheduler helping?**

Over the next 6 months, you'll collect evidence to:
1. Quantify time savings
2. Demonstrate compliance improvements
3. Build a case for broader adoption (Ask Sage, multi-MTF)

This is not a technical document. It's your playbook for proving value.

---

## Phase 1: Baseline (Week 1)

**Goal:** Capture how things work TODAY, before using the scheduler.

### What to Measure Now

Before you generate your first schedule, document your current state:

| Metric | Your Current Value | How to Measure |
|--------|-------------------|----------------|
| **Time spent scheduling (hours/week)** | _____ | Track for one week |
| **Time spent on swap coordination (hours/week)** | _____ | Include phone calls, emails, texts |
| **ACGME violations caught per block** | _____ | Review last 2-3 blocks if records exist |
| **Swap resolution time (days)** | _____ | From request to confirmed swap |
| **Current method** | Excel / Paper / Memory / Other | Document what you use now |
| **Number of people involved in scheduling** | _____ | Who touches the schedule? |
| **Last-minute changes per block** | _____ | Coverage gaps, sick calls, etc. |

### Pain Points to Document (Anecdotal)

Write down 3-5 specific frustrations with current scheduling:

1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________
4. _________________________________________________________________
5. _________________________________________________________________

These become your "before" stories for the Ask Sage case.

### Baseline Evidence to Collect

- [ ] Screenshot of current scheduling tool (Excel, Amion, etc.)
- [ ] Sample of email chains for swap coordination
- [ ] Any existing compliance reports (if you have them)
- [ ] Calendar showing time blocked for scheduling tasks

---

## Phase 2: Operations (Months 1-3)

**Goal:** Run the scheduler, track what matters, identify issues early.

### Weekly Check-In (5 minutes)

Every Friday, answer these questions:

| Question | Week 1 | Week 2 | Week 3 | Week 4 |
|----------|--------|--------|--------|--------|
| Time spent in scheduler this week (minutes) | | | | |
| Schedules generated | | | | |
| Manual overrides made after generation | | | | |
| Swap requests processed | | | | |
| Issues encountered | | | | |
| Quick wins / things that worked well | | | | |

### Monthly Metrics

At the end of each month, compile:

#### Operational Metrics
- Total time spent in scheduler (sum weekly)
- Compare to baseline: time saved = baseline - actual
- Number of schedules generated
- Percentage requiring manual adjustment
- Swap requests: count, average resolution time

#### Compliance Metrics
- ACGME violations detected during generation (prevented)
- 80-hour limit catches
- 1-in-7 day-off violations prevented
- Supervision gap warnings

#### Quality Metrics
- Schedule completeness (% slots filled on first generation)
- Coverage gaps requiring manual intervention
- Last-minute changes needed (compare to baseline)

### Month-by-Month Focus

**Month 1: Stabilization**
- Primary question: Does it work?
- Focus: Get comfortable with the tool, report bugs, establish routine
- Expected issues: Learning curve, data entry, workflow adjustment
- Success marker: Generated at least 2 complete schedules

**Month 2: Efficiency**
- Primary question: Is it faster?
- Focus: Time tracking, identify bottlenecks, optimize workflow
- Compare: Weekly time spent vs. baseline
- Success marker: Time spent is less than baseline

**Month 3: Quality Check**
- Primary question: Is it better?
- Focus: Compliance metrics, schedule quality, user feedback
- Milestone: First quarterly compliance report
- Success marker: Quantified compliance improvements

---

## Phase 3: Assessment (Months 4-6)

**Goal:** Analyze results, prepare evidence, make recommendations.

### Month 4: User Feedback

Collect feedback from anyone who interacts with schedules:

**Resident Survey (simple):**
1. How satisfied are you with schedule communication? (1-5)
2. How quickly are swap requests resolved? (1-5)
3. Any comments?

**Faculty Survey (if applicable):**
1. Is supervision coverage clear? (1-5)
2. Any scheduling conflicts this quarter? (count)

### Month 5: Comparative Analysis

Build your before/after comparison:

| Metric | Before (Baseline) | After (Average Mo 2-4) | Improvement |
|--------|-------------------|------------------------|-------------|
| Time spent scheduling (hrs/week) | | | ___% saved |
| Swap resolution time (days) | | | ___% faster |
| ACGME violations per block | | | ___% reduced |
| Last-minute changes | | | ___% fewer |
| Manual interventions | | | ___% reduced |

### Month 6: Decision Point

Three options based on results:

1. **Expand:** Results strong - pursue Ask Sage, multi-MTF
2. **Continue:** Results promising - refine for another quarter
3. **Pivot:** Results mixed - identify specific improvements needed

Prepare a 1-page summary for leadership.

---

## Metrics Framework

Complete reference of what to track, how, and where to find it.

| Metric | What It Measures | Collection Method | Frequency | Where Stored |
|--------|------------------|-------------------|-----------|--------------|
| **Scheduling time** | Hours spent on scheduling tasks | Manual log | Weekly | Your spreadsheet |
| **Swap resolution time** | Days from request to confirmation | System logs + manual | Per swap | Audit logs |
| **ACGME violations prevented** | Compliance issues caught before publishing | Validation results | Per generation | Database |
| **Schedule completeness** | % slots filled on first attempt | Generation report | Per schedule | API response |
| **Manual overrides** | Changes made after generation | Count manually | Weekly | Your log |
| **User logins** | Engagement with system | API logs | Monthly | Database |
| **Generation runs** | How often scheduler is used | Background task logs | Monthly | Celery results |
| **Coverage gaps** | Unfilled required slots | Conflict detection | Per schedule | Database |
| **Swap volume** | Number of swap requests | Swap audit trail | Monthly | Database |
| **System errors** | Reliability issues | Error logs | Monthly | Backend logs |

---

## Built-in Telemetry

The scheduler automatically tracks these. No extra work required.

### Audit Logs (SQLAlchemy-Continuum)
- Every schedule change (who, what, when)
- Every swap lifecycle event (requested, approved, rejected, executed)
- User login events
- Data modifications

**How to access:**
```
Admin > Audit Logs (in frontend)
-- or --
API: GET /api/v1/audit/logs
```

### Constraint Violations
- Stored with each validation run
- Includes: violation type, severity, affected persons, suggested resolution

**How to access:**
```
After any schedule generation, check the validation results panel
-- or --
API: GET /api/v1/schedule/{id}/validation
```

### Schedule Generation Metrics
- Solver runtime (how long generation took)
- Algorithm used
- Objective function value (optimization score)
- Constraint satisfaction percentage

**How to access:**
```
Generation History in Schedule > History
-- or --
API: GET /api/v1/schedule/runs
```

### Swap History
- Complete trail: request -> review -> approval -> execution
- Timestamps at each stage
- Who approved, why (if comments provided)

**How to access:**
```
Swaps > History (filtered by date range)
-- or --
API: GET /api/v1/swaps?status=all
```

---

## Monthly Review Template

Copy this template for each monthly check-in.

```
# Month [X] Review - [Date]

## Time Tracking
- Total hours on scheduling this month: ____
- Compared to baseline: ____ hours saved/lost

## Schedule Generation
- Schedules generated: ____
- Average completeness: ____%
- Manual overrides needed: ____

## Compliance
- ACGME violations prevented: ____
- Types: ________________________________

## Swaps
- Requests processed: ____
- Average resolution time: ____ days
- Rejected (and why): ____

## Issues Encountered
1. ________________________________
2. ________________________________

## Wins This Month
1. ________________________________
2. ________________________________

## Next Month Focus
________________________________
```

---

## 6-Month Summary Template

Use this format for your final report to leadership.

```
# Residency Scheduler: 6-Month Pilot Summary

## Executive Summary
[2-3 sentences: What we tested, what we found, what we recommend]

## Baseline (Where We Started)
- Hours/week on scheduling: ____
- Swap resolution time: ____ days
- ACGME violations per block: ____
- Method: ____

## Results (What Changed)

### Time Savings
- Before: ____ hours/week
- After: ____ hours/week
- Savings: ____ hours/week (____ hours/year)
- FTE equivalent: ____ (if applicable)

### Compliance Improvement
- ACGME violations prevented: ____ total
- 80-hour violations caught: ____
- Day-off violations caught: ____
- Estimated risk reduction: [qualitative assessment]

### Operational Improvements
- Swap resolution time: Before ____ days, After ____ days
- Schedule completeness: ____%
- Last-minute changes: Reduced by ____%

### User Feedback
[Summary of survey results or qualitative feedback]

## System Reliability
- Uptime: ____%
- Critical errors: ____
- Data security incidents: ____

## Recommendation
[ ] Expand - Pursue DOD-wide deployment
[ ] Continue - Extend pilot with refinements
[ ] Pivot - Reassess approach

## Next Steps
1. ________________________________
2. ________________________________
3. ________________________________

## Appendix: Raw Data
[Attach monthly tracking spreadsheet]
```

---

## Evidence Collection for Ask Sage Case

What DOD/Ask Sage reviewers will want to see:

### Quantified Impact
- **Time savings:** X hours/week = Y hours/year = Z FTE equivalent
- **Compliance improvement:** N violations prevented, M% reduction in risk
- **Efficiency gains:** Swap time reduced by X%, schedule generation in Y minutes vs Z hours

### Adoption Metrics
- Active users: ____
- Login frequency: ____ sessions/week
- Feature usage: Which capabilities are used most?

### Security Posture
- Data breaches: 0 (document this explicitly)
- Audit trail completeness: 100%
- Access control: RBAC implemented and tested

### Reliability
- System uptime: ____%
- Mean time to recover from issues: ____
- Backup verification: Tested and confirmed

### User Testimonials
- Quotes from coordinator, residents, faculty (with permission)
- Before/after workflow descriptions
- Specific examples of problems solved

---

## Simple Tracking Tools

Don't overcomplicate this. Use what works for you.

### Option 1: Weekly Log (Simplest)
Every Friday, spend 5 minutes answering:
1. How much time did I spend in the scheduler?
2. What worked well?
3. What didn't work?

Keep in a notebook, text file, or simple spreadsheet.

### Option 2: Monthly Metrics Spreadsheet

| Month | Sched Hours | Swaps | Violations Prevented | Issues | Notes |
|-------|-------------|-------|---------------------|--------|-------|
| Month 1 | | | | | |
| Month 2 | | | | | |
| ... | | | | | |

### Option 3: Screenshot/Evidence Folder
Create a folder structure:
```
/Evidence
  /Baseline
    - old_excel_schedule.xlsx
    - email_chain_example.pdf
  /Month1
    - validation_report.png
    - time_log.txt
  /Month2
    ...
```

---

## Appendix: Data Export Commands

How to pull data from the system for your reports.

### Export Schedule History
```bash
# From Docker container
docker-compose exec backend python -c "
from app.services.schedule_service import ScheduleService
# Export logic here - creates CSV/Excel
"
```

Or use the frontend: **Schedule > Export > History**

### Export Audit Logs
```bash
# API call
curl -X GET "http://localhost:8000/api/v1/audit/export?start=2026-01-01&end=2026-06-30" \
  -H "Authorization: Bearer <token>" \
  -o audit_logs.csv
```

### Export Swap History
```bash
curl -X GET "http://localhost:8000/api/v1/swaps/export?start=2026-01-01&end=2026-06-30" \
  -H "Authorization: Bearer <token>" \
  -o swap_history.csv
```

### Export Validation Results
```bash
curl -X GET "http://localhost:8000/api/v1/validation/export?start=2026-01-01&end=2026-06-30" \
  -H "Authorization: Bearer <token>" \
  -o validation_results.csv
```

### Quick Database Query (if needed)
```bash
docker-compose exec db psql -U scheduler residency_scheduler -c "
SELECT
  date_trunc('month', created_at) as month,
  COUNT(*) as schedule_runs,
  AVG(solver_runtime_seconds) as avg_runtime
FROM schedule_generation_runs
GROUP BY 1
ORDER BY 1;
"
```

---

## Key Principle

This roadmap exists to answer: **"Was deploying the scheduler worth it?"**

In 6 months, you should be able to say:

> "Before the scheduler, I spent X hours/week on scheduling. Now I spend Y hours/week. That's Z hours saved per year. We also prevented N ACGME violations and reduced swap resolution time from A days to B days. The system has been reliable with zero data incidents."

That's the case for expansion.

---

*For technical deployment instructions, see `docs/operations/DOCKER_LOCAL_SETUP.md`*
