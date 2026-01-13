/**
 * useSolverWebSocket - Subscribe to real-time solver updates
 *
 * This hook connects to the WebSocket server to receive streaming
 * solution updates from the CP-SAT solver. It handles:
 *
 * - Subscribing/unsubscribing to solver tasks
 * - Parsing full solutions and deltas
 * - Tracking solver progress metrics
 * - Managing current assignment state
 *
 * @module features/voxel-schedule/useSolverWebSocket
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

// ============================================================================
// Types
// ============================================================================

/**
 * Solver progress metrics.
 */
export interface SolverMetrics {
  /** Number of solutions found so far */
  solutionsFound: number;
  /** Current objective value (higher = more assignments) */
  currentObjective: number;
  /** Gap from proven optimal (0% = optimal) */
  optimalityGapPct: number;
  /** Estimated progress percentage */
  progressPct: number;
  /** Seconds elapsed since solve started */
  elapsedSeconds: number;
  /** Whether current solution is proven optimal */
  isOptimal: boolean;
}

/**
 * Assignment from solver.
 */
export interface Assignment {
  personId: string;
  blockId: string;
  templateId: string;
  rIdx?: number;
  bIdx?: number;
  tIdx?: number;
}

/**
 * Delta between consecutive solutions.
 */
export interface SolutionDelta {
  added: Assignment[];
  removed: Assignment[];
  moved: Array<{
    personId: string;
    blockId: string;
    oldTemplateId: string;
    newTemplateId: string;
  }>;
}

/**
 * WebSocket event for solver solution.
 */
export interface SolverSolutionEvent {
  eventType: 'solver_solution';
  taskId: string;
  solutionNum: number;
  solutionType: 'full' | 'delta';
  assignments?: Assignment[];
  delta?: SolutionDelta;
  assignmentCount: number;
  objectiveValue: number;
  optimalityGapPct: number;
  isOptimal: boolean;
  elapsedSeconds: number;
}

/**
 * WebSocket event for solver completion.
 */
export interface SolverCompleteEvent {
  eventType: 'solver_complete';
  taskId: string;
  status: 'optimal' | 'feasible' | 'timeout' | 'infeasible' | 'error';
  totalSolutions: number;
  finalAssignmentCount: number;
  totalElapsedSeconds: number;
  message?: string;
}

/**
 * Union type of solver events.
 */
export type SolverEvent = SolverSolutionEvent | SolverCompleteEvent;

/**
 * Solver status states.
 */
export type SolverStatus = 'idle' | 'solving' | 'complete' | 'error';

/**
 * Completion status from solver.
 */
export type CompletionStatus =
  | 'optimal'
  | 'feasible'
  | 'timeout'
  | 'infeasible'
  | 'error';

/**
 * Options for the solver WebSocket hook.
 */
