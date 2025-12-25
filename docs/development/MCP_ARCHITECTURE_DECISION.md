# MCP Architecture Decision: FastAPI vs Direct Database

> **Decision Required:** How should MCP tools access schedule data?
> **Created:** 2025-12-24
> **Updated:** 2025-12-25
> **Status:** IMPLEMENTED: FastAPI + Docker Container

---

## Current State

The MCP tools currently use **mock/simulated data** (see `tools.py:234-235`):

```python
# In a real implementation, this would query the database for assignments
# For now, we simulate with mock data showing the validation logic
```

The MCP server is configured to accept both:
- `DATABASE_URL` - Direct PostgreSQL connection
- `API_BASE_URL` - FastAPI backend (optional)

**Neither is actually connected yet.**

---

## Architecture Options

### Option A: Direct Database Connection

```
Claude Code IDE
      ↓
MCP Server (Python)
      ↓
PostgreSQL (via SQLAlchemy)
      ↓
Raw schedule data
```

### Option B: FastAPI Integration (RECOMMENDED)

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

## Comparison Matrix

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

## Risk Analysis

### Direct Database Risks

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

### FastAPI Risks

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

## Implementation Details

### FastAPI Connection (Recommended)

```python
# mcp-server/src/scheduler_mcp/api_client.py

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

### Tool Integration

```python
# mcp-server/src/scheduler_mcp/tools.py

from .api_client import SchedulerAPIClient

# Initialize client
api_client = SchedulerAPIClient(
    base_url=os.environ.get("API_BASE_URL", "http://localhost:8000")
)

async def validate_schedule(
    request: ScheduleValidationRequest
) -> ScheduleValidationResult:
    """Validate using FastAPI backend."""

    # Call real API instead of mock data
    result = await api_client.validate_schedule(
        start_date=str(request.start_date),
        end_date=str(request.end_date),
        checks=[
            "work_hours" if request.check_work_hours else None,
            "supervision" if request.check_supervision else None,
            # ...
        ]
    )

    # Transform API response to MCP schema
    # (API already sanitizes PII - returns person_id not person_name)
    return ScheduleValidationResult(
        is_valid=result["is_valid"],
        issues=[
            ValidationIssue(
                severity=issue["severity"],
                person_id=issue["person_id"],  # No person_name!
                message=issue["message"],
                # ...
            )
            for issue in result["issues"]
        ]
    )
```

---

## Docker Compose Integration

```yaml
# docker-compose.yml (relevant section)
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

## Hybrid Option (Future Consideration)

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

# Choose based on environment
data_source = (
    APIDataSource()
    if os.environ.get("API_BASE_URL")
    else DatabaseDataSource()
)
```

**Recommendation:** Start with FastAPI only. Add hybrid later if needed.

---

## Decision

### Recommendation: FastAPI Integration

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

## Next Steps

1. Create `api_client.py` with httpx client
2. Map existing FastAPI endpoints to MCP tool needs
3. Update MCP tools to call API instead of mock data
4. Add connection health checks
5. Test with real schedule data

---

---

## Implementation: Docker Container (2025-12-25)

### Container Architecture

Following the Docker MCP Toolkit patterns, the MCP server runs as an isolated container:

```
AI Client (Claude Code/VS Code/Cursor)
         ↓ stdio/SSE/HTTP
   MCP Server Container (residency-scheduler-mcp)
         ↓ HTTP (internal network)
   FastAPI Backend Container (residency-scheduler-backend)
         ↓ SQL
   PostgreSQL Database Container (residency-scheduler-db)
```

### Docker Compose Service

```yaml
# docker-compose.yml
mcp-server:
  build:
    context: ./mcp-server
    dockerfile: Dockerfile
  container_name: residency-scheduler-mcp
  depends_on:
    backend:
      condition: service_healthy
  environment:
    API_BASE_URL: http://backend:8000
    CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
  security_opt:
    - no-new-privileges:true
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 2G
```

### Security Model (Docker MCP Toolkit Pattern)

Following Docker's MCP Toolkit security patterns:

| Constraint | Implementation | Rationale |
|------------|----------------|-----------|
| **Resource Limits** | 1 CPU, 2GB RAM | Prevent runaway processes |
| **Privilege Dropping** | `no-new-privileges:true` | No privilege escalation |
| **Network Isolation** | `app-network` bridge | Container-only access |
| **No Host Access** | No volume mounts (prod) | Filesystem isolation |
| **Secret Injection** | Environment variables | No secrets in image |

### Transport Modes

| Mode | Use Case | Configuration |
|------|----------|---------------|
| **stdio** | Claude Code IDE | Default (no ports exposed) |
| **HTTP** | Testing, multi-client | `ports: ["8080:8080"]` |
| **SSE** | Streaming responses | Not yet implemented |

### Development vs Production

**Production (docker-compose.yml):**
- No ports exposed (stdio transport)
- 1 CPU, 2GB RAM limits
- INFO log level
- No volume mounts

**Development (docker-compose.dev.yml):**
- Port 8080 exposed (HTTP transport)
- 2 CPU, 4GB RAM limits
- DEBUG log level
- Source code mounted for hot reload

### Claude Code Integration

Claude Code connects via the unified Gateway pattern:

```json
// .claude/settings.json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "docker",
      "args": ["exec", "-i", "residency-scheduler-mcp",
               "python", "-m", "scheduler_mcp.server"],
      "transport": "stdio"
    }
  }
}
```

Or for development with HTTP:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://localhost:8080",
      "transport": "http"
    }
  }
}
```

### Startup Sequence

1. PostgreSQL container starts, becomes healthy
2. Redis container starts, becomes healthy
3. FastAPI backend starts, runs migrations, becomes healthy
4. MCP server starts, connects to backend API
5. MCP server ready for tool invocations

### Verification Commands

```bash
# Check MCP server health
docker compose ps mcp-server

# View MCP server logs
docker compose logs -f mcp-server

# Test MCP server import
docker compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp.tools)}')"

# Test API connectivity from MCP container
docker compose exec mcp-server curl -s http://backend:8000/health
```

---

*Decision Date: 2025-12-24*
*Implementation Date: 2025-12-25*
*Approved By: Implemented*
