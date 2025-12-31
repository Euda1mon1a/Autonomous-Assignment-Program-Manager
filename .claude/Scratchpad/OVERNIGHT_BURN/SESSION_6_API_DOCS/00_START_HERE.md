***REMOVED*** API Documentation - Start Here

**Welcome to the Residency Scheduler API Documentation**

This directory contains comprehensive documentation for all API endpoints, real-time features, and system architecture of the Residency Scheduler application.

---

***REMOVED******REMOVED*** What's Included

***REMOVED******REMOVED******REMOVED*** Complete API Documentation (9 files)

1. **api-docs-authentication.md** - Login, tokens, security
2. **api-docs-schedule.md** - Schedule generation and management
3. **api-docs-assignments.md** - Assignment operations
4. **api-docs-rotations.md** - Rotation templates and assignment
5. **api-docs-people.md** - Person/resident/faculty management
6. **api-docs-swaps.md** - Schedule swap workflows
7. **api-docs-procedures.md** - Procedure tracking and credentialing
8. **api-docs-admin.md** - System administration
9. **api-docs-realtime.md** - WebSocket and real-time events

***REMOVED******REMOVED******REMOVED*** Support Documentation

- **README.md** - Quick reference and overview
- **INDEX.md** - Navigation guide for all docs
- **SEARCH_PARTY_RESULTS.md** - How we discovered everything

---

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** If you're a Frontend Developer

1. Read: `api-docs-authentication.md` → JWT setup
2. Read: `api-docs-realtime.md` → "Client Integration Guide"
3. Copy: TypeScript WebSocket example from `api-docs-realtime.md`
4. Implement: All 8 event handlers
5. Test: With `/ws/health` and `/ws/stats` endpoints

***REMOVED******REMOVED******REMOVED*** If you're a Backend Developer

1. Read: `api-docs-schedule.md` → Core domain
2. Read: `api-docs-people.md` → Data models
3. Read: `api-docs-realtime.md` → "Event Bus System"
4. Review: How to broadcast events when making changes
5. Add: Tests following patterns in E2E tests

***REMOVED******REMOVED******REMOVED*** If you're in DevOps/Operations

1. Read: Each file → "Monitoring & Statistics" sections
2. Monitor: Health endpoints in all files
3. Alert on: Metrics and error codes documented
4. Configure: WebSocket cluster setup from `api-docs-realtime.md`

***REMOVED******REMOVED******REMOVED*** If you're in QA/Testing

1. Review: E2E test patterns in each file
2. Test: All endpoints with provided examples
3. Validate: Error scenarios documented in each file
4. Load test: Using patterns in `api-docs-realtime.md`

---

***REMOVED******REMOVED*** Key Discoveries

***REMOVED******REMOVED******REMOVED*** Three-Layer Real-Time Architecture

The application doesn't just have WebSockets - it has three integrated real-time layers:

1. **WebSocket Layer** - Client-facing live updates
2. **Event Bus Layer** - Internal loosely-coupled event distribution
3. **GraphQL Subscriptions** - Schema-aware typed subscriptions

All documented in `api-docs-realtime.md`.

***REMOVED******REMOVED******REMOVED*** Subscription-Based Broadcasting

Events aren't broadcast to everyone - they're smart:

- **Schedule-level**: Send to all users watching a specific schedule
- **Person-level**: Send to all users watching a specific person
- **User-level**: Send to all connections of one user (multi-tab)
- **System-wide**: Send to all users (only for resilience alerts)

***REMOVED******REMOVED******REMOVED*** Multi-Tab Support

One user in 5 browser tabs = 5 WebSocket connections. All managed automatically by the ConnectionManager singleton.

***REMOVED******REMOVED******REMOVED*** Resilience Built-In

- **Event Bus**: Failed handlers retry with exponential backoff
- **WebSocket**: Automatic reconnection (5 attempts, ~93 second total)
- **Connection Manager**: Thread-safe cleanup on disconnect
- **Dead Letter Queue**: Failed events can be manually replayed

---

***REMOVED******REMOVED*** File Statistics

