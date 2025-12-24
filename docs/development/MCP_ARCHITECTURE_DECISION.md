***REMOVED*** MCP Architecture Decision: FastAPI vs Direct Database

> **Decision Required:** How should MCP tools access schedule data?
> **Created:** 2025-12-24
> **Status:** RECOMMENDATION: FastAPI

---

***REMOVED******REMOVED*** Current State

The MCP tools currently use **mock/simulated data** (see `tools.py:234-235`):

```python
***REMOVED*** In a real implementation, this would query the database for assignments
***REMOVED*** For now, we simulate with mock data showing the validation logic
```

The MCP server is configured to accept both:
- `DATABASE_URL` - Direct PostgreSQL connection
- `API_BASE_URL` - FastAPI backend (optional)

**Neither is actually connected yet.**

---

***REMOVED******REMOVED*** Architecture Options

***REMOVED******REMOVED******REMOVED*** Option A: Direct Database Connection

```
Claude Code IDE
      ↓
MCP Server (Python)
      ↓
PostgreSQL (via SQLAlchemy)
      ↓
Raw schedule data
```

***REMOVED******REMOVED******REMOVED*** Option B: FastAPI Integration (RECOMMENDED)

```
Claude Code IDE
      ↓
MCP Server (Python)
      ↓
FastAPI Backend (localhost:8000)
      ↓
Services → Repositories → Database
      ↓
Validated, authorized data
```

---

***REMOVED******REMOVED*** Comparison Matrix

| Factor | Direct DB | FastAPI | Winner |
|--------|-----------|---------|--------|
| **Latency** | ~5ms | ~50ms | Direct DB |
| **Business Logic** | Must duplicate | Already built | FastAPI |
| **ACGME Validation** | Must reimplement | Built-in | FastAPI |
| **Audit Trails** | Must add | Built-in | FastAPI |
| **Authorization** | Must add | Built-in | FastAPI |
| **PII Handling** | Raw access | Sanitized | FastAPI |
| **Schema Coupling** | Tight | API contract | FastAPI |
| **Offline Work** | Possible | Requires server | Direct DB |
| **Maintenance** | 2 codebases | 1 codebase | FastAPI |
| **Type Safety** | New Pydantic | Existing Pydantic | FastAPI |

**Score: FastAPI 8, Direct DB 2**

---

***REMOVED******REMOVED*** Risk Analysis

***REMOVED******REMOVED******REMOVED*** Direct Database Risks

1. **Duplicated Business Logic**
   ```
   Current: 2,836 lines in ConstraintManager alone
   Risk: Must duplicate or risk inconsistency
   ```

2. **ACGME Compliance Bypass**
   ```
   Current: 640+ lines in ACGMEConstraintValidator
   Risk: MCP tools could return non-compliant data
   ```

3. **PII Leakage**
   ```
   Current: person.name accessible directly
   Risk: No sanitization layer
   ```

4. **Schema Coupling**
   ```
   Current: 47 Alembic migrations
   Risk: DB changes break MCP tools
   ```

***REMOVED******REMOVED******REMOVED*** FastAPI Risks

1. **Server Dependency**
   ```
   Risk: FastAPI must be running
   Mitigation: Docker Compose starts all services
   ```

2. **Latency**
   ```
   Risk: ~45ms extra per call
   Mitigation: Acceptable for AI tool calls (humans won't notice)
   ```

---

***REMOVED******REMOVED*** Implementation Details

***REMOVED******REMOVED******REMOVED*** FastAPI Connection (Recommended)

```python
***REMOVED*** mcp-server/src/scheduler_mcp/api_client.py

import httpx
from typing import Any

class SchedulerAPIClient:
    """Client for FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def validate_schedule(
        self,
        start_date: str,
        end_date: str,
        checks: list[str]
    ) -> dict[str, Any]:
        """Call existing validation endpoint."""
        response = await self.client.post(
            "/api/v1/schedules/validate",
            json={
                "start_date": start_date,
                "end_date": end_date,
                "checks": checks
            }
        )
        return response.json()

    async def get_conflicts(self, schedule_id: str) -> dict[str, Any]:
        """Call existing conflict detection."""
        response = await self.client.get(
            f"/api/v1/schedules/{schedule_id}/conflicts"
        )
        return response.json()
```

***REMOVED******REMOVED******REMOVED*** Tool Integration

```python
***REMOVED*** mcp-server/src/scheduler_mcp/tools.py

from .api_client import SchedulerAPIClient

***REMOVED*** Initialize client
api_client = SchedulerAPIClient(
    base_url=os.environ.get("API_BASE_URL", "http://localhost:8000")
)

async def validate_schedule(
    request: ScheduleValidationRequest
) -> ScheduleValidationResult:
    """Validate using FastAPI backend."""

    ***REMOVED*** Call real API instead of mock data
    result = await api_client.validate_schedule(
        start_date=str(request.start_date),
        end_date=str(request.end_date),
        checks=[
            "work_hours" if request.check_work_hours else None,
            "supervision" if request.check_supervision else None,
            ***REMOVED*** ...
        ]
    )

    ***REMOVED*** Transform API response to MCP schema
    ***REMOVED*** (API already sanitizes PII - returns person_id not person_name)
    return ScheduleValidationResult(
        is_valid=result["is_valid"],
        issues=[
            ValidationIssue(
                severity=issue["severity"],
                person_id=issue["person_id"],  ***REMOVED*** No person_name!
                message=issue["message"],
                ***REMOVED*** ...
            )
            for issue in result["issues"]
        ]
    )
```

---

***REMOVED******REMOVED*** Docker Compose Integration

```yaml
***REMOVED*** docker-compose.yml (relevant section)
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-server:
    build: ./mcp-server
    environment:
      - API_BASE_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
```

---

***REMOVED******REMOVED*** Hybrid Option (Future Consideration)

For offline/disconnected work, could implement:

```python
class DataSource:
    """Abstraction for data access."""

    async def get_schedule(self, schedule_id: str) -> Schedule:
        raise NotImplementedError

class APIDataSource(DataSource):
    """Use FastAPI backend (default)."""
    async def get_schedule(self, schedule_id: str) -> Schedule:
        return await api_client.get_schedule(schedule_id)

class DatabaseDataSource(DataSource):
    """Direct DB access (offline mode)."""
    async def get_schedule(self, schedule_id: str) -> Schedule:
        async with get_db_session() as db:
            return await db.get(Schedule, schedule_id)

***REMOVED*** Choose based on environment
data_source = (
    APIDataSource()
    if os.environ.get("API_BASE_URL")
    else DatabaseDataSource()
)
```

**Recommendation:** Start with FastAPI only. Add hybrid later if needed.

---

***REMOVED******REMOVED*** Decision

***REMOVED******REMOVED******REMOVED*** Recommendation: FastAPI Integration

**Rationale:**

1. **Business logic reuse** - 10,000+ lines of constraint/validation code already exists
2. **ACGME compliance** - Critical for medical scheduling, already implemented
3. **PII protection** - API layer can enforce sanitization
4. **Maintenance** - Single source of truth for data access
5. **Type safety** - Existing Pydantic schemas in backend

**Tradeoffs accepted:**

- ~45ms latency per call (acceptable for AI tools)
- Requires FastAPI to be running (Docker Compose handles this)

---

***REMOVED******REMOVED*** Next Steps

1. Create `api_client.py` with httpx client
2. Map existing FastAPI endpoints to MCP tool needs
3. Update MCP tools to call API instead of mock data
4. Add connection health checks
5. Test with real schedule data

---

*Decision Date: 2025-12-24*
*Approved By: TBD*
