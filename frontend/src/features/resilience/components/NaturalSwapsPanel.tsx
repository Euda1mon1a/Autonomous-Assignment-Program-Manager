import React from "react";
import { useNaturalSwaps } from "@/hooks/useResilience";
import { RefreshCw, ArrowLeftRight } from "lucide-react";

interface NaturalSwapsPanelProps {
  scheduleId?: string;
}

export function NaturalSwapsPanel({ scheduleId }: NaturalSwapsPanelProps) {
  const { data, isLoading, isError, refetch, isRefetching } = useNaturalSwaps(
    scheduleId ?? "",
    5,
    { enabled: !!scheduleId }
  );

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5 text-indigo-400" />
            Natural Swaps
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Topologically sound schedule trades based on foam dynamics.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isRefetching || !scheduleId}
          className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRefetching ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto pr-2">
        {!scheduleId ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 py-8">
            <ArrowLeftRight className="w-12 h-12 mb-4 opacity-20" />
            <p>Select a schedule to view natural swaps</p>
          </div>
        ) : isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse flex space-x-4">
                <div className="flex-1 space-y-4 py-1">
                  <div className="h-4 bg-slate-800 rounded w-3/4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-slate-800 rounded"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className="text-red-400 text-sm p-4 bg-red-900/20 rounded-lg">
            Unable to calculate natural swaps. Check backend services.
          </div>
        ) : data?.recommendations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <p>No natural swaps found.</p>
            <p className="text-xs mt-1">The schedule topology is currently rigid.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {data?.recommendations.map((swap, i) => (
              <div
                key={i}
                className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 hover:border-indigo-500/50 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-300">
                    Trade Option #{i + 1}
                  </span>
                  <span
                    className={`text-xs px-2 py-1 rounded-full ${
                      swap.naturalScore > 0.8
                        ? "bg-green-500/20 text-green-400"
                        : swap.naturalScore > 0.5
                        ? "bg-yellow-500/20 text-yellow-400"
                        : "bg-slate-700 text-slate-300"
                    }`}
                  >
                    {(swap.naturalScore * 100).toFixed(0)}% Natural
                  </span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-400">
                  <div className="flex-1 truncate" title={swap.residentA}>
                    Res: {swap.residentA.substring(0, 8)}...
                  </div>
                  <ArrowLeftRight className="w-4 h-4 flex-shrink-0 text-slate-500" />
                  <div className="flex-1 truncate" title={swap.residentB}>
                    Res: {swap.residentB.substring(0, 8)}...
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs">
                  <span className="text-slate-500">
                    Energy Δ: {swap.energyImprovement.toFixed(2)}
                  </span>
                  <button className="text-indigo-400 hover:text-indigo-300 font-medium">
                    Review Swap
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
