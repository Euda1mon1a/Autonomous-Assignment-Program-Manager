# Gaussian Splatting for Schedule Visualization & Generation

> **Date:** 2026-01-13
> **Status:** Research / Exploration
> **Related:** `docs/architecture/3d-voxel-visualization.md`, `backend/app/visualization/schedule_voxel.py`

---

## Executive Summary

This document explores whether 3D visualization capabilities (specifically Gaussian Splatting) unlock genuinely novel approaches to schedule generation and analysis that weren't previously possible. The conclusion: **yes, but the real value is computational, not visual.**

The key insight is that representing schedules as 3D/4D Gaussian fields enables:
1. Application of algorithms from medical imaging, robotics, and graphics
2. Differentiable constraint satisfaction via physics simulation
3. Generative schedule creation via diffusion models
4. Real-time browser rendering via WebGPU

---

## Table of Contents

1. [Current State: Voxel Representation](#current-state-voxel-representation)
2. [What 3D Actually Provides](#what-3d-actually-provides)
3. [Gaussian Splatting Fundamentals](#gaussian-splatting-fundamentals)
4. [Apple SHARP Model](#apple-sharp-model)
5. [Novel Applications](#novel-applications)
   - [4D Gaussians for Temporal Schedules](#1-4d-gaussians-for-temporal-schedules)
   - [WebGPU Rendering (Visionary)](#2-webgpu-rendering-visionary)
   - [Diffusion-Based Schedule Generation](#3-diffusion-based-schedule-generation)
   - [Physics-Informed Constraint Satisfaction](#4-physics-informed-constraint-satisfaction)
   - [3D CNN Pathology Detection](#5-3d-cnn-pathology-detection)
6. [Gap Analysis: What We Have vs Need](#gap-analysis-what-we-have-vs-need)
7. [Research Landscape](#research-landscape)
8. [Implementation Roadmap](#implementation-roadmap)
9. [References](#references)

---

## Current State: Voxel Representation

### What We Have

The current implementation (`backend/app/visualization/schedule_voxel.py`) provides:

```python
@dataclass
class ScheduleVoxel:
    """A single voxel in the 3D schedule space."""
    x: int  # Time index (half-day blocks)
    y: int  # Person index
    z: int  # Activity layer
    color: VoxelColor
    opacity: float
    identity: VoxelIdentity  # assignment_id, person_name, etc.
    state: VoxelState        # is_conflict, is_violation, etc.
    metadata: VoxelMetadata  # role, confidence, hours
```

### Axes Definition

```
         Time (X-axis)
         →→→→→→→→→→→

    ↑   ┌─────────────┐
    │  /             /│
    │ /  Activity   / │
P   │/   (Z-axis)  /  │
e   │─────────────│   │
o   │             │   │
p   │   VOXEL     │  /
l   │             │ /
e   │_____________│/
(Y)
```

- **X-axis (horizontal):** Time - Each unit is a half-day block (AM/PM)
- **Y-axis (vertical):** People - Faculty at top, then residents by PGY level
- **Z-axis (depth):** Activity type - Different layers for clinic, inpatient, etc.

### NumPy Export

```python
def to_numpy_grid(self) -> np.ndarray:
    """Convert to 3D numpy array.

    Returns:
        Shape: (time_steps, num_people, num_activities)
        Values: 0=empty, 1=occupied, 2=conflict, 3=violation
    """
```

### Limitations of Current Approach

| Limitation | Impact |
|------------|--------|
| Discrete positions | Can't represent uncertainty, gradual transitions |
| Binary occupancy | No partial assignments, confidence levels as structure |
| Hard edges | No natural blending for overlapping concerns |
| Integer grid | Can't interpolate between time points |
| No differentiability | Can't backprop through the representation |

---

## What 3D Actually Provides

### Honest Assessment

Most 3D visualization benefits CAN be achieved in 2D:
- Conflict detection → Red highlighted cells
- Coverage gaps → Empty cells in grid
- Workload heatmaps → 2D color gradients

### What 3D Genuinely Unlocks

1. **Multi-activity conflict detection** - A person scheduled for clinic AND call shows as overlapping cubes. 2D requires color-coding gymnastics or multiple views.

2. **Supervision ratio visualization** - Seeing resident layers (bottom) and faculty layers (top) together makes supervision gaps visible as spatial "holes."

3. **NumPy tensor analysis** - The real win:
   ```python
   grid = grid.to_numpy_grid()  # Shape: (time, person, activity)
   conflicts = np.where(grid == 2)  # Find all conflicts computationally
   ```

4. **Algorithm applicability** - Every 3D algorithm from medical imaging, robotics, graphics, and ML becomes applicable to scheduling.

---

## Gaussian Splatting Fundamentals

### What is a Gaussian Splat?

A 3D Gaussian is a "fuzzy blob" defined by:
- **Position (μ):** Center point in 3D space
- **Covariance (Σ):** 3×3 matrix defining shape/orientation
- **Color:** RGB values
- **Opacity (α):** Transparency

```python
@dataclass
class Gaussian3D:
    mean: np.ndarray       # [x, y, z] position
    covariance: np.ndarray # 3x3 matrix (spread/uncertainty)
    color: np.ndarray      # [r, g, b]
    opacity: float         # 0-1
```

### Voxels vs Gaussians

| Aspect | Voxels | Gaussians |
|--------|--------|-----------|
| Shape | Discrete cubes | Continuous blobs |
| Edges | Hard | Soft/blended |
| Overlap | Binary conflict | Additive density |
| Rendering | Ray marching | Splatting (fast) |
| Differentiable | No | Yes |
| Memory | O(n³) grid | O(k) primitives |

### Why Gaussians for Schedules?

1. **Continuous density field** - Instead of "occupied/not," get "workload density = 0.73 here"
2. **Natural overlap handling** - Overlapping Gaussians = higher density (stress concentration)
3. **Differentiable** - Can backprop through the entire representation
4. **Fast rendering** - 100+ FPS with modern splatting

---

## Apple SHARP Model

### Overview

In December 2025, Apple released **SHARP** (Sharp Monocular View Synthesis): an open-source model that converts a single 2D photo into a 3D Gaussian Splat representation in under 1 second.

**Repository:** https://github.com/apple/ml-sharp

### How It Works

1. Input: Single 2D image
2. Neural network predicts Gaussian parameters
3. Output: `.ply` file with millions of Gaussians
4. Render from any viewpoint at 100+ FPS

### Key Technical Details

- Single feedforward pass (no iterative optimization)
- Output format: PLY files compatible with standard viewers
- Coordinate system: OpenCV convention (x right, y down, z forward)
- Performance: Sub-second on standard GPU

### Relevance to Scheduling

The SHARP architecture demonstrates that neural networks can learn to predict 3D Gaussian representations from 2D inputs. This pattern could apply to:

```
Photo → 3D Scene           (SHARP, proven)
2D Schedule Grid → 3D Problem Density Field   (Novel, unexplored)
```

A schedule-trained version would learn "what problems look like" - patterns in 2D grids that imply hidden issues in the person/time/activity space.

---

## Novel Applications

### 1. 4D Gaussians for Temporal Schedules

#### The Concept

Schedules are inherently 4D: Person × Activity × Time × [something]. Recent research on **4D Gaussian Splatting** models dynamic scenes with time as the 4th dimension.

#### Key Research

**4DGS-1K (March 2025):**
- Runs at **1000+ FPS** on modern GPUs
- 41× reduction in storage vs vanilla 4DGS
- Uses "Spatial-Temporal Variation Score" for efficient pruning

**4D-Rotor Gaussian Splatting:**
- Models dynamics with anisotropic 4D XYZT Gaussians
- Handles abrupt motions and fine details
- 277 FPS on RTX 3090, 583 FPS on RTX 4090

#### Application to Schedules

```python
# Instead of discrete time slices:
grid[person][activity][time] = occupied

# Model as continuous 4D field:
gaussian(person, activity, time, t) → density at spacetime point
```

**Benefits:**
- Smooth interpolation between any two time points
- See how a schedule "evolves" over a block
- Temporal coherence enforced by representation

---

### 2. WebGPU Rendering (Visionary)

#### The Platform

**Visionary** (December 2025) is a WebGPU-powered Gaussian Splatting platform that runs entirely in the browser.

**Repository:** https://github.com/Visionary-Laboratory/visionary
**Paper:** https://arxiv.org/html/2512.08478v1

#### Architecture

```
ONNX Pre-decoding → WebGPU Rendering → ONNX Post-processing
        ↓                  ↓                    ↓
   Neural decode     GPU splatting      Diffusion denoise
```

#### Performance

| Metric | Visionary | SparkJS (competitor) |
|--------|-----------|---------------------|
| Frame time (6M Gaussians) | **2.09ms** | 176.90ms |
| Sorting time | 0.58ms | 172.87ms |
| Speedup | **85×** | baseline |

#### Supported Variants

- Classic 3DGS
- MLP-based 3DGS (Scaffold-GS, Octree-GS)
- **4D Gaussian Splatting** for dynamic scenes
- Neural avatars (GauHuman, R3-Avatar, LHM)
- Generative post-processing networks

#### Application to Schedules

Replace our voxel renderer with Gaussian splatting:
- 85× faster rendering
- Blobs instead of cubes (more natural density visualization)
- 4DGS support for temporal animation
- ONNX integration for ML-enhanced views

---

### 3. Diffusion-Based Schedule Generation

#### The Insight

**SceneDiffuser** (CVPR 2023) proved diffusion can do planning/optimization, not just generation. It treats generation, optimization, and planning as iterations of denoising.

**DiffSplat** (ICLR 2025) generates 3D Gaussian Splats via diffusion.

**DiffGS** (OpenReview) represents Gaussians as functions and trains latent diffusion on them.

#### The Novel Idea

Train a diffusion model where:
- **Input:** Noisy/random schedule (as 3D/4D Gaussians)
- **Output:** Valid schedule that satisfies constraints
- **Denoising = Constraint satisfaction**

```python
# Pseudocode
class ScheduleDiffusion:
    def __init__(self):
        self.model = UNet3D(in_channels=1, out_channels=1)

    def denoise_step(self, noisy_schedule, timestep, constraints):
        """One denoising step conditioned on ACGME constraints."""
        noise_pred = self.model(noisy_schedule, timestep, constraints)
        return noisy_schedule - noise_pred

    def generate(self, constraints):
        """Generate valid schedule from noise."""
        schedule = torch.randn(shape=(time, people, activities))
        for t in reversed(range(1000)):
            schedule = self.denoise_step(schedule, t, constraints)
        return schedule
```

#### Why This Matters

This is fundamentally different from OR-Tools/constraint programming:
- **CP approach:** Define constraints explicitly, search for solutions
- **Diffusion approach:** Learn what valid schedules "look like," generate by denoising

The model learns implicit patterns that explicit rules might miss.

---

### 4. Physics-Informed Constraint Satisfaction

#### The Research

**PhysGaussian** and **Physics-Informed Deformable Gaussian Splatting (PIDG)** integrate differentiable physics with Gaussians:
- Constraints from continuum mechanics
- Differentiable simulation (MPM, PBD)
- End-to-end optimization through rendering

#### The Wild Idea

Model ACGME constraints as physical forces:

| Constraint | Physical Analogy |
|------------|------------------|
| 80-hour week limit | Pressure/compression force |
| 1-in-7 day off | Repulsion between consecutive assignments |
| Supervision ratio | Spring connecting resident↔faculty |
| Coverage requirement | Gravity pulling toward gaps |
| Conflict avoidance | Hard collision spheres |

#### Implementation Sketch

```python
class PhysicsScheduler:
    def __init__(self, schedule_gaussians):
        self.gaussians = schedule_gaussians

    def compute_forces(self):
        forces = []
        for g in self.gaussians:
            force = np.zeros(3)

            # 80-hour pressure: push away from overloaded regions
            weekly_hours = self.compute_weekly_hours(g)
            if weekly_hours > 80:
                force += self.pressure_gradient(g) * (weekly_hours - 80)

            # Supervision spring: pull residents toward faculty
            if g.is_resident:
                nearest_faculty = self.find_nearest_faculty(g)
                force += self.spring_force(g, nearest_faculty)

            # Coverage gravity: pull toward uncovered slots
            uncovered = self.find_uncovered_slots(g.time)
            force += self.gravity_toward(g, uncovered)

            forces.append(force)
        return forces

    def simulate(self, dt=0.01, steps=1000):
        """Run physics simulation until equilibrium."""
        for _ in range(steps):
            forces = self.compute_forces()
            for g, f in zip(self.gaussians, forces):
                g.position += f * dt
                g.velocity *= 0.99  # damping
        return self.gaussians
```

#### Why This is Novel

**Nobody is doing constraint satisfaction via physics simulation on Gaussian fields.**

The differentiability means you can:
1. Define a loss function (constraint violations)
2. Backprop through the physics simulation
3. Optimize Gaussian parameters end-to-end

This turns scheduling into a continuous optimization problem rather than discrete search.

---

### 5. 3D CNN Pathology Detection

#### The Concept

Medical imaging uses 3D CNNs to find tumors in CT scans. Schedules are now 3D tensors...

#### Application

```python
# Train on historical schedules labeled with outcomes
# (burnout, violations, resignations, complaints)
class Schedule3DCNN(nn.Module):
    def __init__(self):
        self.conv1 = nn.Conv3d(1, 32, kernel_size=3)
        self.conv2 = nn.Conv3d(32, 64, kernel_size=3)
        self.conv3 = nn.Conv3d(64, 128, kernel_size=3)
        self.fc = nn.Linear(128 * reduced_size, num_outcomes)

    def forward(self, schedule_tensor):
        x = F.relu(self.conv1(schedule_tensor))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = x.view(x.size(0), -1)
        return self.fc(x)

# Training
model = Schedule3DCNN()
model.fit(historical_schedule_tensors, outcome_labels)

# Inference: predict problems BEFORE they manifest
risk_map = model.predict(current_schedule.to_numpy_grid())
# Returns: 3D heatmap of "this region looks like past problems"
```

#### Why This is Powerful

You're not looking for explicit rules anymore. You're looking for **shapes** that correlate with bad outcomes - patterns that explicit ACGME rules might not capture but that historically predict problems.

This is **epidemiology on schedules**.

---

## Gap Analysis: What We Have vs Need

### Current Repository State

| Component | Status | Location |
|-----------|--------|----------|
| 3D voxel grid | ✅ Have | `backend/app/visualization/schedule_voxel.py` |
| NumPy export | ✅ Have | `to_numpy_grid()` method |
| Voxel types/interfaces | ✅ Have | Full type system |
| Frontend 3D view | ✅ Have | `frontend/src/features/voxel-schedule/` |

### What We Need to Acquire

| Component | Effort | Source | Purpose |
|-----------|--------|--------|---------|
| Gaussian primitive | ~200 LOC | Write ourselves | Basic Gaussian3D class |
| Covariance handling | ~100 LOC | Write ourselves | Shape/orientation |
| PLY exporter | ~150 LOC | Standard format | Interop with viewers |
| gsplat integration | Dependency | `pip install gsplat` | GPU rendering |
| Visionary WebGPU | Integration | MIT license | Browser rendering |
| 4D Gaussian support | ~300 LOC | Extend primitives | Temporal dimension |
| Diffusion training loop | ~500 LOC | PyTorch | Generative scheduling |
| Physics layer | ~400 LOC | Warp or Taichi | Constraint forces |

### Recommended Libraries

| Library | Purpose | License |
|---------|---------|---------|
| **gsplat** | Python Gaussian splatting | Apache 2.0 |
| **Visionary** | WebGPU browser rendering | MIT |
| **Warp** | Differentiable physics (NVIDIA) | Apache 2.0 |
| **Taichi** | Differentiable physics (portable) | Apache 2.0 |
| **diffusers** | Diffusion model training | Apache 2.0 |

---

## Research Landscape

### Who's Doing Related Work

| Area | Status | Gap |
|------|--------|-----|
| Photorealistic 3DGS | Very active (SHARP, etc.) | Not abstract data |
| Scientific visualization | Growing (isosurfaces) | Physical data only |
| 4D dynamic scenes | Active research | Video/motion only |
| Physics-informed GS | Emerging | Physical objects only |
| Diffusion + Gaussians | ICLR 2025 papers | 3D content only |

### The Unexplored Territory

**Nobody is applying Gaussian Splatting to discrete structured data:**
- Schedules
- Graphs/networks
- Resource allocation
- Constraint satisfaction problems

This is genuinely novel research territory.

### Potential Publications

1. **"Physics-Informed Gaussian Splatting for Constraint Satisfaction"**
   - Model constraints as forces
   - Differentiable scheduling
   - Novel contribution to both GS and CSP literature

2. **"Diffusion Models for Schedule Generation"**
   - Learn from historical data
   - Generate valid schedules by denoising
   - Novel application of diffusion to structured data

3. **"3D CNN Pathology Detection for Workforce Scheduling"**
   - Medical imaging techniques for schedule analysis
   - Predict burnout/violations from spatial patterns
   - Cross-domain transfer from radiology

---

## Implementation Roadmap

### Phase 1: Foundation (Low Risk)

1. **Add Gaussian primitive alongside voxels**
   ```python
   class ScheduleGaussian:
       mean: np.ndarray
       covariance: np.ndarray
       color: np.ndarray
       opacity: float
   ```

2. **Implement voxel-to-Gaussian conversion**
   ```python
   def voxel_to_gaussian(voxel: ScheduleVoxel) -> ScheduleGaussian:
       return ScheduleGaussian(
           mean=np.array([voxel.x, voxel.y, voxel.z]),
           covariance=np.eye(3) * 0.3,
           color=voxel.color.to_array(),
           opacity=voxel.opacity
       )
   ```

3. **Add PLY export for standard viewer compatibility**

### Phase 2: Rendering (Medium Risk)

1. **Integrate Visionary for WebGPU rendering**
2. **Replace/augment voxel frontend with splatting**
3. **Add 4DGS support for temporal visualization**

### Phase 3: Novel Research (High Risk/Reward)

1. **Prototype physics-informed constraint layer**
2. **Train diffusion model on historical schedules**
3. **Implement 3D CNN for pattern detection**

---

## References

### Core Papers

1. **3D Gaussian Splatting** (Kerbl et al., SIGGRAPH 2023)
   - Original 3DGS paper
   - https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/

2. **SHARP** (Apple, December 2025)
   - Single-image to 3D Gaussian
   - https://github.com/apple/ml-sharp

3. **4D Gaussian Splatting** (Wu et al., CVPR 2024)
   - Dynamic scene rendering
   - https://github.com/hustvl/4DGaussians

4. **4DGS-1K** (March 2025)
   - 1000+ FPS rendering
   - https://arxiv.org/abs/2503.16422

### Diffusion + Gaussians

5. **DiffSplat** (ICLR 2025)
   - Diffusion for Gaussian generation
   - https://github.com/chenguolin/DiffSplat

6. **DiffGS** (OpenReview 2025)
   - Functional Gaussian Splatting Diffusion
   - https://openreview.net/forum?id=6zROYoHlcp

7. **SceneDiffuser** (CVPR 2023)
   - Diffusion for planning/optimization
   - https://arxiv.org/abs/2301.06015

### Physics-Informed

8. **PhysGaussian**
   - Physics-integrated 3D Gaussians
   - https://www.researchgate.net/publication/384181082

9. **Physics-Informed Deformable Gaussian Splatting**
   - https://www.emergentmind.com/topics/physics-informed-deformable-gaussian-splatting-pidg

### WebGPU

10. **Visionary** (December 2025)
    - WebGPU Gaussian platform
    - https://arxiv.org/html/2512.08478v1
    - https://github.com/Visionary-Laboratory/visionary

---

## Conclusion

The 3D voxel representation unlocks more than just visualization. By extending to Gaussian Splatting, we gain:

1. **Computational tools** from medical imaging, robotics, and graphics
2. **Differentiability** for end-to-end optimization
3. **Physics simulation** for constraint satisfaction
4. **Generative models** for schedule creation
5. **Real-time rendering** via WebGPU

The most novel opportunity is **physics-informed constraint satisfaction** - modeling ACGME rules as physical forces and letting schedules "relax" to valid configurations. This is unexplored territory that could yield both practical tools and academic publications.

---

*Last updated: 2026-01-13*
