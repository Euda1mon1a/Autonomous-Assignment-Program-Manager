# Perception Probe - Prompt Templates

> **Role:** Visual analysis, pattern detection, data profiling
> **Model:** Claude Opus 4.5
> **Ability:** Notice important details

## 1. VISUAL ANALYSIS TEMPLATE

```
**PERCEPTION CHECK:** Visual Analysis of ${TARGET}

**PERCEPTION DC:** ${DC}
**CHECK RESULT:** ${ROLL}d20 + 4 = ${TOTAL}

**WHAT YOU NOTICE:**

### Immediate Observations (DC 10)
- ${OBSERVATION_1}
- ${OBSERVATION_2}
- ${OBSERVATION_3}

### Keen Observations (DC 15)
${SUCCESS_15_OR_HIGHER}
- ${OBSERVATION_4}
- ${OBSERVATION_5}

### Critical Details (DC 20)
${SUCCESS_20_OR_HIGHER}
- ${OBSERVATION_6}
- ${OBSERVATION_7}

**HIDDEN DETAILS DISCOVERED:**
${HIDDEN_IF_ROLL_PASSES}

Conduct visual analysis and report findings.
```

## 2. SCHEDULE PATTERN ANALYSIS TEMPLATE

```
**PERCEPTION PROBE:** Identify patterns in schedule data

**DATA ANALYZED:** ${SCHEDULE_ID}
**PATTERN SCAN SCOPE:** ${SCOPE}

**OBVIOUS PATTERNS (immediately visible):**
- Pattern 1: ${PATTERN_1} (frequency: ${FREQ_1})
- Pattern 2: ${PATTERN_2} (frequency: ${FREQ_2})
- Pattern 3: ${PATTERN_3} (frequency: ${FREQ_3})

**SUBTLE PATTERNS (requires DC 15 perception):**
- Pattern 4: ${PATTERN_4} (relationship: ${REL_4})
- Pattern 5: ${PATTERN_5} (trend: ${TREND_5})

**ANOMALIES DETECTED:**
- Anomaly 1: ${ANOMALY_1} (appears ${COUNT_1} times)
- Anomaly 2: ${ANOMALY_2} (appears ${COUNT_2} times)

**IMPLICATIONS:**
${IMPLICATIONS}

Report detected patterns.
```

## 3. METRICS DASHBOARD TEMPLATE

```
**PERCEPTION PROBE:** Key metrics at a glance

**SCHEDULE HEALTH:**
- Coverage: ${COVERAGE}% [████████░░] Status: ${STATUS}
- Compliance: ${COMPLIANCE}% [██████████] Status: ${STATUS}
- Balance: ${BALANCE_SCORE}% [████████░░] Status: ${STATUS}

**PERSONNEL STATUS:**
- Roster strength: ${ROSTER_STRENGTH}% (${FILLED}/${AUTHORIZED})
- At capacity: ${AT_CAPACITY}% (overcommitted: ${OVERCOMMITTED}%)
- At risk: ${AT_RISK}% (retention risk high)

**SYSTEM HEALTH:**
- API uptime: ${UPTIME}%
- Database response: ${DB_RESPONSE}ms (p95)
- Solver health: ${SOLVER_HEALTH}%

**ALERTS:**
- 🔴 Critical: ${CRITICAL_COUNT}
- 🟠 High: ${HIGH_COUNT}
- 🟡 Medium: ${MEDIUM_COUNT}

**TREND INDICATORS:**
- Coverage trend: ${COVERAGE_TREND} ${ARROW}
- Compliance trend: ${COMPLIANCE_TREND} ${ARROW}
- Utilization trend: ${UTIL_TREND} ${ARROW}

Report metrics overview.
```

## 4. ANOMALY SPOTTING TEMPLATE

```
**PERCEPTION PROBE:** Spot anomalies in data

**DATA SOURCE:** ${DATA_SOURCE}
**BASELINE:** Last ${BASELINE_DAYS} days
**SCAN PERIOD:** ${SCAN_PERIOD}

**DETECTED ANOMALIES:**

### Assignment Anomalies
- Multiple assignments in same time: ${CONFLICT_COUNT}
- Unusual rotation patterns: ${UNUSUAL_COUNT}
- Credential mismatches: ${MISMATCH_COUNT}

### Workload Anomalies
- Spike in hours: ${SPIKE_COUNT}
- Unusual absences: ${ABSENCE_SPIKES}
- Leave pattern changes: ${LEAVE_CHANGES}

### System Anomalies
- Query performance degradation: ${PERF_DEGRADE}
- Cache misses spiking: ${CACHE_ANOMALY}
- Error rate increase: ${ERROR_SPIKE}

**CONFIDENCE LEVELS:**
- High confidence anomalies: ${HIGH_CONF}
- Medium confidence: ${MED_CONF}
- Low confidence: ${LOW_CONF}

Identify and report anomalies.
```

## 5. COMPARATIVE ANALYSIS TEMPLATE

```
**PERCEPTION PROBE:** Compare current state to baseline

**COMPARISON:**
- Current schedule: ${CURRENT_ID}
- Baseline schedule: ${BASELINE_ID}
- Difference period: ${PERIOD}

**KEY DIFFERENCES:**

### Personnel Changes
- New assignments: ${NEW_COUNT}
- Removed assignments: ${REMOVED_COUNT}
- Changed assignments: ${CHANGED_COUNT}
- Net change: ${NET_CHANGE}%

### Metrics Changes
- Coverage change: ${COVERAGE_CHANGE}% (was ${BASELINE_COVERAGE}%)
- Compliance change: ${COMPLIANCE_CHANGE}
- Balance improvement: ${BALANCE_CHANGE}

### Rotation Distribution
- Rotation A distribution: ${ROT_A_CHANGE}
- Rotation B distribution: ${ROT_B_CHANGE}
- Most affected rotation: ${MOST_AFFECTED}

**STATISTICAL SIGNIFICANCE:**
- Chi-square test p-value: ${P_VALUE}
- Significant change: ${SIGNIFICANT}

Report comparative analysis.
```

---

*Last Updated: 2025-12-31*
*Agent: Perception Probe*
*Version: 1.0*
