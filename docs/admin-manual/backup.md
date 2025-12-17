# Backup & Restore

Data backup and recovery procedures.

---

## Automated Backups

The system creates daily automated backups via Celery.

### Backup Location

```
/backups/
├── daily/
│   ├── backup-2025-01-15.sql
│   └── backup-2025-01-14.sql
├── weekly/
│   └── backup-week-03.sql
└── monthly/
    └── backup-2025-01.sql
```

---

## Manual Backup

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres residency_scheduler > backup.sql

# Compressed backup
docker-compose exec db pg_dump -U postgres residency_scheduler | gzip > backup.sql.gz
```

### Full System Backup

```bash
# Stop services
docker-compose down

# Backup volumes
tar -czvf backup-full.tar.gz ./data

# Restart services
docker-compose up -d
```

---

## Restore Procedures

### Database Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U postgres residency_scheduler < backup.sql
```

### Full System Restore

```bash
# Stop services
docker-compose down

# Restore volumes
tar -xzvf backup-full.tar.gz

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

---

## Backup Best Practices

!!! tip "Backup Recommendations"
    - Test restores regularly
    - Store backups off-site
    - Encrypt sensitive backups
    - Document restore procedures
