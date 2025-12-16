# Operational Runbooks

This directory contains operational runbooks for handling alerts and incidents in the Residency Scheduler system.

## Quick Reference

| Alert Category | Runbook | Severity |
|----------------|---------|----------|
| API Service Down | [api-down.md](api-down.md) | Critical |
| High Error Rate | [high-error-rate.md](high-error-rate.md) | Warning/Critical |
| Database Issues | [database-issues.md](database-issues.md) | Warning/Critical |
| ACGME Work Hours | [acgme-work-hours.md](acgme-work-hours.md) | Warning/Critical |
| ACGME Compliance | [acgme-compliance.md](acgme-compliance.md) | Warning/Critical |
| Resilience Alerts | [resilience-alerts.md](resilience-alerts.md) | Info/Warning/Critical |
| Infrastructure | [infrastructure.md](infrastructure.md) | Warning/Critical |

## Alert Routing

Alerts are routed based on severity and type:

- **Critical Alerts**: PagerDuty + Slack + Email (immediate response required)
- **Warning Alerts**: Slack + Email (respond within 1 hour during business hours)
- **Info Alerts**: Slack only (review during daily standup)

## Escalation Path

1. **Level 1** (0-15 min): On-call engineer
2. **Level 2** (15-30 min): Team lead
3. **Level 3** (30+ min): Engineering manager + stakeholders

## Contact Information

| Role | Contact | When to Engage |
|------|---------|----------------|
| On-Call Engineer | PagerDuty Rotation | All critical alerts |
| DBA | dba@hospital.org | Database alerts |
| Compliance Officer | compliance@hospital.org | ACGME violations |
| Program Director | pd@hospital.org | Critical compliance issues |

---

*Last Updated: December 2024*
