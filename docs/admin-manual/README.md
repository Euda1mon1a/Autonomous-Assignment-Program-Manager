# Administrator Manual

> Complete guide for managing the Residency Scheduler system

**New Admin?** Start with [START_HERE_ADMIN.md](../START_HERE_ADMIN.md) for a quick orientation.

---

## Quick Navigation by Task

### First-Time Setup
- [Installation Guide](../getting-started/installation.md) - System installation
- [Configuration Guide](configuration.md) - Initial configuration
- [User Account Setup](users.md) - Creating user accounts

### Daily Operations
- [Backup Procedures](backup.md) - Daily/weekly/monthly backups
- [Health Monitoring](../operations/metrics.md) - System health checks
- [Log Management](../operations/logging.md) - Viewing and managing logs

### User Management
- [Creating Accounts](users.md#creating-accounts) - New user setup
- [Role Assignment](users.md#roles) - Configuring permissions
- [Access Control](../security/RBAC_AUDIT.md) - RBAC and access audit

### Data Management
- [People Management](people-management.md) - Bulk edit residents and faculty
- [Rotation Templates](rotation-templates.md) - Rotation abbreviations and mappings
- [Procedure Credentials](credentials.md) - Faculty credentialing matrix

### Emergency Procedures
- [Incident Response](../playbooks/INCIDENT_RESPONSE_PLAYBOOK.md) - Emergency response steps
- [Disaster Recovery](backup.md#disaster-recovery) - Recovery procedures
- [Emergency Contacts](../playbooks/README.md#emergency-quick-reference) - Contact list

### System Maintenance
- [Database Maintenance](../database/DATABASE_UTILITIES_GUIDE.md) - DB operations
- [Upgrade Procedures](../playbooks/SYSTEM_MAINTENANCE_PLAYBOOK.md) - System updates
- [Security Patching](../operations/SECURITY_SCANNING.md) - Security updates

---

## Admin Guides

| Guide | Description |
|-------|-------------|
| [People Management](people-management.md) | Bulk edit residents and faculty |
| [Procedure Credentials](credentials.md) | Faculty credentialing matrix |
| [Rotation Templates](rotation-templates.md) | Rotation abbreviations and mappings |
| [Configuration](configuration.md) | System settings |
| [Backup & Recovery](backup.md) | Data protection |
| [User Management](users.md) | Account administration |
| [AI Interface Guide](ai-interface-guide.md) | Claude Code integration |
| [MCP Admin Guide](mcp-admin-guide.md) | MCP server administration |

---

## Admin Checklists

### Daily Checklist
- [ ] Verify overnight backup completed
- [ ] Check system health dashboard
- [ ] Review any error alerts
- [ ] Check disk space usage

### Weekly Checklist
- [ ] Review access logs
- [ ] Check certificate expiry
- [ ] Verify backup integrity test
- [ ] Review system metrics

### Monthly Checklist
- [ ] User access audit
- [ ] Security patch review
- [ ] Performance review
- [ ] Disaster recovery drill

---

## Quick Reference

### Default Ports

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

### Common Commands

```bash
# Service management
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose restart        # Restart all services
docker-compose logs -f        # Follow logs

# Health check
curl http://localhost:8000/health

# Database backup
docker-compose exec db pg_dump -U postgres scheduler > backup.sql
```

### Important Paths

| Resource | Location |
|----------|----------|
| Application logs | `/var/log/scheduler/` or `docker logs` |
| Configuration | `.env` and `docker-compose.yml` |
| Database | PostgreSQL container volume |

---

## See Also

- [START_HERE_ADMIN.md](../START_HERE_ADMIN.md) - Quick start for new admins
- [Operational Playbooks](../playbooks/README.md) - Step-by-step procedures
- [API Reference](../api/README.md) - For automation
- [Developer Guide](../development/README.md) - For customization
- [Security Documentation](../security/README.md) - Security policies
