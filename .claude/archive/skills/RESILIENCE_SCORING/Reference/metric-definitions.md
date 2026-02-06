# Reference: Metric Definitions

## Overview

This document defines all resilience metrics used in the RESILIENCE_SCORING skill. Each metric has a clear formula, interpretation range, and examples.

---

## Core Health Score Components

### Overall Health Score

**Formula:**
```
Health Score = 0.4 × Coverage + 0.3 × Margin + 0.3 × Continuity
```

**Range:** [0, 1]

**Interpretation:**
- **1.0**: Perfect score (unrealistic in practice)
- **0.85-1.0**: Excellent - Robust schedule with high margins
- **0.70-0.84**: Good - Acceptable resilience, some slack
- **0.50-0.69**: Fair - Tight margins, increased monitoring needed
- **0.30-0.49**: Poor - Vulnerable to failures, daily monitoring
- **0.0-0.29**: Critical - Collapse imminent, emergency intervention

**Rationale for Weights:**
- **Coverage (40%)**: Most important - directly measures whether rotations are staffed
- **Margin (30%)**: ACGME compliance buffer (regulatory requirement)
- **Continuity (30%)**: Resident experience and learning quality

---

## Component Metrics

### 1. Coverage Component

**Definition:** Measures rotation staffing adequacy relative to minimum requirements.

**Formula (per rotation):**
```
coverage_ratio = actual_residents / required_residents
normalized_coverage = min(coverage_ratio, 1.5) / 1.5
```

**Aggregation:**
```
coverage_component = mean(normalized_coverage for all rotations)
```

**Range:** [0, 1]

**Interpretation:**
- **1.0**: All rotations at 150%+ of minimum (excellent buffer)
- **0.67**: All rotations at exactly minimum staffing (tight, no buffer)
- **0.50**: Average rotation at 75% of minimum (understaffed)
- **<0.67**: Warning threshold - rotations understaffed

**Example:**

| Rotation | Required | Actual | Ratio | Normalized | Coverage Score |
|----------|----------|--------|-------|------------|----------------|
| EM Night | 2 | 3 | 1.5 | 1.0 | 1.0 |
| Peds Clinic | 4 | 4 | 1.0 | 0.67 | 0.67 |
| OB/GYN Call | 2 | 1 | 0.5 | 0.33 | 0.33 |
| **Average** | - | - | - | - | **0.67** |

**Why Cap at 1.5?**
Overstaffing beyond 150% provides diminishing resilience returns and wastes resources.

---

### 2. Margin Component

**Definition:** Measures constraint slack - how close residents are to ACGME work hour limits.

**Formula (per resident):**
```
work_hours_4week = sum(hours worked in rolling 4-week window)
max_hours_4week = 80 × 4 = 320 hours
slack_hours = max_hours_4week - work_hours_4week
margin_ratio = slack_hours / max_hours_4week
```

**Aggregation:**
```
margin_component = mean(margin_ratio for all residents)
```

**Range:** [0, 1]

**Interpretation:**
- **1.0**: Residents averaging 0 hours/week (impossible in practice)
- **0.75**: Residents averaging 20 hours/week (very light load)
- **0.50**: Residents averaging 40 hours/week (moderate load, good margin)
- **0.25**: Residents averaging 60 hours/week (heavy load, low slack)
- **0.0**: Residents at 80-hour limit (zero slack, critical)
- **<0.30**: Warning threshold - approaching ACGME limits

**Example:**

| Resident | 4-Week Hours | Slack Hours | Margin Ratio |
|----------|--------------|-------------|--------------|
| PGY1-01 | 240 | 80 | 0.25 |
| PGY2-03 | 280 | 40 | 0.125 |
| PGY3-01 | 200 | 120 | 0.375 |
| **Average** | - | - | **0.25** |

**Additional Margin Metrics:**

#### 1-in-7 Margin
```
days_since_last_24h_off = current_date - last_off_date
margin_1in7 = max(0, 7 - days_since_last_24h_off) / 7
```

#### Call Frequency Margin
```
calls_per_month = count(call_assignments in month)
max_calls_per_month = 7  # Typical maximum
margin_call_freq = max(0, max_calls_per_month - calls_per_month) / max_calls_per_month
```

---

### 3. Continuity Component

**Definition:** Measures rotation stability - fewer mid-block switches = better continuity.

**Formula (per resident):**
```
mid_block_switches = count(rotation changes not on block boundary)
expected_blocks = evaluation_days / 14  # Assuming 2-week blocks
continuity_ratio = 1.0 - (mid_block_switches / expected_blocks)
```

