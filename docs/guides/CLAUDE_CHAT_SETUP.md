# Claude Code Chat - Quick Start Setup

## 1. Get Your Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

## 2. Environment Setup

### Backend (.env)

```bash
# Add to your existing .env file:
ANTHROPIC_API_KEY=sk-ant-YOUR_API_KEY_HERE
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Frontend (.env.local)

```bash
REACT_APP_API_URL=http://localhost:8000
```

## 3. Install Dependencies

### Backend

```bash
cd backend
pip install anthropic
```

### Frontend

```bash
cd frontend
npm install uuid
```

## 4. Update Backend Main App

In `backend/app/main.py`, add:

```python
from app.api.routes import claude_chat

# After creating the FastAPI app:
app.include_router(claude_chat.router)
```

## 5. Update Frontend App Entry

In `frontend/src/app.tsx` or your main component, wrap with provider:

```tsx
import { ClaudeChatProvider } from './contexts/ClaudeChatContext';

function App() {
  return (
    <ClaudeChatProvider>
      {/* Your existing app content */}
    </ClaudeChatProvider>
  );
}
```

## 6. Add Chat Component

In your admin dashboard page:

```tsx
import ClaudeCodeChat from './components/admin/ClaudeCodeChat';

function AdminDashboard() {
  return (
    <div>
      <ClaudeCodeChat
        programId="your_program_id"
        adminId="your_admin_id"
      />
    </div>
  );
}
```

## 7. Test the Integration

### Start Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Start Frontend

```bash
cd frontend
npm start
```

### Test in Chat

Try these prompts:

1. **"Generate a 4-week schedule for 12 residents"**
2. **"Check for ACGME violations in the current schedule"**
3. **"Analyze fairness of night shift distribution"**
4. **"Export a compliance report"**

## File Structure Added

```
frontend/
├── src/
│   ├── types/
│   │   └── chat.ts                 # Chat type definitions
│   ├── hooks/
│   │   └── useClaudeChat.ts        # Chat hook with streaming
│   ├── contexts/
│   │   └── ClaudeChatContext.tsx   # Chat context provider
│   └── components/
│       └── admin/
│           ├── ClaudeCodeChat.tsx  # Main chat component
│           └── ClaudeCodeChat.css  # Component styles

backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── claude_chat.py      # API endpoints
│   ├── services/
│   │   └── claude_service.py       # Claude API client
│   └── schemas/
│       └── chat.py                 # Pydantic models

docs/
├── CLAUDE_CHAT_INTEGRATION.md       # Full integration guide

examples/
└── claude-chat-admin.tsx            # Example admin dashboard
```

## Architecture Diagram

```
┌─────────────────────────────────────┐
│   Admin Browser                     │
│  ┌───────────────────────────────┐  │
│  │  ClaudeCodeChat Component     │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Chat Messages Display   │  │  │
│  │  │ Input textarea          │  │  │
│  │  │ Send Button             │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
│              ↓↑ SSE Stream           │
└──────────────┼────────────────────────┘
               │
        [Network/HTTP]
               │
┌──────────────┴────────────────────────┐
│  FastAPI Backend                       │
│  ┌────────────────────────────────┐   │
│  │ /api/claude/chat/stream        │   │
│  ├────────────────────────────────┤   │
│  │ Claude Service                 │   │
│  │ ┌──────────────────────────┐   │   │
│  │ │ Stream Management        │   │   │
│  │ │ Context Building         │   │   │
│  │ │ Prompt Engineering       │   │   │
│  │ └──────────────────────────┘   │   │
│  └────────────────────────────────┘   │
│              ↓↑ HTTP Requests          │
└──────────────┼────────────────────────┘
               │
        [Network/TLS]
               │
┌──────────────┴────────────────────────┐
│  Anthropic Claude API                  │
│  ┌────────────────────────────────┐   │
│  │ claude-3-5-sonnet-20241022     │   │
│  │ ┌──────────────────────────┐   │   │
│  │ │ Message Processing       │   │   │
│  │ │ Token Streaming          │   │   │
│  │ │ Response Generation      │   │   │
│  │ └──────────────────────────┘   │   │
│  └────────────────────────────────┘   │
└────────────────────────────────────────┘
```

## Data Flow

1. **User Types Message** → ClaudeCodeChat captures input
2. **Send Button Clicked** → useClaudeChat hook sends POST to `/api/claude/chat/stream`
3. **Backend Receives** → claude_chat route validates and calls ClaudeService
4. **Claude Service** → Builds context, calls Anthropic API with streaming
5. **Streaming Response** → Backend sends SSE updates back to frontend
6. **Frontend Displays** → Messages appear in real-time as they stream in
7. **Artifacts Generated** → Code blocks and data artifacts extracted and displayable
8. **User Can Apply** → Accept/reject/download generated schedules

## Authentication

All endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

The token is automatically included by the frontend from localStorage.

## Cost Estimation

Using Claude 3.5 Sonnet:
- Input: $3 per million tokens
- Output: $15 per million tokens

Typical scheduling task:
- Input: ~1,000 tokens (context + prompt)
- Output: ~2,000 tokens (response)
- Cost per task: ~$0.045

With 100 tasks/month = ~$4.50/month

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Verify `.env` file has `ANTHROPIC_API_KEY=sk-ant-...`
- Restart backend after updating `.env`
- Check key is valid at console.anthropic.com

### "Connection refused"
- Verify backend is running on port 8000
- Check `REACT_APP_API_URL` matches backend address
- Verify no firewall blocking localhost:8000

### "No response from Claude"
- Check Claude API status at status.anthropic.com
- Verify API key has credits/isn't rate limited
- Check network tab in browser dev tools
- Review backend logs for detailed errors

### "Streaming stops mid-response"
- Check for network timeouts (increase if needed)
- Verify browser supports EventSource (SSE)
- Check for proxy/firewall issues
- Review browser console for errors

## Next Steps

1. ✅ Setup complete
2. Test basic chat functionality
3. Try example prompts from the integration guide
4. Integrate with your existing schedule data
5. Customize system prompts for your needs
6. Add more specialized endpoints
7. Implement artifact persistence
8. Add analytics/logging

## Support

For issues:
1. Check the [integration guide](docs/CLAUDE_CHAT_INTEGRATION.md)
2. Review [example implementation](examples/claude-chat-admin.tsx)
3. Check backend logs for error messages
4. Review Claude API documentation at https://docs.anthropic.com

## License

This integration uses the Anthropic Claude API. See Anthropic's terms for usage.
