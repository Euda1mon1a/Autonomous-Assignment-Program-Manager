'use client';

/**
 * Absences Hub Page
 *
 * Consolidated absence management interface combining:
 * - My Absences: Self-service absence view (Tier 0+)
 * - Directory: View all absences (Tier 0+)
 * - Approvals/Admin: Approve requests, view sick reasons (Tier 1+)
 *
 * Permission Tiers:
 * - Tier 0 (Green): Read-only, self-service actions (all users)
 * - Tier 1 (Amber): Approve operations, sensitive data (coordinator, admin)
 * - Tier 2 (Red): Admin forced changes
 */

import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Calendar, User, Shield, Stethoscope } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { AllAbsencesTab } from '@/features/absences/components/AllAbsencesTab';
import { MyAbsencesTab } from '@/features/absences/components/MyAbsencesTab';
import { ApprovalsTab } from '@/features/absences/components/ApprovalsTab';

type AbsencesTab = 'my-absences' | 'directory' | 'approvals';

interface TabConfig {
  id: AbsencesTab;
  label: string;
  icon: typeof Calendar;
  description: string;
  requiredTier: RiskTier;
}

const TABS: TabConfig[] = [
  {
    id: 'my-absences',
    label: 'My Absences',
    icon: User,
    description: 'View and request your own absences',
    requiredTier: 0,
  },
  {
    id: 'directory',
    label: 'All Absences',
    icon: Calendar,
    description: 'View the program-wide absence calendar',
    requiredTier: 0,
  },
  {
    id: 'approvals',
    label: 'Approvals & Admin',
    icon: Shield,
    description: 'Manage absence requests and view sensitive details',
    requiredTier: 1,
  },
];

const VALID_ABSENCE_TABS: AbsencesTab[] = ['my-absences', 'directory', 'approvals'];

export default function AbsencesHubPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();

  const initialTabParam = searchParams.get('tab') as AbsencesTab;
  const initialTab = VALID_ABSENCE_TABS.includes(initialTabParam) ? initialTabParam : 'directory';

  const [activeTab, setActiveTab] = useState<AbsencesTab>(initialTab);

  // Sync tab state when URL search params change
  useEffect(() => {
    const tabParam = searchParams.get('tab') as AbsencesTab;
    if (tabParam && VALID_ABSENCE_TABS.includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  const availableTabs = useMemo(() => {
    return TABS.filter((tab) => tab.requiredTier <= userTier);
  }, [userTier]);

  const currentRiskTier: RiskTier = useMemo(() => {
    if (activeTab === 'my-absences' || activeTab === 'directory') return 0;
    if (activeTab === 'approvals') return userTier >= 2 ? 2 : 1;
    return 0;
  }, [activeTab, userTier]);

  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'View Mode & Self-Service',
          tooltip: 'You can view program absences and manage your own requests.',
        };
      case 1:
        return {
          label: 'Program Operations',
          tooltip: 'You can approve/deny requests and view sensitive leave details.',
        };
      case 2:
        return {
          label: 'System Admin',
          tooltip: 'You have full administrative access to all absence records.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  useEffect(() => {
    const currentTabConfig = TABS.find((t) => t.id === activeTab);
    if (currentTabConfig && currentTabConfig.requiredTier > userTier) {
      setActiveTab('directory');
    }
  }, [activeTab, userTier]);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <RiskBar
          tier={currentRiskTier}
          label={riskBarConfig.label}
          tooltip={riskBarConfig.tooltip}
        />

        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
                <Stethoscope className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Absences Hub</h1>
                <p className="text-sm text-gray-600">
                  Manage vacation, sick leave, TDY, and other schedule absences
                </p>
              </div>
            </div>

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
                            ? 'border-indigo-500 text-indigo-600'
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

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {activeTab === 'directory' && (
            <div id="tabpanel-directory" role="tabpanel" aria-labelledby="tab-directory">
              <AllAbsencesTab />
            </div>
          )}

          {activeTab === 'my-absences' && (
            <div id="tabpanel-my-absences" role="tabpanel" aria-labelledby="tab-my-absences">
              <MyAbsencesTab />
            </div>
          )}

          {activeTab === 'approvals' && userTier >= 1 && (
            <div id="tabpanel-approvals" role="tabpanel" aria-labelledby="tab-approvals">
              <ApprovalsTab />
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
