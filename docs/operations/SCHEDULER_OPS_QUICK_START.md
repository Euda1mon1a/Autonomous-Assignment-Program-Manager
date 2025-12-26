# Scheduler Operations API - Quick Start Guide

## What Was Created

Three new API endpoints for n8n/Slack integration:

1. **GET /api/scheduler/sitrep** - System status and health report
2. **POST /api/scheduler/fix-it** - Automated task recovery
3. **POST /api/scheduler/approve** - Task approval workflow

## Files Created

```
backend/
├── app/
│   ├── api/routes/
│   │   └── scheduler_ops.py          ← NEW: API endpoint handlers
│   └── schemas/
│       └── scheduler_ops.py           ← NEW: Request/response schemas
├── tests/
│   └── test_scheduler_ops.py          ← NEW: Test suite
└── SCHEDULER_OPS_INTEGRATION.md       ← NEW: Detailed documentation
```

## Quick Setup (3 Steps)

### Step 1: Register the Router

Edit `/backend/app/api/routes/__init__.py`:

```python
# Add import (around line 24)
from app.api.routes import (
    # ... existing imports ...
    resilience,
    scheduler_ops,  # ← ADD THIS
    settings,
    # ...
)

# Add router registration (around line 47)
api_router.include_router(resilience.router, prefix="/resilience", tags=["resilience"])
api_router.include_router(scheduler_ops.router, prefix="/scheduler", tags=["scheduler-ops"])  # ← ADD THIS
```

### Step 2: Test the Endpoints

```bash
# Start server
cd backend
uvicorn app.main:app --reload

# In another terminal, test sitrep
curl http://localhost:8000/api/scheduler/sitrep \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 3: Update n8n Workflows (Optional)

The n8n workflows already point to these endpoints. You can optionally update:

- `n8n/workflows/slack_sitrep.json` - Change from `/api/resilience/report` to `/api/scheduler/sitrep`

## API Cheat Sheet

### Sitrep - System Status

```bash
curl -X GET http://localhost:8000/api/scheduler/sitrep \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Returns: task metrics, health status, recent tasks, coverage metrics

### Fix-It - Auto Recovery

```bash
curl -X POST http://localhost:8000/api/scheduler/fix-it \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "balanced",
    "max_retries": 3,
    "auto_approve": false,
    "initiated_by": "your_username",
    "dry_run": true
  }'
```

Modes: `greedy`, `conservative`, `balanced`

### Approve - Task Approval

```bash
# Step 1: Generate token
curl -X POST http://localhost:8000/api/scheduler/approve/token/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": ["task-1", "task-2"],
    "task_type": "schedule_change"
  }'

# Step 2: Use token to approve
curl -X POST http://localhost:8000/api/scheduler/approve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_FROM_STEP_1",
    "action": "approve",
    "approved_by": "your_username"
  }'
```

Actions: `approve`, `deny`

## Common Issues & Solutions

### Issue: 401 Unauthorized

**Solution:** Get a valid JWT token:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_password"}'

# Use the access_token in Authorization header
```

### Issue: 500 Internal Server Error

**Solution:** Check logs and ensure:
- Database is running and seeded
- Resilience service is configured
- All dependencies are installed

```bash
# Check logs
tail -f backend/logs/app.log

# Verify database connection
docker-compose ps db
```

### Issue: n8n workflow not calling endpoint

**Solution:** Check n8n configuration:
1. Verify `API_BASE_URL` environment variable in n8n
2. Check authentication headers in n8n workflow
3. Test endpoint manually with curl first

## Testing

Run tests:

```bash
cd backend
pytest tests/test_scheduler_ops.py -v
```

## File Reference

| File | Purpose |
|------|---------|
| `backend/app/api/routes/scheduler_ops.py` | API endpoint handlers |
| `backend/app/schemas/scheduler_ops.py` | Pydantic request/response models |
| `backend/tests/test_scheduler_ops.py` | Test suite |
| `SCHEDULER_OPS_INTEGRATION.md` | Full documentation |
| `SCHEDULER_OPS_QUICK_START.md` | This file |

## Next Steps

1. ✅ Files created
2. ⏳ **Update `__init__.py`** (Step 1 above)
3. ⏳ Test endpoints manually
4. ⏳ Run test suite
5. ⏳ Update n8n workflows if needed
6. ⏳ Deploy to production

## Production Checklist

Before deploying to production:

- [ ] Add rate limiting to fix-it endpoint
- [ ] Move approval tokens to Redis/database
- [ ] Integrate with actual Celery task tracking
- [ ] Add comprehensive audit logging
- [ ] Configure monitoring and alerts
- [ ] Test all n8n workflows end-to-end
- [ ] Document operational procedures

## Need Help?

- 📖 Full docs: `SCHEDULER_OPS_INTEGRATION.md`
- 🧪 Tests: `backend/tests/test_scheduler_ops.py`
- 📝 Schemas: `backend/app/schemas/scheduler_ops.py`
- 🔌 Routes: `backend/app/api/routes/scheduler_ops.py`
- 🤖 n8n workflows: `n8n/workflows/slack_*.json`

---

**Quick Command Reference:**

```bash
# Start backend
cd backend && uvicorn app.main:app --reload

# Run tests
pytest tests/test_scheduler_ops.py -v

# Check API docs
open http://localhost:8000/docs

# View logs
tail -f backend/logs/app.log
```
