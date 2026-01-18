'use client';

/**
 * Resilience & Risk Labs
 *
 * Identify cascading failure risks and simulate black swan events.
 * Target: Tier 1-2 users (medium graduation readiness)
 *
 * Contains:
 * - Fragility Triage: Cascading failure analysis and simulation
 * - N-1/N-2 Resilience: Faculty absence simulation
 *
 * Note: May merge with Optimization category in the future if concepts converge
 * under a unified "Scheduling Intelligence" domain.
 *
 * @route /admin/labs/resilience
 */

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Skull, Activity, ArrowLeft, Shield, Users } from 'lucide-react';
import {
  FragilityGrid,
  AnalysisPanel,
  SimulationControl,
  generateMockDays,
} from '@/features/fragility-triage';
import type { DayData, Scenario, AnalysisResponse } from '@/features/fragility-triage';

// Dynamic import for N-1/N-2 visualizer
const N1N2Visualizer = dynamic(
  () => import('@/features/n1n2-resilience').then((mod) => mod.N1N2Visualizer),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
          <p className="mt-4 text-sm uppercase tracking-widest text-cyan-400">
            Initializing Resilience Simulator...
          </p>
        </div>
      </div>
    ),
  }
);

type TabId = 'fragility' | 'n1n2';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ElementType;
  description: string;
}

const TABS: Tab[] = [
  {
    id: 'fragility',
    label: 'Fragility Triage',
    icon: Skull,
    description: 'Cascading failure analysis',
  },
  {
    id: 'n1n2',
    label: 'N-1/N-2 Resilience',
    icon: Users,
    description: 'Faculty absence simulation',
  },
];

function MetricCard({
  label,
  value,
  subValue,
  subColor,
}: {
  label: string;
  value: string;
  subValue: string;
  subColor: string;
}) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-colors">
      <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className="text-xl font-bold text-white">
        {value}{' '}
        <span className={`text-xs ${subColor} ml-1`}>{subValue}</span>
      </div>
    </div>
  );
}

