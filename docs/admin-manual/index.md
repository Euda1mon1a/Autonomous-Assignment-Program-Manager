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

## Operational Lessons Learned

Use these safeguards to avoid schedule loss and unexpected changes:

- Regenerate schedules only when necessary and confirm the date range.
- Preserve manual overrides with a written reason and timestamp.
- Treat emergency closures as manual decisions (do not auto-cancel clinics).
- Prefer draft runs before overwriting a stable schedule.
- Document any exception to coverage or supervision rules.
- **Split terminal is not shared context**: an AI session cannot see another AI's terminal state; coordinate explicitly.

---

## "main" and "origin" Explained (Clinician-Friendly)

If you ever follow terminal steps, you may see "main" and "origin." They are just names:

- **main**: the official, approved version of the system (the source of truth).
- **origin**: the remote copy of that official version (the GitHub server).

Think of it like this:
- **main** = the published policy binder.
- **origin** = the same binder stored in a central, shared cabinet.

If the system says "main and origin are aligned," your local copy matches the official version.

---

## Parallel AI Sessions (What “Split Terminal” Really Means)

If you are running multiple AI tools (e.g., Claude Web and Codex), they do **not** share a live terminal. Each session sees only what is on disk when it runs its own commands.

Practical guidance:

- Assume AI sessions are **independent** unless you explicitly coordinate.
- If two sessions are working on the same files, expect conflicts.
- Always check `git status -sb` before and after AI runs.
- Prefer one “driver” session at a time for changes that touch the same files.

---

## Security Considerations

!!! danger "Production Security"
    - Change all default passwords
    - Use HTTPS in production
    - Configure CORS appropriately
    - Enable rate limiting
    - Regular security updates

See [Configuration](configuration.md) for security settings.
