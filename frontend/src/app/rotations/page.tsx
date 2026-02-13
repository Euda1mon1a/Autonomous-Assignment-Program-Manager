'use client';

/**
 * Rotations Page
 *
 * Consolidated rotation management interface combining:
 * - Rotation Templates: View rotations and edit their 4-week activity patterns (Tier 0+)
 * - Faculty Activities: Manage faculty weekly activity patterns (Tier 1+)
 *
 * Permission Tiers:
 * - Tier 0 (Green): View templates, view faculty patterns (read-only)
 * - Tier 1 (Amber): Create/edit templates and faculty patterns
 * - Tier 2 (Red): Delete templates and advanced operations
 */

import { useState, useMemo, useEffect } from 'react';
import { Calendar, Users, Layers } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { RotationTemplatesTab } from './components/RotationTemplatesTab';
import { FacultyActivityTemplatesTab } from './components/FacultyActivityTemplatesTab';

// ============================================================================
// Types
// ============================================================================

type RotationsTab = 'templates' | 'faculty';

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
    id: 'templates',
    label: 'Rotation Templates',
    icon: Calendar,
    description: 'View and manage rotation activity templates',
    requiredTier: 0,
  },
  {
    id: 'faculty',
    label: 'Faculty Activities',
    icon: Users,
    description: 'Manage faculty weekly activity patterns',
    requiredTier: 1,
  },
];

// ============================================================================
// Component
// ============================================================================

export default function RotationsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<RotationsTab>('templates');

  // Determine user's permission tier from role
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  // Filter tabs based on user permissions
  const availableTabs = useMemo(() => {
    return TABS.filter((tab) => tab.requiredTier <= userTier);
  }, [userTier]);

  // Determine current risk tier based on active tab and user permissions
  const currentRiskTier: RiskTier = useMemo(() => {
    if (activeTab === 'templates') {
      return userTier;
    }
    if (activeTab === 'faculty') {
      return userTier >= 2 ? 2 : 1;
    }
    return 0;
  }, [activeTab, userTier]);

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'View Mode',
          tooltip: 'You can browse rotation templates. Contact an administrator to make changes.',
        };
      case 1:
        return {
          label: 'Edit Mode',
          tooltip: 'You can create and edit templates. Deletion requires admin access.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'You have full access to create, edit, and delete templates.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  // Reset to templates if user doesn't have access to current tab
  useEffect(() => {
    const currentTabConfig = TABS.find((t) => t.id === activeTab);
    if (currentTabConfig && currentTabConfig.requiredTier > userTier) {
      setActiveTab('templates');
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
              <div className="p-2 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg">
                <Layers className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Rotations</h1>
                <p className="text-sm text-gray-600">
                  Manage rotation templates and activity patterns
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
          {/* Rotation Templates Tab */}
          {activeTab === 'templates' && (
            <div
              id="tabpanel-templates"
              role="tabpanel"
              aria-labelledby="tab-templates"
            >
              <RotationTemplatesTab canEdit={canEdit} canDelete={canDelete} />
            </div>
          )}

          {/* Faculty Activities Tab */}
          {activeTab === 'faculty' && userTier >= 1 && (
            <div
              id="tabpanel-faculty"
              role="tabpanel"
              aria-labelledby="tab-faculty"
            >
              <FacultyActivityTemplatesTab canEdit={canEdit} canDelete={canDelete} />
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
