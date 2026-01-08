'use client';

/**
 * ExpiringCredentialsAlert Component
 *
 * Alert banner showing credentials expiring soon.
 */
import { useMemo } from 'react';
import { AlertTriangle, Clock, ChevronRight } from 'lucide-react';
import type { Credential } from '@/hooks/useProcedures';

// ============================================================================
// Types
// ============================================================================

export interface ExpiringCredentialsAlertProps {
  credentials: Credential[];
  isLoading?: boolean;
}

// ============================================================================
// Helpers
// ============================================================================

function getDaysUntilExpiration(expirationDate: string): number {
  const expDate = new Date(expirationDate);
  const today = new Date();
  const diffTime = expDate.getTime() - today.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

function getSeverity(days: number): 'critical' | 'warning' | 'info' {
  if (days <= 7) return 'critical';
  if (days <= 14) return 'warning';
  return 'info';
}

// ============================================================================
// Main Component
// ============================================================================

export function ExpiringCredentialsAlert({
  credentials,
  isLoading = false,
}: ExpiringCredentialsAlertProps) {
  // Group by severity
  const grouped = useMemo(() => {
    const critical: Credential[] = [];
    const warning: Credential[] = [];
    const info: Credential[] = [];

    credentials.forEach((cred) => {
      if (!cred.expiration_date) return;
      const days = getDaysUntilExpiration(cred.expiration_date);
      const severity = getSeverity(days);

      if (severity === 'critical') critical.push(cred);
      else if (severity === 'warning') warning.push(cred);
      else info.push(cred);
    });

    return { critical, warning, info };
  }, [credentials]);

  if (isLoading || credentials.length === 0) {
    return null;
  }

  const totalCritical = grouped.critical.length;
  const totalWarning = grouped.warning.length;
  const totalInfo = grouped.info.length;

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">
            Expiring Credentials
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {totalCritical > 0 && (
            <span className="px-2 py-1 rounded bg-red-500/20 text-red-400">
              {totalCritical} critical
            </span>
          )}
          {totalWarning > 0 && (
            <span className="px-2 py-1 rounded bg-amber-500/20 text-amber-400">
              {totalWarning} warning
            </span>
          )}
          {totalInfo > 0 && (
            <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400">
              {totalInfo} soon
            </span>
          )}
        </div>
      </div>

      {/* List */}
      <div className="divide-y divide-slate-700/50 max-h-[200px] overflow-y-auto">
        {[...grouped.critical, ...grouped.warning, ...grouped.info].slice(0, 10).map((cred) => {
          const days = getDaysUntilExpiration(cred.expiration_date!);
          const severity = getSeverity(days);

          return (
            <div
              key={cred.id}
              className="px-4 py-2 flex items-center justify-between hover:bg-slate-700/30"
            >
              <div className="flex items-center gap-3">
                <Clock
                  className={`w-4 h-4 ${
                    severity === 'critical'
                      ? 'text-red-400'
                      : severity === 'warning'
                      ? 'text-amber-400'
                      : 'text-blue-400'
                  }`}
                />
                <div>
                  <div className="text-sm text-white">
                    Credential #{cred.id.slice(0, 8)}
                  </div>
                  <div className="text-xs text-slate-400">
                    Expires in {days} day{days !== 1 ? 's' : ''}
                  </div>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500" />
            </div>
          );
        })}

        {credentials.length > 10 && (
          <div className="px-4 py-2 text-center text-xs text-slate-400">
            +{credentials.length - 10} more expiring soon
          </div>
        )}
      </div>
    </div>
  );
}
