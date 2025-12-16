# Runbook: ACGME Work Hours Compliance

**Alert Names:** `ACGMEWorkHoursWarning`, `ACGMEWorkHoursViolation`, `ACGMEContinuousDutyViolation`
**Severity:** Warning/Critical
**Service:** Compliance
**Regulation Reference:** ACGME Common Program Requirements VI.F

## Description

These alerts fire when resident work hours approach or exceed ACGME limits:
- **Warning**: Resident approaching 80-hour weekly limit (>72 hours)
- **Violation**: Resident exceeds 80-hour weekly limit
- **Continuous Duty**: Resident exceeds 24+3 hour continuous duty limit

## Regulatory Context

ACGME requirements (must be documented and enforced):
- Maximum 80 hours/week averaged over 4 weeks
- No more than 24 hours of continuous duty (+3 hours for transition)
- Minimum 1 day off per 7 days (averaged over 4 weeks)
- Compliance is reviewed during program accreditation

## Impact

- **Warning**: Preventive action needed; no violation yet
- **Violation**: Regulatory non-compliance; must be documented
- **Repeated Violations**: Risk to program accreditation

## Quick Diagnosis

```bash
# Check current resident hours via API
curl http://localhost:8000/api/residents/{resident_id}/work-hours

# Get all residents approaching limits
curl http://localhost:8000/api/compliance/work-hours-report

# Check current schedule for the resident
curl http://localhost:8000/api/schedule?resident_id={resident_id}
```

## Resolution Steps

### For Warning Alerts (Approaching Limit)

1. **Review upcoming schedule**
   - Identify remaining shifts scheduled this week
   - Calculate projected total hours

2. **Adjust schedule if possible**
   - Swap shifts with other residents
   - Assign to less demanding rotations
   - Ensure adequate rest periods

3. **Document action taken**
   - Log in compliance tracking system
   - Note preventive measures applied

### For Violation Alerts (Limit Exceeded)

**IMMEDIATE ACTIONS (within 1 hour):**

1. **Document the violation**
   ```bash
   # Generate violation report
   curl http://localhost:8000/api/compliance/violations/generate \
     -X POST \
     -d '{"resident_id": "{id}", "violation_type": "work_hours"}'
   ```

2. **Notify required parties**
   - Program Director (mandatory)
   - Chief Resident
   - Compliance Officer

3. **Remove resident from duty if currently working**
   - Resident safety is priority
   - Arrange coverage for remaining shifts

4. **Root cause analysis**
   - Was this a scheduling error?
   - Did unexpected call-ins occur?
   - Was cross-coverage inadequate?

### For Continuous Duty Violations

**IMMEDIATE ACTION:**

1. **Relieve the resident immediately**
   - Patient safety concern
   - Document handoff properly

2. **Arrange coverage**
   - Contact backup call resident
   - Escalate to chief resident if needed

3. **Document circumstances**
   - Why did duty period extend?
   - Were there emergent situations?

## Investigation Checklist

- [ ] Identify affected resident(s)
- [ ] Verify hours calculation is accurate
- [ ] Review schedule that led to violation
- [ ] Check for system errors in time tracking
- [ ] Document in compliance log
- [ ] Notify Program Director
- [ ] Implement corrective action
- [ ] Schedule follow-up review

## Prevention

1. **Scheduling safeguards**
   - Enable pre-scheduling compliance checks
   - Use scheduling engine's ACGME validator
   - Review weekly projections every Monday

2. **Real-time monitoring**
   - Dashboard alerts for approaching limits
   - Daily compliance report review
   - Automated schedule adjustments

3. **Training**
   - Ensure residents understand reporting requirements
   - Train schedulers on ACGME requirements
   - Regular compliance education

## Escalation

| Timeframe | Action |
|-----------|--------|
| Immediate | Notify on-call chief resident |
| 1 hour | Notify Program Director |
| 24 hours | Submit compliance report |
| 1 week | Review at program meeting |

## Documentation Requirements

All violations must be documented in:
1. Residency management system
2. ACGME WebADS (Annual Data System)
3. Program compliance records

## Related Alerts

- `ACGMEDayOffViolation`
- `ACGMENightFloatViolation`
- `ACGMEComplianceScoreLow`

---

*Last Updated: December 2024*
*Compliance Reference: ACGME Common Program Requirements, Section VI*
