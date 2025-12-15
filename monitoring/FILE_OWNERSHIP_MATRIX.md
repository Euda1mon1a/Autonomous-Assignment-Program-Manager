# File Ownership Matrix - Monitoring Directory

This document defines the ownership and responsibility matrix for all files in the `monitoring/` directory.

## Ownership Legend

| Role | Abbreviation | Responsibilities |
|------|--------------|-----------------|
| DevOps Engineer | DevOps | Infrastructure, CI/CD, deployment |
| Site Reliability Engineer | SRE | Monitoring, alerting, reliability |
| Platform Engineer | Platform | Container orchestration, observability |
| Database Administrator | DBA | Database-specific monitoring |
| Security Engineer | Security | Security monitoring, compliance |

## File Ownership Matrix

### Root Level Files

| File | Primary Owner | Secondary Owner | Description |
|------|---------------|-----------------|-------------|
| `README.md` | DevOps | SRE | Documentation for monitoring stack |
| `docker-compose.monitoring.yml` | DevOps | Platform | Docker Compose configuration |
| `.env.example` | DevOps | SRE | Environment variable template |
| `FILE_OWNERSHIP_MATRIX.md` | DevOps | - | This file |

### Prometheus Configuration (`prometheus/`)

| File | Primary Owner | Secondary Owner | Description |
|------|---------------|-----------------|-------------|
| `prometheus/prometheus.yml` | SRE | DevOps | Main Prometheus configuration |
| `prometheus/rules/application.yml` | SRE | DevOps | Application-level alert rules |
| `prometheus/rules/infrastructure.yml` | SRE | Platform | Infrastructure alert rules |

### Alertmanager Configuration (`alertmanager/`)

| File | Primary Owner | Secondary Owner | Description |
|------|---------------|-----------------|-------------|
| `alertmanager/alertmanager.yml` | SRE | DevOps | Alert routing configuration |
| `alertmanager/templates/slack.tmpl` | SRE | DevOps | Slack notification template |

### Grafana Configuration (`grafana/`)

| File | Primary Owner | Secondary Owner | Description |
|------|---------------|-----------------|-------------|
| `grafana/provisioning/datasources/datasources.yml` | SRE | DevOps | Data source auto-provisioning |
| `grafana/provisioning/dashboards/dashboards.yml` | SRE | DevOps | Dashboard provisioning config |
| `grafana/dashboards/overview.json` | SRE | DevOps | Overview dashboard |
| `grafana/dashboards/application-metrics.json` | SRE | DevOps | Application metrics dashboard |
| `grafana/dashboards/system-metrics.json` | SRE | Platform | System metrics dashboard |
| `grafana/dashboards/database-metrics.json` | DBA | SRE | PostgreSQL metrics dashboard |

### Loki Configuration (`loki/`)

| File | Primary Owner | Secondary Owner | Description |
|------|---------------|-----------------|-------------|
| `loki/loki-config.yml` | SRE | Platform | Loki log aggregation config |

### Promtail Configuration (`promtail/`)

| File | Primary Owner | Secondary Owner | Description |
|------|---------------|-----------------|-------------|
| `promtail/promtail-config.yml` | SRE | Platform | Log collection agent config |

### Scripts (`scripts/`)

| File | Primary Owner | Secondary Owner | Description |
|------|---------------|-----------------|-------------|
| `scripts/setup-monitoring.sh` | DevOps | SRE | Initial setup script |
| `scripts/health-check.sh` | SRE | DevOps | Health verification script |
| `scripts/backup-monitoring.sh` | DevOps | SRE | Data backup script |

## Change Management

### Approval Requirements

| Change Type | Required Approvals |
|-------------|-------------------|
| Alert rules (critical) | SRE Lead + On-call Engineer |
| Alert rules (warning/info) | SRE |
| Dashboard changes | SRE |
| Infrastructure config | DevOps Lead |
| Retention policies | SRE Lead + Legal (if applicable) |
| Notification channels | SRE + Security |

### Review Process

1. **Minor Changes** (typos, formatting): Self-merge after review
2. **Standard Changes** (new dashboards, alert tuning): Peer review required
3. **Major Changes** (architecture, retention): Team lead approval required

## Contact Information

| Role | Team | Slack Channel |
|------|------|---------------|
| DevOps | Platform Team | #platform-ops |
| SRE | Reliability Team | #sre-team |
| DBA | Database Team | #dba-team |

## Escalation Path

1. **P1 (Critical)**: Page on-call SRE → SRE Lead → VP Engineering
2. **P2 (High)**: Slack #sre-team → SRE Lead
3. **P3 (Medium)**: Create ticket, assign to team
4. **P4 (Low)**: Backlog grooming

## Audit Log

| Date | Author | Files Changed | Reason |
|------|--------|---------------|--------|
| 2024-12-15 | DevOps | Initial creation | Monitoring stack setup |
