'use client';

/**
 * Rotations Hub Page
 *
 * Consolidated rotation management interface combining:
 * - Outpatient Rotations (Flexible Targets) - View/Edit distribution targets (Tier 0/1)
 * - Inpatient Rotations (Fixed Grids) - View/Edit the rigid 7x2 grid (Tier 0/1)
 *
 * Permission Tiers:
 * - Tier 0 (Green): View rotation setups
 * - Tier 1 (Amber): Create/edit rotations
 * - Tier 2 (Red): Delete rotations
 */

import { useState, useMemo, useEffect } from 'react';
import { Calendar, ClipboardList, Layers } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { InpatientGridTab } from '@/features/rotations/components/InpatientGridTab';
import { OutpatientTargetsTab } from '@/features/rotations/components/OutpatientTargetsTab';

// ============================================================================
// Types
// ============================================================================

type RotationsTab = 'outpatient' | 'inpatient';

interface TabConfig {
  id: RotationsTab;
  label: string;
  icon: typeof Calendar;
  description: string;
  requiredTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'outpatient',
    label: 'Outpatient (Targets)',
    icon: ClipboardList,
    description: 'Set flexible volume targets for outpatient rotations',
    requiredTier: 0,
  },
  {
    id: 'inpatient',
    label: 'Inpatient (Fixed Grid)',
    icon: Calendar,
    description: 'Lock activities into a rigid 7x2 weekly schedule',
    requiredTier: 0,
  },
];

// ============================================================================
// Component
// ============================================================================

export default function RotationsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<RotationsTab>('outpatient');

  // Determine user's permission tier from role
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  // Filter tabs based on user permissions
  const availableTabs = useMemo(() => {
    return TABS.filter((tab) => tab.requiredTier <= userTier);
  }, [userTier]);

  // Determine current risk tier based on user permissions (both tabs share tier)
  const currentRiskTier: RiskTier = useTier(userTier);

  function useTier(tier: RiskTier) {
      return useMemo(() => {
          return tier;
      }, [tier]);
  }

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'View Mode',
          tooltip: 'You can browse rotation definitions. Contact an administrator to make changes.',
        };
      case 1:
        return {
          label: 'Edit Mode',
          tooltip: 'You can create and edit rotation definitions. Deletion requires admin access.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'You have full access to create, edit, and delete rotation definitions.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  // Reset to outpatient if user doesn't have access to current tab
  useEffect(() => {
    const currentTabConfig = TABS.find((t) => t.id === activeTab);
    if (currentTabConfig && currentTabConfig.requiredTier > userTier) {
      setActiveTab('outpatient');
    }
  }, [activeTab, userTier]);

  // Permission flags for tab components
  const canEdit = userTier >= 1;
  const canDelete = userTier >= 2;

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
              <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg">
                <Layers className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Rotations Hub</h1>
                <p className="text-sm text-gray-600">
                  Define 4-week resident rotation blueprints
                </p>
              </div>
            </div>

            {/* Tabs */}
            {availableTabs.length > 1 && (
              <nav className="mt-4 -mb-px flex space-x-4 sm:space-x-8" aria-label="Tabs">
                {availableTabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`
                        group flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors
                        ${
                          isActive
                            ? 'border-blue-500 text-blue-600'
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
          {/* Outpatient Tab */}
          {activeTab === 'outpatient' && (
            <div
              id="tabpanel-outpatient"
              role="tabpanel"
              aria-labelledby="tab-outpatient"
            >
              <OutpatientTargetsTab />
            </div>
          )}

          {/* Inpatient Tab */}
          {activeTab === 'inpatient' && (
            <div
              id="tabpanel-inpatient"
              role="tabpanel"
              aria-labelledby="tab-inpatient"
            >
              <InpatientGridTab canEdit={canEdit} canDelete={canDelete} />
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
