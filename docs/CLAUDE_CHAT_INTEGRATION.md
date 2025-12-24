# Claude Code Chat Integration Guide

This guide explains how to integrate the Claude Code Chat interface into your admin panel for real-time agentic task execution.

## Overview

The Claude Chat system allows admins to:
- **Generate schedules** using natural language
- **Analyze compliance violations** interactively
- **Optimize fairness** metrics
- **Export reports** on demand
- **Execute custom scheduling tasks** with live streaming feedback

## Architecture

```
Frontend (React)                Backend (FastAPI)           Claude API
┌─────────────────┐            ┌──────────────────┐         ┌────────┐
│ ClaudeCodeChat  │ ─stream──> │ /api/claude/chat/│ ─────> │Claude  │
│   Component     │ <──SSE──   │  stream          │ <─────  │  API   │
│                 │            │                  │         └────────┘
│ useClaudeChat   │            │ ClaudeService    │
│     hook        │            │                  │
└─────────────────┘            └──────────────────┘
```

## Setup Instructions

### 1. Environment Configuration

Add to your `.env` file:

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
```

### 2. Backend Setup

#### Install Dependencies

```bash
pip install anthropic
```

#### Register Routes

In `backend/app/main.py`, add the claude_chat router:

```python
from app.api.routes import claude_chat

app.include_router(claude_chat.router)
```

### 3. Frontend Setup

#### Install Dependencies

```bash
npm install uuid
```

#### Add Context to App

Wrap your admin panel with `ClaudeChatProvider` in your main app component:

```tsx
import { ClaudeChatProvider } from './contexts/ClaudeChatContext';

function App() {
  return (
    <ClaudeChatProvider>
      {/* Your admin routes */}
    </ClaudeChatProvider>
  );
}
```

#### Add Chat Component

In your admin dashboard:

```tsx
import ClaudeCodeChat from './components/admin/ClaudeCodeChat';

function AdminDashboard() {
  const { user, program } = useAuth();

  return (
    <div className="dashboard">
      <ClaudeCodeChat
        programId={program.id}
        adminId={user.id}
        onTaskComplete={(artifact) => {
          // Handle completed task (e.g., apply schedule)
          console.log('Task completed:', artifact);
        }}
      />
    </div>
  );
}
```

## Usage Examples

### 1. Generate Schedule

**User Input:**
```
"Generate a 4-week rotation schedule for our Family Medicine program with 12 residents. 
Avoid Friday nights and ensure each resident gets 2 weeks off."
```

**Response:**
- Real-time progress updates
- Generated schedule in JSON format
- Compliance check results
- Downloadable artifact

### 2. Check Compliance

**User Input:**
```
"Analyze the current schedule for ACGME violations. Flag any residents exceeding 80 hours/week."
```

**Response:**
- Violation report with specific residents and weeks
- Remediation suggestions
- Updated schedule with violations fixed

### 3. Fairness Analysis

**User Input:**
```
"How fairly are night shifts distributed across residents? Provide recommendations."
```

**Response:**
- Fairness metrics and variance analysis
- Residents with inequitable distributions
- Suggested redistribution
- Updated schedule with improved fairness

### 4. Export Report

**User Input:**
```
"Generate a comprehensive report on the current schedule including metrics, compliance status, and recommendations."
```

**Response:**
- Professional formatted report
- Key metrics and statistics
- Compliance status summary
- Actionable recommendations
- Downloadable PDF/JSON

## API Endpoints

### POST `/api/claude/chat`

Non-streaming request (full response at once).

**Request:**
```json
{
  "action": "generate_schedule",
  "context": {
    "program_id": "prog_123",
    "admin_id": "admin_456",
    "session_id": "sess_789",
    "constraints": {
      "max_hours_per_week": 80,
      "max_consecutive_days": 7,
      "min_rest_days": 1
    },
    "residents": [
      {
        "id": "res_1",
        "name": "Dr. Smith",
        "restrictions": ["No Friday nights"]
      }
    ]
  },
  "user_query": "Generate the Q1 schedule"
}
```

**Response:**
```json
{
  "success": true,
  "result": { /* Schedule data */ },
  "artifacts": []
}
```

### POST `/api/claude/chat/stream`

Streaming request with Server-Sent Events (SSE).

**Same request format as above, but returns SSE stream:**

```
data: {"type": "text", "content": "Generating schedule..."}
data: {"type": "status", "content": "Processing residents"}
data: {"type": "code", "content": "...", "metadata": {...}}
data: {"type": "artifact", "content": "Schedule generated", "metadata": {...}}
data: {"type": "status", "content": "Complete"}
```

## Stream Update Types

The streaming interface sends different update types:

| Type | Content | Use Case |
|------|---------|----------|
| `text` | Narrative response | Display progress/explanation |
| `code` | Code block with language | Display generated code |
| `artifact` | Generated data structure | Handle schedule/report data |
| `status` | Progress indicator | Show task progress |
| `error` | Error message | Handle failures |

## Component API

### useClaudeChat Hook

```tsx
const {
  session,          // Current chat session
  messages,         // All messages in session
  isLoading,        // Is request in progress
  error,            // Current error message
  initializeSession,// Create new session
  sendMessage,      // Send message with streaming
  cancelRequest,    // Abort current request
  clearMessages,    // Clear chat history
  exportSession,    // Export session data
} = useClaudeChat();

