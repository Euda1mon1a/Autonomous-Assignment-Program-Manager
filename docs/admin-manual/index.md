# Admin Manual

System administration guide for Residency Scheduler.

---

## Overview

This manual is for system administrators responsible for:

- Initial system setup and configuration
- User management and permissions
- Backup and restore operations
- System monitoring and maintenance

---

## Admin Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-cog: [System Setup](setup.md)
Initial configuration and deployment.
</div>

<div class="feature-card" markdown>
### :material-account-cog: [User Management](users.md)
Managing users, roles, and permissions.
</div>

<div class="feature-card" markdown>
### :material-wrench: [Configuration](configuration.md)
Advanced system configuration.
</div>

<div class="feature-card" markdown>
### :material-backup-restore: [Backup & Restore](backup.md)
Data backup and recovery procedures.
</div>

<div class="feature-card" markdown>
### :material-robot: [AI Interface Guide](ai-interface-guide.md)
Understanding Web vs CLI AI assistants.
</div>

</div>

---

## Administrative Tasks

### User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access, user management |
| **Coordinator** | Schedule generation, assignment management |
| **Faculty** | View schedules, approve swaps |
| **Resident** | View own schedule, request swaps |
| **Clinical Staff** | View schedules (read-only) |

### Maintenance Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Database backup | Daily | Automated via Celery |
| Log rotation | Weekly | Managed by Docker |
| Contingency analysis | Every 4 hours | Automated resilience check |
| Certificate renewal | As needed | SSL/TLS certificates |

---

## Quick Admin Actions

### Create Admin User

```bash
docker-compose exec backend python -c "
from app.core.security import get_password_hash
print(get_password_hash('admin_password'))
"
```

### Database Operations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create backup
docker-compose exec db pg_dump -U postgres residency_scheduler > backup.sql

# Restore backup
docker-compose exec -T db psql -U postgres residency_scheduler < backup.sql
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

---

## Security Considerations

!!! danger "Production Security"
    - Change all default passwords
    - Use HTTPS in production
    - Configure CORS appropriately
    - Enable rate limiting
    - Regular security updates

See [Configuration](configuration.md) for security settings.
