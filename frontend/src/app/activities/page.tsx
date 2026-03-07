'use client';

import { useState, useMemo, useCallback } from 'react';
import {
  Plus,
  Search,
  Pencil,
  Archive,
  Trash2,
  Loader2,
  Shield,
  Eye,
  EyeOff,
  Layers,
} from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorAlert } from '@/components/ErrorAlert';
import { EmptyState } from '@/components/EmptyState';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { useAuth } from '@/contexts/AuthContext';
import {
  useActivities,
  useCreateActivity,
  useUpdateActivity,
  useDeleteActivity,
  useArchiveActivity,
} from '@/hooks/useActivities';
import type {
  Activity,
  ActivityCategory,
  ActivityCreateRequest,
  ActivityUpdateRequest,
} from '@/types/activity';
import {
  ACTIVITY_CATEGORIES,
  ACTIVITY_CATEGORY_LABELS,
} from '@/types/activity';
import { ActivityFormModal } from './components/ActivityFormModal';

// Tailwind color name to hex for preview swatches
const tailwindToHex: Record<string, string> = {
  black: '#000000',
  white: '#ffffff',
  'gray-100': '#f3f4f6',
  'gray-200': '#e5e7eb',
  'gray-600': '#4b5563',
  'gray-800': '#1f2937',
  'green-500': '#22c55e',
  'yellow-300': '#fde047',
  'sky-500': '#0ea5e9',
  'purple-700': '#7e22ce',
  'red-300': '#fca5a5',
  'blue-300': '#93c5fd',
  'amber-200': '#fde68a',
  'orange-400': '#fb923c',
  'teal-300': '#5eead4',
};

// Category badge colors
const CATEGORY_COLORS: Record<ActivityCategory, string> = {
  clinical: 'bg-emerald-100 text-emerald-700',
  educational: 'bg-blue-100 text-blue-700',
  administrative: 'bg-amber-100 text-amber-700',
  time_off: 'bg-gray-100 text-gray-600', // eslint-disable-line @typescript-eslint/naming-convention -- enum value key
};

