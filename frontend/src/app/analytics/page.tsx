'use client';

/**
 * Analytics Hub Page
 *
 * Unified analytics dashboard combining:
 * - Fairness Metrics: Workload distribution, Gini coefficients, Shapley values (Tier 0)
 * - Game Theory: Swap market liquidity, auction dynamics, Nash equilibrium (Tier 0)
 *
 * Permission Tiers:
 * - Tier 0 (Green): View all analytics for transparency
 * - Tier 1 (Amber): Edit baseline constraints / parameters
 */

import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { LineChart, BarChart2, Scale } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { FairnessTab, GameTheoryTab } from '@/features/analytics';

// ============================================================================
// Types
// ============================================================================

type AnalyticsTab = 'fairness' | 'game-theory';

interface TabConfig {
  id: AnalyticsTab;
  label: string;
  icon: typeof LineChart;
  description: string;
  requiredTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'fairness',
    label: 'Workload Fairness',
    icon: Scale,
    description: 'Monitor schedule equity across the program',
    requiredTier: 0,
  },
  {
    id: 'game-theory',
    label: 'Game Theory & Markets',
    icon: BarChart2,
    description: 'Analyze swap market liquidity and auction dynamics',
    requiredTier: 0,
  },
];

// ============================================================================
// Component
// ============================================================================

export default function AnalyticsHubPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();

  const initialTabParam = searchParams.get('tab') as AnalyticsTab;
  const initialTab = ['fairness', 'game-theory'].includes(initialTabParam)
    ? initialTabParam
    : 'fairness';

  const [activeTab, setActiveTab] = useState<AnalyticsTab>(initialTab);

  // Sync tab state when URL search params change
  useEffect(() => {
    const tabParam = searchParams.get('tab') as AnalyticsTab;
    if (tabParam && ['fairness', 'game-theory'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  // Determine user's permission tier from role
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  // Filter tabs based on user permissions
  const availableTabs = useMemo(() => {
    return TABS.filter((tab) => tab.requiredTier <= userTier);
  }, [userTier]);

  // Determine current risk tier
  const currentRiskTier: RiskTier = useMemo(() => {
    // Note: If we add parameter editing in the future, this would check activeTab
    return userTier; // Both current tabs are read-only for transparency
  }, [activeTab, userTier]);

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'Transparency Mode',
          tooltip: 'Analytics data is open to all users to ensure program fairness and trust.',
        };
      case 1:
        return {
          label: 'Operations Mode',
          tooltip: 'You can adjust the baseline constraints used to calculate fairness.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'Full access to analytics configuration.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  // Reset to default if user doesn't have access to current tab
  useEffect(() => {
    const currentTabConfig = TABS.find((t) => t.id === activeTab);
    if (currentTabConfig && currentTabConfig.requiredTier > userTier) {
      setActiveTab('fairness');
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
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-lg">
                <LineChart className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Analytics Hub</h1>
                <p className="text-sm text-gray-600">
                  Data-driven insights into schedule equity and market dynamics
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
                            ? 'border-indigo-600 text-indigo-600'
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
          {activeTab === 'fairness' && (
            <div id="tabpanel-fairness" role="tabpanel" aria-labelledby="tab-fairness">
              <FairnessTab />
            </div>
          )}

          {activeTab === 'game-theory' && (
            <div id="tabpanel-game-theory" role="tabpanel" aria-labelledby="tab-game-theory">
              <GameTheoryTab />
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
