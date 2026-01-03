import { useSystemHealth, useDefenseLevel } from "@/hooks";
import { OverallStatus, UtilizationLevel } from "@/types/resilience";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, Shield, Users, AlertCircle } from "lucide-react";

const STAT_VARIANTS: any = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.5,
      ease: "easeOut",
    },
  }),
};

function getStatusColor(status: OverallStatus) {
  switch (status) {
    case OverallStatus.HEALTHY:
      return "text-green-400 bg-green-400/10 border-green-400/20";
    case OverallStatus.WARNING:
      return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
    case OverallStatus.DEGRADED:
      return "text-orange-400 bg-orange-400/10 border-orange-400/20";
    case OverallStatus.CRITICAL:
      return "text-red-400 bg-red-400/10 border-red-400/20";
    case OverallStatus.EMERGENCY:
      return "text-rose-600 bg-rose-600/10 border-rose-600/20 animate-pulse";
    default:
      return "text-slate-400 bg-slate-400/10 border-slate-400/20";
  }
}

function getUtilizationColor(level: UtilizationLevel) {
  switch (level) {
    case UtilizationLevel.GREEN:
      return "text-green-400";
    case UtilizationLevel.YELLOW:
      return "text-yellow-400";
    case UtilizationLevel.ORANGE:
      return "text-orange-400";
    case UtilizationLevel.RED:
      return "text-red-400";
    case UtilizationLevel.BLACK:
      return "text-slate-900 bg-slate-100"; // Special styling for black level
    default:
      return "text-slate-400";
  }
}

/**
 * ResilienceMetrics - Key system health indicators
 *
 * Self-contained component that fetches resilience data via useSystemHealth hook.
 * Displays four key metrics: System Health, Utilization, N-1 Compliance, and Active Fallbacks.
 */
export function ResilienceMetrics() {
  const { data, isLoading, error } = useSystemHealth();

  // Also fetch defense level details for enhanced display
  const coverageRate = data?.utilization?.utilization_rate ?? 0;
  const { data: defenseLevelData } = useDefenseLevel(
    1 - coverageRate, // Coverage rate is inverse of utilization for defense level
    { enabled: !!data && coverageRate > 0 }
  );

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-slate-800/50 rounded-xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="col-span-full p-6 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <div>
            <p className="text-red-300 font-medium">Unable to load resilience metrics</p>
            <p className="text-red-400/80 text-sm">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const metrics = [
    {
      label: "System Health",
      value: data.overall_status.toUpperCase(),
      icon: Activity,
      color: getStatusColor(data.overall_status),
      subtext: `Defense: ${data.defense_level}`,
    },
    {
      label: "Utilization",
      value: `${(data.utilization.utilization_rate * 100).toFixed(1)}%`,
      icon: Users,
      color: `bg-slate-800 border-slate-700 ${getUtilizationColor(
        data.utilization.level
      )}`,
      subtext: `Capacity: ${data.utilization.current_demand} / ${data.utilization.safe_capacity}`,
    },
    {
      label: "N-1 Compliance",
      value: data.n1_pass ? "PASS" : "FAIL",
      icon: Shield,
      color: data.n1_pass
        ? "text-green-400 bg-green-400/10 border-green-400/20"
        : "text-red-400 bg-red-400/10 border-red-400/20",
      subtext: data.n2_pass ? "N-2 Also Passing" : "N-2 Failing",
    },
    {
      label: "Active Fallbacks",
      value: data.active_fallbacks.length.toString(),
      icon: AlertTriangle,
      color:
        data.active_fallbacks.length === 0
          ? "text-blue-400 bg-blue-400/10 border-blue-400/20"
          : "text-orange-400 bg-orange-400/10 border-orange-400/20",
      subtext:
        data.active_fallbacks.length > 0
          ? "Contingencies Active"
          : "Normal Operations",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, i) => (
        <motion.div
          key={metric.label}
          custom={i}
          variants={STAT_VARIANTS}
          initial="hidden"
          animate="visible"
          className={`p-6 rounded-xl border backdrop-blur-sm ${metric.color} transition-all hover:scale-[1.02]`}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium opacity-80 mb-1">
                {metric.label}
              </p>
              <h3 className="text-2xl font-bold">{metric.value}</h3>
              <p className="text-xs mt-2 opacity-60">{metric.subtext}</p>
            </div>
            <metric.icon className="w-6 h-6 opacity-80" />
          </div>
        </motion.div>
      ))}
    </div>
  );
}
