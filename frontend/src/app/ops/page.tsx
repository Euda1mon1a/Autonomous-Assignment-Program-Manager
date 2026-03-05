'use client';

/**
 * Ops Hub Page
 *
 * Tactical command center for day-of operations.
 *
 * Permission Tiers:
 * - Tier 0 (Green): View manifest, conflicts, demand
 * - Tier 1 (Amber): Resolve conflicts, proxy coverage, manual overrides
 */

import { useState, useMemo, useEffect } from 'react';
import { CalendarDays, AlertTriangle, ShieldAlert, BarChart3, Activity } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { DailyManifest } from '@/features/daily-manifest';
import { ProxyCoverageDashboard } from '@/features/proxy-coverage';
import { ConflictDashboard } from '@/features/conflicts';
import { HeatmapTab } from '@/features/ops';

// ============================================================================
// Types
// ============================================================================

type OpsTab = 'manifest' | 'coverage' | 'conflicts' | 'demand';

interface TabConfig {
  id: OpsTab;
  label: string;
  icon: typeof CalendarDays;
  description: string;
  requiredTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'manifest',
    label: 'Daily Manifest',
    icon: CalendarDays,
    description: 'View the source of truth for who is where today',
    requiredTier: 0,
  },
  {
    id: 'coverage',
    label: 'Proxy Coverage',
    icon: ShieldAlert,
    description: 'Find coverage for sudden absences',
    requiredTier: 1,
  },
  {
    id: 'conflicts',
    label: 'Conflicts',
    icon: AlertTriangle,
    description: 'Detect and resolve ACGME compliance errors',
    requiredTier: 0,
  },
  {
    id: 'demand',
    label: 'Demand Heatmap',
    icon: BarChart3,
    description: 'Visualize where the program is stretched thin',
    requiredTier: 0,
  },
];

// ============================================================================
// Component
// ============================================================================

export default function OpsHubPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<OpsTab>('manifest');

  // Determine user's permission tier from role
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  // Filter tabs based on user permissions
  const availableTabs = useMemo(() => {
    return TABS.filter((tab) => tab.requiredTier <= userTier);
  }, [userTier]);

  // Determine current risk tier based on user permissions
  const currentRiskTier: RiskTier = useMemo(() => {
    if (activeTab === 'coverage') {
      return userTier;
    }
    return 0; // Other tabs are primarily read-only visualization and conflict checking
  }, [activeTab, userTier]);

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'View Mode',
          tooltip: 'You are viewing operational data. Contact a coordinator to make changes.',
        };
      case 1:
        return {
          label: 'Operations Mode',
          tooltip: 'You can resolve conflicts and manage proxy coverage.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'You have full operations access.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  // Reset to manifest if user doesn't have access to current tab
  useEffect(() => {
    const currentTabConfig = TABS.find((t) => t.id === activeTab);
    if (currentTabConfig && currentTabConfig.requiredTier > userTier) {
      setActiveTab('manifest');
    }
  }, [activeTab, userTier]);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Risk Bar */}
        <RiskBar
          tier={currentRiskTier}
          label={riskBarConfig.label}
          tooltip={riskBarConfig.tooltip}
        />

        {/* Header */}
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg">
                <Activity className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Operations Hub</h1>
                <p className="text-sm text-gray-600">
                  Tactical command center for managing day-of scheduling reality
                </p>
              </div>
            </div>

            {/* Tabs */}
            {availableTabs.length > 1 && (
              <nav className="mt-4 -mb-px flex space-x-4 sm:space-x-8 overflow-x-auto" aria-label="Tabs">
                {availableTabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`
                        group flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap
                        ${
                          isActive
                            ? 'border-red-500 text-red-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }
                      `}
                      role="tab"
                      aria-selected={isActive}
                      aria-controls={`tabpanel-${tab.id}`}
                      title={tab.description}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                      <span>{tab.label}</span>
                      {tab.requiredTier >= 1 && (
                        <span
                          className={`
                            ml-1 px-1.5 py-0.5 text-xs rounded
                            ${tab.requiredTier === 2 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}
                          `}
                          aria-label={tab.requiredTier === 2 ? 'Admin only' : 'Elevated permissions'}
                        >
                          {tab.requiredTier === 2 ? 'Admin' : 'Coord'}
                        </span>
                      )}
                    </button>
                  );
                })}
              </nav>
            )}
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {activeTab === 'manifest' && (
            <div id="tabpanel-manifest" role="tabpanel" aria-labelledby="tab-manifest">
              <DailyManifest />
            </div>
          )}

          {activeTab === 'coverage' && userTier >= 1 && (
            <div id="tabpanel-coverage" role="tabpanel" aria-labelledby="tab-coverage">
              <ProxyCoverageDashboard />
            </div>
          )}

          {activeTab === 'conflicts' && (
            <div id="tabpanel-conflicts" role="tabpanel" aria-labelledby="tab-conflicts">
              <ConflictDashboard />
            </div>
          )}

          {activeTab === 'demand' && (
            <div id="tabpanel-demand" role="tabpanel" aria-labelledby="tab-demand">
              <HeatmapTab />
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