export default function ActivitiesPage() {
  const { user } = useAuth();
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);
  const canEdit = userTier >= 1;
  const canDelete = userTier >= 2;

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<ActivityCategory | ''>('');
  const [showArchived, setShowArchived] = useState(false);
  const [editingActivity, setEditingActivity] = useState<Activity | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Activity | null>(null);

  // Data
  const { data, isLoading, error } = useActivities(categoryFilter || undefined, {
    includeArchived: showArchived,
  });
  const createActivity = useCreateActivity();
  const updateActivity = useUpdateActivity();
  const deleteActivity = useDeleteActivity();
  const archiveActivity = useArchiveActivity();

  const activities = useMemo(() => data?.activities ?? [], [data]);

  // Filter by search
  const filteredActivities = useMemo(() => {
    if (!searchQuery) return activities;
    const q = searchQuery.toLowerCase();
    return activities.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.code.toLowerCase().includes(q) ||
        (a.displayAbbreviation?.toLowerCase().includes(q) ?? false)
    );
  }, [activities, searchQuery]);

  // Handlers
  const handleCreate = useCallback(() => {
    setEditingActivity(null);
    setIsFormOpen(true);
  }, []);

  const handleEdit = useCallback((activity: Activity) => {
    setEditingActivity(activity);
    setIsFormOpen(true);
  }, []);

  const handleFormClose = useCallback(() => {
    setIsFormOpen(false);
    setEditingActivity(null);
  }, []);

  const handleFormSave = useCallback(
    async (formData: ActivityCreateRequest | ActivityUpdateRequest) => {
      if (editingActivity) {
        await updateActivity.mutateAsync({
          activityId: editingActivity.id,
          data: formData as ActivityUpdateRequest,
        });
      } else {
        await createActivity.mutateAsync(formData as ActivityCreateRequest);
      }
      handleFormClose();
    },
    [editingActivity, updateActivity, createActivity, handleFormClose]
  );

  const handleArchive = useCallback(
    async (activity: Activity) => {
      await archiveActivity.mutateAsync(activity.id);
    },
    [archiveActivity]
  );

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return;
    await deleteActivity.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  }, [deleteTarget, deleteActivity]);

  const riskConfig = useMemo(() => {
    switch (userTier) {
      case 0:
        return { label: 'View Mode', tooltip: 'You can browse activities. Contact an administrator to make changes.' };
      case 1:
        return { label: 'Edit Mode', tooltip: 'You can create and edit activities.' };
      case 2:
        return { label: 'Admin Mode', tooltip: 'Full access to create, edit, archive, and delete activities.' };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [userTier]);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <RiskBar tier={userTier} label={riskConfig.label} tooltip={riskConfig.tooltip} />

        {/* Header */}
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                <Layers className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Activities</h1>
                <p className="text-sm text-gray-600">
                  Manage slot-level schedule activities (clinic, lecture, off, etc.)
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {/* Toolbar */}
          <div className="flex flex-col sm:flex-row gap-4 justify-between mb-6">
            <div className="flex flex-1 gap-3">
              {/* Search */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, code, or abbreviation..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                />
              </div>

              {/* Category filter */}
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value as ActivityCategory | '')}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white text-sm"
              >
                <option value="">All Categories</option>
                {ACTIVITY_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {ACTIVITY_CATEGORY_LABELS[cat]}
                  </option>
                ))}
              </select>

              {/* Show archived toggle */}
              <button
                onClick={() => setShowArchived(!showArchived)}
                className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm transition-colors ${
                  showArchived
                    ? 'border-purple-300 bg-purple-50 text-purple-700'
                    : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
                }`}
                title={showArchived ? 'Hide archived activities' : 'Show archived activities'}
              >
                {showArchived ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                <span className="hidden sm:inline">Archived</span>
              </button>
            </div>

            {/* Create button */}
            {canEdit && (
              <button
                onClick={handleCreate}
                className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm font-medium"
              >
                <Plus className="h-4 w-4" />
                Add Activity
              </button>
            )}
          </div>

          {/* Table */}
          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : error ? (
            <ErrorAlert message="Failed to load activities" />
          ) : filteredActivities.length === 0 ? (
            <EmptyState
              title="No activities found"
              description={
                searchQuery || categoryFilter
                  ? 'Try adjusting your filters'
                  : 'Create your first activity to get started'
              }
            />
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Preview
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Code
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Abbreviation
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Flags
                      </th>
                      {canEdit && (
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredActivities.map((activity) => (
                      <tr
                        key={activity.id}
                        className={`hover:bg-gray-50 transition-colors ${
                          activity.isArchived ? 'opacity-50' : ''
                        }`}
                      >
                        {/* Color preview */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div
                            className="inline-block px-2.5 py-1 rounded text-xs font-semibold min-w-[2.5rem] text-center"
                            style={{
                              color: tailwindToHex[activity.fontColor ?? ''] || activity.fontColor || '#000',
                              backgroundColor:
                                tailwindToHex[activity.backgroundColor ?? ''] ||
                                activity.backgroundColor ||
                                '#e5e7eb',
                            }}
                          >
                            {activity.displayAbbreviation || activity.code.toUpperCase().slice(0, 3)}
                          </div>
                        </td>

                        {/* Name */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-sm font-medium text-gray-900">{activity.name}</span>
                        </td>

                        {/* Code */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <code className="text-sm text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">
                            {activity.code}
                          </code>
                        </td>

                        {/* Abbreviation */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-sm text-gray-600">
                            {activity.displayAbbreviation || '—'}
                          </span>
                        </td>

                        {/* Category */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                              CATEGORY_COLORS[activity.activityCategory] || 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {ACTIVITY_CATEGORY_LABELS[activity.activityCategory] || activity.activityCategory}
                          </span>
                        </td>

                        {/* Flags */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex gap-1.5">
                            {activity.isProtected && (
                              <span
                                className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs bg-yellow-100 text-yellow-700"
                                title="Protected — solver cannot modify"
                              >
                                <Shield className="w-3 h-3" />
                                Locked
                              </span>
                            )}
                            {activity.requiresSupervision && (
                              <span
                                className="inline-block px-1.5 py-0.5 rounded text-xs bg-blue-100 text-blue-700"
                                title="Requires faculty supervision"
                              >
                                Supervised
                              </span>
                            )}
                            {activity.isArchived && (
                              <span className="inline-block px-1.5 py-0.5 rounded text-xs bg-red-100 text-red-600">
                                Archived
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Actions */}
                        {canEdit && (
                          <td className="px-4 py-3 whitespace-nowrap text-right">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => handleEdit(activity)}
                                className="p-1.5 rounded hover:bg-gray-100 transition-colors"
                                title="Edit activity"
                              >
                                <Pencil className="w-4 h-4 text-gray-400 hover:text-purple-500" />
                              </button>
                              {!activity.isArchived && (
                                <button
                                  onClick={() => handleArchive(activity)}
                                  disabled={archiveActivity.isPending}
                                  className="p-1.5 rounded hover:bg-gray-100 transition-colors disabled:opacity-50"
                                  title="Archive activity"
                                >
                                  {archiveActivity.isPending ? (
                                    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                                  ) : (
                                    <Archive className="w-4 h-4 text-gray-400 hover:text-amber-500" />
                                  )}
                                </button>
                              )}
                              {canDelete && (
                                <button
                                  onClick={() => setDeleteTarget(activity)}
                                  className="p-1.5 rounded hover:bg-gray-100 transition-colors"
                                  title="Delete activity permanently"
                                >
                                  <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-500" />
                                </button>
                              )}
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Count footer */}
              <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-500">
                {filteredActivities.length} of {activities.length} activities
                {showArchived && ' (including archived)'}
              </div>
            </div>
          )}
        </main>

        {/* Form Modal */}
        <ActivityFormModal
          isOpen={isFormOpen}
          onClose={handleFormClose}
          onSave={handleFormSave}
          activity={editingActivity}
          isSaving={createActivity.isPending || updateActivity.isPending}
        />

        {/* Delete Confirmation */}
        <ConfirmDialog
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDeleteConfirm}
          title="Delete Activity"
          message={`Are you sure you want to permanently delete "${deleteTarget?.name}"? This will fail if the activity is in use by weekly patterns or requirements.`}
          confirmLabel="Delete Activity"
          cancelLabel="Cancel"
          variant="danger"
          isLoading={deleteActivity.isPending}
        />
      </div>
    </ProtectedRoute>
  );
}
