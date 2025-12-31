***REMOVED*** Security Auditor Agent - Prompt Templates

> **Role:** Security assessment, vulnerability detection, compliance auditing
> **Model:** Claude Opus 4.5
> **Mission:** Ensure system security and data protection

***REMOVED******REMOVED*** 1. SECURITY AUDIT TEMPLATE

```
**SECURITY AUDIT**

**AUDIT SCOPE:** ${SCOPE}
**AUDIT DATE:** ${TODAY}
**AUDITOR:** Security Auditor Agent

**AUDIT METHODOLOGY:**
1. Code review for security patterns
2. Vulnerability scanning
3. Dependency analysis
4. Configuration review
5. Compliance verification

**AUDIT AREAS:**

***REMOVED******REMOVED******REMOVED*** Authentication & Authorization
- [ ] Password requirements enforced
- [ ] JWT tokens properly validated
- [ ] Rate limiting on auth endpoints
- [ ] RBAC implemented correctly

***REMOVED******REMOVED******REMOVED*** Data Protection
- [ ] PII never hardcoded
- [ ] Sensitive data encrypted at rest
- [ ] TLS/SSL for all connections
- [ ] No secrets in logs

***REMOVED******REMOVED******REMOVED*** Input Validation
- [ ] All inputs validated with Pydantic
- [ ] SQL injection prevention (ORM usage)
- [ ] Path traversal prevention
- [ ] XSS prevention (proper escaping)

***REMOVED******REMOVED******REMOVED*** Error Handling
- [ ] No sensitive data in error messages
- [ ] Proper exception handling
- [ ] Logging doesn't expose secrets
- [ ] Error responses don't leak system info

***REMOVED******REMOVED******REMOVED*** Dependencies
- [ ] All dependencies scanned for CVEs
- [ ] No known vulnerabilities
- [ ] Dependency versions pinned
- [ ] License compliance verified

**FINDINGS:**
${FINDINGS}

**SEVERITY LEVELS:**
- CRITICAL: Fix immediately
- HIGH: Fix within 7 days
- MEDIUM: Fix within 30 days
- LOW: Fix in next release

Conduct security audit comprehensively.
```

***REMOVED******REMOVED*** 2. VULNERABILITY ASSESSMENT TEMPLATE

```
**VULNERABILITY ASSESSMENT**

**VULNERABILITY:** ${VULNERABILITY_NAME}
**SEVERITY:** ${SEVERITY}
**CVSS SCORE:** ${CVSS_SCORE}

**VULNERABILITY DETAILS:**
- Type: ${VULNERABILITY_TYPE}
- Location: ${FILE_PATH}:${LINE_NUMBER}
- Component: ${AFFECTED_COMPONENT}

**DESCRIPTION:**
${DETAILED_DESCRIPTION}

**ATTACK VECTOR:**
${ATTACK_VECTOR}

**IMPACT:**
${IMPACT_ASSESSMENT}

**REMEDIATION:**
1. ${STEP_1}
2. ${STEP_2}
3. ${STEP_3}

**VERIFICATION:**
- [ ] Fix implemented
- [ ] Tests added/updated
- [ ] No regression
- [ ] Deployment verified

**TIMELINE:**
- Discovery: ${DISCOVERY_DATE}
- Patch available: ${PATCH_DATE}
- Deadline: ${DEADLINE}

Report vulnerability and remediation plan.
```

***REMOVED******REMOVED*** 3. DEPENDENCY VULNERABILITY SCANNING TEMPLATE

```
**DEPENDENCY SCAN RESULTS**

**BACKEND DEPENDENCIES:**
Location: `backend/requirements.txt`

\`\`\`bash
pip install safety
safety check
\`\`\`

**VULNERABLE PACKAGES:**
- Package: ${PACKAGE}
  Version: ${VERSION}
  CVE: ${CVE_ID}
  Fix: Upgrade to ${FIXED_VERSION}

**FRONTEND DEPENDENCIES:**
Location: `frontend/package.json`

\`\`\`bash
npm audit
\`\`\`

**ACTION PLAN:**
- Update vulnerable packages
- Test for compatibility
- Deploy safely
- Monitor for new vulnerabilities

Run dependency scans regularly.
```

***REMOVED******REMOVED*** 4. ENCRYPTION & SECRETS TEMPLATE

```
**ENCRYPTION & SECRETS AUDIT**

**SECRET MANAGEMENT:**
- [ ] All secrets in environment variables
- [ ] No hardcoded credentials
- [ ] Secret rotation policy enforced
- [ ] Access logging enabled

**ENVIRONMENT VARIABLES:**
\`\`\`bash
***REMOVED*** Required secrets (.env)
- DATABASE_URL: PostgreSQL connection
- SECRET_KEY: JWT signing key (>= 32 chars)
- WEBHOOK_SECRET: External webhooks
- API_KEYS: Third-party services

***REMOVED*** Validation
bash scripts/validate-secrets.sh
\`\`\`

**ENCRYPTION AT REST:**
- Database passwords: Hashed (bcrypt)
- API tokens: Encrypted column
- PII: Column-level encryption (if needed)

**ENCRYPTION IN TRANSIT:**
- TLS 1.2+: All connections
- Certificate validation: Enforced
- HSTS: Enabled (if applicable)

**KEY ROTATION:**
- Frequency: ${ROTATION_FREQUENCY}
- Process: ${ROTATION_PROCESS}
- Testing: Before production

Audit encryption and secrets management.
```

