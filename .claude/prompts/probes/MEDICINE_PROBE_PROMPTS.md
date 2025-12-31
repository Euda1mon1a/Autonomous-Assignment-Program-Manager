# Medicine Probe - Prompt Templates

> **Role:** Health diagnosis, problem detection, healing recommendations
> **Model:** Claude Opus 4.5
> **Ability:** Diagnose system health and recommend treatments

## Medicine Check: System Health Diagnosis

```
**MEDICINE PROBE:** Diagnose system health status

**DC:** ${DC} | **CHECK:** ${ROLL}d20 + 4 = ${TOTAL}

**DIAGNOSIS FINDINGS:**

### Vital Signs (DC 10)
- System pulse: ${PULSE} (API response time)
- Respiration: ${RESPIRATION} (throughput)
- Temperature: ${TEMPERATURE} (CPU usage)
- Overall health: ${HEALTH}

### Detailed Examination (DC 15)
${IF_DC_15}
- Underlying condition: ${CONDITION}
- Severity assessment: ${SEVERITY}
- Prognosis: ${PROGNOSIS}

### Expert Diagnosis (DC 20)
${IF_DC_20}
- Root disease: ${ROOT_DISEASE}
- Recommended treatment: ${TREATMENT}
- Recovery timeline: ${TIMELINE}

Diagnose system health.
```

## Personnel Health Analysis

```
**MEDICINE PROBE:** Analyze personnel burnout health

**ASSESSMENT:** Personnel wellness status

**VITAL SIGNS BY PERSON:**
- Person A: Stress level ${STRESS_A}, Burnout risk ${RISK_A}
- Person B: Stress level ${STRESS_B}, Burnout risk ${RISK_B}
- Person C: Stress level ${STRESS_C}, Burnout risk ${RISK_C}

**POPULATION HEALTH:**
- Average stress level: ${AVG_STRESS}
- Burnout prevalence: ${PREVALENCE}%
- At-risk population: ${AT_RISK}%

**TREATMENT RECOMMENDATIONS:**
- Immediate intervention: ${IMMEDIATE}
- Preventive measures: ${PREVENTIVE}
- Wellness programs: ${PROGRAMS}

**HEALING TIMELINE:**
- Expected recovery: ${RECOVERY_TIME}
- Monitoring frequency: ${MONITORING}

Report personnel health analysis.
```

---

*Last Updated: 2025-12-31*
