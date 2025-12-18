<!--
Run database migrations using Alembic.
Applies pending migrations to update the database schema.
-->

Run database migrations using Alembic:

1. Check the current database migration status
2. Review any pending migrations
3. Apply migrations to bring the database up to date
4. Verify the migration was successful

Execute these commands:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Check current migration status
alembic current

# Show migration history
alembic history

# Check for pending migrations
alembic heads

# Apply all pending migrations
alembic upgrade head
```

After running migrations:
- Report the previous migration version
- List all migrations that were applied
- Show the new current migration version
- Verify no errors occurred during migration

Key migration files are located in:
- Configuration: `/home/user/Autonomous-Assignment-Program-Manager/backend/alembic.ini`
- Migration scripts: `/home/user/Autonomous-Assignment-Program-Manager/backend/alembic/versions/`
- Environment setup: `/home/user/Autonomous-Assignment-Program-Manager/backend/alembic/env.py`

If you need to create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

If you need to rollback one migration:
```bash
alembic downgrade -1
```

Always review migration scripts before applying them to production databases.
