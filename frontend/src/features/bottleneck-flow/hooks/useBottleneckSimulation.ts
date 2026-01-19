/**
 * Bottleneck Simulation State Hook
 *
 * Manages the simulation state for the bottleneck cascade visualization.
 * Handles faculty toggling, fix suggestions, and reset functionality.
 */

import { useState, useCallback } from 'react';
import type { SimulationState, BottleneckMetrics } from '../types';

/**
 * Initial simulation state with all faculty enabled.
 */
const INITIAL_SIM_STATE: SimulationState = {
  showSuggestedFix: false,
  disabledFacultyIds: new Set(),
};

/**
 * Initial metrics showing 100% coverage.
 */
const INITIAL_METRICS: BottleneckMetrics = {
  coverage: 100,
  orphaned: 0,
  rerouted: 0,
  atRisk: 0,
};

/**
 * Hook for managing bottleneck simulation state.
 *
 * @returns Simulation state, metrics, and handlers
 *
 * @example
 * ```tsx
 * const {
 *   simState,
 *   metrics,
 *   handleToggleFaculty,
 *   handleToggleFix,
 *   handleReset,
 *   setMetrics,
 * } = useBottleneckSimulation();
 * ```
 */
export function useBottleneckSimulation() {
  const [simState, setSimState] = useState<SimulationState>(INITIAL_SIM_STATE);
  const [metrics, setMetrics] = useState<BottleneckMetrics>(INITIAL_METRICS);

  /**
   * Toggle a faculty member's disabled state.
   * Disabled faculty cannot supervise trainees, triggering cascade effects.
   */
  const handleToggleFaculty = useCallback((id: string) => {
    setSimState((prev) => {
      const newSet = new Set(prev.disabledFacultyIds);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return { ...prev, disabledFacultyIds: newSet };
    });
  }, []);

  /**
   * Toggle the "show suggested fix" mode.
   * When enabled, at-risk trainees are rerouted to backup faculty.
   */
  const handleToggleFix = useCallback(() => {
    setSimState((prev) => ({
      ...prev,
      showSuggestedFix: !prev.showSuggestedFix,
    }));
  }, []);

  /**
   * Reset simulation to initial state.
   * Re-enables all faculty and disables suggested fix.
   */
  const handleReset = useCallback(() => {
    setSimState(INITIAL_SIM_STATE);
    setMetrics(INITIAL_METRICS);
  }, []);

  return {
    simState,
    metrics,
    handleToggleFaculty,
    handleToggleFix,
    handleReset,
    setMetrics,
  };
}
