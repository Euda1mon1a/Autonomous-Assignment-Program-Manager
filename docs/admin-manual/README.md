***REMOVED*** Residency Scheduler - Administrator Manual

***REMOVED******REMOVED*** Overview

This administrator manual provides comprehensive guidance for deploying, configuring, and maintaining the Residency Scheduler application. It is intended for system administrators, IT staff, and technical personnel responsible for managing the application in production environments.

***REMOVED******REMOVED*** Document Scope

This manual covers:

- Installation and deployment procedures
- User and permission management
- System configuration options
- Data storage locations and persistence
- Database backup and restore procedures
- Security best practices
- Performance tuning and optimization

***REMOVED******REMOVED*** Table of Contents

| Document | Description |
|----------|-------------|
| [Installation Guide](./installation.md) | Complete installation and deployment instructions |
| [Service Operations](./service-operations.md) | Starting, stopping, monitoring, and troubleshooting services |
| [User Management](./user-management.md) | User administration and permission configuration |
| [Configuration Guide](./configuration.md) | System configuration options and environment variables |
| [Data Storage](./data-storage.md) | Where data is stored in different deployment scenarios |
| [Backup & Restore](./backup-restore.md) | Database backup and disaster recovery procedures |
| [Security Guide](./security.md) | Security best practices and hardening guidelines |
| [Performance Tuning](./performance.md) | Performance optimization and monitoring |

***REMOVED******REMOVED*** System Requirements

***REMOVED******REMOVED******REMOVED*** Minimum Requirements

| Component | Specification |
|-----------|---------------|
| CPU | 2 cores |
| RAM | 4 GB |
| Storage | 20 GB SSD |
| OS | Ubuntu 20.04 LTS or later |
| Network | 100 Mbps |

***REMOVED******REMOVED******REMOVED*** Recommended Requirements

| Component | Specification |
|-----------|---------------|
| CPU | 4+ cores |
| RAM | 8+ GB |
| Storage | 50+ GB SSD |
| OS | Ubuntu 22.04 LTS |
| Network | 1 Gbps |

***REMOVED******REMOVED******REMOVED*** Software Prerequisites

| Software | Version | Required For |
|----------|---------|--------------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Container orchestration |
| Git | 2.30+ | Source control |

For manual (non-Docker) deployments:

| Software | Version | Required For |
|----------|---------|--------------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20 LTS | Frontend runtime |
| PostgreSQL | 15+ | Database |
| Nginx | 1.18+ | Reverse proxy |

***REMOVED******REMOVED*** Architecture Overview

```
                    [Load Balancer / Reverse Proxy]
                              |
                    +---------+---------+
                    |                   |
              [Frontend]          [Backend API]
              (Next.js)            (FastAPI)
                    |                   |
                    +---------+---------+
                              |
                       [PostgreSQL]
```

***REMOVED******REMOVED******REMOVED*** Component Responsibilities

- **Frontend (Next.js)**: Web user interface, client-side routing, React components
- **Backend (FastAPI)**: REST API, business logic, ACGME validation, scheduling engine
- **Database (PostgreSQL)**: Data persistence, relational storage

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Common Administrative Tasks

| Task | Command/Location |
|------|------------------|
| Start all services | `docker compose up -d` |
| Stop all services | `docker compose down` |
| View logs | `docker compose logs -f` |
| Check health | `curl http://localhost:8000/health` |
| Check resilience status | `curl http://localhost:8000/health/resilience` |
| View metrics | `http://localhost:9090` (Prometheus) |
| View dashboards | `http://localhost:3001` (Grafana) |
| Database backup | See [Backup Guide](./backup-restore.md) |
| Add new user | See [User Management](./user-management.md) |
| Service troubleshooting | See [Service Operations](./service-operations.md) |

***REMOVED******REMOVED******REMOVED*** Default Ports

| Service | Port | Protocol |
|---------|------|----------|
| Frontend | 3000 | HTTP |
| Backend API | 8000 | HTTP |
| PostgreSQL | 5432 | TCP |

***REMOVED******REMOVED******REMOVED*** Important File Locations (Docker)

| Description | Location |
|-------------|----------|
| Environment config | `.env` |
| Docker config | `docker-compose.yml` |
| Database volume | `postgres_data` |
| Application logs | Container stdout |

***REMOVED******REMOVED******REMOVED*** Important File Locations (Manual Install)

| Description | Location |
|-------------|----------|
| Backend application | `/opt/residency-scheduler/backend` |
| Frontend application | `/opt/residency-scheduler/frontend` |
| Environment config | `/opt/residency-scheduler/.env` |
| Nginx config | `/etc/nginx/sites-available/residency-scheduler` |
| Backend service | `/etc/systemd/system/residency-backend.service` |
| PostgreSQL data | `/var/lib/postgresql/15/main` |

***REMOVED******REMOVED*** Support and Resources

***REMOVED******REMOVED******REMOVED*** Documentation

- [Setup Guide](../SETUP.md) - Development environment setup
- [API Reference](../API_REFERENCE.md) - API endpoint documentation
- [Architecture](../ARCHITECTURE.md) - System architecture details
- [Error Handling](../ERROR_HANDLING.md) - Error codes and troubleshooting

***REMOVED******REMOVED******REMOVED*** Getting Help

1. Review this administrator manual
2. Check application logs for error details
3. Consult the API documentation for endpoint-specific issues
4. Review the troubleshooting sections in each guide

***REMOVED******REMOVED*** Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | December 2024 | Initial administrator manual |

---

*Residency Scheduler Administrator Manual - Confidential*
