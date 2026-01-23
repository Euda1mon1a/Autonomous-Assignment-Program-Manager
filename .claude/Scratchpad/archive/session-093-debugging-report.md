# Session 093: Debugging Report - Next.js Proxy & Auth Headers

**Date:** 2026-01-13
**Status:** ✅ MYTH BUSTED
**Focus:** Verifying if Next.js rewrites strip Authorization headers.

## 1. The Myth
**Theory:** Next.js rewrites (`/api/:path*` -> `http://backend:8000/api/:path*`) strip the `Authorization: Bearer ...` header, causing the backend to see an anonymous user and crash (500).

## 2. The Evidence

### Test A: Instrumentation
We added debug logging to `backend/app/core/security.py` inside `get_current_user`.

### Test B: The Proxy Test
We executed a `curl` request against the **Next.js Frontend Proxy (Port 3000)**:
```bash
curl -X POST http://localhost:3000/api/v1/schedule/generate \
  -H "Authorization: Bearer <VALID_TOKEN>" ...
```

### Test C: The Logs
Reference `docker logs scheduler-local-backend`:
```
DEBUG: [get_current_user] Headers keys: [..., 'authorization', ...]
DEBUG: [get_current_user] Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn...
DEBUG: [get_current_user] Cookie token: Bearer eyJhbGciOiJIUzI1NiIsIn...
```
✅ **Confirmed:** The backend RECEIVED the Authorization header from the Next.js proxy.

## 3. Findings

1.  **Next.js Proxy is Transparent:** It successfully forwards `Authorization` headers. No manual route handlers are needed.
2.  **`user=anonymous` is a Red Herring:**
    *   Observed Log: `PHI_ACCESS_ATTEMPT ... user=anonymous`
    *   Cause: `PHIMiddleware` runs *before* authentication logic. It tries to peek at `request.state.user`, which is not yet set. This is normal and benign.
3.  **The 500 Error:**
    *   Since auth is verified working, the reported 500 error is **NOT** an auth failure coverage (which would be 401).
    *   It is a legitimate backend crash (Application Logic Error).
    *   Likely Candidates:
        *   Solver Timeout/Crash (e.g. `CP-SAT` hitting memory limits).
        *   Data Validation edge cases (e.g. `None` being accessed).

## 4. Next Steps

1.  **Revert:** Workarounds like "custom API route handlers" for proxying are **unnecessary** and should be abandoned.
2.  **Locate the Crash:** The 500 error is masking a genuine traceback.
    *   Look for `ERROR` logs in `scheduler-local-backend` immediately following a failed request.
    *   Search for `traceback` or `AttributeError`.
3.  **Frontend Code:** Ensure the React frontend is actually sending the header (the interceptor logic seemed correct). Since `curl` worked, the infrastructure is fine.

## 5. Clean Up
Removed debug instrumentation from `backend/app/core/security.py`.
