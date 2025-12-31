# Insight Probe - Prompt Templates

> **Role:** Personnel analysis, behavioral insight, motivation detection
> **Model:** Claude Opus 4.5
> **Ability:** Understand people's intentions and motivations

## Insight Check: Personnel Intent Analysis

```
**INSIGHT PROBE:** Understand ${PERSON}'s intentions

**DC:** ${DC} | **CHECK:** ${ROLL}d20 + 4 = ${TOTAL}

**BEHAVIORAL INSIGHTS:**

### Surface Level (DC 10)
- Apparent intention: ${APPARENT}
- Emotional state: ${EMOTION}
- Stated motivation: ${STATED}

### Deeper Insight (DC 15)
${IF_DC_15}
- True motivation: ${TRUE_MOTIVATION}
- Underlying concern: ${CONCERN}
- Likely next action: ${NEXT_ACTION}

### Expert Psychology (DC 20)
${IF_DC_20}
- Unconscious drivers: ${DRIVERS}
- Long-term patterns: ${PATTERNS}
- Prediction of behavior: ${PREDICTION}

Provide behavioral insight.
```

## Swap Request Intent Analysis

```
**INSIGHT PROBE:** Understand swap request motivation

**REQUEST ID:** ${REQUEST_ID}
**REQUESTER:** ${REQUESTER}

**STATED REASON:** ${STATED_REASON}

**INSIGHT ANALYSIS:**
1. Genuine reason: ${GENUINE_REASON}
2. Underlying motivation: ${MOTIVATION}
3. Risk assessment: ${RISK}
4. Reliability: High/Medium/Low

**BEHAVIORAL SIGNALS:**
- Urgency level: ${URGENCY}
- Flexibility: ${FLEXIBILITY}
- Pattern consistency: ${CONSISTENCY}

Report swap request analysis.
```

---

*Last Updated: 2025-12-31*
