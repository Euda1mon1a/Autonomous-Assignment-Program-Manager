# Investigation Probe - Prompt Templates

> **Role:** Deep analysis, evidence gathering, root cause analysis
> **Model:** Claude Opus 4.5
> **Ability:** Gather clues and dig deeper

## Investigation Check: Incident Analysis

```
**INVESTIGATION PROBE:** Analyze ${INCIDENT_TYPE}

**DC:** ${DC} | **CHECK:** ${ROLL}d20 + 4 = ${TOTAL}

**INVESTIGATION FINDINGS:**

### Surface Level (DC 10)
- Initial cause appears to be: ${SURFACE_CAUSE}
- Evidence of: ${SURFACE_EVIDENCE}
- Timeline established: ${TIMELINE}

### Deep Analysis (DC 15)
${IF_DC_15}
- Root cause likely: ${ROOT_CAUSE}
- Contributing factors: ${CONTRIBUTING}
- Chain of events: ${CHAIN}

### Expert Forensics (DC 20)
${IF_DC_20}
- Underlying issue: ${UNDERLYING}
- Systemic problem: ${SYSTEMIC}
- Preventive measures: ${PREVENTIVE}

Investigate incident thoroughly.
```

## Schedule Conflict Investigation

```
**INVESTIGATION:** Schedule conflict at ${LOCATION_DATE}

**CONFLICT DETAILS:**
- Personnel involved: ${PERSONNEL_LIST}
- Assignments: ${ASSIGNMENT_LIST}
- Severity: ${SEVERITY}

**INVESTIGATION EVIDENCE:**
1. Assignment records show: ${RECORD_1}
2. Personnel availability indicates: ${AVAILABILITY}
3. Credential validation reveals: ${CREDENTIAL_CHECK}
4. ACGME rules analysis shows: ${ACGME_CHECK}

**ROOT CAUSE IDENTIFIED:**
- Primary cause: ${PRIMARY_CAUSE}
- Contributing factors: ${FACTORS}
- System weakness: ${WEAKNESS}

**EVIDENCE TRAIL:**
${EVIDENCE_CHAIN}

**REMEDIATION RECOMMENDATION:**
${REMEDIATION}

Report investigation findings.
```

---

*Last Updated: 2025-12-31*
