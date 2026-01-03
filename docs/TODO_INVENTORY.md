# TODO Inventory

Generated: 2026-01-02

## Critical (Blocking)
- None identified

## High Priority (This Week)
- **Activity logging implementation** (`backend/app/api/routes/admin_users.py:77`) - Admin activity logging is currently a no-op placeholder; essential for audit trail compliance
- **Invitation email system** (`backend/app/api/routes/admin_users.py:236, 552`) - User invitations are not actually being sent

## Medium Priority (This Month)
- **Service layer pagination** (`backend/app/controllers/absence_controller.py:45`) - Pagination currently applied at controller level instead of service layer; affects query performance
- **Shapley value service integration** (`mcp-server/src/scheduler_mcp/server.py:1701`) - MCP tool returns placeholder data instead of actual fair workload calculations

## Low Priority (Future Work)
- **Database loading for schedule comparisons** (`mcp-server/src/scheduler_mcp/time_crystal_tools.py:281, 417`) - Time crystal tools use empty schedules when schedule IDs provided without direct assignments
- **Activity log table creation** (`backend/app/api/routes/admin_users.py:596`) - Endpoint returns empty response pending table creation

## Deferred (Intentionally Pending)
- None identified

---

## Detailed Inventory

### File: mcp-server/src/scheduler_mcp/time_crystal_tools.py

| Line | Type | Description | Priority |
|------|------|-------------|----------|
| 281 | stub | Load schedule from database using schedule_ids for rigidity analysis | Low |
| 417 | stub | Load schedule from database for periodicity analysis | Low |

**Context:** Both TODOs relate to the time crystal scheduling feature. Currently, if you provide `schedule_id` parameters instead of direct `assignments` data, the functions fall back to using empty schedules. This is acceptable because the primary use case passes assignments directly via MCP tool calls.

### File: mcp-server/src/scheduler_mcp/server.py

| Line | Type | Description | Priority |
|------|------|-------------|----------|
| 1701 | integration | Connect to actual ShapleyValueService when DB is available | Medium |

**Context:** The Shapley value MCP tool (`calculate_shapley_values`) currently returns placeholder data with evenly distributed workload values. The backend `ShapleyValueService` exists but the MCP server needs proper database connectivity to call it. Affects fair workload distribution visibility in AI-assisted scheduling.

### File: backend/app/controllers/absence_controller.py

| Line | Type | Description | Priority |
|------|------|-------------|----------|
| 45 | refactor | Update service layer to support pagination (page, page_size) | Medium |

**Context:** The `list_absences` method fetches all records and applies pagination at the controller level. For large datasets, this is inefficient. The TODO suggests pushing pagination to the service/repository layer for proper SQL LIMIT/OFFSET queries.

### File: backend/app/api/routes/admin_users.py

| Line | Type | Description | Priority |
|------|------|-------------|----------|
| 77 | feature | Implement activity logging to activity_log table when it exists | High |
| 236 | feature | Send invitation email if user_data.send_invite is True | High |
| 552 | feature | Actually send the invitation email (resend flow) | High |
| 596 | feature | Implement activity log query when activity_log table exists | Low |

**Context:** The admin user management routes have placeholder implementations for:
1. **Activity logging** (line 77): The `_log_activity` function is a no-op. Admin actions (create, update, delete, lock/unlock) should be logged for compliance auditing.
2. **Invitation emails** (lines 236, 552): User creation and resend-invite endpoints update timestamps but don't actually send emails. This requires email service integration (SMTP or transactional email provider).
3. **Activity log retrieval** (line 596): The `/activity-log` endpoint returns empty results pending the activity_log table creation via Alembic migration.

---

## Summary Statistics

| Priority | Count |
|----------|-------|
| Critical | 0 |
| High | 3 |
| Medium | 2 |
| Low | 3 |
| **Total** | **8** |

## Recommended Next Steps

1. **Create activity_log table** - Design schema and Alembic migration for admin activity logging
2. **Integrate email service** - Configure SMTP or transactional email provider for invitations
3. **Refactor absence pagination** - Push pagination to service layer for efficiency
4. **Connect MCP Shapley service** - Wire up database connectivity for fair workload calculations
