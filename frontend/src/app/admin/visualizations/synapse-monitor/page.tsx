"use client";

import dynamic from "next/dynamic";

const SynapseMonitor = dynamic(
  () =>
    import("@/features/synapse-monitor").then((mod) => mod.SynapseMonitor),
  {
    ssr: false,
    loading: () => (
      <div className="min-h-screen bg-[#020202] flex items-center justify-center">
        <div className="text-cyan-400 font-mono text-sm animate-pulse">
          Initializing Neural Interface...
        </div>
      </div>
    ),
  }
);

export default function SynapseMonitorPage() {
  return <SynapseMonitor />;
}
