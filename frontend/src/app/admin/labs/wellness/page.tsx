'use client';

/**
 * Wellness & Fatigue Labs
 *
 * Intuitive monitoring for burnout risk, fatigue levels, and team wellbeing.
 * Target: Tier 0-1 users (high graduation readiness)
 *
 * Contains:
 * - Synapse Monitor: Neural interface visualization for fatigue tracking
 *
 * @route /admin/labs/wellness
 */

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ArrowLeft, Heart } from 'lucide-react';

const SynapseMonitor = dynamic(
  () =>
    import('@/features/synapse-monitor').then((mod) => mod.SynapseMonitor),
  {
    ssr: false,
    loading: () => (
      <div className="min-h-screen bg-[#020202] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
          <p className="mt-4 text-cyan-400 font-mono text-sm animate-pulse">
            Initializing Neural Interface...
          </p>
        </div>
      </div>
    ),
  }
);

export default function WellnessLabsPage() {
  return (
    <div className="min-h-screen bg-[#020202]">
      {/* Minimal Header - overlays the visualization */}
      <div className="fixed top-4 left-4 z-50 flex items-center gap-4">
        <Link
          href="/admin/labs"
          className="flex items-center gap-2 px-3 py-2 bg-black/50 backdrop-blur-sm border border-slate-700/50 rounded-lg text-slate-400 hover:text-cyan-400 hover:border-cyan-500/50 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">Labs</span>
        </Link>
        <div className="flex items-center gap-2 px-3 py-2 bg-black/50 backdrop-blur-sm border border-rose-500/30 rounded-lg">
          <Heart className="w-4 h-4 text-rose-500" />
          <span className="text-sm text-rose-400">Wellness</span>
        </div>
      </div>

      {/* Main Visualization */}
      <SynapseMonitor />
    </div>
  );
}
