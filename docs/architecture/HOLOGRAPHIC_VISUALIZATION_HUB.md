# Holographic Visualization Hub - Architecture Documentation

> **The Telescope for Multi-Spectral Constraint Observation**

## Overview

The Holographic Visualization Hub is the integration layer that receives and renders data from all Far Realm analysis sessions (1-8). It projects N-dimensional constraint data into an interactive 3D space, enabling simultaneous observation of multiple "wavelengths" (constraint types) and "spectral layers" (analytical dimensions).

### The Holographic Metaphor

Like a hologram that encodes 3D information in interference patterns, this visualization encodes the complex relationships between schedule constraints in spatial form:

- **Different wavelengths** = Different constraint types (ACGME=red, fairness=blue, fatigue=yellow)
- **Spectral layers** = Different analytical dimensions from each session
- **Manifold projection** = Dimensionality reduction preserving constraint relationships
- **Spatial clustering** = Related constraints appear near each other
- **Tension lines** = Connections showing constraint interdependencies

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HOLOGRAPHIC VISUALIZATION HUB                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     DATA INGEST PIPELINE                      │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │   │
│  │  │Session 1│  │Session 2│  │Session 3│  │Session 4│   ...    │   │
│  │  │ Quantum │  │Temporal │  │Topology │  │Spectral │          │   │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘          │   │
│  │       │            │            │            │                │   │
│  │       └────────────┴────────────┴────────────┘                │   │
│  │                          │                                     │   │
│  │                    ┌─────▼─────┐                               │   │
│  │                    │ Normalize │                               │   │
│  │                    │  & Merge  │                               │   │
│  │                    └─────┬─────┘                               │   │
│  └──────────────────────────┼───────────────────────────────────┘   │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                 DIMENSIONALITY REDUCTION                      │   │
│  │                                                               │   │
│  │  ┌───────────┐    ┌───────────┐    ┌───────────┐             │   │
│  │  │    PCA    │    │   UMAP    │    │   t-SNE   │             │   │
│  │  │ (default) │    │ (local)   │    │ (visual)  │             │   │
│  │  └───────────┘    └───────────┘    └───────────┘             │   │
│  │                                                               │   │
│  │  N-dimensional ConstraintDataPoint[] -> 3D ManifoldPoint[]   │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                    RENDERING ENGINE                           │   │
│  │                                                               │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │   │
│  │  │   Canvas    │    │   Shaders   │    │   WebXR     │       │   │
│  │  │  Renderer   │    │  (GLSL)     │    │  Foundation │       │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘       │   │
│  │                                                               │   │
│  │  - Perspective projection                                     │   │
│  │  - Point rendering with glow                                  │   │
│  │  - Grid/axis visualization                                    │   │
│  │  - Real-time animation                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## The Spatial Projection Lens

### How 3D Reveals Hidden Correlations

Traditional 2D schedule views show constraints linearly: a list of violations, a timeline of conflicts. The holographic projection reveals **structural relationships** that are invisible in 2D:

#### 1. Constraint Clustering

When constraints are projected from N-dimensional feature space to 3D, **similar constraints cluster together**:

```
Before projection (N-dimensional):
  c1: [0.8, 0.2, 0.5, 0.1, 0.9, 0.3, ...]  // ACGME work hour
  c2: [0.7, 0.3, 0.4, 0.2, 0.8, 0.4, ...]  // ACGME work hour
  c3: [0.1, 0.9, 0.8, 0.7, 0.2, 0.1, ...]  // Fairness

After PCA projection (3D):
  c1: (2.1, 1.5, 0.3)  ─┐
  c2: (2.0, 1.4, 0.4)  ─┴─ Cluster A (ACGME related)
  c3: (-1.5, 2.8, -0.2) ── Far from Cluster A (Fairness)
```

This clustering reveals which constraints are **fundamentally related** even if they appear different on the surface.

#### 2. Tension Topology

The 3D space reveals the **stress topology** of the schedule:

- **Dense regions** = Many constraints competing for the same resources
- **Sparse regions** = Schedule slack, flexibility
- **Tension lines** = Direct conflicts between constraint pairs
- **Bridge points** = Constraints that connect otherwise separate clusters

```
Tension Visualization:

    [ACGME Cluster]
         ╱   ╲
        ╱     ╲ (tension lines)
       ╱       ╲
    [Coverage]──────[Fairness Cluster]
         │
         │ (bridge constraint)
         │
    [Preference Cluster]
```

