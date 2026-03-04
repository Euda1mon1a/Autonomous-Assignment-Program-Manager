# Voxel Visualization Feature Designs

> **Created:** 2026-01-13 | **Based on:** PR #700 (3D Voxel Command Center)
> **Status:** Design Sketches for Future Implementation

---

## Table of Contents

1. [Real Data Integration (Phase 2)](#1-real-data-integration-phase-2)
2. [Resilience Overlay for Voxel Grid](#2-resilience-overlay-for-voxel-grid)
3. [Catastrophe Surface Visualization](#3-catastrophe-surface-visualization)
4. [Spin Glass Diversity View](#4-spin-glass-diversity-view)
5. [Time Crystal Periodicity Animation](#5-time-crystal-periodicity-animation)
6. [Unified Ops Hub with 3D View](#6-unified-ops-hub-with-3d-view)
7. [Phase Transition Early Warning Aura](#7-phase-transition-early-warning-aura)
8. [N-1/N-2 Contingency What-If Mode](#8-n-1n-2-contingency-what-if-mode)
9. [Holographic Hub Integration](#9-holographic-hub-integration)
10. [WebXR/Vision Pro Foundation](#10-webxrvision-pro-foundation)

---

## 1. Real Data Integration (Phase 2)

**Priority:** Critical | **Complexity:** Medium

Connect the 3D Voxel Command Center to real schedule data via the existing backend endpoint.

### Frontend Hook

```typescript
// frontend/src/features/voxel-schedule/hooks/useVoxelGridData.ts

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { VoxelGridData } from '../types';

interface UseVoxelGridDataParams {
  startDate: string;  // ISO date
  endDate: string;
  personIds?: number[];
  activityTypes?: string[];
  includeViolations?: boolean;
}

export function useVoxelGridData({
  startDate,
  endDate,
  personIds,
  activityTypes,
  includeViolations = true,
}: UseVoxelGridDataParams) {
  return useQuery<VoxelGridData>({
    queryKey: ['voxel-grid', startDate, endDate, personIds, activityTypes],
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        include_violations: String(includeViolations),
      });

      personIds?.forEach(id => params.append('person_ids', String(id)));
      rotationTypes?.forEach(type => params.append('rotation_types', type));

      const response = await api.get(`/api/visualization/voxel-grid?${params}`);
      return response.data;
    },
    staleTime: 30_000,  // 30 seconds
    refetchOnWindowFocus: false,
  });
}

// Conflict detection hook
export function useVoxelConflicts(startDate: string, endDate: string) {
  return useQuery({
    queryKey: ['voxel-conflicts', startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/api/visualization/voxel-grid/conflicts', {
        params: { start_date: startDate, end_date: endDate },
      });
      return response.data;
    },
  });
}

// Coverage gaps hook
export function useVoxelCoverageGaps(
  startDate: string,
  endDate: string,
  requiredActivityTypes: string[] = ['clinic']
) {
  return useQuery({
    queryKey: ['voxel-coverage-gaps', startDate, endDate, requiredActivityTypes],
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });
      requiredRotationTypes.forEach(t => params.append('required_rotation_types', t));

      const response = await api.get(`/api/visualization/voxel-grid/coverage-gaps?${params}`);
      return response.data;
    },
  });
}
```

### Updated VoxelScheduleView3D Integration

```typescript
// frontend/src/features/voxel-schedule/VoxelScheduleView3D.tsx (additions)

import { useVoxelGridData } from './hooks/useVoxelGridData';

interface VoxelScheduleView3DProps {
  startDate: string;
  endDate: string;
  personIds?: number[];
  activityTypes?: string[];
  useDemoData?: boolean;  // Keep for testing
}

export function VoxelScheduleView3D({
  startDate,
  endDate,
  personIds,
  activityTypes,
  useDemoData = false,
}: VoxelScheduleView3DProps) {
  // Real data fetch
  const { data: gridData, isLoading, error } = useVoxelGridData({
    startDate,
    endDate,
    personIds,
    activityTypes,
  });

  // Transform API data to render format
  const voxels = useMemo(() => {
    if (useDemoData) return DEMO_VOXELS;
    if (!gridData?.voxels) return [];

    return gridData.voxels.map(v => ({
      id: v.identity.assignmentId,
      position: { x: v.position.x, y: v.position.y, z: v.position.z },
      person: v.identity.personName,
      activity: v.identity.activityName,
      color: v.visual.color,
      isConflict: v.state.isConflict,
      isViolation: v.state.isViolation,
      violationDetails: v.state.violationDetails,
      hours: v.metadata.hours,
      role: v.metadata.role,
    }));
  }, [gridData, useDemoData]);

  // Statistics panel data
  const stats = gridData?.statistics ?? {
    totalAssignments: voxels.length,
    totalConflicts: voxels.filter(v => v.isConflict).length,
    totalViolations: voxels.filter(v => v.isViolation).length,
    coveragePercentage: 0,
  };

  if (isLoading) {
    return <VoxelLoadingState />;
  }

  if (error) {
    return <VoxelErrorState error={error} />;
  }

  return (
    <Canvas>
      {/* ... existing Canvas content ... */}
      {voxels.map(voxel => (
        <AnimatedVoxel key={voxel.id} voxel={voxel} is3D={is3D} />
      ))}
    </Canvas>
  );
}
```

### Filter Controls Component

```typescript
// frontend/src/features/voxel-schedule/VoxelFilterControls.tsx

import { useState } from 'react';
import { DateRangePicker } from '@/components/ui/DateRangePicker';
import { PersonMultiSelect } from '@/components/PersonMultiSelect';
import { ActivityTypeSelect } from '@/components/ActivityTypeSelect';

interface VoxelFilterControlsProps {
  onFilterChange: (filters: VoxelFilters) => void;
  initialFilters?: VoxelFilters;
}

interface VoxelFilters {
  startDate: string;
  endDate: string;
  personIds: number[];
  activityTypes: string[];
}

export function VoxelFilterControls({
  onFilterChange,
  initialFilters,
}: VoxelFilterControlsProps) {
  const [filters, setFilters] = useState<VoxelFilters>(initialFilters ?? {
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    personIds: [],
    activityTypes: [],
  });

  const handleChange = (partial: Partial<VoxelFilters>) => {
    const updated = { ...filters, ...partial };
    setFilters(updated);
    onFilterChange(updated);
  };

  return (
    <div className="flex flex-wrap gap-4 p-4 bg-gray-900/50 rounded-lg">
      <DateRangePicker
        startDate={filters.startDate}
        endDate={filters.endDate}
        onChange={(start, end) => handleChange({ startDate: start, endDate: end })}
      />

      <PersonMultiSelect
        value={filters.personIds}
        onChange={personIds => handleChange({ personIds })}
        placeholder="Filter by person..."
      />

      <ActivityTypeSelect
        value={filters.activityTypes}
        onChange={activityTypes => handleChange({ activityTypes })}
        placeholder="Filter by activity..."
      />

      <button
        onClick={() => handleChange({
          personIds: [],
          activityTypes: [],
        })}
        className="px-3 py-1 text-sm text-gray-400 hover:text-white"
      >
        Clear Filters
      </button>
    </div>
  );
}
```

---

## 2. Resilience Overlay for Voxel Grid

**Priority:** High | **Complexity:** Low

Visualize resilience metrics (utilization, burnout Rt, defense level) as visual effects on voxels.

### Resilience Data Hook

```typescript
// frontend/src/features/voxel-schedule/hooks/useResilienceOverlay.ts

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface ResilienceMetrics {
  utilizationByPerson: Record<number, number>;  // personId -> utilization %
  burnoutRtByPerson: Record<number, number>;    // personId -> Rt value
  defenseLevel: 'NORMAL' | 'ELEVATED' | 'HIGH' | 'CRITICAL';
  keystoneFacultyIds: number[];  // N-1 critical personnel
  warningMessages: string[];
}

export function useResilienceOverlay(startDate: string, endDate: string) {
  // Fetch utilization
  const utilization = useQuery({
    queryKey: ['resilience-utilization', startDate, endDate],
    queryFn: () => api.get('/api/v1/resilience/utilization', {
      params: { start_date: startDate, end_date: endDate },
    }).then(r => r.data),
  });

  // Fetch burnout Rt
  const burnoutRt = useQuery({
    queryKey: ['resilience-burnout-rt'],
    queryFn: () => api.get('/api/v1/resilience/burnout-rt').then(r => r.data),
  });

  // Fetch defense level
  const defenseLevel = useQuery({
    queryKey: ['resilience-defense-level'],
    queryFn: () => api.get('/api/v1/resilience/defense-level').then(r => r.data),
  });

  // Fetch keystone analysis
  const keystone = useQuery({
    queryKey: ['resilience-keystone'],
    queryFn: () => api.get('/api/v1/resilience/keystone-analysis').then(r => r.data),
  });

  return {
    isLoading: utilization.isLoading || burnoutRt.isLoading,
    metrics: {
      utilizationByPerson: utilization.data?.byPerson ?? {},
      burnoutRtByPerson: burnoutRt.data?.byPerson ?? {},
      defenseLevel: defenseLevel.data?.level ?? 'NORMAL',
      keystoneFacultyIds: keystone.data?.keystoneIds ?? [],
      warningMessages: [
        ...(utilization.data?.warnings ?? []),
        ...(burnoutRt.data?.warnings ?? []),
      ],
    } as ResilienceMetrics,
  };
}
```

### Enhanced Voxel with Resilience Glow

```typescript
// frontend/src/features/voxel-schedule/components/ResilienceVoxel.tsx

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { animated, useSpring } from '@react-spring/three';
import * as THREE from 'three';

interface ResilienceVoxelProps {
  voxel: VoxelData;
  resilience: {
    utilization: number;  // 0-100
    burnoutRt: number;    // 0-2+
    isKeystone: boolean;
  };
  is3D: boolean;
}

export function ResilienceVoxel({ voxel, resilience, is3D }: ResilienceVoxelProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  // Calculate resilience-based visual properties
  const resilienceVisuals = useMemo(() => {
    const { utilization, burnoutRt, isKeystone } = resilience;

    // Color shifts based on stress
    let emissiveIntensity = 0;
    let emissiveColor = '#000000';

    if (utilization > 90) {
      emissiveColor = '#EF4444';  // Red - critical
      emissiveIntensity = 0.5;
    } else if (utilization > 80) {
      emissiveColor = '#F97316';  // Orange - warning
      emissiveIntensity = 0.3;
    } else if (utilization > 70) {
      emissiveColor = '#EAB308';  // Yellow - elevated
      emissiveIntensity = 0.2;
    }

    // Burnout Rt pulse effect
    const shouldPulse = burnoutRt > 1.1;

    // Keystone marker
    const scale = isKeystone ? 1.3 : 1.0;
    const outlineColor = isKeystone ? '#FFD700' : null;  // Gold for keystone

    return {
      emissiveColor,
      emissiveIntensity,
      shouldPulse,
      scale,
      outlineColor,
    };
  }, [resilience]);

  // Animate pulsing for high burnout Rt
  useFrame(({ clock }) => {
    if (!meshRef.current || !resilienceVisuals.shouldPulse) return;

    const material = meshRef.current.material as THREE.MeshStandardMaterial;
    const pulse = Math.sin(clock.elapsedTime * 3) * 0.5 + 0.5;
    material.emissiveIntensity = resilienceVisuals.emissiveIntensity * (0.5 + pulse * 0.5);
  });

  const { position, scale } = useSpring({
    position: is3D
      ? [voxel.position.x, voxel.position.y, voxel.position.z]
      : [voxel.position.x, 0.5, voxel.position.y],
    scale: resilienceVisuals.scale,
    config: { mass: 1, tension: 170, friction: 26 },
  });

  return (
    <group>
      <animated.mesh
        ref={meshRef}
        position={position as any}
        scale={scale}
      >
        <boxGeometry args={[0.9, 0.9, 0.9]} />
        <meshStandardMaterial
          color={voxel.color}
          emissive={resilienceVisuals.emissiveColor}
          emissiveIntensity={resilienceVisuals.emissiveIntensity}
          metalness={0.1}
          roughness={0.8}
        />
      </animated.mesh>

      {/* Keystone outline */}
      {resilienceVisuals.outlineColor && (
        <animated.lineSegments position={position as any} scale={scale}>
          <edgesGeometry args={[new THREE.BoxGeometry(0.95, 0.95, 0.95)]} />
          <lineBasicMaterial color={resilienceVisuals.outlineColor} linewidth={2} />
        </animated.lineSegments>
      )}
    </group>
  );
}
```

### Resilience Legend Panel

```typescript
// frontend/src/features/voxel-schedule/components/ResilienceLegend.tsx

interface ResilienceLegendProps {
  defenseLevel: string;
  warningCount: number;
}

export function ResilienceLegend({ defenseLevel, warningCount }: ResilienceLegendProps) {
  const defenseLevelColors: Record<string, string> = {
    NORMAL: 'bg-green-500',
    ELEVATED: 'bg-yellow-500',
    HIGH: 'bg-orange-500',
    CRITICAL: 'bg-red-500',
  };

  return (
    <div className="absolute bottom-4 left-4 bg-black/70 p-4 rounded-lg text-white text-sm">
      <h4 className="font-semibold mb-2">Resilience Overlay</h4>

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded ${defenseLevelColors[defenseLevel]}`} />
          <span>Defense Level: {defenseLevel}</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-yellow-500 animate-pulse" />
          <span>Utilization &gt;70%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-orange-500 animate-pulse" />
          <span>Utilization &gt;80%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-red-500 animate-pulse" />
          <span>Utilization &gt;90% (Critical)</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded border-2 border-yellow-400" />
          <span>Keystone Personnel (N-1)</span>
        </div>

        {warningCount > 0 && (
          <div className="mt-2 text-orange-400">
            ⚠️ {warningCount} warning{warningCount !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 3. Catastrophe Surface Visualization

**Priority:** Medium | **Complexity:** High (showcase feature)

Render the cusp catastrophe bifurcation surface from `exotic/catastrophe.py` in 3D space.

### Backend Endpoint for Catastrophe Data

```python
# backend/app/api/routes/exotic.py (addition)

from fastapi import APIRouter, Query
from app.resilience.exotic.catastrophe import CatastropheTheory

router = APIRouter(prefix="/api/v1/resilience/exotic", tags=["exotic"])

@router.get("/catastrophe/surface")
async def get_catastrophe_surface(
    a_min: float = Query(-2.0, description="Min asymmetry"),
    a_max: float = Query(2.0, description="Max asymmetry"),
    b_min: float = Query(-2.0, description="Min bias"),
    b_max: float = Query(2.0, description="Max bias"),
    resolution: int = Query(50, ge=10, le=100, description="Grid resolution"),
):
    """
    Generate cusp catastrophe surface data for 3D visualization.

    Returns a grid of potential values V(x; a, b) = x^4/4 + ax^2/2 + bx
    along with bifurcation curve (where a^3 + 27b^2 = 0).
    """
    ct = CatastropheTheory()

    import numpy as np

    a_vals = np.linspace(a_min, a_max, resolution)
    b_vals = np.linspace(b_min, b_max, resolution)

    # Calculate surface points
    surface_points = []
    for a in a_vals:
        for b in b_vals:
            equilibria = ct.find_equilibria(a, b)
            for x_eq in equilibria:
                potential = ct.calculate_cusp_potential(x_eq, a, b)
                surface_points.append({
                    "a": float(a),
                    "b": float(b),
                    "x": float(x_eq),
                    "potential": float(potential),
                    "isStable": ct.is_stable_equilibrium(x_eq, a),
                })

    # Calculate bifurcation curve (cusp)
    bifurcation_points = []
    for a in np.linspace(a_min, 0, resolution // 2):
        # a^3 + 27b^2 = 0 => b = ±sqrt(-a^3/27)
        if a < 0:
            b_crit = np.sqrt(-a**3 / 27)
            bifurcation_points.append({"a": float(a), "b": float(b_crit)})
            bifurcation_points.append({"a": float(a), "b": float(-b_crit)})

    return {
        "surface": surface_points,
        "bifurcation": bifurcation_points,
        "cuspPoint": {"a": 0, "b": 0},
        "metadata": {
            "aRange": [a_min, a_max],
            "bRange": [b_min, b_max],
            "resolution": resolution,
        },
    }


@router.get("/catastrophe/current-state")
async def get_catastrophe_current_state(db: AsyncSession = Depends(get_db)):
    """
    Map current schedule state to catastrophe parameters.

    a (asymmetry) = workload imbalance metric
    b (bias) = cumulative stress/fatigue metric
    """
    ct = CatastropheTheory()

    # Calculate from real metrics (pseudo-code)
    # workload_variance = await calculate_workload_variance(db)
    # cumulative_stress = await calculate_cumulative_stress(db)

    # Placeholder mapping
    a = -0.5  # Moderate asymmetry
    b = 0.3   # Some bias toward stress

    equilibria = ct.find_equilibria(a, b)
    current_x = equilibria[0] if equilibria else 0

    # Check proximity to bifurcation
    discriminant = a**3 + 27 * b**2
    near_catastrophe = discriminant < 0.5  # Close to cusp

    return {
        "a": a,
        "b": b,
        "currentState": current_x,
        "potential": ct.calculate_cusp_potential(current_x, a, b),
        "nearCatastrophe": near_catastrophe,
        "distanceToCusp": abs(discriminant),
        "riskLevel": "HIGH" if near_catastrophe else "NORMAL",
    }
```

### Frontend Catastrophe Surface Component

```typescript
// frontend/src/features/voxel-schedule/components/CatastropheSurface3D.tsx

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useQuery } from '@tanstack/react-query';
import * as THREE from 'three';
import { api } from '@/lib/api';

interface CatastropheSurfaceProps {
  showBifurcation?: boolean;
  showCurrentState?: boolean;
}

export function CatastropheSurface3D({
  showBifurcation = true,
  showCurrentState = true,
}: CatastropheSurfaceProps) {
  const currentStateRef = useRef<THREE.Mesh>(null);

  // Fetch surface data
  const { data: surfaceData } = useQuery({
    queryKey: ['catastrophe-surface'],
    queryFn: () => api.get('/api/v1/resilience/exotic/catastrophe/surface').then(r => r.data),
  });

  // Fetch current state
  const { data: currentState } = useQuery({
    queryKey: ['catastrophe-current'],
    queryFn: () => api.get('/api/v1/resilience/exotic/catastrophe/current-state').then(r => r.data),
  });

  // Build surface geometry
  const surfaceGeometry = useMemo(() => {
    if (!surfaceData?.surface) return null;

    const geometry = new THREE.BufferGeometry();
    const positions: number[] = [];
    const colors: number[] = [];

    // Create point cloud for surface
    surfaceData.surface.forEach((point: any) => {
      positions.push(point.a, point.x, point.b);  // a=x, x=y, b=z in 3D space

      // Color by stability
      if (point.isStable) {
        colors.push(0.2, 0.6, 1.0);  // Blue for stable
      } else {
        colors.push(1.0, 0.3, 0.3);  // Red for unstable
      }
    });

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    return geometry;
  }, [surfaceData]);

  // Build bifurcation curve
  const bifurcationGeometry = useMemo(() => {
    if (!surfaceData?.bifurcation) return null;

    const points = surfaceData.bifurcation.map((p: any) =>
      new THREE.Vector3(p.a, 0, p.b)
    );

    return new THREE.BufferGeometry().setFromPoints(points);
  }, [surfaceData]);

  // Animate current state marker if near catastrophe
  useFrame(({ clock }) => {
    if (!currentStateRef.current || !currentState?.nearCatastrophe) return;

    const pulse = Math.sin(clock.elapsedTime * 4) * 0.2 + 1;
    currentStateRef.current.scale.setScalar(pulse);
  });

  if (!surfaceData) return null;

  return (
    <group position={[0, 5, 0]} scale={2}>
      {/* Axis labels */}
      <axisHelper args={[3]} />

      {/* Surface points */}
      {surfaceGeometry && (
        <points geometry={surfaceGeometry}>
          <pointsMaterial
            size={0.05}
            vertexColors
            transparent
            opacity={0.7}
          />
        </points>
      )}

      {/* Bifurcation curve (cusp) */}
      {showBifurcation && bifurcationGeometry && (
        <line geometry={bifurcationGeometry}>
          <lineBasicMaterial color="#FFD700" linewidth={3} />
        </line>
      )}

      {/* Cusp point marker */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[0.1, 16, 16]} />
        <meshStandardMaterial color="#FFD700" emissive="#FFD700" emissiveIntensity={0.5} />
      </mesh>

      {/* Current state marker */}
      {showCurrentState && currentState && (
        <mesh
          ref={currentStateRef}
          position={[currentState.a, currentState.currentState, currentState.b]}
        >
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial
            color={currentState.nearCatastrophe ? '#EF4444' : '#22C55E'}
            emissive={currentState.nearCatastrophe ? '#EF4444' : '#22C55E'}
            emissiveIntensity={0.3}
          />
        </mesh>
      )}

      {/* Labels */}
      <Html position={[3.5, 0, 0]}>
        <div className="text-white text-xs">Asymmetry (a)</div>
      </Html>
      <Html position={[0, 3.5, 0]}>
        <div className="text-white text-xs">State (x)</div>
      </Html>
      <Html position={[0, 0, 3.5]}>
        <div className="text-white text-xs">Bias (b)</div>
      </Html>
    </group>
  );
}
```

### Catastrophe Info Panel

```typescript
// frontend/src/features/voxel-schedule/components/CatastropheInfoPanel.tsx

interface CatastropheInfoPanelProps {
  currentState: {
    a: number;
    b: number;
    currentState: number;
    nearCatastrophe: boolean;
    distanceToCusp: number;
    riskLevel: string;
  } | null;
}

export function CatastropheInfoPanel({ currentState }: CatastropheInfoPanelProps) {
  if (!currentState) return null;

  return (
    <div className="absolute top-4 right-4 bg-black/80 p-4 rounded-lg text-white text-sm max-w-xs">
      <h4 className="font-semibold mb-2 flex items-center gap-2">
        🌀 Catastrophe Analysis
        {currentState.nearCatastrophe && (
          <span className="px-2 py-0.5 bg-red-500 rounded text-xs animate-pulse">
            NEAR TIPPING POINT
          </span>
        )}
      </h4>

      <div className="space-y-1 text-gray-300">
        <div>Asymmetry (a): {currentState.a.toFixed(3)}</div>
        <div>Bias (b): {currentState.b.toFixed(3)}</div>
        <div>Current State (x): {currentState.currentState.toFixed(3)}</div>
        <div>Distance to Cusp: {currentState.distanceToCusp.toFixed(3)}</div>
      </div>

      <div className="mt-3 p-2 bg-gray-800 rounded text-xs">
        <strong>Interpretation:</strong>
        <p className="mt-1">
          {currentState.nearCatastrophe
            ? 'System is near a bifurcation point. Small changes in workload or stress could cause sudden state transition (morale collapse).'
            : 'System is in stable region. Gradual changes will produce gradual responses.'}
        </p>
      </div>
    </div>
  );
}
```

---

## 4. Spin Glass Diversity View

**Priority:** Low | **Complexity:** High (research feature)

Show multiple schedule alternatives as overlapping ghost voxels using spin glass ensemble.

### Backend Spin Glass Ensemble Endpoint

```python
# backend/app/api/routes/exotic.py (addition)

@router.get("/spin-glass/ensemble")
async def get_spin_glass_ensemble(
    start_date: date = Query(...),
    end_date: date = Query(...),
    num_replicas: int = Query(5, ge=2, le=10, description="Number of alternative schedules"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate spin glass ensemble of schedule alternatives.

    Returns multiple schedule "replicas" showing different valid assignments
    for the same constraints, plus overlap analysis.
    """
    from app.resilience.exotic.spin_glass import SpinGlassScheduler

    sg = SpinGlassScheduler()

    # Get current schedule as replica 0
    current_voxels = await get_current_voxel_grid(db, start_date, end_date)

    # Generate alternative schedules via replica exchange
    replicas = [{"replicaId": 0, "voxels": current_voxels, "isCurrent": True}]

    for i in range(1, num_replicas):
        # Generate alternative at different "temperature"
        alt_voxels = sg.generate_replica(
            constraints=await get_constraints(db),
            temperature=1.0 + i * 0.5,  # Higher T = more exploration
            seed=i,
        )
        replicas.append({
            "replicaId": i,
            "voxels": alt_voxels,
            "isCurrent": False,
            "temperature": 1.0 + i * 0.5,
        })

    # Calculate overlap matrix (agreement between replicas)
    overlap_matrix = sg.calculate_overlap_matrix(replicas)

    # Find stable assignments (high agreement across replicas)
    stable_assignments = []
    flexible_assignments = []

    for voxel in current_voxels:
        agreement = sum(
            1 for r in replicas[1:]
            if any(v["position"] == voxel["position"] and v["personId"] == voxel["personId"]
                   for v in r["voxels"])
        ) / (num_replicas - 1)

        if agreement > 0.7:
            stable_assignments.append({**voxel, "agreement": agreement})
        else:
            flexible_assignments.append({**voxel, "agreement": agreement})

    # Calculate frustration (constraint conflicts)
    frustration = sg.calculate_frustration(current_voxels)

    return {
        "replicas": replicas,
        "overlapMatrix": overlap_matrix,
        "stableAssignments": stable_assignments,
        "flexibleAssignments": flexible_assignments,
        "frustration": frustration,
        "metadata": {
            "numReplicas": num_replicas,
            "dateRange": {"start": start_date, "end": end_date},
        },
    }
```

### Frontend Spin Glass View Component

```typescript
// frontend/src/features/voxel-schedule/components/SpinGlassEnsembleView.tsx

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { animated, useSpring } from '@react-spring/three';
import * as THREE from 'three';

interface SpinGlassEnsembleViewProps {
  startDate: string;
  endDate: string;
  showGhosts?: boolean;
}

export function SpinGlassEnsembleView({
  startDate,
  endDate,
  showGhosts = true,
}: SpinGlassEnsembleViewProps) {
  const [selectedReplica, setSelectedReplica] = useState<number | null>(null);
  const [showStableOnly, setShowStableOnly] = useState(false);

  const { data: ensemble } = useQuery({
    queryKey: ['spin-glass-ensemble', startDate, endDate],
    queryFn: () => api.get('/api/v1/resilience/exotic/spin-glass/ensemble', {
      params: { start_date: startDate, end_date: endDate, num_replicas: 5 },
    }).then(r => r.data),
  });

  // Current schedule voxels (solid)
  const currentVoxels = useMemo(() => {
    return ensemble?.replicas?.[0]?.voxels ?? [];
  }, [ensemble]);

  // Ghost voxels from alternative schedules
  const ghostVoxels = useMemo(() => {
    if (!showGhosts || !ensemble?.replicas) return [];

    return ensemble.replicas
      .slice(1)  // Skip current (replica 0)
      .filter((r: any) => selectedReplica === null || r.replicaId === selectedReplica)
      .flatMap((r: any) => r.voxels.map((v: any) => ({
        ...v,
        replicaId: r.replicaId,
        opacity: 0.3,
      })));
  }, [ensemble, showGhosts, selectedReplica]);

  return (
    <group>
      {/* Current schedule (solid voxels) */}
      {currentVoxels.map((voxel: any) => {
        const isStable = ensemble?.stableAssignments?.some(
          (s: any) => s.position.x === voxel.position.x && s.position.y === voxel.position.y
        );

        if (showStableOnly && !isStable) return null;

        return (
          <StabilityVoxel
            key={`current-${voxel.id}`}
            voxel={voxel}
            isStable={isStable}
            agreement={ensemble?.stableAssignments?.find(
              (s: any) => s.id === voxel.id
            )?.agreement ?? 0}
          />
        );
      })}

      {/* Ghost voxels from alternatives */}
      {ghostVoxels.map((voxel: any, i: number) => (
        <GhostVoxel
          key={`ghost-${voxel.replicaId}-${i}`}
          voxel={voxel}
          replicaId={voxel.replicaId}
        />
      ))}

      {/* Frustration indicator */}
      {ensemble?.frustration && (
        <FrustrationIndicator frustration={ensemble.frustration} />
      )}
    </group>
  );
}

// Solid voxel with stability indicator
function StabilityVoxel({ voxel, isStable, agreement }: any) {
  // Green = stable (high agreement), Yellow = flexible (low agreement)
  const color = useMemo(() => {
    if (isStable) return '#22C55E';  // Green
    if (agreement > 0.4) return '#EAB308';  // Yellow
    return '#F97316';  // Orange (very flexible)
  }, [isStable, agreement]);

  return (
    <mesh position={[voxel.position.x, voxel.position.y, voxel.position.z]}>
      <boxGeometry args={[0.9, 0.9, 0.9]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

// Transparent ghost voxel from alternative schedule
function GhostVoxel({ voxel, replicaId }: any) {
  // Different colors for different replicas
  const replicaColors = ['#60A5FA', '#A78BFA', '#F472B6', '#34D399', '#FBBF24'];
  const color = replicaColors[(replicaId - 1) % replicaColors.length];

  return (
    <mesh position={[voxel.position.x, voxel.position.y, voxel.position.z]}>
      <boxGeometry args={[0.85, 0.85, 0.85]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={0.25}
        depthWrite={false}
      />
    </mesh>
  );
}

// Visual indicator of constraint frustration
function FrustrationIndicator({ frustration }: { frustration: number }) {
  // Higher frustration = more intense red glow around scene
  const intensity = Math.min(frustration / 100, 1);

  return (
    <pointLight
      position={[0, 10, 0]}
      color="#EF4444"
      intensity={intensity * 2}
      distance={50}
    />
  );
}
```

### Spin Glass Control Panel

```typescript
// frontend/src/features/voxel-schedule/components/SpinGlassControls.tsx

interface SpinGlassControlsProps {
  ensemble: any;
  selectedReplica: number | null;
  onSelectReplica: (id: number | null) => void;
  showStableOnly: boolean;
  onToggleStableOnly: (show: boolean) => void;
}

export function SpinGlassControls({
  ensemble,
  selectedReplica,
  onSelectReplica,
  showStableOnly,
  onToggleStableOnly,
}: SpinGlassControlsProps) {
  return (
    <div className="absolute bottom-4 right-4 bg-black/80 p-4 rounded-lg text-white text-sm">
      <h4 className="font-semibold mb-3">🧊 Spin Glass Ensemble</h4>

      <div className="space-y-3">
        {/* Replica selector */}
        <div>
          <label className="text-xs text-gray-400">Show Alternative</label>
          <select
            value={selectedReplica ?? 'all'}
            onChange={e => onSelectReplica(e.target.value === 'all' ? null : Number(e.target.value))}
            className="w-full mt-1 bg-gray-700 rounded px-2 py-1"
          >
            <option value="all">All Alternatives</option>
            {ensemble?.replicas?.slice(1).map((r: any) => (
              <option key={r.replicaId} value={r.replicaId}>
                Replica {r.replicaId} (T={r.temperature})
              </option>
            ))}
          </select>
        </div>

        {/* Stable only toggle */}
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={showStableOnly}
            onChange={e => onToggleStableOnly(e.target.checked)}
            className="rounded"
          />
          <span>Show stable assignments only</span>
        </label>

        {/* Stats */}
        <div className="pt-2 border-t border-gray-600 space-y-1">
          <div>Stable: {ensemble?.stableAssignments?.length ?? 0}</div>
          <div>Flexible: {ensemble?.flexibleAssignments?.length ?? 0}</div>
          <div>Frustration: {(ensemble?.frustration ?? 0).toFixed(2)}</div>
        </div>

        {/* Legend */}
        <div className="pt-2 border-t border-gray-600 text-xs space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-green-500" />
            <span>Stable (locked in)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-yellow-500" />
            <span>Somewhat flexible</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-orange-500" />
            <span>Very flexible</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-blue-400/50" />
            <span>Ghost (alternative)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 5. Time Crystal Periodicity Animation

**Priority:** Medium | **Complexity:** Medium

Animate voxels over time to show schedule stability using time crystal concepts.

### Backend Time Crystal Animation Data

```python
# backend/app/api/routes/exotic.py (addition)

@router.get("/time-crystal/animation")
async def get_time_crystal_animation(
    num_weeks: int = Query(4, ge=2, le=12),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate time crystal animation data showing schedule evolution over weeks.

    Returns weekly snapshots with stability scores per assignment.
    """
    from app.resilience.exotic.time_crystal import TimeCrystalAnalyzer

    tc = TimeCrystalAnalyzer()

    # Get schedule snapshots for each week
    today = date.today()
    frames = []

    for week in range(num_weeks):
        start = today - timedelta(weeks=num_weeks - week - 1)
        end = start + timedelta(days=6)

        voxels = await get_voxel_grid(db, start, end)

        # Calculate stability metrics for each voxel
        for voxel in voxels:
            voxel["stabilityScore"] = tc.calculate_assignment_stability(
                voxel["assignmentId"],
                historical_weeks=week + 1,
            )
            voxel["churnCount"] = tc.count_changes(
                voxel["personId"],
                voxel["position"],
                historical_weeks=week + 1,
            )

        frames.append({
            "weekIndex": week,
            "dateRange": {"start": start.isoformat(), "end": end.isoformat()},
            "voxels": voxels,
        })

    # Calculate overall rigidity and periodicity
    rigidity = tc.calculate_schedule_rigidity(frames)
    periodicity = tc.detect_periodicity(frames)

    return {
        "frames": frames,
        "rigidity": rigidity,
        "periodicity": periodicity,
        "metadata": {
            "numWeeks": num_weeks,
            "frameRate": 1,  # 1 week per frame
        },
    }
```

### Frontend Time Crystal Animation Component

```typescript
// frontend/src/features/voxel-schedule/components/TimeCrystalAnimation.tsx

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSpring, animated } from '@react-spring/three';

interface TimeCrystalAnimationProps {
  numWeeks?: number;
  autoPlay?: boolean;
  frameDelay?: number;  // ms between frames
}

export function TimeCrystalAnimation({
  numWeeks = 4,
  autoPlay = false,
  frameDelay = 1000,
}: TimeCrystalAnimationProps) {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);

  const { data: animation } = useQuery({
    queryKey: ['time-crystal-animation', numWeeks],
    queryFn: () => api.get('/api/v1/resilience/exotic/time-crystal/animation', {
      params: { num_weeks: numWeeks },
    }).then(r => r.data),
  });

  // Auto-advance frames when playing
  useEffect(() => {
    if (!isPlaying || !animation?.frames) return;

    const timer = setInterval(() => {
      setCurrentFrame(prev => (prev + 1) % animation.frames.length);
    }, frameDelay);

    return () => clearInterval(timer);
  }, [isPlaying, animation, frameDelay]);

  const currentVoxels = useMemo(() => {
    return animation?.frames?.[currentFrame]?.voxels ?? [];
  }, [animation, currentFrame]);

  const currentDateRange = animation?.frames?.[currentFrame]?.dateRange;

  return (
    <group>
      {/* Voxels with stability-based opacity */}
      {currentVoxels.map((voxel: any) => (
        <StabilityAnimatedVoxel
          key={voxel.id}
          voxel={voxel}
          stabilityScore={voxel.stabilityScore}
          churnCount={voxel.churnCount}
        />
      ))}

      {/* Timeline indicator */}
      <Html position={[0, -3, 0]}>
        <TimeCrystalControls
          currentFrame={currentFrame}
          totalFrames={animation?.frames?.length ?? 0}
          isPlaying={isPlaying}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onSeek={setCurrentFrame}
          dateRange={currentDateRange}
          rigidity={animation?.rigidity}
          periodicity={animation?.periodicity}
        />
      </Html>
    </group>
  );
}

// Voxel that flickers based on instability
function StabilityAnimatedVoxel({ voxel, stabilityScore, churnCount }: any) {
  const meshRef = useRef<THREE.Mesh>(null);

  // Unstable voxels flicker
  useFrame(({ clock }) => {
    if (!meshRef.current || stabilityScore > 0.7) return;

    const material = meshRef.current.material as THREE.MeshStandardMaterial;

    // More flickering for less stable
    const flickerSpeed = (1 - stabilityScore) * 10;
    const flicker = Math.random() < (1 - stabilityScore) * 0.3
      ? 0.3
      : 1.0;

    material.opacity = flicker;
  });

  // Color based on stability
  const color = useMemo(() => {
    if (stabilityScore > 0.8) return '#22C55E';  // Green - very stable
    if (stabilityScore > 0.5) return '#EAB308';  // Yellow - somewhat stable
    return '#EF4444';  // Red - unstable
  }, [stabilityScore]);

  return (
    <mesh
      ref={meshRef}
      position={[voxel.position.x, voxel.position.y, voxel.position.z]}
    >
      <boxGeometry args={[0.9, 0.9, 0.9]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={stabilityScore}
      />
    </mesh>
  );
}

// Playback controls
function TimeCrystalControls({
  currentFrame,
  totalFrames,
  isPlaying,
  onPlay,
  onPause,
  onSeek,
  dateRange,
  rigidity,
  periodicity,
}: any) {
  return (
    <div className="bg-black/80 p-4 rounded-lg text-white text-sm min-w-[300px]">
      <h4 className="font-semibold mb-2">💎 Time Crystal View</h4>

      {/* Date range display */}
      {dateRange && (
        <div className="text-gray-400 text-xs mb-2">
          {dateRange.start} → {dateRange.end}
        </div>
      )}

      {/* Playback controls */}
      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={isPlaying ? onPause : onPlay}
          className="px-3 py-1 bg-blue-600 rounded hover:bg-blue-500"
        >
          {isPlaying ? '⏸️ Pause' : '▶️ Play'}
        </button>

        <input
          type="range"
          min={0}
          max={totalFrames - 1}
          value={currentFrame}
          onChange={e => onSeek(Number(e.target.value))}
          className="flex-1"
        />

        <span className="text-xs">
          Week {currentFrame + 1}/{totalFrames}
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-400">Rigidity:</span>
          <span className="ml-1">{(rigidity * 100).toFixed(1)}%</span>
        </div>
        <div>
          <span className="text-gray-400">Period:</span>
          <span className="ml-1">{periodicity?.period ?? '?'} weeks</span>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-2 pt-2 border-t border-gray-600 flex gap-4 text-xs">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded bg-green-500" />
          <span>Stable</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded bg-yellow-500" />
          <span>Moderate</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded bg-red-500 animate-pulse" />
          <span>Unstable</span>
        </div>
      </div>
    </div>
  );
}
```

---

## 6. Unified Ops Hub with 3D View

**Priority:** High | **Complexity:** Medium

Consolidate operational views into a single hub following the pattern from `FRONTEND_HUB_CONSOLIDATION_ROADMAP.md`.

### Ops Hub Page Structure

```typescript
// frontend/src/app/ops/page.tsx

'use client';

import { useState, Suspense, lazy } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar } from '@/components/RiskBar';
import { TabNavigation, Tab } from '@/components/ui/TabNavigation';

// Lazy-load heavy components
const DailyManifest = lazy(() => import('@/features/daily-manifest/DailyManifest'));
const HeatmapView = lazy(() => import('@/features/heatmap/HeatmapView'));
const ConflictsList = lazy(() => import('@/features/conflicts/ConflictsList'));
const ProxyCoverageMatrix = lazy(() => import('@/features/proxy-coverage/ProxyCoverageMatrix'));
const VoxelScheduleView3D = lazy(() => import('@/features/voxel-schedule/VoxelScheduleView3D'));

// Tab configuration following hub pattern
const OPS_HUB_TABS: Tab[] = [
  {
    id: 'manifest',
    label: 'Daily Manifest',
    icon: '📋',
    minTier: 0,
    description: 'Today\'s assignments and coverage',
  },
  {
    id: 'heatmap',
    label: 'Demand Heatmap',
    icon: '🔥',
    minTier: 0,
    description: '2D demand visualization',
  },
  {
    id: 'conflicts',
    label: 'Conflicts',
    icon: '⚠️',
    minTier: 0,
    description: 'Double-bookings and violations',
    badge: (data) => data?.conflictCount > 0 ? data.conflictCount : undefined,
  },
  {
    id: 'coverage',
    label: 'Proxy Coverage',
    icon: '🔄',
    minTier: 0,
    description: 'Who covers for whom',
  },
  {
    id: '3d-command',
    label: '3D Command',
    icon: '🎮',
    minTier: 0,
    description: '3D voxel visualization',
    isNew: true,  // Show "NEW" badge
  },
  {
    id: 'resolve',
    label: 'Resolve',
    icon: '🔧',
    minTier: 1,  // Requires higher tier
    description: 'Conflict resolution tools',
  },
];

export default function OpsHubPage() {
  const { user, tier } = useAuth();
  const [activeTab, setActiveTab] = useState('manifest');
  const [dateRange, setDateRange] = useState({
    start: new Date().toISOString().split('T')[0],
    end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  });

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-900">
        {/* Risk bar at top */}
        <RiskBar
          tier={tier}
          labels={{
            0: 'View Only',
            1: 'Operations',
            2: 'Full Control',
          }}
        />

        {/* Hub header */}
        <header className="border-b border-gray-700 px-6 py-4">
          <h1 className="text-2xl font-bold text-white">Operations Hub</h1>
          <p className="text-gray-400 text-sm">
            Daily operations, coverage monitoring, and conflict resolution
          </p>
        </header>

        {/* Tab navigation */}
        <TabNavigation
          tabs={OPS_HUB_TABS}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          userTier={tier}
        />

        {/* Tab content */}
        <main className="p-6">
          <Suspense fallback={<TabLoadingState />}>
            {activeTab === 'manifest' && (
              <DailyManifest date={dateRange.start} />
            )}

            {activeTab === 'heatmap' && (
              <HeatmapView
                startDate={dateRange.start}
                endDate={dateRange.end}
              />
            )}

            {activeTab === 'conflicts' && (
              <ConflictsList
                startDate={dateRange.start}
                endDate={dateRange.end}
              />
            )}

            {activeTab === 'coverage' && (
              <ProxyCoverageMatrix />
            )}

            {activeTab === '3d-command' && (
              <div className="h-[calc(100vh-250px)]">
                <VoxelScheduleView3D
                  startDate={dateRange.start}
                  endDate={dateRange.end}
                />
              </div>
            )}

            {activeTab === 'resolve' && tier >= 1 && (
              <ConflictResolutionPanel
                startDate={dateRange.start}
                endDate={dateRange.end}
              />
            )}
          </Suspense>
        </main>
      </div>
    </ProtectedRoute>
  );
}

function TabLoadingState() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
    </div>
  );
}
```

### Tab Navigation Component

```typescript
// frontend/src/components/ui/TabNavigation.tsx

export interface Tab {
  id: string;
  label: string;
  icon?: string;
  minTier?: number;
  description?: string;
  badge?: (data: any) => number | string | undefined;
  isNew?: boolean;
  disabled?: boolean;
}

interface TabNavigationProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  userTier: number;
  badgeData?: any;
}

export function TabNavigation({
  tabs,
  activeTab,
  onTabChange,
  userTier,
  badgeData,
}: TabNavigationProps) {
  return (
    <nav className="flex border-b border-gray-700 px-6 overflow-x-auto">
      {tabs.map(tab => {
        const isLocked = (tab.minTier ?? 0) > userTier;
        const isActive = tab.id === activeTab;
        const badge = tab.badge?.(badgeData);

        return (
          <button
            key={tab.id}
            onClick={() => !isLocked && onTabChange(tab.id)}
            disabled={isLocked || tab.disabled}
            className={`
              relative px-4 py-3 text-sm font-medium whitespace-nowrap
              transition-colors border-b-2 -mb-px
              ${isActive
                ? 'text-blue-400 border-blue-400'
                : 'text-gray-400 border-transparent hover:text-white hover:border-gray-600'
              }
              ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}
            `}
            title={tab.description}
          >
            <span className="flex items-center gap-2">
              {tab.icon && <span>{tab.icon}</span>}
              {tab.label}

              {/* Lock icon for tier-gated tabs */}
              {isLocked && <span className="text-xs">🔒</span>}

              {/* Badge */}
              {badge && (
                <span className="px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                  {badge}
                </span>
              )}

              {/* New indicator */}
              {tab.isNew && (
                <span className="px-1.5 py-0.5 text-xs bg-green-500 text-white rounded">
                  NEW
                </span>
              )}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
```

---

## 7. Phase Transition Early Warning Aura

**Priority:** Low | **Complexity:** Low

Add atmospheric effects to Command Center based on phase transition risk.

### Phase Transition Hook

```typescript
// frontend/src/features/voxel-schedule/hooks/usePhaseTransitionRisk.ts

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface PhaseTransitionRisk {
  level: 'normal' | 'elevated' | 'high' | 'critical' | 'imminent';
  score: number;  // 0-1
  indicators: {
    criticalSlowingDown: number;
    flickering: number;
    autocorrelation: number;
  };
  warnings: string[];
}

export function usePhaseTransitionRisk() {
  return useQuery<PhaseTransitionRisk>({
    queryKey: ['phase-transition-risk'],
    queryFn: () => api.get('/api/v1/resilience/exotic/phase-transition/risk').then(r => r.data),
    refetchInterval: 30_000,  // Check every 30s
  });
}
```

### Atmospheric Effects Component

```typescript
// frontend/src/features/voxel-schedule/components/AtmosphericEffects.tsx

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { usePhaseTransitionRisk } from '../hooks/usePhaseTransitionRisk';
import * as THREE from 'three';

export function AtmosphericEffects() {
  const { data: risk } = usePhaseTransitionRisk();
  const fogRef = useRef<THREE.Fog>(null);
  const lightRef = useRef<THREE.PointLight>(null);

  // Map risk level to visual parameters
  const atmosphere = useMemo(() => {
    const configs = {
      normal: {
        fogColor: '#111827',
        fogNear: 50,
        fogFar: 100,
        ambientColor: '#ffffff',
        ambientIntensity: 0.4,
        warningLight: false,
      },
      elevated: {
        fogColor: '#1f1f00',
        fogNear: 40,
        fogFar: 80,
        ambientColor: '#fffacd',
        ambientIntensity: 0.35,
        warningLight: false,
      },
      high: {
        fogColor: '#2d1f00',
        fogNear: 30,
        fogFar: 60,
        ambientColor: '#ffa500',
        ambientIntensity: 0.3,
        warningLight: true,
      },
      critical: {
        fogColor: '#2d0000',
        fogNear: 20,
        fogFar: 40,
        ambientColor: '#ff4444',
        ambientIntensity: 0.25,
        warningLight: true,
      },
      imminent: {
        fogColor: '#1a0000',
        fogNear: 10,
        fogFar: 30,
        ambientColor: '#ff0000',
        ambientIntensity: 0.2,
        warningLight: true,
      },
    };

    return configs[risk?.level ?? 'normal'];
  }, [risk?.level]);

  // Animate warning light for high+ risk
  useFrame(({ clock }) => {
    if (!lightRef.current || !atmosphere.warningLight) return;

    // Flickering effect
    const flicker = risk?.indicators?.flickering ?? 0;
    const base = Math.sin(clock.elapsedTime * 2) * 0.5 + 0.5;
    const noise = Math.random() * flicker * 0.3;

    lightRef.current.intensity = (base + noise) * 2;
  });

  return (
    <>
      {/* Fog effect */}
      <fog
        ref={fogRef}
        attach="fog"
        args={[atmosphere.fogColor, atmosphere.fogNear, atmosphere.fogFar]}
      />

      {/* Ambient light colored by risk */}
      <ambientLight
        color={atmosphere.ambientColor}
        intensity={atmosphere.ambientIntensity}
      />

      {/* Warning pulse light for elevated risk */}
      {atmosphere.warningLight && (
        <pointLight
          ref={lightRef}
          position={[0, 20, 0]}
          color="#ff4444"
          intensity={1}
          distance={100}
        />
      )}

      {/* Lightning flashes for imminent risk */}
      {risk?.level === 'imminent' && <LightningEffect />}
    </>
  );
}

// Random lightning flashes
function LightningEffect() {
  const lightRef = useRef<THREE.PointLight>(null);
  const nextFlash = useRef(0);

  useFrame(({ clock }) => {
    if (!lightRef.current) return;

    const time = clock.elapsedTime * 1000;

    if (time > nextFlash.current) {
      // Flash!
      lightRef.current.intensity = 10;

      // Schedule next flash (random 2-8 seconds)
      nextFlash.current = time + 2000 + Math.random() * 6000;

      // Fade out over 100ms
      setTimeout(() => {
        if (lightRef.current) lightRef.current.intensity = 0;
      }, 100);
    }
  });

  return (
    <pointLight
      ref={lightRef}
      position={[0, 50, 0]}
      color="#ffffff"
      intensity={0}
      distance={200}
    />
  );
}
```

### Risk Level Indicator

```typescript
// frontend/src/features/voxel-schedule/components/PhaseTransitionIndicator.tsx

interface PhaseTransitionIndicatorProps {
  risk: {
    level: string;
    score: number;
    warnings: string[];
  } | null;
}

export function PhaseTransitionIndicator({ risk }: PhaseTransitionIndicatorProps) {
  if (!risk) return null;

  const levelColors: Record<string, string> = {
    normal: 'bg-green-500',
    elevated: 'bg-yellow-500',
    high: 'bg-orange-500',
    critical: 'bg-red-500',
    imminent: 'bg-red-600 animate-pulse',
  };

  return (
    <div className="absolute top-4 left-4 bg-black/80 p-3 rounded-lg text-white text-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-3 h-3 rounded-full ${levelColors[risk.level]}`} />
        <span className="font-semibold capitalize">
          Phase Transition Risk: {risk.level}
        </span>
      </div>

      <div className="text-xs text-gray-400 mb-2">
        Score: {(risk.score * 100).toFixed(0)}%
      </div>

      {risk.warnings.length > 0 && (
        <div className="text-xs text-orange-400 space-y-1">
          {risk.warnings.map((w, i) => (
            <div key={i}>⚠️ {w}</div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 8. N-1/N-2 Contingency What-If Mode

**Priority:** High | **Complexity:** Medium

Interactive vulnerability exploration by simulating personnel removal.

### Contingency Analysis Hook

```typescript
// frontend/src/features/voxel-schedule/hooks/useContingencyAnalysis.ts

import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface ContingencyResult {
  removedPersonId: number;
  removedPersonName: string;
  affectedAssignments: Array<{
    id: string;
    blockDate: string;
    activityName: string;
    position: { x: number; y: number; z: number };
  }>;
  coverageGaps: Array<{
    position: { x: number; y: number; z: number };
    severity: 'critical' | 'warning';
    activityType: string;
  }>;
  suggestedSwaps: Array<{
    fromPersonId: number;
    fromPersonName: string;
    toPosition: { x: number; y: number; z: number };
    compatibility: number;
  }>;
  impactScore: number;  // 0-100, higher = more critical
}

export function useContingencyAnalysis() {
  return useMutation<ContingencyResult, Error, { personId: number; startDate: string; endDate: string }>({
    mutationFn: async ({ personId, startDate, endDate }) => {
      const response = await api.post('/api/v1/resilience/contingency/analyze', {
        person_id: personId,
        start_date: startDate,
        end_date: endDate,
        include_swap_suggestions: true,
      });
      return response.data;
    },
  });
}
```

### What-If Mode Component

```typescript
// frontend/src/features/voxel-schedule/components/ContingencyWhatIfMode.tsx

import { useState, useMemo } from 'react';
import { useContingencyAnalysis } from '../hooks/useContingencyAnalysis';

interface ContingencyWhatIfModeProps {
  voxels: VoxelData[];
  startDate: string;
  endDate: string;
  onHighlight: (voxelIds: string[]) => void;
}

export function ContingencyWhatIfMode({
  voxels,
  startDate,
  endDate,
  onHighlight,
}: ContingencyWhatIfModeProps) {
  const [selectedPersonId, setSelectedPersonId] = useState<number | null>(null);
  const [isWhatIfActive, setIsWhatIfActive] = useState(false);

  const contingencyAnalysis = useContingencyAnalysis();

  // Get unique persons from voxels
  const persons = useMemo(() => {
    const personMap = new Map<number, string>();
    voxels.forEach(v => {
      if (v.personId && !personMap.has(v.personId)) {
        personMap.set(v.personId, v.person);
      }
    });
    return Array.from(personMap.entries()).map(([id, name]) => ({ id, name }));
  }, [voxels]);

  const handlePersonSelect = async (personId: number) => {
    setSelectedPersonId(personId);

    const result = await contingencyAnalysis.mutateAsync({
      personId,
      startDate,
      endDate,
    });

    // Highlight affected voxels
    const affectedIds = result.affectedAssignments.map(a => a.id);
    onHighlight(affectedIds);
  };

  const handleReset = () => {
    setSelectedPersonId(null);
    setIsWhatIfActive(false);
    onHighlight([]);
    contingencyAnalysis.reset();
  };

  return (
    <div className="absolute top-4 right-4 bg-black/80 p-4 rounded-lg text-white text-sm w-80">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold">🔮 What-If Analysis</h4>
        <button
          onClick={() => setIsWhatIfActive(!isWhatIfActive)}
          className={`px-2 py-1 text-xs rounded ${
            isWhatIfActive ? 'bg-red-500' : 'bg-blue-500'
          }`}
        >
          {isWhatIfActive ? 'Exit' : 'Enter'} What-If Mode
        </button>
      </div>

      {isWhatIfActive && (
        <>
          <p className="text-xs text-gray-400 mb-3">
            Select a person to see what happens if they become unavailable.
          </p>

          {/* Person selector */}
          <select
            value={selectedPersonId ?? ''}
            onChange={e => handlePersonSelect(Number(e.target.value))}
            className="w-full mb-3 bg-gray-700 rounded px-2 py-1"
          >
            <option value="">Select person to remove...</option>
            {persons.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>

          {/* Analysis results */}
          {contingencyAnalysis.data && (
            <ContingencyResults result={contingencyAnalysis.data} />
          )}

          {contingencyAnalysis.isPending && (
            <div className="text-center text-gray-400">Analyzing...</div>
          )}

          {selectedPersonId && (
            <button
              onClick={handleReset}
              className="w-full mt-3 px-3 py-1 bg-gray-600 rounded hover:bg-gray-500"
            >
              Reset Analysis
            </button>
          )}
        </>
      )}
    </div>
  );
}

function ContingencyResults({ result }: { result: ContingencyResult }) {
  return (
    <div className="space-y-3">
      {/* Impact score */}
      <div className="flex items-center gap-2">
        <span className="text-gray-400">Impact:</span>
        <div className="flex-1 h-2 bg-gray-700 rounded">
          <div
            className={`h-full rounded ${
              result.impactScore > 70 ? 'bg-red-500' :
              result.impactScore > 40 ? 'bg-orange-500' :
              'bg-yellow-500'
            }`}
            style={{ width: `${result.impactScore}%` }}
          />
        </div>
        <span>{result.impactScore}%</span>
      </div>

      {/* Affected assignments */}
      <div>
        <span className="text-gray-400 text-xs">
          Affected: {result.affectedAssignments.length} assignments
        </span>
      </div>

      {/* Coverage gaps */}
      {result.coverageGaps.length > 0 && (
        <div className="p-2 bg-red-900/50 rounded">
          <span className="text-red-400 text-xs font-semibold">
            ⚠️ {result.coverageGaps.length} coverage gaps created
          </span>
          <ul className="mt-1 text-xs text-gray-300">
            {result.coverageGaps.slice(0, 3).map((gap, i) => (
              <li key={i}>• {gap.activityType} ({gap.severity})</li>
            ))}
            {result.coverageGaps.length > 3 && (
              <li>• +{result.coverageGaps.length - 3} more...</li>
            )}
          </ul>
        </div>
      )}

      {/* Suggested swaps */}
      {result.suggestedSwaps.length > 0 && (
        <div className="p-2 bg-green-900/50 rounded">
          <span className="text-green-400 text-xs font-semibold">
            ✓ Suggested replacements
          </span>
          <ul className="mt-1 text-xs text-gray-300">
            {result.suggestedSwaps.slice(0, 3).map((swap, i) => (
              <li key={i}>
                • {swap.fromPersonName} ({(swap.compatibility * 100).toFixed(0)}% match)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

### Voxel Highlight State

```typescript
// frontend/src/features/voxel-schedule/components/HighlightableVoxel.tsx

interface HighlightableVoxelProps {
  voxel: VoxelData;
  isHighlighted: boolean;
  highlightType: 'affected' | 'gap' | 'suggestion' | null;
  is3D: boolean;
}

export function HighlightableVoxel({
  voxel,
  isHighlighted,
  highlightType,
  is3D,
}: HighlightableVoxelProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  // Animate highlighted voxels
  useFrame(({ clock }) => {
    if (!meshRef.current || !isHighlighted) return;

    const material = meshRef.current.material as THREE.MeshStandardMaterial;

    if (highlightType === 'affected') {
      // Fade out effect (being removed)
      material.opacity = 0.3 + Math.sin(clock.elapsedTime * 3) * 0.2;
    } else if (highlightType === 'gap') {
      // Red pulse for gaps
      material.emissiveIntensity = Math.sin(clock.elapsedTime * 5) * 0.5 + 0.5;
    } else if (highlightType === 'suggestion') {
      // Green glow for suggestions
      material.emissiveIntensity = 0.3;
    }
  });

  const highlightColors = {
    affected: '#666666',  // Gray (fading)
    gap: '#EF4444',       // Red
    suggestion: '#22C55E', // Green
  };

  const color = isHighlighted && highlightType
    ? highlightColors[highlightType]
    : voxel.color;

  return (
    <mesh
      ref={meshRef}
      position={[voxel.position.x, voxel.position.y, voxel.position.z]}
    >
      <boxGeometry args={[0.9, 0.9, 0.9]} />
      <meshStandardMaterial
        color={color}
        transparent={isHighlighted}
        opacity={isHighlighted && highlightType === 'affected' ? 0.4 : 1}
        emissive={highlightType === 'gap' ? '#EF4444' : highlightType === 'suggestion' ? '#22C55E' : '#000000'}
        emissiveIntensity={0}
      />
    </mesh>
  );
}
```

---

## 9. Holographic Hub Integration

**Priority:** Low | **Complexity:** Medium

Integrate the existing HolographicManifold as a "Constraint View" mode in Command Center.

### View Mode Switcher

```typescript
// frontend/src/features/voxel-schedule/components/ViewModeSwitcher.tsx

type ViewMode = 'assignment' | 'constraint' | 'exotic';

interface ViewModeSwitcherProps {
  mode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
}

export function ViewModeSwitcher({ mode, onModeChange }: ViewModeSwitcherProps) {
  const modes: Array<{ id: ViewMode; label: string; icon: string; description: string }> = [
    {
      id: 'assignment',
      label: 'Assignments',
      icon: '📦',
      description: 'What is scheduled',
    },
    {
      id: 'constraint',
      label: 'Constraints',
      icon: '🌀',
      description: 'Why it\'s scheduled (ACGME, fairness)',
    },
    {
      id: 'exotic',
      label: 'Exotic',
      icon: '🔬',
      description: 'How stable is it (physics models)',
    },
  ];

  return (
    <div className="flex gap-1 bg-gray-800 p-1 rounded-lg">
      {modes.map(m => (
        <button
          key={m.id}
          onClick={() => onModeChange(m.id)}
          className={`
            px-3 py-2 rounded text-sm font-medium transition-colors
            ${mode === m.id
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }
          `}
          title={m.description}
        >
          <span className="mr-1">{m.icon}</span>
          {m.label}
        </button>
      ))}
    </div>
  );
}
```

### Integrated Command Center with Mode Switching

```typescript
// frontend/src/app/command-center/page.tsx (enhanced)

'use client';

import { useState, Suspense, lazy } from 'react';
import { ViewModeSwitcher, ViewMode } from '@/features/voxel-schedule/components/ViewModeSwitcher';

const VoxelScheduleView3D = lazy(() => import('@/features/voxel-schedule/VoxelScheduleView3D'));
const HolographicManifold = lazy(() => import('@/features/holographic-hub/HolographicManifold'));
const ExoticDashboard = lazy(() => import('@/features/exotic-dashboard/ExoticDashboard'));

export default function CommandCenterPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('assignment');
  const [dateRange, setDateRange] = useState({ /* ... */ });

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header with mode switcher */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-white">Command Center</h1>
          <p className="text-gray-400 text-sm">3D Schedule Visualization</p>
        </div>

        <ViewModeSwitcher mode={viewMode} onModeChange={setViewMode} />
      </header>

      {/* Main visualization area */}
      <main className="h-[calc(100vh-120px)]">
        <Suspense fallback={<LoadingState />}>
          {viewMode === 'assignment' && (
            <VoxelScheduleView3D
              startDate={dateRange.start}
              endDate={dateRange.end}
            />
          )}

          {viewMode === 'constraint' && (
            <HolographicManifold
              startDate={dateRange.start}
              endDate={dateRange.end}
              showLayers={['acgme', 'fairness', 'fatigue', 'coverage']}
            />
          )}

          {viewMode === 'exotic' && (
            <ExoticDashboard
              showCatastrophe
              showSpinGlass
              showTimeCrystal
              showPhaseTransition
            />
          )}
        </Suspense>
      </main>
    </div>
  );
}
```

### Exotic Dashboard Aggregate View

```typescript
// frontend/src/features/exotic-dashboard/ExoticDashboard.tsx

import { Suspense, lazy } from 'react';

const CatastropheSurface3D = lazy(() => import('../voxel-schedule/components/CatastropheSurface3D'));
const SpinGlassEnsembleView = lazy(() => import('../voxel-schedule/components/SpinGlassEnsembleView'));
const TimeCrystalAnimation = lazy(() => import('../voxel-schedule/components/TimeCrystalAnimation'));
const AtmosphericEffects = lazy(() => import('../voxel-schedule/components/AtmosphericEffects'));

interface ExoticDashboardProps {
  showCatastrophe?: boolean;
  showSpinGlass?: boolean;
  showTimeCrystal?: boolean;
  showPhaseTransition?: boolean;
}

export function ExoticDashboard({
  showCatastrophe = true,
  showSpinGlass = false,
  showTimeCrystal = false,
  showPhaseTransition = true,
}: ExoticDashboardProps) {
  return (
    <Canvas camera={{ position: [10, 10, 10], fov: 50 }}>
      {/* Base lighting and controls */}
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} />
      <OrbitControls />

      {/* Atmospheric effects based on phase transition */}
      {showPhaseTransition && (
        <Suspense fallback={null}>
          <AtmosphericEffects />
        </Suspense>
      )}

      {/* Catastrophe surface */}
      {showCatastrophe && (
        <Suspense fallback={null}>
          <CatastropheSurface3D showCurrentState />
        </Suspense>
      )}

      {/* Spin glass ensemble (positioned offset) */}
      {showSpinGlass && (
        <group position={[15, 0, 0]}>
          <Suspense fallback={null}>
            <SpinGlassEnsembleView
              startDate="2026-01-13"
              endDate="2026-01-20"
            />
          </Suspense>
        </group>
      )}

      {/* Time crystal animation (positioned offset) */}
      {showTimeCrystal && (
        <group position={[-15, 0, 0]}>
          <Suspense fallback={null}>
            <TimeCrystalAnimation numWeeks={4} />
          </Suspense>
        </group>
      )}

      {/* Grid and labels */}
      <gridHelper args={[50, 50, '#333', '#222']} />
    </Canvas>
  );
}
```

---

## 10. WebXR/Vision Pro Foundation

**Priority:** Future | **Complexity:** High

Foundation for VR/AR immersive schedule exploration.

### XR-Ready Canvas Setup

```typescript
// frontend/src/features/voxel-schedule/VoxelScheduleViewXR.tsx

import { Canvas } from '@react-three/fiber';
import { XR, Controllers, Hands, useXR } from '@react-three/xr';
import { useCallback, useState } from 'react';

interface VoxelScheduleViewXRProps {
  voxels: VoxelData[];
  onVoxelSelect: (voxel: VoxelData) => void;
}

export function VoxelScheduleViewXR({ voxels, onVoxelSelect }: VoxelScheduleViewXRProps) {
  return (
    <Canvas>
      <XR>
        <XRScene voxels={voxels} onVoxelSelect={onVoxelSelect} />
      </XR>
    </Canvas>
  );
}

function XRScene({ voxels, onVoxelSelect }: VoxelScheduleViewXRProps) {
  const { isPresenting, player } = useXR();

  // Position player in the middle of the schedule
  useEffect(() => {
    if (isPresenting && player) {
      player.position.set(5, 1.6, 5);  // Standing height in center
    }
  }, [isPresenting, player]);

  return (
    <>
      {/* XR Controllers and Hands */}
      <Controllers />
      <Hands />

      {/* Environment */}
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />

      {/* Floor grid */}
      <gridHelper args={[20, 20]} position={[5, 0, 5]} />

      {/* Voxels scaled for room-scale */}
      <group scale={0.5}>
        {voxels.map(voxel => (
          <XRInteractiveVoxel
            key={voxel.id}
            voxel={voxel}
            onSelect={() => onVoxelSelect(voxel)}
          />
        ))}
      </group>

      {/* Floating UI panels */}
      <XRFloatingUI />
    </>
  );
}

// Voxel with XR interaction (grab, point)
function XRInteractiveVoxel({ voxel, onSelect }: { voxel: VoxelData; onSelect: () => void }) {
  const [hovered, setHovered] = useState(false);
  const { controllers } = useXR();

  // Ray intersection handling
  const handlePointerOver = useCallback(() => setHovered(true), []);
  const handlePointerOut = useCallback(() => setHovered(false), []);
  const handleSelect = useCallback(() => onSelect(), [onSelect]);

  return (
    <mesh
      position={[voxel.position.x, voxel.position.y + 1, voxel.position.z]}  // Raise for standing view
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
      onClick={handleSelect}
    >
      <boxGeometry args={[0.9, 0.9, 0.9]} />
      <meshStandardMaterial
        color={hovered ? '#60A5FA' : voxel.color}
        emissive={hovered ? '#60A5FA' : '#000000'}
        emissiveIntensity={hovered ? 0.3 : 0}
      />
    </mesh>
  );
}

// Floating UI panel for XR
function XRFloatingUI() {
  const { isPresenting } = useXR();

  if (!isPresenting) return null;

  return (
    <group position={[0, 1.5, -1]}>
      <mesh>
        <planeGeometry args={[0.8, 0.4]} />
        <meshBasicMaterial color="#1f2937" transparent opacity={0.9} />
      </mesh>

      <Html transform occlude>
        <div className="w-64 p-4 text-white text-sm">
          <h3 className="font-bold mb-2">Schedule Overview</h3>
          <p>Point at voxels to see details</p>
          <p>Pinch to select</p>
        </div>
      </Html>
    </group>
  );
}
```

### Vision Pro Specific Interactions

```typescript
// frontend/src/features/voxel-schedule/hooks/useVisionProGestures.ts

import { useXR } from '@react-three/xr';
import { useCallback, useEffect, useRef } from 'react';

interface VisionProGestureHandlers {
  onLookAtVoxel?: (voxelId: string) => void;
  onPinchSelect?: (voxelId: string) => void;
  onTwoHandZoom?: (scale: number) => void;
}

export function useVisionProGestures(handlers: VisionProGestureHandlers) {
  const { controllers } = useXR();
  const lastGazeTarget = useRef<string | null>(null);

  // Eye tracking simulation via controller ray
  useEffect(() => {
    if (!controllers.length) return;

    const checkGaze = () => {
      // In real Vision Pro, use eye tracking API
      // For now, use controller ray direction
      const controller = controllers[0];
      if (!controller) return;

      // Raycast to find voxel
      // ... raycasting logic ...
    };

    const interval = setInterval(checkGaze, 100);
    return () => clearInterval(interval);
  }, [controllers, handlers.onLookAtVoxel]);

  // Pinch gesture detection
  const detectPinch = useCallback((hand: 'left' | 'right') => {
    // WebXR hand tracking pinch detection
    // Vision Pro: native pinch gesture

    // Placeholder - actual implementation depends on WebXR Hand API
    return false;
  }, []);

  return {
    detectPinch,
    lastGazeTarget: lastGazeTarget.current,
  };
}
```

### XR Entry Point Button

```typescript
// frontend/src/features/voxel-schedule/components/XREntryButton.tsx

import { useState, useCallback } from 'react';

interface XREntryButtonProps {
  onEnterXR: () => void;
}

export function XREntryButton({ onEnterXR }: XREntryButtonProps) {
  const [xrSupported, setXrSupported] = useState<boolean | null>(null);
  const [xrMode, setXrMode] = useState<'vr' | 'ar' | null>(null);

  // Check XR support on mount
  useEffect(() => {
    async function checkXR() {
      if (!navigator.xr) {
        setXrSupported(false);
        return;
      }

      const vrSupported = await navigator.xr.isSessionSupported('immersive-vr');
      const arSupported = await navigator.xr.isSessionSupported('immersive-ar');

      setXrSupported(vrSupported || arSupported);
      setXrMode(arSupported ? 'ar' : vrSupported ? 'vr' : null);
    }

    checkXR();
  }, []);

  if (xrSupported === false) {
    return (
      <button
        disabled
        className="px-4 py-2 bg-gray-700 text-gray-500 rounded cursor-not-allowed"
        title="WebXR not supported on this device"
      >
        🥽 XR Not Available
      </button>
    );
  }

  if (xrSupported === null) {
    return (
      <button disabled className="px-4 py-2 bg-gray-700 rounded animate-pulse">
        Checking XR...
      </button>
    );
  }

  return (
    <button
      onClick={onEnterXR}
      className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded flex items-center gap-2"
    >
      <span>🥽</span>
      <span>Enter {xrMode === 'ar' ? 'AR' : 'VR'}</span>
    </button>
  );
}
```

---

## Summary & Priority Matrix

| # | Feature | Priority | Complexity | Dependencies |
|---|---------|----------|------------|--------------|
| 1 | Real Data Integration | **Critical** | Medium | Backend API exists |
| 2 | Resilience Overlay | High | Low | Resilience endpoints |
| 3 | Catastrophe Surface | Medium | High | Exotic backend |
| 4 | Spin Glass Ensemble | Low | High | Exotic backend |
| 5 | Time Crystal Animation | Medium | Medium | Exotic backend |
| 6 | Ops Hub with 3D | **High** | Medium | Hub pattern exists |
| 7 | Phase Transition Aura | Low | Low | Exotic backend |
| 8 | N-1/N-2 What-If | **High** | Medium | Resilience endpoints |
| 9 | Holographic Integration | Low | Medium | HolographicManifold exists |
| 10 | WebXR/Vision Pro | Future | High | @react-three/xr |

### Recommended Implementation Order

1. **Real Data Integration** (unblock everything else)
2. **Ops Hub with 3D Tab** (user-facing value)
3. **Resilience Overlay** (enhance existing view)
4. **N-1/N-2 What-If Mode** (operational tool)
5. **Phase Transition Aura** (quick win, visual impact)
6. **Time Crystal Animation** (showcase feature)
7. **Catastrophe Surface** (advanced visualization)
8. **Holographic Integration** (mode switching)
9. **Spin Glass Ensemble** (research feature)
10. **WebXR Foundation** (Phase 5 roadmap)

---

*Document created 2026-01-13 based on PR #700 exploration*
