'use client';

/**
 * Fragility Triage Admin Dashboard
 *
 * Cascading failure analysis and black swan simulation
 * for medical residency scheduling resilience.
 */
import { useState, useEffect, useCallback } from 'react';
import { Skull, Activity } from 'lucide-react';
import {
  FragilityGrid,
  AnalysisPanel,
  SimulationControl,
  generateMockDays,
} from '@/features/fragility-triage';
import type { DayData, Scenario, AnalysisResponse } from '@/features/fragility-triage';

export default function FragilityTriagePage() {
  const [days, setDays] = useState<DayData[]>([]);
  const [selectedDay, setSelectedDay] = useState<DayData | null>(null);
  const [redundancy, setRedundancy] = useState(72);

  // AI Analysis State (mock for now)
  const [aiAnalysis, setAiAnalysis] = useState<Record<number, AnalysisResponse>>({});
  const [isLoadingAI, setIsLoadingAI] = useState(false);

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

  // Loading state
  if (!selectedDay) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
          <Activity className="w-5 h-5 animate-pulse" />
          <span>Initializing Fragility Core...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
              <Skull className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Fragility Triage
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Cascading Failure Analysis // 28-Day Cycle
              </p>
            </div>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              System Status
            </div>
            <div
              className={`text-sm font-semibold ${
                redundancy < 50
                  ? 'text-red-600 dark:text-red-400 animate-pulse'
                  : 'text-emerald-600 dark:text-emerald-400'
              }`}
            >
              {redundancy < 50 ? 'CRITICAL INSTABILITY' : 'OPERATIONAL'}
            </div>
          </div>
          <div className="pl-6 border-l border-gray-200 dark:border-gray-700 text-right">
            <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              Redundancy
            </div>
            <div
              className={`text-3xl font-bold ${
                redundancy < 50
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-emerald-600 dark:text-emerald-400'
              }`}
            >
              {redundancy}%
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Grid & Controls */}
        <div className="lg:col-span-5 space-y-6">
          {/* Temporal Map */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
                  Temporal Map
                </h2>
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
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
              subColor="text-gray-500 dark:text-gray-400"
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
      <div className="flex flex-col md:flex-row justify-between items-center pt-6 border-t border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <span>System requires 7 faculty anchors to maintain coherence.</span>
        </div>
        <div className="text-xs italic mt-2 md:mt-0">
          &quot;The system is only as strong as its most exhausted node.&quot;
        </div>
      </div>
    </div>
  );
}

// Metric Card Component
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-md transition-shadow">
      <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className="text-xl font-bold text-gray-900 dark:text-white">
        {value}{' '}
        <span className={`text-xs ${subColor} ml-1`}>{subValue}</span>
      </div>
    </div>
  );
}
