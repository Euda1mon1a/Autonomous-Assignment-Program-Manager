import { useSystemHealth, useBurnoutRt } from "@/hooks";
import { motion } from "framer-motion";
import { AlertCircle, CheckCircle, Info, Activity, TrendingUp, TrendingDown } from "lucide-react";

interface BurnoutDashboardProps {
  /** Optional list of provider IDs currently experiencing burnout for Rt calculation */
  burnedOutProviderIds?: string[];
}

/**
 * BurnoutDashboard - Analysis & Recommendations with optional Burnout Rt
 *
 * Self-contained component that fetches system health data via useSystemHealth hook.
 * Displays immediate actions and watch items from the resilience system.
 *
 * When burnedOutProviderIds are provided, also displays burnout epidemiological
 * metrics including the reproduction number (Rt) via useBurnoutRt hook.
 */
export function BurnoutDashboard({ burnedOutProviderIds = [] }: BurnoutDashboardProps) {
  const { data, isLoading, error } = useSystemHealth();

  // Only fetch burnout Rt if we have provider IDs (the hook is disabled with empty array)
  const {
    data: burnoutData,
    isLoading: burnoutLoading,
  } = useBurnoutRt(burnedOutProviderIds);

  if (isLoading) {
    return (
      <div className="h-full w-full bg-slate-800/30 rounded-xl animate-pulse" />
    );
  }

  if (error) {
    return (
      <div className="h-full p-6 bg-slate-900/50 border border-red-500/20 rounded-xl flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-6 h-6 text-red-400 mx-auto mb-2" />
          <p className="text-red-300 text-sm">Unable to load data</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="p-6 bg-slate-900/50 border border-slate-700/50 rounded-xl backdrop-blur-sm flex flex-col h-full"
    >
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">
            Analysis & Recommendations
          </h3>
          <p className="text-sm text-slate-400">
            Actionable insights for system stability
          </p>
        </div>
        <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center">
          <Info className="w-4 h-4 text-slate-400" />
        </div>
      </div>

      <div className="space-y-6 overflow-y-auto pr-2 custom-scrollbar">
        {/* Immediate Actions */}
        {data.immediate_actions.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              Immediate Actions Required
            </h4>
            <div className="space-y-2">
              {data.immediate_actions.map((action, idx) => (
                <motion.div
                  key={`action-${idx}`}
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.2 + idx * 0.1 }}
                  className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-200"
                >
                  {action}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Watch Items */}
        {data.watch_items.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-yellow-400 uppercase tracking-wider flex items-center gap-2">
              <Info className="w-4 h-4" />
              Watch Items
            </h4>
            <div className="space-y-2">
              {data.watch_items.map((item, idx) => (
                <motion.div
                  key={`watch-${idx}`}
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.4 + idx * 0.1 }}
                  className="p-3 bg-yellow-500/5 border border-yellow-500/10 rounded-lg text-sm text-yellow-200"
                >
                  {item}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {data.immediate_actions.length === 0 &&
          data.watch_items.length === 0 && (
            <div className="h-40 flex flex-col items-center justify-center text-center p-4 border border-dashed border-slate-700 rounded-lg">
              <CheckCircle className="w-8 h-8 text-green-500 mb-2" />
              <p className="text-slate-300 font-medium">All Clear</p>
              <p className="text-xs text-slate-500">
                No immediate risks detected.
              </p>
            </div>
          )}

        {/* Burnout Rt Section (only shown when provider IDs are available) */}
        {burnedOutProviderIds.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-slate-700">
            <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Burnout Epidemiology
            </h4>

            {burnoutLoading ? (
              <div className="p-3 bg-slate-800/50 rounded-lg animate-pulse">
                <div className="h-4 bg-slate-700 rounded w-1/2 mb-2" />
                <div className="h-3 bg-slate-700 rounded w-3/4" />
              </div>
            ) : burnoutData ? (
              <motion.div
                initial={{ x: -10, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                className={`p-4 rounded-lg border ${
                  burnoutData.rt > 1
                    ? "bg-red-500/10 border-red-500/20"
                    : burnoutData.rt > 0.8
                    ? "bg-yellow-500/10 border-yellow-500/20"
                    : "bg-green-500/10 border-green-500/20"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">
                    Reproduction Number (Rt)
                  </span>
                  <div className="flex items-center gap-1">
                    {burnoutData.rt > 1 ? (
                      <TrendingUp className="w-4 h-4 text-red-400" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-green-400" />
                    )}
                    <span
                      className={`text-lg font-bold ${
                        burnoutData.rt > 1
                          ? "text-red-400"
                          : burnoutData.rt > 0.8
                          ? "text-yellow-400"
                          : "text-green-400"
                      }`}
                    >
                      {burnoutData.rt.toFixed(2)}
                    </span>
                  </div>
                </div>
                <p
                  className={`text-xs ${
                    burnoutData.rt > 1
                      ? "text-red-200/80"
                      : burnoutData.rt > 0.8
                      ? "text-yellow-200/80"
                      : "text-green-200/80"
                  }`}
                >
                  Status:{" "}
                  <span className="capitalize">{burnoutData.status}</span>
                  {burnoutData.secondary_cases > 0 &&
                    ` (${burnoutData.secondary_cases} secondary cases)`}
                </p>

                {/* Interventions */}
                {burnoutData.interventions && burnoutData.interventions.length > 0 && (
                  <ul className="mt-3 space-y-1">
                    {burnoutData.interventions.slice(0, 2).map((intervention, i) => (
                      <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                        <span className="text-purple-400">-</span>
                        {intervention}
                      </li>
                    ))}
                  </ul>
                )}
              </motion.div>
            ) : null}
          </div>
        )}
      </div>
    </motion.div>
  );
}
