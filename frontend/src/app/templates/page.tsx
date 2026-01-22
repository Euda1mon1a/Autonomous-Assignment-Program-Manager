'use client';

/**
 * Templates Hub Page
 *
 * Unified interface for viewing and managing:
 * - Rotation templates (scheduling patterns for rotations)
 * - Faculty weekly templates (default weekly schedules)
 *
 * Permission Tiers:
 * - Tier 0 (Green): View rotation templates, view own schedule (residents, clinical staff)
 * - Tier 0.5 (Green): Same as Tier 0 but for faculty
 * - Tier 1 (Amber): Edit rotation templates, edit any faculty template (coordinator, chief)
 * - Tier 2 (Red): Bulk operations, system-wide changes (admin only)
 *
 * @see docs/plans/keen-tumbling-bentley.md
 */

import { useState, useMemo } from 'react';
import {
  LayoutTemplate,
  Calendar,
  User,
  Users,
  Settings2,
} from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier } from '@/components/ui/RiskBar';
import { useRole } from '@/hooks/useAuth';
import { RotationsPanel } from './_components/RotationsPanel';
import { MySchedulePanel } from './_components/MySchedulePanel';
import { FacultyPanel } from './_components/FacultyPanel';
import { MatrixPanel } from './_components/MatrixPanel';

// ============================================================================
// Types
// ============================================================================

type TemplatesHubTab = 'rotations' | 'my-schedule' | 'faculty' | 'matrix' | 'bulk';

interface TabConfig {
  id: TemplatesHubTab;
  label: string;
  icon: typeof LayoutTemplate;
  description: string;
  /** Minimum tier required to SEE this tab */
  requiredTier: RiskTier;
  /** Tier at which this tab becomes editable (vs view-only) */
  editTier?: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'rotations',
    label: 'Rotations',
    icon: LayoutTemplate,
    description: 'View rotation templates and scheduling patterns',
    requiredTier: 0,
    editTier: 1, // Tier 0 can view, Tier 1+ can edit
  },
  {
    id: 'my-schedule',
    label: 'My Schedule',
    icon: User,
    description: 'View your weekly activity template',
    requiredTier: 0,
    // No editTier - always read-only, must request coordinator for changes
  },
  {
    id: 'faculty',
    label: 'Faculty Templates',
    icon: Calendar,
    description: 'Edit faculty weekly activity templates',
    requiredTier: 1,
    editTier: 1,
  },
  {
    id: 'matrix',
    label: 'Matrix View',
    icon: Users,
    description: 'Overview of all faculty schedules',
    requiredTier: 1,
    editTier: 1,
  },
  {
    id: 'bulk',
    label: 'Bulk Operations',
    icon: Settings2,
    description: 'Batch template operations and system tools',
    requiredTier: 2,
    editTier: 2,
  },
];

// ============================================================================
// Component
// ============================================================================

