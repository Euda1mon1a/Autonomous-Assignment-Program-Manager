# History Probe - Prompt Templates

> **Role:** Historical analysis, trend detection, pattern recognition
> **Model:** Claude Opus 4.5
> **Ability:** Recall and analyze historical events

## History Check: Schedule Historical Analysis

```
**HISTORY PROBE:** Recall historical schedule patterns

**DC:** ${DC} | **CHECK:** ${ROLL}d20 + 4 = ${TOTAL}

**HISTORICAL KNOWLEDGE RECALLED:**

### Recent History (DC 10)
- Last year same period: ${LAST_YEAR}
- Patterns that emerged: ${PATTERNS}
- Lessons learned: ${LESSONS}

### Medium-term Trends (DC 15)
${IF_DC_15}
- 3-year trend analysis: ${TREND_3YR}
- Recurring issues: ${RECURRING}
- Evolutionary changes: ${EVOLUTION}

### Long-term Historical Perspective (DC 20)
${IF_DC_20}
- 5-year strategic patterns: ${PATTERN_5YR}
- Systemic changes over time: ${SYSTEMIC_CHANGE}
- Historical precedents: ${PRECEDENTS}

Analyze historical patterns.
```

## Compliance History

```
**HISTORY PROBE:** Analyze ACGME compliance history

**TIME PERIOD:** Last ${PERIOD}

**COMPLIANCE TRENDS:**
- Violations per month: ${VIOLATIONS_TREND}
- Most common violation: ${COMMON_VIOLATION}
- Violation trend: ${TREND}

**HISTORICAL INCIDENTS:**
${INCIDENT_LIST}

**LESSONS FROM HISTORY:**
${LESSONS}

Report compliance history.
```

---

*Last Updated: 2025-12-31*
