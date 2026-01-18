/**
 * Status Badge Component
 *
 * System-wide status indicator.
 */

'use client';

import { Shield, ShieldAlert, ShieldX, ShieldOff } from 'lucide-react';
import { SYSTEM_STATUS_COLORS } from '../constants';
import type { SystemStatus } from '../types';

interface StatusBadgeProps {
  status: SystemStatus;
  lastUpdate?: Date;
}

const STATUS_ICONS = {
  OPERATIONAL: Shield,
  DEGRADED: ShieldAlert,
  CRITICAL: ShieldX,
  OFFLINE: ShieldOff,
};

export function StatusBadge({ status, lastUpdate }: StatusBadgeProps) {
  const Icon = STATUS_ICONS[status];
  const color = SYSTEM_STATUS_COLORS[status];

  return (
    <div className="flex items-center gap-3">
      <div
        className={`p-2 rounded-lg ${
          status === 'OPERATIONAL'
            ? 'bg-green-500/20'
            : status === 'DEGRADED'
              ? 'bg-amber-500/20'
              : status === 'CRITICAL'
                ? 'bg-red-500/20'
                : 'bg-slate-500/20'
        }`}
      >
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div>
        <div className={`text-lg font-bold ${color}`}>{status}</div>
        {lastUpdate && (
          <div className="text-xs text-slate-500">
            Last update: {lastUpdate.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}

export default StatusBadge;
