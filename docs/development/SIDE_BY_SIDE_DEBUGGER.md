# Side-by-Side Debugger Design Document

> **Status:** RFC (Request for Comments)
> **Author:** Claude Code
> **Date:** 2026-01-20
> **Target Route:** `/admin/debugger`

---

## Executive Summary

This document proposes a **Side-by-Side Debugger** page for the Residency Scheduler that displays the frontend application view alongside raw database data (via NocoDB or direct API inspection). This enables rapid diagnosis of whether issues originate in the frontend rendering layer or the backend/database layer.

---

## Problem Statement

When debugging schedule display issues, developers must currently:
1. Check the frontend UI to see what's rendered
2. Open a separate tool (pgAdmin/DBeaver/psql) to query the database
3. Mentally correlate the two views
4. Repeat for each hypothesis

This context-switching is slow and error-prone. A unified view would reduce debugging time by ~60%.

---

## Solution Architecture

### Option A: Dual-Iframe Layout (Recommended for MVP)

```
┌─────────────────────────────────────────────────────────────┐
│  [Debugger Toolbar]  [Refresh] [Split: 50/50 ▼] [Settings]  │
├────────────────────────────┬────────────────────────────────┤
│                            │                                │
│   FRONTEND VIEW            │   DATABASE VIEW                │
│   (Your App at /schedule)  │   (NocoDB / API Inspector)     │
│                            │                                │
│   ┌──────────────────┐     │   ┌──────────────────────┐     │
│   │ Schedule Grid    │     │   │ assignments table    │     │
│   │ showing shifts   │     │   │ ─────────────────    │     │
│   │                  │     │   │ id | person | date   │     │
│   │ [Dr. Smith: AM]  │     │   │ 1  | Smith  | 01-20  │     │
│   │ [Dr. Jones: PM]  │     │   │ 2  | Jones  | 01-20  │     │
│   └──────────────────┘     │   └──────────────────────┘     │
│                            │                                │
├────────────────────────────┴────────────────────────────────┤
│  [Status: Connected] [Last Sync: 2s ago] [Queries: 3]       │
└─────────────────────────────────────────────────────────────┘
```

### Option B: Integrated Inspector Panel

Rather than iframes, embed a React-based database inspector that queries the API directly:

```
┌─────────────────────────────────────────────────────────────┐
│  Schedule Page (normal view)                    [🔍 Debug]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Normal schedule view content...                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ▼ Debug Panel (collapsible)                               │
│  ┌─────────────────────────────────────────────────────────┐
│  │ [API Calls] [DB State] [Component Tree] [Network]       │
│  │                                                         │
│  │ GET /api/v1/assignments?block_id=10                     │
│  │ Response: 200 OK (145ms)                                │
│  │ ┌─────────────────────────────────────────────────────┐ │
│  │ │ { "items": [ { "id": 1, "person_id": 42, ... } ] }  │ │
│  │ └─────────────────────────────────────────────────────┘ │
│  └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

---

## Debugging Decision Matrix

| Symptom | Frontend Shows | Database Shows | Diagnosis |
|---------|----------------|----------------|-----------|
| Missing shift | Empty slot | Data exists | **Frontend Issue**: React not rendering, API filter wrong |
| Missing shift | Empty slot | Row missing | **Backend Issue**: Scheduler didn't write to DB |
| Wrong name | "Dr. Smith" | "Dr. Jones" | **Cache Issue**: Stale frontend state or API cache |
| Duplicate | Two blocks | Two rows | **Logic Issue**: Script ran twice or no dedup |
| Duplicate | Two blocks | One row | **Render Bug**: Component rendering same data twice |
| Wrong date | Shows Jan 21 | Shows Jan 20 | **Timezone Issue**: UTC vs local conversion bug |

---

## Technical Implementation

### 1. Route Structure

```
frontend/src/app/admin/debugger/
├── page.tsx           # Main debugger page
├── layout.tsx         # Debugger-specific layout (no nav interference)
├── components/
│   ├── DebugToolbar.tsx
│   ├── IframePanel.tsx
│   ├── ApiInspector.tsx
│   ├── TableViewer.tsx
│   └── QueryBuilder.tsx
└── hooks/
    ├── useApiInterceptor.ts
    └── useTableData.ts
