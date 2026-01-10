import { useVulnerabilityReport } from "@/hooks/useResilience";
import { AlertTriangle, CheckCircle2, Shield, Users } from "lucide-react";

export function N1Analysis() {
  const { data, isLoading, error } = useVulnerabilityReport();

  if (isLoading) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 h-full flex items-center justify-center">
        <div className="animate-pulse text-slate-500 text-sm">
          Analyzing N-1 Topology...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 h-full flex flex-col items-center justify-center text-center">
        <Shield className="w-10 h-10 text-slate-600 mb-3" />
        <h3 className="text-slate-400 font-medium">
          Vulnerability Data Unavailable
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Unable to compute N-1 status
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            N-1 Analysis
          </h2>
          <p className="text-sm text-slate-400">
            Single Point of Failure Detection
          </p>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-white">
            {data.n1Pass ? "PASSED" : "FAILED"}
          </div>
          <div
            className={`text-xs uppercase font-medium ${
              data.n1Pass ? "text-green-400" : "text-red-400"
            }`}
          >
            Status
          </div>
        </div>
      </div>

      <div className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {/* Critical Roles (Most Critical Faculty) */}
        {data.mostCriticalFaculty && data.mostCriticalFaculty.length > 0 ? (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-red-400 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-3 h-3" />
              Critical Redundancy Risks
            </h3>
            {data.mostCriticalFaculty.slice(0, 3).map((faculty, i) => (
              <div
                key={i}
                className="bg-red-500/10 border border-red-500/20 rounded-lg p-3"
              >
                <div className="flex justify-between items-start">
                  <span className="text-sm font-medium text-red-200">
                    {faculty.facultyName}
                  </span>
                  <span className="text-xs text-red-300 font-mono">
                    Score: {faculty.centralityScore.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-red-300/80 mt-1">
                  Risk Level: {faculty.riskLevel}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-400" />
            <div>
              <div className="text-sm font-medium text-green-300">
                Resilience Optimal
              </div>
              <div className="text-xs text-green-400/80">
                No single points of failure detected.
              </div>
            </div>
          </div>
        )}

        {/* Mitigation Strategies (Recommended Actions) */}
        <div className="pt-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Mitigation Strategies
          </h3>
          <ul className="space-y-2">
            {data.recommendedActions && data.recommendedActions.length > 0 ? (
              data.recommendedActions.slice(0, 3).map((rec, i) => (
                <li
                  key={i}
                  className="text-sm text-slate-300 flex items-start gap-2"
                >
                  <span className="text-purple-400 mt-1">•</span>
                  {rec}
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500 italic">
                No active recommendations.
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
