# Session: Bottleneck Flow + Hopfield Status Report

**Date:** 2026-01-18
**Terminal:** Alpha (this session)

---

## Bottleneck Flow Visualizer

### What's DONE (14 files created)

```
frontend/src/features/bottleneck-flow/
├── index.ts                    # Public exports
├── types.ts                    # TypeScript interfaces
├── constants.ts                # Colors, sizes, lane configs
├── BottleneckFlowVisualizer.tsx # Main wrapper
├── components/
│   ├── index.ts
│   ├── SimulationScene.tsx     # R3F scene
│   ├── LaneVisual.tsx          # Lane floors + particles
│   ├── FacultyNode.tsx         # Faculty spheres
│   ├── TraineeNode.tsx         # Trainee orbits
│   ├── DynamicConnection.tsx   # Lines between nodes
│   └── UIOverlay.tsx           # HUD, controls, metrics
└── hooks/
    ├── index.ts
    ├── useBottleneckData.ts    # Transform API → viz format
    └── useBottleneckSimulation.ts # Simulation state
```

### What's NOT DONE

**Tab integration was reverted by linter/formatter.**

Need to re-apply to `frontend/src/app/admin/labs/optimization/page.tsx`:

1. Add `Network` to lucide-react import (line 23)
2. Add dynamic import for `BottleneckFlowVisualizer` (after line 92)
3. Add `'bottleneck'` to `TabId` union (line 94)
4. Add tab object to `TABS` array (after bridge entry)
5. Add render case `{activeTab === 'bottleneck' && <BottleneckFlowVisualizer />}`

---

## Hopfield Energy Visualizer

### What's DONE (Infrastructure)

| Component | File | Status |
|-----------|------|--------|
| API Functions | `frontend/src/api/exotic-resilience.ts` | ✅ `findNearbyAttractors()`, `measureBasinDepth()`, `detectSpuriousAttractors()` |
| Hooks | `frontend/src/hooks/useHopfield.ts` | ✅ `useHopfieldEnergy()`, `useNearbyAttractors()`, etc. |
| Visualizer Props | `frontend/src/features/hopfield-energy/` | ✅ Accepts `apiData` prop, has metrics panel |

### What's NOT DONE (Page Integration)

1. `/admin/labs/optimization` page doesn't call the Hopfield hooks
2. Nothing passes `apiData` to `HopfieldVisualizer`
3. 3D ball/surface still uses local `computeEnergy()`, not API values
4. Need wrapper component (like `StigmergyFlowWrapper`) to:
   - Call `useHopfieldEnergy()` with current coverage/balance
   - Pass result as `apiData` prop to visualizer

---

## Next Steps Priority

1. **Bottleneck Tab:** Re-apply 5 line changes to optimization page
2. **Hopfield Integration:** Create wrapper component that calls hooks and passes data to visualizer

---

## Files Reference

- Feature: `frontend/src/features/bottleneck-flow/` (complete)
- Target: `frontend/src/app/admin/labs/optimization/page.tsx` (needs tab integration)
- Hopfield: `frontend/src/features/hopfield-energy/` (needs page wrapper)
