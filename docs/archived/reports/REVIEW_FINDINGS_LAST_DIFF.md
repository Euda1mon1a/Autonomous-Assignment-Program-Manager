# Review Findings: Diff Since Last

Date: 2026-01-18
Scope: Working tree changes vs `HEAD`

## Executive Summary
Multiple frontend integrations now rely on live resilience APIs, but several response-shape mismatches and missing exports will break compilation or yield incorrect metrics at runtime. The highest risk issues are a missing hook export (`useVulnerabilityReport`) and backend/FE schema drift in the Sovereign Portal and Stigmergy patterns pipeline.

## Findings (Ordered by Severity)

### High
1) Missing hook export + incorrect usage
- Problem: `useVulnerabilityReport` is re-exported but not defined in the referenced file, and the call site uses positional args rather than the hook’s existing signature.
- Impact: TypeScript compile error or runtime call mismatch; resilience lab page will not build.
- Evidence:
  - `frontend/src/features/fragility-triage/index.ts:11`
  - `frontend/src/features/fragility-triage/hooks/useFragilityData.ts` (no `useVulnerabilityReport` export)
  - `frontend/src/app/admin/labs/resilience/page.tsx:129-134`
- Recommendation: Either import `useVulnerabilityReport` from `frontend/src/hooks/useResilience.ts`, or implement/export a wrapper in `useFragilityData.ts` with the expected signature. Fix call site to match a single signature.

2) Sovereign Portal health response shape mismatch
- Problem: The Sovereign Portal hook expects `overallStatus` values `GREEN|YELLOW|RED` and redundancy fields `role/required/available/isAdequate`, but the backend returns `overall_status` values `healthy|warning|degraded|critical|emergency` and redundancy fields `service/minimum_required/buffer`.
- Impact: Incorrect status mapping (likely `OFFLINE`), broken redundancy metrics, and derived fragility values become inaccurate.
- Evidence:
  - `frontend/src/features/sovereign-portal/hooks.ts:32-46`
  - Backend schema: `backend/app/schemas/resilience.py:53-70`, `backend/app/schemas/resilience.py:134-158`
- Recommendation: Update the frontend types + mapping to reflect backend enums and redundancy fields.

### Medium
3) Stigmergy patterns parsing uses the wrong shape
- Problem: The frontend expects `data.patterns` to include keys like `popularSlots` and `strongSwapPairs`, but backend returns those keys at the top-level (`popular_slots`, `strong_swap_pairs`). The transform will always fall back to mock data.
- Impact: Live stigmergy patterns are ignored; UI always shows simulated visuals.
- Evidence:
  - `backend/app/resilience/stigmergy.py:664-707`
  - `backend/app/schemas/resilience.py:1654-1663`
  - `frontend/src/app/admin/visualizations/stigmergy-flow/constants.ts:132-180`
- Recommendation: Align on a single response shape. Either update backend to return `patterns` list with those fields, or update `transformPatternsToNodes` to read top-level keys.

4) N1 vulnerability `affectedBlocks` typed as number but is list
- Problem: `affectedBlocks` is typed as `number` but backend returns a list; variance calculation reduces arrays, producing `NaN` or string concatenation.
- Impact: Fragility variance and downstream metrics become unstable or invalid.
- Evidence:
  - `frontend/src/features/fragility-triage/hooks/useFragilityData.ts:26-29`
  - `backend/app/schemas/resilience.py:255-274`
- Recommendation: Update the type to `number[]` and adjust variance calculation to sum lengths or counts.

### Low
5) Stigmergy loading ref unmounted guard removed
- Problem: `mountedRef` is used in the analyze handler, but `useEffect` cleanup that flips it false was removed.
- Impact: Potential state update after unmount if analysis completes late.
- Evidence:
  - `frontend/src/app/admin/labs/optimization/page.tsx:177-184`
- Recommendation: Restore cleanup or remove `mountedRef` if no longer needed.

6) Energy landscape endpoint reads unused `temperature`
- Problem: API endpoint checks `request.temperature` but the request model has no such field.
- Impact: Dead code and potential confusion; caller cannot influence temperature.
- Evidence:
  - `backend/app/api/routes/exotic_resilience.py:868-872`
- Recommendation: Remove temperature reference or add it to `EnergyLandscapeRequest`.

## Additional Notes
- There are several new hook-based integrations with live endpoints (Overseer, N1N2, Synapse Monitor, Holographic Hub). These look consistent with existing resilience endpoints but should be validated against the backend’s actual response shapes.

## Suggested Verification
1) Run frontend typecheck/build to catch TS errors.
2) Hit `/api/v1/resilience/health` and `/api/v1/resilience/tier3/stigmergy/patterns` and compare payloads to frontend expectations.
3) Exercise `/admin/labs/resilience` and `/admin/labs/optimization` to confirm data displays and fallbacks.
