'use client';

/**
 * Activities Hub Page
 *
 * Single-purpose hub for managing the Activity Dictionary.
 *
 * Permission Tiers:
 * - Tier 0 (Green): View dictionary
 * - Tier 1 (Amber): Edit dictionary definitions
 */

import { useState, useMemo } from 'react';
import { BookText, Layers } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { ActivityDictionaryTab } from '@/features/activities/components/ActivityDictionaryTab';

// ============================================================================
// Types
// ============================================================================

type ActivitiesTab = 'dictionary';

interface TabConfig {
  id: ActivitiesTab;
  label: string;
  icon: typeof BookText;
  description: string;
  requiredTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'dictionary',
    label: 'Activity Dictionary',
    icon: BookText,
    description: 'Manage atomic schedule building blocks',
    requiredTier: 0,
  }
];

// ============================================================================
// Component
// ============================================================================

export default function ActivitiesPage() {
  const { user } = useAuth();
  const [activeTab] = useState<ActivitiesTab>('dictionary');

  // Determine user's permission tier from role
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  const currentRiskTier: RiskTier = useMemo(() => {
    return userTier;
  }, [userTier]);

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'View Mode',
          tooltip: 'You can browse activity definitions. Contact an administrator to make changes.',
        };
      case 1:
        return {
          label: 'Edit Mode',
          tooltip: 'You can create and edit activity definitions affecting the entire program.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'You have full access to create, edit, and delete activity definitions.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

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
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-lg">
                <Layers className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Activities Hub</h1>
                <p className="text-sm text-gray-600">
                  Manage the core scheduling vocabulary
                </p>
              </div>
            </div>

            {/* Tabs (Only 1 currently, so we hide the navigation block for cleaner UI,
                but keep structure for future expansion) */}
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {activeTab === 'dictionary' && (
            <div
              id="tabpanel-dictionary"
              role="tabpanel"
              aria-labelledby="tab-dictionary"
            >
              <ActivityDictionaryTab />
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
