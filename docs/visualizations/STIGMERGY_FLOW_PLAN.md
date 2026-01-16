# Stigmergy Flow Visualization Plan

> **Status:** In Progress
> **Created:** 2026-01-15
> **Concept:** Bioluminescent particle system representing schedule assignments flowing through spacetime

---

## Concept: "Stigmergy Flow"

*Named after the ant pheromone trails in the resilience framework*

A bioluminescent particle system representing schedule assignments flowing through spacetime.

## Exotic Visual Effects

| Effect | What It Represents | Implementation |
|--------|-------------------|----------------|
| **Bioluminescent trails** | Assignment history | Particle trails with glow shader, color = rotation type |
| **Magnetic field lines** | Supervision relationships | Curved Bezier tubes connecting faculty↔resident particles |
| **Gravitational lensing** | High workload zones | Shader distortion near overloaded nodes |
| **Quantum uncertainty halos** | Unconfirmed/draft assignments | Particles with probabilistic opacity, fuzzy edges |
| **Plasma vortices** | Conflicts/violations | Swirling red particle clusters at collision points |
| **Aurora ribbons** | ACGME compliance flow | Green/yellow/red ribbon following the "safe path" |

## Particle Types

```
🔵 Blue particles   = Clinic assignments (steady flow)
🟢 Green particles  = FMIT rotations (clustered bursts)
🟡 Yellow particles = Call shifts (night-side flow)
🔴 Red particles    = Conflicts (collision sparks)
⚪ White particles  = Unassigned slots (ghost particles)
```

## Scene Structure

```
┌─────────────────────────────────────────────────────────┐
│                    TIME AXIS (Z)                         │
│         ══════════════════════════════════►              │
│                                                          │
│    ┌──────┐     ┌──────┐     ┌──────┐                   │
│    │ Mon  │────▶│ Tue  │────▶│ Wed  │ ...               │
│    └──┬───┘     └──┬───┘     └──┬───┘                   │
│       │            │            │                        │
│    ┌──▼───┐     ┌──▼───┐     ┌──▼───┐                   │
│    │  AM  │     │  AM  │     │  AM  │  ← Y axis         │
│    │  PM  │     │  PM  │     │  PM  │    (time of day)  │
│    │ Call │     │ Call │     │ Call │                   │
│    └──────┘     └──────┘     └──────┘                   │
│                                                          │
│         X axis = faculty/resident positions              │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
frontend/src/app/admin/visualizations/
├── stigmergy-flow/
│   ├── page.tsx              # Next.js page wrapper
│   ├── StigmergyScene.tsx    # Main R3F canvas component
│   ├── components/
│   │   ├── ParticleSystem.tsx   # Particle system with shaders
│   │   ├── GridGuides.tsx       # Spacetime grid
│   │   └── HUD.tsx              # Heads-up display overlay
│   ├── shaders/
│   │   └── particle.ts          # GLSL shaders as strings
│   └── types.ts              # TypeScript interfaces
```

## TypeScript Interfaces

```typescript
interface FlowParticle {
  id: string;
  type: 'clinic' | 'fmit' | 'call' | 'conflict' | 'unassigned';
  personId: string;
  position: { x: number; y: number; z: number };
  velocity: { x: number; y: number; z: number };
  connections: string[]; // IDs of connected particles
  intensity: number; // 0-1 for glow brightness
}
```

## Gemini Prototype Features

The initial prototype includes:
- 2,500 particles across 90 days
- Color-coded by assignment type
- Custom GLSL shaders for glow effect
- Additive blending for bioluminescence
- OrbitControls for camera manipulation
- Dynamic date display based on camera Z position
- AI panel with Gemini API integration for insights

## Verification Steps

1. Run `npm run dev` in frontend
2. Navigate to `/admin/visualizations/stigmergy-flow`
3. Verify particles render with trails
4. Verify OrbitControls work (drag to rotate)
5. Check console for WebGL errors

---

**Risk:** Zero - isolated frontend component, no backend changes, can be feature-flagged or deleted
