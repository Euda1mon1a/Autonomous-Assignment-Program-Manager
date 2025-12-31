# ACGME Program Evaluation Framework

**Status:** Complete Reconnaissance Report
**Date Generated:** 2025-12-30
**Scope:** Program evaluation requirements, metrics tracking, site visit preparation, and continuous improvement documentation

---

## Executive Summary

This document provides a comprehensive framework for ACGME (Accreditation Council for Graduate Medical Education) program evaluation within the Residency Scheduler system. The framework integrates:

1. **Core ACGME Compliance Requirements** (80-hour rule, 1-in-7 rule, supervision ratios)
2. **Real-Time Metrics Tracking** (compliance dashboards, trend analysis)
3. **Site Visit Preparation** (documentation procedures, citation response)
4. **Continuous Improvement Documentation** (evaluation cycles, evidence collection)

---

## Table of Contents

1. [ACGME Core Requirements](#acgme-core-requirements)
2. [Evaluation Metrics Framework](#evaluation-metrics-framework)
3. [Real-Time Monitoring & Dashboards](#real-time-monitoring--dashboards)
4. [Site Visit Preparation Checklist](#site-visit-preparation-checklist)
5. [Documentation & Audit Trail](#documentation--audit-trail)
6. [Improvement Cycles & Evidence](#improvement-cycles--evidence)
7. [Citation Response Procedures](#citation-response-procedures)
8. [Hidden Evaluation Gaps](#hidden-evaluation-gaps)
9. [Implementation Roadmap](#implementation-roadmap)

---

## ACGME Core Requirements

### 1. Eighty-Hour Rule

**Requirement:** Residents must not exceed 80 hours per week, averaged over a rolling 4-week period.

**System Implementation:**
```
Component: backend/app/scheduling/validator.py::ACGMEValidator._check_80_hour_rule()
Constants:
  - MAX_WEEKLY_HOURS = 80
  - HOURS_PER_HALF_DAY = 6 (realistic clinical duty)
  - ROLLING_WINDOW_WEEKS = 4
```

**Monitoring Approach:**
- Weekly aggregation of assignments per resident
- Rolling 4-week window calculations
- Alert triggers at 75 hours/week (warning) and 80+ hours/week (violation)
- Real-time dashboard updates via Prometheus metrics

**Compliance Report Metrics:**
- Average weekly hours (per resident, per PGY level)
- Maximum weekly hours in any given week
- Number of residents exceeding limits
- Trend analysis over time

### 2. One-in-Seven (1-in-7) Rule

**Requirement:** Residents must have at least one 24-hour period off every 7 consecutive days.

**System Implementation:**
```
Component: backend/app/scheduling/validator.py::ACGMEValidator._check_1_in_7_rule()
```

**Monitoring Approach:**
- Sliding 7-day windows
- Consecutive day calculations
- Rest period identification
- Violation tracking by resident and date range

**Compliance Report Metrics:**
- Residents with consecutive day violations
- Maximum consecutive days worked per resident
- Distribution of rest periods
- Violation frequency and severity

### 3. Supervision Ratios

**Requirement:** Adequate faculty supervision based on PGY level
- PGY-1 residents: 1 faculty per 2 residents
- PGY-2+ residents: 1 faculty per 4 residents

**System Implementation:**
```
Component: backend/app/scheduling/validator.py::ACGMEValidator._check_supervision_ratios()
Logic:
  required = max(1, (pgy1_count + 1) // 2 + (other_count + 3) // 4)
  violation = faculty_count < required
```

**Monitoring Approach:**
- Block-level supervision calculations
- Real-time faculty availability tracking
- Deficit identification and escalation
- Coverage analysis by rotation type

**Compliance Report Metrics:**
- Total blocks analyzed
- Supervision compliance rate
- Blocks with violations (by severity)
- Faculty-to-resident ratios by PGY level
- Supervision gaps by rotation/block

---

## Evaluation Metrics Framework

### Tier 1: Compliance Metrics

#### 1.1 Work Hour Metrics

| Metric | Source | Type | Target | Alert |
|--------|--------|------|--------|-------|
| Average weekly hours | Rolling window analysis | Gauge | ≤ 70 hrs | > 75 hrs |
| Max weekly hours | Peak week analysis | Gauge | ≤ 80 hrs | > 80 hrs |
| Residents exceeding limit | Count aggregation | Counter | 0 | > 0 |
| Compliance rate (work hours) | Percentage of residents compliant | Gauge | 100% | < 95% |
| Violation trends | Week-over-week comparison | Trend | Stable/improving | Increasing |

**Code Reference:**
- Report generation: `backend/app/compliance/reports.py::ComplianceReportGenerator.generate_compliance_data()`
- Resident analysis: `backend/app/compliance/reports.py::ComplianceReportGenerator._analyze_resident()`

#### 1.2 Coverage & Availability Metrics

| Metric | Source | Type | Target | Alert |
|--------|--------|------|--------|-------|
| Schedule coverage rate | Assigned blocks / total blocks | Gauge | ≥ 95% | < 90% |
| Faculty availability | Available faculty count | Gauge | > minimum | = minimum |
| Supervision compliance rate | Blocks meeting ratios / total blocks | Gauge | 100% | < 95% |
| Unassigned blocks | Count by period | Counter | 0-2% | > 5% |

**Code Reference:**
- Coverage calculation: `backend/app/compliance/reports.py::ComplianceReportGenerator._calculate_coverage_metrics()`
- Supervision analysis: `backend/app/compliance/reports.py::ComplianceReportGenerator._calculate_supervision_summary()`

#### 1.3 Leave & Absence Metrics

| Metric | Source | Type | Target | Alert |
|--------|--------|------|--------|-------|
| Total absence days | Sum of all absences | Counter | Proportional to program size | > 10% of workdays |
| Average absence/resident | Total / resident count | Gauge | ≤ 30 days/year | > 40 days/year |
| Absence rate (%) | Absence days / total possible days | Gauge | ≤ 8% | > 12% |
| Leave balance (by type) | Vacation/medical/deployment breakdown | Gauge | Within policy | Skewed distribution |

**Code Reference:**
- Leave analysis: `backend/app/compliance/reports.py::ComplianceReportGenerator._calculate_leave_utilization()`

### Tier 2: Fairness & Equity Metrics

#### 2.1 Workload Distribution

| Metric | Source | Type | Target | Alert |
|--------|--------|------|--------|-------|
| Fairness index | Gini coefficient analysis | Gauge | ≥ 0.90 | < 0.85 |
| Hours std. deviation | Statistical spread | Gauge | ≤ 5 hrs | > 10 hrs |
| Min/max hours ratio | Max hours / min hours | Ratio | ≤ 1.15x | > 1.25x |
| Preference satisfaction | Granted preferences / requested | Gauge | ≥ 80% | < 70% |

**Code Reference:**
- Fairness schemas: `backend/app/schemas/analytics.py::FairnessTrendReport`

#### 2.2 Equity by Demographics

| Metric | Source | Type | Target | Alert |
|--------|--------|------|--------|-------|
| PGY-level fairness | Fairness index by PGY | Gauge | ≥ 0.88 | < 0.80 |
| Gender distribution in assignments | Male/female split by rotation | Gauge | < 5% difference | > 10% difference |
| Clinical experience balance | Diverse rotation exposure | Gauge | ≥ 90% | < 80% |

### Tier 3: Quality & Educational Metrics

#### 3.1 Rotation Coverage & Learning

| Metric | Source | Type | Target | Alert |
|--------|--------|------|--------|-------|
| Rotation coverage rate | Total assignments / target slots | Gauge | ≥ 95% | < 90% |
| Resident rotation diversity | Unique rotations per resident / total available | Gauge | ≥ 0.85 | < 0.75 |
| Procedure tracking coverage | Procedures logged / program target | Gauge | ≥ 95% | < 85% |
| Faculty-led sessions | Attended / scheduled | Gauge | ≥ 90% | < 80% |

#### 3.2 Educational Quality Indicators

| Metric | Source | Type | Target | Alert |
|--------|--------|------|--------|-------|
| Credentialing completeness | Current credentials / program requirements | Gauge | 100% | < 95% |
| Training expiration alerts | Upcoming expirations detected (30/60/90 days) | Counter | Proactive notification | Zero notice |
| Certification readiness | PGY-X preparedness metrics | Gauge | Varies | Declining |

---

## Real-Time Monitoring & Dashboards

### Dashboard Architecture

The system implements multi-level monitoring via Prometheus metrics and Grafana dashboards:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Monitoring Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │        Residency Scheduler Application                   │   │
│  │  (FastAPI backend with metric instrumentation)          │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐   │
│  │   Prometheus Metrics Collector                           │   │
│  │  (backend/app/core/metrics/collectors.py)              │   │
│  │                                                          │   │
│  │  Metrics:                                               │   │
│  │  - ACGME compliance score (per rule)                    │   │
│  │  - Violations total (by type)                           │   │
│  │  - Schedule generation duration                         │   │
│  │  - Coverage rate (real-time)                            │   │
│  │  - Resilience health (defense levels)                   │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐   │
│  │   Grafana Dashboards                                    │   │
│  │  (backend/app/core/metrics/dashboards.py)              │   │
│  │                                                          │   │
│  │  - Compliance Dashboard                                │   │
│  │  - Performance Dashboard                               │   │
│  │  - Resilience Health                                   │   │
│  │  - Educational Quality                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Dashboard Types

#### 1. Compliance Dashboard
**Primary Users:** Program Director, ACGME Coordinator

**Panels:**
- 80-hour rule compliance (line graph, weekly trend)
- 1-in-7 rule violations (table, by resident)
- Supervision ratio analysis (gauge, real-time)
- Coverage rate (gauge with thresholds)
- Violation timeline (bar chart, by month)
- Compliance rate summary (stat)

**Refresh Rate:** 5 minutes
**Alert Thresholds:**
- Compliance rate < 95% → YELLOW
- Compliance rate < 90% → RED
- Any critical violation → CRITICAL (page)

#### 2. Educational Quality Dashboard
**Primary Users:** Program Director, Associate Program Director

**Panels:**
- Rotation diversity (heatmap, by resident)
- Procedure tracking (progress gauge, per resident)
- Faculty-led session attendance (bar chart)
- Certification status (table, expiring credentials)
- Learning outcome correlations (scatter plot)

#### 3. Workload Distribution Dashboard
**Primary Users:** Scheduler, Fairness Coordinator

**Panels:**
- Fairness index (gauge)
- Hours distribution (histogram)
- By-resident hours (table, sortable)
- Preference satisfaction (pie chart)
- Equity metrics by PGY level (grouped bar)

#### 4. Program Director Executive Dashboard
**Primary Users:** Program Director, Associate Deans

**Panels:**
- Overall compliance status (large stat)
- Key metrics scoreboard (4-metric summary)
- Trend sparklines (12-month view)
- Risk alerts (most urgent 5)
- Improvement actions (status tracker)

### Real-Time Metrics Collection

**Collection Points:**

```python
# Work Hour Validation (triggered after each assignment)
from app.core.metrics import ResilienceMetrics
metrics = ResilienceMetrics()
metrics.update_acgme_score("80_hour_rule", compliance_rate)

# Schedule Generation Completion
metrics.record_schedule_generation(
    algorithm="multi_objective",
    duration_seconds=45.2,
    success=True
)

# Violation Detection (immediate)
metrics.record_violation(
    violation_type="80_hour_violation",
    severity="critical",
    resident_id=resident.id
)

# Coverage Analysis (hourly batch)
metrics.update_coverage_rate(0.97, "residential")
```

**Code Reference:**
- Metrics collection: `backend/app/core/metrics/collectors.py`
- Prometheus instrumentation: `backend/app/core/metrics/prometheus.py`
- Alert configuration: `backend/app/core/metrics/alerts.py`

---

## Site Visit Preparation Checklist

### Pre-Visit Documentation (30-60 days before)

#### Document Audit Trail
```
✓ Compliance audit trail (6-month review minimum)
  - Total violations detected
  - Violations resolved
  - Appeal/override documentation
  - Remediation actions taken

✓ Schedule generation logs
  - Algorithm performance metrics
  - Constraint satisfaction scores
  - Failed generation attempts (and reasons)
  - Solver diagnostic outputs

✓ Resident feedback logs
  - Schedule satisfaction surveys
  - Work hour concerns documented
  - Requested swaps (granted/denied)
  - Special circumstance accommodations

✓ Faculty coordination records
  - Supervision coverage documentation
  - Last-minute coverage changes
  - Absence management procedures
  - Credentialing status
```

#### Prepare Key Reports
```
✓ Compliance Report (full year)
  - 80-hour rule analysis (all residents)
  - 1-in-7 rule analysis (all residents)
  - Supervision ratio analysis (all blocks)
  - Coverage metrics
  - Trend analysis

✓ Educational Quality Report
  - Rotation coverage by resident
  - Procedure tracking results
  - Diversity metrics
  - Learning outcome correlations
  - Faculty engagement summary

✓ Workload Distribution Report
  - Fairness analysis (with supporting data)
  - Hours distribution by PGY level
  - Absence patterns
  - Preference satisfaction metrics

✓ Safety & Wellness Report
  - Burnout indicators (if available)
  - Fatigue risk assessment
  - Leave utilization patterns
  - Support services offered/utilized
```

### During Site Visit

#### Information Systems Demonstration
```
Demonstrate:
1. Compliance monitoring dashboard
   - Real-time metrics visualization
   - Alert escalation procedures
   - Violation tracking mechanisms

2. Schedule generation process
   - Constraint explanation
   - Multi-objective optimization display
   - Fairness validation before release

3. Audit trail capabilities
   - Change logging (who/what/when)
   - Reversal/rollback procedures
   - Compliance check timestamps

4. Reporting system
   - Report generation (on-demand)
   - Trend analysis capabilities
   - Data export for external analysis
```

#### Resident/Faculty Interviews
```
Questions to Support with Data:
1. "How is the program ensuring 80-hour compliance?"
   → Show: Real-time dashboard, compliance rate trend

2. "How are residents kept informed of work hour concerns?"
   → Show: Alert procedures, feedback mechanisms, survey results

3. "How is schedule fairness determined?"
   → Show: Fairness metrics, algorithmic approach, appeals process

4. "What happens if violations are detected?"
   → Show: Remediation procedures, documentation, follow-up

5. "How do residents access the schedule?"
   → Show: Scheduling system interface, mobile access, alert notifications
```

### Post-Visit Documentation

#### Citation Response Framework

**If citation received:**

```
Within 30 days:
1. Root cause analysis
   - What caused the violation?
   - Was it a one-time event or systemic?
   - What was the context?

2. Corrective action plan
   - What will be changed?
   - Who is responsible?
   - What is the timeline?
   - How will compliance be verified?

3. Monitoring plan
   - How will we prevent recurrence?
   - What metrics will be tracked?
   - What is the escalation procedure?

4. Stakeholder communication
   - How will residents/faculty be informed?
   - What education will occur?
   - What feedback mechanisms are in place?
```

**Evidence Collection:**

```
Document:
✓ Before/after comparison (metrics)
✓ Resident acknowledgment of changes
✓ Faculty training documentation
✓ System configuration changes (with timestamps)
✓ Monitoring results (1-3 months post-correction)
✓ Communication records (emails, meeting minutes)
```

**System Support:**

```
Automated Citation Response Support:
- Generate compliance timeline (show improvement)
- Export relevant metrics (before/after)
- Compile change logs (system modifications)
- Prepare evidence package (exportable)
```

---

## Documentation & Audit Trail

### Audit Trail Requirements

The system maintains comprehensive audit trails for ACGME compliance:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Audit Trail Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Schedule Generation Events:                                    │
│  - Algorithm used, parameters, start/end time                  │
│  - Constraint violations detected                              │
│  - Solver diagnostics (time limits, restarts)                  │
│  - Final schedule hash (immutability proof)                    │
│                                                                 │
│  Assignment Changes:                                           │
│  - User/system who made change                                 │
│  - Before/after state                                          │
│  - Reason/justification                                        │
│  - Compliance validation result                                │
│  - Timestamp (UTC)                                             │
│                                                                 │
│  Violation Detection:                                          │
│  - Violation type, severity, details                           │
│  - Resident affected                                           │
│  - Detection method (schedule vs. real-time)                   │
│  - Remediation action taken                                    │
│                                                                 │
│  Compliance Checks:                                            │
│  - Check type, date/time                                       │
│  - Residents checked                                           │
│  - Violations found (count/type)                               │
│  - Report generated (link)                                     │
│                                                                 │
│  Absence Management:                                           │
│  - Absence requested, approved, effective                      │
│  - Coverage plan (who covered)                                 │
│  - Compliance impact assessment                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Compliance Reports Repository

**Report Storage Structure:**

```
reports/
├── compliance/
│   ├── monthly/
│   │   ├── 2025-01-compliance-report.pdf
│   │   ├── 2025-02-compliance-report.pdf
│   │   └── ...
│   ├── quarterly/
│   │   ├── Q1-2025-compliance-summary.pdf
│   │   └── ...
│   └── annual/
│       └── 2025-annual-compliance-review.pdf
├── educational-quality/
│   ├── 2025-procedure-tracking.xlsx
│   ├── 2025-rotation-diversity.xlsx
│   └── ...
├── workload-distribution/
│   ├── fairness-analysis-2025.xlsx
│   └── ...
└── audit/
    ├── compliance-check-log.csv
    ├── violation-timeline.csv
    └── remediation-tracker.csv
```

**Report Generation API:**

```python
# Generate compliance report
from app.compliance.reports import ComplianceReportGenerator

generator = ComplianceReportGenerator(db)
report_data = generator.generate_compliance_data(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
    include_violations_only=False
)

# Export to PDF (for sharing, archival)
pdf_bytes = generator.export_to_pdf(report_data)
with open("2025-compliance-report.pdf", "wb") as f:
    f.write(pdf_bytes)

# Export to Excel (for detailed analysis)
excel_bytes = generator.export_to_excel(report_data)
with open("2025-compliance-data.xlsx", "wb") as f:
    f.write(excel_bytes)
```

---

## Improvement Cycles & Evidence

### Continuous Improvement Framework

**PDCA Model Implementation:**

```
┌─────────────────────────────────────────────────────────────────┐
│              Plan-Do-Check-Act (PDCA) Cycle                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PLAN (Baseline & Goal Setting):                               │
│  ├─ Collect baseline compliance metrics                        │
│  ├─ Define improvement targets                                 │
│  ├─ Identify specific problem areas                            │
│  └─ Design intervention                                        │
│                                                                 │
│  DO (Implementation):                                          │
│  ├─ Execute planned changes                                    │
│  ├─ Document all modifications                                 │
│  ├─ Provide stakeholder education                              │
│  └─ Monitor implementation fidelity                            │
│                                                                 │
│  CHECK (Measurement & Analysis):                               │
│  ├─ Collect outcome metrics                                    │
│  ├─ Compare to baseline and targets                            │
│  ├─ Analyze trend data                                         │
│  └─ Identify any unexpected effects                            │
│                                                                 │
│  ACT (Standardization & Refinement):                           │
│  ├─ Decide whether to sustain changes                          │
│  ├─ Document lessons learned                                   │
│  ├─ Standardize successful practices                           │
│  └─ Identify next improvement opportunity                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Improvement Project Template

```markdown
# Improvement Project: [Name]
Date: [Start Date]
Status: [Plan/Do/Check/Act]

## Problem Statement
- Current state (baseline metrics)
- Gap (target - current)
- Impact (why this matters)

## Root Cause Analysis
- What is causing the problem?
- Evidence supporting the analysis
- Why current approaches aren't working

## Improvement Strategy
- Planned intervention
- Expected outcome
- Key success factors

## Implementation Plan
- Timeline and milestones
- Responsible parties
- Resource needs
- Communication plan

## Measurement & Evidence
- Baseline metrics (collected)
- Target metrics (goal)
- Check frequency (weekly/monthly)
- Data source (system reports)

## Results & Lessons
- Outcome (achieved vs. target)
- Contributing factors
- Unexpected consequences
- Key insights

## Sustainability Plan
- How will this change be sustained?
- Who is responsible for monitoring?
- When will we check compliance?
- What triggers re-evaluation?

## Next Opportunity
- What did we learn?
- What should we improve next?
```

### Quality Improvement Tracking

**Metrics Dashboard:**

| Project | Status | Baseline | Target | Current | Timeline |
|---------|--------|----------|--------|---------|----------|
| Reduce 80-hr violations | Check | 5/month | 0/month | 2/month | Jan-Mar 2025 |
| Improve fairness | Do | 0.87 | 0.92 | 0.89 | Ongoing |
| Increase supervision compliance | Act | 94% | 100% | 99.5% | Jan-Feb 2025 |
| Enhance rotation diversity | Plan | 0.78 | 0.90 | TBD | Feb-Jun 2025 |

---

## Citation Response Procedures

### Violation Detection & Initial Response

**Immediate (< 24 hours):**

```python
# When violation detected
from app.compliance.notifications import ComplianceAlert

violation = ACGMEViolation(
    type="80_hour_violation",
    resident_id=resident_id,
    week_ending=week_end_date,
    hours_worked=82.5,
    severity="critical"
)

# Trigger immediate actions
alert = ComplianceAlert(
    title=f"CRITICAL: Work hour violation for {resident.name}",
    description=f"82.5 hours in week of {week_end_date}",
    recipients=["pd@program.edu", "coordinator@program.edu"],
    severity="critical",
    requires_action=True,
    action_deadline=datetime.utcnow() + timedelta(days=1)
)

await alert.send()
await log_incident(violation, alert)
```

**Documentation:**
- Violation details (what, when, who, why)
- System-generated alert record
- Recipient acknowledgment timestamps
- Initial response actions taken

### 30-Day Remediation Plan

**Week 1 (Days 1-7):**

```
✓ Root cause analysis meeting
  - Review violation circumstances
  - Identify causal factors
  - Assess whether systemic or isolated

✓ Immediate corrective action
  - Adjust schedule for affected resident
  - Redistribute assignments
  - Prevent recurrence in next cycle

✓ Stakeholder notification
  - Resident counseling (supportive)
  - Faculty awareness
  - Program leadership briefing
```

**Week 2-3 (Days 8-21):**

```
✓ Implement systemic improvements
  - Modify scheduling constraints (if needed)
  - Adjust algorithm parameters
  - Update policies/procedures

✓ Monitoring intensification
  - Weekly work hour reports (instead of monthly)
  - Real-time dashboard alerts
  - Compliance spot-checks

✓ Education & training
  - Coordinator retraining
  - Resident education (if needed)
  - Faculty communication
```

**Week 4 (Days 22-30):**

```
✓ Evidence compilation
  - Corrective action taken (documented)
  - Monitoring data (showing improvement)
  - Resident/faculty feedback
  - System configuration changes

✓ Response submission
  - Written response to accreditor
  - Supporting documentation package
  - Commitment to ongoing monitoring

✓ Follow-up plan
  - Continue weekly monitoring (30-60 days)
  - Monthly reports to PD
  - Quarterly review with accreditor
```

### Multi-Violation Crisis Response

**If violations cluster (> 3 in 30 days):**

```
ESCALATION PROTOCOL:

Level 1 (1-2 violations):
├─ Immediate response (documented)
├─ Root cause analysis
└─ Corrective action plan

Level 2 (3+ violations):
├─ Program leadership emergency meeting
├─ Comprehensive system review
├─ Algorithm/policy overhaul
├─ External consultation (if needed)
├─ Interim manual schedule management (fallback)
└─ Weekly accreditor updates

Level 3 (systemic failure):
├─ Contingency execution (predetermined fallback schedule)
├─ Emergency staffing adjustments
├─ Immediate accreditor notification
├─ Legal/compliance team activation
└─ Intensive daily monitoring & response
```

---

## Hidden Evaluation Gaps

### Metrics Currently Under-Measured

#### 1. Procedural Learning & Competency
**Gap:** System tracks time but not clinical competency acquisition

```
Current Metric:
- Procedure count (logged)

Missing Metrics:
- Procedure complexity vs. resident level match
- Supervisor assessment of competency progression
- Correlation between procedure exposure and board pass rates
- Longitudinal skill development tracking
```

**Recommendation:** Integrate ACGME Outcome Project data if available

#### 2. Burnout & Mental Health Indicators
**Gap:** Work hours tracked but not psychological impact

```
Current Metric:
- Work hours compliance

Missing Metrics:
- Burnout scores (validated instruments)
- Sleep quality/fatigue measures
- Mental health resource utilization
- Resident satisfaction/wellness surveys
- Depression/anxiety screening participation
```

**Recommendation:** Implement optional burnout survey integration

#### 3. Educational Outcomes
**Gap:** Schedule generated but learning not measured

```
Current Metric:
- Rotation coverage

Missing Metrics:
- Board examination pass rates
- In-training exam (ITE) scores
- Graduation outcome tracking
- Program-specific learning objectives assessed
- Faculty-rated clinical competency
```

**Recommendation:** Create optional outcome tracking module

#### 4. Patient Safety & Quality
**Gap:** Schedule compliance but clinical safety not measured

```
Current Metric:
- Supervision ratios

Missing Metrics:
- Adverse events per shift
- Near-miss incidents
- Patient satisfaction scores
- Quality metrics (infection rates, error rates)
- Incident report correlation with fatigue
```

**Recommendation:** Develop optional patient safety integration

#### 5. Diversity, Equity & Inclusion
**Gap:** Hours fairness measured but demographic equity not assessed

```
Current Metric:
- Hours distribution (fairness index)

Missing Metrics:
- Rotation access equity (by demographics if tracked)
- Leadership opportunity distribution
- Mentorship parity
- Advancement opportunity equality
- Professional development access
```

**Recommendation:** Implement anonymized demographic tracking (with consent)

### Metrics Not Covered by Current System

#### Clinical Education Quality
- Graduate competency assessments
- Milestones framework progress
- Procedural volume & complexity match

#### Resident Wellness
- Burnout risk assessment
- Psychological safety culture survey
- Sleep tracking integration

#### Outcomes
- Board certification results
- Fellowship placement rates
- Career satisfaction

#### Faculty Development
- Teaching quality evaluation
- Faculty burnout monitoring
- Professional development progress

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-3)

**Deliverables:**
1. Complete compliance reporting suite (PDF/Excel)
   - Monthly compliance reports (automated)
   - Violation tracking dashboard
   - Trend analysis reports

2. Real-time compliance dashboard
   - 80-hour rule monitoring
   - 1-in-7 rule monitoring
   - Supervision ratio monitoring
   - Alert escalation system

3. Audit trail logging
   - Assignment change logging
   - Violation detection logging
   - Report generation logging

**Code Changes Required:**
```
- Enhance ComplianceReportGenerator
- Implement automated report scheduling
- Add Grafana dashboard templates
- Create audit trail database schema
```

### Phase 2: Advanced Monitoring (Months 4-6)

**Deliverables:**
1. Trend analysis & prediction
   - 4-week rolling analysis
   - Violation risk prediction
   - Burnout risk correlation

2. Site visit preparation toolkit
   - Automated checklist generator
   - Evidence package compiler
   - Interview preparation guide

3. Citation response automation
   - Remediation plan generator
   - Evidence collector
   - Response document templates

**Code Changes Required:**
```
- Add trend analysis algorithms
- Implement time-series forecasting
- Create template generation system
- Build evidence package export
```

### Phase 3: Continuous Improvement (Months 7-9)

**Deliverables:**
1. Improvement project framework
   - PDCA cycle templates
   - Metrics baseline calculator
   - Progress tracking dashboard

2. Educational quality metrics
   - Rotation diversity analysis
   - Procedure tracking enhancements
   - Learning outcome correlations

3. Integration with external data sources
   - Optional ITE score import
   - Optional board pass rate tracking
   - Optional patient safety metrics

**Code Changes Required:**
```
- Create improvement tracking database
- Implement quality metric calculations
- Build third-party data integration framework
```

### Phase 4: Enhanced Evaluation (Months 10-12)

**Deliverables:**
1. Comprehensive evaluation report suite
   - Educational quality report
   - Diversity & equity report
   - 5-year trend analysis
   - Benchmarking comparison

2. Advanced dashboards
   - Educational outcomes dashboard
   - DEI metrics dashboard
   - Long-term trend dashboard
   - Predictive risk dashboard

3. External reporting
   - ACGME-ready data packages
   - Research data export (anonymized)
   - Institutional comparison datasets

---

## System Architecture for Evaluation

### Key Components

**1. Compliance Module**
```
Location: backend/app/compliance/
Files:
  - reports.py: Report generation
  - notifications.py: Alert system
  - validator.py: Rule validation
```

**2. Metrics Module**
```
Location: backend/app/core/metrics/
Files:
  - collectors.py: Data collection
  - prometheus.py: Prometheus export
  - dashboards.py: Dashboard definitions
  - alerts.py: Alert configuration
```

**3. Audit Module**
```
Location: backend/app/audit/ (proposed)
Purpose: Change logging and audit trail
Tables:
  - audit_log (all changes)
  - violation_log (compliance violations)
  - remediation_log (corrective actions)
```

**4. Evaluation Module**
```
Location: backend/app/evaluation/ (proposed)
Purpose: Program evaluation framework
Components:
  - evaluation_projects.py: PDCA tracking
  - metrics_baseline.py: Baseline calculations
  - improvement_tracking.py: Progress tracking
  - report_generator.py: Evaluation reports
```

### Data Model Extensions

**Proposed Tables:**

```sql
-- Violation tracking (enhanced)
ALTER TABLE violations ADD COLUMN
  remediation_plan_id UUID,
  remediation_status ENUM ('open', 'in_progress', 'resolved'),
  resolved_date DATE;

-- Audit trail
CREATE TABLE audit_log (
  id UUID PRIMARY KEY,
  entity_type VARCHAR (50),
  entity_id UUID,
  action VARCHAR(50),
  changed_by UUID,
  change_details JSONB,
  change_timestamp TIMESTAMP,
  reason VARCHAR(500)
);

-- Improvement projects
CREATE TABLE evaluation_projects (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  status ENUM ('plan', 'do', 'check', 'act'),
  baseline_metrics JSONB,
  target_metrics JSONB,
  current_metrics JSONB,
  timeline_start DATE,
  timeline_end DATE,
  responsible_person_id UUID,
  created_date TIMESTAMP,
  updated_date TIMESTAMP
);

-- Compliance check results
CREATE TABLE compliance_checks (
  id UUID PRIMARY KEY,
  check_type VARCHAR(50),
  check_date DATE,
  residents_checked INT,
  violations_found INT,
  report_url VARCHAR(255),
  performed_by UUID,
  created_timestamp TIMESTAMP
);
```

---

## Conclusion

This comprehensive ACGME Program Evaluation Framework provides:

1. **Real-Time Compliance Monitoring** - Detect violations immediately with automated alerts
2. **Comprehensive Metrics Tracking** - Measure compliance, fairness, coverage, and educational quality
3. **Site Visit Ready Documentation** - Automated report generation and evidence compilation
4. **Continuous Improvement Support** - PDCA framework integration with progress tracking
5. **Citation Response Procedures** - Structured remediation and escalation protocols
6. **Gap Identification** - Recognition of metrics not yet covered by the system

The system is designed to be:
- **Transparent**: All metrics visible to stakeholders
- **Auditable**: Complete change and violation logging
- **Responsive**: Real-time alerts for compliance issues
- **Compliant**: Aligned with ACGME accreditation requirements
- **Continuous**: Built-in improvement cycle support

---

## Appendix A: Metric Definitions

### ACGME Compliance Metrics

**80-Hour Rule Compliance Rate**
- Definition: Percentage of residents in rolling 4-week periods with ≤80 hours/week average
- Calculation: (Residents with ≤80 hrs / Total residents) × 100%
- Target: 100%
- Alert: < 95%

**1-in-7 Rule Compliance Rate**
- Definition: Percentage of 7-day windows where residents had ≥24 hours off
- Calculation: (7-day windows with adequate rest / Total 7-day windows) × 100%
- Target: 100%
- Alert: < 95%

**Supervision Compliance Rate**
- Definition: Percentage of clinical blocks meeting ACGME supervision ratios
- Calculation: (Blocks with adequate faculty / Total blocks) × 100%
- Target: 100%
- Alert: < 98%

### Fairness Metrics

**Fairness Index**
- Definition: Gini coefficient of work hours distribution (0=perfect equality, 1=perfect inequality)
- Formula: (2 × Σ(i × hours_i)) / (n × Σ hours_i) - (n+1)/n
- Target: ≤ 0.10 (high fairness = low inequality)
- Alert: > 0.15

**Preference Satisfaction Rate**
- Definition: Percentage of resident scheduling preferences granted
- Calculation: (Granted preferences / Total preferences requested) × 100%
- Target: ≥ 80%
- Alert: < 70%

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Next Review:** 2025-06-30
