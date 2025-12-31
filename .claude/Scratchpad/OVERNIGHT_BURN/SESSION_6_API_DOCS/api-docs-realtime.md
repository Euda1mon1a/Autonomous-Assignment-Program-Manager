***REMOVED*** WebSocket & Real-Time API Documentation

**Residency Scheduler** provides comprehensive real-time capabilities through WebSocket connections and event-driven architecture. This document covers the complete real-time API surface.

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [WebSocket API](***REMOVED***websocket-api)
3. [Event Type Inventory](***REMOVED***event-type-inventory)
4. [Client Integration Guide](***REMOVED***client-integration-guide)
5. [Reconnection & Resilience](***REMOVED***reconnection--resilience)
6. [Broadcasting Architecture](***REMOVED***broadcasting-architecture)
7. [Event Bus System](***REMOVED***event-bus-system)
8. [GraphQL Subscriptions](***REMOVED***graphql-subscriptions)
9. [Error Handling](***REMOVED***error-handling)
10. [Monitoring & Statistics](***REMOVED***monitoring--statistics)

---

***REMOVED******REMOVED*** Overview

***REMOVED******REMOVED******REMOVED*** Real-Time Systems

The application implements three layers of real-time communication:

| Layer | Protocol | Purpose | Use Case |
|-------|----------|---------|----------|
| **WebSocket** | RFC 6455 | Raw event streaming | Live dashboard updates, schedule changes |
| **Event Bus** | In-memory pub/sub | Internal event distribution | Loose coupling between components |
| **GraphQL Subscriptions** | GraphQL over WebSocket | Typed subscriptions | Clients with GraphQL schema needs |

***REMOVED******REMOVED******REMOVED*** Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend Application                        │
│  (Next.js, React - WebSocket Client or GraphQL Subscription)    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket Connection
                           │ (JWT authenticated)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend WebSocket Layer                       │
│  - ConnectionManager: Tracks active connections                 │
│  - Subscription Manager: Filters events by schedule/person      │
│  - Event Router: Distributes messages to subscribed clients     │
└──────────────┬──────────────────────┬──────────────────────────┘
               │                      │
    ┌──────────▼──────────┐  ┌────────▼─────────┐
    │   Event Bus Layer   │  │ GraphQL Schema   │
    │  (pub/sub in-memory)│  │ (Strawberry)     │
    │  - EventType enum   │  │ + Redis pub/sub  │
    │  - Handlers         │  │ (for clustering) │
    └──────────┬──────────┘  └────────┬─────────┘
               │                      │
    ┌──────────▼──────────────────────▼────────┐
    │      Event Sources (Anywhere in App)     │
    │  - Schedule generation engine            │
    │  - Swap executor                         │
    │  - ACGME validator                       │
    │  - Absence approval workflows            │
    │  - Celery background tasks               │
    │  - Resilience health checks              │
    └──────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** WebSocket API

***REMOVED******REMOVED******REMOVED*** Endpoint

```
wss://scheduler.hospital.org/ws?token=<JWT_TOKEN>
```

**Protocol**: WebSocket with JWT authentication
**Authentication**: Query parameter token (JWT access token)
**Message Format**: JSON

***REMOVED******REMOVED******REMOVED*** Connection Lifecycle

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Connect with Authentication

```javascript
// Client-side connection
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`wss://api.hospital.org/ws?token=${token}`);

