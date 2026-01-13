'use client';

/**
 * Solver Visualization Page
 *
 * Real-time visualization of CP-SAT solver progress.
 * Shows voxels updating as the solver finds solutions.
 *
 * Usage: /solver-viz?taskId=<schedule-run-id>
 */

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { SolverVisualization } from '@/features/voxel-schedule';
import { ProtectedRoute } from '@/components/ProtectedRoute';

function SolverVizContent() {
  const params = useSearchParams();
  const taskId = params.get('taskId');

  if (!taskId) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-center text-white">
          <h1 className="text-2xl font-bold mb-4">Solver Visualization</h1>
          <p className="text-slate-400">
            No task ID provided. Start a schedule generation to watch it solve.
          </p>
          <p className="text-slate-500 text-sm mt-2">
            Usage: /solver-viz?taskId=&lt;schedule-run-id&gt;
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-slate-900">
      <SolverVisualization taskId={taskId} />
    </div>
  );
}

export default function SolverVizPage() {
  return (
    <ProtectedRoute>
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-screen bg-slate-900">
            <div className="text-white">Loading solver visualization...</div>
          </div>
        }
      >
        <SolverVizContent />
      </Suspense>
    </ProtectedRoute>
  );
}
