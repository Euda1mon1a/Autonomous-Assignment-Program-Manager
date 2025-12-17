***REMOVED*** Backup & Restore

Data backup and recovery procedures.

---

***REMOVED******REMOVED*** Automated Backups

The system creates daily automated backups via Celery.

***REMOVED******REMOVED******REMOVED*** Backup Location

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

***REMOVED******REMOVED*** Manual Backup

***REMOVED******REMOVED******REMOVED*** Database Backup

```bash
***REMOVED*** Create backup
docker-compose exec db pg_dump -U postgres residency_scheduler > backup.sql

***REMOVED*** Compressed backup
docker-compose exec db pg_dump -U postgres residency_scheduler | gzip > backup.sql.gz
```

***REMOVED******REMOVED******REMOVED*** Full System Backup

```bash
***REMOVED*** Stop services
docker-compose down

***REMOVED*** Backup volumes
tar -czvf backup-full.tar.gz ./data

***REMOVED*** Restart services
docker-compose up -d
```

---

***REMOVED******REMOVED*** Restore Procedures

***REMOVED******REMOVED******REMOVED*** Database Restore

```bash
***REMOVED*** Restore from backup
docker-compose exec -T db psql -U postgres residency_scheduler < backup.sql
```

***REMOVED******REMOVED******REMOVED*** Full System Restore

```bash
***REMOVED*** Stop services
docker-compose down

***REMOVED*** Restore volumes
tar -xzvf backup-full.tar.gz

***REMOVED*** Start services
docker-compose up -d

***REMOVED*** Run migrations
docker-compose exec backend alembic upgrade head
```

---

***REMOVED******REMOVED*** Backup Best Practices

!!! tip "Backup Recommendations"
    - Test restores regularly
    - Store backups off-site
    - Encrypt sensitive backups
    - Document restore procedures