#### 3. Spectral Layer Interaction

By overlaying multiple spectral layers, we see how different analytical perspectives interact:

- **Quantum layer** (Session 1): Probabilistic constraint satisfaction
- **Evolutionary layer** (Session 5): Game-theoretic strategy stability
- **Thermodynamic layer** (Session 8): Energy/entropy of configurations

When the same constraint appears in multiple layers with different positions, it indicates the constraint has different behaviors under different analytical lenses.

#### 4. Severity Gradients

The 3D rendering encodes severity through:

- **Size**: Larger points = higher severity
- **Color intensity**: Brighter = more critical
- **Glow effect**: Pulsing glow = actively violated
- **Height/Y-axis**: Often encodes severity dimension

### Mathematical Foundation

The projection preserves relative distances through variance-maximizing transforms:

```
PCA Projection:
  Given: X ∈ ℝⁿˣᵈ (n constraints, d dimensions)
  Compute: Σ = (1/n) XᵀX (covariance matrix)
  Eigendecompose: Σ = VΛVᵀ
  Project: X₃ᴰ = X · V[:, :3] (first 3 eigenvectors)

UMAP Projection:
  Build: k-NN graph in high-D
  Optimize: Low-D embedding preserving local distances
  Result: Non-linear projection preserving neighborhoods

t-SNE Projection:
  Compute: Pairwise similarity distributions (high-D, low-D)
  Minimize: KL divergence between distributions
  Result: Preserves local structure, reveals clusters
```

## Data Pipeline

### Standard Session Export Format

All Far Realm sessions export data in this format:

```typescript
interface SessionDataExport {
  sessionId: number;           // 1-8
  sessionName: SpectralLayer;  // "quantum", "temporal", etc.
  timestamp: string;
  version: string;

  constraints: ConstraintDataPoint[];

  metrics: {
    totalConstraints: number;
    satisfiedCount: number;
    violatedCount: number;
    criticalCount: number;
    averageSeverity: number;
    averageTension: number;
  };

  correlations?: {
    targetSession: SpectralLayer;
    correlationCoefficient: number;
    sharedConstraintIds: string[];
  }[];
}
```

### Pipeline Stages

1. **Ingest**: Receive session exports via API or WebSocket
2. **Normalize**: Convert to standard `ConstraintDataPoint` format
3. **Merge**: Combine all sessions, deduplicate by constraint ID
4. **Project**: Apply dimensionality reduction (PCA/UMAP/t-SNE)
5. **Colorize**: Apply constraint type colors and layer tints
6. **Render**: Generate `ManifoldPoint[]` for visualization

## Component Structure

```
frontend/src/features/holographic-hub/
├── index.ts                    # Public API exports
├── types.ts                    # Type definitions
├── data-pipeline.ts            # Data processing & projection
├── shaders.ts                  # GLSL shader code
├── hooks.ts                    # React hooks for state/data
├── HolographicManifold.tsx     # Main 3D renderer component
├── LayerControlPanel.tsx       # Layer/constraint toggles
└── __tests__/                  # Test files
    ├── HolographicManifold.test.tsx
    ├── data-pipeline.test.ts
    └── hooks.test.ts
```

## Usage

### Basic Usage

```tsx
import { HolographicManifold } from '@/features/holographic-hub';

function ConstraintVisualization() {
  return (
    <HolographicManifold
      startDate={new Date()}
      endDate={new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)}
      useMockData={true}
      showControls={true}
      showLegend={true}
      showStats={true}
      onPointClick={(point) => console.log('Selected:', point)}
      onPointHover={(point) => console.log('Hovered:', point)}
    />
  );
}
```

### With Custom State Management

```tsx
import {
  HolographicManifold,
  useHolographicData,
  useHolographicState,
  LayerControlPanel,
} from '@/features/holographic-hub';

function AdvancedVisualization() {
  const { data, isLoading } = useHolographicData({
    startDate: '2024-01-01',
    endDate: '2024-01-14',
    layers: ['quantum', 'evolutionary'],
    projectionMethod: 'umap',
  });

  const {
    state,
    toggleLayer,
    toggleConstraint,
    setAllLayersVisible,
    setAllConstraintsVisible,
  } = useHolographicState();

  return (
    <div className="flex gap-4">
      <LayerControlPanel
        layerVisibility={state.layerVisibility}
        constraintVisibility={state.constraintVisibility}
        onToggleLayer={toggleLayer}
        onToggleConstraint={toggleConstraint}
        onSetAllLayersVisible={setAllLayersVisible}
        onSetAllConstraintsVisible={setAllConstraintsVisible}
        data={data}
      />
      <HolographicManifold
        startDate={new Date('2024-01-01')}
        endDate={new Date('2024-01-14')}
        showControls={false}
      />
    </div>
  );
}
```