export default function TemplatesHubPage() {
  const { isAdmin, isCoordinator, isLoading: roleLoading } = useRole();
  const [activeTab, setActiveTab] = useState<TemplatesHubTab>('rotations');

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

  // Get current tab config
  const currentTabConfig = useMemo(() => {
    return TABS.find((t) => t.id === activeTab);
  }, [activeTab]);

  // Determine if current tab is in edit mode (user has edit permissions)
  const canEdit = useMemo(() => {
    if (!currentTabConfig?.editTier) return false;
    return userTier >= currentTabConfig.editTier;
  }, [currentTabConfig, userTier]);

  // Determine current risk tier based on active tab and edit capability
  const currentRiskTier: RiskTier = useMemo(() => {
    // If user can edit on this tab, show their edit tier
    if (canEdit && currentTabConfig?.editTier !== undefined) {
      return Math.min(userTier, 2) as RiskTier;
    }
    // Otherwise show green (read-only)
    return 0;
  }, [canEdit, currentTabConfig, userTier]);

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    if (!canEdit) {
      return {
        label: 'View Only',
        tooltip: 'You can view this information but cannot make changes. Contact a coordinator for edits.',
      };
    }

    switch (currentRiskTier) {
      case 1:
        return {
          label: 'Edit Mode',
          tooltip: 'You can create and modify templates. Changes affect scheduling patterns.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'You have full access including bulk operations. Proceed with caution.',
        };
      default:
        return {
          label: 'View Only',
          tooltip: 'You can view this information but cannot make changes.',
        };
    }
  }, [canEdit, currentRiskTier]);

  // Reset to rotations if user doesn't have access to current tab
  useMemo(() => {
    const currentTab = TABS.find((t) => t.id === activeTab);
    if (currentTab && currentTab.requiredTier > userTier) {
      setActiveTab('rotations');
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
              <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                <LayoutTemplate className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Templates Hub</h1>
                <p className="text-sm text-gray-600">
                  Manage rotation patterns and faculty schedules
                </p>
              </div>
            </div>

            {/* Tabs */}
            {!roleLoading && (
              <nav className="mt-4 -mb-px flex flex-wrap gap-2 sm:gap-4" aria-label="Tabs">
                {availableTabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  const isEditableTab = tab.editTier !== undefined && userTier >= tab.editTier;

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`
                        group flex items-center gap-2 py-3 px-3 border-b-2 font-medium text-sm transition-colors
                        ${
                          isActive
                            ? 'border-violet-500 text-violet-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }
                      `}
                      role="tab"
                      aria-selected={isActive}
                      aria-controls={`tabpanel-${tab.id}`}
                      title={tab.description}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                      <span className="hidden sm:inline">{tab.label}</span>
                      {/* Tier badge */}
                      {tab.requiredTier >= 1 && (
                        <span
                          className={`
                            ml-1 px-1.5 py-0.5 text-xs rounded hidden sm:inline
                            ${tab.requiredTier === 2 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}
                          `}
                          aria-label={tab.requiredTier === 2 ? 'Admin only' : 'Coordinator'}
                        >
                          {tab.requiredTier === 2 ? 'Admin' : 'Coord'}
                        </span>
                      )}
                      {/* View-only indicator for tabs user can see but not edit */}
                      {tab.editTier !== undefined && !isEditableTab && (
                        <span className="ml-1 text-xs text-gray-400 hidden sm:inline">(view)</span>
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
          {/* Rotations Tab */}
          {activeTab === 'rotations' && (
            <div
              id="tabpanel-rotations"
              role="tabpanel"
              aria-labelledby="tab-rotations"
              className="p-4 sm:p-6 lg:p-8"
            >
              <RotationsPanel canEdit={canEdit} />
            </div>
          )}

          {/* My Schedule Tab */}
          {activeTab === 'my-schedule' && (
            <div
              id="tabpanel-my-schedule"
              role="tabpanel"
              aria-labelledby="tab-my-schedule"
              className="p-4 sm:p-6 lg:p-8"
            >
              <MySchedulePanel />
            </div>
          )}

          {/* Faculty Templates Tab */}
          {activeTab === 'faculty' && userTier >= 1 && (
            <div
              id="tabpanel-faculty"
              role="tabpanel"
              aria-labelledby="tab-faculty"
              className="p-4 sm:p-6 lg:p-8"
            >
              <FacultyPanel />
            </div>
          )}

          {/* Matrix View Tab */}
          {activeTab === 'matrix' && userTier >= 1 && (
            <div
              id="tabpanel-matrix"
              role="tabpanel"
              aria-labelledby="tab-matrix"
              className="p-4 sm:p-6 lg:p-8"
            >
              <MatrixPanel canEdit={canEdit} />
            </div>
          )}

          {/* Bulk Operations Tab */}
          {activeTab === 'bulk' && userTier >= 2 && (
            <div
              id="tabpanel-bulk"
              role="tabpanel"
              aria-labelledby="tab-bulk"
              className="p-4 sm:p-6 lg:p-8"
            >
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                <Settings2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h2 className="text-lg font-medium text-gray-900 mb-2">Bulk Operations</h2>
                <p className="text-gray-500">
                  Batch template operations coming in Phase 2.
                </p>
              </div>
            </div>
          )}
        </main>

        {/* Help Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              About the Templates Hub
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <LayoutTemplate className="w-5 h-5 text-violet-600" aria-hidden="true" />
                  <h3 className="font-medium text-gray-900">Rotation Templates</h3>
                </div>
                <p className="text-sm text-gray-600">
                  Define scheduling patterns for each rotation. Templates specify required
                  activities, supervision levels, and weekly schedules.
                </p>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <User className="w-5 h-5 text-blue-600" aria-hidden="true" />
                  <h3 className="font-medium text-gray-900">My Schedule</h3>
                </div>
                <p className="text-sm text-gray-600">
                  View your default weekly activity template. Contact your coordinator
                  if you need to make changes.
                </p>
              </div>
              {userTier >= 1 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-5 h-5 text-amber-600" aria-hidden="true" />
                    <h3 className="font-medium text-gray-900">Faculty Templates</h3>
                  </div>
                  <p className="text-sm text-gray-600">
                    Edit weekly activity templates for any faculty member. Changes
                    affect their default schedule pattern.
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
