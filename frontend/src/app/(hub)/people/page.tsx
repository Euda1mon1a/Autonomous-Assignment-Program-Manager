'use client';

/**
 * People Hub - Unified People Management Interface
 *
 * Consolidates the read-only people directory and admin people management
 * into a single hub with tier-based access controls and risk indicators.
 *
 * Tier Model:
 * - Tier 0 (Green): Read-only directory view for residents and faculty
 * - Tier 1 (Amber): Role/PGY updates for coordinators and PDs
 * - Tier 2 (Red): Bulk delete operations for admins
 *
 * WCAG 2.1 AA Compliance: All interactive elements have proper focus
 * indicators, color contrast ratios, and keyboard navigation support.
 */
import { useState, useMemo, useCallback } from 'react';
import { Users } from 'lucide-react';
import { RiskBar, type RiskTier } from '@/components/ui/RiskBar';
import { useAuth, type UserRole } from '@/hooks/useAuth';
import { PeopleDirectory } from '@/components/people/PeopleDirectory';
import { PeopleAdminPanel } from '@/components/people/PeopleAdminPanel';
import { LoadingSpinner } from '@/components/LoadingSpinner';

// ============================================================================
// Types
// ============================================================================

type ViewMode = 'directory' | 'admin';

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Determines the risk tier based on user role and current view mode
 */
function getRiskTier(role: UserRole | undefined, viewMode: ViewMode): RiskTier {
  if (!role) return 0;

  // Tier 2: Admin with bulk delete capability
  if (role === 'admin' && viewMode === 'admin') {
    return 2;
  }

  // Tier 1: Coordinator/Admin in admin view (can edit roles/PGY)
  if ((role === 'coordinator' || role === 'admin') && viewMode === 'admin') {
    return 1;
  }

  // Tier 0: Everyone else or directory view
  return 0;
}

/**
 * Gets appropriate labels for the risk bar based on tier and context
 */
function getRiskBarConfig(tier: RiskTier, viewMode: ViewMode): { label: string; tooltip: string } {
  switch (tier) {
    case 2:
      return {
        label: 'High Impact',
        tooltip: 'Bulk delete and system-wide changes available. Review changes carefully before applying.',
      };
    case 1:
      return {
        label: 'Scoped Changes',
        tooltip: 'You can update role and PGY level for individuals. Changes are reversible.',
      };
    case 0:
    default:
      return {
        label: viewMode === 'admin' ? 'View Only' : 'Read-only',
        tooltip: 'You can view the people directory. No changes can be made.',
      };
  }
}

/**
 * Checks if user can access admin panel
 */
function canAccessAdmin(role: UserRole | undefined): boolean {
  return role === 'admin' || role === 'coordinator';
}

/**
 * Checks if user can perform bulk delete (Tier 2)
 */
function canBulkDelete(role: UserRole | undefined): boolean {
  return role === 'admin';
}

// ============================================================================
// Main Component
// ============================================================================

export default function PeopleHubPage() {
  const { user, isLoading, isAuthenticated } = useAuth();
  const [viewMode, setViewMode] = useState<ViewMode>('directory');

  const userRole = user?.role as UserRole | undefined;
  const hasAdminAccess = canAccessAdmin(userRole);
  const hasBulkDeleteAccess = canBulkDelete(userRole);

  // Calculate risk tier based on role and view mode
  const riskTier = useMemo(
    () => getRiskTier(userRole, viewMode),
    [userRole, viewMode]
  );

  const riskBarConfig = useMemo(
    () => getRiskBarConfig(riskTier, viewMode),
    [riskTier, viewMode]
  );

  // Tab change handler
  const handleTabChange = useCallback((mode: ViewMode) => {
    setViewMode(mode);
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  // Not authenticated (should be handled by layout, but safety check)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Risk Bar - Fixed under header */}
      <RiskBar
        tier={riskTier}
        label={riskBarConfig.label}
        tooltip={riskBarConfig.tooltip}
      />

      {/* Page Header */}
      <header className="border-b border-slate-200 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-8 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  People Hub
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  {hasAdminAccess
                    ? 'Directory and management for residents and faculty'
                    : 'Residents and faculty directory'}
                </p>
              </div>
            </div>

            {/* View Mode Tabs - Only show if user has admin access */}
            {hasAdminAccess && (
              <div className="flex gap-2" role="tablist" aria-label="View mode">
                <button
                  role="tab"
                  aria-selected={viewMode === 'directory'}
                  aria-controls="directory-panel"
                  onClick={() => handleTabChange('directory')}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                    dark:focus:ring-offset-slate-900
                    ${
                      viewMode === 'directory'
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                    }
                  `}
                >
                  Directory
                </button>
                <button
                  role="tab"
                  aria-selected={viewMode === 'admin'}
                  aria-controls="admin-panel"
                  onClick={() => handleTabChange('admin')}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                    dark:focus:ring-offset-slate-900
                    ${
                      viewMode === 'admin'
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                    }
                  `}
                >
                  Manage
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {viewMode === 'directory' ? (
          <div
            id="directory-panel"
            role="tabpanel"
            aria-labelledby="directory-tab"
          >
            <PeopleDirectory />
          </div>
        ) : (
          <div
            id="admin-panel"
            role="tabpanel"
            aria-labelledby="admin-tab"
          >
            <PeopleAdminPanel
              canBulkDelete={hasBulkDeleteAccess}
              riskTier={riskTier}
            />
          </div>
        )}
      </main>
    </div>
  );
}
