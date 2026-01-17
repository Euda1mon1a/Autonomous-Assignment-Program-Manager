/**
 * useSolutionTransitions - Animate between solver solutions
 *
 * This hook manages smooth voxel transitions when CP-SAT discovers
 * improved solutions. It handles:
 *
 * - Appear animations: New voxels drop in from above
 * - Disappear animations: Removed voxels fade out downward
 * - Move animations: Voxels slide to new activity layers
 *
 * The animation uses spring physics for natural motion with
 * configurable stagger delays between voxels.
 *
 * @module features/voxel-schedule/useSolutionTransitions
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import * as THREE from 'three';

// ============================================================================
// Types
// ============================================================================

/**
 * Assignment from the solver.
 */
export interface Assignment {
  personId: string;
  blockId: string;
  templateId: string;
}

/**
 * Delta between two consecutive solutions.
 */
export interface SolutionDelta {
  /** New assignments not in previous solution */
  added: Assignment[];
  /** Assignments removed from previous solution */
  removed: Assignment[];
  /** Assignments with same person/block but different template */
  moved: Array<{
    personId: string;
    blockId: string;
    oldTemplateId: string;
    newTemplateId: string;
  }>;
}

/**
 * Position in 3D space.
 */
export interface VoxelPosition {
  x: number;
  y: number;
  z: number;
}

/**
 * State of a transitioning voxel.
 */
export interface TransitionState {
  /** Unique voxel identifier */
  voxelId: string;
  /** Type of transition animation */
  type: 'appear' | 'disappear' | 'move';
  /** Starting position */
  from: THREE.Vector3;
  /** Target position */
  to: THREE.Vector3;
  /** Animation progress (0-1) */
  progress: number;
}

/**
 * Options for the transition hook.
 */
export interface UseSolutionTransitionsOptions {
  /** Duration of each voxel animation in milliseconds */
  animationDuration?: number;
  /** Delay between starting each voxel's animation */
  staggerDelay?: number;
  /** Grid spacing multiplier */
  spacing?: number;
  /** Easing function (default: ease-out cubic) */
  easingFn?: (t: number) => number;
}

/**
 * Return type of the hook.
 */
export interface UseSolutionTransitionsReturn {
  /** Map of currently transitioning voxels */
  transitions: Map<string, TransitionState>;
  /** Whether any animation is in progress */
  isAnimating: boolean;
  /** Apply a solution delta with animations */
  applyDelta: (
    delta: SolutionDelta,
    personIndex: Map<string, number>,
    blockIndex: Map<string, number>,
    templateToLayer: Map<string, number>
  ) => void;
  /** Cancel all in-progress animations */
  cancelAnimations: () => void;
  /** Get completed voxels that should be rendered statically */
  completedVoxels: string[];
}

// ============================================================================
// Easing Functions
// ============================================================================

/**
 * Ease-out cubic: fast start, slow end.
 */
export const easeOutCubic = (t: number): number => {
  return 1 - Math.pow(1 - t, 3);
};

/**
 * Ease-in-out cubic: slow start and end.
 */
export const easeInOutCubic = (t: number): number => {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
};

/**
 * Spring-like bounce effect.
 */
