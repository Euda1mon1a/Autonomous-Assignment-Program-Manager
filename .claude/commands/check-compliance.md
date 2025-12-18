<!--
Check ACGME compliance status and MTF compliance metrics.
Validates residency work hour rules and military treatment facility readiness.
-->

Check ACGME compliance status and system compliance metrics:

1. Run ACGME-specific test suite to validate compliance rules
2. Check for any ACGME validation warnings or violations in the codebase
3. Review MTF compliance and resilience metrics

Execute these checks:

```bash
# Run ACGME-tagged tests
cd /home/user/Autonomous-Assignment-Program-Manager/backend
pytest -m acgme -v

# Check for ACGME validator usage
grep -r "acgme" backend/app/validators/ --include="*.py" -i

# Check MTF compliance module
grep -r "compliance" backend/app/resilience/ --include="*.py" -i
```

After running compliance checks:
- Report all ACGME test results (should all pass)
- List any compliance validators found in the codebase
- Note the key ACGME rules being enforced:
  - 80-hour work week limits
  - Duty hour restrictions
  - Rest period requirements
  - Call frequency limits
  - Specialty-specific requirements

Also review:
- MTF compliance readiness (Defense Readiness Reporting System - DRRS)
- Circuit breaker states for safety thresholds
- Mission capability status
- Any active compliance violations or warnings

If tests fail, provide detailed information about which ACGME rules are being violated and suggest remediation steps.
