# ADR: 3D Visualization Library Evaluation

> **Status:** Accepted
> **Date:** 2026-01-18
> **Decision:** Stay with Three.js/R3F, selectively add Theatre.js and Deck.gl
> **Context:** Evaluate alternative 3D libraries for schedule visualization

---

## Executive Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VISUALIZATION LIBRARY DECISION                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   KEEP ━━━━━━━━━━━━━━━━┓                                                │
│   ┌──────────────────┐ ┃  ADD (TARGETED) ━━━━━━━━━━━━━┓                 │
│   │  Three.js        │ ┃  ┌─────────────┐ ┌──────────┐┃                 │
│   │  React Three     │ ┃  │ Theatre.js  │ │ Deck.gl  │┃                 │
│   │  Fiber           │ ┃  │ (animation) │ │ (maps)   │┃                 │
│   │  Recharts        │ ┃  └─────────────┘ └──────────┘┃                 │
│   │  Plotly          │ ┃                              ┃                 │
│   └──────────────────┘ ┃  REJECT ━━━━━━━━━━━━━━━━━━━━━┛                 │
│                        ┃  ┌───────────┐ ┌──────┐ ┌──────┐              │
│                        ┃  │ Babylon.js│ │PixiJS│ │OGL.js│              │
│                        ┃  │ (overkill)│ │(niche)│ │(dup) │              │
│                        ┃  └───────────┘ └──────┘ └──────┘              │
│                        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Current Visualization Stack

### Installed Libraries (package.json)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURRENT TECH STACK                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────── 3D LAYER ──────────────────────┐             │
│  │                                                        │             │
│  │  three.js ──────────► @react-three/fiber ◄─────┐      │             │
│  │    v0.164.1              v8.18.0               │      │             │
│  │        │                     │                 │      │             │
│  │        │            ┌────────┴────────┐        │      │             │
│  │        │            │                 │        │      │             │
│  │        ▼            ▼                 ▼        │      │             │
│  │  @react-three/  @react-three/  @react-spring/ │      │             │
│  │  postprocessing    drei           three       │      │             │
│  │    v3.0.4        v9.122.0        v9.7.3       │      │             │
│  │                                                        │             │
│  └────────────────────────────────────────────────────────┘             │
│                                                                         │
│  ┌─────────────────────── 2D LAYER ──────────────────────┐             │
│  │                                                        │             │
│  │  recharts ────────────────────────────► Charts        │             │
│  │    v3.6.0                                              │             │
│  │                                                        │             │
│  │  plotly.js + react-plotly.js ─────────► Interactive   │             │
│  │    v3.3.1     v2.6.0                                   │             │
│  │                                                        │             │
│  │  framer-motion ───────────────────────► Animation     │             │
│  │    v12.23.26                                           │             │
│  │                                                        │             │
│  └────────────────────────────────────────────────────────┘             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Existing 3D Visualizations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ACTIVE 3D VISUALIZATION COMPONENTS                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐   ┌──────────────────────┐                   │
│  │  VoxelScheduleView3D │   │  FoamTopologyViz     │                   │
│  │  ────────────────────│   │  ────────────────────│                   │
│  │  • 50K+ voxels @60fps│   │  • Force-directed    │                   │
│  │  • WebGL instancing  │   │  • Custom physics    │                   │
│  │  • Conflict pulsing  │   │  • Iridescent shaders│                   │
│  │  • 2D/3D toggle      │   │  • T1 swap events    │                   │
│  │  • Real-time updates │   │  • Stress films      │                   │
│  └──────────────────────┘   └──────────────────────┘                   │
│                                                                         │
│  ┌──────────────────────┐   ┌──────────────────────┐                   │
│  │  HolographicManifold │   │  StigmergyFlow       │                   │
│  │  ────────────────────│   │  ────────────────────│                   │
│  │  • N-dim projection  │   │  • Particle system   │                   │
│  │  • Canvas 2D (fast)  │   │  • Flow simulation   │                   │
│  │  • Layer filtering   │   │  • WebGL particles   │                   │
│  │  • Constraint viz    │   │  • Connection lines  │                   │
│  └──────────────────────┘   └──────────────────────┘                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Library Evaluation Matrix

### Decision Table

