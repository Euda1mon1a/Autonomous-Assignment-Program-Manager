# MCP Implementation Plan: Local IDE Integration

> **Created:** 2025-12-24
> **Goal:** Enable Claude Code IDE to use MCP tools with real schedule context
> **Approach:** Parallel task execution across 4 work streams

---

## Vision

```
BEFORE (Current):
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code IDE                                                │
│       ↓                                                         │
│  Built-in tools only (Bash, Read, Edit, etc.)                  │
│       ↓                                                         │
│  No schedule context, no ACGME validation                      │
│       ↓                                                         │
│  Generic advice based on code reading                          │
└─────────────────────────────────────────────────────────────────┘

AFTER (Target):
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code IDE                                                │
│       ↓                                                         │
│  MCP Tools (29 specialized scheduling tools)                   │
│       ↓                                                         │
│  FastAPI Backend (real data, ACGME validation)                 │
│       ↓                                                         │
│  Context-aware responses:                                       │
│   "The 4th Wednesday constraint is violated because..."        │
│   "3 ACGME violations detected in Block 5..."                  │
│   "Recommended swap: RES-003 ↔ RES-007"                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Parallel Execution Strategy

### 4 Work Streams

```
┌─────────────────────────────────────────────────────────────────┐
│                    PARALLEL EXECUTION PLAN                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Stream 1              Stream 2              Stream 3           │
│  ─────────────         ─────────────         ─────────────      │
│  PII Sanitization      API Client            Context Layer      │
│                                                                 │
│  • Remove person_name  • Create httpx        • Domain glossary  │
│  • Update schemas      • Map endpoints         integration      │
│  • Update tests        • Health checks       • Abbreviation     │
│  • Update docs         • Error handling        expansion        │
│                                              • Constraint       │
│                                                explanations     │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│                    Stream 4                                     │
│                    ─────────────                                │
│                    IDE Connection                               │
│                                                                 │
│                    • .claude/settings.json                      │
│                    • Startup script                             │
│                    • Docker compose update                      │
│                    • Connection verification                    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│                    MERGE POINT                                  │
│                    ───────────                                  │
│                    • Integration test                           │
│                    • Full validation                            │
│                    • Single commit                              │
│                    • Push → PR                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stream 1: PII Sanitization

### Files to Modify

| File | Changes | LOC Est. |
|------|---------|----------|
| `tools.py` | Remove `person_name` from schemas and mock data | ~50 |
| `resources.py` | Remove `person_name` from schemas and DB access | ~30 |
| `tests/test_*.py` | Update tests to not expect `person_name` | ~20 |
| `docs/MCP_RESOURCES_REFERENCE.md` | Update documentation | ~10 |

### Specific Changes

```python
# tools.py:35 - BEFORE
class ValidationIssue(BaseModel):
    person_id: str | None = None
    person_name: str | None = None  # REMOVE

# tools.py:35 - AFTER
class ValidationIssue(BaseModel):
    person_id: str | None = None
    role: str | None = None  # Add role for context without PII
```

```python
# tools.py:252 - BEFORE
ValidationIssue(
    person_id="resident-001",
    person_name="Dr. Williams",  # REMOVE
    ...
)

# tools.py:252 - AFTER
ValidationIssue(
    person_id="RES-001",
    role="PGY-2",  # Add role for context
    ...
)
```

### Verification

```bash
# Must return 0 after changes
grep -r "person_name" mcp-server/src | wc -l
grep -r "candidate_name" mcp-server/src | wc -l
```

---

## Stream 2: API Client

### New File: `mcp-server/src/scheduler_mcp/api_client.py`

