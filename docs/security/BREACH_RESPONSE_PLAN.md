# PHI Breach Response Plan

> **Document Classification:** INTERNAL USE ONLY
> **Last Updated:** 2026-01-04
> **Version:** 1.0
> **Owner:** Security Team

---

## Purpose

This document outlines the incident response procedures for suspected or confirmed Protected Health Information (PHI) data breaches in the Residency Scheduler application. This plan ensures compliance with HIPAA Breach Notification Rule (45 CFR §§ 164.400-414) and DoD data breach requirements.

---

## Definitions

**Protected Health Information (PHI):** Individually identifiable health information including:
- Names, email addresses, and contact information
- Medical absence types and health conditions
- Schedule patterns revealing work status
- Deployment and TDY information (OPSEC-sensitive)

**Breach:** Unauthorized acquisition, access, use, or disclosure of PHI that compromises the security or privacy of the information.

**Covered Entity:** The medical residency program using this system.

---

## Roles and Responsibilities

| Role | Responsibility | Contact |
|------|---------------|---------|
| **Incident Commander** | Overall incident response coordination | Chief of Staff / Program Director |
| **Security Lead** | Technical investigation and containment | IT Security Officer |
| **Privacy Officer** | HIPAA compliance and notification | Privacy Officer |
| **Legal Counsel** | Legal review and regulatory reporting | JAG / Legal Department |
| **Communications Lead** | Internal and external communications | Public Affairs Officer |

---

## Detection and Reporting

### Detection Methods

1. **Automated Alerts:**
   - Anomalous API access patterns (rate limiting triggers)
   - Bulk export endpoint usage outside normal hours
   - Failed authentication attempts exceeding threshold
   - Unusual database query patterns

2. **Manual Detection:**
   - User reports of unauthorized access
   - Security audit findings
   - Third-party security assessments
   - Routine log reviews

3. **X-Contains-PHI Header Monitoring:**
   - Track all requests to PHI-containing endpoints
   - Alert on unusual access patterns or bulk downloads

### Initial Reporting (Within 1 Hour of Discovery)

**Anyone discovering a potential breach must immediately:**

1. **Do NOT:**
   - Attempt to fix or investigate on your own
   - Delete logs or evidence
   - Notify affected individuals directly

2. **DO:**
   - Document what you observed (timestamp, screenshots, logs)
   - Contact Security Lead immediately
   - Preserve all evidence
   - Follow verbal instructions from Security Lead

**Security Lead Contact:**
- Primary: [INSERT PHONE/EMAIL]
- Secondary: [INSERT PHONE/EMAIL]
- After Hours: [INSERT ON-CALL NUMBER]

---

## Incident Response Procedure

### Phase 1: Initial Assessment (0-4 Hours)

**Objective:** Determine if a breach occurred and its scope.

**Actions:**

1. **Activate Incident Response Team:**
   - Notify Incident Commander, Security Lead, Privacy Officer
   - Establish secure communication channel
   - Begin incident log (time, actions, findings)

2. **Preliminary Investigation:**
   - Review audit logs for PHI-containing endpoints:
     ```bash
     # Check recent PHI endpoint access
     grep "X-Contains-PHI" /var/log/residency-scheduler/access.log | tail -1000
     ```
   - Identify affected endpoints, users, and time windows
   - Estimate number of records potentially exposed
   - Determine attack vector (if applicable)

3. **Breach Determination (within 4 hours):**
   - **Breach:** Unauthorized PHI access confirmed
   - **Incident:** Security event not meeting breach criteria
   - **False Alarm:** No actual exposure occurred

4. **Escalation:**
   - If breach confirmed: Proceed to Phase 2
   - If incident only: Follow standard incident response
   - If false alarm: Document and close

### Phase 2: Containment (4-24 Hours)

**Objective:** Stop ongoing exposure and prevent further unauthorized access.

**Technical Containment Actions:**

1. **Immediate Actions (within 1 hour of breach confirmation):**
   - Disable compromised user accounts
   - Rotate API keys and session tokens
   - Block suspicious IP addresses at firewall
   - Enable enhanced logging on all PHI endpoints

2. **Short-Term Containment:**
   - Reset passwords for all potentially affected accounts
   - Review and revoke active sessions
   - Patch exploited vulnerabilities
   - Deploy emergency firewall rules

3. **Isolation:**
   - If database compromised: Take snapshot, isolate database server
   - If application compromised: Deploy clean backup, preserve infected instance
   - If network compromised: Segment affected systems

**Evidence Preservation:**
- Create forensic copies of logs before rotation
- Preserve database backups from before and after breach
- Document all containment actions taken
- Maintain chain of custody for all evidence

### Phase 3: Investigation (24-72 Hours)

**Objective:** Determine root cause, scope, and extent of breach.

**Investigation Tasks:**

1. **Forensic Analysis:**
   - Analyze access logs, database audit trails, application logs
   - Reconstruct attacker timeline and actions
   - Identify all affected PHI records
   - Determine if data was exfiltrated (vs. just accessed)

2. **Scope Determination:**
   - Number of individuals affected
   - Types of PHI exposed (names, emails, medical info, deployment data)
   - Duration of unauthorized access
   - Geographic origin of breach

3. **Root Cause Analysis:**
   - Technical vulnerability exploited
   - Policy/process failures
   - Human error or social engineering
   - Insider threat indicators

