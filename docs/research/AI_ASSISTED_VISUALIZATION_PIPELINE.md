# AI-Assisted Visualization Pipeline

> **The Workflow Behind Novel Data Representations**
> **Date:** January 16, 2026
> **Status:** Active Research Pattern

---

## Overview

This document describes the AI-assisted development pipeline used to create novel visualization components for the Residency Scheduler. The process demonstrates how human intuition combined with multiple AI systems can rapidly prototype complex 3D/4D data representations.

---

## The Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI-ASSISTED VISUALIZATION PIPELINE               │
└─────────────────────────────────────────────────────────────────────┘

     ┌──────────┐      ┌──────────────┐      ┌──────────────┐
     │  HUMAN   │      │   GEMINI     │      │   GOOGLE     │
     │ INSIGHT  │ ───▶ │   (Ideas)    │ ───▶ │  AI STUDIO   │
     └──────────┘      └──────────────┘      └──────────────┘
          │                   │                     │
          │                   ▼                     ▼
          │           ┌──────────────┐      ┌──────────────┐
          │           │   DESIGN     │      │    CODE      │
          │           │   DOCUMENT   │      │  GENERATION  │
          │           └──────────────┘      └──────────────┘
          │                   │                     │
          │                   └─────────┬───────────┘
          │                             ▼
          │                   ┌──────────────────┐
          │                   │   CLAUDE CODE    │
          │                   │  (Integration)   │
          │                   └──────────────────┘
          │                             │
          │                             ▼
          │                   ┌──────────────────┐
          └──────────────────▶│   ITERATION &    │
                              │   REFINEMENT     │
                              └──────────────────┘
```

---

## Stage 1: Human Insight (The Spark)

### The Pattern

1. **Deep domain immersion** - Years working with the scheduling problem
2. **Random input** - Reading an article about foam physics (Penn Engineering research)
3. **Pattern recognition** - "This is the shape of my problem"
4. **Intuitive connection** - Feeling the isomorphism before articulating it

### Example: Foam Topology

> "I read about soap bubbles continuously reorganizing in patterns that mirror how AI systems learn. My gut said: that's what schedule swaps look like. Bubbles under pressure, films thinning at constraint boundaries, T1 transitions as natural swap points."

This isn't random—it's **prepared mind meeting information**. The insight emerges from saturation in the domain.

---

## Stage 2: Gemini (Idea Elaboration)

### Purpose

Use Google's Gemini to explore and elaborate the initial insight:
- Research the physics foundations
- Identify mathematical connections
- Generate technical specifications
- Explore implementation approaches

### Workflow

```
Input: "I want to visualize medical residency schedules as foam bubbles,
        where T1 transitions represent natural swap opportunities.
        Help me understand the physics and design a visualization."

