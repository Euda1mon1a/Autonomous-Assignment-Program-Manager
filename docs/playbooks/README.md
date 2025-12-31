# Operational Playbooks

**Comprehensive Step-by-Step Guides for Medical Residency Scheduling Operations**

Last Updated: 2025-12-31

---

## Overview

This directory contains six comprehensive operational playbooks designed for medical residency program administration. Each playbook provides detailed, step-by-step procedures for critical operational workflows.

### Quick Navigation

| Playbook | Purpose | Audience | Pages |
|----------|---------|----------|-------|
| [Schedule Generation](SCHEDULE_GENERATION_PLAYBOOK.md) | Creating and deploying annual schedules | Coordinators, Directors | 40+ |
| [Swap Processing](SWAP_PROCESSING_PLAYBOOK.md) | Managing resident/faculty schedule swaps | Coordinators, Faculty | 20+ |
| [Incident Response](INCIDENT_RESPONSE_PLAYBOOK.md) | Handling system incidents and crises | IT, Coordinators, Leadership | 30+ |
| [Compliance Audit](COMPLIANCE_AUDIT_PLAYBOOK.md) | ACGME audit procedures and reporting | Directors, Compliance, GME | 35+ |
| [System Maintenance](SYSTEM_MAINTENANCE_PLAYBOOK.md) | Database, backups, and system health | IT, System Admins | 25+ |
| [Onboarding & Offboarding](ONBOARDING_PLAYBOOK.md) | New person setup and departure | HR, Coordinators, IT | 30+ |

---

## Playbook Summaries

### 1. Schedule Generation Playbook

**When to Use:** Every academic year (usually July start)

**Contains:**
- Pre-generation checklist (data validation, system health checks)
- Constraint configuration procedures
- Generation execution steps with monitoring
- Validation and review process
- Publication workflow
- Rollback procedures for failures
- Post-generation verification
- Comprehensive troubleshooting guide
- Approval checklists and issue tracking templates

**Key Workflows:**
```
Pre-Generation → Constraint Config → Execution → Validation → Review → Publication
```

**Typical Timeline:** 3-4 weeks total
- Preparation: 2-3 weeks
- Generation: 2-4 hours
- Review period: 3-5 days
- Publication: 1-2 days

---

### 2. Swap Processing Playbook

**When to Use:** Throughout academic year (after 30 days from publication)

**Contains:**
- Swap request intake procedures
- Compatibility analysis (rotations, credentials, coverage)
- Approval workflow by role
- Step-by-step execution
- Rollback procedures (within 24 hours)
- Compliance verification
- Comprehensive troubleshooting

**Key Workflows:**
```
Request → Validation → Confirmation → Analysis → Approval → Execution → Verification
```

**Processing Time:** 24-48 hours typical
- Simple 1:1 swaps: 24-36 hours
- Complex swaps: 36-48 hours
- Rollback (if needed): < 1 hour

---

### 3. Incident Response Playbook

**When to Use:** For system issues, data corruption, operational failures

**Contains:**
- Severity classification (P1-P4)
- Initial triage procedures
- Escalation decision trees and procedures
- Communication templates for all severity levels
- Resolution steps specific to each severity
- Post-incident review procedures
- On-call rotation procedures
- Rollback procedures for critical incidents
- Incident documentation templates

**Severity Levels:**
- **P1 (CRITICAL):** System down, data at risk → 15 min response
- **P2 (HIGH):** Major functionality broken → 1 hour response
- **P3 (MEDIUM):** Non-critical feature broken → 4 hour response
- **P4 (LOW):** Minor issues, workarounds exist → next business day

**Resolution Timeline:**
- P1: Immediate response, < 4 hours resolution
- P2: 30 min response, < 4 hours resolution
- P3: 1 hour response, < 24 hours resolution
- P4: Standard ticket process

---

### 4. Compliance Audit Playbook

**When to Use:** Annual audits (typically June), quarterly checks, before ACGME surveys

**Contains:**
- Pre-audit preparation (4-6 weeks)
- Data extraction procedures
- Compliance report generation
- Violation analysis and classification
- Root cause analysis for each violation
- Remediation planning and execution
- ACGME survey preparation
- Audit trail review
- Comprehensive compliance checklists
- Documentation templates