```python
"""
API client for connecting MCP tools to FastAPI backend.

This module provides async HTTP client functionality for MCP tools
to call the FastAPI backend instead of accessing the database directly.
"""

import os
from typing import Any

import httpx
from pydantic import BaseModel


class APIConfig(BaseModel):
    """Configuration for API client."""
    base_url: str = "http://localhost:8000"
    timeout: float = 30.0
    api_prefix: str = "/api/v1"


class SchedulerAPIClient:
    """Async client for FastAPI backend."""

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig(
            base_url=os.environ.get("API_BASE_URL", "http://localhost:8000")
        )
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if FastAPI backend is available."""
        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def validate_schedule(
        self,
        start_date: str,
        end_date: str,
        checks: list[str] | None = None
    ) -> dict[str, Any]:
        """Validate schedule via API."""
        response = await self._client.post(
            f"{self.config.api_prefix}/schedules/validate",
            json={
                "start_date": start_date,
                "end_date": end_date,
                "checks": checks or ["all"]
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_conflicts(
        self,
        start_date: str,
        end_date: str
    ) -> dict[str, Any]:
        """Get schedule conflicts via API."""
        response = await self._client.get(
            f"{self.config.api_prefix}/conflicts",
            params={"start_date": start_date, "end_date": end_date}
        )
        response.raise_for_status()
        return response.json()

    async def get_swap_candidates(
        self,
        person_id: str,
        block_id: str
    ) -> dict[str, Any]:
        """Get swap candidates via API."""
        response = await self._client.get(
            f"{self.config.api_prefix}/swaps/candidates",
            params={"person_id": person_id, "block_id": block_id}
        )
        response.raise_for_status()
        return response.json()

    async def run_contingency_analysis(
        self,
        scenario: str,
        affected_ids: list[str],
        start_date: str,
        end_date: str
    ) -> dict[str, Any]:
        """Run contingency analysis via API."""
        response = await self._client.post(
            f"{self.config.api_prefix}/resilience/contingency",
            json={
                "scenario": scenario,
                "affected_person_ids": affected_ids,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        response.raise_for_status()
        return response.json()


# Singleton instance for tool use
_api_client: SchedulerAPIClient | None = None


async def get_api_client() -> SchedulerAPIClient:
    """Get or create API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = SchedulerAPIClient()
        await _api_client.__aenter__()
    return _api_client
```

### Tool Integration Example

```python
# tools.py - Update validate_schedule to use API

from .api_client import get_api_client

async def validate_schedule(
    request: ScheduleValidationRequest
) -> ScheduleValidationResult:
    """Validate schedule using FastAPI backend."""

    # Get API client
    client = await get_api_client()

    # Check if API is available
    if not await client.health_check():
        raise RuntimeError(
            "FastAPI backend not available. "
            "Start with: docker-compose up -d backend"
        )

    # Call API (returns sanitized data - no PII)
    result = await client.validate_schedule(
        start_date=str(request.start_date),
        end_date=str(request.end_date),
        checks=_build_check_list(request)
    )

    # Transform to MCP schema
    return ScheduleValidationResult(
        is_valid=result["is_valid"],
        overall_compliance_rate=result["compliance_rate"],
        total_issues=len(result["issues"]),
        # ... map remaining fields
    )
```

---

## Stream 3: Context Layer

### New File: `mcp-server/src/scheduler_mcp/domain_context.py`

