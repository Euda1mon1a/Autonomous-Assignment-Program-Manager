# Codex App Automation Prompts (Reference)

Use these in the Codex macOS app Automations pane.

## Backend env preflight

For backend commands in Codex worktrees, use:

```bash
python3 scripts/ops/codex_worktree_env_exec.py -- <your backend command>
```

Example:

```bash
python3 scripts/ops/codex_worktree_env_exec.py -- pytest -q backend/tests/test_core.py -k database_url
```

## Daily Bug Scan

```
Scan commits from the last 24 hours for likely bugs. Focus on:
- Missing await on async functions
- Unclosed resources (db sessions, file handles)
- Off-by-one errors in date/block logic
- Null/undefined access without guards

For each bug found, create a minimal fix. If no bugs, report "No issues found."
```

## Test Gap Detection

```
Identify untested code paths added in the last 7 days. Check:
- backend/app/api/routes/ for endpoints without test coverage
- backend/app/services/ for service methods without unit tests
- frontend/src/hooks/ for hooks without test files

For each gap, write a focused test. Prioritize ACGME compliance and scheduling logic.
```

## Security Sweep

```
Run a security audit on the codebase:
- Check for hardcoded secrets or credentials
- Review auth routes for bypass vulnerabilities
- Scan for SQL injection in raw queries
- Check rate limiting on sensitive endpoints
- Verify CORS and cookie settings

Report findings with severity (P1/P2/P3). Propose fixes for P1/P2.
```

## Pre-release Check

```
Verify release readiness:
- CHANGELOG.md updated for recent commits
- No pending Alembic migrations without documentation
- Feature flags documented in docs/
- No TODO or FIXME in committed code from last 48 hours
- OpenAPI types match frontend (run generate:types:check)

Report blockers. If clean, report "Ready for release."
```

## Dead Code Detection

```
Find dead code in the codebase:
- Unused imports in Python and TypeScript files
- Functions/methods never called
- Unreachable code paths
- Commented-out code blocks older than 30 days

Remove dead code and create a commit. Skip files in tests/ and __pycache__.
```

## Type Coverage Expansion

```
Improve type coverage:
- Add type hints to untyped Python functions in backend/app/
- Fix mypy errors that are currently ignored
- Add missing TypeScript types in frontend/src/
- Replace 'any' types with proper interfaces

Focus on public APIs and service layer. Create minimal, focused commits.
```

## API Contract Sync

```
Ensure frontend types match backend:
- Regenerate OpenAPI types
- Compare any diffs against frontend usage
- Fix mismatches and update typings

Report if changes are required. Create a commit if needed.
```

## Doc Freshness

```
Scan docs/ for stale references, broken links, or outdated instructions.
Fix obvious issues and report any ambiguous ones.
```
