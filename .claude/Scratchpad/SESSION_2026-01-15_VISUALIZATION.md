# Session 2026-01-15: Stigmergy Flow Visualization Prototype

> **Date:** 2026-01-15
> **Focus:** Experimental 3D schedule visualization
> **Status:** Prototype complete, runtime errors in browser

---

## Mission

**Objective:** Create exotic 3D visualization of schedule data to explore whether humans can interpret scheduling patterns intuitively through spatial visualization.

**Inspiration:** Named "Stigmergy Flow" after ant pheromone trails in the resilience framework.

---

## Work Completed

### 1. Dense Particle Flow (Gemini HTML)
**File:** `frontend/public/stigmergy-flow.html`

- 2500 particles representing schedule assignments
- 90-day timeline on Z-axis
- Color-coded: Blue=Clinic, Green=FMIT, Yellow=Call, Red=Conflict, White=Unassigned
- Custom GLSL shaders for glow effect
- Particles flow through time (animated)
- Grid guides showing spacetime structure
- Mock AI analysis panel (no external API)

**Status:** Serves 200, but runtime JS errors in browser

### 2. React Three Fiber Version
**Directory:** `frontend/src/app/admin/visualizations/stigmergy-flow/`

Files created:
- `page.tsx` - Next.js page with dynamic imports (ssr: false)
- `types.ts` - ParticleType enum, ScheduleNode, SimulationConfig
- `constants.ts` - Mock data generator, layout constants
- `components/StigmergyScene.tsx` - R3F Canvas (postprocessing removed)
- `components/FlowSimulation.tsx` - Particle system with Trail, Float, Sparkles
- `components/UIOverlay.tsx` - HUD with controls and AI panel
- `components/index.ts` - Exports

**Issue:** `@react-three/postprocessing@3` requires `@react-three/fiber@9` but repo has `@8.18.0`. Removed postprocessing to fix, but visualization too sparse (~35 particles) to show meaningful patterns.

### 3. N-1/N-2 Contingency Visualization
**File:** `frontend/public/n1-contingency.html`

- 10 faculty nodes (outer circle)
- 24 resident nodes (inner area)
- Connection lines showing supervision relationships
- Click faculty to simulate absence
- Real-time metrics: Coverage Rate, Supervision Gaps, Overloaded Faculty, At-Risk Residents
- N-1 mode (1 removal) vs N-2 mode (2 removals)

**Status:** Serves 200, runtime errors (likely Three.js CDN + OrbitControls loading issue)

### 4. Google AI Studio Prompt
**File:** `docs/visualizations/N1_N2_GOOGLE_STUDIO_PROMPT.md`

Complete prompt for generating N-1/N-2 visualization including:
- All 10 faculty with specialties/capacities
- 24 residents with primary/backup supervision structure
- Visualization requirements (layout, interactivity, metrics)
- The "cascade risk" insight

---

## Key Insight

**Dense HTML version (2500 particles) > Sparse R3F version (~35 particles)**

The dense version shows interpretable patterns (the "mound" of coverage), while the sparse version just looks like scattered dots. Density matters for pattern recognition.

**N-1/N-2 is the killer use case** - "what breaks if Dr. X is out?" is immediately actionable for program coordinators.

---

## Files Created This Session

```
frontend/
├── public/
│   ├── stigmergy-flow.html      # Dense particle flow (2500 particles)
│   └── n1-contingency.html      # N-1/N-2 contingency visualization
├── src/app/admin/visualizations/stigmergy-flow/
│   ├── page.tsx
│   ├── types.ts
│   ├── constants.ts
│   └── components/
│       ├── index.ts
│       ├── StigmergyScene.tsx
│       ├── FlowSimulation.tsx
│       └── UIOverlay.tsx
docs/visualizations/
├── STIGMERGY_FLOW_PLAN.md
└── N1_N2_GOOGLE_STUDIO_PROMPT.md
```

---

## Dependencies Added

```json
"@react-three/postprocessing": "^3.x"  // Added with --legacy-peer-deps
"postprocessing": "^6.x"               // Peer dependency
```

**Warning:** Version mismatch with @react-three/fiber@8. Either upgrade fiber to v9 or downgrade postprocessing.

---

## Runtime Errors

Both HTML visualizations serve (200) but have JS errors:

1. **stigmergy-flow.html**: Unknown - need browser console
2. **n1-contingency.html**: Unknown - likely OrbitControls loading from CDN

**Probable cause:** Three.js r128 CDN + OrbitControls addon loading order

---

## Recommendations for Next Session

### Quick Fixes
1. Check browser console for exact errors
2. May need to load OrbitControls differently (ES module import vs global)
3. Consider using a bundled approach instead of CDN

### If Continuing Visualization Work
1. Use Google AI Studio prompt to generate cleaner N-1/N-2 version
2. The dense particle approach needs performance optimization (InstancedMesh)
3. N-1/N-2 with 10 faculty is the right scope for immediate value

### If Pivoting
Visualization prototypes are in `/public/` - can delete or keep as experiments.

Higher priority items from plan:
- PR #690: MEDCOM Day-Type System (awaiting Codex)
- Faculty 56-Slot Phase 2
- Block Quality Report Tests
- Fairness API Endpoints

---

## URLs (when dev server running on port 3002)

- Dense flow: http://localhost:3002/stigmergy-flow.html
- N-1/N-2: http://localhost:3002/n1-contingency.html
- R3F version: http://localhost:3002/admin/visualizations/stigmergy-flow

---

*Session incomplete - IDE communication issues*
