# Scheduler Operations API Integration Guide

## Overview

This document describes the new scheduler operations API endpoints created for n8n workflow integration. These endpoints enable Slack-based monitoring and control of the scheduling system.

## Files Created

### 1. `/backend/app/schemas/scheduler_ops.py`

Pydantic schemas for scheduler operations, including:

- **Request/Response Models:**
  - `SitrepResponse` - Situation report with task metrics, health status, and coverage
  - `FixItRequest/Response` - Fix-it mode for automated task recovery
  - `ApprovalRequest/Response` - Task approval workflow

- **Enums:**
  - `FixItMode` - greedy, conservative, balanced
  - `ApprovalAction` - approve, deny
  - `TaskStatus` - pending, in_progress, completed, failed, cancelled

### 2. `/backend/app/api/routes/scheduler_ops.py`

Three main API endpoints:

#### GET `/api/v1/scheduler/sitrep`
Returns situation report including:
- Task execution metrics (total, active, completed, failed tasks)
- System health status from resilience service
- Recent task activity
- Schedule coverage metrics
- Immediate actions and watch items

**Used by:** `n8n/workflows/slack_sitrep.json`

#### POST `/api/v1/scheduler/fix-it`
Initiates automated task recovery:
- Retries failed tasks based on selected mode (greedy/conservative/balanced)
- Applies corrective actions
- Returns execution results with affected tasks
- Supports dry-run mode for preview

**Used by:** `n8n/workflows/slack_fix_it.json`

#### POST `/api/v1/scheduler/approve`
Approves or denies pending tasks:
- Validates approval tokens
- Processes task approvals/denials
- Supports batch approval or single task approval
- Returns detailed approval results

**Used by:** `n8n/workflows/slack_approve.json`

#### POST `/api/v1/scheduler/approve/token/generate` (Helper)
Generates approval tokens for tasks requiring approval:
- Creates secure tokens with expiration
- Associates tasks with tokens
- Used internally to create approval workflows

## Integration Required

### Update `/backend/app/api/routes/__init__.py`

Add the following import and router registration:

```python
from app.api.routes import (
    # ... existing imports ...
    resilience,
    scheduler_ops,  # ADD THIS LINE
    settings,
    # ... rest of imports ...
)

# In the api_router setup section, add:
api_router.include_router(scheduler_ops.router, prefix="/scheduler", tags=["scheduler-ops"])
```

**Suggested placement:** After the `resilience` router registration (around line 47), add:

```python
api_router.include_router(resilience.router, prefix="/resilience", tags=["resilience"])
api_router.include_router(scheduler_ops.router, prefix="/scheduler", tags=["scheduler-ops"])  # NEW
api_router.include_router(procedures.router, prefix="/procedures", tags=["procedures"])
```

## API Endpoints Summary

All endpoints require authentication via JWT token.

| Method | Endpoint | Purpose | n8n Workflow |
|--------|----------|---------|--------------|
| GET | `/api/v1/scheduler/sitrep` | Get situation report | `slack_sitrep.json` |
| POST | `/api/v1/scheduler/fix-it` | Initiate task recovery | `slack_fix_it.json` |
| POST | `/api/v1/scheduler/approve` | Approve/deny tasks | `slack_approve.json` |
| POST | `/api/v1/scheduler/approve/token/generate` | Generate approval token | Internal use |

## Request/Response Examples

### Sitrep (GET /api/v1/scheduler/sitrep)

**Response:**
```json
{
  "timestamp": "2025-12-18T10:30:00Z",
  "task_metrics": {
    "total_tasks": 100,
    "active_tasks": 5,
    "completed_tasks": 85,
    "failed_tasks": 5,
    "pending_tasks": 5,
    "success_rate": 0.85
  },
  "health_status": "healthy",
  "defense_level": "PREVENTION",
  "recent_tasks": [...],
  "coverage_metrics": {
    "coverage_rate": 0.95,
    "blocks_covered": 950,
    "blocks_total": 1000,
    "critical_gaps": 50,
    "faculty_utilization": 0.75
  },
  "immediate_actions": [],
  "watch_items": [],
  "last_update": "2025-12-18T10:30:00Z",
  "crisis_mode": false
}
```

### Fix-It (POST /api/v1/scheduler/fix-it)

**Request:**
```json
{
  "mode": "balanced",
  "max_retries": 3,
  "auto_approve": false,
  "initiated_by": "slack_user",
  "dry_run": false
}
```

**Response:**
```json
{
  "status": "completed",
  "execution_id": "uuid-here",
  "mode": "balanced",
  "tasks_fixed": 4,
  "tasks_retried": 5,
  "tasks_skipped": 0,
  "tasks_failed": 1,
  "affected_tasks": [...],
  "estimated_completion": null,
  "initiated_by": "slack_user",
  "initiated_at": "2025-12-18T10:30:00Z",
  "completed_at": "2025-12-18T10:31:00Z",
  "message": "Fix-it completed: 4/5 tasks recovered.",
  "warnings": []
}
```

### Approve (POST /api/v1/scheduler/approve)

**Request:**
```json
{
  "token": "approval-token-here",
  "task_id": "task-123",
  "action": "approve",
  "approved_by": "slack_user",
  "approved_by_id": "U123456",
  "notes": "Approved via Slack"
}
```

**Response:**
```json
{
  "status": "approved",
  "action": "approve",
  "task_id": "task-123",
  "approved_tasks": 1,
  "denied_tasks": 0,
  "task_details": [...],
  "approved_by": "slack_user",
  "approved_at": "2025-12-18T10:30:00Z",
  "message": "Successfully approved 1 task(s).",
  "warnings": []
}
```

