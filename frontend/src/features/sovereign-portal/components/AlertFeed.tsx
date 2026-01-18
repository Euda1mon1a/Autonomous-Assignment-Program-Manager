/**
 * Alert Feed Component
 *
 * Shows recent system alerts from all panels.
 */

'use client';

import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { formatTimestamp } from '../constants';
import type { SystemAlert } from '../types';

interface AlertFeedProps {
  alerts: SystemAlert[];
  maxAlerts?: number;
}

const SEVERITY_CONFIG = {
  info: {
    icon: Info,
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
  },
  critical: {
    icon: AlertCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
  },
};

export function AlertFeed({ alerts, maxAlerts = 5 }: AlertFeedProps) {
  const displayAlerts = alerts.slice(0, maxAlerts);

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-3">
        System Alerts
      </h3>

      {displayAlerts.length === 0 ? (
        <p className="text-xs text-slate-500 italic">No active alerts</p>
      ) : (
        <div className="space-y-2">
          {displayAlerts.map((alert) => {
            const config = SEVERITY_CONFIG[alert.severity];
            const Icon = config.icon;

            return (
              <div
                key={alert.id}
                className={`flex items-start gap-3 p-2 rounded-lg ${config.bg}`}
              >
                <Icon className={`w-4 h-4 mt-0.5 ${config.color}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white">{alert.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-500 uppercase">
                      {alert.panel}
                    </span>
                    <span className="text-xs text-slate-600">•</span>
                    <span className="text-xs text-slate-500">
                      {formatTimestamp(alert.timestamp)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default AlertFeed;
