# Codex Guardrails (Startup)

This root `AGENTS.md` exists so Codex startup can always load critical guardrails for this repo.

Authoritative references:
- `.codex/AGENTS.md` (full Codex rules, anti-patterns, run procedure)
- `CLAUDE.md` (project-wide engineering, security, and contract rules)
- `docs/development/AGENTS.md` (monitoring and quality patterns)

If there is any conflict, follow the strictest rule.

---

## HARD BOUNDARIES (NEVER CROSS)

### Validation and types
- NEVER remove or relax Pydantic constraints (`min_length`, `max_length`, `ge`, `le`, `regex`, `pattern`).
- NEVER weaken type annotations (for example `dict[str, int]` to `dict[str, Any]`).
- NEVER add `extra="allow"` / `ConfigDict(extra="allow")` to Pydantic models.
- NEVER change `Literal[...]` types to plain `str`.

### Error handling and security
- NEVER replace generic client-safe errors with `str(e)`.
- NEVER add try/except fallback behavior that can mask failures or create ghost state.
- NEVER reduce authentication or authorization checks.
- NEVER remove rate limiting.
- NEVER log or commit sensitive data (PII, schedules, credentials, deployment data).

### Code structure and scope
- NEVER change function signatures or return types without updating all callers.
- NEVER register a FastAPI router at multiple prefixes.
- NEVER change algorithm thresholds/constants unless explicitly requested.
- NEVER modify more than 30 files in one branch.

### Scheduling and compliance
- NEVER modify scheduling logic, ACGME compliance rules, or constraint definitions without explicit approval.
- NEVER modify models without creating a new Alembic migration.
- NEVER edit existing Alembic migrations.

---

## Code Change Safety Classification

| Change Type | Safety |
|---|---|
| Add `from e` to exception handlers | SAFE |
| Reorder imports | SAFE |
| Fix `datetime.utcnow()` to `datetime.now(UTC)` and both sides of comparisons | SAFE |
| Remove unused imports | CHECK |
| Add type annotations | CHECK |
| Remove Pydantic field constraints | FORBIDDEN |
| Add snake_case/camelCase normalization functions in backend | FORBIDDEN |
| Change Pydantic Field defaults without explicit instruction | FORBIDDEN |
| Add try/except fallback patterns | FORBIDDEN |
| Change error message text to `str(e)` | FORBIDDEN |
| Register routers at new prefixes without explicit instruction | FORBIDDEN |

---

## Known Anti-Patterns to Avoid

- Flexible Validation: removing strict constraints (for example dropping `min_length=32` on webhook secrets).
- Normalization Layer: adding backend `_normalize_*()` response converters for snake/camel case.
- Improved Error Messages: exposing internals with `str(e)` in API responses.
- Defensive Fallback: converting hard failures into silent alternate write paths.
- Lint Comment Removal: deleting `eslint-disable`, `noqa`, or `type: ignore` comments without verifying the underlying type issue is actually resolved.