### Real-Time Updates

```tsx
import { useRealTimeUpdates } from '@/features/holographic-hub';

function LiveVisualization() {
  const { isConnected, lastUpdate } = useRealTimeUpdates({
    endpoint: '/api/visualization/holographic/stream',
    enabled: true,
    onUpdate: (data) => {
      console.log('New data:', data);
    },
  });

  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <div>Last update: {lastUpdate?.toISOString()}</div>
      <HolographicManifold useMockData={false} />
    </div>
  );
}
```

## Spectral Layers Reference

| Layer | Session | Description | Primary Insights |
|-------|---------|-------------|------------------|
| Quantum | 1 | Probabilistic constraint states | Uncertainty in satisfaction |
| Temporal | 2 | Time-evolving dynamics | Schedule evolution patterns |
| Topological | 3 | Structural relationships | Constraint dependencies |
| Spectral | 4 | Frequency-domain patterns | Recurring conflicts |
| Evolutionary | 5 | Game-theoretic evolution | Strategy stability |
| Gravitational | 6 | Attraction/repulsion fields | Resource competition |
| Phase | 7 | State transitions | Critical change points |
| Thermodynamic | 8 | Energy/entropy | Schedule stability |

## Color Scheme

### Constraint Types

| Type | Color | RGB | Purpose |
|------|-------|-----|---------|
| ACGME | Red | (0.9, 0.2, 0.2) | Regulatory compliance |
| Fairness | Blue | (0.2, 0.5, 0.9) | Workload equity |
| Fatigue | Yellow | (0.95, 0.8, 0.2) | Burnout risk |
| Temporal | Cyan | (0.2, 0.8, 0.9) | Time conflicts |
| Preference | Green | (0.3, 0.8, 0.4) | Individual preferences |
| Coverage | Orange | (0.95, 0.5, 0.2) | Staffing gaps |
| Skill | Purple | (0.6, 0.3, 0.8) | Credentials |
| Custom | Gray | (0.8, 0.8, 0.8) | User-defined |

### Layer Tints

Each spectral layer adds a subtle color tint to help distinguish which analytical dimension a constraint comes from.

## WebXR Foundation

The hub includes basic WebXR support for immersive VR viewing:

```tsx
import { useWebXR } from '@/features/holographic-hub';

function ImmersiveVisualization() {
  const { isSupported, isSessionActive, startSession, endSession, error } =
    useWebXR();

  return (
    <div>
      {isSupported ? (
        <button onClick={isSessionActive ? endSession : startSession}>
          {isSessionActive ? 'Exit VR' : 'Enter VR'}
        </button>
      ) : (
        <span>WebXR not supported</span>
      )}
      {error && <div className="text-red-500">{error}</div>}
      <HolographicManifold />
    </div>
  );
}
```

## Performance Considerations

### Rendering Optimization

- **Point culling**: Off-screen points are not rendered
- **LOD**: Point size adapts to camera distance
- **Batch rendering**: Points are drawn in depth-sorted order
- **Animation throttling**: Animations pause when tab is hidden

### Data Optimization

- **Incremental updates**: Only new/changed constraints are processed
- **Query caching**: React Query caches fetched data (5 min)
- **Filtered rendering**: Hidden layers don't consume render cycles

### Memory Management

- **Point pooling**: ManifoldPoint objects are reused
- **Canvas resize**: Uses ResizeObserver for efficient resizing
- **Cleanup**: All event listeners and intervals are properly disposed

## Future Enhancements

1. **Three.js Integration**: Full WebGL rendering for 10,000+ points
2. **Tension Line Rendering**: Visual connections between related constraints
3. **Cluster Detection**: Automatic identification of constraint clusters
4. **Time Animation**: Play back schedule evolution over time
5. **Collaborative Viewing**: Multiple users viewing same manifold
6. **VR Controllers**: Hand-based interaction in VR mode
7. **Export to 3D Model**: Save manifold as GLTF for external viewing