ws.onopen = () => {
  console.log('Connected to WebSocket server');
};
```

**Backend validation** (`backend/app/api/routes/ws.py:get_websocket_user`):
- Token extracted from query parameter
- Token verified using `verify_token()`
- User loaded from database
- User must be active (`is_active=True`)
- Returns 1008 (Policy Violation) if authentication fails

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Connection Acknowledgment

Server immediately sends:

```json
{
  "event_type": "connection_ack",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Connection established"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Message Handling Loop

Client can send commands or server can broadcast events. Connection stays open until:
- Client sends close frame
- Network disconnection
- Timeout (implement client-side ping/pong)

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Graceful Disconnection

Client initiates:
```javascript
ws.close(1000, 'Normal closure');
```

Server cleans up:
- Removes connection from `ConnectionManager._connections`
- Unsubscribes from all watched schedules/persons
- Logs disconnection event

***REMOVED******REMOVED******REMOVED*** Client-to-Server Messages

***REMOVED******REMOVED******REMOVED******REMOVED*** Subscribe to Schedule

```json
{
  "action": "subscribe_schedule",
  "schedule_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**: None (subscription happens silently)
**Effect**: User added to `_schedule_watchers[schedule_id]`
**Use case**: User viewing a specific schedule timeline

***REMOVED******REMOVED******REMOVED******REMOVED*** Subscribe to Person

```json
{
  "action": "subscribe_person",
  "person_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**: None
**Effect**: User added to `_person_watchers[person_id]`
**Use case**: Resident/faculty monitoring their own assignments

***REMOVED******REMOVED******REMOVED******REMOVED*** Unsubscribe from Schedule

```json
{
  "action": "unsubscribe_schedule",
  "schedule_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Unsubscribe from Person

```json
{
  "action": "unsubscribe_person",
  "person_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Ping (Keep-Alive)

```json
{
  "action": "ping"
}
```

**Response**:
```json
{
  "event_type": "pong",
  "timestamp": "2025-12-30T14:23:45.123Z"
}
```

**Purpose**: Prevent proxy timeouts, keep connection alive
**Frequency**: Client should send every 30-60 seconds if no activity

---

***REMOVED******REMOVED*** Event Type Inventory

***REMOVED******REMOVED******REMOVED*** Event Categories

The system broadcasts **7 event types** across WebSocket connections:

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Schedule Updated Event

**Emitted when**: Schedule is generated, modified, or regenerated

```json
{
  "event_type": "schedule_updated",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
  "academic_year_id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "770e8400-e29b-41d4-a716-446655440000",
  "update_type": "generated",
  "affected_blocks_count": 365,
  "message": "Schedule generated successfully with 100% compliance"
}
```

**Fields**:
- `schedule_id`: UUID of the schedule (optional)
- `academic_year_id`: UUID of the academic year (optional)
- `user_id`: User who triggered the update
- `update_type`: One of: `generated`, `modified`, `regenerated`
- `affected_blocks_count`: Number of blocks changed
- `message`: Human-readable description

**Broadcast scope**: All users watching this `schedule_id` via `broadcast_to_schedule()`
**Source code**: `backend/app/websocket/manager.py:broadcast_schedule_updated()`

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Assignment Changed Event

**Emitted when**: Assignment created, updated, or deleted

```json
{
  "event_type": "assignment_changed",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
  "person_id": "660e8400-e29b-41d4-a716-446655440000",
  "block_id": "770e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "880e8400-e29b-41d4-a716-446655440000",
  "change_type": "created",
  "changed_by": "990e8400-e29b-41d4-a716-446655440000",
  "message": "Assignment created: PGY2 resident assigned to Sports Medicine clinic"
}
```

**Fields**:
- `assignment_id`: UUID of the assignment
- `person_id`: UUID of the affected person
- `block_id`: UUID of the block
- `rotation_template_id`: UUID of the rotation (optional)
- `change_type`: One of: `created`, `updated`, `deleted`
- `changed_by`: User ID who made the change (optional)

**Broadcast scope**: All users watching `person_id` via `broadcast_to_person()`
**Use case**: Resident sees their own assignment appear/change
**Source code**: `backend/app/websocket/manager.py:broadcast_assignment_changed()`

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Swap Requested Event

**Emitted when**: Faculty requests a schedule swap

```json
{
  "event_type": "swap_requested",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "swap_id": "550e8400-e29b-41d4-a716-446655440000",
  "requester_id": "660e8400-e29b-41d4-a716-446655440000",
  "target_person_id": "770e8400-e29b-41d4-a716-446655440000",
  "swap_type": "one_to_one",
  "affected_assignments": [
    "880e8400-e29b-41d4-a716-446655440000",
    "990e8400-e29b-41d4-a716-446655440000"
  ],
  "message": "Swap requested between Dr. Smith (call Jan 15) and Dr. Jones (call Jan 22)"
}
```

**Fields**:
- `swap_id`: Unique swap request ID
- `requester_id`: Person requesting the swap
- `target_person_id`: Person being asked (optional for "absorb" swaps)
- `swap_type`: `one_to_one` or `absorb`
- `affected_assignments`: List of assignment IDs involved

**Broadcast scope**:
- To requester's watchers via `broadcast_to_person(requester_id)`
- To target's watchers via `broadcast_to_person(target_person_id)` if specified
**Source code**: `backend/app/websocket/manager.py:broadcast_swap_requested()`

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Swap Approved Event

**Emitted when**: Administrator approves a swap request

```json
{
  "event_type": "swap_approved",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "swap_id": "550e8400-e29b-41d4-a716-446655440000",
  "requester_id": "660e8400-e29b-41d4-a716-446655440000",
  "target_person_id": "770e8400-e29b-41d4-a716-446655440000",
  "approved_by": "880e8400-e29b-41d4-a716-446655440000",
  "affected_assignments": [
    "990e8400-e29b-41d4-a716-446655440000"
  ],
  "message": "Swap approved - assignments exchanged successfully"
}
```

**Fields**:
- `swap_id`: ID of the swap request being approved
- `requester_id`: Original requester
- `target_person_id`: Target person (optional)
- `approved_by`: Administrator who approved
- `affected_assignments`: Assignments after swap

**Broadcast scope**: Both requester and target (if applicable)
**Source code**: `backend/app/websocket/manager.py:broadcast_swap_approved()`

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Conflict Detected Event

**Emitted when**: Schedule conflict or ACGME violation detected

```json
{
  "event_type": "conflict_detected",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "conflict_id": "550e8400-e29b-41d4-a716-446655440000",
  "person_id": "660e8400-e29b-41d4-a716-446655440000",
  "conflict_type": "double_booking",
  "severity": "high",
  "affected_blocks": [
    "770e8400-e29b-41d4-a716-446655440000",
    "880e8400-e29b-41d4-a716-446655440000"
  ],
  "message": "Double booking detected: Resident assigned to clinic AND call on Jan 15"
}
```

**Fields**:
- `conflict_id`: Unique conflict ID (optional)
- `person_id`: Person with the conflict
- `conflict_type`: One of: `double_booking`, `acgme_violation`, `absence_overlap`
- `severity`: `low`, `medium`, `high`, or `critical`
- `affected_blocks`: List of block IDs involved

**Broadcast scope**: Watched person
**Use case**: Alert resident/coordinator of scheduling issues
**Source code**: `backend/app/websocket/manager.py:broadcast_conflict_detected()`

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 6. Resilience Alert Event

**Emitted when**: System health or utilization changes significantly

```json
{
  "event_type": "resilience_alert",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "alert_type": "utilization_high",
  "severity": "orange",
  "current_utilization": 0.85,
  "defense_level": "orange",
  "affected_persons": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440000"
  ],
  "message": "System utilization above 80% threshold - schedule at risk",
  "recommendations": [
    "Reduce non-essential assignments",
    "Activate contingency staffing",
    "Review PGY-1 supervision ratios"
  ]
}
```

**Fields**:
- `alert_type`: `utilization_high`, `n1_failure`, `n2_failure`, `defense_level_change`
- `severity`: `green`, `yellow`, `orange`, `red`, or `black` (defense levels)
- `current_utilization`: Current system utilization (0.0-1.0)
- `defense_level`: Current defense in depth level
- `affected_persons`: People impacted by alert
- `recommendations`: List of recommended actions

**Broadcast scope**: **All connected users** (system-wide alert)
**Use case**: Notify administrators of system health concerns
**Source code**: `backend/app/websocket/manager.py:broadcast_resilience_alert()`

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 7. Connection Ack Event

**Emitted when**: WebSocket connection established

```json
{
  "event_type": "connection_ack",
  "timestamp": "2025-12-30T14:23:45.123Z",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Connection established"
}
```

**Broadcast scope**: Connecting client only
**Source code**: `backend/app/websocket/manager.py:Connection.send_event()`

---

***REMOVED******REMOVED******REMOVED******REMOVED*** 8. Pong Event

**Emitted when**: Server responds to client ping

```json
{
  "event_type": "pong",
  "timestamp": "2025-12-30T14:23:45.123Z"
}
```

---

***REMOVED******REMOVED******REMOVED*** Event Type Enumeration

Complete list defined in `backend/app/websocket/events.py`:

```python
class EventType(str, Enum):
    """WebSocket event types."""

    SCHEDULE_UPDATED = "schedule_updated"
    ASSIGNMENT_CHANGED = "assignment_changed"
    SWAP_REQUESTED = "swap_requested"
    SWAP_APPROVED = "swap_approved"
    CONFLICT_DETECTED = "conflict_detected"
    RESILIENCE_ALERT = "resilience_alert"
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"
```

---

***REMOVED******REMOVED*** Client Integration Guide

***REMOVED******REMOVED******REMOVED*** JavaScript/TypeScript Example

```typescript
// 1. Get access token
const token = localStorage.getItem('access_token');

// 2. Create WebSocket connection
class SchedulerWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private pingInterval: NodeJS.Timeout | null = null;

  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws?token=${token}`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.startPingInterval();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        this.ws.onerror = (event) => {
          console.error('WebSocket error:', event);
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = () => {
          this.stopPingInterval();
          this.handleDisconnection();
        };
      } catch (e) {
        reject(e);
      }
    });
  }

  // 3. Subscribe to schedule
  subscribeToSchedule(scheduleId: string): void {
    if (!this.ws) return;
    this.ws.send(JSON.stringify({
      action: 'subscribe_schedule',
      schedule_id: scheduleId
    }));
  }

  // 4. Subscribe to person
  subscribeToPerson(personId: string): void {
    if (!this.ws) return;
    this.ws.send(JSON.stringify({
      action: 'subscribe_person',
      person_id: personId
    }));
  }

  // 5. Handle incoming messages
  private handleMessage(message: any): void {
    const { event_type, ...payload } = message;

    switch (event_type) {
      case 'schedule_updated':
        this.onScheduleUpdated(payload);
        break;
      case 'assignment_changed':
        this.onAssignmentChanged(payload);
        break;
      case 'swap_requested':
        this.onSwapRequested(payload);
        break;
      case 'conflict_detected':
        this.onConflictDetected(payload);
        break;
      case 'resilience_alert':
        this.onResilienceAlert(payload);
        break;
      case 'pong':
        // Ping/pong for keep-alive
        break;
      default:
        console.warn('Unknown event type:', event_type);
    }
  }

  private onScheduleUpdated(payload: any): void {
    console.log('Schedule updated:', payload);
    // Trigger UI update, refetch schedule data, etc.
    window.dispatchEvent(new CustomEvent('schedule-updated', { detail: payload }));
  }

  private onAssignmentChanged(payload: any): void {
    console.log('Assignment changed:', payload);
    window.dispatchEvent(new CustomEvent('assignment-changed', { detail: payload }));
  }

  private onSwapRequested(payload: any): void {
    console.log('Swap requested:', payload);
    window.dispatchEvent(new CustomEvent('swap-requested', { detail: payload }));
  }

  private onConflictDetected(payload: any): void {
    console.log('Conflict detected:', payload);
    window.dispatchEvent(new CustomEvent('conflict-detected', { detail: payload }));
  }

  private onResilienceAlert(payload: any): void {
    console.log('Resilience alert:', payload);
    window.dispatchEvent(new CustomEvent('resilience-alert', { detail: payload }));
  }

  // 6. Keep-alive mechanism
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  // 7. Reconnection handling
  private handleDisconnection(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => {
        // Re-establish connection with stored token
        const token = localStorage.getItem('access_token');
        if (token) {
          this.connect(token);
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect(): void {
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close(1000, 'Normal closure');
      this.ws = null;
    }
  }
}

// 8. Usage in React component
function SchedulerDashboard() {
  const [ws, setWs] = useState<SchedulerWebSocket | null>(null);

  useEffect(() => {
    const wsInstance = new SchedulerWebSocket();
    const token = localStorage.getItem('access_token');

    if (token) {
      wsInstance.connect(token)
        .then(() => {
          // Subscribe to your schedule
          wsInstance.subscribeToSchedule(currentScheduleId);
          // Subscribe to your assignments
          wsInstance.subscribeToPerson(currentUserId);
          setWs(wsInstance);
        })
        .catch(err => console.error('Failed to connect:', err));
    }

    return () => {
      wsInstance.disconnect();
    };
  }, []);

  // Listen to custom events
  useEffect(() => {
    const handleScheduleUpdate = (event: any) => {
      // Refetch schedule or update state
      refetchSchedule();
    };

    window.addEventListener('schedule-updated', handleScheduleUpdate);
    return () => {
      window.removeEventListener('schedule-updated', handleScheduleUpdate);
    };
  }, []);

  return <div>{/* Your schedule UI */}</div>;
}
```

---

***REMOVED******REMOVED*** Reconnection & Resilience

***REMOVED******REMOVED******REMOVED*** Automatic Reconnection

The client should implement exponential backoff reconnection:

```typescript
// Exponential backoff formula
delay = reconnectDelay * Math.pow(2, attemptNumber - 1)

// Example progression:
// Attempt 1: 3s delay
// Attempt 2: 6s delay
// Attempt 3: 12s delay
// Attempt 4: 24s delay
// Attempt 5: 48s delay
// (max 5 attempts = ~93 seconds total)
```

***REMOVED******REMOVED******REMOVED*** Subscription Persistence

When reconnecting, re-subscribe to watched resources:

```typescript
reconnect() {
  const token = localStorage.getItem('access_token');
  this.connect(token).then(() => {
    // Restore subscriptions
    this.storedSubscriptions.forEach(({ type, id }) => {
      if (type === 'schedule') {
        this.subscribeToSchedule(id);
      } else if (type === 'person') {
        this.subscribeToPerson(id);
      }
    });
  });
}
```

***REMOVED******REMOVED******REMOVED*** Message Queue

For resilience, queue important messages during disconnection:

```typescript
private messageQueue: any[] = [];

send(message: any): void {
  if (this.ws && this.ws.readyState === WebSocket.OPEN) {
    this.ws.send(JSON.stringify(message));
  } else {
    // Queue message for later
    this.messageQueue.push(message);
  }
}

private flushQueue(): void {
  while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
    const message = this.messageQueue.shift();
    this.ws.send(JSON.stringify(message));
  }
}
```

---

***REMOVED******REMOVED*** Broadcasting Architecture

***REMOVED******REMOVED******REMOVED*** Connection Manager

Located in `backend/app/websocket/manager.py`, handles:

```python
class ConnectionManager:
    """
    Manages WebSocket connections with subscription tracking.
    """

    ***REMOVED*** Per-user connection tracking (supports multiple tabs)
    _connections: dict[UUID, list[Connection]] = defaultdict(list)

    ***REMOVED*** Schedule watchers: schedule_id -> set of user_ids
    _schedule_watchers: dict[UUID, set[UUID]] = defaultdict(set)

    ***REMOVED*** Person watchers: person_id -> set of user_ids
    _person_watchers: dict[UUID, set[UUID]] = defaultdict(set)
