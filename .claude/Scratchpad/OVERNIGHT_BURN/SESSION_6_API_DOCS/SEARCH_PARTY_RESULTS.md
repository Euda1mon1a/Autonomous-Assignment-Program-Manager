# SEARCH_PARTY Operation Results: Real-Time API Discovery

**Operation**: G2_RECON WebSocket/Real-time API Documentation
**Status**: COMPLETE
**Date**: 2025-12-30
**Output**: `api-docs-realtime.md`

---

## Executive Summary

### Discovery Findings

The Residency Scheduler implements **three-layer real-time architecture**:

1. **WebSocket Layer** (`/ws` endpoint)
   - JWT-authenticated connections
   - 8 event types (connection_ack, schedule_updated, assignment_changed, swap_requested, swap_approved, conflict_detected, resilience_alert, pong)
   - Subscription-based filtering (schedule-level, person-level, system-wide)
   - Auto-reconnection support (client-side)

2. **Event Bus Layer** (In-memory pub/sub)
   - 28 domain event types (ScheduleCreated, AssignmentUpdated, SwapExecuted, etc.)
   - Handler pattern with decorator support
   - Dead letter queue for failed events
   - Retry logic with exponential backoff

3. **GraphQL Subscriptions** (Strawberry + Redis)
   - 8 subscription types (ScheduleUpdate, AssignmentUpdate, SwapNotification, etc.)
   - Redis pub/sub channels for clustering
   - Heartbeat/presence tracking

---

## SEARCH_PARTY Probe Results

### 1. PERCEPTION: Real-Time Features in Codebase

**Found Components**:
- WebSocket manager: `backend/app/websocket/manager.py` (371 lines)
- WebSocket events: `backend/app/websocket/events.py` (226 lines)
- WebSocket route: `backend/app/api/routes/ws.py` (219 lines)
- Event bus: `backend/app/events/event_bus.py` (438 lines)
- Event types: `backend/app/events/event_types.py` (518 lines)
- GraphQL subscriptions: `backend/app/graphql/subscriptions.py` (partial read)
- Event handlers: `backend/app/events/handlers/schedule_events.py` (partial read)
- E2E tests: `backend/tests/e2e/test_websocket_e2e.py` (935 lines)

**Statistics**:
- 8 WebSocket event types defined
- 28 domain event types defined
- 8 GraphQL subscription types
- 6+ broadcast convenience functions
- Comprehensive E2E test suite with 20+ test cases

### 2. INVESTIGATION: WebSocket Protocol Documentation

**Findings**:
- Protocol: RFC 6455 WebSocket with JWT authentication
- Endpoint: `wss://host/ws?token=<JWT>`
- Message format: JSON
- Broadcast scope: 4 modes (user, schedule, person, all)
- Keepalive: ping/pong mechanism (client sends action="ping")

**Authentication Flow**:
1. Client connects with JWT token in query parameter
2. Server validates token via `verify_token()`
3. User loaded and checked for active status
4. Connection accepted → ConnectionAckEvent sent immediately
5. Invalid → WS 1008 (Policy Violation) close

### 3. ARCANA: Real-Time Patterns

**Patterns Discovered**:

**Pattern 1: Subscription-Based Broadcasting**
- Users explicitly subscribe to schedules and persons
- Events only sent to subscribers (not all connected users)
- Exceptions: Resilience alerts broadcast to all users (system-wide)

**Pattern 2: Connection Manager as Singleton**
- Global instance via `get_connection_manager()`
- Thread-safe with asyncio.Lock()
- Tracks connections per user (supports multi-tab)
- Maintains watcher sets for efficient broadcast

**Pattern 3: Broadcast Convenience Functions**
- 6 async functions for common broadcast scenarios
- Each wraps ConnectionManager.broadcast_to_*()
- Examples: broadcast_schedule_updated(), broadcast_swap_requested()

**Pattern 4: Event Bus Loose Coupling**
- Internal events published on event bus
- Handlers subscribe to event types
- Event bus manages retry/DLQ
- Decouples schedule generation from WebSocket notifications

### 4. HISTORY: Real-Time Evolution

**Version Timeline**:
- WebSocket infrastructure: Foundation layer
- Event types: Base domain events
- GraphQL subscriptions: Recent addition (Strawberry)
- Redis pub/sub: For multi-instance clustering

**Known Issues**:
- E2E tests marked with note: "fail due to pre-existing infrastructure issue where rotation_preferences model uses JSONB type (PostgreSQL-specific) which is not supported in SQLite"
- Async WebSocket client testing challenging with TestClient