**Audit Types:**
- Annual formal audit (full year, ACGME-ready)
- Quarterly internal audits (spot checks)
- Monthly spot checks (quick verification)
- Continuous monitoring (real-time dashboards)

**Key Rules Audited:**
- 80-hour weekly limit (averaged over 4 weeks)
- 1-in-7 rest days
- Supervision ratios (PGY1: 1:2, PGY2+: 1:4)
- Adequate training/education value

---

### 5. System Maintenance Playbook

**When to Use:** Daily (automated), weekly (Sunday), monthly (first Sunday)

**Contains:**
- Daily backup procedures and verification
- Weekly full backup procedures
- Monthly backup and archiving
- Backup retention policies
- Point-in-time restore procedures
- Full system restore procedures
- Log management and rotation
- Cache management (Redis)
- Daily/weekly/monthly health checks
- System upgrade procedures
- Security patching procedures
- Maintenance scheduling

**Maintenance Windows:**
- **Daily:** 2-3 AM (1 hour, automated)
- **Weekly:** Sunday 2-6 AM (4 hours, planned)
- **Monthly:** First Sunday 2-8 AM (6 hours, major work)
- **Emergency:** ASAP (any time, critical issues)

**Backup Strategy:**
- Daily: 7-day retention
- Weekly: 8-week retention
- Monthly: 1-year retention
- Off-site: 2-year retention

---

### 6. Onboarding & Offboarding Playbook

**When to Use:** New residents (July 1, yearly), new faculty (ongoing), departures (ongoing)

**Contains:**
- New resident onboarding (4-12 weeks pre-arrival through month 1)
- New faculty onboarding (4 weeks pre-arrival through month 1)
- System access provisioning procedures
- IT account setup
- Training requirements and tracking
- Credentialing procedures
- Workspace setup
- First-day orientation schedule
- System training plan
- Supervision training (faculty)
- Offboarding procedures (2+ weeks before departure)
- System access removal
- Schedule cleanup
- Final status verification

**Key Timelines:**
- Resident onboarding: 12+ weeks pre-arrival
- Faculty onboarding: 4+ weeks pre-arrival
- Offboarding: 2+ weeks notice

**Training Requirements:**
- Mandatory: HIPAA, Security, Anti-harassment, Safety, Compliance
- Role-specific: System training, Supervision (faculty), Clinical orientation
- All must complete before start/beginning of duties

---

## How to Use These Playbooks

### Step 1: Find Your Task

1. Identify what operation you're performing
2. Locate corresponding playbook in table above
3. Open the playbook document

### Step 2: Follow the Process

Each playbook follows a standard structure:

```
1. Overview/Context
   ↓
2. Pre-operation checklist
   ↓
3. Step-by-step procedures with verification
   ↓
4. Troubleshooting section
   ↓
5. Templates and checklists
```

### Step 3: Use Checklists

Every major procedure includes:
- **Pre-execution checklist:** Verify prerequisites
- **Process checklist:** Track steps as you complete them
- **Post-execution checklist:** Verify success

### Step 4: Document Actions

Use provided templates to:
- Record decisions made
- Document issues encountered
- Track timelines and approvals
- Create audit trail

---

## Key Concepts Across All Playbooks

### ACGME Compliance

All playbooks maintain focus on ACGME (Accreditation Council for Graduate Medical Education) requirements:
- **80-Hour Rule:** Maximum 80 hours/week averaged over 4 weeks
- **1-in-7 Rule:** One 24-hour period off every 7 days
- **Supervision Ratios:** PGY1 1:2, PGY2+ 1:4
- **Documentation:** All changes and violations documented

### Authorization & Approval

Operations follow approval hierarchy:
- **Residents:** Can request swaps, view own schedule
- **Faculty:** Can approve swaps, monitor work hours, advise on changes
- **Coordinators:** Can execute swaps, modify schedules, generate reports
- **Program Director:** Final approval for major changes, schedule publication
- **IT/Admin:** System access, configuration, maintenance

### Documentation & Audit Trail

Every operation must:
- Be documented in system or record
- Be authorized appropriately
- Be reversible (with rollback procedures)
- Have audit trail for compliance

### Communication

Critical operations include:
- Pre-notification (when possible)
- Real-time status updates
- Post-completion notification
- Issue/escalation communication