```
┌────────────────┬─────────┬───────────┬────────────┬─────────────────────┐
│ Library        │ Verdict │ Priority  │ Difficulty │ Rationale           │
├────────────────┼─────────┼───────────┼────────────┼─────────────────────┤
│ Three.js/R3F   │ KEEP ✓  │ —         │ —          │ Already invested    │
│ Recharts       │ KEEP ✓  │ —         │ —          │ 2D charts covered   │
│ Plotly         │ KEEP ✓  │ —         │ —          │ Interactive viz     │
├────────────────┼─────────┼───────────┼────────────┼─────────────────────┤
│ Theatre.js     │ ADD ✓   │ P2 Medium │ ★★☆☆☆     │ Animation timeline  │
│ Deck.gl        │ ADD ✓   │ P3 Low    │ ★★★☆☆     │ Geospatial only     │
├────────────────┼─────────┼───────────┼────────────┼─────────────────────┤
│ Babylon.js     │ REJECT  │ —         │ ★★★★★     │ Full rewrite needed │
│ PixiJS         │ REJECT  │ —         │ ★★★☆☆     │ 2D only, niche use  │
│ OGL.js         │ REJECT  │ —         │ ★★★★☆     │ Duplicates R3F      │
│ Rapier         │ DEFER   │ P4 Future │ ★★★☆☆     │ If physics needed   │
└────────────────┴─────────┴───────────┴────────────┴─────────────────────┘
```

---

## Library Deep Dive

### 1. Babylon.js — REJECTED

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BABYLON.JS EVALUATION                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  What It Is:                                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Full Game Engine (Microsoft)                                │       │
│  │  • Built-in physics (Havok)                                  │       │
│  │  • Built-in GUI system                                       │       │
│  │  • Built-in inspector/debugger                               │       │
│  │  • Native TypeScript                                         │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Why NOT for This Project:                                              │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  ✗ Would require rewriting ALL existing R3F components      │       │
│  │  ✗ Game engine overhead for non-game application            │       │
│  │  ✗ Different paradigm (imperative vs React declarative)     │       │
│  │  ✗ Physics engine unnecessary (custom foam physics exists)  │       │
│  │  ✗ Bundle size increase for unused features                 │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Migration Cost:                                                        │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Files to Rewrite: 4 major components + all 3D utilities    │       │
│  │  Estimated LOC: ~3,000+ lines                                │       │
│  │  Risk: HIGH (tested code → untested code)                    │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  VERDICT: ✗ REJECTED — Migration cost exceeds benefits                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. PixiJS — REJECTED (Niche Use Case)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PIXIJS EVALUATION                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  What It Is:                                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  2D WebGL Rendering Engine                                   │       │
│  │  • Hardware-accelerated sprites                              │       │
│  │  • 10,000+ sprites at 60 FPS                                 │       │
│  │  • Sprite sheets, filters, masks                             │       │
│  │  • Native TypeScript                                         │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Potential Use Case:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐               │       │
│  │  │ Mon │ Tue │ Wed │ Thu │ Fri │ Sat │ Sun │   High-perf   │       │
│  │  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┤   2D schedule │       │
│  │  │░░░░░│█████│░░░░░│█████│░░░░░│     │     │   grid with   │       │
│  │  │░░░░░│█████│░░░░░│█████│░░░░░│     │     │   1000s of    │       │
│  │  │░░░░░│█████│░░░░░│█████│░░░░░│     │     │   cells       │       │
│  │  └─────┴─────┴─────┴─────┴─────┴─────┴─────┘               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Why NOT for This Project:                                              │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  ✗ 2D only — doesn't help with 3D visualizations            │       │
│  │  ✗ Recharts already handles 2D charts well                  │       │
│  │  ✗ HolographicManifold already uses fast Canvas 2D          │       │
│  │  ✗ Niche use: only if Recharts hits performance limits      │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  VERDICT: ✗ REJECTED — Only reconsider if 2D performance degrades      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Deck.gl — APPROVED (Conditional)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DECK.GL EVALUATION                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  What It Is:                                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Large-Scale Geospatial Data Visualization (Uber)            │       │
│  │  • Render millions of data points on maps                    │       │
│  │  • Layer-based architecture (hexagons, arcs, scatter)        │       │
│  │  • React integration via react-map-gl                        │       │
│  │  • Native TypeScript                                         │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Use Cases for Residency Scheduler:                                     │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                                                               │       │
│  │         ┌──────────────────────────────────────┐             │       │
│  │         │         TAMC Main Hospital           │             │       │
│  │         │              ◉                       │             │       │
│  │         │             /│\                      │             │       │
│  │         │            / │ \                     │             │       │
│  │         │           /  │  \  Rotation Arcs     │             │       │
│  │         │          ◎   ◎   ◎                   │             │       │
│  │         │       Clinic Outpost Satellite       │             │       │
│  │         │                                       │             │       │
│  │         └──────────────────────────────────────┘             │       │
│  │                                                               │       │
│  │  • Visualize multi-site rotation coverage                    │       │
│  │  • Show resident commute/travel patterns                     │       │
│  │  • Display facility capacity heatmaps                        │       │
│  │  • Overlay deployment/TDY locations (sanitized)              │       │
│  │                                                               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Implementation Sketch:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  // Example: Multi-site coverage visualization               │       │
│  │  import { DeckGL } from '@deck.gl/react';                    │       │
│  │  import { ArcLayer, ScatterplotLayer } from '@deck.gl/layers';│       │
│  │                                                               │       │
│  │  <DeckGL                                                     │       │
│  │    layers={[                                                 │       │
│  │      new ScatterplotLayer({                                  │       │
│  │        data: facilities,                                     │       │
│  │        getPosition: d => [d.lon, d.lat],                     │       │
│  │        getRadius: d => d.capacity * 100,                     │       │
│  │        getFillColor: d => d.coverageColor                    │       │
│  │      }),                                                     │       │
│  │      new ArcLayer({                                          │       │
│  │        data: rotationPaths,                                  │       │
│  │        getSourcePosition: d => d.from,                       │       │
│  │        getTargetPosition: d => d.to,                         │       │
│  │        getSourceColor: [0, 128, 255],                        │       │
│  │        getTargetColor: [255, 128, 0]                         │       │
│  │      })                                                      │       │
│  │    ]}                                                        │       │
│  │  />                                                          │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Priority: P3 (Low) — Only if geospatial features requested            │
│  Difficulty: ★★★☆☆ — New paradigm but good React integration           │
│                                                                         │
│  VERDICT: ✓ APPROVED — Add when geospatial visualization needed        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4. OGL.js — REJECTED

