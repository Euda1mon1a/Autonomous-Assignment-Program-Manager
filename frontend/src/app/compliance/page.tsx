'use client';

/**
 * Compliance Hub Page
 *
 * Unified compliance dashboard combining:
 * - ACGME Compliance: Work hour rules, supervision ratios, rest periods (Tier 0)
 * - Away-From-Program Compliance: 28-day annual absence limit tracking (Tier 0)
 * - Audit Trail: Detailed system logs and security events (Tier 1/2)
 *
 * Permission Tiers:
 * - Tier 0 (Green): View compliance summaries
 * - Tier 1 (Amber): View detailed audit logs
 */

import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Shield, Plane, FileText, CheckSquare } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { ACGMEComplianceTab } from '@/features/compliance/components/ACGMEComplianceTab';
import { AwayFromProgramTab } from '@/features/compliance/components/AwayFromProgramTab';
import { AuditTab } from '@/features/compliance/components/AuditTab';

// ============================================================================
// Types
// ============================================================================

type ComplianceTab = 'acgme' | 'away-from-program' | 'audit';

interface TabConfig {
  id: ComplianceTab;
  label: string;
  icon: typeof Shield;
  description: string;
  requiredTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'acgme',
    label: 'ACGME Compliance',
    icon: Shield,
    description: 'Monitor work hour and supervision compliance',
    requiredTier: 0,
  },
  {
    id: 'away-from-program',
    label: 'Away-From-Program',
    icon: Plane,
    description: 'Track the 28-day annual absence limit',
    requiredTier: 0,
  },
  {
    id: 'audit',
    label: 'Audit Trail',
    icon: FileText,
    description: 'View detailed system logs and security events',
    requiredTier: 1,
  },
];

// ============================================================================
// Component
// ============================================================================

export default function ComplianceHubPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();

  // Parse initial tab from query params, fallback to 'acgme'
  const initialTabParam = searchParams.get('tab') as ComplianceTab;
  const initialTab = ['acgme', 'away-from-program', 'audit'].includes(initialTabParam)
    ? initialTabParam
    : 'acgme';

  const [activeTab, setActiveTab] = useState<ComplianceTab>(initialTab);

  // Sync tab state when URL search params change (e.g., command palette deep links)
  useEffect(() => {
    const tabParam = searchParams.get('tab') as ComplianceTab;
    if (tabParam && ['acgme', 'away-from-program', 'audit'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  // Determine user's permission tier from role
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  // Filter tabs based on user permissions
  const availableTabs = useMemo(() => {
    return TABS.filter((tab) => tab.requiredTier <= userTier);
  }, [userTier]);

  // Determine current risk tier based on user permissions and active tab
  const currentRiskTier: RiskTier = useMemo(() => {
    if (activeTab === 'audit') {
      return userTier;
    }
    return 0; // ACGME and Away-From-Program are read-only
  }, [activeTab, userTier]);

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'View Mode',
          tooltip: 'You are viewing compliance summaries. No modifications can be made from this page.',
        };
      case 1:
        return {
          label: 'Audit Access',
          tooltip: 'You have access to detailed system logs and security events.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'You have full access to compliance and audit data.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  // Reset to acgme if user doesn't have access to current tab
  // Only enforce after auth has loaded (user is non-null) to avoid
  // resetting deep-linked tabs during initial auth hydration
  useEffect(() => {
    if (!user) return;
    const currentTabConfig = TABS.find((t) => t.id === activeTab);
    if (currentTabConfig && currentTabConfig.requiredTier > userTier) {
      setActiveTab('acgme');
    }
  }, [activeTab, userTier, user]);

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
              <div className="p-2 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg">
                <CheckSquare className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Compliance Hub</h1>
                <p className="text-sm text-gray-600">
                  Monitor ACGME compliance, tracking, and system audit logs
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
                            ? 'border-emerald-500 text-emerald-600'
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
          {activeTab === 'acgme' && (
            <div id="tabpanel-acgme" role="tabpanel" aria-labelledby="tab-acgme">
              <ACGMEComplianceTab />
            </div>
          )}

          {activeTab === 'away-from-program' && (
            <div id="tabpanel-away-from-program" role="tabpanel" aria-labelledby="tab-away-from-program">
              <AwayFromProgramTab />
            </div>
          )}

          {activeTab === 'audit' && userTier >= 1 && (
            <div id="tabpanel-audit" role="tabpanel" aria-labelledby="tab-audit">
              <AuditTab />
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
