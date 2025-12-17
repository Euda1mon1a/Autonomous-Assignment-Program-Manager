***REMOVED*** Admin Manual

System administration guide for Residency Scheduler.

---

***REMOVED******REMOVED*** Overview

This manual is for system administrators responsible for:

- Initial system setup and configuration
- User management and permissions
- Backup and restore operations
- System monitoring and maintenance

---

***REMOVED******REMOVED*** Admin Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-cog: [System Setup](setup.md)
Initial configuration and deployment.
</div>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-account-cog: [User Management](users.md)
Managing users, roles, and permissions.
</div>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-wrench: [Configuration](configuration.md)
Advanced system configuration.
</div>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-backup-restore: [Backup & Restore](backup.md)
Data backup and recovery procedures.
</div>

</div>

---

***REMOVED******REMOVED*** Administrative Tasks

***REMOVED******REMOVED******REMOVED*** User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access, user management |
| **Coordinator** | Schedule generation, assignment management |
| **Faculty** | View schedules, approve swaps |
| **Resident** | View own schedule, request swaps |
| **Clinical Staff** | View schedules (read-only) |

***REMOVED******REMOVED******REMOVED*** Maintenance Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Database backup | Daily | Automated via Celery |
| Log rotation | Weekly | Managed by Docker |
| Contingency analysis | Every 4 hours | Automated resilience check |
| Certificate renewal | As needed | SSL/TLS certificates |

---

***REMOVED******REMOVED*** Quick Admin Actions

***REMOVED******REMOVED******REMOVED*** Create Admin User

```bash
docker-compose exec backend python -c "
from app.core.security import get_password_hash
print(get_password_hash('admin_password'))
"
```

***REMOVED******REMOVED******REMOVED*** Database Operations

```bash
***REMOVED*** Run migrations
docker-compose exec backend alembic upgrade head

***REMOVED*** Create backup
docker-compose exec db pg_dump -U postgres residency_scheduler > backup.sql

***REMOVED*** Restore backup
docker-compose exec -T db psql -U postgres residency_scheduler < backup.sql
```

***REMOVED******REMOVED******REMOVED*** View Logs

```bash
***REMOVED*** All services
docker-compose logs -f

***REMOVED*** Specific service
docker-compose logs -f backend

***REMOVED*** Last 100 lines
docker-compose logs --tail=100 backend
```

---

***REMOVED******REMOVED*** Security Considerations

!!! danger "Production Security"
    - Change all default passwords
    - Use HTTPS in production
    - Configure CORS appropriately
    - Enable rate limiting
    - Regular security updates

See [Configuration](configuration.md) for security settings.