```
┌─────────────────────────────────────────────────────────────────────────┐
│  OGL.JS EVALUATION                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  What It Is:                                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Minimal WebGL Library ("Three.js Lite")                     │       │
│  │  • Tiny bundle size (~30KB vs Three.js ~600KB)               │       │
│  │  • Similar API to Three.js                                   │       │
│  │  • Closer to raw WebGL                                       │       │
│  │  • Good for custom shaders                                   │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Why NOT for This Project:                                              │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                                                               │       │
│  │    Three.js ◄──── Already Using ────► R3F Integration        │       │
│  │        │                                   │                  │       │
│  │        │         Would Create              │                  │       │
│  │        │            Split                  │                  │       │
│  │        ▼              ▼                    ▼                  │       │
│  │     OGL.js ════ Fragmented ════ Inconsistent Codebase        │       │
│  │                  Ecosystem                                    │       │
│  │                                                               │       │
│  │  ✗ Bundle size savings irrelevant (R3F already loaded)       │       │
│  │  ✗ No React integration (would need custom bindings)         │       │
│  │  ✗ Smaller ecosystem (fewer helpers, examples)               │       │
│  │  ✗ Would fragment the rendering layer                        │       │
│  │                                                               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  VERDICT: ✗ REJECTED — Duplicates existing capability                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5. Theatre.js — APPROVED

```
┌─────────────────────────────────────────────────────────────────────────┐
│  THEATRE.JS EVALUATION                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  What It Is:                                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Animation & Motion Design Library                           │       │
│  │  • Visual timeline editor (like After Effects)               │       │
│  │  • Works directly with Three.js/R3F                          │       │
│  │  • Keyframe-based animation                                  │       │
│  │  • Export animations as JSON                                 │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Visual Timeline Editor:                                                │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  ┌───────────────────────────────────────────────────────┐  │       │
│  │  │ Timeline                                    [▶] [⏸]  │  │       │
│  │  ├───────────────────────────────────────────────────────┤  │       │
│  │  │ Camera.position ──●───────●─────────────●────────────│  │       │
│  │  │ Camera.rotation ────●─────────●───────────────●──────│  │       │
│  │  │ Voxel.opacity   ●─────────────────●──────────────────│  │       │
│  │  │ Bloom.intensity ──────●──────────────────●───────────│  │       │
│  │  ├───────────────────────────────────────────────────────┤  │       │
│  │  │ 0s      1s      2s      3s      4s      5s      6s   │  │       │
│  │  └───────────────────────────────────────────────────────┘  │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Use Cases for Residency Scheduler:                                     │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                                                               │       │
│  │  1. SCHEDULE TRANSITION ANIMATIONS                           │       │
│  │     ┌────────┐         ┌────────┐                            │       │
│  │     │ Week 1 │ ──────► │ Week 2 │  Smooth camera fly-through │       │
│  │     └────────┘         └────────┘  with voxel morphing       │       │
│  │                                                               │       │
│  │  2. 2D → 3D VIEW TOGGLE                                      │       │
│  │     ┌────────┐         ┌────────┐                            │       │
│  │     │ ═══════│ ──────► │  ╱╲    │  Animated perspective      │       │
│  │     │ ═══════│         │ ╱  ╲   │  shift with easing         │       │
│  │     └────────┘         └────────┘                            │       │
│  │                                                               │       │
│  │  3. CONFLICT HIGHLIGHT SEQUENCES                             │       │
│  │     ◯ ──────► ◉ ──────► ◯  Orchestrated pulse + zoom        │       │
│  │                                                               │       │
│  │  4. ONBOARDING TOURS                                         │       │
│  │     Camera path through 3D schedule with annotations         │       │
│  │                                                               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Implementation Sketch:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  import { getProject, types } from '@theatre/core';          │       │
│  │  import { SheetProvider, editable as e } from '@theatre/r3f';│       │
│  │                                                               │       │
│  │  const project = getProject('ScheduleViz');                  │       │
│  │  const sheet = project.sheet('View Transitions');            │       │
│  │                                                               │       │
│  │  // In VoxelScheduleView3D.tsx:                              │       │
│  │  <SheetProvider sheet={sheet}>                               │       │
│  │    <e.perspectiveCamera                                      │       │
│  │      theatreKey="camera"                                     │       │
│  │      makeDefault                                             │       │
│  │      position={[0, 5, 10]}                                   │       │
│  │    />                                                        │       │
│  │    <e.group theatreKey="voxelGrid">                          │       │
│  │      <InstancedVoxelRenderer ... />                          │       │
│  │    </e.group>                                                │       │
│  │  </SheetProvider>                                            │       │
│  │                                                               │       │
│  │  // Trigger animation programmatically:                      │       │
│  │  sheet.sequence.play({ range: [0, 3] });                     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Priority: P2 (Medium) — High polish, good UX impact                   │
│  Difficulty: ★★☆☆☆ — Direct R3F integration, good docs                 │
│                                                                         │
│  VERDICT: ✓ APPROVED — Add for polished animation sequences            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6. Rapier (Physics) — DEFERRED

