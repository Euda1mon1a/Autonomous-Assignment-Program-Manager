'use client';

/**
 * Swaps Hub Page
 *
 * Consolidated swap management interface combining:
 * - Marketplace: Browse and manage swap requests (Tier 0+)
 * - Admin Actions: Force swaps and direct assignment edits (Tier 1/2)
 *
 * Permission Tiers:
 * - Tier 0 (Green): Read-only, self-service actions (all users)
 * - Tier 1 (Amber): Execute Swap operations (coordinator, admin)
 * - Tier 2 (Red): Direct Assignment Edit (admin only)
 *
 * @see docs/reviews/2026-01-11-frontend-consolidation-map.md
 */

import { useState, useMemo } from 'react';
import {
  ArrowLeftRight,
  ShoppingCart,
  Shield,
  Pencil,
} from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier } from '@/components/ui/RiskBar';
import { useRole } from '@/hooks/useAuth';
import { SwapMarketplace } from '@/features/swap-marketplace';
import { AdminSwapPanel } from './_components/AdminSwapPanel';

// ============================================================================
// Types
// ============================================================================

type SwapsHubTab = 'marketplace' | 'admin';

interface TabConfig {
  id: SwapsHubTab;
  label: string;
  icon: typeof ShoppingCart;
  description: string;
  requiredTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'marketplace',
    label: 'Marketplace',
    icon: ShoppingCart,
    description: 'Browse and manage swap requests',
    requiredTier: 0,
  },
  {
    id: 'admin',
    label: 'Admin Actions',
    icon: Shield,
    description: 'Force swaps and direct assignment edits',
    requiredTier: 1,
  },
];

// ============================================================================
// Component
// ============================================================================

export default function SwapsHubPage() {
  const { isAdmin, isCoordinator, isLoading: roleLoading } = useRole();
  const [activeTab, setActiveTab] = useState<SwapsHubTab>('marketplace');

  // Determine user's permission tier
  const userTier: RiskTier = useMemo(() => {
    if (isAdmin) return 2;
    if (isCoordinator) return 1;
    return 0;
  }, [isAdmin, isCoordinator]);

  // Filter tabs based on user permissions
  const availableTabs = useMemo(() => {
    return TABS.filter((tab) => tab.requiredTier <= userTier);
  }, [userTier]);

  // Determine current risk tier based on active tab and user permissions
  const currentRiskTier: RiskTier = useMemo(() => {
    if (activeTab === 'marketplace') {
      // Marketplace is always Tier 0 (read-only / self-service)
      return 0;
    }
    if (activeTab === 'admin') {
      // Admin tab: Tier 1 for coordinators, Tier 2 for admins
      return userTier >= 2 ? 2 : 1;
    }
    return 0;
  }, [activeTab, userTier]);

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'Self-Service',
          tooltip: 'You can browse swaps and manage your own requests. Changes only affect your schedule.',
        };
      case 1:
        return {
          label: 'Scoped Changes',
          tooltip: 'You can execute swaps between faculty members. Changes are reversible within 24 hours.',
        };
      case 2:
        return {
          label: 'High Impact',
          tooltip: 'You have access to direct assignment edits. These changes may not be reversible. Proceed with caution.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  // Reset to marketplace if user doesn't have access to current tab
  useMemo(() => {
    const currentTabConfig = TABS.find((t) => t.id === activeTab);
    if (currentTabConfig && currentTabConfig.requiredTier > userTier) {
      setActiveTab('marketplace');
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
              <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg">
                <ArrowLeftRight className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Swaps Hub</h1>
                <p className="text-sm text-gray-600">
                  Browse swap opportunities and manage schedule changes
                </p>
              </div>
            </div>

            {/* Tabs */}
            {!roleLoading && availableTabs.length > 1 && (
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
        <main className="max-w-7xl mx-auto">
          {/* Marketplace Tab */}
          {activeTab === 'marketplace' && (
            <div
              id="tabpanel-marketplace"
              role="tabpanel"
              aria-labelledby="tab-marketplace"
            >
              <SwapMarketplace />
            </div>
          )}

          {/* Admin Actions Tab */}
          {activeTab === 'admin' && userTier >= 1 && (
            <div
              id="tabpanel-admin"
              role="tabpanel"
              aria-labelledby="tab-admin"
              className="p-4 sm:p-6 lg:p-8"
            >
              <AdminSwapPanel userTier={userTier} />
            </div>
          )}
        </main>

        {/* Help Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              About the Swaps Hub
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <ShoppingCart className="w-5 h-5 text-blue-600" aria-hidden="true" />
                  <h3 className="font-medium text-gray-900">Marketplace</h3>
                </div>
                <p className="text-sm text-gray-600">
                  Browse available swap requests from faculty. Create your own requests
                  or accept offers from others to exchange schedule assignments.
                </p>
              </div>
              {userTier >= 1 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <ArrowLeftRight className="w-5 h-5 text-amber-600" aria-hidden="true" />
                    <h3 className="font-medium text-gray-900">Execute Swap</h3>
                  </div>
                  <p className="text-sm text-gray-600">
                    Coordinators can execute swaps between faculty members. All swaps
                    are validated against ACGME compliance rules before execution.
                  </p>
                </div>
              )}
              {userTier >= 2 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Pencil className="w-5 h-5 text-red-600" aria-hidden="true" />
                    <h3 className="font-medium text-gray-900">Direct Edit</h3>
                  </div>
                  <p className="text-sm text-gray-600">
                    Admins can directly modify individual assignments. Use with caution
                    as these changes may not be reversible through the standard workflow.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </ProtectedRoute>
  );
}