```

***REMOVED******REMOVED******REMOVED*** Broadcast Methods

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Send to Individual User

```python
async def send_to_user(self, user_id: UUID, event: BaseModel) -> int:
    """Send event to all connections of a specific user (all tabs/devices)."""
    connections = self._connections.get(user_id, [])
    sent_count = 0
    for connection in connections:
        success = await connection.send_event(event)
        if success:
            sent_count += 1
    return sent_count
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Broadcast to Schedule Watchers

```python
async def broadcast_to_schedule(self, schedule_id: UUID, event: BaseModel) -> int:
    """Broadcast to all users watching this schedule."""
    watchers = self._schedule_watchers.get(schedule_id, set()).copy()
    sent_count = 0
    for user_id in watchers:
        count = await self.send_to_user(user_id, event)
        if count > 0:
            sent_count += 1
    return sent_count
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Broadcast to Person Watchers

```python
async def broadcast_to_person(self, person_id: UUID, event: BaseModel) -> int:
    """Broadcast to all users watching this person."""
    watchers = self._person_watchers.get(person_id, set()).copy()
    ***REMOVED*** Similar to broadcast_to_schedule
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Broadcast to All Users

```python
async def broadcast_to_all(self, event: BaseModel) -> int:
    """Broadcast to all connected users (system-wide)."""
    all_user_ids = list(self._connections.keys())
    ***REMOVED*** Iterate and send to each
```