**Documentation:**
- Create incident timeline
- List all affected individuals with PHI categories exposed
- Document evidence collected
- Prepare preliminary incident report

### Phase 4: Notification (Within 60 Days of Discovery)

**HIPAA Breach Notification Rule Requirements:**

#### A. Individual Notification (Required if ≥1 person affected)

**Timing:** Within 60 days of breach discovery

**Method:**
- First-class mail to last known address
- Email if individual has agreed to electronic notice
- Substitute notice if contact information insufficient

**Content (HIPAA Required Elements):**
1. Brief description of what happened
2. Types of PHI involved
3. Steps individuals should take to protect themselves
4. What organization is doing to investigate/mitigate
5. Contact procedures for questions

**Template:** See Appendix A - Individual Notification Template

#### B. Media Notification (Required if ≥500 individuals in same state/jurisdiction)

**Timing:** Within 60 days of breach discovery

**Method:** Prominent media outlets serving the affected area

**Content:** Same as individual notification

#### C. HHS Secretary Notification

**If ≥500 individuals affected:**
- Within 60 days via HHS Breach Portal
- Include breach details, individuals affected, description

**If <500 individuals affected:**
- Annual notification to HHS
- Due by March 1 following year of breach

#### D. DoD/Military Notification (Additional Requirement)

**Timing:** Within 72 hours of breach discovery

**Recipients:**
- Installation Commander
- Medical Group Commander
- Air Force Personnel Center (AFPC)
- DoD Cyber Crime Center (DC3) if cyber incident

**Method:** SITREP via official channels

### Phase 5: Remediation (Ongoing)

**Objective:** Fix root cause and prevent recurrence.

**Technical Remediation:**

1. **Immediate Fixes:**
   - Patch exploited vulnerabilities
   - Fix configuration errors
   - Update access controls
   - Deploy security hotfixes

2. **Long-Term Improvements:**
   - Implement missing security controls (per PHI_EXPOSURE_AUDIT.md)
   - Add field-level access control
   - Implement PHI access audit logging
   - Encrypt bulk exports
   - Add data loss prevention (DLP) rules

3. **Validation:**
   - Penetration testing of remediated systems
   - Security scan verification
   - Code review of security patches

**Policy/Process Remediation:**
- Update security policies
- Implement new procedures
- Enhance training programs
- Increase audit frequency

### Phase 6: Post-Incident Review (30 Days After Containment)

**Objective:** Learn from incident and improve defenses.

**Activities:**

1. **After-Action Review (AAR):**
   - What happened and why
   - What went well
   - What needs improvement
   - Specific action items with owners and deadlines

2. **Documentation:**
   - Final incident report
   - Lessons learned
   - Updated runbooks
   - Policy/procedure updates

3. **Metrics:**
   - Time to detection
   - Time to containment
   - Number of individuals affected
   - Financial impact

4. **Follow-Up:**
   - Verify remediation completed
   - Implement AAR action items
   - Schedule follow-up testing
   - Update breach response plan

---

## Appendix A: Individual Notification Template

```
[Date]

[Individual Name]
[Address]

Re: Notice of Data Breach

Dear [Name]:

We are writing to inform you of a data security incident that may have affected your personal information. On [Date], we discovered that unauthorized access to our residency scheduling system may have exposed some of your protected health information.

WHAT HAPPENED:
[Brief description of incident]

WHAT INFORMATION WAS INVOLVED:
The following types of information may have been affected:
- [List PHI categories: name, email, schedule data, etc.]

WHAT WE ARE DOING:
We have taken the following steps:
- [Containment actions]
- [Investigation status]
- [Enhanced security measures]

WHAT YOU CAN DO:
We recommend the following precautions:
- [Specific recommendations based on data exposed]
- Monitor your accounts for suspicious activity
- Report any unusual communications

FOR MORE INFORMATION:
If you have questions, please contact:
[Contact name, phone, email]
[Hours of availability]

We sincerely apologize for this incident and any inconvenience it may cause.

Sincerely,

[Program Director/Privacy Officer Name]
[Title]
[Organization]
```

---

## Appendix B: Breach Assessment Checklist

Use this checklist to determine if an incident constitutes a HIPAA breach:

- [ ] Was PHI involved?
- [ ] Was PHI acquired, accessed, used, or disclosed?
- [ ] Was the access/disclosure unauthorized?
- [ ] Does a regulatory exception apply?
  - [ ] Unintentional acquisition/access by workforce member
  - [ ] Inadvertent disclosure among authorized personnel
  - [ ] Good faith belief recipient cannot retain information
- [ ] Could the information be re-identified?
- [ ] Was harm to individual mitigated?

**If YES to questions 1-3 and NO to exceptions:** This is likely a breach requiring notification.

---

## Appendix C: Emergency Contacts

| Organization | Contact | Phone | Email |
|-------------|---------|-------|-------|
| HHS Breach Portal | - | - | https://ocrportal.hhs.gov/ocr/breach/wizard_breach.jsf |
| DoD Cyber Crime Center | DC3 | 1-800-XXX-XXXX | [INSERT] |
| Installation Security | [Name] | [Phone] | [Email] |
| Legal Office (JAG) | [Name] | [Phone] | [Email] |
| Public Affairs | [Name] | [Phone] | [Email] |

---

**Document Control:**
- Review annually or after each breach incident
- Approved by: [Privacy Officer, Security Lead, Program Director]
- Next Review Date: 2027-01-04