---

## Operational Metrics & Targets

### Schedule Generation
- **Success Rate:** > 99%
- **Timeline:** < 4 hours
- **Violations Post-generation:** 0
- **Quality Score:** > 0.90

### Swap Processing
- **Average Processing Time:** 36 hours
- **Success Rate:** > 95%
- **Compliance Violations from Swaps:** 0
- **Resident Satisfaction:** > 4.0/5.0

### Incident Response
- **P1 Initial Response:** < 15 minutes
- **P1 Resolution:** < 4 hours
- **P2 Initial Response:** < 30 minutes
- **P2 Resolution:** < 4 hours

### Compliance Audit
- **Audit Completion:** < 2 weeks from start
- **Violation Discovery Rate:** > 95%
- **Remediation Rate:** 100% (all violations addressed)
- **ACGME Readiness:** 100%

### System Maintenance
- **Backup Success Rate:** 100%
- **API Uptime:** > 99.9%
- **Database Uptime:** > 99.99%
- **Recovery Time Objective (RTO):** < 1 hour
- **Recovery Point Objective (RPO):** < 24 hours

### Onboarding
- **Completion Rate:** 100% before start
- **Training Completion:** 100% within week 1
- **Time to Productivity:** 2-4 weeks
- **Satisfaction:** > 4.0/5.0

---

## Emergency Quick Reference

### P1 Incident (System Down)

1. **Within 15 minutes:**
   - Confirm incident is real
   - Call on-call tech lead
   - Check system status
   - Declare incident

2. **Within 30 minutes:**
   - Assemble response team
   - Start war room
   - Begin diagnosis
   - Notify leadership

3. **Within 1 hour:**
   - Root cause identified
   - Remediation plan determined
   - Begin implementation

4. **Within 4 hours:**
   - Issue resolved
   - System verified
   - All-clear communication sent

See [Incident Response Playbook](INCIDENT_RESPONSE_PLAYBOOK.md) for full procedures.

### Schedule Publication Failure

1. Verify root cause (see [Troubleshooting Guide](SCHEDULE_GENERATION_PLAYBOOK.md#troubleshooting-guide))
2. Execute rollback (see [Rollback Procedures](SCHEDULE_GENERATION_PLAYBOOK.md#rollback-procedures))
3. Analyze issue (see [Failure Recovery](SCHEDULE_GENERATION_PLAYBOOK.md#failure-recovery))
4. Re-generate schedule
5. Document lessons learned

### Critical Violation Found

1. Immediately notify Program Director
2. Do not publish/distribute schedule
3. Analyze impact (residents affected)
4. Determine remediation strategy
5. Execute fixes (swaps, assignments)
6. Re-validate
7. Publish clean schedule

---

## Related Documentation

These playbooks complement and reference:

- **[CLAUDE.md](../../CLAUDE.md)** - Project guidelines and code standards
- **[Architecture Documentation](../architecture/)** - System design
- **[API Reference](../api/)** - API endpoint details
- **[Operations Guides](../operations/)** - Additional operational resources
- **[Admin Manual](../admin-manual/)** - Administrator guides

---

## Document Maintenance

### Review Cycle

- **Quarterly:** Review for accuracy and updates
- **Annual:** Full review before new academic year
- **As-needed:** Update for process changes or lessons learned

### Version Control

Each playbook tracks:
- Version number (e.g., 1.0)
- Last update date
- Owner/responsible party
- Review cycle frequency

### Feedback and Improvements

To suggest improvements:
1. Document what needs changing
2. Note where in playbook
3. Explain reason for change
4. Submit to Program Director for review
5. Update will be incorporated in next revision

---

## Contact & Support

For questions about:

- **Schedule Generation:** Contact Program Coordinator
- **Swap Processing:** Contact Scheduling Coordinator
- **Incidents:** Contact IT/System Administrator (on-call)
- **Compliance:** Contact Program Director or GME Specialist
- **System Maintenance:** Contact IT System Administrator
- **Onboarding/Offboarding:** Contact HR Manager

---

**Last Updated:** 2025-12-31
**Total Pages:** 150+ comprehensive operational guides
**Status:** Ready for Operational Use
**Next Review:** 2026-06-30 (before next academic year)
