# Welcome, System Administrator!

> Your starting point for maintaining the Residency Scheduler system

This guide helps you understand your responsibilities and find critical documentation quickly.

---

## Your First Day

1. **Get Credentials** - Request admin account from IT/security team
2. **System Overview** - Read [Architecture Overview](architecture/overview.md)
3. **Verify Backups** - Confirm backup status per [Backup Guide](admin-manual/backup.md)
4. **Review Emergency Procedures** - Know the [Incident Response Playbook](playbooks/INCIDENT_RESPONSE_PLAYBOOK.md)

---

## Critical Documentation (Priority Order)

| Priority | Document | Why |
|----------|----------|-----|
| 1 | [Incident Response Playbook](playbooks/INCIDENT_RESPONSE_PLAYBOOK.md) | Emergency procedures |
| 2 | [System Maintenance Playbook](playbooks/SYSTEM_MAINTENANCE_PLAYBOOK.md) | Regular maintenance |
| 3 | [Backup & Recovery](admin-manual/backup.md) | Data protection |
| 4 | [Quick Reference](operations/QUICK_REFERENCE.md) | Common commands |
| 5 | [Security Guide](security/README.md) | Security policies |

---

## Daily Checklist

- [ ] Verify overnight backup completed successfully
- [ ] Check system health dashboard/metrics
- [ ] Review error logs for critical issues
- [ ] Check disk space and database size
- [ ] Verify all services are running

### Health Check Commands

```bash
# Check service status
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check database connectivity
docker-compose exec backend python -c "from app.db.session import engine; print('OK')"

# Check recent errors
docker-compose logs --tail=100 backend | grep -i error
```

---

## Weekly Tasks

| Task | How To | When |
|------|--------|------|
| Review access logs | [Audit Guide](security/RBAC_AUDIT.md) | Monday |
| Check certificate expiry | [Security Checklist](security/deployment-checklist.md) | Wednesday |
| Verify backup integrity | [Backup Testing](admin-manual/backup.md#testing) | Friday |
| Review system metrics | [Monitoring Guide](operations/metrics.md) | Friday |

---

## Monthly Tasks

| Task | How To | When |
|------|--------|------|
| User access audit | [RBAC Audit](security/RBAC_AUDIT.md) | 1st week |
| Security patch review | [Security Scanning](operations/SECURITY_SCANNING.md) | 2nd week |
| Performance review | [Load Testing](operations/load-testing.md) | 3rd week |
| Disaster recovery drill | [DR Playbook](admin-manual/backup.md#disaster-recovery) | 4th week |

---

## Key Administrative Functions

### User Management
Create, modify, and deactivate user accounts.
- **Guide**: [User Management](admin-manual/users.md)
- **Roles**: Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA

### Backup & Recovery
Protect system data and enable recovery.
- **Guide**: [Backup Guide](admin-manual/backup.md)
- **Schedule**: Daily full, hourly incremental

### System Configuration
Modify system settings and parameters.
- **Guide**: [Configuration Guide](admin-manual/configuration.md)
- **Sensitive**: Requires restart for some changes

### Database Maintenance
Manage database health and performance.
- **Guide**: [Database Utilities](database/DATABASE_UTILITIES_GUIDE.md)
- **Migration**: [Alembic Guide](development/migrations.md)

---

## Emergency Procedures

### System Down

1. **Check services**: `docker-compose ps`
2. **Check logs**: `docker-compose logs --tail=200`
3. **Restart services**: `docker-compose restart`
4. **Escalate**: If unresolved after 15 minutes

Full procedure: [Incident Response Playbook](playbooks/INCIDENT_RESPONSE_PLAYBOOK.md)

### Data Recovery

1. **Stop write operations** if possible
2. **Identify backup to restore** from backup catalog
3. **Follow restoration procedure**: [Backup Guide](admin-manual/backup.md#restore)
4. **Verify data integrity** after restore

### Security Incident

1. **Contain**: Isolate affected systems
2. **Preserve**: Don't delete logs
3. **Escalate**: Contact security team immediately
4. **Document**: Record all actions taken

---

## Quick Reference

### Common Commands

```bash
# Service management
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose restart        # Restart all services
docker-compose logs -f        # Follow logs

# Database
docker-compose exec backend alembic upgrade head  # Run migrations
docker-compose exec db pg_dump -U postgres scheduler > backup.sql  # Manual backup

# Monitoring
docker-compose exec backend python -m app.cli health  # Health check
```

### Important Paths

| Resource | Location |
|----------|----------|
| Application logs | `/var/log/scheduler/` or `docker logs` |
| Configuration | `.env` and `docker-compose.yml` |
| Backups | Per backup configuration |
| Database | PostgreSQL container volume |

### Default Ports

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│   Backend API   │
│   (Next.js)     │     │   (FastAPI)     │
│   Port 3000     │     │   Port 8000     │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │PostgreSQL│ │  Redis   │ │  Celery  │
             │Port 5432 │ │Port 6379 │ │ Workers  │
             └──────────┘ └──────────┘ └──────────┘
```

Full architecture: [Architecture Overview](architecture/overview.md)

---

## Security Considerations

### OPSEC/PERSEC (Military Context)
- Never commit real names or schedules to version control
- Logs must not contain PII
- Access audit required monthly

### Data Classification
- Schedule data: FOUO equivalent
- Personal data: Privacy Act protected
- Compliance reports: Internal use only

Full guide: [Security Guide](security/README.md)

---

## Learn More

### Essential Documentation
- [Admin Manual](admin-manual/README.md) - Full administration guide
- [Operations Guide](operations/README.md) - Day-to-day operations
- [Security Documentation](security/README.md) - Security policies
- [Database Guide](database/README.md) - Database management

### Playbooks
- [Incident Response](playbooks/INCIDENT_RESPONSE_PLAYBOOK.md)
- [System Maintenance](playbooks/SYSTEM_MAINTENANCE_PLAYBOOK.md)
- [Onboarding](playbooks/ONBOARDING_PLAYBOOK.md)

---

## Get Help

### Internal Resources
1. Check this guide and linked documentation
2. Review [Troubleshooting Guide](troubleshooting.md)
3. Search existing issues in project tracker

### Emergency Contacts
See [Incident Response Playbook](playbooks/INCIDENT_RESPONSE_PLAYBOOK.md#contact--support)

---

*You're the last line of defense for system reliability. Thank you for keeping everything running.*