## Architecture Notes

### Current Implementation

The current implementation provides a working foundation with:

1. **Proper FastAPI patterns:**
   - Async endpoint handlers
   - Pydantic schema validation
   - JWT authentication via `get_current_active_user`
   - Comprehensive logging
   - Error handling with proper HTTP status codes

2. **Integration with existing services:**
   - Uses `ResilienceService` for health data
   - Queries database for coverage metrics
   - Follows existing patterns from `resilience.py` routes

3. **Placeholder logic for task tracking:**
   - Task metrics are currently synthesized from system state
   - Recent tasks use assignments as a proxy
   - Approval tokens stored in memory

### Production Enhancements Needed

For production deployment, enhance these areas:

1. **Task Tracking Integration:**
   - Integrate with Celery for actual task status
   - Query real task execution logs
   - Connect to task queue for fix-it operations

2. **Persistent Storage:**
   - Move approval tokens to Redis or database
   - Store fix-it execution history
   - Add task approval records to database

3. **Rate Limiting:**
   - Add rate limiting for fix-it operations
   - Throttle approval attempts
   - Protect against token brute-force

4. **Notifications:**
   - Send notifications on task completion
   - Alert on fix-it failures
   - Notify on approvals/denials

5. **Audit Trail:**
   - Log all fix-it executions
   - Track approval decisions
   - Record token usage

## Testing

### Manual Testing

1. **Start the backend server:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Authenticate and get token:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "your_user", "password": "your_password"}'
   ```

3. **Test sitrep endpoint:**
   ```bash
   curl http://localhost:8000/api/scheduler/sitrep \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. **Test fix-it endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/scheduler/fix-it \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"mode": "balanced", "max_retries": 3, "auto_approve": false, "initiated_by": "test_user", "dry_run": true}'
   ```

5. **Generate approval token:**
   ```bash
   curl -X POST http://localhost:8000/api/scheduler/approve/token/generate \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"task_ids": ["task-1", "task-2"], "task_type": "schedule_change"}'
   ```

6. **Test approve endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/scheduler/approve \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"token": "TOKEN_FROM_STEP_5", "action": "approve", "approved_by": "test_user"}'
   ```

### Automated Testing

Create test file at `backend/tests/test_scheduler_ops.py`:

```python
import pytest
from fastapi.testclient import TestClient

def test_sitrep_endpoint(client: TestClient, auth_headers: dict):
    """Test situation report endpoint."""
    response = client.get("/api/scheduler/sitrep", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "task_metrics" in data
    assert "health_status" in data
    assert "coverage_metrics" in data

def test_fix_it_dry_run(client: TestClient, auth_headers: dict):
    """Test fix-it dry run mode."""
    response = client.post(
        "/api/scheduler/fix-it",
        headers=auth_headers,
        json={
            "mode": "balanced",
            "max_retries": 3,
            "auto_approve": False,
            "initiated_by": "test_user",
            "dry_run": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "dry_run"
    assert "execution_id" in data

def test_approve_invalid_token(client: TestClient, auth_headers: dict):
    """Test approval with invalid token."""
    response = client.post(
        "/api/scheduler/approve",
        headers=auth_headers,
        json={
            "token": "invalid_token",
            "action": "approve",
            "approved_by": "test_user",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "invalid_token"
```

## n8n Workflow Integration

The n8n workflows in `/n8n/workflows/` are already configured to call these endpoints:

1. **slack_sitrep.json** - Calls GET `/api/resilience/report`
   - **Note:** The workflow currently calls `/api/resilience/report`. You may want to update it to call `/api/scheduler/sitrep` instead, or keep both endpoints available.

2. **slack_fix_it.json** - Calls POST `/api/scheduler/fix-it`
   - ✅ Ready to use with new endpoint

3. **slack_approve.json** - Calls POST `/api/scheduler/approve`
   - ✅ Ready to use with new endpoint

## Security Considerations

1. **Authentication Required:**
   - All endpoints require valid JWT authentication
   - Use `get_current_active_user` dependency

2. **Rate Limiting:**
   - Consider adding rate limiting for production
   - Especially important for fix-it operations

3. **Approval Token Security:**
   - Tokens are cryptographically secure (32 bytes)
   - Tokens expire after 24 hours by default
   - Tokens are single-use (marked as used after approval)
   - Store in Redis or database for production

4. **Audit Logging:**
   - All operations are logged via Python logging
   - Consider adding database audit trail for compliance

## Next Steps

1. **Update `__init__.py`** to register the new router (see Integration Required section above)
2. **Test the endpoints** using the manual testing steps
3. **Update n8n workflows** if needed to use the new `/api/scheduler/sitrep` endpoint
4. **Add automated tests** for the new endpoints
5. **Implement production enhancements** as needed (Celery integration, Redis storage, etc.)
6. **Configure rate limiting** for production deployment
7. **Set up monitoring** and alerting for scheduler operations

## Questions or Issues?

- Check logs at `backend/logs/` for detailed error messages
- Verify authentication tokens are valid
- Ensure database is properly seeded with test data
- Review resilience service configuration

## Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Pydantic Schemas:** See other schemas in `backend/app/schemas/`
- **Existing Routes:** See patterns in `backend/app/api/routes/resilience.py`
- **n8n Workflows:** See `n8n/workflows/` for Slack integration examples
