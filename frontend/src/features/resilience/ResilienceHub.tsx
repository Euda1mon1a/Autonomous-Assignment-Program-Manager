import { useSystemHealth } from "@/hooks/useResilience";
import { OverallStatus } from "@/types/resilience";
import { RefreshCw, ShieldAlert } from "lucide-react";
import { useState, useEffect } from "react";
import { BurnoutDashboard } from "./components/BurnoutDashboard";
import { N1Analysis } from "./components/N1Analysis";
import { ResilienceMetrics } from "./components/ResilienceMetrics";
import { UtilizationChart } from "./components/UtilizationChart";

/**
 * ResilienceHub - Main resilience dashboard orchestrator
 *
 * This component serves as the main resilience monitoring dashboard.
 * Child components (ResilienceMetrics, UtilizationChart, BurnoutDashboard, N1Analysis)
 * are now self-contained and fetch their own data via hooks.
 *
 * The parent still fetches system health for:
 * - Emergency mode detection
 * - Timestamp display
 * - Manual refresh functionality
 */
export function ResilienceHub() {
  const { data, refetch, isRefetching } = useSystemHealth();
  const [emergencyMode, setEmergencyMode] = useState(false);

  // Auto-enable emergency visual mode if system status is CRITICAL or EMERGENCY
  useEffect(() => {
    if (
      data?.overallStatus === OverallStatus.CRITICAL ||
      data?.overallStatus === OverallStatus.EMERGENCY
    ) {
      setEmergencyMode(true);
    }
  }, [data?.overallStatus]);

  return (
    <div
      className={`min-h-screen w-full transition-colors duration-1000 ${
        emergencyMode ? "bg-red-950/30" : "bg-transparent"
      }`}
    >
      <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                Resilience Command
              </h1>
              {emergencyMode && (
                <span className="px-3 py-1 text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30 rounded-full animate-pulse flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4" />
                  EMERGENCY PROTOCOLS ACTIVE
                </span>
              )}
            </div>
            <p className="text-slate-400 mt-2">
              System monitoring, vulnerability analysis, and load shedding
              controls.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            >
              <RefreshCw
                className={`w-5 h-5 ${isRefetching ? "animate-spin" : ""}`}
              />
            </button>
            {/* Note: This is a Visual Simulation Toggle for Demonstration */}
            <button
              onClick={() => setEmergencyMode(!emergencyMode)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                emergencyMode
                  ? "bg-red-500/20 text-red-200 border border-red-500/30"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-300"
              }`}
            >
              {emergencyMode ? "Deactivate Sims" : "Simulate Crisis"}
            </button>
          </div>
        </div>

        {/* Key Metrics - Self-contained, fetches own data */}
        <ResilienceMetrics />

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[500px]">
          {/* Chart Section - Takes up 2/3 width */}
          <div className="lg:col-span-2 h-full">
            {/* Self-contained, fetches own data via useSystemHealth and useUtilizationThreshold */}
            <UtilizationChart />
          </div>

          {/* Recommendations / Sidebar - Takes up 1/3 width */}
          <div className="h-full flex flex-col gap-6">
            <div className="flex-1">
              {/* Self-contained, fetches own data via useSystemHealth and optionally useBurnoutRt */}
              {/* To enable burnout Rt, pass burnedOutProviderIds prop */}
              <BurnoutDashboard />
            </div>
            <div className="flex-1">
              {/* Self-contained, fetches own data via useVulnerabilityReport */}
              <N1Analysis />
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="text-xs text-slate-500 italic text-center pt-8">
          Resilience engine polling at 30s intervals. Last updated:{" "}
          {data ? new Date(data.timestamp).toLocaleTimeString() : "..."}
        </div>
      </div>
    </div>
  );
}

export default ResilienceHub;