| File | Size | Events | Endpoints | Examples |
|------|------|--------|-----------|----------|
| api-docs-authentication.md | 32 KB | - | 5 | 5 |
| api-docs-schedule.md | 31 KB | 10+ | 8 | 4 |
| api-docs-assignments.md | 38 KB | 4 | 8 | 6 |
| api-docs-rotations.md | 28 KB | 4 | 6 | 3 |
| api-docs-people.md | 33 KB | 4 | 8 | 4 |
| api-docs-swaps.md | 28 KB | 6 | 6 | 4 |
| api-docs-procedures.md | 37 KB | - | 7 | 5 |
| api-docs-admin.md | 29 KB | - | 10 | 4 |
| api-docs-realtime.md | 35 KB | 36 | 1 WS | 5 |
| **TOTAL** | **291 KB** | **64** | **59** | **40+** |

---

***REMOVED******REMOVED*** Navigation by Topic

***REMOVED******REMOVED******REMOVED*** Authentication & Security

- How to get a JWT token
- Token refresh and rotation
- Password reset and 2FA
- Role-based access control

→ Start with: `api-docs-authentication.md`

***REMOVED******REMOVED******REMOVED*** Creating & Managing Schedules

- Generate schedules with the solver
- Manage blocks and academic years
- Publish schedules
- Handle conflicts

→ Start with: `api-docs-schedule.md`

***REMOVED******REMOVED******REMOVED*** Real-Time Updates

- WebSocket connection and events
- Subscribe to schedule/person updates
- Reconnection and resilience
- Event bus and domain events

→ Start with: `api-docs-realtime.md`

***REMOVED******REMOVED******REMOVED*** Managing People

- Create/update residents and faculty
- Assign roles and PGY levels
- Track absences and leaves
- Credential management

→ Start with: `api-docs-people.md`

***REMOVED******REMOVED******REMOVED*** Schedule Swaps

- Request schedule swaps
- Auto-matching algorithm
- Approval workflow
- Rollback and cancellation

→ Start with: `api-docs-swaps.md`

***REMOVED******REMOVED******REMOVED*** Rotations & Procedures

- Create rotation templates
- Assign rotations to residents
- Track procedure competency
- Faculty credentialing

→ Start with: `api-docs-rotations.md` and `api-docs-procedures.md`

***REMOVED******REMOVED******REMOVED*** System Administration

- User management
- Roles and permissions
- Audit logging
- System configuration

→ Start with: `api-docs-admin.md`

---

***REMOVED******REMOVED*** Code Examples You'll Find

***REMOVED******REMOVED******REMOVED*** TypeScript/JavaScript

- WebSocket client class with reconnection
- React hooks for WebSocket events
- Custom event dispatching
- Exponential backoff implementation

***REMOVED******REMOVED******REMOVED*** Python/FastAPI

- How to publish domain events
- Event handler registration
- Broadcasting events to clients
- Dead letter queue handling

***REMOVED******REMOVED******REMOVED*** GraphQL

- Subscription type definitions
- Redis pub/sub integration
- Heartbeat and presence tracking

***REMOVED******REMOVED******REMOVED*** SQL

- Common query patterns
- Indexing for performance
- Transaction boundaries

---

***REMOVED******REMOVED*** API Response Format

All endpoints follow this pattern:

```json
{
  "status": "success",
  "data": { /* ... */ },
  "error": null,
  "timestamp": "2025-12-30T14:23:45.123Z"
}
```

Error responses:

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Human-readable message",
    "details": { /* optional */ }
  }
}
```

---

***REMOVED******REMOVED*** Testing Your Integration

***REMOVED******REMOVED******REMOVED*** Health Checks

```bash
***REMOVED*** WebSocket health
curl https://api.hospital.org/ws/health

***REMOVED*** WebSocket stats
curl -H "Authorization: Bearer TOKEN" https://api.hospital.org/ws/stats

