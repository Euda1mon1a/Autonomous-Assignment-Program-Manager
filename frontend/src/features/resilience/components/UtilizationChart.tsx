import type { HealthCheckResponse } from "@/types/resilience";
import { motion } from "framer-motion";
import { useMemo } from "react";

interface UtilizationChartProps {
  data: HealthCheckResponse | undefined;
  isLoading: boolean;
}

export function UtilizationChart({ data, isLoading }: UtilizationChartProps) {
  // Memoize chart data to safely handle nulls
  const chartData = useMemo(() => {
    if (!data) return [];

    // Create a single data point for now based on current snapshot
    // Ideally this would be historical data, but we'll start with the instantaneous view
    return [
      {
        name: "Capacity",
        utilization: data.utilization.utilization_rate * 100,
        safe_limit: 100, // Normalized to %
        demand:
          (data.utilization.current_demand /
            data.utilization.theoretical_capacity) *
          100,
      },
    ];
  }, [data]);

  if (isLoading) {
    return (
      <div className="h-[300px] w-full bg-slate-800/30 rounded-xl animate-pulse flex items-center justify-center">
        <span className="text-slate-500">Loading visualization...</span>
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
        </div>
      </div>
    </motion.div>
  );
}
