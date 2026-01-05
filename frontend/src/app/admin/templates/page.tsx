'use client';

/**
 * Admin Rotation Templates Page
 *
 * Management interface for rotation templates with:
 * - Sortable, filterable template list
 * - Multi-select for bulk operations
 * - Pattern editor integration
 * - Preference management
 */
import { useState, useCallback, useMemo } from 'react';
import {
  LayoutGrid,
  Plus,
  Search,
  Filter,
  Loader2,
  RefreshCw,
  Calendar,
  Settings,
  X,
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { TemplateTable } from '@/components/admin/TemplateTable';
import { BulkActionsToolbar } from '@/components/admin/BulkActionsToolbar';
import { PreferenceEditor } from '@/components/admin/PreferenceEditor';
import { WeeklyGridEditor, WeeklyGridEditorSkeleton } from '@/components/scheduling/WeeklyGridEditor';
import {
  useAdminTemplates,
  useDeleteTemplate,
  useBulkDeleteTemplates,
  useBulkUpdateTemplates,
  useTemplatePreferences,
  useReplaceTemplatePreferences,
} from '@/hooks/useAdminTemplates';
import { useWeeklyPattern, useUpdateWeeklyPattern, useAvailableTemplates } from '@/hooks/useWeeklyPattern';
import type {
  RotationTemplate,
  ActivityType,
  SortField,
  TemplateFilters,
  TemplateSort,
  BulkActionType,
  RotationPreferenceCreate,
} from '@/types/admin-templates';
import type { WeeklyPatternGrid } from '@/types/weekly-pattern';
import { ACTIVITY_TYPE_CONFIGS } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

type EditorMode = 'none' | 'patterns' | 'preferences';

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminTemplatesPage() {
  // State
  const [filters, setFilters] = useState<TemplateFilters>({
    activity_type: '',
    search: '',
  });
  const [sort, setSort] = useState<TemplateSort>({
    field: 'name',
    direction: 'asc',
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editorMode, setEditorMode] = useState<EditorMode>('none');
  const [editingTemplate, setEditingTemplate] = useState<RotationTemplate | null>(null);
  const [pendingAction, setPendingAction] = useState<BulkActionType | null>(null);

  // Queries
  const {
    data: templatesData,
    isLoading: templatesLoading,
    refetch: refetchTemplates,
  } = useAdminTemplates(filters.activity_type as ActivityType | '');

  // Pattern editing queries (conditional on editingTemplate)
  const {
    data: patternData,
    isLoading: patternLoading,
  } = useWeeklyPattern(editingTemplate?.id || '', {
    enabled: !!editingTemplate && editorMode === 'patterns',
  });

  const { data: availableTemplates } = useAvailableTemplates({
    enabled: editorMode === 'patterns',
  });

  const {
    data: preferencesData,
    isLoading: preferencesLoading,
  } = useTemplatePreferences(editingTemplate?.id || '', {
    enabled: !!editingTemplate && editorMode === 'preferences',
  });

  // Mutations
  const deleteTemplate = useDeleteTemplate();
  const bulkDelete = useBulkDeleteTemplates();
  const bulkUpdate = useBulkUpdateTemplates();
  const updatePattern = useUpdateWeeklyPattern();
  const replacePreferences = useReplaceTemplatePreferences();

  // Derived data
  const templates = useMemo(() => {
    if (!templatesData?.items) return [];

    let filtered = [...templatesData.items];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.name.toLowerCase().includes(searchLower) ||
          t.abbreviation?.toLowerCase().includes(searchLower) ||
          t.display_abbreviation?.toLowerCase().includes(searchLower)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sort.field) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'activity_type':
          comparison = a.activity_type.localeCompare(b.activity_type);
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }
      return sort.direction === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [templatesData?.items, filters.search, sort]);

  // Handlers
  const handleSortChange = useCallback((field: SortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handleDeleteSingle = useCallback(
    async (template: RotationTemplate) => {
      if (confirm(`Delete "${template.name}"? This cannot be undone.`)) {
        await deleteTemplate.mutateAsync(template.id);
      }
    },
    [deleteTemplate]
  );

  const handleBulkDelete = useCallback(async () => {
    setPendingAction('delete');
    try {
      await bulkDelete.mutateAsync(selectedIds);
      setSelectedIds([]);
    } finally {
      setPendingAction(null);
    }
  }, [selectedIds, bulkDelete]);

  const handleBulkUpdateActivityType = useCallback(
    async (activityType: ActivityType) => {
      setPendingAction('update_activity_type');
      try {
        await bulkUpdate.mutateAsync({
          templateIds: selectedIds,
          updates: { activity_type: activityType },
        });
        setSelectedIds([]);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate]
  );

  const handleBulkUpdateSupervision = useCallback(
    async (required: boolean) => {
      setPendingAction('update_supervision');
      try {
        await bulkUpdate.mutateAsync({
          templateIds: selectedIds,
          updates: { supervision_required: required },
        });
        setSelectedIds([]);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate]
  );

  const handleBulkUpdateMaxResidents = useCallback(
    async (maxResidents: number) => {
      setPendingAction('update_max_residents');
      try {
        await bulkUpdate.mutateAsync({
          templateIds: selectedIds,
          updates: { max_residents: maxResidents },
        });
        setSelectedIds([]);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate]
  );

  const handleEditPatterns = useCallback((template: RotationTemplate) => {
    setEditingTemplate(template);
    setEditorMode('patterns');
  }, []);

  const handleEditPreferences = useCallback((template: RotationTemplate) => {
    setEditingTemplate(template);
    setEditorMode('preferences');
  }, []);

  const handleCloseEditor = useCallback(() => {
    setEditingTemplate(null);
    setEditorMode('none');
  }, []);

  const handlePatternChange = useCallback(
    (pattern: WeeklyPatternGrid) => {
      if (!editingTemplate) return;
      updatePattern.mutate({
        templateId: editingTemplate.id,
        pattern,
      });
    },
    [editingTemplate, updatePattern]
  );

  const handlePreferencesSave = useCallback(
    (preferences: RotationPreferenceCreate[]) => {
      if (!editingTemplate) return;
      replacePreferences.mutate(
        {
          templateId: editingTemplate.id,
          preferences,
        },
        {
          onSuccess: () => {
            handleCloseEditor();
          },
        }
      );
    },
    [editingTemplate, replacePreferences, handleCloseEditor]
  );

  const isPending = pendingAction !== null || bulkDelete.isPending || bulkUpdate.isPending;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                <LayoutGrid className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Rotation Templates
                </h1>
                <p className="text-sm text-slate-400">
                  Manage rotation template configurations
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => refetchTemplates()}
                disabled={templatesLoading}
                className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                title="Refresh"
              >
                <RefreshCw className={`w-5 h-5 ${templatesLoading ? 'animate-spin' : ''}`} />
              </button>
              <button
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white rounded-lg font-medium transition-all"
              >
                <Plus className="w-4 h-4" />
                New Template
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search templates..."
              value={filters.search}
              onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
              className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            />
            {filters.search && (
              <button
                onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Activity Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={filters.activity_type}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, activity_type: e.target.value as ActivityType | '' }))
              }
              className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            >
              <option value="">All Activity Types</option>
              {ACTIVITY_TYPE_CONFIGS.map((config) => (
                <option key={config.type} value={config.type}>
                  {config.label}
                </option>
              ))}
            </select>
          </div>

          {/* Stats */}
          <div className="flex-1" />
          <div className="text-sm text-slate-400">
            {templates.length} template{templates.length !== 1 ? 's' : ''}
            {templatesData?.total && templatesData.total !== templates.length && (
              <span> of {templatesData.total}</span>
            )}
          </div>
        </div>

        {/* Template Table */}
        {templatesLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner />
          </div>
        ) : (
          <TemplateTable
            templates={templates}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            sort={sort}
            onSortChange={handleSortChange}
            onDelete={handleDeleteSingle}
            onEditPatterns={handleEditPatterns}
            onEditPreferences={handleEditPreferences}
          />
        )}
      </main>

      {/* Bulk Actions Toolbar */}
      <BulkActionsToolbar
        selectedCount={selectedIds.length}
        onClearSelection={() => setSelectedIds([])}
        onBulkDelete={handleBulkDelete}
        onBulkUpdateActivityType={handleBulkUpdateActivityType}
        onBulkUpdateSupervision={handleBulkUpdateSupervision}
        onBulkUpdateMaxResidents={handleBulkUpdateMaxResidents}
        isPending={isPending}
        pendingAction={pendingAction}
      />

      {/* Pattern Editor Modal */}
      {editorMode === 'patterns' && editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-blue-400" />
                <div>
                  <h2 className="text-lg font-semibold text-white">Weekly Pattern</h2>
                  <p className="text-sm text-slate-400">{editingTemplate.name}</p>
                </div>
              </div>
              <button
                onClick={handleCloseEditor}
                className="p-2 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              {patternLoading ? (
                <WeeklyGridEditorSkeleton />
              ) : (
                <WeeklyGridEditor
                  templateId={editingTemplate.id}
                  pattern={patternData?.pattern || { slots: [] }}
                  onChange={handlePatternChange}
                  availableTemplates={availableTemplates || []}
                />
              )}

              {updatePattern.isPending && (
                <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving changes...
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Preferences Editor Modal */}
      {editorMode === 'preferences' && editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800">
              <div className="flex items-center gap-3">
                <Settings className="w-5 h-5 text-violet-400" />
                <div>
                  <h2 className="text-lg font-semibold text-white">Preferences</h2>
                  <p className="text-sm text-slate-400">{editingTemplate.name}</p>
                </div>
              </div>
              <button
                onClick={handleCloseEditor}
                className="p-2 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <PreferenceEditor
                templateId={editingTemplate.id}
                templateName={editingTemplate.name}
                preferences={preferencesData || []}
                isLoading={preferencesLoading}
                onSave={handlePreferencesSave}
                isSaving={replacePreferences.isPending}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
