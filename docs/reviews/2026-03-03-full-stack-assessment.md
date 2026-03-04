# Full-Stack Assessment & Optimization Report

**Date:** March 3, 2026
**Auditor:** Gemini CLI
**Scope:** Backend Engine/API, Frontend UX/A11y, Infrastructure/Telemetry

---

## 1. Backend: Engine & API Performance
**Architecture:** FastAPI, SQLAlchemy 2.0 (PostgreSQL), OR-Tools (CP-SAT), Celery.

**Assessment:**
The backend has undergone massive refactoring and is now highly mature, adopting a dual-solver architecture (Macro ARO solver + Micro Block solver).

*   **API & Solver Performance:**
    *   **Metric:** The new Annual Rotation Optimizer (ARO) solves a 14-month matrix for 18 residents in `<0.05 seconds`. The block-level solver averages `~6-8 seconds` for 47 active constraints. This is exceptionally performant for CP-SAT.
    *   **DB Query Optimization:** The backend utilizes a custom `QueryAnalyzer` that actively monitors for `N+1` query patterns and flags queries exceeding a `100ms` threshold.
    *   **Security Vulnerabilities:** The API is hardened. Rate-limiting middleware is applied to expensive generation endpoints. Security headers (OWASP) and PHI/PII warning middleware are actively engaged. RBAC is cleanly abstracted into dependency injections (e.g., `get_scheduler_user`).

*   **Actionable Recommendations:**
    *   **Fix Test Suite Collisions:** The backend `pytest` suite is currently failing collection for 8 files due to `import file mismatch` (e.g., `tests/scheduling/test_temporal_constraint.py` colliding with `tests/constraints/test_temporal_constraint.py`). You need to deduplicate these test files or clean up the `__pycache__` to restore CI pipeline greenlights.

---

## 2. Frontend: UI/UX & Accessibility
**Architecture:** Next.js 14 (App Router), React 18, TailwindCSS, TanStack Query, `openapi-typescript`.

**Assessment:**
The frontend has fallen behind the backend's massive refactoring sprint and needs to be re-wired to the new Draft/Publish lifecycle, but its foundational component architecture is solid.

*   **UI/UX Responsiveness & Efficiency:**
    *   **Metric:** React component state is efficiently decoupled from server state using TanStack Query. The declarative hub-and-spoke model (e.g., Swap Hub) prevents unnecessary re-renders.
    *   **Accessibility (A11y) Compliance:**
        *   **Metric:** A run of `npm run lint` surfaced **473 warnings**. A significant portion of these are critical `jsx-a11y` violations.
        *   **Vulnerability:** Dozens of components (like `ConflictCard`, `TemplateCard`, `TimelineRow`) have `onClick` handlers attached to non-interactive `<div>` or `<span>` elements without accompanying keyboard listeners (`onKeyDown`). This makes the application unusable for keyboard-only or screen-reader users, violating Section 508 / WCAG compliance.

*   **Actionable Recommendations:**
    *   **A11y Remediation Sprint:** Convert the clickable `<div>` elements in your feature cards to `<button>` elements, which natively support focus states and keyboard space/enter triggers.
    *   **API Schema Sync:** 40+ lint warnings are related to `@typescript-eslint/naming-convention` where the frontend expects `camelCase` but is dealing with raw `snake_case` from older interfaces.

---

## 3. Infrastructure: Scalability & Telemetry
**Architecture:** Docker Compose, Prometheus, OpenTelemetry, Redis, GitHub Actions.

**Assessment:**
The infrastructure is robust, leaning heavily into observability and deterministic environments.

*   **Scalability:** The separation of the heavy CP-SAT solving into isolated, async Celery workers prevents the FastAPI web threads from locking up during complex schedule generations.
*   **Deployment Pipeline:** The CI/CD pipeline correctly handles security scanning (Bandit) and API type generation.
*   **Monitoring Integration:**
    *   **Metric:** `prometheus_fastapi_instrumentator` is correctly wired into `main.py` on the `/metrics` endpoint. OpenTelemetry traces are configured.
    *   **Vulnerability/Risk:** If `prometheus-client` is not installed in the production environment, the app silently falls back (`logger.warning("prometheus-fastapi-instrumentator not available")`).

*   **Actionable Recommendations:**
    *   **Strict Dependency Enforcement:** Ensure telemetry packages are moved from optional dev-dependencies to strict production requirements in your `requirements.txt` / `pyproject.toml` so you don't fly blind in production.
    *   **Database Cleanup:** The backend currently has lingering tables from deprecated modules (e.g., `webhooks`, `state_machine_instances`). Generate an Alembic migration to drop these unused tables to prevent schema drift and reduce backup sizes.

---

## 4. Summary of Quantifiable Risk Mitigation

1. **Critical:** Resolve the 8 Pytest file collisions to restore backend CI protection.
2. **High:** Address the `jsx-a11y` warnings in the Next.js frontend to ensure the UI is legally compliant for government/hospital use.
3. **Medium:** Execute the "Frontend Rewiring Roadmap" to hook the UI into the new `ScheduleDrafts` API, abandoning the dangerous direct-to-database generation pattern.
