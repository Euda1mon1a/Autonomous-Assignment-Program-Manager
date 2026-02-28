# SQL Identifier Security Layer

> **Module:** `backend/app/db/sql_identifiers.py`
> **Added:** PR #1197 (Feb 26, 2026)
> **Last Updated:** 2026-02-26

---

## Overview

Prevents SQL injection via identifier validation and quoting. All SQL identifiers (table names, schema names, column names, policy names) must pass through `validate_identifier()` before interpolation into `text()` calls.

## API

```python
from app.db.sql_identifiers import validate_identifier

# Validates and double-quotes an identifier for safe SQL interpolation
safe_name = validate_identifier("my_table", "table")
# Returns: '"my_table"'

# Raises ValueError on invalid input
validate_identifier("DROP TABLE users; --", "table")  # ValueError
```

### Parameters

| Parameter         | Type  | Description                                           |
| ----------------- | ----- | ----------------------------------------------------- |
| `name`            | `str` | The raw identifier to validate                        |
| `identifier_type` | `str` | One of: `"table"`, `"schema"`, `"column"`, `"policy"` |

### Validation Rules

- Must be non-empty string
- Must match pattern: `^[a-zA-Z_][a-zA-Z0-9_]*$` (alphanumeric + underscore, starts with letter/underscore)
- No SQL reserved words in isolation
- No semicolons, quotes, or special characters
- Returns double-quoted identifier ready for SQL interpolation

## Coverage

Fixed 20+ instances across 9 files:

| File                        | Identifiers Protected                                          |
| --------------------------- | -------------------------------------------------------------- |
| `backup.py`                 | Table names in SELECT/TRUNCATE                                 |
| `strategies.py`             | Table names in backup queries                                  |
| `db_admin.py`               | Table names in VACUUM                                          |
| `maintenance_commands.py`   | Table names in REINDEX                                         |
| `health/checks/database.py` | Table names in health queries                                  |
| `pool/health.py`            | Numeric values → bind parameters                               |
| `query_optimizer.py`        | EXPLAIN with compiled statements                               |
| `partitioning.py`           | Partition names in DDL                                         |
| `tenancy/isolation.py`      | Schema/table/policy names in DDL, SET values → bind parameters |

## Why Not Just Use ORM?

These files perform **infrastructure-level** operations (VACUUM, REINDEX, DDL, RLS policies) that cannot be expressed through SQLAlchemy ORM. Raw `text()` calls are unavoidable here, but identifiers must still be safe.

## Related PRs

- **#1197**: Initial implementation (20+ fixes)
- **#1200**: Codex P1/P2 follow-up feedback
- **#1201**: Codex round 2 + Gemini code review findings