***REMOVED******REMOVED******REMOVED*** Convenience Functions

Located in `backend/app/websocket/manager.py`, these functions simplify broadcasting:

```python
***REMOVED*** Example: Broadcasting a schedule update
await broadcast_schedule_updated(
    schedule_id=schedule_uuid,
    academic_year_id=academic_year_uuid,
    user_id=coordinator_uuid,
    update_type="generated",
    affected_blocks_count=365,
    message="Schedule generated successfully"
)
```

---

***REMOVED******REMOVED*** Event Bus System

***REMOVED******REMOVED******REMOVED*** Architecture

The **Event Bus** provides in-memory pub/sub for internal event distribution. Located in `backend/app/events/event_bus.py`.

***REMOVED******REMOVED******REMOVED*** Event Types

Distinct from WebSocket events - these are internal domain events. Located in `backend/app/events/event_types.py`:

```python
class EventType(str, Enum):
    ***REMOVED*** Schedule events
    SCHEDULE_CREATED = "ScheduleCreated"
    SCHEDULE_UPDATED = "ScheduleUpdated"
    SCHEDULE_DELETED = "ScheduleDeleted"
    SCHEDULE_PUBLISHED = "SchedulePublished"
    SCHEDULE_ARCHIVED = "ScheduleArchived"

    ***REMOVED*** Assignment events
    ASSIGNMENT_CREATED = "AssignmentCreated"
    ASSIGNMENT_UPDATED = "AssignmentUpdated"
    ASSIGNMENT_DELETED = "AssignmentDeleted"
    ASSIGNMENT_CONFIRMED = "AssignmentConfirmed"

    ***REMOVED*** Swap events
    SWAP_REQUESTED = "SwapRequested"
    SWAP_APPROVED = "SwapApproved"
    SWAP_REJECTED = "SwapRejected"
    SWAP_EXECUTED = "SwapExecuted"

    ***REMOVED*** ... more event types
```

