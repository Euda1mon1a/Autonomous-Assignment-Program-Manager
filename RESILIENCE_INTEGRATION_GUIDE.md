# Resilience Concept Integration Guide

## Mission Summary

Integration of exotic resilience concepts into admin rotation template bulk editing UI for enterprise differentiation. Created hooks and components to show intelligent previews before bulk operations.

**Status:** Hooks and Components Complete | Integration Pending MCP Proxy

---

## Files Created

### Hooks (3)

1. **`frontend/src/hooks/useEquityMetrics.ts`** - Gini coefficient calculation
2. **`frontend/src/hooks/useRigidityScore.ts`** - Time crystal rigidity analysis
3. **`frontend/src/hooks/usePhaseTransitionRisk.ts`** - Phase transition early warnings

### Components (3)

1. **`frontend/src/components/admin/EquityIndicator.tsx`** - Gini equity display
2. **`frontend/src/components/admin/RigidityBadge.tsx`** - Rigidity score display
3. **`frontend/src/components/admin/PhaseTransitionBanner.tsx`** - Warning banner

---

## Architecture

### Data Flow

```
Frontend Component
  ↓
React Query Hook
  ↓
API Client (post/get)
  ↓
[BLOCKER] MCP Proxy Endpoint (needs creation)
  ↓
Exotic Resilience API (/exotic-resilience/*)
  ↓
MCP Tools (already exist)
```

### Endpoints Required

The hooks call these endpoints which **need to be created** in the backend:

1. **Equity Metrics:**
   - Frontend calls: `POST /api/v1/mcp/calculate-equity-metrics`
   - Should proxy to MCP tool: `calculate_equity_metrics_tool`

2. **Rigidity Score:**
   - Frontend calls: `POST /api/v1/exotic-resilience/time-crystal/rigidity`
   - **Already exists** in backend (verified)

3. **Phase Transition:**
   - Frontend calls: `POST /api/v1/exotic-resilience/thermodynamics/phase-transition`
   - **Already exists** in backend (verified)

### Blocker Details

**Status:** 🔴 **2 of 3 endpoints exist**

The equity metrics endpoint needs an MCP proxy. Two options:

#### Option A: Create MCP Proxy Route (Recommended)

Create `backend/app/api/routes/mcp_proxy.py`:

```python
"""MCP Tool Proxy Routes - Frontend access to MCP tools."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.mcp.client import mcp_client  # Assuming MCP client exists

router = APIRouter(prefix="/mcp", tags=["mcp"])

class EquityMetricsRequest(BaseModel):
    provider_hours: dict[str, float]
    intensity_weights: dict[str, float] | None = None

@router.post("/calculate-equity-metrics")
async def calculate_equity_metrics(request: EquityMetricsRequest):
    """Proxy to calculate_equity_metrics_tool MCP tool."""
    result = await mcp_client.call_tool(
        "calculate_equity_metrics_tool",
        {
            "provider_hours": request.provider_hours,
            "intensity_weights": request.intensity_weights,
        }
    )
    return result
```

Then register in `backend/app/api/routes/__init__.py`.

#### Option B: Use Exotic Resilience Endpoint

Alternatively, create equity endpoint in exotic_resilience.py similar to rigidity.

---

## Integration Instructions

### P0: Gini Equity Preview in BulkActionsToolbar

**File:** `frontend/src/components/admin/BulkActionsToolbar.tsx`

**Add import:**
```typescript
import { EquityIndicator } from './EquityIndicator';
```

**Add to toolbar (after selection count, before dropdowns):**
```typescript
{/* Equity Impact Preview */}
{selectedCount > 0 && (
  <div className="px-3 py-2 bg-slate-800 rounded-lg">
    <EquityIndicator
      currentProviderHours={calculateProviderHours(templates, selectedIds)}
      compact={true}
    />
  </div>
)}
```

**Helper function needed:**
```typescript
function calculateProviderHours(
  templates: RotationTemplate[],
  selectedIds: string[]
): Record<string, number> {
  // Extract provider workload from selected templates
  // This requires access to template assignment data
  // Implementation depends on your data structure
  const hours: Record<string, number> = {};

  selectedIds.forEach(id => {
    const template = templates.find(t => t.id === id);
    if (template) {
      // Aggregate hours per provider
      // e.g., hours[providerId] = (hours[providerId] || 0) + templateHours;
    }
  });

  return hours;
}
```