### 5. INSIGHT: Client Integration Guide

**Complete Integration Example Provided**:
- Connection lifecycle (connect → subscribe → handle → reconnect)
- All 8 event handler patterns
- Exponential backoff reconnection (5 attempts, 3s→48s delay)
- Message queueing for offline resilience
- Ping/pong keepalive (30-second intervals)
- React component example with custom events

### 6. RELIGION: Event Documentation Completeness

**All Events Fully Documented**:
- ✅ connection_ack - documented
- ✅ schedule_updated - documented with 7 fields
- ✅ assignment_changed - documented with 7 fields
- ✅ swap_requested - documented with 6 fields
- ✅ swap_approved - documented with 6 fields
- ✅ conflict_detected - documented with 7 fields
- ✅ resilience_alert - documented with 7 fields
- ✅ pong - documented

**Missing in Codebase**: None identified. All events that can be broadcast are documented.

### 7. NATURE: Event Complexity Analysis

**Event Categorization**:
- **Simple Events** (2): connection_ack, pong
- **Medium Events** (4): schedule_updated, swap_requested, swap_approved, conflict_detected
- **Complex Events** (2): assignment_changed (7 fields, various types), resilience_alert (7 fields, recommendations array)

**Optimization Opportunities**:
- All events are reasonable complexity (no redundancy detected)
- Event union types properly used (UUID | None for optional fields)
- Timestamp always included for proper ordering

### 8. MEDICINE: Message Format Examples

**Provided in Documentation**:
- All 8 event types with complete JSON examples
- Field descriptions for each
- Broadcast scope explained
- Source code location for each event

**Format Validation**:
- Pydantic models enforce schema
- JSON serialization handles UUID and datetime
- No detected format inconsistencies

### 9. SURVIVAL: Reconnection Documentation

**Reconnection Handling Documented**:
1. **Detection**: Client monitors ws.readyState
2. **Backoff Strategy**: Exponential (2^n multiplier)
3. **Max Attempts**: 5 retries = ~93 seconds total
4. **Subscription Restoration**: Explicitly re-subscribe on reconnect
5. **Message Queue**: Buffer messages during disconnection

**Resilience Features Documented**:
- Multiple tabs supported (one user → multiple connections)
- Thread-safe cleanup on disconnect
- Subscription watcher cleanup
- Graceful degradation (connection stays open for most errors)

### 10. STEALTH: Undocumented Events

**Audit Result**:
- ✅ No undocumented events found
- ✅ All broadcast functions documented
- ✅ All EventType enums exported
- ✅ Test coverage reflects implemented events

**Potential Gaps**:
- GraphQL subscription events exist but not all mapped to WebSocket events (schema mismatch opportunity)

---

## Deliverable Quality Assessment

### Coverage

| Category | Status | Notes |
|----------|--------|-------|
| API endpoint documentation | Complete | `/ws` endpoint fully documented |
| Event type inventory | Complete | All 8 types with examples |
| Client integration guide | Complete | TypeScript example with all patterns |
| Reconnection handling | Complete | Backoff strategy, message queue, subscription restore |
| Broadcasting architecture | Complete | All 4 broadcast modes explained |
| Error handling | Complete | All error codes mapped to causes |
| Monitoring & stats | Complete | Two stats endpoints documented |
| GraphQL subscriptions | Partial | Types listed, but query examples minimal |

### Depth

- **Breadth**: 7 major sections + appendix with full TypeScript schemas
- **Code References**: 8 source files cited with line numbers
- **Examples**: 5 complete code examples (TypeScript, Python, GraphQL)
- **Field Documentation**: Every field in every event type explained

### Usability

- **For Frontend Devs**: TypeScript example with React hooks, custom events, reconnection
- **For Backend Devs**: Event bus patterns, handler registration, broadcast calls
- **For Ops**: Health endpoints, stats endpoints, metrics to monitor
- **For Testing**: E2E test patterns, load testing guidance

---

## Key Discoveries

### 1. Three-Tier Architecture (Not Just WebSocket)

Most documentation focuses on WebSocket, but the full picture includes:
- **Tier 1**: WebSocket (client-facing real-time)
- **Tier 2**: Event Bus (internal domain events, loose coupling)
- **Tier 3**: GraphQL Subscriptions (schema-aware, clustering support)

### 2. Subscription Filtering is Granular

