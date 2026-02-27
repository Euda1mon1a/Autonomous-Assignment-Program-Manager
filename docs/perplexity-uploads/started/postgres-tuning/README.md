# PostgreSQL Query Tuning Upload

Upload folder for analyzing SQLAlchemy query patterns and PostgreSQL 15 optimization opportunities.

## Usage

1. Upload all files from this folder to Perplexity Computer
2. Paste the contents of `PROMPT.md` as the session prompt

## File Manifest

| Upload Path | Original Source Path | Size |
|-------------|---------------------|------|
| **services/** (query-heavy) | | |
| `services/schedule_draft_service.py` | `backend/app/services/schedule_draft_service.py` | ~80K |
| `services/conflict_auto_resolver.py` | `backend/app/services/conflict_auto_resolver.py` | ~60K |
| `services/call_assignment_service.py` | `backend/app/services/call_assignment_service.py` | ~40K |
| **repositories/** (data access) | | |
| `repositories/swap_repository.py` | `backend/app/repositories/swap_repository.py` | 13K |
| `repositories/audit_repository.py` | `backend/app/repositories/audit_repository.py` | 16K |
| `repositories/async_base.py` | `backend/app/repositories/async_base.py` | 16K |
| **models/** (schema + indexes) | | |
| `models/block_assignment.py` | `backend/app/models/block_assignment.py` | ~8K |
| `models/person.py` | `backend/app/models/person.py` | ~12K |
| **migrations/** (existing indexes) | | |
| `migrations/20260219_indexes.py` | `backend/alembic/versions/20260219_add_composite_query_indexes.py` | 9K |
| `migrations/20260212_indexes.py` | `backend/alembic/versions/20260212_add_query_perf_indexes.py` | 11K |
| **middleware/** (timing) | | |
| `middleware/timing_middleware.py` | `backend/app/middleware/timing_middleware.py` | ~3K |

## Sections

| # | Section | Focus |
|---|---------|-------|
| 1 | Query Pattern Classification | Categorize all queries by type (point, range, join, aggregation) |
| 2 | Index Gap Analysis | Compare queries against existing indexes |
| 3 | PG15 Features | MERGE, JSON path, parallel query, security |
| 4 | EXPLAIN Prediction | Predicted query plans for top 10 complex queries |
| 5 | Connection Pool Tuning | Async SQLAlchemy pool + session configuration |
| 6 | Partial Indexes | Status-filtered, date-bounded, expression indexes |
| 7 | Materialized Views | Precomputed aggregations for call equity, conflicts |
| 8 | Monitoring | pg_stat_statements, auto_explain, alerting thresholds |

## Notes

- No PII: all source code and migration DDL
- Scale: ~100 people, ~5,000 assignments/year, ~1,000 conflict alerts
- Three index migration waves already applied
- Using async SQLAlchemy 2.0 with selectinload