export const easeOutBack = (t: number): number => {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for animating transitions between solver solutions.
 *
 * @example
 * ```tsx
 * const { transitions, isAnimating, applyDelta } = useSolutionTransitions();
 *
 * // When new solution arrives from WebSocket:
 * useEffect(() => {
 *   if (solutionDelta) {
 *     applyDelta(solutionDelta, personIndex, blockIndex, templateToLayer);
 *   }
 * }, [solutionDelta]);
 *
 * // Pass transitions to renderer:
 * <InstancedVoxelRenderer voxels={voxels} transitions={transitions} />
 * ```
 */
export function useSolutionTransitions(
  options: UseSolutionTransitionsOptions = {}
): UseSolutionTransitionsReturn {
  const {
    animationDuration = 500,
    staggerDelay = 20,
    spacing = 1.1,
    easingFn = easeOutCubic,
  } = options;

  // State
  const [transitions, setTransitions] = useState<Map<string, TransitionState>>(
    new Map()
  );
  const [isAnimating, setIsAnimating] = useState(false);
  const [completedVoxels, setCompletedVoxels] = useState<string[]>([]);

  // Refs for animation loop
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

  /**
   * Convert assignment to 3D position.
   */
  const assignmentToPosition = useCallback(
    (
      assignment: { personId: string; blockId: string; templateId?: string },
      personIndex: Map<string, number>,
      blockIndex: Map<string, number>,
      templateToLayer: Map<string, number>,
      templateId?: string
    ): THREE.Vector3 => {
      const x = (blockIndex.get(assignment.blockId) ?? 0) * spacing;
      const y = (personIndex.get(assignment.personId) ?? 0) * spacing;
      const z =
        (templateToLayer.get(templateId || assignment.templateId || '') ?? 0) *
        spacing;
      return new THREE.Vector3(x, y, z);
    },
    [spacing]
  );

  /**
   * Cancel all in-progress animations.
   */
  const cancelAnimations = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    setTransitions(new Map());
    setIsAnimating(false);
    setCompletedVoxels([]);
  }, []);

  /**
   * Apply a solution delta with animated transitions.
   */
  const applyDelta = useCallback(
    (
      delta: SolutionDelta,
      personIndex: Map<string, number>,
      blockIndex: Map<string, number>,
      templateToLayer: Map<string, number>
    ) => {
      // Cancel any existing animations
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }

      const newTransitions = new Map<string, TransitionState>();
      const _newCompleted: string[] = [];

      // Process added voxels (drop in from above)
      delta.added.forEach((assignment) => {
        const voxelId = `${assignment.personId}-${assignment.blockId}`;
        const to = assignmentToPosition(
          assignment,
          personIndex,
          blockIndex,
          templateToLayer
        );
        const from = new THREE.Vector3(to.x, to.y + 3 * spacing, to.z);

        newTransitions.set(voxelId, {
          voxelId,
          type: 'appear',
          from,
          to,
          progress: 0,
        });
      });

      // Process removed voxels (fall downward and fade)
      delta.removed.forEach((assignment) => {
        const voxelId = `${assignment.personId}-${assignment.blockId}`;
        const from = assignmentToPosition(
          assignment,
          personIndex,
          blockIndex,
          templateToLayer
        );
        const to = new THREE.Vector3(from.x, from.y - 3 * spacing, from.z);

        newTransitions.set(voxelId, {
          voxelId,
          type: 'disappear',
          from,
          to,
          progress: 0,
        });
      });

      // Process moved voxels (slide to new layer)
      delta.moved.forEach((assignment) => {
        const voxelId = `${assignment.personId}-${assignment.blockId}`;
        const from = assignmentToPosition(
          { personId: assignment.personId, blockId: assignment.blockId },
          personIndex,
          blockIndex,
          templateToLayer,
          assignment.oldTemplateId
        );
        const to = assignmentToPosition(
          { personId: assignment.personId, blockId: assignment.blockId },
          personIndex,
          blockIndex,
          templateToLayer,
          assignment.newTemplateId
        );

        newTransitions.set(voxelId, {
          voxelId,
          type: 'move',
          from,
          to,
          progress: 0,
        });
      });

      // Early exit if no transitions
      if (newTransitions.size === 0) {
        return;
      }

      setTransitions(newTransitions);
      setIsAnimating(true);
      setCompletedVoxels([]);

      // Start animation loop
      startTimeRef.current = performance.now();
      const totalDuration = animationDuration + newTransitions.size * staggerDelay;

      const animate = (currentTime: number) => {
        const elapsed = currentTime - startTimeRef.current;

        setTransitions((prev) => {
          const updated = new Map(prev);
          const _allComplete = true;
          const nowCompleted: string[] = [];

          let index = 0;
          updated.forEach((transition, id) => {
            const staggeredStart = index * staggerDelay;
            const localElapsed = elapsed - staggeredStart;

            if (localElapsed < 0) {
              // Not started yet
              allComplete = false;
            } else {
              const rawProgress = Math.min(localElapsed / animationDuration, 1);
              const easedProgress = easingFn(rawProgress);

              updated.set(id, { ...transition, progress: easedProgress });

              if (rawProgress < 1) {
                allComplete = false;
              } else {
                // This transition is complete
                nowCompleted.push(id);
              }
            }
            index++;
          });

          // Track newly completed voxels
          if (nowCompleted.length > 0) {
            setCompletedVoxels((prev) => [...prev, ...nowCompleted]);
          }

          return updated;
        });

        if (elapsed < totalDuration) {
          animationRef.current = requestAnimationFrame(animate);
        } else {
          // Animation complete
          setIsAnimating(false);

          // Clear disappearing voxels, keep others at final position
          setTransitions((prev) => {
            const final = new Map<string, TransitionState>();
            prev.forEach((t, id) => {
              if (t.type !== 'disappear') {
                // Keep non-disappearing voxels at final position
                final.set(id, { ...t, progress: 1 });
              }
            });
            return final;
          });

          animationRef.current = null;
        }
      };

      animationRef.current = requestAnimationFrame(animate);
    },
    [animationDuration, staggerDelay, spacing, assignmentToPosition, easingFn]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return {
    transitions,
    isAnimating,
    applyDelta,
    cancelAnimations,
    completedVoxels,
  };
}

export default useSolutionTransitions;