```
┌─────────────────────────────────────────────────────────────────────────┐
│  RAPIER EVALUATION                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  What It Is:                                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Rust-based Physics Engine (WASM)                            │       │
│  │  • Rigid body dynamics                                       │       │
│  │  • Collision detection                                       │       │
│  │  • Deterministic simulation                                  │       │
│  │  • @react-three/rapier for R3F integration                   │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Current State:                                                         │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                                                               │       │
│  │  FoamTopologyVisualizer uses CUSTOM PHYSICS:                 │       │
│  │                                                               │       │
│  │  // Current implementation (works well)                      │       │
│  │  const applyForces = () => {                                 │       │
│  │    bubbles.forEach(bubble => {                               │       │
│  │      // Repulsion between bubbles                            │       │
│  │      const repulsion = calculateRepulsion(bubble, others);   │       │
│  │      // Center gravity                                       │       │
│  │      const gravity = calculateCenterPull(bubble);            │       │
│  │      // Damping                                              │       │
│  │      bubble.velocity *= DAMPING;                             │       │
│  │      // Apply                                                │       │
│  │      bubble.position.add(repulsion).add(gravity);            │       │
│  │    });                                                       │       │
│  │  };                                                          │       │
│  │                                                               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Why DEFER:                                                             │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  ✓ Custom physics is domain-specific and working             │       │
│  │  ✓ Rapier adds WASM complexity                               │       │
│  │  ? Only useful if we need rigid body collisions              │       │
│  │  ? Consider if adding "physical schedule manipulation"       │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Priority: P4 (Future) — Only if interactive physics needed            │
│  Difficulty: ★★★☆☆ — WASM setup, but good R3F bindings                 │
│                                                                         │
│  VERDICT: ⏸ DEFERRED — Revisit if interactive physics required         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Priority Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRIORITY MATRIX                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│         HIGH IMPACT                                                     │
│              ▲                                                          │
│              │                                                          │
│              │   ┌───────────────┐                                      │
│              │   │  Theatre.js   │  ◄── P2: Add for polish             │
│              │   │  (Animation)  │                                      │
│              │   └───────────────┘                                      │
│              │                                                          │
│              │   ┌───────────────┐                                      │
│              │   │  R3F v9       │  ◄── P1: Upgrade (unblocks          │
│              │   │  Upgrade      │       postprocessing)                │
│              │   └───────────────┘                                      │
│              │                                                          │
│  LOW ────────┼───────────────────────────────────────────► HIGH        │
│  EFFORT      │                                               EFFORT     │
│              │                                                          │
│              │   ┌───────────────┐                                      │
│              │   │   Deck.gl     │  ◄── P3: Add if geospatial needed   │
│              │   │   (Maps)      │                                      │
│              │   └───────────────┘                                      │
│              │                                                          │
│              │   ┌───────────────┐                                      │
│              │   │   Rapier      │  ◄── P4: Defer for now              │
│              │   │   (Physics)   │                                      │
│              │   └───────────────┘                                      │
│              │                                                          │
│              ▼                                                          │
│         LOW IMPACT                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: R3F v9 Upgrade (P1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: REACT THREE FIBER v9 UPGRADE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Current Blocker:                                                       │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  @react-three/postprocessing v3 requires R3F v9             │       │
│  │  Currently on R3F v8.18.0                                    │       │
│  │  Postprocessing effects DISABLED in VoxelScheduleView3D     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Steps:                                                                 │
│  ┌────┐                                                                 │
│  │ 1  │ npm install @react-three/fiber@^9.0.0                          │
│  └────┘                                                                 │
│  ┌────┐                                                                 │
│  │ 2  │ Update @react-three/drei to compatible version                 │
│  └────┘                                                                 │
│  ┌────┐                                                                 │
│  │ 3  │ Test all 4 existing 3D visualizations                          │
│  └────┘                                                                 │
│  ┌────┐                                                                 │
│  │ 4  │ Re-enable postprocessing in VoxelScheduleView3D                │
│  └────┘                                                                 │
│  ┌────┐                                                                 │
│  │ 5  │ Add Bloom, Vignette effects to all 3D scenes                   │
│  └────┘                                                                 │
│                                                                         │
│  Difficulty: ★★☆☆☆                                                      │
│  Risk: Medium (API changes between v8 and v9)                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Theatre.js Integration (P2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: THEATRE.JS INTEGRATION                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Install:                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  npm install @theatre/core @theatre/studio @theatre/r3f     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Integration Architecture:                                              │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                                                               │       │
│  │  frontend/src/                                                │       │
│  │  └── lib/                                                     │       │
│  │      └── theatre/                                             │       │
│  │          ├── projects/                                        │       │
│  │          │   ├── schedule-viz.json    # Exported animations  │       │
│  │          │   └── onboarding.json                              │       │
│  │          ├── sheets/                                          │       │
│  │          │   ├── view-transitions.ts  # 2D↔3D transitions    │       │
│  │          │   ├── conflict-zoom.ts     # Conflict highlights  │       │
│  │          │   └── week-scrub.ts        # Timeline scrubbing   │       │
│  │          └── TheatreProvider.tsx      # Context wrapper       │       │
│  │                                                               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  First Animation Target: VoxelScheduleView3D 2D↔3D Toggle              │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                                                               │       │
│  │   BEFORE (current):                                          │       │
│  │   ┌──────────┐         ┌──────────┐                          │       │
│  │   │  2D View │ ──────► │  3D View │  Instant swap            │       │
│  │   └──────────┘         └──────────┘                          │       │
│  │                                                               │       │
│  │   AFTER (with Theatre.js):                                   │       │
│  │   ┌──────────┐    ╭─────╮    ┌──────────┐                    │       │
│  │   │  2D View │ ───│ 1.5s│───►│  3D View │  Animated camera   │       │
│  │   └──────────┘    │ ease│    └──────────┘  + voxel extrusion │       │
│  │                   ╰─────╯                                     │       │
│  │                                                               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Difficulty: ★★☆☆☆                                                      │
│  Prerequisite: Phase 1 (R3F v9)                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Deck.gl for Geospatial (P3 — Conditional)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: DECK.GL INTEGRATION (IF NEEDED)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Trigger Conditions:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  ✓ Multi-site rotation visualization requested               │       │
│  │  ✓ Facility capacity mapping needed                          │       │
│  │  ✓ Travel pattern analysis for residents                     │       │
│  │  ✓ Geographic coverage optimization                          │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Install:                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  npm install deck.gl @deck.gl/react @deck.gl/layers         │       │
│  │  npm install react-map-gl maplibre-gl                        │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Example Component:                                                     │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  frontend/src/features/facility-map/                         │       │
│  │  ├── FacilityMapView.tsx        # Main map component         │       │
│  │  ├── layers/                                                  │       │
│  │  │   ├── FacilityLayer.ts       # Hospital markers           │       │
│  │  │   ├── RotationArcLayer.ts    # Resident movement arcs     │       │
│  │  │   └── CoverageHexLayer.ts    # Coverage density hexbins   │       │
│  │  └── hooks/                                                   │       │
│  │      └── useFacilityData.ts     # API integration            │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Note: Requires facility coordinate data (lat/lon)                     │
│  OPSEC: Sanitize exact military facility locations                     │
│                                                                         │
│  Difficulty: ★★★☆☆                                                      │
│  Prerequisite: Backend facility location API                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Difficulty Assessment Key

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DIFFICULTY RATING SCALE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ★☆☆☆☆  TRIVIAL                                                         │
│          • npm install + follow docs                                    │
│          • <1 day effort                                                │
│          • No architectural changes                                     │
│                                                                         │
│  ★★☆☆☆  EASY                                                            │
│          • Some integration work needed                                 │
│          • 1-3 days effort                                              │
│          • Minor component updates                                      │
│                                                                         │
│  ★★★☆☆  MODERATE                                                        │
│          • New patterns to learn                                        │
│          • 3-7 days effort                                              │
│          • New feature area                                             │
│                                                                         │
│  ★★★★☆  HARD                                                            │
│          • Significant refactoring                                      │
│          • 1-2 weeks effort                                             │
│          • Cross-cutting changes                                        │
│                                                                         │
│  ★★★★★  VERY HARD                                                       │
│          • Major rewrite/migration                                      │
│          • 2+ weeks effort                                              │
│          • High risk of regressions                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Decision Summary

| Library | Decision | Priority | Difficulty | Next Action |
|---------|----------|----------|------------|-------------|
| **R3F v9** | UPGRADE | P1 | ★★☆☆☆ | Unblocks postprocessing |
| **Theatre.js** | ADD | P2 | ★★☆☆☆ | After R3F upgrade |
| **Deck.gl** | ADD (conditional) | P3 | ★★★☆☆ | When geospatial needed |
| **Rapier** | DEFER | P4 | ★★★☆☆ | If physics requested |
| **Babylon.js** | REJECT | — | ★★★★★ | No action |
| **PixiJS** | REJECT | — | ★★★☆☆ | No action |
| **OGL.js** | REJECT | — | ★★★★☆ | No action |

---

## Files Referenced

| File | Purpose |
|------|---------|
| `frontend/package.json` | Current dependencies |
| `frontend/src/features/voxel-schedule/VoxelScheduleView3D.tsx` | Main 3D component |
| `frontend/src/components/scheduling/FoamTopologyVisualizer.tsx` | Custom physics |
| `frontend/src/features/holographic-hub/HolographicManifold.tsx` | Canvas 2D viz |
| `frontend/src/app/admin/visualizations/stigmergy-flow/` | Particle system |

---

*Document created: 2026-01-18 | Author: Claude (AI-assisted evaluation)*
