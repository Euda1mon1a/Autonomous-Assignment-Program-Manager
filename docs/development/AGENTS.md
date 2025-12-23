***REMOVED*** AI Agent Instructions

This document provides guidance for AI coding assistants (Codex, Claude, etc.) working on this codebase.

***REMOVED******REMOVED*** Project Overview

**Residency Scheduler** - A medical residency program scheduling system with ACGME compliance validation. The system manages complex scheduling for medical residency programs while ensuring compliance with federal regulations.

***REMOVED******REMOVED******REMOVED*** Tech Stack
- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **Monitoring**: Prometheus, Grafana, Loki

---

***REMOVED******REMOVED*** Codex Background Monitoring Instructions

When performing background code health assessments, focus on these categories of subtle issues that accumulate over time.

***REMOVED******REMOVED******REMOVED*** 🔴 Priority 1: Code Rot Detection

***REMOVED******REMOVED******REMOVED******REMOVED*** 1.1 Stubbed/Placeholder Code
Look for functions that appear complete but are actually placeholders:

```python
***REMOVED*** Search patterns:
***REMOVED*** - "***REMOVED*** TODO" in function bodies
***REMOVED*** - "***REMOVED*** Placeholder" comments
***REMOVED*** - Functions returning hardcoded False/None
***REMOVED*** - "pass" as sole implementation
```

**Known issues to track:**
- `backend/app/services/swap_executor.py:60-62` - TODOs indicate non-functional persistence
- `backend/app/services/swap_executor.py:84-93` - `rollback_swap()` and `can_rollback()` return hardcoded False

***REMOVED******REMOVED******REMOVED******REMOVED*** 1.2 Silent Failure Patterns
Identify exception handlers that swallow errors:

```python
***REMOVED*** Anti-patterns to flag:
except (ValueError, TypeError):
    pass  ***REMOVED*** Silent failure - no logging

except Exception as e:
    continue  ***REMOVED*** Error ignored
```

**Known issues:**
- `backend/app/api/routes/portal.py:443,451,547,556` - Invalid dates silently disappear

***REMOVED******REMOVED******REMOVED******REMOVED*** 1.3 Placeholder Workarounds
Find temporary hacks that assume future fixes:

```python
***REMOVED*** Example anti-pattern:
target_faculty_id = faculty.id  ***REMOVED*** Placeholder
```

**Known issues:**
- `backend/app/api/routes/portal.py:271` - Uses faculty's own ID as placeholder for marketplace requests

---

***REMOVED******REMOVED******REMOVED*** 🟡 Priority 2: Consistency Drift

***REMOVED******REMOVED******REMOVED******REMOVED*** 2.1 DateTime Handling
The codebase mixes UTC and local time. Flag any new instances:

```python
***REMOVED*** Inconsistent - should pick ONE:
datetime.utcnow()  ***REMOVED*** Some files use this
datetime.now()     ***REMOVED*** Other files use this
```

**Recommendation:** Standardize on `datetime.now(timezone.utc)` per Python 3.11+ best practices.

***REMOVED******REMOVED******REMOVED******REMOVED*** 2.2 Response Format Consistency
Three response patterns exist - flag divergence:

| Pattern | Example Location | When to Use |
|---------|------------------|-------------|
| Inline dict | `portal.py:380` | Avoid - use Pydantic |
| Pydantic schema | `portal.py:114` | Preferred |
| Service result | `swap_request_service.py:232` | For service layer |

***REMOVED******REMOVED******REMOVED******REMOVED*** 2.3 Error Handling Patterns
Ensure consistent HTTPException usage:
- Include error codes
- Don't expose internal details to clients
- Log before raising

---

***REMOVED******REMOVED******REMOVED*** 🟢 Priority 3: Type Safety Erosion

***REMOVED******REMOVED******REMOVED******REMOVED*** 3.1 Untyped Dictionaries
Flag new uses of `dict[str, Any]` in core business logic:

```python
***REMOVED*** Anti-pattern in service/business logic:
def process_data(data: dict[str, Any]) -> dict[str, Any]:
    ...

***REMOVED*** Preferred - use TypedDict or Pydantic:
class ProcessInput(TypedDict):
    field1: str
    field2: int
```

