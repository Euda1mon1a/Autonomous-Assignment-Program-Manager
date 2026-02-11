# AAPM — Autonomous Coding Tasks

> Format: `- [ ] description` | Coder picks next unchecked task, commits to claude/ branch.
> AAPM requires manual review — branches are NOT auto-merged.

## Backend Quality

- [ ] Add integration tests for the schedule generation pipeline — test that /api/scheduler/generate returns valid assignments for a simple 2-resident, 1-block scenario using the test DB
- [ ] Audit all API routes for consistent error response format — ensure every route returns {"detail": "..."} on 4xx/5xx, not raw strings or HTML
- [ ] Add request validation tests for routes that accept complex JSON bodies (block_scheduler, half_day_assignments, schedule_drafts) — test malformed input returns 422
- [ ] Review and add missing type hints in backend/app/services/ — run mypy on the services directory and fix any errors
- [ ] Add retry logic with exponential backoff to the RAG embedding ingestion pipeline (backend/app/services/rag/) for transient DB connection failures

## Frontend Quality

- [ ] Audit all pages for missing loading states — ensure every page that fetches data shows a skeleton/spinner, not a blank screen
- [ ] Add error boundary components to the top 5 most-visited admin pages (dashboard, scheduling, people, compliance, swaps)
- [ ] Review all useEffect hooks for missing dependency arrays — run eslint rule react-hooks/exhaustive-deps and fix warnings
- [ ] Add keyboard navigation tests for the schedule grid component — tab, arrow keys, enter should all work

## Infrastructure

- [ ] Add a /api/health/deep endpoint that checks DB connectivity, Redis connectivity, and returns version info from pyproject.toml
- [ ] Create a DB migration that adds indexes on the most-queried columns (check slow query log or EXPLAIN ANALYZE on common queries)