// Send message with stream callback
await sendMessage(
  "Generate schedule",
  { /* context */ },
  (update) => {
    // Handle real-time stream updates
    if (update.type === 'artifact') {
      // Process generated artifact
    }
  }
);
```

### ClaudeCodeChat Component

```tsx
<ClaudeCodeChat
  programId="prog_123"    // Required: program ID
  adminId="admin_456"     // Required: admin user ID
  onTaskComplete={         // Optional: callback when task completes
    (artifact) => console.log(artifact)
  }
/>
```

## Error Handling

The system handles various error scenarios:

```tsx
// Network errors
{
  "type": "error",
  "content": "HTTP 500: Internal Server Error"
}

// Validation errors
{
  "type": "error",
  "content": "Invalid schedule context provided"
}

// API rate limits
{
  "type": "error",
  "content": "Rate limit exceeded. Please try again later."
}
```

Errors are caught and:
1. Logged to console
2. Displayed in chat interface
3. Passed to error state
4. Can be handled in `onTaskComplete` callback

## Security Considerations

1. **Authentication**: All requests require valid JWT token
2. **Authorization**: Users can only access their program
3. **Data Privacy**: Sensitive scheduling data never leaves your server
4. **API Keys**: Store ANTHROPIC_API_KEY securely in environment variables
5. **Rate Limiting**: Implement rate limits on `/api/claude/*` endpoints
6. **Input Validation**: All user queries are validated before sending to Claude

## Performance Tips

1. **Streaming**: Always use `/api/claude/chat/stream` for better UX
2. **Cancellation**: Allow users to cancel long-running tasks
3. **Caching**: Cache generated artifacts locally
4. **Pagination**: Limit chat history to last 50 messages
5. **Debouncing**: Debounce input to avoid excessive API calls

## Troubleshooting

### Chat not sending messages
- Check ANTHROPIC_API_KEY is set
- Verify network connection
- Check browser console for errors
- Ensure session is initialized

### Streaming stops
- Check for browser tab inactive state
- Verify streaming endpoint is accessible
- Check for network timeouts
- Review server logs

### Generated schedules are invalid
- Verify context data is complete
- Check constraints are realistic
- Review constraint order (some depend on others)
- Test with simplified constraints first

## Example Implementation

See the [admin dashboard example](../examples/claude-chat-admin.tsx) for a complete working implementation.

## Future Enhancements

- [ ] Voice input for hands-free commands
- [ ] Schedule visualization in real-time
- [ ] Multi-turn conversation with context persistence
- [ ] Integration with calendar systems (Google Calendar, Outlook)
- [ ] Batch processing for multiple programs
- [ ] Machine learning for schedule preferences
- [ ] Advanced fairness algorithms
- [ ] Team collaboration features
