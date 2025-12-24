# Claude Chat Bridge

> **Added:** 2025-12-24
> **Purpose:** WebSocket-based bridge between admin interface and Claude API with tool execution

## Overview

The Claude Chat Bridge provides a real-time streaming interface for administrators to interact with Claude for scheduling operations. It bridges Claude's tool calls to backend services while maintaining security and audit trails.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE CHAT BRIDGE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (React)                                              │
│   ┌─────────────────────────────────────┐                       │
│   │  ClaudeCodeChat Component           │                       │
│   │  - useClaudeChat hook               │                       │
│   │  - Streaming message display        │                       │
│   │  - Tool call visualization          │                       │
│   └────────────────┬────────────────────┘                       │
│                    │ WebSocket                                  │
│                    ▼                                            │
│   Backend (FastAPI)                                             │
│   ┌─────────────────────────────────────┐                       │
│   │  /api/claude-chat/ws                │                       │
│   │  - JWT Authentication               │                       │
│   │  - Session Management               │                       │
│   │  - Stream Interruption              │                       │
│   └────────────────┬────────────────────┘                       │
│                    │                                            │
│                    ▼                                            │
│   Claude API                                                    │
│   ┌─────────────────────────────────────┐                       │
│   │  Anthropic Messages API             │                       │
│   │  - Streaming responses              │                       │
│   │  - Tool use (function calling)      │                       │
│   └────────────────┬────────────────────┘                       │
│                    │                                            │
│                    ▼                                            │
│   Backend Services                                              │
│   ┌─────────────────────────────────────┐                       │
│   │  - ConstraintService                │                       │
│   │  - SwapAutoMatcher                  │                       │
│   │  - ContingencyAnalyzer              │                       │
│   │  - ConflictAnalyzer                 │                       │
│   └─────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## WebSocket Protocol

### Connection

```javascript
// Connect with JWT authentication
const ws = new WebSocket(
  `ws://localhost:8000/api/claude-chat/ws?token=${jwt}&session_id=${optional_session_id}`
);
```

### Message Types

#### Client → Server

| Type | Description | Payload |
|------|-------------|---------|
| `user_message` | Send message to Claude | `{"type": "user_message", "content": "..."}` |
| `interrupt` | Stop generation | `{"type": "interrupt"}` |
| `get_history` | Retrieve session history | `{"type": "get_history"}` |

#### Server → Client

| Type | Description | Payload |
|------|-------------|---------|
| `connected` | Connection established | `{"type": "connected", "session_id": "...", "history_count": N}` |
| `token` | Streaming token | `{"type": "token", "content": "..."}` |
| `tool_call_start` | Tool execution starting | `{"type": "tool_call_start", "name": "...", "id": "..."}` |
| `tool_call` | Tool being executed | `{"type": "tool_call", "name": "...", "input": {...}, "id": "..."}` |
| `tool_result` | Tool execution result | `{"type": "tool_result", "id": "...", "result": {...}}` |
| `complete` | Response complete | `{"type": "complete", "usage": {"input_tokens": N, "output_tokens": N}}` |
| `interrupted` | Generation stopped | `{"type": "interrupted", "message": "...", "partial_response": bool}` |
| `error` | Error occurred | `{"type": "error", "message": "..."}` |
| `history` | Session history | `{"type": "history", "messages": [...]}` |

## Available Tools

The bridge exposes 5 scheduling tools to Claude:

### 1. `validate_schedule`

Validates a schedule against ACGME compliance rules.

**Input:**
```json
{
  "schedule_id": "uuid-or-identifier",
  "start_date": "2025-01-01",  // optional
  "end_date": "2025-01-31"     // optional
}
```

**Backend Service:** `ConstraintService.validate_schedule()`

### 2. `analyze_swap_candidates`

Finds compatible swap candidates for a faculty member.

**Input:**
```json
{
  "person_id": "faculty-uuid",
  "max_candidates": 10
}
```

**Backend Service:** `SwapAutoMatcher.suggest_proactive_swaps()`

### 3. `run_contingency_analysis`

Performs N-1 vulnerability analysis on the schedule.

**Input:**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

**Backend Service:** `ContingencyAnalyzer.analyze_n1()`

### 4. `detect_conflicts`

Detects scheduling conflicts with resolution suggestions.

**Input:**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

**Backend Service:** `ConflictAnalyzer.analyze_schedule()`

### 5. `health_check`

Checks system health status.

**Input:** None

**Returns:** Database connectivity, API status

## Stream Interruption

The bridge supports graceful stream interruption:

### How It Works

1. **Interrupt Event**: Each session has an `asyncio.Event` for interruption signaling
2. **Active Stream Tracking**: Running streams are tracked in `_active_streams` dict
3. **Interruption Flow**:
   - Client sends `{"type": "interrupt"}`
   - Server sets interrupt event and cancels task
   - Partial response is preserved in session history
   - Client receives `{"type": "interrupted", ...}`

### Implementation Details

```python
# Interrupt handling in WebSocket handler
elif msg_type == "interrupt":
    # Set the interrupt flag
    interrupt_event.set()

    # Cancel the task if running
    if session.session_id in _active_streams:
        task = _active_streams[session.session_id]
        if not task.done():
            task.cancel()
