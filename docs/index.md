# Residency Scheduler Documentation

Welcome to the **Residency Scheduler** documentation. This application automates medical residency scheduling while ensuring full ACGME compliance.

---

## Quick Links

<div class="grid cards" markdown>

-   :material-account-group:{ .lg .middle } **User Guide**

    ---

    Learn how to use the scheduler for day-to-day operations

    [:octicons-arrow-right-24: Get Started](user-guide/README.md)

-   :material-server:{ .lg .middle } **Administrator Manual**

    ---

    Deploy, configure, and maintain the system

    [:octicons-arrow-right-24: Admin Guide](admin-manual/README.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Integrate with the REST API

    [:octicons-arrow-right-24: API Docs](api/README.md)

-   :material-code-braces:{ .lg .middle } **Developer Guide**

    ---

    Contribute to and extend the application

    [:octicons-arrow-right-24: Dev Docs](development/README.md)

</div>

---

## What is Residency Scheduler?

Residency Scheduler is a production-ready application for managing medical residency program schedules. It handles:

- **ACGME Compliance** - Automatic enforcement of 80-hour work weeks, 1-in-7 days off, and supervision ratios
- **Smart Scheduling** - Constraint-based optimization using OR-Tools and custom algorithms
- **Absence Management** - Track vacations, deployments, TDY, and medical leaves
- **Schedule Resilience** - Plan for faculty shortages and activate contingency schedules
- **Military Support** - Built-in support for deployment and TDY tracking

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│   PostgreSQL    │
│   (Next.js)     │     │   (FastAPI)     │     │   Database      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Celery + Redis │
                        │  (Background)   │
                        └─────────────────┘
```

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Next.js 14, React, TypeScript, TailwindCSS | User interface |
| Backend | FastAPI, SQLAlchemy, Pydantic | REST API, business logic |
| Database | PostgreSQL 15 | Data persistence |
| Background Jobs | Celery, Redis | Async task processing |
| Monitoring | Prometheus, Grafana, Loki | Observability |

## Getting Started

### For Users

1. Read the [Getting Started Tutorial](user-guide/getting-started.md)
2. Explore the [Dashboard](user-guide/dashboard.md)
3. Learn about [Schedule Generation](user-guide/schedule-generation.md)

### For Administrators

1. Follow the [Installation Guide](admin-manual/installation.md)
2. Configure the system using the [Configuration Guide](admin-manual/configuration.md)
3. Set up [Backup & Restore](admin-manual/backup-restore.md)

### For Developers

1. Set up your [Development Environment](development/environment-setup.md)
2. Review the [Architecture](development/architecture.md)
3. Follow the [Contributing Guide](development/contributing.md)

## Key Features

### ACGME Compliance Monitoring

The scheduler automatically validates schedules against ACGME requirements:

| Rule | Limit | Enforcement |
|------|-------|-------------|
| Weekly Hours | 80 hours (4-week average) | Hard constraint |
| Days Off | 1 in 7 days | Hard constraint |
| PGY-1 Supervision | 1:2 faculty ratio | Hard constraint |
| PGY-2/3 Supervision | 1:4 faculty ratio | Hard constraint |

### Schedule Resilience

Built-in resilience engineering patterns help maintain schedule stability:

- **Blast Radius Analysis** - Understand the impact of schedule changes
- **Cognitive Load Monitoring** - Track workload distribution
- **N-1/N-2 Contingency** - Plan for faculty shortages
- **Load Shedding** - Prioritized degradation during crises

## Documentation Structure

| Section | Audience | Content |
|---------|----------|---------|
| [User Guide](user-guide/README.md) | Coordinators, Faculty | Feature walkthroughs, workflows |
| [Admin Manual](admin-manual/README.md) | System Admins | Deployment, operations |
| [API Reference](api/README.md) | Developers, Integrators | REST API documentation |
| [Runbooks](runbooks/README.md) | On-Call Engineers | Incident response |
| [Developer Guide](development/README.md) | Contributors | Code architecture, testing |
| [Technical References](#) | All | Deep-dive documentation |

---

## Need Help?

- **In-app**: Click the Help icon in the navigation bar
- **This documentation**: Use the search bar above
- **Issues**: [GitHub Issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)

---

*Residency Scheduler - Streamlining medical education scheduling with ACGME compliance*
