# GraphQL Subscriptions for Real-Time Updates

This document describes the GraphQL subscription system for the Residency Scheduler backend.

## Overview

The GraphQL subscription system provides real-time updates for:
- Schedule changes
- Assignment updates
- Swap requests and approvals
- Conflict alerts
- Resilience system alerts
- User presence tracking
- Connection heartbeat/keep-alive

## Architecture

### Components

1. **Strawberry GraphQL**: GraphQL server implementation
2. **Redis Pub/Sub**: Message broadcasting infrastructure
3. **WebSocket Transport**: Real-time bidirectional communication
4. **Connection Manager**: Manages active subscriptions and filtering

### Data Flow

```
Backend Service
    ↓ (calls broadcast function)
Redis Pub/Sub
    ↓ (publishes to channel)
RedisSubscriptionManager
    ↓ (filters & yields)
Strawberry Subscription
    ↓ (GraphQL over WebSocket)
Client Application
```

## Available Subscriptions

### 1. Schedule Updates

Subscribe to real-time schedule changes.

**GraphQL Query:**
```graphql
subscription ScheduleUpdates {
  scheduleUpdates(filter: {
    scheduleId: "123e4567-e89b-12d3-a456-426614174000"
    updateTypes: ["generated", "modified"]
  }) {
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

**Filter Options:**
- `scheduleId`: Filter by specific schedule
- `academicYearId`: Filter by academic year
- `personId`: Filter by person
- `updateTypes`: Filter by update type (generated, modified, regenerated)

**Broadcasting from Backend:**
```python
from app.graphql import broadcast_schedule_update