export interface UseSolverWebSocketOptions {
  /** Task ID to subscribe to (null = not subscribed) */
  taskId: string | null;
  /** Callback when a new solution arrives */
  onSolution?: (solution: SolverSolutionEvent) => void;
  /** Callback when a delta arrives (useful for animations) */
  onDelta?: (delta: SolutionDelta, solutionNum: number) => void;
  /** Callback when solver completes */
  onComplete?: (event: SolverCompleteEvent) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

/**
 * Return type of the hook.
 */
export interface UseSolverWebSocketReturn {
  /** Whether WebSocket is connected */
  isConnected: boolean;
  /** Whether subscribed to solver updates */
  isSubscribed: boolean;
  /** Current solver status */
  status: SolverStatus;
  /** Completion status (only set when status === 'complete') */
  completionStatus: CompletionStatus | null;
  /** Current metrics */
  metrics: SolverMetrics | null;
  /** Current assignments (full state) */
  currentAssignments: Assignment[];
  /** Latest delta received (for animation triggers) */
  latestDelta: SolutionDelta | null;
  /** Number of the latest solution */
  latestSolutionNum: number;
  /** Manually subscribe to a task */
  subscribe: (taskId: string) => void;
  /** Manually unsubscribe */
  unsubscribe: () => void;
  /** Reset state */
  reset: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for subscribing to real-time solver updates via WebSocket.
 *
 * @example
 * ```tsx
 * const {
 *   status,
 *   metrics,
 *   currentAssignments,
 *   latestDelta,
 * } = useSolverWebSocket({
 *   taskId: scheduleRunId,
 *   onSolution: (sol) => console.log('New solution:', sol.solutionNum),
 *   onDelta: (delta, num) => {
 *     // Trigger animation
 *     applyDelta(delta, personIndex, blockIndex, templateToLayer);
 *   },
 *   onComplete: (event) => {
 *     toast.success(`Schedule complete: ${event.status}`);
 *   },
 * });
 * ```
 */
export function useSolverWebSocket(
  options: UseSolverWebSocketOptions
): UseSolverWebSocketReturn {
  const { taskId, onSolution, onDelta, onComplete, onError } = options;

  // State
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [status, setStatus] = useState<SolverStatus>('idle');
  const [completionStatus, setCompletionStatus] =
    useState<CompletionStatus | null>(null);
  const [metrics, setMetrics] = useState<SolverMetrics | null>(null);
  const [currentAssignments, setCurrentAssignments] = useState<Assignment[]>([]);
  const [latestDelta, setLatestDelta] = useState<SolutionDelta | null>(null);
  const [latestSolutionNum, setLatestSolutionNum] = useState(0);

  // Ref to track assignments without triggering re-renders during updates
  const assignmentsRef = useRef<Assignment[]>([]);

  // Ref for current taskId to handle subscription changes
  const currentTaskIdRef = useRef<string | null>(null);

  /**
   * Apply delta to current assignments.
   */
  const applyDeltaToAssignments = useCallback(
    (delta: SolutionDelta): Assignment[] => {
      const current = assignmentsRef.current;

      // Create lookup map for efficient updates
      const assignmentMap = new Map<string, Assignment>();
      current.forEach((a) => {
        const key = `${a.personId}-${a.blockId}`;
        assignmentMap.set(key, a);
      });

      // Remove deleted assignments
      delta.removed.forEach((a) => {
        const key = `${a.personId}-${a.blockId}`;
        assignmentMap.delete(key);
      });

      // Update moved assignments
      delta.moved.forEach((a) => {
        const key = `${a.personId}-${a.blockId}`;
        const existing = assignmentMap.get(key);
        if (existing) {
          assignmentMap.set(key, {
            ...existing,
            templateId: a.newTemplateId,
            // Clear tIdx so renderer uses new templateId for layer positioning
            tIdx: undefined,
          });
        }
      });

      // Add new assignments
      delta.added.forEach((a) => {
        const key = `${a.personId}-${a.blockId}`;
        assignmentMap.set(key, a);
      });

      return Array.from(assignmentMap.values());
    },
    []
  );

  /**
   * Handle incoming solver solution event.
   */
  const handleSolutionEvent = useCallback(
    (event: SolverSolutionEvent) => {
      // Update metrics
      const newMetrics: SolverMetrics = {
        solutionsFound: event.solutionNum,
        currentObjective: event.objectiveValue,
        optimalityGapPct: event.optimalityGapPct,
        progressPct: Math.min(100 - event.optimalityGapPct, 99),
        elapsedSeconds: event.elapsedSeconds,
        isOptimal: event.isOptimal,
      };
      setMetrics(newMetrics);
      setLatestSolutionNum(event.solutionNum);
      setStatus('solving');

      // Update assignments
      if (event.solutionType === 'full' && event.assignments) {
        // Full solution: replace all assignments
        assignmentsRef.current = event.assignments;
        setCurrentAssignments(event.assignments);
        setLatestDelta(null);
      } else if (event.solutionType === 'delta' && event.delta) {
        // Delta solution: apply changes
        const newAssignments = applyDeltaToAssignments(event.delta);
        assignmentsRef.current = newAssignments;
        setCurrentAssignments(newAssignments);
        setLatestDelta(event.delta);

        // Trigger delta callback for animations
        onDelta?.(event.delta, event.solutionNum);
      }

      // Trigger solution callback
      onSolution?.(event);
    },
    [applyDeltaToAssignments, onSolution, onDelta]
  );

  /**
   * Handle solver complete event.
   */
  const handleCompleteEvent = useCallback(
    (event: SolverCompleteEvent) => {
      setStatus('complete');
      setCompletionStatus(event.status);

      // Update final metrics
      if (metrics) {
        setMetrics({
          ...metrics,
          progressPct: 100,
          isOptimal: event.status === 'optimal',
        });
      }

      onComplete?.(event);
    },
    [metrics, onComplete]
  );

  /**
   * Handle WebSocket messages.
   */
  const handleMessage = useCallback(
    (event: unknown) => {
      // Type guard for solver events
      const data = event as Record<string, unknown>;
      if (!data || typeof data !== 'object') return;

      const eventType = data.eventType as string;

      // Only process if this is for our task
      const eventTaskId = data.taskId as string;
      if (eventTaskId !== currentTaskIdRef.current) return;

      if (eventType === 'solver_solution') {
        handleSolutionEvent(data as unknown as SolverSolutionEvent);
      } else if (eventType === 'solver_complete') {
        handleCompleteEvent(data as unknown as SolverCompleteEvent);
      }
    },
    [handleSolutionEvent, handleCompleteEvent]
  );

  /**
   * Handle WebSocket errors.
   */
  const handleError = useCallback(
    (error: Event) => {
      setStatus('error');
      onError?.(new Error('WebSocket connection error'));
    },
    [onError]
  );

  // WebSocket connection
  const { isConnected, send } = useWebSocket({
    onMessage: handleMessage,
    onError: handleError,
  });

  /**
   * Subscribe to solver updates.
   */
  const subscribe = useCallback(
    (newTaskId: string) => {
      if (!isConnected) return;

      currentTaskIdRef.current = newTaskId;
      // Note: The actual subscription message format depends on backend implementation
      // This assumes a subscribe_solver action is supported
      send({
        action: 'subscribe_solver' as 'ping', // Type workaround
        taskId: newTaskId,
      } as unknown as Parameters<typeof send>[0]);
      setIsSubscribed(true);
      setStatus('solving');
    },
    [isConnected, send]
  );

  /**
   * Unsubscribe from solver updates.
   */
  const unsubscribe = useCallback(() => {
    if (!isConnected || !currentTaskIdRef.current) return;

    send({
      action: 'unsubscribe_solver' as 'ping', // Type workaround
      taskId: currentTaskIdRef.current,
    } as unknown as Parameters<typeof send>[0]);
    setIsSubscribed(false);
    currentTaskIdRef.current = null;
  }, [isConnected, send]);

  /**
   * Reset all state.
   */
  const reset = useCallback(() => {
    setMetrics(null);
    setCurrentAssignments([]);
    assignmentsRef.current = [];
    setLatestDelta(null);
    setLatestSolutionNum(0);
    setStatus('idle');
    setCompletionStatus(null);
    setIsSubscribed(false);
    currentTaskIdRef.current = null;
  }, []);

  // Auto-subscribe when taskId changes
  useEffect(() => {
    if (isConnected && taskId && taskId !== currentTaskIdRef.current) {
      // Unsubscribe from previous task
      if (currentTaskIdRef.current) {
        unsubscribe();
      }

      // Reset state for new task
      reset();

      // Subscribe to new task
      subscribe(taskId);
    } else if (!taskId && currentTaskIdRef.current) {
      // taskId cleared, unsubscribe
      unsubscribe();
      reset();
    }
  }, [isConnected, taskId, subscribe, unsubscribe, reset]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (currentTaskIdRef.current) {
        unsubscribe();
      }
    };
  }, [unsubscribe]);

