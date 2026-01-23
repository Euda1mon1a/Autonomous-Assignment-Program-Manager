# Session 092: WebSocket + HTTP Auth Fix (Continued)

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`

## Problem Summary

Solver 3D visualization not rendering due to:
1. WebSocket connecting to wrong port (3000 instead of 8000) ✅ FIXED
2. WebSocket auth failing (no token passed) ✅ FIXED
3. HTTP API requests failing with 500 (token not sent to backend) ✅ PARTIALLY FIXED
4. Session lost on page refresh ✅ FIXED

## Root Cause Analysis

**Next.js rewrites don't forward cookies OR custom headers** (like Authorization) from browser → backend. The flow is:

1. Browser → Next.js (port 3000): Has cookie + Authorization header
2. Next.js → Backend (port 8000): **Neither cookie nor Authorization header forwarded**
3. Backend sees "user=anonymous" → 500 error

## Fixes Applied

### 1. WebSocket URL Fix
**File:** `frontend/src/hooks/useWebSocket.ts`
- Auto-converts port 3000 → 8000 for WebSocket

### 2. WebSocket Auth Fix
**Files:**
- `frontend/src/lib/auth.ts` - Added `getAccessToken()` export
- `frontend/src/features/voxel-schedule/useSolverWebSocket.ts` - Passes token as query param

### 3. HTTP Authorization Header Fix
**File:** `frontend/src/lib/api.ts`
- Added async request interceptor to inject `Authorization: Bearer <token>` header
- Token retrieved via `getAccessToken()` from in-memory storage

### 4. Session Persistence Fix (Page Refresh)
**Files:**
- `frontend/src/lib/auth.ts`:
  - `storeTokens()` now saves refresh token to `sessionStorage.__rt`
  - Added `restoreSession()` function that loads from sessionStorage and calls `performRefresh()`
  - `clearTokenState()` now clears sessionStorage
- `frontend/src/contexts/AuthContext.tsx`:
  - `initAuth()` now calls `restoreSession()` before `validateToken()`

## Current Status

**Working:**
- ✅ Fresh login stores tokens and subsequent requests have Authorization header
- ✅ Page refresh restores session from sessionStorage
- ✅ WebSocket connects to correct port with token

**NOT Working:**
- ❌ Backend still shows `user=anonymous` even when Authorization header is sent
- ❌ `/schedule/generate` and `/schedule/queue` return 500

## Next Steps to Debug

The Authorization header IS being added by the frontend, but Next.js rewrites might be stripping it. Need to either:

1. **Check if Next.js forwards Authorization header** - May need to configure rewrites
2. **Create custom API route handlers** that properly forward headers
3. **Or have frontend connect directly to backend** (bypass proxy, requires CORS)

### To verify the header is being stripped:

```bash
# Add logging to backend to see incoming headers
docker exec scheduler-local-backend grep -r "Authorization" /app/app/core/security.py
```

### Check backend security.py for how it extracts the token:
- Location: `backend/app/core/security.py`
- Uses `OAuth2PasswordBearer` which looks for `Authorization: Bearer <token>` header
- Need to verify if cookie fallback exists for proxied requests

## Files Modified This Session

```
frontend/src/features/voxel-schedule/index.ts        # Duplicate export fix (earlier)
frontend/src/hooks/useWebSocket.ts                   # URL port fix
frontend/src/lib/auth.ts                             # Token storage + sessionStorage
frontend/src/lib/api.ts                              # Authorization header injection
frontend/src/features/voxel-schedule/useSolverWebSocket.ts  # Pass token to WS
frontend/src/contexts/AuthContext.tsx                # Session restore on mount
```

## Console Log Markers Added (for debugging)

- `[Auth] storeTokens called:` - When tokens are stored
- `[Auth] Access token stored:` - When access token is saved
- `[Auth] getAccessToken called, token:` - When token is retrieved
- `[Auth] Found stored refresh token, attempting refresh...` - Session restore
- `[Auth] Session restored successfully` - Session restore success
- `[AuthContext] restoreSession result:` - Session restore result
- `[API] Request interceptor:` - Every API request
- `[API] Added Authorization header` - When header is injected

## Key Learning

**Next.js rewrites are NOT a transparent proxy.** They:
1. DO NOT forward cookies from browser to backend
2. DO NOT forward custom headers (Authorization) from browser to backend
3. Make a NEW request server-side that loses browser context

**Solution options:**
1. Store tokens client-side and pass via header (done, but header not reaching backend)
2. Create `/app/api/**/route.ts` handlers that manually forward headers
3. Have frontend talk directly to backend (needs CORS)
