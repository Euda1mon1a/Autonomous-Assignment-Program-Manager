'use client';

/**
 * CallHubClient Component
 *
 * Client component for the unified Call Hub.
 * Provides tabbed navigation between:
 * - Roster tab: Read-only call roster (Tier 0)
 * - Admin tab: Call management controls (Tier 1/2 only)
 *
 * Uses RiskBar to indicate current permission level.
 * WCAG 2.1 AA compliant with proper ARIA attributes.
 */

import { useState, useMemo } from 'react';
import { Phone, Calendar, Settings, AlertTriangle } from 'lucide-react';
import { RiskBar, type RiskTier } from '@/components/ui/RiskBar';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { CallRosterTab } from './tabs/CallRosterTab';
import { CallAdminTab } from './tabs/CallAdminTab';

// ============================================================================
// Types
// ============================================================================

type TabId = 'roster' | 'admin';

interface TabConfig {
  id: TabId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  minTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'roster',
    label: 'Call Roster',
    icon: Calendar,
    description: 'View who is on call',
    minTier: 0,
  },
  {
    id: 'admin',
    label: 'Admin Panel',
    icon: Settings,
    description: 'Manage call assignments',
    minTier: 1,
  },
];

/**
 * Maps user roles to risk tiers.
 * This determines what level of access the user has.
 */
function getRiskTierFromRole(role: string | undefined): RiskTier {
  switch (role) {
    case 'admin':
      return 2; // High impact
    case 'coordinator':
      return 1; // Scoped changes
    case 'faculty':
    case 'resident':
    default:
      return 0; // Read-only
  }
}

/**
 * Gets the risk bar label for a given tier.
 */
function getRiskLabel(tier: RiskTier, activeTab: TabId): string {
  if (activeTab === 'roster') {
    return 'Read-only';
  }
  switch (tier) {
    case 0:
      return 'Read-only';
    case 1:
      return 'Scoped Changes';
    case 2:
      return 'High Impact';
    default:
      return 'Read-only';
  }
}

/**
 * Gets the tooltip for the risk bar.
 */
function getRiskTooltip(tier: RiskTier, activeTab: TabId): string {
  if (activeTab === 'roster') {
    return 'This view shows the call roster. No changes can be made here.';
  }
  switch (tier) {
    case 0:
      return 'You can view call data but cannot make changes.';
    case 1:
      return 'You can make reversible changes to call assignments within your scope.';
    case 2:
      return 'You have access to bulk operations and system-wide changes. Proceed with caution.';
    default:
      return 'Read-only access';
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function CallHubClient() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>('roster');

  // Determine user's tier based on role
  const userTier = useMemo(() => getRiskTierFromRole(user?.role), [user?.role]);

  // Filter tabs based on user's tier
  const availableTabs = useMemo(
    () => TABS.filter((tab) => userTier >= tab.minTier),
    [userTier]
  );

  // Determine effective tier for display (roster is always green)
  const effectiveTier = activeTab === 'roster' ? 0 : userTier;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        {/* Risk Bar */}
        <RiskBar
          tier={effectiveTier}
          label={getRiskLabel(effectiveTier, activeTab)}
          tooltip={getRiskTooltip(effectiveTier, activeTab)}
        />

        {/* Header */}
        <header className="bg-white border-b border-slate-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl shadow-lg">
                <Phone className="w-8 h-8 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Call Hub</h1>
                <p className="text-slate-600">
                  View on-call roster and manage call assignments
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Tab Navigation */}
        <nav
          className="bg-white border-b border-slate-200"
          aria-label="Call Hub navigation"
        >
          <div className="max-w-7xl mx-auto px-4">
            <div
              className="flex gap-1"
              role="tablist"
              aria-label="Call Hub sections"
            >
              {availableTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;

                return (
                  <button
                    key={tab.id}
                    role="tab"
                    id={`tab-${tab.id}`}
                    aria-selected={isActive}
                    aria-controls={`tabpanel-${tab.id}`}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex items-center gap-2 px-4 py-3 text-sm font-medium
                      border-b-2 transition-colors focus:outline-none
                      focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
                      ${
                        isActive
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" aria-hidden="true" />
                    {tab.label}
                    {tab.id === 'admin' && userTier >= 2 && (
                      <span
                        className="ml-1 px-1.5 py-0.5 text-xs bg-red-100 text-red-700 rounded"
                        title="High impact actions available"
                      >
                        <AlertTriangle
                          className="w-3 h-3 inline-block"
                          aria-hidden="true"
                        />
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </nav>

        {/* Tab Content */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          {/* Roster Tab */}
          <div
            role="tabpanel"
            id="tabpanel-roster"
            aria-labelledby="tab-roster"
            hidden={activeTab !== 'roster'}
          >
            {activeTab === 'roster' && <CallRosterTab />}
          </div>

          {/* Admin Tab */}
          {userTier >= 1 && (
            <div
              role="tabpanel"
              id="tabpanel-admin"
              aria-labelledby="tab-admin"
              hidden={activeTab !== 'admin'}
            >
              {activeTab === 'admin' && <CallAdminTab userTier={userTier} />}
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
