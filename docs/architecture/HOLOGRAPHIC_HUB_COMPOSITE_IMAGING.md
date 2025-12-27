# Holographic Hub: Composite Imaging Guide

> **Far Realm Session 10: Correlation & Interaction Engine**
>
> This document explains how multi-spectral correlation reveals hidden structure
> in scheduling data through cross-wavelength composite imaging.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Wavelength Channels](#wavelength-channels)
3. [Cross-Wavelength Correlation](#cross-wavelength-correlation)
4. [Composite Imaging Techniques](#composite-imaging-techniques)
5. [Pattern Detection](#pattern-detection)
6. [Interactive Exploration](#interactive-exploration)
7. [3D Visualization](#3d-visualization)
8. [Audio Sonification](#audio-sonification)
9. [Looking Glass Integration](#looking-glass-integration)
10. [Implementation Guide](#implementation-guide)

---

## Introduction

### What is Composite Imaging?

Just as astronomers combine images from different wavelengths (radio, infrared,
visible, X-ray) to reveal hidden structures in the cosmos, the Holographic Hub
combines multiple data "wavelengths" from scheduling data to reveal patterns
invisible in any single view.

```
Traditional View:              Composite View:
┌─────────────────┐           ┌─────────────────┐
│ Schedule Grid   │           │ Quantum state   │
│ (flat, 2D)      │     →     │ + Time phase    │
│ Limited insight │           │ + Frequency     │
└─────────────────┘           │ + Evolution     │
                              │ = Deep insight  │
                              └─────────────────┘
```

### The Multi-Spectral Telescope Analogy

| Astronomy           | Holographic Hub        | What It Reveals            |
|---------------------|------------------------|----------------------------|
| Radio waves         | Quantum channel        | Superposition of options   |
| Infrared            | Thermal channel        | Burnout/stress hotspots    |
| Visible light       | Temporal channel       | Day-to-day patterns        |
| Ultraviolet         | Spectral channel       | Periodic cycles            |
| X-rays              | Evolutionary channel   | Strategy fitness           |
| Gamma rays          | Topological channel    | Network structure          |

---

## Wavelength Channels

### 1. Quantum Channel (Purple: `#8b5cf6`)

**What it represents:** Schedule alternatives existing in superposition until
"observed" (assigned).

**Data sources:**
- Alternative schedule variants from the solver
- Uncertainty in assignments
- Entanglement between dependent assignments

**Key metrics:**
- **Coherence**: How stable the quantum state is (0-1)
- **Entanglement density**: How interconnected options are
- **Decoherence rate**: How quickly options collapse

**Visualization:** Bloch sphere points, probability clouds

```typescript
interface QuantumState {
  stateId: string;
  amplitude: ComplexNumber;  // Wave function
  probability: number;       // |ψ|²
  coherence: number;         // Phase stability
  entanglements: EntanglementLink[];
}
```

### 2. Temporal Channel (Blue: `#3b82f6`)

**What it represents:** Time-series patterns and phase relationships.

**Data sources:**
- Assignment timestamps
- Schedule changes over time
- Lag correlations

**Key metrics:**
- **Phase relationships**: Sync between different elements
- **Temporal clusters**: Recurring patterns (daily, weekly)
- **Derivatives**: Rate of change, acceleration

**Visualization:** Time series, phase diagrams

### 3. Spectral Channel (Amber: `#f59e0b`)

**What it represents:** Frequency-domain view of scheduling patterns.

**Data sources:**
- FFT of assignment time series
- Power spectral density
- Harmonic analysis

**Key metrics:**
- **Dominant frequencies**: Main periodic patterns
- **Harmonics**: Sub-patterns (e.g., weekly within monthly)
- **Coherence spectrum**: Frequency-specific correlations

**Visualization:** Power spectrum, spectrogram

### 4. Evolutionary Channel (Green: `#22c55e`)

**What it represents:** Strategy fitness and population dynamics.

**Data sources:**
- Game theory tournament results
- Strategy evolution over generations
- Fitness landscape

**Key metrics:**
- **Population distribution**: Which strategies dominate
- **Fitness scores**: How well configurations perform
- **Attractor basins**: Stable equilibrium points

**Visualization:** Fitness landscape, population evolution

### 5. Topological Channel (Cyan: `#06b6d4`)

**What it represents:** Network structure and connectivity.

**Data sources:**
- Dependency graph
- Constraint relationships
- Communication patterns

**Key metrics:**
- **Centrality**: Important nodes
- **Clustering**: Related groups
- **Path lengths**: Distance between elements

**Visualization:** Force-directed graphs, adjacency matrices

### 6. Thermal Channel (Red: `#ef4444`)

**What it represents:** Stress, workload, and burnout gradients.

**Data sources:**
- Workload distribution
- Burnout risk scores
- Overtime accumulation

**Key metrics:**
- **Hotspots**: Overloaded individuals/times
- **Gradients**: Rate of stress change
- **Diffusion**: How stress spreads

**Visualization:** Heat maps, thermal flow

---

## Cross-Wavelength Correlation

### Correlation Pairs

When two wavelength channels are correlated, new patterns emerge:

| Primary   | Secondary    | Insight                        | Example Discovery           |
|-----------|--------------|--------------------------------|---------------------------|
| Temporal  | Spectral     | **Circadian Resonance**        | 24h work pattern cycles    |
| Quantum   | Evolutionary | **Quantum Fitness**            | Best options by fitness    |
| Spectral  | Thermal      | **Harmonic Stress**            | Frequency of overwork      |
| Temporal  | Topological  | **Network Evolution**          | How connections change     |
| Quantum   | Spectral     | **Quantum Harmonics**          | Coherence in frequency     |
| Evolutionary | Thermal   | **Evolution Pressure**         | Stress driving change      |

### Correlation Metrics

1. **Pearson Correlation** (r): Linear relationship strength
   ```
   r = Σ(x-x̄)(y-ȳ) / √[Σ(x-x̄)² × Σ(y-ȳ)²]
   ```

2. **Mutual Information** (MI): Non-linear dependency
   ```
   MI(X,Y) = Σ p(x,y) × log[p(x,y) / (p(x)×p(y))]
   ```

3. **Transfer Entropy** (TE): Directional causality
   ```
   TE(X→Y) = H(Y|Y_past) - H(Y|Y_past, X_past)
   ```

### Composite Mixing Modes

```typescript
type MixingMode = 'additive' | 'multiplicative' | 'spectral' | 'phase';
```

| Mode           | Formula                        | Best For                   |
|----------------|--------------------------------|----------------------------|
| Additive       | w₁×A + w₂×B                    | General blending           |
| Multiplicative | A × B                          | Detecting coincidence      |
| Spectral       | sin(A×π) × cos(B×π)            | Phase-sensitive patterns   |
| Phase          | atan2(B, A)                    | Angular relationships      |

---

## Composite Imaging Techniques

### 1. Circadian Resonance Detection

**Channels:** Temporal × Spectral

**What it reveals:** Natural work rhythm patterns that align with circadian biology.

**Algorithm:**
```python
def detect_circadian_resonance(temporal: TemporalData, spectral: SpectralData):
    # Look for 24-hour period in spectral harmonics
    daily_freq = 1 / 24  # cycles per hour

    # Find harmonics near circadian frequency
    circadian_harmonics = [h for h in spectral.harmonics
                          if abs(h.frequency - daily_freq) < 0.01]

    # Check phase consistency in temporal clusters
    daily_clusters = [c for c in temporal.clusters if c.pattern == 'daily']

    return {
        'resonance_strength': max(h.amplitude for h in circadian_harmonics),
        'phase_coherence': mean(c.strength for c in daily_clusters),
        'recommendation': 'Align schedule with natural circadian peaks'
    }
```

### 2. Quantum Fitness Landscape

**Channels:** Quantum × Evolutionary

**What it reveals:** Which schedule alternatives have the highest fitness.

**Insight:** High-coherence quantum states that align with fitness peaks are
stable, optimal solutions.

```python
def map_quantum_fitness(quantum: QuantumData, evolutionary: EvolutionaryData):
    # Correlate coherence with fitness
    correlations = []
    for state in quantum.states:
        nearby_fitness = find_nearest_fitness(state.position, evolutionary.landscape)
        correlations.append((state.coherence, nearby_fitness))

    # Identify quantum tunneling opportunities
    high_coherence = [s for s in quantum.states if s.coherence > 0.7]
    attractors = evolutionary.attractors

    return {
        'optimal_states': rank_by_fitness(high_coherence),
        'tunneling_paths': find_tunneling_routes(high_coherence, attractors)
    }
```

### 3. Harmonic Stress Mapping

**Channels:** Spectral × Thermal

**What it reveals:** Correlation between schedule frequency patterns and burnout.

**Key insight:** High-frequency oscillations (constant changes) correlate with
thermal hotspots (burnout risk).

```python
def harmonic_stress_analysis(spectral: SpectralData, thermal: ThermalData):
    # High-frequency energy
    high_freq_power = sum(h.amplitude for h in spectral.harmonics if h.harmonic >= 3)

    # Thermal hotspots
    avg_thermal = mean(p.value for p in thermal.points)
    hotspots = [p for p in thermal.points if p.value > avg_thermal * 1.5]

    if high_freq_power > 0.3 and len(hotspots) > 0:
        return {
            'warning': 'High-frequency schedule oscillations correlate with burnout',
            'affected_individuals': [h.entityId for h in hotspots],
            'recommendation': 'Reduce schedule volatility for flagged individuals'
        }
```

---

## Pattern Detection

### Pattern Types

1. **Resonance**: Two signals oscillating in sync
   - Detected by: Cross-correlation peaks
   - Example: Weekly rotation cycles synchronized

2. **Coupling**: Strong local correlations
   - Detected by: Clustering in scatter plots
   - Example: Certain constraints always co-occur

3. **Cascade**: Sequential activation patterns
   - Detected by: Peak sequences in time series
   - Example: One person's overwork triggers others

4. **Feedback**: Bidirectional causality
   - Detected by: High transfer entropy both directions
   - Example: Mutual workload dependencies

5. **Synchronization**: Multiple signals phase-locked
   - Detected by: High correlation within groups
   - Example: Team members with aligned schedules

### Detection Algorithms

```typescript
// Resonance: Find peaks in cross-correlation
const crossCorr = crossCorrelation(signal1, signal2, maxLag=30);
const resonancePeaks = crossCorr.filter(c => Math.abs(c.correlation) > 0.7);

// Coupling: Cluster analysis in feature space
const clusters = clusterByProximity(entityData, eps=0.2);
const couplings = clusters.filter(c => c.length >= 3);

// Cascade: Sequential peak detection
const peaks = findPeaks(timeSeries);
const cascades = groupSequentialPeaks(peaks, maxGap=5);

// Feedback: Bidirectional transfer entropy
const teForward = transferEntropy(x, y, lag=1);
const teBackward = transferEntropy(y, x, lag=1);
const feedback = teForward > 0.1 && teBackward > 0.1;

// Synchronization: Correlation-based clustering
const syncGroups = signals.filter((s1, s2) =>
    pearsonCorrelation(s1.values, s2.values) > 0.8
);
```

---

## Interactive Exploration

### Selection System

The interactive selector enables:

1. **Multi-select**: Shift+click to add to selection
2. **Dependency highlighting**: See connected entities
3. **Highlight modes**:
   - Dependencies: Show constraint relationships
   - Conflicts: Highlight conflicting assignments
   - Correlations: Show correlation strength
   - None: Raw visualization

### Selection-Driven Updates

```typescript
// When selection changes:
1. Update dependency graph with selected IDs
2. Filter correlation results to selected entities
3. Highlight connected nodes in 3D view
4. Update audio sources for selected violations
5. Refresh wavelength channel data for selection
```

### Keyboard Shortcuts

| Key         | Action                |
|-------------|----------------------|
| Shift+Click | Add to selection     |
| Ctrl+Click  | Toggle selection     |
| Escape      | Clear selection      |
| Ctrl+Z      | Undo last selection  |

---

## 3D Visualization

### Constraint Coupling View

Shows constraints as nodes in 3D space with coupling edges:

```
   ACGME Hours ───── Supervision
       │ (competing)     │
       │                 │ (reinforcing)
       ▼                 ▼
   Coverage ─────────── Workload
         (reinforcing)
```

**Visual encoding:**
- Node size: Importance (weight)
- Node color: Category (ACGME=red, coverage=blue, etc.)
- Edge color: Type (green=reinforcing, red=competing)
- Edge width: Coupling strength
- Ring around node: Satisfaction rate

### 3D Navigation

- **Drag**: Rotate view
- **Scroll**: Zoom
- **Reset**: Return to default view
- **Force field toggle**: Show/hide constraint force vectors

---

## Audio Sonification

### Violation Audio Mapping

Each violation type maps to distinct audio characteristics:

| Violation Type      | Frequency | Waveform  | Character        |
|---------------------|-----------|-----------|------------------|
| ACGME Hours         | 220 Hz    | Sine      | Low warning      |
| ACGME Rest          | 330 Hz    | Triangle  | Mid alert        |
| Supervision         | 440 Hz    | Square    | Sharp attention  |
| Coverage Gap        | 523 Hz    | Sawtooth  | High urgency     |
| Conflict            | 587 Hz    | Square+FM | Clashing         |
| Credential Missing  | 392 Hz    | Triangle  | Moderate concern |
| Workload Imbalance  | 349 Hz    | Sine+LFO  | Fatigue tone     |

### Spatial Audio

Violations are positioned in 3D audio space:

```typescript
interface SpatialAudioConfig {
  distanceModel: 'linear' | 'inverse' | 'exponential';
  refDistance: number;      // Distance at full volume
  maxDistance: number;      // Cutoff distance
  rolloffFactor: number;    // How quickly sound fades
}
```

**Experience:** Move the "camera" (listener) through the visualization to
hear violations get louder as you approach them.

---

## Looking Glass Integration

### What is Looking Glass?

A holographic display that shows true 3D without glasses, using
lightfield technology with ~50 different viewing angles.

### Quilt Rendering

The display requires a "quilt" image containing all viewing angles:

```
┌─────┬─────┬─────┬─────┬─────┐
│ V1  │ V2  │ V3  │ V4  │ V5  │
├─────┼─────┼─────┼─────┼─────┤
│ V6  │ V7  │ V8  │ V9  │ V10 │
├─────┼─────┼─────┼─────┼─────┤
│ ... │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┘

Quilt: 8×6 = 48 views for Portrait display
```

### Device Presets

| Device    | Views | Quilt Size   | View Cone |
|-----------|-------|--------------|-----------|
| Portrait  | 48    | 3360×3360    | 40°       |
| Landscape | 45    | 4096×4096    | 50°       |
| Go        | 66    | 5632×3072    | 54°       |

### Holographic Effect Parameters

```typescript
interface HolographicMaterial {
  type: 'holographic';
  hologramColor: string;       // Hologram tint
  scanlineIntensity: number;   // 0-1, retro effect
  fresnelPower: number;        // Edge glow strength
}
```

---

## Implementation Guide

### Quick Start

```tsx
import { HolographicHub } from '@/features/holographic-hub';

function ScheduleVisualization() {
  return (
    <HolographicHub
      initialTimeRange={{
        start: '2024-01-01',
        end: '2024-03-31'
      }}
      enableLookingGlass={false}
      onStateChange={(state) => console.log('State changed:', state)}
    />
  );
}
```

### Using Individual Hooks

```tsx
import {
  useCorrelationEngine,
  useWavelengthCorrelation,
  useSpatialAudio,
  WAVELENGTH_PAIRS,
} from '@/features/holographic-hub';

function CustomVisualization() {
  // Correlation between temporal and spectral
  const { result, isLoading } = useWavelengthCorrelation(
    WAVELENGTH_PAIRS.find(p => p.label === 'Circadian Resonance')!
  );

  // Spatial audio for violations
  const { initAudio, addViolationSource, config } = useSpatialAudio();

  // Custom correlation engine
  const { updateChannel, computeCorrelations, correlations } = useCorrelationEngine();

  // ...
}
```

### Adding Custom Wavelength Channels

```typescript
// 1. Define the channel type
type CustomChannel = 'financial' | 'satisfaction';

// 2. Add data generator
function generateFinancialData(): CustomChannelData {
  return {
    costs: [...],
    budget: [...],
    variance: [...]
  };
}

// 3. Register with correlation engine
correlationEngine.updateChannel('financial', generateFinancialData());

// 4. Define correlation pairs
const customPairs: WavelengthPair[] = [
  {
    primary: 'financial',
    secondary: 'thermal',
    label: 'Cost-Stress Correlation',
    description: 'How budget constraints correlate with staff burnout'
  }
];
```

### Export Formats

| Format | Use Case                  | Includes                    |
|--------|---------------------------|-----------------------------|
| PNG    | Static presentation       | Current view snapshot       |
| SVG    | Scalable graphics         | Vector version of view      |
| WebM   | Video presentation        | Animation sequence          |
| GIF    | Quick sharing             | Looping animation           |
| glTF   | 3D software/AR/VR         | Full 3D scene               |
| USDZ   | Apple AR Quick Look       | AR-ready model              |
| JSON   | Data analysis             | Raw visualization data      |
| CSV    | Spreadsheet analysis      | Tabular correlation data    |

---

## Summary

The Holographic Hub transforms scheduling data into a multi-dimensional
experience where:

1. **Six wavelength channels** reveal different aspects of the data
2. **Cross-correlation** discovers hidden patterns between channels
3. **Interactive selection** enables exploration of dependencies
4. **3D visualization** shows constraint coupling in space
5. **Spatial audio** makes violations audible
6. **Looking Glass** enables holographic viewing
7. **Guided tours** walk through key insights
8. **Export** shares visualizations in multiple formats

This composite imaging approach reveals structure that would be invisible
in traditional 2D schedule views, enabling deeper understanding and
better decision-making for residency program management.

---

*Last Updated: December 2024*
*Far Realm Session 10: Correlation Visualization Engine*
