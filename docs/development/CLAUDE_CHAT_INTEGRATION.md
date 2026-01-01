# Claude Chat Integration Plan

> **Purpose:** Enable clinician administrators to interact with Claude Code via a web chat interface
> **Status:** Planning/Initial Implementation
> **Created:** 2025-12-24

---

## Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN CLAUDE CHAT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Admin Frontend                    Terminal (optional)         │
│   ┌─────────────────┐              ┌─────────────────┐         │
│   │ Chat Interface  │              │ Claude Code CLI │         │
│   │ (React)         │              │ (parallel work) │         │
│   └────────┬────────┘              └────────┬────────┘         │
│            │ WebSocket                      │                   │
│            ▼                                ▼                   │
│   ┌─────────────────────────────────────────────────────┐      │
│   │           Claude Chat Bridge (FastAPI)               │      │
│   │  - Streams Claude responses                          │      │
│   │  - Executes MCP tools                                │      │
│   │  - Maintains session history                         │      │
│   └─────────────────────────────────────────────────────┘      │
│            │                                │                   │
│            ▼                                ▼                   │
│   ┌─────────────────┐              ┌─────────────────┐         │
│   │ Anthropic API   │              │ Backend Services │         │
│   │ (Claude)        │              │ (Scheduler, etc) │         │
│   └─────────────────┘              └─────────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Already Exists

Your codebase already has **90% of the infrastructure** needed:

| Component | Status | Location |
|-----------|--------|----------|
| WebSocket Manager | Ready | `backend/app/websocket/manager.py` |
| Event System | Ready | `backend/app/websocket/events.py` |
| Notification Service | Ready | `backend/app/notifications/service.py` |
| Admin Pages | Ready | `frontend/src/app/admin/` |
| JWT Authentication | Ready | `backend/app/api/deps.py` |
| MCP Tools | Ready | `mcp-server/src/scheduler_mcp/tools.py` |
| Role-based Access | Ready | Existing RBAC |

---

## Implementation Phases

### Phase 1: Backend Bridge (DONE)

**File:** `backend/app/api/routes/claude_chat.py`

Core functionality:
- [x] WebSocket endpoint at `/api/claude-chat/ws`
- [x] JWT authentication via query param
- [x] Admin role check
- [x] Session management (in-memory)
- [x] Claude API streaming integration
- [x] Tool definitions matching MCP tools
- [x] Tool execution bridge to services
- [x] Message protocol (token, tool_call, complete, error)

### Phase 2: Router Registration (TODO)

Add to `backend/app/main.py`:

```python
from app.api.routes import claude_chat

# In the router registration section:
app.include_router(claude_chat.router, prefix="/api")
```

Add to `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Claude Chat Integration
    ANTHROPIC_API_KEY: str = ""  # Required for chat
```

### Phase 3: Frontend Chat Component (TODO)

**File:** `frontend/src/components/admin/ClaudeChat.tsx`