```python
"""
Domain context provider for MCP tools.

Provides abbreviation expansion, constraint explanations,
and scheduling pattern context.
"""

from typing import Any

# Import from the glossary we created
ABBREVIATIONS = {
    "PGY": "Post-Graduate Year",
    "ACGME": "Accreditation Council for Graduate Medical Education",
    "FMIT": "Family Medicine Inpatient Team",
    "PC": "Post-Call",
    "ASM": "Academic Sports Medicine",
    "TDY": "Temporary Duty",
    "APD": "Associate Program Director",
    "PD": "Program Director",
    "SM": "Sports Medicine",
    "NF": "Night Float",
    "MTF": "Military Treatment Facility",
}

CONSTRAINT_EXPLANATIONS = {
    "InvertedWednesday": {
        "description": "4th Wednesday has inverted schedule",
        "rule": "Residents: Lecture AM, Advising PM. "
               "Faculty: 1 AM, 1 DIFFERENT PM",
        "detection": "Day 22-28 of month that is Wednesday",
        "fix_options": [
            "Assign different faculty to AM vs PM",
            "Swap faculty assignments with adjacent days"
        ]
    },
    "EightyHourRule": {
        "description": "ACGME 80-hour weekly limit",
        "rule": "Max 80 hours/week averaged over rolling 4 weeks",
        "detection": "Sum hours in 4-week window > 320",
        "fix_options": [
            "Remove assignments from high-hour weeks",
            "Redistribute load to lower-hour residents"
        ]
    },
    "OneInSevenRule": {
        "description": "ACGME 1-in-7 rest requirement",
        "rule": "One 24-hour period off every 7 days",
        "detection": "7+ consecutive days with assignments",
        "fix_options": [
            "Insert day off in sequence",
            "Swap with resident who has day off"
        ]
    },
    # ... add more constraints
}

SCHEDULING_PATTERNS = {
    "inverted_wednesday": {
        "name": "Inverted Wednesday (4th Wednesday)",
        "normal_pattern": {
            "AM": "Residents in clinic",
            "PM": "Residents at lecture/sim, 1 faculty covers"
        },
        "inverted_pattern": {
            "AM": "Residents at lecture, 1 faculty covers",
            "PM": "Residents at advising, 1 DIFFERENT faculty covers"
        },
        "why": "Equity - distributes solo coverage across faculty"
    },
    "fmit_week": {
        "name": "FMIT Week",
        "pattern": "Mon-Wed FMIT, Thu overnight call, Fri post-call",
        "constraints": [
            "Wednesday AM still has ASM",
            "Friday is recovery - no clinic",
            "Weekend coverage if on FMIT"
        ]
    }
}


def expand_abbreviations(text: str) -> str:
    """Expand known abbreviations in text."""
    result = text
    for abbrev, full in ABBREVIATIONS.items():
        # Only expand if it's a standalone word
        import re
        pattern = rf'\b{abbrev}\b'
        replacement = f"{abbrev} ({full})"
        result = re.sub(pattern, replacement, result, count=1)
    return result


def explain_constraint(constraint_name: str) -> dict[str, Any]:
    """Get detailed explanation for a constraint."""
    if constraint_name in CONSTRAINT_EXPLANATIONS:
        return CONSTRAINT_EXPLANATIONS[constraint_name]
    return {
        "description": f"Constraint: {constraint_name}",
        "rule": "See constraint implementation for details",
        "fix_options": ["Review constraint code"]
    }


def explain_pattern(pattern_name: str) -> dict[str, Any]:
    """Get explanation for a scheduling pattern."""
    if pattern_name in SCHEDULING_PATTERNS:
        return SCHEDULING_PATTERNS[pattern_name]
    return {
        "name": pattern_name,
        "pattern": "Unknown pattern",
        "why": "Pattern not documented"
    }


def enrich_violation_response(violation: dict) -> dict:
    """Add context to a constraint violation response."""
    constraint = violation.get("constraint", "")

    # Add explanation
    explanation = explain_constraint(constraint)
    violation["explanation"] = explanation["description"]
    violation["fix_options"] = explanation.get("fix_options", [])

    # Expand abbreviations in message
    if "message" in violation:
        violation["message"] = expand_abbreviations(violation["message"])

    return violation
```

---

## Stream 4: IDE Connection (IMPLEMENTED 2025-12-25)

### Docker Container Approach

Instead of running the MCP server directly via Python, we now use a Docker container
following the Docker MCP Toolkit patterns. This provides:

- **Isolation**: Container-level security
- **Consistency**: Same environment across all deployments
- **Security**: Resource limits, privilege dropping

### Docker Compose Service (Implemented)

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

### Claude Code Integration Options