**Known hotspot:** `backend/app/resilience/mtf_compliance.py` - 40+ occurrences

***REMOVED******REMOVED******REMOVED******REMOVED*** 3.2 Type Ignore Comments
Track and reduce `***REMOVED*** type: ignore` usage:

**Known issues:**
- `backend/app/resilience/simulation/__init__.py:42`
- `backend/app/resilience/simulation/base.py:20,177`

***REMOVED******REMOVED******REMOVED******REMOVED*** 3.3 Missing Type Annotations
Flag functions without return type hints in core modules:

```python
***REMOVED*** Missing annotation:
def _get_week_start(any_date):  ***REMOVED*** No type hint!
    ...

***REMOVED*** Should be:
def _get_week_start(any_date: date) -> date:
    ...
```

---

***REMOVED******REMOVED******REMOVED*** 🔵 Priority 4: Documentation Drift

***REMOVED******REMOVED******REMOVED******REMOVED*** 4.1 Docstring vs Implementation
Compare docstrings against actual behavior:

**Known issue:**
- `portal.py:51-55` - Docstring promises "conflict indicators" but `has_conflict` always returns `False`

***REMOVED******REMOVED******REMOVED******REMOVED*** 4.2 TODO Age Tracking
Flag TODOs older than 6 months. Check git blame for age.

***REMOVED******REMOVED******REMOVED******REMOVED*** 4.3 Dead Documentation References
Verify referenced docs exist:
- ~~`docs/TODO_RESILIENCE.md`~~ - Fixed: now references `docs/architecture/resilience.md`

---

***REMOVED******REMOVED******REMOVED*** ⚪ Priority 5: Performance Patterns

***REMOVED******REMOVED******REMOVED******REMOVED*** 5.1 N+1 Query Detection
Look for patterns that trigger multiple queries:

```python
***REMOVED*** Potential N+1:
assignments = db.query(Assignment).all()
for a in assignments:
    print(a.block.date)  ***REMOVED*** Lazy load per iteration
```

**Known hotspots:** `portal.py` has 54+ `.all()` queries

***REMOVED******REMOVED******REMOVED******REMOVED*** 5.2 Missing Eager Loading
Flag relationship access without `joinedload`/`selectinload`:

```python
***REMOVED*** Should use eager loading:
.options(joinedload(Assignment.block))
```

---

***REMOVED******REMOVED*** Assessment Output Format

When reporting findings, use this structure:

```markdown
***REMOVED******REMOVED*** Code Health Assessment - [DATE]

***REMOVED******REMOVED******REMOVED*** Critical Issues (Action Required)
| File:Line | Category | Description | Age |
|-----------|----------|-------------|-----|
| ... | ... | ... | ... |

***REMOVED******REMOVED******REMOVED*** Warnings (Monitor)
| File:Line | Category | Description | Age |
|-----------|----------|-------------|-----|
| ... | ... | ... | ... |

***REMOVED******REMOVED******REMOVED*** Improvements (Nice to Have)
| File:Line | Category | Description |
|-----------|----------|-------------|
| ... | ... | ... |

***REMOVED******REMOVED******REMOVED*** Metrics
- Total TODOs: X (Y new since last assessment)
- Type coverage: X%
- Silent exception handlers: X
- Placeholder code blocks: X
```

---

***REMOVED******REMOVED*** Files to Prioritize

These files have the highest concentration of known issues:

1. `backend/app/services/swap_executor.py` - Stub implementations
2. `backend/app/api/routes/portal.py` - Multiple pattern issues
3. `backend/app/notifications/tasks.py` - Stubbed email/webhook
4. `backend/app/resilience/mtf_compliance.py` - Type safety

---

***REMOVED******REMOVED*** What NOT to Flag

- Test files using mocks/stubs (intentional)
- `***REMOVED*** type: ignore` on third-party library issues
- TODOs in test files
- Placeholder data in fixtures/seeds

---

***REMOVED******REMOVED*** Conventions to Enforce

1. **Imports**: Group stdlib, third-party, local with blank lines
2. **Logging**: Use structured logging with context
3. **Errors**: Raise specific exceptions, not generic `Exception`
4. **Types**: Prefer Pydantic models over raw dicts
5. **Queries**: Use repository pattern, not inline queries in routes