Gemini Output:
- Foam physics primer (Plateau's laws, T1 events, coarsening)
- Mathematical model mapping (pressure → workload, films → constraints)
- Visualization requirements (3D, physics simulation, interactive)
- Technical considerations (Three.js, React, WebGL)
```

### Value

Gemini excels at:
- Broad knowledge synthesis
- Research and explanation
- Exploring possibility spaces
- Generating technical context

---

## Stage 3: Google AI Studio (Code Generation)

### Purpose

Use Google AI Studio for rapid code generation:
- Full component scaffolding
- Three.js/React integration
- Physics simulation code
- UI/UX implementation

### Workflow

```
Input: [Gemini output + specific requirements]
       "Generate a Three.js visualization component for foam topology
        scheduling with these specifications..."

AI Studio Output:
- Complete React component (~500 lines)
- Three.js scene setup with physics
- Material and lighting configuration
- Interactive controls and UI panels
```

### Value

AI Studio excels at:
- Rapid code generation
- Boilerplate elimination
- Framework-specific patterns
- Complex integrations

---

## Stage 4: Claude Code (Integration & Refinement)

### Purpose

Use Claude Code for:
- Codebase integration
- Type safety and patterns
- Testing and validation
- Documentation and explanation
- Deeper technical insight

### Workflow

```
Input: [Generated components + codebase context]
       "Integrate these visualizations into the admin routes,
        add ProtectedRoute wrappers, update navigation..."

Claude Code Output:
- Admin page wrappers
- Navigation integration
- Dynamic imports (SSR handling)
- Documentation
- Technical analysis (quantum computing connection!)
```

### Value

Claude Code excels at:
- Codebase understanding
- Pattern consistency
- Deep technical analysis
- Collaborative refinement
- Emergent insight discovery

---

## Stage 5: Iteration & Refinement

### The Feedback Loop

Human reviews output → identifies gaps → returns to appropriate AI:

| Gap Type | Return To |
|----------|-----------|
| Conceptual clarity | Gemini |
| Code structure | AI Studio |
| Integration issues | Claude Code |
| New insight | Human reflection |

### Example Iteration

```
1. Claude Code integrates visualization
2. Human notices: "The foam model maps to quantum annealing"
3. Discussion with Claude Code reveals deeper connection
4. Document insight for future reference
5. Consider quantum computing research direction
```

---

## Artifacts Produced

### This Session (January 16, 2026)

| Artifact | Type | Location |
|----------|------|----------|
| FoamTopologyVisualizer | Component | `frontend/src/components/scheduling/FoamTopologyVisualizer.tsx` |
| ResilienceOverseerDashboard | Component | `frontend/src/components/scheduling/ResilienceOverseerDashboard.tsx` |
| Foam Topology Admin Page | Route | `frontend/src/app/admin/foam-topology/page.tsx` |
| Resilience Overseer Admin Page | Route | `frontend/src/app/admin/resilience-overseer/page.tsx` |
| Design Document | Doc | `docs/exotic/FOAM_TOPOLOGY_SCHEDULER.md` |
| Philosophy Document | Doc | `docs/research/FOAM_TOPOLOGY_AND_DIMENSIONAL_DATA_REPRESENTATION.md` |
| This Pipeline Document | Doc | `docs/research/AI_ASSISTED_VISUALIZATION_PIPELINE.md` |

---

## The Two Visualizations

### 1. Foam Topology Visualizer

**Purpose:** 3D visualization of schedule as foam bubbles

**Physics Model:**
- Bubbles = Assignment units (resident + block + rotation)
- Bubble volume = Workload
- Bubble pressure = Capacity utilization (under/over-loaded)
- Films = Constraint interfaces between adjacent assignments
- T1 events = Natural swap opportunities

**Features:**
- Three.js 3D rendering with physics simulation
- Interactive bubble selection
- T1 candidate detection and execution
- Stress histogram
- Real-time pressure visualization

**Technical:**
- `@react-three/fiber` for React integration
- `@react-three/drei` for helpers (OrbitControls, Html labels)
- Physical material with iridescence for soap bubble effect
- Force-directed layout simulation

### 2. Resilience Overseer Dashboard

**Purpose:** Military ops-style command center for system health

**Metrics:**
- DEFCON gauge (N-1/N-2 contingency status)
- Burnout Rt (epidemic model of fatigue spread)
- Active threats (residents approaching violations)
- Coverage map (rotation saturation)
- Circuit breakers (Netflix Hystrix pattern)

**Aesthetic:**
- Military command center visual language
- Zulu time, uppercase labels, monospace fonts
- Color-coded status indicators
- Real-time countdown timers

**Technical:**
- Pure React (no Three.js dependency)
- CSS-based animations
- Live data simulation

---

## Why This Works

### Complementary Strengths

| Actor | Strength | Role |
|-------|----------|------|
| Human | Pattern recognition, domain knowledge, intuition | Spark, direction, judgment |
| Gemini | Broad knowledge, research, explanation | Exploration, elaboration |
| AI Studio | Rapid code generation, scaffolding | Production, implementation |
| Claude Code | Deep analysis, integration, insight | Refinement, connection |

### The Emergent Property

No single actor produces the final result. The visualization emerges from the *interaction*:

1. Human sees foam → scheduling connection
2. Gemini elaborates the physics
3. AI Studio generates the code
4. Claude Code integrates and discovers quantum connection
5. Human validates: "That's exactly right"

The quantum annealing insight wasn't in any input—it emerged from the collaboration.

---

## Reproducible Pattern

### For Future Novel Visualizations

1. **Saturate in domain** - Know the problem deeply
2. **Collect random inputs** - Read widely, follow curiosity
3. **Trust intuition** - When something "feels right," explore it
4. **Use Gemini** - Elaborate the concept, understand foundations
5. **Use AI Studio** - Generate implementation quickly
6. **Use Claude Code** - Integrate, refine, discover connections
7. **Document everything** - Capture insights for posterity
8. **Iterate** - The first version is never the last

### Anti-Patterns

- **Don't skip human insight** - AI can't see the original connection
- **Don't skip integration** - Generated code needs codebase context
- **Don't skip documentation** - Insights are lost without capture
- **Don't expect perfection** - Iteration is part of the process

---

## Future Directions

### Near Term

- Connect visualizations to real MCP tools (live data)
- Add animation for T1 swap execution
- Implement foam coarsening visualization
- Add haptic feedback exploration (gamepad rumble for pressure)

### Medium Term

- AR/VR prototypes using WebXR
- Voice control for hands-free operation
- Multi-user collaborative visualization
- Time dimension: animate schedule evolution

### Long Term

- Quantum annealing integration for actual optimization
- Neural interface research (direct perception of constraint space)
- Analog computing exploration (physical soap film solvers)

---

## Acknowledgments

This pipeline emerged from the collaboration between:
- **Human insight** - Domain expert (clinical operations)
- **AI Systems** - Google Gemini, Google AI Studio, Anthropic Claude

The key insight: these are complementary, not competing. Each has strengths the others lack. The magic is in the orchestration.

---

*The apparent chaos is actually high-dimensional pattern matching that doesn't fit into words until after the fact. Years of context compress into an intuition—"this foam thing is the shape of this problem"—then someone needs to unpack it back into structure.*

— Session notes, January 16, 2026
