import { useSystemHealth, useUtilizationThreshold } from "@/hooks";
import { motion } from "framer-motion";
import { AlertCircle, TrendingUp } from "lucide-react";

/**
 * UtilizationChart - System utilization visualization
 *
 * Self-contained component that fetches utilization data via useSystemHealth hook.
 * Displays real-time utilization metrics including:
 * - Total utilization bar
 * - Safety buffer indicator
 * - Demand/Capacity/Wait time metrics grid
 *
 * Additionally fetches detailed utilization threshold analysis for enhanced recommendations.
 */
export function UtilizationChart() {
  const { data, isLoading, error } = useSystemHealth();

  // Fetch detailed utilization threshold analysis when we have faculty/block data
  const { data: thresholdData } = useUtilizationThreshold(
    {
      available_faculty: data?.utilization?.safe_capacity ?? 0,
      required_blocks: data?.utilization?.current_demand ?? 0,
    },
    {
      enabled: !!data && data.utilization.safe_capacity > 0,
    }
  );

  if (isLoading) {
    return (
      <div className="h-full w-full bg-slate-800/30 rounded-xl animate-pulse flex items-center justify-center">
        <span className="text-slate-500">Loading visualization...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full w-full bg-slate-900/50 border border-red-500/20 rounded-xl flex items-center justify-center p-6">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-3" />
          <p className="text-red-300 font-medium">Unable to load utilization data</p>
          <p className="text-red-400/80 text-sm mt-1">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="p-6 bg-slate-900/50 border border-slate-700/50 rounded-xl backdrop-blur-sm"
    >
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white">System Utilization</h3>
        <p className="text-sm text-slate-400">
          Current load vs safe capacity limits
        </p>
      </div>

      <div className="h-[300px] w-full">
        {/* Note: For a real time-series, we would map historical data here.
            Since we only have snapshot data in HealthCheckResponse,
            we'll render a gauge-like visualization or wait for historical API integration.

            For V1, creating a visual representation of the current utilization levels.
        */}
        <div className="relative h-full flex flex-col justify-center space-y-8">
          {/* Custom Visualization for Snapshot Data */}

          {/* Utilization Bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300">Total Utilization</span>
              <span className="font-mono text-white">
                {(data.utilization.utilization_rate * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-4 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${Math.min(
                    data.utilization.utilization_rate * 100,
                    100
                  )}%`,
                }}
                transition={{ duration: 1, ease: "easeOut" }}
                className={`h-full rounded-full ${
                  data.utilization.utilization_rate > 0.9
                    ? "bg-red-500"
                    : data.utilization.utilization_rate > 0.8
                    ? "bg-orange-500"
                    : data.utilization.utilization_rate > 0.7
                    ? "bg-yellow-500"
                    : "bg-green-500"
                }`}
              />
            </div>
          </div>

          {/* Buffer Bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300">Safety Buffer</span>
              <span className="font-mono text-white">
                {data.utilization.buffer_remaining.toFixed(1)} FTE
              </span>
            </div>
            <div className="h-4 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${Math.min(
                    (data.utilization.buffer_remaining / 5) * 100,
                    100
                  )}%`,
                }} // Normalized assumption: 5 FTE max buffer visual
                transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
                className="h-full bg-blue-500 rounded-full"
              />
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-800">
            <div className="text-center">
              <div className="text-xs text-slate-500 uppercase tracking-wider">
                Demand
              </div>
              <div className="text-xl font-bold text-white">
                {data.utilization.current_demand}
              </div>
              <div className="text-xs text-slate-400">Assignments</div>
            </div>
            <div className="text-center border-l border-slate-800">
              <div className="text-xs text-slate-500 uppercase tracking-wider">
                Safe Capacity
              </div>
              <div className="text-xl font-bold text-green-400">
                {data.utilization.safe_capacity}
              </div>
              <div className="text-xs text-slate-400">Assignments</div>
            </div>
            <div className="text-center border-l border-slate-800">
              <div className="text-xs text-slate-500 uppercase tracking-wider">
                Wait Time
              </div>
              <div className="text-xl font-bold text-blue-400">
                {data.utilization.wait_time_multiplier.toFixed(1)}x
              </div>
              <div className="text-xs text-slate-400">Multiplier</div>
            </div>
          </div>

          {/* Threshold Status from detailed analysis */}
          {thresholdData && (
            <div className="pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-slate-400" />
                <span className="text-xs text-slate-400 uppercase tracking-wider">
                  Threshold Analysis
                </span>
              </div>
              <p className="text-sm text-slate-300">{thresholdData.message}</p>
              {thresholdData.recommendations && thresholdData.recommendations.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {thresholdData.recommendations.slice(0, 2).map((rec, i) => (
                    <li
                      key={i}
                      className="text-xs text-slate-400 flex items-start gap-2"
                    >
                      <span className="text-blue-400">-</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
