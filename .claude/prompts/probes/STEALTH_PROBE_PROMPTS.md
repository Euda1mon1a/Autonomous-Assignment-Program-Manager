# Stealth Probe - Prompt Templates

> **Role:** Covert analysis, hidden vulnerability detection, security assessment
> **Model:** Claude Opus 4.5
> **Ability:** Move unseen, find hidden threats and vulnerabilities

## Stealth Check: Hidden Vulnerability Discovery

```
**STEALTH PROBE:** Uncover hidden vulnerabilities

**DC:** ${DC} | **CHECK:** ${ROLL}d20 + 4 = ${TOTAL}

**HIDDEN DISCOVERIES:**

### Obvious Weak Points (DC 10)
- Visible vulnerability 1: ${VUL_1}
- Visible vulnerability 2: ${VUL_2}
- Obvious attack vector: ${VECTOR}

### Well-Hidden Issues (DC 15)
${IF_DC_15}
- Subtle vulnerability: ${SUBTLE_VUL}
- Indirect attack path: ${INDIRECT_PATH}
- Hidden dependency: ${DEPENDENCY}

### Masterful Infiltration (DC 20)
${IF_DC_20}
- Expertly hidden flaw: ${HIDDEN_FLAW}
- Multi-stage attack chain: ${ATTACK_CHAIN}
- Systemic weakness: ${SYSTEMIC}

Discover hidden vulnerabilities.
```

## Security Posture Assessment

```
**STEALTH PROBE:** Assess security posture covertly

**ASSESSMENT SCOPE:** ${SCOPE}

**VISIBLE SECURITY MEASURES:**
- Authentication: ${AUTH_VISIBLE}
- Authorization: ${AUTHZ_VISIBLE}
- Audit logging: ${AUDIT_VISIBLE}

**HIDDEN SECURITY ISSUES:**
- Bypasses found: ${BYPASSES}
- Default credentials: ${DEFAULTS}
- Unpatched vulnerabilities: ${UNPATCHED}

**ATTACK SURFACE:**
- Entry points: ${ENTRY_POINTS}
- Escalation paths: ${ESCALATION}
- Data exfiltration routes: ${EXFIL}

**SECURITY RATING:** ${SECURITY_RATING}/10

**CRITICAL GAPS:**
${CRITICAL_GAPS}

**RECOMMENDED HARDENING:**
${HARDENING}

Report security assessment.
```

## Covert Monitoring Analysis

```
**STEALTH PROBE:** Monitor system without detection

**MONITORING OBJECTIVE:** ${OBJECTIVE}

**SURVEILLANCE CAPABILITIES:**
- Data gathering: ${DATA_GATHERING}%
- Pattern analysis: ${PATTERN_ANALYSIS}%
- Undetected operations: ${UNDETECTED}%

**MONITORED ACTIVITIES:**
1. Personnel movements: ${PERSONNEL}
2. Data access patterns: ${DATA_ACCESS}
3. Communication flows: ${COMMS}
4. Resource usage: ${RESOURCES}

**FINDINGS:**
${FINDINGS}

**DETECTION RISK:**
- Probability of detection: ${DETECTION_RISK}%
- Time before discovery: ${TIME_BEFORE_DISCOVERY}
- Countermeasure effectiveness: ${COUNTERMEASURE}%

Report covert monitoring results.
```

---

*Last Updated: 2025-12-31*
