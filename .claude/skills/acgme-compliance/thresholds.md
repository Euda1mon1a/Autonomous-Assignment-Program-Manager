# ACGME Compliance Thresholds

Configurable warning and violation thresholds for proactive monitoring.

## Hours Thresholds

| Metric | Green | Yellow (Warning) | Red (Violation) |
|--------|-------|------------------|-----------------|
| Weekly Hours (4-wk avg) | ≤ 70 | 71-79 | ≥ 80 |
| Single Week Hours | ≤ 75 | 76-84 | ≥ 85 |
| Consecutive Days | ≤ 5 | 6 | ≥ 7 |
| Shift Length | ≤ 16h | 17-24h | > 24h |
| Time Between Shifts | ≥ 10h | 8-9h | < 8h |

## Supervision Thresholds

| Level | Green | Yellow | Red |
|-------|-------|--------|-----|
| PGY-1 Ratio | ≤ 1.5:1 | 1.5-2:1 | > 2:1 |
| PGY-2+ Ratio | ≤ 3:1 | 3-4:1 | > 4:1 |
| Night Coverage | 2+ faculty | 1 faculty | 0 faculty |

## Utilization Thresholds

Based on queuing theory (80% rule):

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Faculty Utilization | ≤ 70% | 71-80% | > 80% |
| Resident Utilization | ≤ 75% | 76-85% | > 85% |
| System Capacity | ≤ 80% | 81-90% | > 90% |

## Early Warning Signals

Monitor these leading indicators:

1. **Creeping Hours**: 3+ weeks trending upward
2. **Swap Velocity**: Unusual increase in swap requests
3. **Coverage Gaps**: Unfilled slots > 48h out
4. **Concentration**: Same person filling multiple gaps

## Threshold Configuration

These thresholds can be adjusted in:
```
backend/app/scheduling/acgme_validator.py
```

Environment variables:
```bash
ACGME_HOURS_WARNING=75
ACGME_HOURS_VIOLATION=80
ACGME_SUPERVISION_PGY1_MAX=2
ACGME_SUPERVISION_PGY2_MAX=4
```
