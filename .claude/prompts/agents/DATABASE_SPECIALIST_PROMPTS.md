# Database Specialist Agent - Prompt Templates

> **Role:** Database schema design, migrations, optimization, integrity
> **Model:** Claude Opus 4.5
> **Mission:** Maintain high-performance, reliable data layer

## 1. SCHEMA DESIGN TEMPLATE

```
**DATABASE SCHEMA DESIGN**

**ENTITY:** ${ENTITY_NAME}

**TABLE DEFINITION:**
\`\`\`sql
CREATE TABLE ${table_name} (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Core fields
  ${FIELD_1} ${TYPE_1} NOT NULL,
  ${FIELD_2} ${TYPE_2} UNIQUE,

  -- Timestamps
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP,

  -- Relationships
  ${FOREIGN_KEY_1}_id UUID REFERENCES ${TABLE_1}(id),

  -- Constraints
  CONSTRAINT chk_${constraint} CHECK (${condition}),
  INDEX idx_${field} (${field})
);
\`\`\`

**RELATIONSHIPS:**
- ${TABLE_A} → ${TABLE_B}: ${RELATIONSHIP_TYPE}
- Cardinality: ${CARDINALITY}
- Cascade: ${CASCADE_BEHAVIOR}

**INDEXES:**
- Primary: id (automatic)
- Unique: email, username
- Foreign keys: All FKs
- Search: frequently queried fields
- Composite: For multi-field queries

Design normalized, performant schema.
```

## 2. MIGRATION TEMPLATE

```
**DATABASE MIGRATION**

**OPERATION:** ${OPERATION_TYPE}

**ALEMBIC MIGRATION:**
Location: `backend/alembic/versions/xxx_${MIGRATION_NAME}.py`

\`\`\`python
from alembic import op
import sqlalchemy as sa

revision = '${REVISION_ID}'
down_revision = '${PARENT_REVISION}'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create table
    op.create_table(
        '${table_name}',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Add column
    op.add_column('${table}', sa.Column('${column}', ${TYPE}))

    # Create index
    op.create_index('idx_${index}', '${table}', ['${column}'])

    # Add constraint
    op.create_unique_constraint('uq_${name}', '${table}', ['${column}'])

def downgrade() -> None:
    op.drop_table('${table_name}')
    op.drop_column('${table}', '${column}')
    op.drop_index('idx_${index}')
\`\`\`

**TESTING MIGRATION:**
\`\`\`bash
cd backend

# Create migration
alembic revision --autogenerate -m "${MIGRATION_NAME}"

# Review generated migration
cat alembic/versions/xxx_${MIGRATION_NAME}.py

# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Re-apply
alembic upgrade head
\`\`\`

**DATA PRESERVATION:**
- Backup before migration: YES
- Data loss risk: ${DATA_LOSS_RISK}
- Rollback tested: YES

Create and test migration.
```

## 3. INDEX OPTIMIZATION TEMPLATE

```
**INDEX ANALYSIS & OPTIMIZATION**

**CURRENT INDEXES:**
\`\`\`sql
SELECT * FROM pg_indexes WHERE tablename = '${table_name}';
\`\`\`

**QUERY PERFORMANCE ANALYSIS:**
\`\`\`sql
-- Analyze query plan
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM ${table_name}
WHERE ${condition}
ORDER BY ${order};
\`\`\`

**INDEX RECOMMENDATIONS:**
1. **Missing Indexes:**
   - For frequently filtered fields: CREATE INDEX
   - For sort operations: CREATE INDEX
   - Composite indexes for multi-field queries

2. **Unused Indexes:**
   \`\`\`sql
   SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
   \`\`\`
   - Drop unused indexes

3. **Index Size:**
   \`\`\`sql
   SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid))
   FROM pg_stat_user_indexes
   ORDER BY pg_relation_size(indexrelid) DESC;
   \`\`\`

**OPTIMIZATION STEPS:**
1. Profile slow queries
2. Create targeted indexes
3. Monitor query performance
4. Remove unused indexes
5. Maintain statistics: ANALYZE

Optimize database indexes.
```

## 4. QUERY OPTIMIZATION TEMPLATE

