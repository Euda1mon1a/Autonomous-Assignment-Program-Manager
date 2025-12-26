<!--
Safe schedule generation with mandatory backup.
REQUIRES database backup before any write operations.
-->

Invoke the safe-schedule-generation skill to generate schedules.

## Arguments

- `$ARGUMENTS` - Block number and year (e.g., "Block 10 2026")

## MANDATORY STEPS

1. Verify recent database backup exists (< 2 hours)
2. If no backup: run ./scripts/backup-db.sh first
3. Confirm with user before generation
4. Run schedule generation
5. Validate results (coverage > 80%, violations < 5)
6. Offer rollback if results are poor

## Backup Verification

```bash
ls -la backups/postgres/*.sql.gz | tail -1
```
