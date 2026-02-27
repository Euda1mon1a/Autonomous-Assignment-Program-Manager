# PostgreSQL 15 Query Tuning Analysis

Upload all files from this folder, then paste the prompt below.

---

## Context

Military residency scheduling system. **Backend:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 15. The database stores schedules, assignments, swap records, conflict alerts, audit logs, and credentials for ~12 residents and ~8 faculty across 13 annual blocks.

**Current state:**
- Three index migration waves already applied (Dec 2025, Feb 2026 ×2)
- Request timing middleware tracks slow queries (>1s warning, >5s critical)
- Using async SQLAlchemy with `selectinload` for N+1 prevention
- No `pg_stat_statements` or `auto_explain` configured yet

**Uploaded files:**
- `services/` — Three heaviest query services (schedule drafts, conflict resolution, call assignments)
- `repositories/` — Data access layer (swap, audit, async base patterns)
- `models/` — Two key models with index definitions (block_assignment, person)
- `migrations/` — Two recent index migrations showing what's already indexed
- `middleware/` — Request timing middleware

**Scale:** Small but complex — ~100 people, ~5,000 assignments/year, ~500 swap records, ~1,000 conflict alerts. Queries are complex (multi-join, temporal range, aggregation) but dataset is small.

---

## Section 1: Query Pattern Classification

Analyze all SQLAlchemy queries in the uploaded service and repository files. Classify each into:

| Pattern | Example | Optimization Strategy |
|---------|---------|----------------------|
| Point lookup | `WHERE id = ?` | Primary key, trivial |
| Composite point | `WHERE person_id = ? AND block_id = ?` | Composite index |
| Range scan | `WHERE date BETWEEN ? AND ?` | B-tree range index |
| Filtered range | `WHERE status = 'pending' AND date > ?` | Partial or composite |
| Multi-table join | `JOIN person ON ...` | Join order, index on FK |
| Aggregation | `GROUP BY person_id` with `COUNT(*)` | Covering index |
| Existence check | `EXISTS (SELECT 1 FROM ...)` | Anti-join optimization |
| Sort + limit | `ORDER BY created_at DESC LIMIT 20` | Index on sort column |

For each query found, report: file, approximate line, classification, tables involved, current index coverage (from migration files).

---

## Section 2: Index Gap Analysis

Compare the queries from Section 1 against the indexes defined in the two migration files:

1. **Covered queries** — Which queries have optimal index support?
2. **Partially covered** — Which queries use an index but not optimally? (e.g., index on `(a, b)` but query filters on `(a, c)`)
3. **Uncovered** — Which queries have NO index support?
4. **Unused indexes** — Are any indexes in the migrations never hit by queries in the uploaded code?

Deliver: Gap analysis table with query, current index, recommended index, expected improvement.

---

## Section 3: PostgreSQL 15 Feature Opportunities

Research PG15-specific features that could benefit this workload:

1. **MERGE statement** — Any upsert patterns in the code that could use MERGE?
2. **JSON path improvements** — Any JSONB queries that benefit from PG15 enhancements?
3. **Improved sort performance** — PG15 has faster sorts for `text` and `numeric`
4. **Parallel query improvements** — Any aggregation queries that could benefit?
5. **Logical replication improvements** — Relevant for future multi-site?
6. **Security improvements** — `GRANT` on schemas, predefined roles
7. **pg_stat_statements improvements** — Better tracking in PG15?

Deliver: Feature-by-feature applicability assessment (YES/NO/MAYBE) with justification.

---

## Section 4: EXPLAIN Plan Prediction

For the **10 most complex queries** found in Section 1, predict what `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` would show:

For each:
1. **Predicted plan** — Sequential scan, index scan, bitmap scan, nested loop, hash join, etc.
2. **Estimated cost** — Relative cost comparison
3. **Bottleneck** — Where time is likely spent
4. **Optimization** — What change would improve the plan (new index, rewrite, materialized view)

Note: You don't have access to the actual database. Predict based on table sizes mentioned in context (~100 people, ~5000 assignments, ~1000 conflicts) and the indexes visible in migration files.

---

## Section 5: Connection Pool & Async Tuning

Analyze the async SQLAlchemy patterns in `async_base.py` and the service files:

1. **Pool sizing** — For a FastAPI app with ~5 concurrent users, what pool settings are optimal? (`pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`)
2. **Session management** — Are sessions properly scoped? Any leak risks?
3. **Eager loading strategy** — Is `selectinload` the right choice vs `joinedload` for this data shape?
4. **Transaction scope** — Are transactions held too long in any service? (Lock contention risk)
5. **Statement caching** — Is `prepared_statement_cache_size` configured?

Deliver: Recommended SQLAlchemy engine configuration with justification.

---

## Section 6: Partial & Expression Indexes

Given the query patterns, recommend partial indexes:

1. **Status filtering** — Many queries filter `WHERE status = 'pending'`. Would `CREATE INDEX ... WHERE status = 'pending'` help?
2. **Active records** — Queries on `WHERE is_active = true`. Partial index worth it?
3. **Date-bounded** — Any queries that only look at recent data? Rolling window index?
4. **Expression indexes** — Any computed expressions in WHERE clauses that could be indexed?

For each recommendation: expected size savings vs full index, maintenance cost, query benefit.

---

## Section 7: Materialized Views & Denormalization

Are any aggregation queries worth precomputing?

1. **Call equity statistics** — `call_assignment_service.py` aggregates call counts per person. Worth materializing?
2. **Conflict summaries** — `conflict_auto_resolver.py` computes complexity scores. Cache as materialized view?
3. **Audit summaries** — `audit_repository.py` joins version tables. Periodic materialization?
4. **Schedule coverage** — Any coverage gap queries that run repeatedly?

For each: refresh frequency, staleness tolerance, storage cost, query speedup estimate.

---

## Section 8: Monitoring & Observability Recommendations

What should we configure for ongoing query performance monitoring?

1. **pg_stat_statements** — Configuration, top-N query identification, reset frequency
2. **auto_explain** — Threshold settings, log format, sampling rate
3. **pg_stat_user_tables** — Which tables to watch for sequential scans
4. **pg_stat_user_indexes** — Identifying unused indexes
5. **Application-level** — What the timing middleware should log beyond response time
6. **Alerting** — What thresholds warrant investigation?

Deliver: Copy-paste `postgresql.conf` additions and a monitoring query dashboard spec.