```tsx
// Minimal example - full implementation in separate file
'use client';

import { useEffect, useRef, useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export function ClaudeChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const streamingContentRef = useRef('');

  useEffect(() => {
    // Get JWT from your auth system
    const token = getAuthToken();

    // Connect to WebSocket
    const ws = new WebSocket(
      `ws://localhost:8000/api/claude-chat/ws?token=${token}`
    );

    ws.onopen = () => {
      console.log('Connected to Claude Chat');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'connected':
          console.log('Session:', data.session_id);
          break;

        case 'token':
          // Append streaming token to current message
          streamingContentRef.current += data.content;
          updateStreamingMessage(streamingContentRef.current);
          break;

        case 'tool_call':
          // Show tool call indicator
          addToolCallToMessage(data.name, data.input);
          break;

        case 'tool_result':
          // Update tool call with result
          updateToolResult(data.id, data.result);
          break;

        case 'complete':
          // Finalize message
          setIsStreaming(false);
          streamingContentRef.current = '';
          break;

        case 'error':
          console.error('Chat error:', data.message);
          setIsStreaming(false);
          break;
      }
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current) return;

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: input }]);

    // Start streaming indicator
    setIsStreaming(true);
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    // Send to backend
    wsRef.current.send(JSON.stringify({
      type: 'user_message',
      content: input,
    }));

    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} isStreaming={isStreaming && i === messages.length - 1} />
        ))}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about schedules, compliance, swaps..."
            className="flex-1 px-4 py-2 border rounded-lg"
            disabled={isStreaming}
          />
          <button
            onClick={sendMessage}
            disabled={isStreaming || !input.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Phase 4: Admin Page Integration (TODO)

**File:** `frontend/src/app/admin/claude-chat/page.tsx`

```tsx
import { ClaudeChat } from '@/components/admin/ClaudeChat';

export default function ClaudeChatPage() {
  return (
    <div className="h-screen flex flex-col">
      <header className="bg-white border-b px-4 py-3">
        <h1 className="text-xl font-semibold">Claude Scheduling Assistant</h1>
        <p className="text-sm text-gray-500">
          Ask about schedules, compliance, swaps, and more
        </p>
      </header>
      <main className="flex-1">
        <ClaudeChat />
      </main>
    </div>
  );
}
```

---

## Message Protocol

### Client -> Server

| Type | Fields | Description |
|------|--------|-------------|
| `user_message` | `content: string` | User's chat message |
| `interrupt` | - | Stop current generation |
| `get_history` | - | Request session history |

### Server -> Client

| Type | Fields | Description |
|------|--------|-------------|
| `connected` | `session_id`, `history_count` | Connection established |
| `token` | `content: string` | Streaming text token |
| `tool_call_start` | `name`, `id` | Tool execution starting |
| `tool_call` | `name`, `input`, `id` | Full tool call info |
| `tool_result` | `id`, `result` | Tool execution result |
| `complete` | `usage: {input_tokens, output_tokens}` | Response finished |
| `error` | `message: string` | Error occurred |
| `interrupted` | `message` | Generation stopped |
| `history` | `messages: Message[]` | Session history |

---

## Tool Integration

The chat bridge has access to these scheduler tools:

| Tool | Purpose | Read/Write |
|------|---------|------------|
| `validate_schedule` | Check ACGME compliance | Read |
| `analyze_swap_candidates` | Find swap matches | Read |
| `run_contingency_analysis` | N-1/N-2 vulnerability | Read |
| `detect_conflicts` | Find scheduling conflicts | Read |
| `health_check` | System status | Read |

**Note:** Currently all tools are read-only. Write operations (generate_schedule, execute_swap) should require explicit confirmation flow before adding.

---

## Security Considerations

### Authentication
- JWT token required (query param for WebSocket)
- Token validated against database
- Session tied to user ID

### Authorization
- Only ADMIN and COORDINATOR roles can access
- Tool execution respects existing RBAC

### Rate Limiting

**Implementation:** Use existing `RateLimiter` infrastructure from `backend/app/core/rate_limit.py`

```python
from app.core.rate_limit import create_rate_limit_dependency

# Add to claude_chat.py route
rate_limit_chat = create_rate_limit_dependency(
    max_requests=10,    # 10 messages per minute
    window_seconds=60,
    key_prefix="claude_chat"
)

rate_limit_chat_hourly = create_rate_limit_dependency(
    max_requests=100,   # 100 messages per hour
    window_seconds=3600,
    key_prefix="claude_chat_hourly"
)

@router.websocket("/api/claude-chat/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    _rate_limit: None = Depends(rate_limit_chat),
    _rate_limit_hourly: None = Depends(rate_limit_chat_hourly),
):
    # Connection established - rate limits verified
    ...
```

**Configuration:**
- Uses Redis sliding window algorithm (existing infrastructure)
- Per-user rate limiting (keyed by user_id, not IP)
- Returns 429 with Retry-After header when exceeded
- Limits: 10 msg/min, 100 msg/hour (prevents runaway costs)

**Testing:**
```bash
pytest tests/api/test_claude_chat_rate_limit.py -v
```

### Audit Trail

**Implementation:** Use existing `NotificationService` for structured logging

```python
from app.notifications.service import NotificationService
from app.models.notification import Notification, NotificationType
from datetime import datetime

async def log_chat_interaction(
    db: Session,
    user_id: str,
    message: str,
    response: str,
    tool_calls: list[dict],
    session_id: str,
):
    """
    Log chat interaction to notification system for audit trail.

    Args:
        db: Database session
        user_id: ID of user who sent the message
        message: User's input message
        response: Claude's response
        tool_calls: List of tools executed during response
        session_id: WebSocket session identifier
    """
    notification_service = NotificationService(db)

    # Create audit record as notification
    await notification_service.send_notification(
        recipient_id=user_id,
        notification_type=NotificationType.SYSTEM_AUDIT,  # New type
        data={
            "event_type": "claude_chat_interaction",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": message,
            "assistant_response": response[:500],  # Truncate for storage
            "tool_calls": [
                {
                    "name": call["name"],
                    "input_summary": str(call["input"])[:200],
                    "execution_time_ms": call.get("execution_time_ms", 0),
                }
                for call in tool_calls
            ],
            "token_usage": {
                "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response.get("usage", {}).get("output_tokens", 0),
            },
        },
        channel="audit_log",  # New channel - write-only to database
    )
```

**Database Schema Addition:**

Add new notification type to `backend/app/notifications/notification_types.py`:

```python
class NotificationType(str, Enum):
    # ... existing types ...
    SYSTEM_AUDIT = "system_audit"  # For audit trail events
```

**Storage Details:**
- Persists to `notifications` table (existing infrastructure)
- Includes: timestamp, user_id, message, tool calls, token usage
- Retention: Configurable (default 90 days for audit compliance)
- Queryable via admin dashboard: `/admin/audit-trail`

**Testing:**
```bash
pytest tests/api/test_claude_chat_audit.py -v
```

**Compliance Notes:**
- Logs stored in database (not just application logs)
- Tamper-evident (notification records are immutable)
- Supports HIPAA audit trail requirements
- Can export for compliance reporting

### API Key Protection
- ANTHROPIC_API_KEY stored in .env
- Never exposed to frontend
- Validated on startup

---

## Deployment Checklist

### Environment Variables

```bash
# Add to .env
ANTHROPIC_API_KEY=sk-ant-api03-...  # Get from console.anthropic.com
```

### Backend Changes

1. [ ] **Add `anthropic` to requirements.txt**
   ```bash
   cd backend
   # Add to requirements.txt:
   anthropic>=0.18.0  # For Claude API integration
   ```

2. [ ] **Register router in main.py**
   ```python
   # In backend/app/main.py
   from app.api.routes import claude_chat

   # Add after other router registrations (around line 80):
   app.include_router(
       claude_chat.router,
       prefix="/api",
       tags=["claude-chat"]
   )
   ```

3. [ ] **Add ANTHROPIC_API_KEY to config.py**
   ```python
   # In backend/app/core/config.py, add to Settings class:

   # Claude Chat Integration
   ANTHROPIC_API_KEY: str = Field(
       default="",
       description="Anthropic API key for Claude chat (get from console.anthropic.com)"
   )

   @validator("ANTHROPIC_API_KEY")
   def validate_anthropic_key(cls, v: str) -> str:
       """Validate ANTHROPIC_API_KEY if chat feature is enabled."""
       if v and len(v) < 32:
           raise ValueError("ANTHROPIC_API_KEY must be at least 32 characters")
       return v
   ```

   Update `.env.example`:
   ```bash
   # Claude Chat Integration (Optional - for admin chat interface)
   ANTHROPIC_API_KEY=sk-ant-api03-...  # Get from console.anthropic.com
   ```

4. [ ] **Run tests**
   ```bash
   cd backend
   pytest tests/api/test_claude_chat.py -v
   pytest tests/api/test_claude_chat_rate_limit.py -v
   pytest tests/api/test_claude_chat_audit.py -v

   # Verify WebSocket connection
   python -m pytest tests/websocket/test_claude_chat_ws.py -v
   ```

### Frontend Changes

1. [ ] **Create ClaudeChat component**
   ```bash
   cd frontend/src/components/admin
   # Create ClaudeChat.tsx (see Phase 3 example above)
   # Create MessageBubble.tsx for message rendering
   # Create ToolCallIndicator.tsx for showing tool executions
   ```

   **Files to create:**
   - `frontend/src/components/admin/ClaudeChat.tsx` (main component)
   - `frontend/src/components/admin/MessageBubble.tsx` (message display)
   - `frontend/src/components/admin/ToolCallIndicator.tsx` (tool visualization)
   - `frontend/src/hooks/useClaudeChat.ts` (WebSocket logic)

2. [ ] **Create admin/claude-chat page**
   ```bash
   cd frontend/src/app/admin
   mkdir claude-chat
   # Create page.tsx (see Phase 4 example above)
   ```

   **File:** `frontend/src/app/admin/claude-chat/page.tsx`
   ```tsx
   import { ClaudeChat } from '@/components/admin/ClaudeChat';
   export default function ClaudeChatPage() { /* ... */ }
   ```

3. [ ] **Add navigation link to admin sidebar**
   ```tsx
   // In frontend/src/components/admin/Sidebar.tsx or AdminLayout.tsx

   const adminNavItems = [
     // ... existing items ...
     {
       name: 'Claude Chat',
       href: '/admin/claude-chat',
       icon: ChatBubbleIcon,  // or MessageSquare from lucide-react
       description: 'AI Scheduling Assistant',
     },
   ];
   ```

4. [ ] **Test WebSocket connection**
   ```bash
   # Start backend
   cd backend && uvicorn app.main:app --reload

   # Start frontend
   cd frontend && npm run dev

   # Manual test with wscat (optional)
   npm install -g wscat
   wscat -c "ws://localhost:8000/api/claude-chat/ws?token=YOUR_JWT_TOKEN"

   # Send test message:
   {"type": "user_message", "content": "Hello Claude"}

   # Should receive streaming responses
   ```

### Testing

```bash
# Backend
pytest tests/api/test_claude_chat.py -v

# Frontend
npm run test -- --grep "ClaudeChat"

# Manual WebSocket test
wscat -c "ws://localhost:8000/api/claude-chat/ws?token=YOUR_JWT"
```

---

## One-Page Setup for Clinician Admins

```
╔══════════════════════════════════════════════════════════════╗
║              CLAUDE SCHEDULING ASSISTANT SETUP                ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  1. LOG IN to the admin panel (admin.example.com)            ║
║                                                               ║
║  2. NAVIGATE to "Claude Chat" in the sidebar                 ║
║                                                               ║
║  3. TYPE naturally:                                           ║
║     - "Check compliance for next month"                       ║
║     - "Find swap candidates for Dr. Smith"                    ║
║     - "Show vulnerable slots this week"                       ║
║     - "Are there any scheduling conflicts?"                   ║
║                                                               ║
║  4. REVIEW the results before taking action                   ║
║                                                               ║
║  That's it. The system handles the rest.                      ║
║                                                               ║
║  ─────────────────────────────────────────────────────────── ║
║                                                               ║
║  TIPS:                                                        ║
║  • Be specific: "Check Block 5 coverage" vs "Check coverage" ║
║  • Ask follow-ups: "Why is that a violation?"                ║
║  • Request summaries: "Summarize the compliance status"       ║
║                                                               ║
║  NEED HELP?                                                   ║
║  Contact IT or check docs/admin-manual/claude-chat-guide.md  ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Future Enhancements

### Phase 5: Write Operations (Requires Confirmation)
- Generate schedule with preview + confirm
- Execute swaps with rollback capability
- Apply bulk changes with audit

### Phase 6: Multi-User Collaboration
- Broadcast tool results to all admin sessions
- Show "Admin X is working on..." indicators
- Conflict resolution for concurrent edits

### Phase 7: CLI Integration
- Bridge WebSocket to Claude Code CLI
- Allow terminal + web parallel work
- Unified session history

---

## References

- **claude-agent-server**: https://github.com/dzhng/claude-agent-server
- **Anthropic Tool Use Cookbook**: https://docs.anthropic.com/claude/docs/tool-use
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/
- **Existing WebSocket Infra**: `backend/app/websocket/`

---

*This document is the integration plan for Claude Chat. Update as implementation progresses.*