***REMOVED*** API health
curl https://api.hospital.org/health
```

***REMOVED******REMOVED******REMOVED*** Test Scenarios

Each API doc file includes:

- ✅ Example requests
- ✅ Expected responses
- ✅ Error scenarios
- ✅ Edge cases
- ✅ Performance considerations

---

***REMOVED******REMOVED*** Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| WebSocket | ✅ Complete | Fully implemented and tested |
| Event Bus | ✅ Complete | In-memory pub/sub with retry |
| GraphQL Subscriptions | ✅ Complete | Strawberry + Redis |
| REST API Endpoints | ✅ Complete | 59 endpoints documented |
| E2E Tests | ✅ Complete | 20+ test cases (pending SQLite fix) |
| Frontend Client | ⏳ Partial | TypeScript example provided |
| Load Testing Suite | ⏳ Pending | Guidelines in docs |

---

***REMOVED******REMOVED*** Common Tasks

***REMOVED******REMOVED******REMOVED*** Generating a Schedule

1. Call: `POST /api/schedules`
2. Wait for: Long-running background task
3. Subscribe: To WebSocket for updates
4. Receive: `schedule_updated` event when complete
5. Verify: `/api/schedules/{id}` for details

***REMOVED******REMOVED******REMOVED*** Requesting a Swap

1. Call: `POST /api/swaps`
2. Submit: One-to-one or absorb request
3. Notify: Affected users via WebSocket
4. Review: In admin dashboard
5. Approve: `PATCH /api/swaps/{id}`

***REMOVED******REMOVED******REMOVED*** Adding a New Person

1. Call: `POST /api/people`
2. Set: Role and PGY level
3. Create: User account
4. Receive: WebSocket notification
5. View: In person management UI

---

***REMOVED******REMOVED*** Performance Guidelines

- **WebSocket**: Handle 1000+ concurrent connections
- **API**: <500ms response time for most endpoints
- **Schedule Generation**: 5-15 minutes depending on complexity
- **Swap Auto-Matching**: <2 seconds

See individual docs for detailed performance notes.

---

***REMOVED******REMOVED*** Production Deployment Checklist

Before going live, verify:

- [ ] SSL/TLS enabled for WebSockets (wss://)
- [ ] JWT secret configured (32+ chars)
- [ ] Database backups configured
- [ ] Monitoring alerts set up (see each doc)
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] Redis configured for Event Bus
- [ ] Log aggregation set up
- [ ] Load tested with 100+ concurrent users
- [ ] Error handling tested
- [ ] Graceful degradation verified

---

***REMOVED******REMOVED*** Getting Help

***REMOVED******REMOVED******REMOVED*** If Something Doesn't Work

1. Check the error code in the relevant API doc
2. Search the file for the error message
3. Review "Error Handling" section
4. Look for similar examples in the doc
5. Check the source code location listed

***REMOVED******REMOVED******REMOVED*** If You Find a Bug

1. Reproduce with curl/Postman using examples
2. Note the exact endpoint and payload
3. Check git history for recent changes
4. Review related tests in `backend/tests/`

***REMOVED******REMOVED******REMOVED*** If You Need New Features

1. Review "Event Bus System" in `api-docs-realtime.md`
2. Follow the pattern for your new event
3. Add E2E tests
4. Document in the appropriate file
5. Update this summary

---

***REMOVED******REMOVED*** Important Files in the Codebase

```
backend/app/
├── api/routes/         ***REMOVED*** API endpoints
│   ├── ws.py           ***REMOVED*** WebSocket
│   ├── auth.py         ***REMOVED*** Authentication
│   ├── schedules.py    ***REMOVED*** Schedule endpoints
│   └── ...
├── websocket/          ***REMOVED*** Real-time infrastructure
│   ├── manager.py      ***REMOVED*** ConnectionManager
│   ├── events.py       ***REMOVED*** WebSocket event types
│   └── __init__.py
├── events/             ***REMOVED*** Event bus
│   ├── event_bus.py    ***REMOVED*** Pub/sub engine
│   ├── event_types.py  ***REMOVED*** 28 domain events
│   └── handlers/       ***REMOVED*** Event handlers
├── services/           ***REMOVED*** Business logic
│   ├── swap_executor.py
│   ├── schedule_generator.py
│   └── ...
└── models/             ***REMOVED*** Database models
    ├── assignment.py
    ├── person.py
    └── ...

backend/tests/
├── e2e/
│   └── test_websocket_e2e.py  ***REMOVED*** WebSocket tests
├── unit/               ***REMOVED*** Unit tests for services
└── integration/        ***REMOVED*** Integration tests
```

---

***REMOVED******REMOVED*** Document Version

- **Generated**: 2025-12-30
- **API Endpoints Documented**: 59
- **Event Types Documented**: 64
- **Code Examples**: 40+
- **Status**: Production Ready

---

***REMOVED******REMOVED*** Next Steps

1. **Pick Your Role** (see Quick Start above)
2. **Read the Relevant Doc** (1-2 hours)
3. **Try the Examples** (in your language)
4. **Implement Your Feature**
5. **Test Using Provided Patterns**
6. **Reference in Production**

---

**Welcome aboard! Happy coding!**