**Option 1: Docker exec (stdio transport)**
```json
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

**Option 2: HTTP transport (development)**
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

### Starting the MCP Server

```bash
# Start all services including MCP server
docker-compose up -d

# Development mode with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View MCP server logs
docker-compose logs -f mcp-server

# Test MCP server
docker-compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp.tools)}')"
```

---

## Merge Point: Integration Test

### Test Script: `scripts/test-mcp-integration.sh`

```bash
#!/bin/bash
# Integration test for MCP + FastAPI + Claude Code

set -e

echo "=== MCP Integration Test ==="

# 1. Start services
echo "1. Starting services..."
docker-compose up -d backend db
sleep 10

# 2. Verify FastAPI
echo "2. Checking FastAPI health..."
curl -f http://localhost:8000/health || exit 1

# 3. Test MCP server starts
echo "3. Testing MCP server startup..."
cd mcp-server/src
timeout 5 python -c "from scheduler_mcp.server import mcp; print('MCP imports OK')" || exit 1

# 4. Test API client
echo "4. Testing API client..."
python -c "
import asyncio
from scheduler_mcp.api_client import SchedulerAPIClient, APIConfig

async def test():
    config = APIConfig(base_url='http://localhost:8000')
    async with SchedulerAPIClient(config) as client:
        health = await client.health_check()
        print(f'Health check: {health}')
        assert health, 'Health check failed'

asyncio.run(test())
" || exit 1

# 5. Test no PII in responses
echo "5. Verifying no PII in MCP code..."
if grep -r "person_name" src/scheduler_mcp/*.py | grep -v "# REMOVED"; then
    echo "ERROR: person_name still found in MCP code"
    exit 1
fi

echo "=== All tests passed ==="
```

---

## Execution Timeline

### Parallel Phase (Can run simultaneously)

| Stream | Agent | Duration | Deliverables |
|--------|-------|----------|--------------|
| 1. PII Sanitization | Task Agent 1 | ~30 min | Sanitized tools.py, resources.py |
| 2. API Client | Task Agent 2 | ~45 min | api_client.py, tool updates |
| 3. Context Layer | Task Agent 3 | ~30 min | domain_context.py |
| 4. IDE Connection | Task Agent 4 | ~20 min | settings.json, scripts |

### Merge Phase (Sequential)

| Step | Duration | Action |
|------|----------|--------|
| Integration | ~15 min | Run test-mcp-integration.sh |
| Verification | ~10 min | Manual test with Claude Code |
| Commit | ~5 min | Single commit with all changes |
| Push | ~2 min | Push to branch, create PR |

### Total Estimated Time

- **Parallel work:** ~45 min (limited by longest stream)
- **Merge work:** ~30 min
- **Total:** ~75 min

---

## Success Criteria

### Functional

- [ ] MCP server starts without errors
- [ ] FastAPI health check passes
- [ ] validate_schedule returns real data (via API)
- [ ] No PII in any MCP response
- [ ] Context layer expands abbreviations correctly

### Security

- [ ] `grep -r "person_name" mcp-server/src` returns 0 matches
- [ ] All tool responses use `person_id` only
- [ ] API client connects to localhost only

### Integration

- [ ] Claude Code IDE can call MCP tools
- [ ] Plan mode works with schedule context
- [ ] Parallel Task execution works

---

## Rollback Plan

If integration fails:

```bash
# Revert to previous state
git checkout HEAD~1 -- mcp-server/
git checkout HEAD~1 -- .claude/settings.json

# Or reset entirely
git reset --hard HEAD~1
```

---

## Post-Implementation

### Documentation Updates

- [ ] Update README.md with MCP setup instructions
- [ ] Update docs/guides/AI_AGENT_USER_GUIDE.md
- [ ] Add MCP troubleshooting section

### Monitoring

- [ ] Add MCP tool call logging
- [ ] Track API latency metrics
- [ ] Monitor for PII leaks in logs

---

*Plan Created: 2025-12-24*
*Ready for Execution: Pending Approval*