**Aggregation:**
```
continuity_component = mean(max(continuity_ratio, 0) for all residents)
```

**Range:** [0, 1]

**Interpretation:**
- **1.0**: Zero mid-block switches (ideal)
- **0.8**: 20% of blocks have mid-block switch (acceptable)
- **0.5**: 50% of blocks have switch (chaotic, poor learning)
- **<0.70**: Warning threshold - excessive disruption

**Example:**

| Resident | Blocks | Mid-Block Switches | Continuity Ratio |
|----------|--------|-------------------|------------------|
| PGY1-01 | 8 | 0 | 1.0 |
| PGY2-03 | 8 | 2 | 0.75 |
| PGY3-01 | 8 | 4 | 0.50 |
| **Average** | - | - | **0.75** |

**Why Continuity Matters:**
- Pedagogical: Learning requires sustained rotation immersion
- Operational: Mid-block switches increase handoff errors
- Wellness: Frequent switches increase cognitive load and stress

---

## N-1 Analysis Metrics

### Critical Resident

**Definition:** A resident whose absence causes at least one rotation to fall below minimum staffing.

**Formula:**
```
For resident R:
  For each rotation:
    coverage_after_removal = (actual_residents - 1) / required_residents
    if coverage_after_removal < 1.0:
      R is CRITICAL
```

**Classification:**
- **Critical**: Absence causes coverage failure (coverage < 1.0)
- **High-Impact**: Absence causes significant redistribution (>10 hours/week added to others)
- **Low-Impact**: Absence absorbed with minimal redistribution (<10 hours/week)

### Understaffing Hours

**Definition:** Total hours where rotation is below minimum staffing due to absence.

**Formula:**
```
understaffing_hours = sum(
  (required_residents - actual_residents_after_absence) × 24 × days_affected
  for each understaffed rotation
)
```

**Example:**
```
Rotation: EM Night Shift
Required: 2 residents
Actual after PGY2-03 absent: 1 resident
Shortfall: 1 resident
Duration: 7 days
Understaffing hours = 1 × 24 × 7 = 168 hours
```

### Recovery Time Estimate

**Definition:** Time required to restore coverage after a disruption.

**Formula:**
```
if failed_rotations:
  recovery_days = max(days_affected for each failed rotation)
elif residents_needing_reassignment:
  recovery_days = 1  # Internal shuffle only
else:
  recovery_days = 0  # Fully absorbed
```

**Factors Affecting Recovery:**
- Credentialing time for supplemental staff (24-48 hours)
- Notification time for residents (2-4 hours)
- Rotation complexity (specialty rotations take longer to cover)

---

## Multi-Failure Metrics

### Collapse Probability

**Definition:** Probability that schedule fails (cannot maintain coverage) under multi-failure scenarios.

**Formula:**
```
collapse_probability = count(trials with coverage failure) / total_trials
```

**Range:** [0, 1]

**Interpretation:**
- **< 0.05**: Excellent resilience
- **0.05-0.10**: Acceptable risk
- **0.10-0.20**: High risk, mitigation recommended
- **> 0.20**: Unacceptable, do not deploy

### Time-to-Failure

**Definition:** Days until first coverage failure occurs after disruption.

**Formula:**
```
time_to_failure = min(days_below_minimum for each failed rotation)
```

**Statistics:**
- **Median TTF**: 50th percentile (half of failures occur within this time)
- **95th Percentile TTF**: Worst-case scenario (95% of failures occur within this time)

**Example:**
```
Monte Carlo Results (10,000 trials):
  - Median TTF: 4.2 days (50% of multi-failures cause collapse within 4.2 days)
  - 95th %ile TTF: 1.1 days (worst-case collapses within 1.1 days)
```

### Impact Score

**Definition:** Quantitative measure of disruption severity.

**Formula:**
```
impact_score = 0
for each failed rotation:
  impact_score += shortfall × days_affected × 10

for each ACGME violation:
  impact_score += (hours - 80) × 2

if cascading_failures (>3 rotations):
  impact_score *= 1.5
```

**Range:** [0, ∞)

**Interpretation:**
- **< 50**: Minor impact, easily absorbed
- **50-150**: Moderate impact, mitigation needed
- **150-300**: Major impact, significant disruption
- **> 300**: Critical impact, schedule collapse

**Example:**
```
Scenario: PGY2-03 and PGY3-01 absent for 7 days

Failed Rotations:
  - EM Night: shortfall=1, days=7 → 1 × 7 × 10 = 70
  - Peds Clinic: shortfall=1, days=7 → 1 × 7 × 10 = 70

ACGME Violations:
  - PGY2-05: 85 hours → (85 - 80) × 2 = 10

Impact Score = 70 + 70 + 10 = 150 (Major Impact)
```