```
**QUERY OPTIMIZATION**

**SLOW QUERY:**
\`\`\`sql
SELECT * FROM ${table}
WHERE ${condition}
ORDER BY ${order};
-- Current: ${SLOW_TIME}ms
\`\`\`

**ANALYSIS:**
1. Run EXPLAIN ANALYZE
2. Check for sequential scans
3. Verify indexes exist
4. Check table statistics

**OPTIMIZATION STRATEGY:**
1. Add missing indexes
2. Rewrite query
3. Use JOIN instead of subquery
4. Limit result set

**OPTIMIZED QUERY:**
\`\`\`sql
SELECT ${fields}
FROM ${table1}
JOIN ${table2} ON ${join_condition}
WHERE ${optimized_condition}
ORDER BY ${order}
LIMIT ${limit};
-- Expected: ${EXPECTED_TIME}ms
\`\`\`

**VERIFICATION:**
- Run EXPLAIN ANALYZE on optimized query
- Benchmark against slow version
- Deploy with monitoring

Optimize slow queries.
```

## 5. BACKUP & RECOVERY TEMPLATE

```
**BACKUP & RECOVERY PLAN**

**BACKUP STRATEGY:**
- Frequency: Daily (automated)
- Retention: 30 days
- Location: ${BACKUP_LOCATION}
- Type: Full + incremental

**BACKUP PROCEDURE:**
\`\`\`bash
# Full backup
pg_dump -U ${user} -d ${database} > backup_$(date +%Y%m%d).sql

# Compressed
pg_dump -U ${user} -d ${database} | gzip > backup_$(date +%Y%m%d).sql.gz

# From Docker
docker-compose exec db pg_dump -U scheduler -d residency_scheduler > backup.sql
\`\`\`

**RECOVERY PROCEDURE:**
\`\`\`bash
# Restore from backup
psql -U ${user} -d ${database} < backup.sql

# From compressed
gunzip < backup.sql.gz | psql -U ${user} -d ${database}

# From Docker
docker-compose exec -T db psql -U scheduler -d residency_scheduler < backup.sql
\`\`\`

**DISASTER RECOVERY:**
- RTO (Recovery Time Objective): ${RTO}
- RPO (Recovery Point Objective): ${RPO}
- Tested recovery: Monthly

Maintain backup & recovery procedures.
```

## 6. MONITORING TEMPLATE

```
**DATABASE MONITORING**

**KEY METRICS:**
\`\`\`sql
-- Connection count
SELECT count(*) as connections FROM pg_stat_activity;

-- Cache hit ratio
SELECT
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;

-- Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Long running queries
SELECT pid, usename, application_name, state, query, query_start
FROM pg_stat_activity
WHERE state != 'idle'
AND query_start < NOW() - INTERVAL '5 minutes';
\`\`\`

**ALERTS:**
- Connection count > ${CONN_THRESHOLD}
- Cache hit ratio < ${CACHE_THRESHOLD}%
- Slow query > ${SLOW_QUERY_THRESHOLD}ms
- Disk usage > ${DISK_THRESHOLD}%

Monitor database health.
```

## 7. STATUS REPORT TEMPLATE

```
**DATABASE SPECIALIST STATUS REPORT**

**SCHEMA:**
- Tables: ${TABLE_COUNT}
- Indexes: ${INDEX_COUNT}
- Constraints: ${CONSTRAINT_COUNT}

**PERFORMANCE:**
- Query performance (p95): ${P95_QUERY}ms
- Cache hit ratio: ${CACHE_HIT}%
- Slow queries: ${SLOW_COUNT}
- Connection pool: ${CONN_USED}/${CONN_TOTAL}

**MAINTENANCE:**
- Last VACUUM: ${LAST_VACUUM}
- Last ANALYZE: ${LAST_ANALYZE}
- Last backup: ${LAST_BACKUP}

**ISSUES:**
${ISSUES}

**OPTIMIZATIONS:**
${OPTIMIZATIONS}

**NEXT:** ${NEXT_GOALS}
```

---

*Last Updated: 2025-12-31*
*Agent: Database Specialist*
*Version: 1.0*