### P1: Time Crystal Rigidity in Selection Summary

**Location:** Create a new "Selection Summary" panel or add to existing panel

**Component usage:**
```typescript
<RigidityBadge
  currentAssignments={convertToAssignments(currentTemplates)}
  proposedAssignments={convertToAssignments(selectedTemplates)}
  detailed={false}
/>
```

### P2: Phase Transition Banner in Page Header

**File:** `frontend/src/app/admin/templates/page.tsx`

**Add import:**
```typescript
import { PhaseTransitionBanner } from '@/components/admin/PhaseTransitionBanner';
```

**Add after `<header>` section, before `<main>`:**
```typescript
{/* Phase Transition Warning */}
<div className="max-w-7xl mx-auto px-4 py-3">
  <PhaseTransitionBanner
    lookbackDays={30}
    hideIfNormal={true}
  />
</div>
```

---

## Graceful Degradation

All hooks handle errors gracefully:

- **Loading state:** Shows spinner
- **Error state:** Shows "data unavailable" message
- **Empty data:** Returns sensible defaults

Example:
```typescript
if (isLoading) return <Spinner />;
if (error) return <div>Equity data unavailable</div>;
```

---

## Testing Without MCP Proxy

To test components before backend integration:

1. **Mock data in hooks:**
```typescript
// In useEquityMetrics.ts
queryFn: async () => {
  // Return mock data for testing
  return {
    gini_coefficient: 0.12,
    is_equitable: true,
    mean_workload: 45,
    // ... etc
  };
}
```

2. **Use `enabled: false` option:**
```typescript
const { data } = useEquityMetrics(hours, null, { enabled: false });
```

---

## Styling Consistency

All components follow existing admin UI patterns:

- **Colors:** Uses Tailwind slate/violet/purple palette
- **Spacing:** Consistent padding (px-3 py-2)
- **Typography:** text-sm for body, text-xs for labels
- **Backgrounds:** bg-slate-800 for panels, bg-slate-700 for dividers
- **Borders:** border-slate-700 for separators

---

## Performance Considerations

1. **Query staleTime:**
   - Equity: 30 seconds (rapid selection changes)
   - Rigidity: 30 seconds (rapid selection changes)
   - Phase Transition: 5 minutes (expensive calculation)

2. **Conditional fetching:**
   - All hooks use `enabled` option to prevent unnecessary calls
   - Equity: `enabled: !!providerHours && Object.keys(providerHours).length > 0`

3. **Refetch intervals:**
   - Phase Transition: Auto-refetches every 10 minutes for early warnings
   - Others: Manual refetch only

---

## Next Steps

### Immediate (Unblock Integration)

1. **Create MCP proxy endpoint** for equity metrics (Option A above)
2. **Implement `calculateProviderHours` helper** in BulkActionsToolbar
3. **Add EquityIndicator** to toolbar
4. **Add PhaseTransitionBanner** to page header

### Future Enhancements

1. **Projected Equity:** Show "before vs after" when bulk operations are prepared
2. **Rigidity Trends:** Track rigidity over time to detect increasing churn
3. **Signal Details Modal:** Click signal in PhaseTransitionBanner to see full analysis
4. **Disable Bulk Ops:** Automatically disable operations during critical phase transitions

---

## Troubleshooting

### "Equity data unavailable"

- Check MCP proxy endpoint exists at `/api/v1/mcp/calculate-equity-metrics`
- Verify MCP client is configured and connected
- Check browser console for fetch errors

### "Rigidity data unavailable"

- Check exotic resilience endpoints are registered
- Verify `/api/v1/exotic-resilience/time-crystal/rigidity` responds
- Check request payload matches expected schema

### "Phase transition data unavailable"

- Same as rigidity (uses same exotic resilience route)
- Check `/api/v1/exotic-resilience/thermodynamics/phase-transition`

---

## Contact

For questions or issues:
- Check `.claude/dontreadme/synthesis/PATTERNS.md` for integration patterns
- Use `rag_search('resilience framework')` for conceptual background
- See `backend/app/api/routes/exotic_resilience.py` for endpoint reference

---

**Created:** 2026-01-04
**Branch:** feature/bulk-template-editing
**Status:** Ready for backend MCP proxy creation