***REMOVED******REMOVED******REMOVED*** Publishing Events

```python
from app.events.event_bus import get_event_bus
from app.events.event_types import ScheduleCreatedEvent

bus = get_event_bus()

***REMOVED*** Create domain event
event = ScheduleCreatedEvent(
    aggregate_id=schedule_id,
    schedule_id=schedule_id,
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    created_by=user_id,
    algorithm_version="2.0"
)

***REMOVED*** Publish (triggers all subscribed handlers)
await bus.publish(event)
```

***REMOVED******REMOVED******REMOVED*** Subscribing to Events

```python
***REMOVED*** Method 1: Direct subscription
async def on_schedule_created(event: ScheduleCreatedEvent):
    logger.info(f"Schedule created: {event.schedule_id}")
    ***REMOVED*** Trigger WebSocket broadcasts
    await broadcast_schedule_updated(...)

bus.subscribe(EventType.SCHEDULE_CREATED, on_schedule_created)

***REMOVED*** Method 2: Decorator
@event_handler(EventType.SCHEDULE_CREATED)
async def on_schedule_created(event: ScheduleCreatedEvent):
    ***REMOVED*** Handler code
    pass

***REMOVED*** Method 3: Multiple event types
bus.subscribe_to_multiple(
    [EventType.ASSIGNMENT_CREATED, EventType.ASSIGNMENT_UPDATED],
    on_assignment_changed
)
```