```

```python
# Interrupt check in stream loop
async for event in stream:
    if interrupt_event and interrupt_event.is_set():
        interrupted = True
        break
    # ... process event
```

## Security

### Authentication

- **JWT Required**: WebSocket connection requires valid JWT token
- **Role Enforcement**: Only `ADMIN` and `COORDINATOR` roles can access
- **Token Validation**: Uses `get_user_from_token()` for verification

### Output Sanitization

All tool results are sanitized to prevent PII leakage:

```python
# Faculty references are anonymized
{
    "faculty_ref": f"entity-{str(v.faculty_id)[:8]}",  # Not full UUID
    "severity": v.severity,
    # No names, only role identifiers
}
```

### Error Handling

Errors are sanitized to prevent information disclosure:

```python
except Exception as e:
    logger.exception(f"Tool execution failed: {tool_name}")
    return {"error": f"Tool execution failed: {type(e).__name__}"}
```

## Session Management

### In-Memory Sessions

Sessions are stored in memory (could be migrated to Redis for multi-instance):

```python
_sessions: dict[str, ChatSession] = {}
_connections: dict[str, WebSocket] = {}
_interrupt_flags: dict[str, asyncio.Event] = {}
_active_streams: dict[str, asyncio.Task] = {}
```

### Session Lifecycle

1. **Creation**: On WebSocket connect, session created/resumed
2. **Activity**: Messages stored in session history
3. **Cleanup**: On disconnect, connections and streams cleaned up

### REST Endpoints

For non-WebSocket operations:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/claude-chat/sessions` | GET | List user's sessions |
| `/api/claude-chat/sessions/{id}` | GET | Get session history |
| `/api/claude-chat/sessions/{id}` | DELETE | Delete session |

## Frontend Integration

### React Hook

```typescript
// hooks/useClaudeChat.ts
const {
  messages,
  isStreaming,
  sendMessage,
  interrupt,
  error
} = useClaudeChat(sessionId);
```

### Component

```tsx
// components/admin/ClaudeCodeChat.tsx
<ClaudeCodeChat
  sessionId={sessionId}
  onArtifact={handleArtifact}
/>
```

### Artifact Types

The chat supports artifact generation:

| Type | Description |
|------|-------------|
| `schedule` | Generated schedule data |
| `analysis` | Analysis results (conflicts, compliance) |
| `report` | Formatted reports |
| `configuration` | System configuration |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |

### System Prompt

The bridge uses a scheduling-focused system prompt:

```
You are a scheduling assistant for a medical residency program.
You help administrators manage schedules, check ACGME compliance,
find swap candidates, and analyze system health.

You have access to tools that interact with the scheduling system...
```

## Troubleshooting

### Connection Issues

**Error:** `4001 - Invalid token`
- Ensure JWT token is valid and not expired
- Check token is passed correctly in query string

**Error:** `4003 - Admin access required`
- User must have ADMIN or COORDINATOR role
- Check user permissions in database

### Streaming Issues

**Issue:** Tokens not appearing
- Check `ANTHROPIC_API_KEY` is configured
- Verify network connectivity to Anthropic API

**Issue:** Interrupt not working
- Ensure WebSocket is still connected
- Check browser console for errors

### Tool Execution Failures

**Issue:** Tools returning errors
- Check backend services are running
- Verify database connectivity
- Check logs for detailed error messages

## Related Documentation

- [MCP Admin Guide](../admin-manual/mcp-admin-guide.md) - **Step-by-step admin workflows for using MCP via chat**
- [MCP Setup](./MCP_SETUP.md) - MCP server configuration
- [MCP Tools Reference](../../mcp-server/docs/MCP_TOOLS_REFERENCE.md) - Full tool documentation
- [AI Rules of Engagement](./AI_RULES_OF_ENGAGEMENT.md) - AI agent policies
- [AI Interface Guide](../admin-manual/ai-interface-guide.md) - Web vs CLI comparison

## Frontend Components

### Chat Session Persistence

The chat interface persists sessions to localStorage:

- **Sessions survive page refresh** - Messages are restored automatically
- **Last 20 sessions retained** - Older sessions are pruned
- **Auto-save on message** - Every message triggers persistence

### MCP Capabilities Panel

A companion panel displays all 30+ MCP tools organized by category:

| Category | Tools | Purpose |
|----------|-------|---------|
| Scheduling & Compliance | 4 | validate_schedule, detect_conflicts, etc. |
| Resilience Framework | 8 | utilization, defense levels, N-1/N-2 |
| Background Tasks | 4 | async task management |
| Deployment & CI/CD | 7 | validate, scan, promote, rollback |
| Advanced Analytics | 5 | Le Chatelier, cognitive load, stigmergy |

Features:
- **Searchable** - Find tools by name or description
- **Click-to-try** - Example prompts for each tool
- **Collapsible categories** - Focus on relevant tools