### Fragile Rotation Failure Rate

**Definition:** Percentage of multi-failure scenarios where a rotation fails.

**Formula:**
```
failure_rate = count(scenarios where rotation failed) / total_scenarios
```

**Severity Classification:**
- **CRITICAL** (>50%): Single point of failure, must address
- **HIGH** (25-50%): Significant vulnerability
- **MEDIUM** (10-25%): Moderate risk
- **LOW** (<10%): Acceptable resilience

---

## Recovery Planning Metrics

### Recovery Time (Hours)

**Definition:** Estimated time to restore full coverage after disruption.

**Components:**
```
recovery_time = notification_time + credentialing_time + orientation_time + deployment_time
```

**Typical Values:**
- **Internal redistribution**: 24 hours (notification + processing)
- **Supplemental staff**: 32-48 hours (credentialing + orientation)
- **Cross-training**: 24 hours (notification + handoff)

### Cost Estimate

**Definition:** Financial cost of recovery strategy.

**Formula:**
```
cost = supplemental_staff_count × weekly_rate × (duration_weeks)
```

**Typical Rates:**
- **Supplemental physician**: $1,000-2,000/week
- **Internal redistribution**: $0 (no additional cost)
- **Cross-training**: $0 (assuming pre-trained)

---

## Historical Tracking Metrics

### Health Score Trend

**Definition:** Change in health score over time.

**Formula:**
```
trend_30day = (health_score_today - health_score_30days_ago) / 30
```

**Interpretation:**
- **Positive trend**: Schedule resilience improving
- **Negative trend**: Schedule resilience degrading
- **Stable**: No significant change

### Seasonal Adjustment

**Definition:** Expected health score variation by season.

**Seasonal Factors:**
- **Deployment Season (Jun-Aug)**: -0.10 to -0.15 (residents on TDY/deployment)
- **Flu Season (Nov-Feb)**: -0.05 to -0.10 (increased illness absences)
- **Academic Year Start (Jul)**: -0.15 (PGY-1 onboarding, less experienced)

**Adjusted Health Score:**
```
adjusted_health = raw_health + seasonal_adjustment
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Baseline** | Schedule state before simulated disruption |
| **Block** | 2-week rotation period (typically) |
| **Cascading Failure** | Failure in one rotation causes failures in others |
| **Collapse** | Schedule cannot maintain minimum coverage for any rotation |
| **Coverage** | Number of residents assigned to a rotation |
| **Critical Resident** | Single point of failure (absence causes coverage failure) |
| **Margin** | Distance from constraint limit (e.g., 60 hours vs 80-hour limit = 20-hour margin) |
| **Monte Carlo** | Statistical simulation using random sampling |
| **N-1 Failure** | Single resident absent |
| **N-2 Failure** | Two residents absent simultaneously |
| **Resilience** | Schedule's ability to withstand and recover from disruptions |
| **Slack** | Unused capacity (e.g., resident at 60 hours/week has 20 hours of slack) |
| **Time-to-Failure** | Days until schedule collapses after disruption |
| **Time-to-Recovery** | Days to restore full coverage after disruption |

---

## Metric Calculation Examples

### Example 1: Compute Health Score

**Given:**
- 5 rotations: 4 at 100% coverage, 1 at 150% coverage
- 10 residents: Average 60 hours/week (margin = 0.25)
- Continuity: 80% of blocks stable (0.2 switches per block)

**Calculation:**
```
coverage = (4×0.67 + 1×1.0) / 5 = 0.736
margin = 0.25
continuity = 0.80

health = 0.4×0.736 + 0.3×0.25 + 0.3×0.80
       = 0.294 + 0.075 + 0.240
       = 0.609 (FAIR)
```

### Example 2: Classify Resident via N-1 Analysis

**Given:**
- Resident PGY2-03 assigned to EM Night Shift
- EM Night requires 2 residents, currently has 2
- If PGY2-03 absent: EM Night drops to 1 resident (50% coverage)

**Classification:**
```
coverage_after_removal = 1 / 2 = 0.5 < 1.0
→ PGY2-03 is CRITICAL
```

### Example 3: Compute Collapse Probability

**Given:**
- Monte Carlo: 10,000 trials of 2-3 simultaneous absences
- 1,234 trials resulted in coverage failure

**Calculation:**
```
collapse_probability = 1234 / 10000 = 0.1234 = 12.34%
→ HIGH RISK (exceeds 10% threshold)
```

---

*This reference document provides the mathematical foundation for all resilience scoring metrics.*