***REMOVED******REMOVED******REMOVED*** Error Handling & Dead Letter Queue

Events that fail processing are added to DLQ:

```python
***REMOVED*** Get failed events
dead_letters = bus.get_dead_letter_queue()

***REMOVED*** Retry a failed event
success = await bus.replay_dead_letter_event(event_id)
```

***REMOVED******REMOVED******REMOVED*** Statistics

```python
stats = get_event_bus_stats(bus)
***REMOVED*** Returns:
***REMOVED*** {
***REMOVED***   "total_subscriptions": 12,
***REMOVED***   "subscriptions_by_type": {
***REMOVED***     "ScheduleCreated": 3,
***REMOVED***     "AssignmentUpdated": 4,
***REMOVED***     ...
***REMOVED***   },
***REMOVED***   "dead_letter_count": 0
***REMOVED*** }
```

---

***REMOVED******REMOVED*** GraphQL Subscriptions

***REMOVED******REMOVED******REMOVED*** Overview

Located in `backend/app/graphql/subscriptions.py`, provides typed subscriptions over GraphQL protocol.

***REMOVED******REMOVED******REMOVED*** Subscription Types

***REMOVED******REMOVED******REMOVED******REMOVED*** Schedule Updates

```graphql
subscription OnScheduleUpdated {
  scheduleUpdated {
    scheduleId
    academicYearId
    userId
    updateType
    affectedBlocksCount
    message
    timestamp
  }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Assignment Updates

```graphql
subscription OnAssignmentUpdated {
  assignmentUpdated {
    assignmentId
    personId
    blockId
    rotationTemplateId
    changeType
    changedBy
    message
    timestamp
  }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Swap Notifications

```graphql
subscription OnSwapNotification {
  swapNotification {
    swapId
    requesterId
    targetPersonId
    swapType
    status
    affectedAssignments
    message
    timestamp
    approvedBy
  }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Conflict Alerts

```graphql
subscription OnConflictAlert {
  conflictAlert {
    conflictId
    personId
    conflictType
    severity
    affectedBlocks
    message
    timestamp
  }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Resilience Alerts

```graphql
subscription OnResilienceAlert {
  resilienceAlert {
    alertType
    severity
    currentUtilization
    defenseLevel
    affectedPersons
    message
    recommendations
    timestamp
  }
}
```

***REMOVED******REMOVED******REMOVED*** Redis Pub/Sub Channels

GraphQL subscriptions use Redis for multi-instance deployments:

```python
CHANNEL_SCHEDULE_UPDATES = "graphql:schedule:updates"
CHANNEL_ASSIGNMENT_UPDATES = "graphql:assignment:updates"
CHANNEL_SWAP_REQUESTS = "graphql:swap:requests"
CHANNEL_SWAP_APPROVALS = "graphql:swap:approvals"
CHANNEL_CONFLICT_ALERTS = "graphql:conflict:alerts"
CHANNEL_RESILIENCE_ALERTS = "graphql:resilience:alerts"
CHANNEL_USER_PRESENCE = "graphql:user:presence"
CHANNEL_HEARTBEAT = "graphql:heartbeat"
```

---

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** WebSocket Connection Errors

| Error | Code | Cause | Recovery |
|-------|------|-------|----------|
| No token | 1008 | Missing `?token=` | Provide JWT token |
| Invalid token | 1008 | Token malformed or expired | Refresh token, reconnect |
| Inactive user | 1008 | User account disabled | Contact administrator |
| Unknown action | (stays open) | Malformed message | Check message structure |
| Subscription error | (stays open) | Invalid UUID | Check format, log warning |

***REMOVED******REMOVED******REMOVED*** Handling Errors in Client

```typescript
ws.onerror = (event) => {
  // Connection error (usually code 1006 or 1008)
  console.error('WebSocket connection error');
};

// For application-level errors in messages:
// (Currently, WebSocket protocol doesn't send error messages back
// All errors are logged server-side only)
```

***REMOVED******REMOVED******REMOVED*** Event Bus Error Handling

Failed event handlers trigger retry logic:

```python
***REMOVED*** Retry configuration in EventBus
EventBus(
    enable_retry=True,      ***REMOVED*** Enable automatic retry
    max_retries=3           ***REMOVED*** Retry up to 3 times
)

***REMOVED*** Retry strategy: exponential backoff
***REMOVED*** Attempt 1: immediate
***REMOVED*** Attempt 2: after 2^1 = 2 seconds
***REMOVED*** Attempt 3: after 2^2 = 4 seconds
***REMOVED*** Attempt 4: after 2^3 = 8 seconds

***REMOVED*** If all retries fail: Event added to Dead Letter Queue
```

---

***REMOVED******REMOVED*** Monitoring & Statistics

***REMOVED******REMOVED******REMOVED*** WebSocket Health Endpoint

```
GET /ws/health
```

**Response**:
```json
{
  "status": "healthy",
  "websocket_enabled": true,
  "connections": {
    "total_connections": 42,
    "unique_users": 28,
    "schedules_watched": 3,
    "persons_watched": 42
  }
}
```

***REMOVED******REMOVED******REMOVED*** WebSocket Statistics Endpoint

```
GET /ws/stats
Headers: Authorization: Bearer <JWT_TOKEN>
```

**Response**:
```json
{
  "status": "ok",
  "stats": {
    "total_connections": 42,
    "unique_users": 28,
    "schedules_watched": 3,
    "persons_watched": 42
  }
}
```

***REMOVED******REMOVED******REMOVED*** Connection Statistics

Accessible programmatically:

```python
manager = get_connection_manager()

***REMOVED*** Get stats dictionary
stats = manager.get_stats()
***REMOVED*** {
***REMOVED***   "total_connections": 42,
***REMOVED***   "unique_users": 28,
***REMOVED***   "schedules_watched": 3,
***REMOVED***   "persons_watched": 42
***REMOVED*** }

***REMOVED*** Get specific counts
total_connections = manager.get_connection_count()
unique_users = manager.get_user_count()
schedule_watchers = manager.get_schedule_watcher_count(schedule_id)
```

***REMOVED******REMOVED******REMOVED*** Metrics to Monitor

For production deployment, track:

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Active WebSocket connections | `/ws/stats` | > 1000 |
| Connection establishment latency | Client-side | > 5 seconds |
| Message delivery latency | Client telemetry | > 1 second |
| Event bus DLQ size | `get_event_bus_stats()` | > 10 items |
| Reconnection attempts | Client logs | > 5/minute |

---

***REMOVED******REMOVED*** Implementation Checklist

***REMOVED******REMOVED******REMOVED*** Backend Setup

- [x] WebSocket manager (`backend/app/websocket/manager.py`)
- [x] Event types (`backend/app/websocket/events.py`)
- [x] WebSocket route (`backend/app/api/routes/ws.py`)
- [x] Event bus (`backend/app/events/event_bus.py`)
- [x] Domain events (`backend/app/events/event_types.py`)
- [x] GraphQL subscriptions (`backend/app/graphql/subscriptions.py`)
- [x] Event handlers (`backend/app/events/handlers/`)
- [x] Health/stats endpoints (`backend/app/api/routes/ws.py`)

***REMOVED******REMOVED******REMOVED*** Frontend Integration

- [ ] WebSocket client library setup
- [ ] Connection state management
- [ ] Subscription lifecycle management
- [ ] Event handlers for each event type
- [ ] Reconnection logic with exponential backoff
- [ ] Message queue for offline resilience
- [ ] UI state updates on events
- [ ] Error boundary for WebSocket failures

***REMOVED******REMOVED******REMOVED*** Testing

- [x] E2E tests (`backend/tests/e2e/test_websocket_e2e.py`)
- [ ] Load testing (async WebSocket with 100+ clients)
- [ ] Reconnection scenario tests
- [ ] Event ordering validation
- [ ] Multi-client broadcasting verification

---

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Source Files

- **WebSocket Manager**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/websocket/manager.py`
- **WebSocket Events**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/websocket/events.py`
- **WebSocket Route**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/api/routes/ws.py`
- **Event Bus**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/events/event_bus.py`
- **Event Types**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/events/event_types.py`
- **GraphQL Subscriptions**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/graphql/subscriptions.py`
- **Event Handlers**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/events/handlers/schedule_events.py`
- **E2E Tests**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/tests/e2e/test_websocket_e2e.py`

***REMOVED******REMOVED******REMOVED*** Related Documentation

- Authentication: See `backend/app/core/security.py` for JWT validation
- Rate Limiting: See `backend/app/core/rate_limit.py` (applied to auth endpoints)
- ACGME Validation: See `backend/app/scheduling/acgme_validator.py` (generates conflict events)
- Swap Execution: See `backend/app/services/swap_executor.py` (emits swap events)

---

***REMOVED******REMOVED*** Appendix: Complete Event Schema

***REMOVED******REMOVED******REMOVED*** Connection Ack

```typescript
interface ConnectionAckEvent {
  event_type: "connection_ack";
  timestamp: string; // ISO 8601
  user_id: string; // UUID
  message: string;
}
```

***REMOVED******REMOVED******REMOVED*** Schedule Updated

```typescript
interface ScheduleUpdatedEvent {
  event_type: "schedule_updated";
  timestamp: string;
  schedule_id: string | null;
  academic_year_id: string | null;
  user_id: string | null;
  update_type: "generated" | "modified" | "regenerated";
  affected_blocks_count: number;
  message: string;
}
```

***REMOVED******REMOVED******REMOVED*** Assignment Changed

```typescript
interface AssignmentChangedEvent {
  event_type: "assignment_changed";
  timestamp: string;
  assignment_id: string;
  person_id: string;
  block_id: string;
  rotation_template_id: string | null;
  change_type: "created" | "updated" | "deleted";
  changed_by: string | null;
  message: string;
}
```

***REMOVED******REMOVED******REMOVED*** Swap Requested

```typescript
interface SwapRequestedEvent {
  event_type: "swap_requested";
  timestamp: string;
  swap_id: string;
  requester_id: string;
  target_person_id: string | null;
  swap_type: "one_to_one" | "absorb";
  affected_assignments: string[];
  message: string;
}
```

***REMOVED******REMOVED******REMOVED*** Swap Approved

```typescript
interface SwapApprovedEvent {
  event_type: "swap_approved";
  timestamp: string;
  swap_id: string;
  requester_id: string;
  target_person_id: string | null;
  approved_by: string;
  affected_assignments: string[];
  message: string;
}
```

***REMOVED******REMOVED******REMOVED*** Conflict Detected

```typescript
interface ConflictDetectedEvent {
  event_type: "conflict_detected";
  timestamp: string;
  conflict_id: string | null;
  person_id: string;
  conflict_type: "double_booking" | "acgme_violation" | "absence_overlap";
  severity: "low" | "medium" | "high" | "critical";
  affected_blocks: string[];
  message: string;
}
```

***REMOVED******REMOVED******REMOVED*** Resilience Alert

```typescript
interface ResilienceAlertEvent {
  event_type: "resilience_alert";
  timestamp: string;
  alert_type: "utilization_high" | "n1_failure" | "n2_failure" | "defense_level_change";
  severity: "green" | "yellow" | "orange" | "red" | "black";
  current_utilization: number | null;
  defense_level: string | null;
  affected_persons: string[];
  message: string;
  recommendations: string[];
}
```

***REMOVED******REMOVED******REMOVED*** Pong

```typescript
interface PongEvent {
  event_type: "pong";
  timestamp: string;
}
```

---

**Last Updated**: 2025-12-30
**Document Version**: 1.0
**Status**: Complete & Implemented