export default function ResilienceLabsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('fragility');
  const [days, setDays] = useState<DayData[]>([]);
  const [selectedDay, setSelectedDay] = useState<DayData | null>(null);
  const [redundancy, setRedundancy] = useState(72);

  // AI Analysis State (mock for now)
  const [aiAnalysis, setAiAnalysis] = useState<Record<number, AnalysisResponse>>({});
  const [isLoadingAI, setIsLoadingAI] = useState(false);

  const handleTabChange = useCallback((tabId: TabId) => {
    setActiveTab(tabId);
  }, []);

  // Initialize on mount
  useEffect(() => {
    const initialDays = generateMockDays();
    setDays(initialDays);
    setSelectedDay(initialDays[0]);
  }, []);

  const handleInject = useCallback((scenario: Scenario) => {
    setRedundancy((prev) => Math.max(0, prev - scenario.impact));

    // Simulation effect: Increase fragility of random days when disaster strikes
    setDays((prevDays) =>
      prevDays.map((d) => ({
        ...d,
        fragility: Math.min(1, d.fragility + Math.random() * 0.15),
        violations:
          d.fragility > 0.5 && d.violations.length === 0
            ? [...d.violations, 'Emergent Staffing Gap']
            : d.violations,
      }))
    );

    // Clear AI analysis as state has changed
    setAiAnalysis({});
  }, []);

  const handleReset = useCallback(() => {
    setRedundancy(72);
    const newDays = generateMockDays();
    setDays(newDays);
    setSelectedDay(newDays[0]);
    setAiAnalysis({});
  }, []);

  const handleRunAI = useCallback(async () => {
    if (!selectedDay) return;

    setIsLoadingAI(true);

    // Mock AI analysis - in production, this would call a real endpoint
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const mockAnalysis: AnalysisResponse = {
      analysis:
        selectedDay.fragility > 0.7
          ? `Day ${selectedDay.day} shows critical instability. The ${selectedDay.spof || 'current configuration'} represents a single point of failure that could cascade through the entire scheduling matrix.`
          : selectedDay.fragility > 0.4
            ? `Day ${selectedDay.day} exhibits moderate stress levels. Preemptive faculty reallocation recommended before secondary failures emerge.`
            : `Day ${selectedDay.day} is operating within nominal parameters. Current redundancy buffers are sufficient.`,
      mitigations:
        selectedDay.fragility > 0.7
          ? [
              'Activate emergency float pool',
              'Redistribute senior resident coverage',
              'Consider temporary schedule compression',
            ]
          : selectedDay.fragility > 0.4
            ? [
                'Pre-position backup faculty',
                'Review cross-coverage agreements',
              ]
            : ['Maintain current posture', 'Continue monitoring'],
    };

    setAiAnalysis((prev) => ({
      ...prev,
      [selectedDay.day]: mockAnalysis,
    }));
    setIsLoadingAI(false);
  }, [selectedDay]);

  // Loading state for Fragility tab
  if (activeTab === 'fragility' && !selectedDay) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Activity className="w-5 h-5 animate-pulse" />
          <span>Initializing Fragility Core...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Header with tabs */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
            <div className="flex items-center gap-4">
              {/* Back to Labs */}
              <Link
                href="/admin/labs"
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-400 hover:text-amber-400 hover:border-amber-500/50 transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm">Labs</span>
              </Link>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white flex items-center gap-2">
                    Resilience & Risk
                  </h1>
                  <p className="text-sm text-slate-300">
                    Failure Analysis & Absence Simulation
                  </p>
                </div>
              </div>
            </div>

            {/* Status Indicators - only show for Fragility tab */}
            {activeTab === 'fragility' && (
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-xs text-slate-400 uppercase tracking-wide">
                    System Status
                  </div>
                  <div
                    className={`text-sm font-semibold ${
                      redundancy < 50
                        ? 'text-red-400 animate-pulse'
                        : 'text-emerald-400'
                    }`}
                  >
                    {redundancy < 50 ? 'CRITICAL INSTABILITY' : 'OPERATIONAL'}
                  </div>
                </div>
                <div className="pl-6 border-l border-slate-700 text-right">
                  <div className="text-xs text-slate-400 uppercase tracking-wide">
                    Redundancy
                  </div>
                  <div
                    className={`text-3xl font-bold ${
                      redundancy < 50
                        ? 'text-red-400'
                        : 'text-emerald-400'
                    }`}
                  >
                    {redundancy}%
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-2">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50 border border-transparent'
                  }`}
                  title={tab.description}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content - Tab-based rendering */}
      {activeTab === 'fragility' && selectedDay && (
        <main className="max-w-7xl mx-auto px-4 py-6">
          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Grid & Controls */}
            <div className="lg:col-span-5 space-y-6">
              {/* Temporal Map */}
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-slate-400" />
                    <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
                      Temporal Map
                    </h2>
                  </div>
                  <span className="text-xs text-slate-400 bg-slate-700 px-2 py-1 rounded">
                    28-DAY CYCLE
                  </span>
                </div>
                <FragilityGrid
                  days={days}
                  selectedDay={selectedDay}
                  onSelectDay={setSelectedDay}
                />
              </div>

              {/* Simulation Control */}
              <SimulationControl
                onInject={handleInject}
                onReset={handleReset}
                redundancy={redundancy}
              />
            </div>

            {/* Right Column: Analysis */}
            <div className="lg:col-span-7 space-y-6">
              {/* Analysis Panel */}
              <AnalysisPanel
                day={selectedDay}
                aiData={aiAnalysis[selectedDay.day] || null}
                isLoadingAi={isLoadingAI}
                onRunAi={handleRunAI}
              />

              {/* Secondary Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <MetricCard
                  label="Jain's Decay"
                  value="0.84"
                  subValue="(-0.02)"
                  subColor="text-red-500"
                />
                <MetricCard
                  label="Max Delay"
                  value="4.2h"
                  subValue="NORMAL"
                  subColor="text-slate-400"
                />
                <MetricCard
                  label="FMIT Buffer"
                  value="1.0"
                  subValue="OPTIMAL"
                  subColor="text-cyan-500"
                />
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex flex-col md:flex-row justify-between items-center pt-6 mt-6 border-t border-slate-700 text-slate-400">
            <div className="flex items-center gap-2 text-xs">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span>System requires 7 faculty anchors to maintain coherence.</span>
            </div>
            <div className="text-xs italic mt-2 md:mt-0">
              &quot;The system is only as strong as its most exhausted node.&quot;
            </div>
          </div>
        </main>
      )}

      {/* N-1/N-2 Resilience Tab */}
      {activeTab === 'n1n2' && (
        <div className="flex-1">
          <N1N2Visualizer />
        </div>
      )}
    </div>
  );
}