```

### 2. Core Components

#### DebugToolbar.tsx
```typescript
interface DebugToolbarProps {
  leftUrl: string;
  rightUrl: string;
  splitRatio: number;
  onSplitChange: (ratio: number) => void;
  onRefresh: () => void;
  onSwap: () => void;
}

// Features:
// - URL input for left/right panels
// - Split ratio slider (25/75, 50/50, 75/25)
// - Swap button to flip panels
// - Sync scroll toggle
// - Auto-refresh interval selector
```

#### ApiInspector.tsx
```typescript
interface ApiCall {
  id: string;
  timestamp: Date;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  url: string;
  requestBody?: unknown;
  responseBody?: unknown;
  status: number;
  duration: number;
  error?: string;
}

// Features:
// - Intercepts all axios calls via request/response interceptors
// - Shows raw request (after snake_case conversion)
// - Shows raw response (before camelCase conversion)
// - Highlights differences between request and response schemas
// - Filter by status (2xx, 4xx, 5xx)
// - Search by URL pattern
```

#### TableViewer.tsx
```typescript
interface TableViewerProps {
  tableName: string;
  filters?: Record<string, unknown>;
  columns?: string[];
  limit?: number;
}

// Features:
// - Direct query to backend API: GET /api/v1/debug/tables/{name}
// - Column sorting and filtering
// - Row highlighting on hover
// - Click row to see full JSON
// - Export to CSV/JSON
```

### 3. Backend API Additions

New debug endpoints (admin-only, dev mode):

```python
# backend/app/api/routes/debug.py