***REMOVED******REMOVED*** 5. COMPLIANCE AUDIT TEMPLATE

```
**COMPLIANCE AUDIT**

**COMPLIANCE FRAMEWORK:** HIPAA, OPSEC, OWASP Top 10

**HIPAA COMPLIANCE (if applicable):**
- [ ] Access controls enforced
- [ ] Audit logging complete
- [ ] Data encryption enabled
- [ ] Incident response plan documented
- [ ] Business associate agreements signed

**OPSEC COMPLIANCE (Military context):**
- [ ] No PII in code/repos
- [ ] No schedule data in version control
- [ ] No TDY/deployment info in logs
- [ ] PERSEC/OPSEC training documented

**OWASP TOP 10:**
- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Authentication Failures
- [ ] A08: Software Data Integrity
- [ ] A09: Logging/Monitoring Failures
- [ ] A10: SSRF

**COMPLIANCE GAPS:**
${GAPS}

**REMEDIATION PLAN:**
${REMEDIATION}

**VERIFICATION TIMELINE:**
${TIMELINE}

Audit compliance comprehensively.
```

***REMOVED******REMOVED*** 6. CODE SECURITY REVIEW TEMPLATE

```
**CODE SECURITY REVIEW**

**FILE:** ${FILE_PATH}

**SECURITY CHECKLIST:**

***REMOVED******REMOVED******REMOVED*** Input Validation
- [ ] All inputs validated
- [ ] Type checking present
- [ ] Range validation present
- [ ] Format validation present

***REMOVED******REMOVED******REMOVED*** Output Encoding
- [ ] Output properly escaped
- [ ] No raw HTML injection risk
- [ ] JSON responses safe
- [ ] Error messages sanitized

***REMOVED******REMOVED******REMOVED*** Authentication
- [ ] Auth check present
- [ ] Correct auth method used
- [ ] Token validation proper
- [ ] Session management secure

***REMOVED******REMOVED******REMOVED*** Authorization
- [ ] RBAC check present
- [ ] Resource ownership verified
- [ ] No privilege escalation risk
- [ ] Audit logging present

***REMOVED******REMOVED******REMOVED*** Data Handling
- [ ] No PII in logs
- [ ] Sensitive data encrypted
- [ ] Proper data disposal
- [ ] No unnecessary data retention

**FINDINGS:**
${FINDINGS}

**RECOMMENDATIONS:**
${RECOMMENDATIONS}

Report code security findings.
```

***REMOVED******REMOVED*** 7. PENETRATION TEST TEMPLATE

```
**PENETRATION TEST PLAN**

**SCOPE:**
- ${SCOPE_1}
- ${SCOPE_2}
- ${SCOPE_3}

**TESTING METHODOLOGY:**
1. Reconnaissance (information gathering)
2. Scanning (identify vulnerabilities)
3. Enumeration (detail vulnerabilities)
4. Exploitation (attempt attacks)
5. Reporting

**TEST CASES:**
- SQL injection attempts
- XSS payload injection
- Authentication bypass
- Authorization bypass
- CSRF attacks
- Session hijacking
- Path traversal
- Privilege escalation

**TEST RESULTS:**
${TEST_RESULTS}

**CRITICAL FINDINGS:**
${CRITICAL_FINDINGS}

**RECOMMENDATIONS:**
${RECOMMENDATIONS}

**TIMELINE:**
- Testing: ${TEST_PERIOD}
- Reporting: ${REPORT_DATE}
- Remediation: ${REMEDIATION_DATE}

Conduct penetration testing.
```

***REMOVED******REMOVED*** 8. STATUS REPORT TEMPLATE

```
**SECURITY AUDITOR STATUS REPORT**

**AUDIT ACTIVITY:**
- Audits conducted: ${AUDIT_COUNT}
- Vulnerabilities found: ${VULNERABILITY_COUNT}
- Vulnerabilities fixed: ${FIXED_COUNT}

**VULNERABILITY METRICS:**
- CRITICAL: ${CRITICAL} (avg time to fix: ${AVG_TIME})
- HIGH: ${HIGH}
- MEDIUM: ${MEDIUM}
- LOW: ${LOW}

**COMPLIANCE STATUS:**
- HIPAA: ${HIPAA_STATUS}
- OPSEC: ${OPSEC_STATUS}
- OWASP: ${OWASP_STATUS}

**REMEDIATION:**
- Pending: ${PENDING}
- In progress: ${IN_PROGRESS}
- Completed: ${COMPLETED}

**CRITICAL ISSUES:**
${CRITICAL_ISSUES}

**NEXT:** ${NEXT_GOALS}
```

---

*Last Updated: 2025-12-31*
*Agent: Security Auditor*
*Version: 1.0*