Broadcasting is not one-to-all; it's filtered by:
- **Schedule-level**: broadcast_to_schedule() - for collaborative viewing
- **Person-level**: broadcast_to_person() - for individual notifications
- **User-level**: send_to_user() - for direct messages
- **System-wide**: broadcast_to_all() - for alerts (only resilience alerts)

### 3. Multi-Tab Support Built-In

Connection manager tracks multiple connections per user:
```python
_connections: dict[UUID, list[Connection]]
```

This allows same user in multiple browser tabs to each have own WebSocket.

### 4. Event Bus Retry/DLQ Pattern

Failed event handlers don't just disappear - they're:
1. Retried up to 3 times with exponential backoff
2. Added to Dead Letter Queue if all retries fail
3. Can be manually replayed via `replay_dead_letter_event()`

### 5. Broadcast Functions Are Convenience Wrappers

Behind every `broadcast_*()` function is the same pattern:
1. Create event object (Pydantic model)
2. Call manager method (broadcast_to_schedule, etc.)
3. Manager iterates watchers and sends individually

---

## Files Referenced in Documentation

```
backend/app/websocket/
  ├── manager.py          (371 lines) - ConnectionManager, broadcast functions
  ├── events.py           (226 lines) - WebSocket event types
  └── __init__.py

backend/app/api/routes/
  └── ws.py               (219 lines) - @router.websocket("/ws")

backend/app/events/
  ├── event_bus.py        (438 lines) - EventBus, pub/sub, retry logic
  ├── event_types.py      (518 lines) - 28 domain event types
  └── handlers/
      └── schedule_events.py - Event handler examples

backend/app/graphql/
  └── subscriptions.py    - GraphQL subscription types

backend/tests/e2e/
  └── test_websocket_e2e.py (935 lines) - Comprehensive E2E tests
```

---

## Recommendations for Users

### For First-Time Integration (Frontend)

1. Read sections: Overview → WebSocket API → Client Integration Guide
2. Use provided TypeScript example as starting point
3. Implement all 8 event handlers
4. Test reconnection with network tab throttling
5. Monitor `/ws/stats` endpoint for debugging

### For Backend Enhancement

1. Review Event Bus System section
2. Understand EventType enum and handler patterns
3. When adding new broadcast, create convenience function
4. Add corresponding E2E test
5. Update this documentation

### For Operations

1. Monitor metrics listed in "Monitoring & Statistics" section
2. Track connection count via `/ws/stats`
3. Watch Event Bus dead letter queue (should be near 0)
4. Alert on reconnection storms (> 5/minute)
5. Test graceful degradation under high connection load

### For Compliance/Audit

1. All broadcasts log which users received events
2. Events include user_id and timestamp for audit trail
3. Dead letter queue prevents silent failures
4. Review handler subscriptions via `get_event_bus_stats()`

---

## Next Steps

### To Use This Documentation

1. Copy to project wiki or docs/ directory
2. Link from main README.md in "Real-Time Features" section
3. Reference in onboarding checklist for new developers
4. Include in API reference alongside REST endpoints

### To Complete Missing Pieces

1. **Frontend**: Implement WebSocket client using provided TypeScript example
2. **Testing**: Add async WebSocket load tests (100+ concurrent connections)
3. **Clustering**: Document Redis pub/sub channel setup for GraphQL subscriptions
4. **Monitoring**: Add Prometheus metrics for WebSocket connection lifecycle
5. **Docs**: Add troubleshooting section for common connection issues

---

## Appendix: Event Flow Example

**Scenario**: Admin generates a new schedule

```
1. Schedule Engine calls:
   await broadcast_schedule_updated(
       schedule_id=schedule_uuid,
       update_type="generated",
       ...
   )

2. ConnectionManager.broadcast_to_schedule():
   - Gets all users watching this schedule_id
   - Calls send_to_user() for each

3. ConnectionManager.send_to_user():
   - Gets all connections for that user (multi-tab)
   - Calls connection.send_event() for each connection

4. Connection.send_event():
   - Serializes Pydantic event to JSON
   - Calls websocket.send_json(event)

5. Client receives:
   {
     "event_type": "schedule_updated",
     "schedule_id": "550e8400...",
     "timestamp": "2025-12-30T14:23:45.123Z",
     ...
   }

6. JavaScript handler:
   window.dispatchEvent(
     new CustomEvent('schedule-updated', {
       detail: eventPayload
     })
   )

7. React component listens:
   window.addEventListener('schedule-updated', () => {
     refetchSchedule()
   })
```

---

**Document Generated**: 2025-12-30 by G2_RECON
**Format**: Markdown
**Status**: Ready for Production Documentation