  return {
    isConnected,
    isSubscribed,
    status,
    completionStatus,
    metrics,
    currentAssignments,
    latestDelta,
    latestSolutionNum,
    subscribe,
    unsubscribe,
    reset,
  };
}

/**
 * Hook for polling solver progress (fallback when WebSocket unavailable).
 *
 * Uses React Query to poll the REST API for solver progress.
 */
export function useSolverProgressPolling(
  taskId: string | null,
  options: {
    enabled?: boolean;
    pollInterval?: number;
  } = {}
) {
  const { enabled = true, pollInterval = 2000 } = options;

  const [metrics, setMetrics] = useState<SolverMetrics | null>(null);
  const [status, setStatus] = useState<SolverStatus>('idle');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!enabled || !taskId) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const poll = async () => {
      try {
        const response = await fetch(`/api/solver/progress/${taskId}`);
        if (!response.ok) return;

        const data = await response.json();

        if (data.status === 'running') {
          setStatus('solving');
          setMetrics({
            solutionsFound: data.solutionsFound || 0,
            currentObjective: data.currentObjective || 0,
            optimalityGapPct: data.optimalityGapPct || 100,
            progressPct: data.progressPct || 0,
            elapsedSeconds: data.elapsedSeconds || 0,
            isOptimal: false,
          });
        } else if (data.status === 'completed') {
          setStatus('complete');
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch (error) {
        // Polling error - continue trying
      }
    };

    // Initial poll
    poll();

    // Set up interval
    intervalRef.current = setInterval(poll, pollInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, taskId, pollInterval]);

  return { metrics, status };
}

export default useSolverWebSocket;
