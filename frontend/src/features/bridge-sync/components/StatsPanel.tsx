/**
 * Stats Panel Component
 *
 * Real-time sync statistics display.
 */

'use client';

import { Activity, Zap, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import type { SyncStats, ConnectionStatus } from '../types';

interface StatsPanelProps {
  stats: SyncStats;
  connection: ConnectionStatus;
}

export function StatsPanel({ stats, connection }: StatsPanelProps) {
  const connectionColor =
    connection === 'connected'
      ? 'text-green-400'
      : connection === 'connecting'
        ? 'text-amber-400'
        : 'text-red-400';

  return (
    <div className="absolute top-4 left-4 w-72 bg-slate-950/90 border border-slate-800 p-4 rounded-xl backdrop-blur-md text-white font-mono">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-cyan-400 uppercase tracking-wide">
          Bridge Sync
        </h2>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              connection === 'connected'
                ? 'bg-green-400 animate-pulse'
                : connection === 'connecting'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-red-400'
            }`}
          />
          <span className={`text-xs uppercase ${connectionColor}`}>
            {connection}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <Activity className="w-4 h-4" />
            <span className="text-xs">Packets/sec</span>
          </div>
          <span className="text-sm font-bold text-white">
            {stats.packetsPerSecond}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <Zap className="w-4 h-4" />
            <span className="text-xs">Throughput</span>
          </div>
          <span className="text-sm font-bold text-white">
            {(stats.bytesPerSecond / 1024).toFixed(1)} KB/s
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <Clock className="w-4 h-4" />
            <span className="text-xs">Latency</span>
          </div>
          <span
            className={`text-sm font-bold ${
              stats.latencyMs < 20
                ? 'text-green-400'
                : stats.latencyMs < 50
                  ? 'text-amber-400'
                  : 'text-red-400'
            }`}
          >
            {stats.latencyMs}ms
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-xs">Error Rate</span>
          </div>
          <span
            className={`text-sm font-bold ${
              stats.errorRate < 0.01
                ? 'text-green-400'
                : stats.errorRate < 0.05
                  ? 'text-amber-400'
                  : 'text-red-400'
            }`}
          >
            {(stats.errorRate * 100).toFixed(2)}%
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <CheckCircle className="w-4 h-4" />
            <span className="text-xs">Uptime</span>
          </div>
          <span className="text-sm font-bold text-green-400">
            {stats.uptime.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-slate-700">
        <div className="text-xs text-slate-500 mb-2">Packet Types</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-slate-400">Schedule</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span className="text-slate-400">Constraint</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-yellow-500" />
            <span className="text-slate-400">Solution</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple-500" />
            <span className="text-slate-400">Validation</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StatsPanel;