await broadcast_schedule_update(
    schedule_id=schedule_id,
    academic_year_id=year_id,
    user_id=current_user.id,
    update_type="generated",
    affected_blocks_count=100,
    message="Schedule successfully generated"
)
```

### 2. Assignment Updates

Subscribe to assignment changes for specific people.

**GraphQL Query:**
```graphql
subscription AssignmentUpdates {
  assignmentUpdates(personId: "456e7890-e89b-12d3-a456-426614174001") {
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

**Broadcasting from Backend:**
```python
from app.graphql import broadcast_assignment_update

await broadcast_assignment_update(
    assignment_id=assignment.id,
    person_id=person.id,
    block_id=block.id,
    rotation_template_id=rotation.id,
    change_type="created",
    changed_by=current_user.id,
    message="Assignment created successfully"
)
```

### 3. Swap Request Notifications

Subscribe to swap request events.

**GraphQL Query:**
```graphql
subscription SwapRequests {
  swapRequests(filter: {
    personId: "789e0123-e89b-12d3-a456-426614174002"
    swapTypes: ["one_to_one"]
    statuses: ["pending", "approved"]
  }) {
    swapId
    requesterId
    targetPersonId
    swapType
    status
    affectedAssignments
    message
    timestamp
  }
}
```

**Filter Options:**
- `personId`: Filter by person (requester or target)
- `swapTypes`: Filter by swap type (one_to_one, absorb)
- `statuses`: Filter by status (pending, approved, executed, rejected)

**Broadcasting from Backend:**
```python
from app.graphql import broadcast_swap_request

await broadcast_swap_request(
    swap_id=swap.id,
    requester_id=requester.id,
    target_person_id=target.id,
    swap_type="one_to_one",
    affected_assignments=[assignment1.id, assignment2.id],
    message="Swap request submitted"
)
```

### 4. Swap Approval Notifications

Subscribe to swap approval events.

**GraphQL Query:**
```graphql
subscription SwapApprovals {
  swapApprovals(filter: {
    personId: "789e0123-e89b-12d3-a456-426614174002"
  }) {
    swapId
    requesterId
    targetPersonId
    swapType
    status
    approvedBy
    affectedAssignments
    message
    timestamp
  }
}
```

**Broadcasting from Backend:**
```python
from app.graphql import broadcast_swap_approval

await broadcast_swap_approval(
    swap_id=swap.id,
    requester_id=requester.id,
    target_person_id=target.id,
    swap_type="one_to_one",
    approved_by=current_user.id,
    affected_assignments=[assignment1.id, assignment2.id],
    message="Swap request approved"
)
```

### 5. Conflict Alert Notifications

Subscribe to conflict detection alerts.

**GraphQL Query:**
```graphql
subscription ConflictAlerts {
  conflictAlerts(filter: {
    personId: "101e2345-e89b-12d3-a456-426614174003"
    severities: ["critical", "warning"]
    conflictTypes: ["leave_fmit_overlap", "back_to_back"]
  }) {
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

**Filter Options:**
- `personId`: Filter by affected person
- `severities`: Filter by severity (critical, warning, info)
- `conflictTypes`: Filter by conflict type

**Broadcasting from Backend:**
```python
from app.graphql import broadcast_conflict_alert

await broadcast_conflict_alert(
    person_id=person.id,
    conflict_type="leave_fmit_overlap",
    severity="critical",
    affected_blocks=[block1.id, block2.id],
    conflict_id=conflict.id,
    message="Leave overlaps with FMIT assignment"
)
```

### 6. Resilience Alerts

Subscribe to resilience system alerts (system-wide).

**GraphQL Query:**
```graphql
subscription ResilienceAlerts {
  resilienceAlerts {
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

**Broadcasting from Backend:**
```python
from app.graphql import broadcast_resilience_alert

await broadcast_resilience_alert(
    alert_type="utilization_high",
    severity="orange",
    current_utilization=0.82,
    defense_level="DEFENSE_LEVEL_2",
    affected_persons=[person1.id, person2.id],
    message="System utilization approaching critical threshold",
    recommendations=[
        "Consider load shedding",
        "Activate fallback schedule"
    ]
)
```

### 7. User Presence Tracking

Subscribe to user online/offline status updates.

**GraphQL Query:**
```graphql
subscription UserPresence {
  userPresence {
    userId
    status
    lastSeen
    activePage
  }
}
```

**Note:** User presence is automatically published when a user connects or disconnects from the subscription.

### 8. Heartbeat (Keep-Alive)

Maintain connection with periodic heartbeat messages.

**GraphQL Query:**
```graphql
subscription Heartbeat {
  heartbeat(intervalSeconds: 30) {
    timestamp
    serverTime
    connectionId
  }
}
```

**Parameters:**
- `intervalSeconds`: Heartbeat interval (default: 30 seconds)

## Client Integration

### JavaScript/TypeScript Example

```typescript
import { createClient } from 'graphql-ws';

const client = createClient({
  url: 'ws://localhost:8000/graphql',
  connectionParams: {
    token: 'your-jwt-token',
  },
});

// Subscribe to schedule updates
const unsubscribe = client.subscribe(
  {
    query: `
      subscription {
        scheduleUpdates {
          scheduleId
          updateType
          message
          timestamp
        }
      }
    `,
  },
  {
    next: (data) => {
      console.log('Schedule update:', data);
    },
    error: (error) => {
      console.error('Subscription error:', error);
    },
    complete: () => {
      console.log('Subscription completed');
    },
  }
);

// Unsubscribe when done
// unsubscribe();
```

### Python Example (for testing)

```python
import asyncio
import json
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport

async def main():
    transport = WebsocketsTransport(
        url="ws://localhost:8000/graphql",
        headers={
            "Authorization": "Bearer your-jwt-token"
        }
    )

    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        subscription = gql("""
            subscription {
                scheduleUpdates {
                    scheduleId
                    updateType
                    message
                    timestamp
                }
            }
        """)

        async for result in session.subscribe(subscription):
            print(f"Received: {result}")

asyncio.run(main())
```

## Authentication

Subscriptions require authentication via JWT token. The token can be provided in:

1. **WebSocket connection params** (recommended):
   ```javascript
   connectionParams: {
     token: 'your-jwt-token'
   }
   ```

2. **Query parameter** (fallback):
   ```
   ws://localhost:8000/graphql?token=your-jwt-token
   ```

## Role-Based Access Control

Subscriptions automatically filter data based on user roles:

- **Admin/Coordinator**: Can subscribe to all updates
- **Faculty**: Can subscribe to updates affecting them
- **Resident**: Can subscribe to updates affecting them
- **Clinical Staff**: Limited to relevant updates

Filtering is handled automatically based on the authenticated user context.

## Redis Configuration

The subscription system uses Redis pub/sub for message broadcasting.

**Environment Variables:**
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password  # Optional
```

**Redis Channels:**
- `graphql:schedule:updates` - Schedule updates
- `graphql:assignment:updates` - Assignment updates
- `graphql:swap:requests` - Swap requests
- `graphql:swap:approvals` - Swap approvals
- `graphql:conflict:alerts` - Conflict alerts
- `graphql:resilience:alerts` - Resilience alerts
- `graphql:user:presence` - User presence
- `graphql:heartbeat` - Heartbeat messages

## Performance Considerations

### Connection Limits

- Maximum concurrent connections: Limited by server resources
- Recommended: Use connection pooling on the client
- Consider load balancing for high-traffic scenarios

### Message Filtering

- Filters are applied server-side to reduce bandwidth
- Use specific filters to minimize unnecessary data transfer
- Person-specific subscriptions are more efficient than global subscriptions

### Redis Pub/Sub

- Redis pub/sub is fire-and-forget (no message persistence)
- Messages are only delivered to currently connected subscribers
- Consider message queueing for critical notifications

### Heartbeat

- Default heartbeat interval: 30 seconds
- Adjust based on network conditions and timeout requirements
- Too frequent = unnecessary bandwidth; too infrequent = delayed disconnect detection

## Error Handling

### Connection Errors

```typescript
client.on('error', (error) => {
  console.error('WebSocket error:', error);
  // Implement reconnection logic
});
```

### Subscription Errors

```typescript
{
  error: (error) => {
    if (error.message.includes('unauthorized')) {
      // Token expired, refresh and reconnect
    } else if (error.message.includes('network')) {
      // Network issue, retry with backoff
    }
  }
}
```

### Reconnection Strategy

```typescript
let retries = 0;
const maxRetries = 5;

function connect() {
  const client = createClient({
    url: 'ws://localhost:8000/graphql',
    retryAttempts: maxRetries,
    on: {
      connected: () => {
        retries = 0;
        console.log('Connected');
      },
      closed: () => {
        if (retries < maxRetries) {
          retries++;
          setTimeout(() => connect(), Math.pow(2, retries) * 1000);
        }
      },
    },
  });
}
```

## Testing

### Manual Testing with GraphQL Playground

1. Navigate to `http://localhost:8000/graphql`
2. Click "Query Variables" tab
3. Add authentication header:
   ```json
   {
     "Authorization": "Bearer your-jwt-token"
   }
   ```
4. Run subscription query in the left panel
5. Trigger events from another tab or API client
6. Watch updates appear in real-time

### Automated Testing

```python
import pytest
from app.graphql import broadcast_schedule_update

@pytest.mark.asyncio
async def test_schedule_update_subscription():
    """Test schedule update subscription receives broadcasts."""
    # Set up subscription listener
    # Broadcast update
    await broadcast_schedule_update(
        schedule_id=test_schedule_id,
        update_type="generated",
        message="Test update"
    )
    # Assert subscription received the update
```

## Troubleshooting

### Issue: Subscriptions not receiving updates

**Causes:**
- Redis connection issues
- Incorrect channel names
- Token authentication failure
- Firewall blocking WebSocket connections

**Solutions:**
- Check Redis connection: `redis-cli ping`
- Verify channel names in logs
- Validate JWT token
- Check WebSocket proxy configuration

### Issue: High memory usage

**Causes:**
- Too many concurrent subscriptions
- Memory leak in subscription handler
- Large message payloads

**Solutions:**
- Limit concurrent connections per user
- Use pagination for large result sets
- Implement connection lifecycle cleanup
- Monitor with Redis memory stats

### Issue: Delayed messages

**Causes:**
- Redis pub/sub backlog
- Network latency
- Server overload

**Solutions:**
- Scale Redis (use Redis Cluster)
- Optimize message size
- Use CDN for WebSocket connections
- Horizontal scaling with load balancer

## Best Practices

1. **Use specific filters**: Filter subscriptions to reduce bandwidth
2. **Implement heartbeat**: Use heartbeat subscription for connection monitoring
3. **Handle reconnection**: Implement exponential backoff for reconnects
4. **Validate tokens**: Refresh JWT tokens before expiration
5. **Clean up**: Unsubscribe when components unmount
6. **Monitor connections**: Track active subscription count
7. **Graceful degradation**: Fall back to polling if WebSocket unavailable
8. **Security**: Validate all user input in filters
9. **Rate limiting**: Implement per-user subscription limits
10. **Logging**: Log subscription lifecycle events for debugging

## Future Enhancements

- [ ] Message persistence with Redis Streams
- [ ] Subscription batching to reduce message frequency
- [ ] Compression for large payloads
- [ ] Subscription analytics and monitoring dashboard
- [ ] Client-side caching of subscription data
- [ ] Subscription multiplexing (multiple subscriptions over one connection)
- [ ] Binary protocol support (e.g., Protocol Buffers)

## References

- [Strawberry GraphQL Subscriptions](https://strawberry.rocks/docs/types/subscriptions)
- [GraphQL Subscriptions Spec](https://github.com/graphql/graphql-spec/blob/main/spec/Section%206%20-%20Execution.md#subscription)
- [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/)
- [GraphQL over WebSocket Protocol](https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md)
