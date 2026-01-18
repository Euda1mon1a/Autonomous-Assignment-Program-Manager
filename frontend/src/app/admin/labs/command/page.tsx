'use client';

/**
 * Command Center Labs
 *
 * Unified command dashboard for scheduling system monitoring.
 * Target: Tier 1 users (high graduation readiness)
 *
 * Contains:
 * - Sovereign Portal: 4-panel unified view (Spatial, Fairness, Solver, Fragility)
 *
 * @route /admin/labs/command
 */

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ArrowLeft, Command } from 'lucide-react';

// Dynamic import for Sovereign Portal
const SovereignPortal = dynamic(
  () => import('@/features/sovereign-portal').then((mod) => mod.SovereignPortal),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" />
          <p className="mt-4 text-sm uppercase tracking-widest text-purple-400">
            Initializing Command Portal...
          </p>
        </div>
      </div>
    ),
  }
);

export default function CommandLabsPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-slate-900/80 border-b border-slate-700/50 backdrop-blur-sm z-40">
        <div className="px-4 py-3">
          <div className="flex items-center gap-4">
            <Link
              href="/admin/labs"
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-400 hover:text-purple-400 hover:border-purple-500/50 transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">Labs</span>
            </Link>
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg">
                <Command className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-medium text-white">
                Command Center
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1">
        <SovereignPortal />
      </div>
    </div>
  );
}
