# Survival Probe - Prompt Templates

> **Role:** Contingency planning, resource management, crisis preparation
> **Model:** Claude Opus 4.5
> **Ability:** Survive in harsh conditions and manage resources

## Survival Check: Crisis Survival Analysis

```
**SURVIVAL PROBE:** How long can system survive under stress?

**DC:** ${DC} | **CHECK:** ${ROLL}d20 + 4 = ${TOTAL}

**SURVIVAL ASSESSMENT:**

### Basic Survival (DC 10)
- Time before critical failure: ${TIME_CRITICAL}
- Essential resources identified: ${RESOURCES}
- Minimum viable operations: ${MINIMUM}

### Extended Survival (DC 15)
${IF_DC_15}
- Time to exhausted backup plans: ${TIME_EXTENDED}
- Resource conservation strategies: ${CONSERVATION}
- Triage priorities: ${TRIAGE}

### Expert Survival (DC 20)
${IF_DC_20}
- Maximum sustainable duration: ${MAX_DURATION}
- Recovery from worst-case scenario: ${RECOVERY}
- Optimal survival strategy: ${OPTIMAL_STRATEGY}

Analyze survival prospects.
```

## Schedule Contingency Survival

```
**SURVIVAL PROBE:** Can schedule survive disruptions?

**SCENARIO:** Loss of ${LOSS_SCENARIO}

**SURVIVAL ANALYSIS:**
- Time to schedule collapse: ${TIME_TO_COLLAPSE}
- Coverage maintained at: ${COVERAGE_MAINTAINED}%
- Personnel burden: ${BURDEN}

**SURVIVAL RESOURCES:**
- Backup coverage available: ${BACKUP}
- Alternative personnel: ${ALTERNATIVES}
- Emergency protocols: ${PROTOCOLS}

**SURVIVAL TIMELINE:**
- Immediate (hours): ${IMMEDIATE}
- Short-term (days): ${SHORT_TERM}
- Long-term (weeks): ${LONG_TERM}

**SURVIVAL VERDICT:**
- System survives: ${SURVIVES}
- Recovery possible: ${RECOVERABLE}
- Estimated recovery time: ${RECOVERY_TIME}

Report survival probability.
```

---

*Last Updated: 2025-12-31*
