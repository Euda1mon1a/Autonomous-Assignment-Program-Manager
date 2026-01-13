'use client';

/**
 * Command Center - 3D Voxel Schedule Visualization
 *
 * Standalone route for 3D schedule visualization with tier-based CRUD.
 * Uses Three.js (React Three Fiber) - lazy loaded for performance.
 *
 * Attribution: Original prototype developed with Gemini Pro 3 in Google AI Studio,
 * with assistance from Claude Code Web.
 */

import dynamic from 'next/dynamic';
import { Suspense, useState, useMemo, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { Box, Loader2, AlertTriangle } from 'lucide-react';

// Lazy load the 3D component - Three.js is ~500KB
const VoxelScheduleView3D = dynamic(
  () => import('@/features/voxel-schedule/VoxelScheduleView3D'),
  {
    loading: () => <LoadingFallback />,
    ssr: false, // Three.js requires browser APIs
  }
);

function LoadingFallback() {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)] gap-4">
      <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
      <p className="text-slate-400">Loading 3D visualization...</p>
      <p className="text-slate-500 text-sm">First load may take a moment</p>
    </div>
  );
}

function WebGLError() {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)] gap-4">
      <AlertTriangle className="w-12 h-12 text-amber-500" />
      <p className="text-slate-300 text-lg font-medium">WebGL Not Supported</p>
      <p className="text-slate-400 text-sm max-w-md text-center">
        Your browser or device doesn&apos;t support WebGL, which is required for 3D visualization.
        Try using a modern browser like Chrome, Firefox, or Edge.
      </p>
    </div>
  );
}

export default function CommandCenterPage() {
  const { user } = useAuth();
  const [webglSupported, setWebglSupported] = useState<boolean | null>(null);

  // Calculate user tier from roles (hook must be called at top level)
  const userTier: RiskTier = useRiskTierFromRoles(user?.roles ?? []);

  // Risk bar label based on tier
  const riskBarConfig = useMemo(() => {
    switch (userTier) {
      case 2:
        return {
          label: 'Full Control',
          tooltip: 'You can create, edit, and delete assignments directly.',
        };
      case 1:
        return {
          label: 'Operations',
          tooltip: 'You can view all data and manage swaps.',
        };
      default:
        return {
          label: 'View Mode',
          tooltip: 'You can view schedules and request swaps for yourself.',
        };
    }
  }, [userTier]);

  // Check WebGL support on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        setWebglSupported(!!gl);
      } catch {
        setWebglSupported(false);
      }
    }
  }, []);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-900">
        {/* Risk Bar */}
        <RiskBar
          tier={userTier}
          label={riskBarConfig.label}
          tooltip={riskBarConfig.tooltip}
        />

        {/* Header */}
        <div className="border-b border-slate-700 bg-slate-800/50">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center gap-3">
              <Box className="w-6 h-6 text-blue-400" />
              <div>
                <h1 className="text-xl font-bold text-white">
                  Command Center
                </h1>
                <p className="text-sm text-slate-400">
                  3D Schedule Visualization
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="h-[calc(100vh-140px)]">
          {webglSupported === null ? (
            <LoadingFallback />
          ) : webglSupported === false ? (
            <WebGLError />
          ) : (
            <Suspense fallback={<LoadingFallback />}>
              <VoxelScheduleView3D userTier={userTier} />
            </Suspense>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