@router.get("/tables/{table_name}")
async def get_table_data(
    table_name: str,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
    filters: str = Query(default="{}"),  # JSON string
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch raw table data for debugging.
    Only available when DEBUG=true.
    """
    if not settings.DEBUG:
        raise HTTPException(403, "Debug endpoints disabled in production")

    # Validate table name against allowlist
    allowed_tables = ["assignments", "people", "blocks", "rotations", "absences"]
    if table_name not in allowed_tables:
        raise HTTPException(400, f"Table not allowed: {table_name}")

    # Execute query with SQLAlchemy
    ...

@router.get("/query")
async def execute_debug_query(
    query: str = Query(..., description="SQL SELECT query"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute read-only SQL for debugging.
    CRITICAL: Only SELECT allowed, validated server-side.
    """
    if not settings.DEBUG:
        raise HTTPException(403, "Debug endpoints disabled in production")

    # Validate query is SELECT only
    if not query.strip().upper().startswith("SELECT"):
        raise HTTPException(400, "Only SELECT queries allowed")

    # Execute with read-only transaction
    ...
```

### 4. Docker Integration for NocoDB

Add NocoDB service to docker-compose.yml:

```yaml
services:
  # ... existing services ...

  nocodb:
    image: nocodb/nocodb:latest
    container_name: residency_nocodb
    environment:
      NC_DB: "pg://db:5432?u=${DB_USER:-postgres}&p=${DB_PASSWORD}&d=${DB_NAME:-residency_scheduler}"
      NC_AUTH_JWT_SECRET: "${SECRET_KEY}"
      NC_PUBLIC_URL: "http://localhost:8085"
      NC_DISABLE_TELE: "true"
    ports:
      - "8085:8080"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - residency_network
    profiles:
      - debug  # Only starts with: docker compose --profile debug up
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Usage:**
```bash
# Start with debug profile (includes NocoDB)
docker compose --profile debug up -d

# Normal start (no NocoDB)
docker compose up -d
```

### 5. Security Considerations

| Risk | Mitigation |
|------|------------|
| SQL injection | Parameterized queries only, SELECT whitelist |
| Data exposure | Admin-only routes, DEBUG flag required |
| PERSEC violation | No PII in debug output, synthetic IDs |
| iframe clickjacking | X-Frame-Options: SAMEORIGIN |
| Token leakage | Redact auth headers in inspector |

**Production Safeguards:**
```typescript
// frontend/src/app/admin/debugger/page.tsx

export default function DebuggerPage() {
  const { user } = useAuth();

  // Block in production
  if (process.env.NODE_ENV === 'production' && !process.env.NEXT_PUBLIC_ENABLE_DEBUGGER) {
    return <div>Debugger disabled in production</div>;
  }

  // Require admin role
  if (!user?.roles?.includes('admin')) {
    return <Unauthorized message="Admin access required" />;
  }

  return <DebuggerLayout />;
}
```

---

## Implementation Phases

### Phase 1: MVP (2-3 days)
- [x] Design document (this file)
- [ ] Create `/admin/debugger` route
- [ ] Dual-iframe layout with toolbar
- [ ] Basic split ratio controls
- [ ] Link in admin navigation

### Phase 2: API Inspector (2-3 days)
- [ ] Axios interceptor for call logging
- [ ] Request/response diff viewer
- [ ] Status filtering and search
- [ ] Latency highlighting

### Phase 3: Table Viewer (3-4 days)
- [ ] Backend debug API endpoints
- [ ] Table browser UI
- [ ] Column sorting/filtering
- [ ] Row detail modal

### Phase 4: NocoDB Integration (1-2 days)
- [ ] Add NocoDB to docker-compose
- [ ] Configure database connection
- [ ] Iframe embedding

### Phase 5: Polish (2-3 days)
- [ ] Keyboard shortcuts (Cmd+D to toggle)
- [ ] Sync scroll between panels
- [ ] Save debug sessions
- [ ] Export debug report

---

## UI/UX Guidelines

Follow existing admin page patterns:

```typescript
// Color palette (from existing health dashboard)
const colors = {
  bg: 'bg-slate-900',
  card: 'bg-slate-800',
  border: 'border-slate-700',
  text: 'text-slate-100',
  accent: 'text-cyan-400',
  success: 'text-emerald-400',
  warning: 'text-amber-400',
  error: 'text-red-400',
};

// Status indicators
const statusColors = {
  healthy: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50',
  degraded: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
  unhealthy: 'bg-red-500/20 text-red-400 border-red-500/50',
};
```

**Icons (Lucide React):**
- `Bug` - Debugger icon
- `Split` - Panel split
- `Database` - DB view
- `Network` - API calls
- `RefreshCw` - Refresh
- `Settings` - Config

---

## Testing Strategy

### Unit Tests
```typescript
// frontend/src/__tests__/admin/debugger/ApiInspector.test.tsx
describe('ApiInspector', () => {
  it('captures axios calls', async () => { ... });
  it('shows request/response bodies', () => { ... });
  it('filters by status code', () => { ... });
  it('redacts auth headers', () => { ... });
});
```

### Integration Tests
```python
# backend/tests/api/test_debug_routes.py
def test_debug_tables_requires_admin():
    ...

def test_debug_tables_blocked_in_production():
    ...

def test_debug_query_rejects_non_select():
    ...
```

### E2E Tests
```typescript
// frontend/e2e/debugger.spec.ts
test('debugger shows API calls in real-time', async ({ page }) => {
  await page.goto('/admin/debugger');
  await page.click('[data-testid="left-panel-refresh"]');
  await expect(page.locator('[data-testid="api-call-list"]')).toContainText('GET /api/v1');
});
```

---

## Related Documentation

- `/admin/health` - Existing health dashboard (UI reference)
- `/admin/labs` - Research labs hub (layout reference)
- `docs/development/BEST_PRACTICES_AND_GOTCHAS.md` - Debugging tips
- `CLAUDE.md` - API type conventions (camelCase/snake_case)

---

## Open Questions

1. **NocoDB vs Custom Table Viewer**: Should we embed NocoDB (quick) or build a custom React table viewer (more integrated)?
   - **Recommendation**: Start with iframes + NocoDB for speed, then iterate to custom if needed.

2. **Debug Mode Persistence**: Should debug state persist across page reloads?
   - **Recommendation**: Yes, use localStorage with encryption for sensitive data.

3. **Remote Debugging**: Should this work against staging/production databases?
   - **Recommendation**: No, local development only. Use audit logs for production debugging.

---

## Appendix: Quick Start

Once implemented, usage will be:

```bash
# 1. Start services with debug profile
docker compose --profile debug up -d

# 2. Open debugger
open http://localhost:3000/admin/debugger

# 3. Configure panels
#    Left:  http://localhost:3000/schedule (your app)
#    Right: http://localhost:8085 (NocoDB)

# 4. Make changes via MCP tool
#    Watch rows appear in NocoDB in real-time
```

---

## Chrome Extension Integration (2026 Strategy)

The 2026 debugging strategy shifts from "watching" to "interacting." Claude for Chrome creates a feedback loop where Claude can see what you see on the screen.

### Claude for Chrome ("The Eyes")

Anthropic's official Chrome extension (and Claude Code + Chrome integration) allows Claude to interact directly with your browser tabs:

**Side-by-Side Comparison:**
```
You: "Open my residency app in one tab and NocoDB in another."
Claude: "I see Dr. Montgomery is on the GUI calendar for Tuesday,
        but the Postgres row in NocoDB says Wednesday.
        There is a frontend timezone rendering bug."
```

**Automatic Testing:**
```
You: "Go to my localhost, try to swap two residents, and tell me
      if the GUI updates correctly."
Claude: *physically clicks buttons in your browser to verify*
```

### Benefits for Residency Scheduler

| Feature | Benefit |
|---------|---------|
| Visual inspection | Catches rendering bugs human eyes might miss |
| Cross-view correlation | Compares GUI vs DB automatically |
| Interactive testing | Simulates user actions to verify workflows |
| Screenshot analysis | Can analyze schedule grids for anomalies |

---

## NocoDB MCP Integration ("The Direct Line")

NocoDB now offers a **native MCP Server**, enabling conversational database queries without writing SQL.

### Configuration

Add to your MCP settings (Claude Desktop or Chrome extension):

```json
{
  "mcpServers": {
    "nocodb": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-nocodb"],
      "env": {
        "NOCODB_BASE_URL": "http://localhost:8085",
        "NOCODB_API_TOKEN": "${NOCODB_API_TOKEN}"
      }
    }
  }
}
```

### Conversational Queries

Instead of writing SQL, you can type into the Claude sidebar:

| Query Type | Example Prompt |
|------------|----------------|
| Data retrieval | "Show me all residents who haven't had a vacation in 3 months" |
| Anomaly detection | "Find any duplicate shift assignments for next week" |
| Coverage analysis | "Which clinics have less than 2 residents assigned tomorrow?" |
| Audit trail | "Show all schedule changes made in the last 24 hours" |

### MCP Tools Available

```typescript
// List records from a table
mcp__nocodb__list_records({ table: 'assignments', filters: {...} })

// Create a new record
mcp__nocodb__create_record({ table: 'assignments', data: {...} })

// Custom query
mcp__nocodb__query({ sql: 'SELECT ...' })

// Get table schema
mcp__nocodb__get_schema({ table: 'assignments' })
```

### OAuth Integration

NocoDB can be configured as an OAuth Connector for Claude, allowing database management directly from the claude.ai web interface without needing the terminal.

---

## 2026 Residency Scheduler Debug Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Backend** | FastAPI + PostgreSQL (pgvector) | Core application |
| **Visualization** | NocoDB | Human-readable "Airtable" view |
| **Interaction** | Claude Code + Chrome Extension | AI-powered debugging |
| **Protocol** | MCP | Glue connecting all components |
| **Deep Dive** | pgAdmin | Manual SQL exploration (when needed) |

### When to Use Each Tool

| Scenario | Recommended Tool |
|----------|------------------|
| Quick data check | NocoDB (visual, instant) |
| Complex query | pgAdmin or raw SQL |
| Visual bug | Chrome Extension + Debugger |
| Data discrepancy | Side-by-Side Debugger |
| Automated testing | Claude Chrome Extension |
| Production audit | Activity logs + pgAdmin |

---

*Document created for CCCLI review. Feedback welcome via PR comments.*
