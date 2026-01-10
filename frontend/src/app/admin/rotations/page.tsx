'use client';

/**
 * Admin Rotation Templates Page
 *
 * Management interface for rotation templates with:
 * - Sortable, filterable template list
 * - Multi-select for bulk operations
 * - Pattern editor integration
 * - Preference management
 * - Keyboard shortcuts for power users
 * - Debounced search for better performance
 */
import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
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
  Keyboard,
  Archive,
  Clock,
  Save,
  Database,
  Sliders,
  Eye,
  EyeOff,
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { TemplateTable } from '@/components/admin/TemplateTable';
import { BulkActionsToolbar } from '@/components/admin/BulkActionsToolbar';
import { PreferenceEditor } from '@/components/admin/PreferenceEditor';
import { WeeklyGridEditor, WeeklyGridEditorSkeleton } from '@/components/scheduling/WeeklyGridEditor';
import { ArchivedTemplatesDrawer } from '@/components/admin/ArchivedTemplatesDrawer';
import { WeeklyRequirementsEditor } from '@/components/admin/WeeklyRequirementsEditor';
import { HalfDayRequirementsEditor } from '@/components/HalfDayRequirementsEditor';
import { BulkWeeklyPatternModal } from '@/components/admin/BulkWeeklyPatternModal';
import { BulkCreateModal } from '@/components/admin/BulkCreateModal';
import {
  useAdminTemplates,
  useDeleteTemplate,
  useBulkDeleteTemplates,
  useBulkUpdateTemplates,
  useBulkCreateTemplates,
  useTemplatePreferences,
  useReplaceTemplatePreferences,
  useBulkRestoreTemplates,
  useInlineUpdateTemplate,
} from '@/hooks/useAdminTemplates';
import { useWeeklyPattern, useUpdateWeeklyPattern, useAvailableTemplates } from '@/hooks/useWeeklyPattern';
import { useHalfDayRequirements, useUpdateHalfDayRequirements } from '@/hooks/useHalfDayRequirements';
import { useActivities, useActivityRequirements, useReplaceActivityRequirements } from '@/hooks/useActivities';
import { RotationEditor } from '@/components/RotationEditor';
import type { ActivityRequirementCreateRequest } from '@/types/activity';
import { useDebounce, useDebouncedCallback } from '@/hooks/useDebounce';
import { useCreateSnapshot } from '@/hooks/useBackup';
import { useKeyboardShortcuts, getShortcutDisplay } from '@/hooks/useKeyboardShortcuts';
import { useToast } from '@/contexts/ToastContext';
import type {
  RotationTemplate,
  ActivityType,
  SortField,
  TemplateFilters,
  TemplateSort,
  BulkActionType,
  RotationPreferenceCreate,
  TemplateUpdateRequest,
} from '@/types/admin-templates';
import type { WeeklyPatternGrid } from '@/types/weekly-pattern';
import { ACTIVITY_TYPE_CONFIGS, TEMPLATE_CATEGORY_CONFIGS, TemplateCategory } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

type EditorMode = 'none' | 'patterns' | 'preferences' | 'weekly-requirements' | 'halfday-requirements' | 'unified-editor';

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminTemplatesPage() {
  // Refs for keyboard shortcuts
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [showShortcutsHint, setShowShortcutsHint] = useState(false);

  // Toast notifications
  const { toast } = useToast();

  // State
  const [filters, setFilters] = useState<TemplateFilters>({
    activityType: '',
    templateCategory: 'rotation', // Default to showing only rotations
    search: '',
  });
  const [showAllCategories, setShowAllCategories] = useState(false);
  const [sort, setSort] = useState<TemplateSort>({
    field: 'name',
    direction: 'asc',
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editorMode, setEditorMode] = useState<EditorMode>('none');
  const [editingTemplate, setEditingTemplate] = useState<RotationTemplate | null>(null);
  const [pendingAction, setPendingAction] = useState<BulkActionType | null>(null);
  const [showArchivedDrawer, setShowArchivedDrawer] = useState(false);
  const [showBulkPatternModal, setShowBulkPatternModal] = useState(false);
  const [showBulkCreateModal, setShowBulkCreateModal] = useState(false);

  // Debounce search input for better performance
  const debouncedSearch = useDebounce(filters.search, 300);

  // Queries
  const {
    data: templatesData,
    isLoading: templatesLoading,
    refetch: refetchTemplates,
  } = useAdminTemplates(filters.activityType as ActivityType | '');

  // Archived templates query (only fetch when drawer is open)
  const {
    data: archivedTemplatesData,
    isLoading: archivedTemplatesLoading,
  } = useAdminTemplates('', {
    includeArchived: true,
    enabled: showArchivedDrawer,
  });

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

  // Half-day requirements query
  const {
    data: halfdayData,
    isLoading: halfdayLoading,
  } = useHalfDayRequirements(editingTemplate?.id || '', {
    enabled: !!editingTemplate && editorMode === 'halfday-requirements',
  });

  // Activities for unified editor
  const {
    data: activitiesData,
    isLoading: activitiesLoading,
  } = useActivities('', {
    enabled: editorMode === 'unified-editor',
  });

  // Activity requirements for unified editor
  const {
    data: activityRequirementsData,
    isLoading: activityRequirementsLoading,
  } = useActivityRequirements(editingTemplate?.id || '', {
    enabled: !!editingTemplate && editorMode === 'unified-editor',
  });

  // Mutations
  const deleteTemplate = useDeleteTemplate();
  const bulkDelete = useBulkDeleteTemplates();
  const bulkUpdate = useBulkUpdateTemplates();
  const bulkCreate = useBulkCreateTemplates();
  const updatePattern = useUpdateWeeklyPattern();
  const updateHalfday = useUpdateHalfDayRequirements();
  const replacePreferences = useReplaceTemplatePreferences();
  const replaceActivityRequirements = useReplaceActivityRequirements();
  const bulkRestore = useBulkRestoreTemplates();
  const inlineUpdate = useInlineUpdateTemplate();
  const createSnapshot = useCreateSnapshot();

  // Edit queue for auto-save
  const [editQueue, setEditQueue] = useState<Map<string, Partial<TemplateUpdateRequest>>>(new Map());
  const [inlineUpdatingId, setInlineUpdatingId] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Flush edit queue (debounced)
  const flushEditQueue = useCallback(async () => {
    if (editQueue.size === 0) return;

    const entries = Array.from(editQueue.entries());
    setEditQueue(new Map()); // Clear queue immediately
    setHasUnsavedChanges(false);

    for (const [templateId, updates] of entries) {
      setInlineUpdatingId(templateId);
      try {
        await inlineUpdate.mutateAsync({
          templateId,
          field: Object.keys(updates)[0],
          value: Object.values(updates)[0],
        });
      } catch (error) {
        toast.error(`Failed to save changes: ${error}`);
        // Re-queue on failure
        setEditQueue((prev) => new Map(prev).set(templateId, updates));
        setHasUnsavedChanges(true);
      } finally {
        setInlineUpdatingId(null);
      }
    }
  }, [editQueue, inlineUpdate, toast]);

  // Debounced flush - auto-save after 1.5s of no changes
  const { debouncedCallback: debouncedFlush, flush: flushNow } = useDebouncedCallback(
    flushEditQueue,
    1500
  );

  // Queue an inline edit (auto-saves via debounce)
  const handleInlineUpdate = useCallback(
    async (templateId: string, updates: TemplateUpdateRequest) => {
      setEditQueue((prev) => {
        const newQueue = new Map(prev);
        const existing = newQueue.get(templateId) || {};
        newQueue.set(templateId, { ...existing, ...updates });
        return newQueue;
      });
      setHasUnsavedChanges(true);
      debouncedFlush();
    },
    [debouncedFlush]
  );

  // Flush on unmount or page navigation
  useEffect(() => {
    return () => {
      if (editQueue.size > 0) {
        flushNow();
      }
    };
  }, [editQueue.size, flushNow]);

  // Derived data - uses debounced search for better performance
  const templates = useMemo(() => {
    if (!templatesData?.items) return [];

    let filtered = [...templatesData.items];

    // Search filter - using debounced value
    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.name.toLowerCase().includes(searchLower) ||
          t.abbreviation?.toLowerCase().includes(searchLower) ||
          t.displayAbbreviation?.toLowerCase().includes(searchLower)
      );
    }

    // Activity type filter
    if (filters.activityType) {
      filtered = filtered.filter((t) => t.activityType === filters.activityType);
    }

    // Category filter - always apply unless showAllCategories is enabled
    if (filters.templateCategory && !showAllCategories) {
      filtered = filtered.filter((t) => t.templateCategory === filters.templateCategory);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sort.field) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'activityType':
          comparison = a.activityType.localeCompare(b.activityType);
          break;
        case 'createdAt':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
      }
      return sort.direction === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [templatesData?.items, debouncedSearch, filters, sort]);

  // Archived templates - filter from the includeArchived query
  const archivedTemplates = useMemo(() => {
    if (!archivedTemplatesData?.items) return [];
    // Filter for only archived templates from the full list
    return archivedTemplatesData.items.filter((t) => t.isArchived === true);
  }, [archivedTemplatesData?.items]);

  // Handlers
  const handleSortChange = useCallback((field: SortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handleRefresh = useCallback(() => {
    refetchTemplates();
    toast.info('Refreshing templates...');
  }, [refetchTemplates, toast]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
    searchInputRef.current?.select();
  }, []);

  const handleDeleteSingle = useCallback(
    async (template: RotationTemplate) => {
      if (confirm(`Delete "${template.name}"? This cannot be undone.`)) {
        try {
          await deleteTemplate.mutateAsync(template.id);
          toast.success(`Template "${template.name}" deleted`);
        } catch (error) {
          toast.error(error);
        }
      }
    },
    [deleteTemplate, toast]
  );

  const handleBulkDelete = useCallback(async () => {
    setPendingAction('delete');
    try {
      // Create backup snapshot before bulk delete
      await createSnapshot.mutateAsync({
        table: 'rotation_templates',
        reason: `Bulk delete of ${selectedIds.length} template(s)`,
      });
      toast.info('Backup created');

      await bulkDelete.mutateAsync(selectedIds);
      toast.success(`${selectedIds.length} template(s) deleted`);
      setSelectedIds([]);
    } catch (error) {
      toast.error(error);
    } finally {
      setPendingAction(null);
    }
  }, [selectedIds, bulkDelete, createSnapshot, toast]);

  const handleBulkUpdateActivityType = useCallback(
    async (activityType: ActivityType) => {
      setPendingAction('update_activityType');
      try {
        await bulkUpdate.mutateAsync({
          templateIds: selectedIds,
          updates: { activityType: activityType },
        });
        toast.success(`${selectedIds.length} template(s) updated`);
        setSelectedIds([]);
      } catch (error) {
        toast.error(error);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate, toast]
  );

  const handleBulkUpdateSupervision = useCallback(
    async (required: boolean) => {
      setPendingAction('update_supervision');
      try {
        await bulkUpdate.mutateAsync({
          templateIds: selectedIds,
          updates: { supervisionRequired: required },
        });
        toast.success(`${selectedIds.length} template(s) updated`);
        setSelectedIds([]);
      } catch (error) {
        toast.error(error);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate, toast]
  );

  const handleBulkUpdateMaxResidents = useCallback(
    async (maxResidents: number) => {
      setPendingAction('update_maxResidents');
      try {
        await bulkUpdate.mutateAsync({
          templateIds: selectedIds,
          updates: { maxResidents: maxResidents },
        });
        toast.success(`${selectedIds.length} template(s) updated`);
        setSelectedIds([]);
      } catch (error) {
        toast.error(error);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate, toast]
  );

  const handleBulkEditPatterns = useCallback(() => {
    setShowBulkPatternModal(true);
  }, []);

  const handleBulkPatternModalClose = useCallback(() => {
    setShowBulkPatternModal(false);
  }, []);

  const handleBulkPatternComplete = useCallback(() => {
    toast.success('Patterns updated successfully');
    setSelectedIds([]);
    refetchTemplates();
  }, [toast, refetchTemplates]);

  const handleEditPatterns = useCallback((template: RotationTemplate) => {
    setEditingTemplate(template);
    setEditorMode('patterns');
  }, []);

  const handleEditPreferences = useCallback((template: RotationTemplate) => {
    setEditingTemplate(template);
    setEditorMode('preferences');
  }, []);

  const handleEditWeeklyRequirements = useCallback((template: RotationTemplate) => {
    setEditingTemplate(template);
    setEditorMode('weekly-requirements');
  }, []);

  const handleEditHalfdayRequirements = useCallback((template: RotationTemplate) => {
    setEditingTemplate(template);
    setEditorMode('halfday-requirements');
  }, []);

  const handleEditUnified = useCallback((template: RotationTemplate) => {
    setEditingTemplate(template);
    setEditorMode('unified-editor');
  }, []);

  const handleActivityRequirementsSave = useCallback(
    (requirements: ActivityRequirementCreateRequest[]) => {
      if (!editingTemplate) return;
      replaceActivityRequirements.mutate(
        {
          templateId: editingTemplate.id,
          requirements,
        },
        {
          onSuccess: () => {
            toast.success('Activity requirements saved');
          },
          onError: (error) => {
            toast.error(error);
          },
        }
      );
    },
    [editingTemplate, replaceActivityRequirements, toast]
  );

  const handleHalfdaySave = useCallback(
    (data: import('@/types/admin-templates').HalfDayRequirementCreate) => {
      if (!editingTemplate) return;
      updateHalfday.mutate(
        {
          templateId: editingTemplate.id,
          requirements: data,
        },
        {
          onSuccess: () => {
            toast.success('Half-day requirements saved');
          },
          onError: (error) => {
            toast.error(error);
          },
        }
      );
    },
    [editingTemplate, updateHalfday, toast]
  );

  const handleCloseEditor = useCallback(() => {
    setEditingTemplate(null);
    setEditorMode('none');
  }, []);

  const handlePatternChange = useCallback(
    (pattern: WeeklyPatternGrid) => {
      if (!editingTemplate) return;
      updatePattern.mutate(
        {
          templateId: editingTemplate.id,
          pattern,
        },
        {
          onSuccess: () => {
            toast.success('Pattern saved');
          },
          onError: (error) => {
            toast.error(error);
          },
        }
      );
    },
    [editingTemplate, updatePattern, toast]
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
            toast.success('Preferences saved');
            handleCloseEditor();
          },
          onError: (error) => {
            toast.error(error);
          },
        }
      );
    },
    [editingTemplate, replacePreferences, handleCloseEditor, toast]
  );

  const handleWeeklyRequirementsSave = useCallback(() => {
    toast.success('Weekly requirements saved');
    handleCloseEditor();
  }, [handleCloseEditor, toast]);

  const handleRestoreTemplates = useCallback(
    async (templateIds: string[]) => {
      try {
        await bulkRestore.mutateAsync(templateIds);
        toast.success(`${templateIds.length} template(s) restored`);
      } catch (error) {
        toast.error(error);
      }
    },
    [bulkRestore, toast]
  );

  // Keyboard shortcuts
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'k',
        modifiers: ['cmd'],
        handler: handleFocusSearch,
        description: 'Focus search',
      },
      {
        key: 'r',
        handler: handleRefresh,
        description: 'Refresh templates',
        ignoreInputs: true,
      },
      {
        key: 'Escape',
        handler: () => {
          if (editorMode !== 'none') {
            handleCloseEditor();
          } else if (filters.search) {
            setFilters((prev) => ({ ...prev, search: '' }));
          } else if (selectedIds.length > 0) {
            setSelectedIds([]);
          }
        },
        description: 'Close modal / Clear selection',
      },
      {
        key: '?',
        modifiers: ['shift'],
        handler: () => setShowShortcutsHint((prev) => !prev),
        description: 'Toggle shortcuts help',
        ignoreInputs: true,
      },
    ],
    enabled: true,
  });

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
                <p className="text-sm text-slate-300">
                  Manage rotation template configurations
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              {/* Unsaved changes indicator */}
              {hasUnsavedChanges && (
                <button
                  onClick={flushNow}
                  disabled={inlineUpdate.isPending}
                  className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/20 border border-amber-500/50 text-amber-400 rounded-lg text-sm font-medium hover:bg-amber-500/30 transition-colors disabled:opacity-50"
                  title="Save pending changes"
                >
                  {inlineUpdate.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {editQueue.size} unsaved
                </button>
              )}
              <button
                onClick={() => setShowShortcutsHint((prev) => !prev)}
                className="p-2 text-slate-300 hover:text-white transition-colors"
                title="Keyboard shortcuts (Shift+?)"
              >
                <Keyboard className="w-5 h-5" />
              </button>
              <button
                onClick={handleRefresh}
                disabled={templatesLoading}
                className="p-2 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
                title={`Refresh (${getShortcutDisplay({ key: 'r' })})`}
              >
                <RefreshCw className={`w-5 h-5 ${templatesLoading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => setShowArchivedDrawer(true)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
                title="View archived templates"
              >
                <Archive className="w-4 h-4" />
                View Archived
              </button>
              <button
                onClick={() => setShowBulkCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white rounded-lg font-medium transition-all"
              >
                <Plus className="w-4 h-4" />
                New Template
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Keyboard Shortcuts Hint */}
      {showShortcutsHint && (
        <div className="fixed bottom-4 right-4 z-50 bg-slate-800 border border-slate-700 rounded-lg shadow-xl p-4 max-w-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Keyboard className="w-4 h-4" />
              Keyboard Shortcuts
            </h3>
            <button
              onClick={() => setShowShortcutsHint(false)}
              className="text-slate-300 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-slate-300">
              <span>Focus search</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">{getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })}</kbd>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Refresh</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">R</kbd>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Close / Clear</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">Esc</kbd>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>This help</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">Shift+?</kbd>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder={`Search templates... (${getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })})`}
              value={filters.search}
              onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
              className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            />
            {filters.search && (
              <button
                onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Activity Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-300" />
            <select
              value={filters.activityType}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, activityType: e.target.value as ActivityType | '' }))
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

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <select
              value={filters.templateCategory}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  templateCategory: e.target.value as TemplateCategory | '',
                }))
              }
              disabled={showAllCategories}
              className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50"
            >
              <option value="">All Categories</option>
              {TEMPLATE_CATEGORY_CONFIGS.map((config) => (
                <option key={config.value} value={config.value}>
                  {config.label}
                </option>
              ))}
            </select>
          </div>

          {/* Show All Categories Toggle */}
          <button
            type="button"
            onClick={() => setShowAllCategories(!showAllCategories)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              showAllCategories
                ? 'bg-violet-500/20 border border-violet-500/50 text-violet-400'
                : 'bg-slate-800/50 border border-slate-700 text-slate-300 hover:text-white'
            }`}
            title={showAllCategories ? 'Hide slot-level activities' : 'Show all (including activities)'}
          >
            {showAllCategories ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {showAllCategories ? 'Showing All' : 'Rotations Only'}
          </button>

          {/* Stats */}
          <div className="flex-1" />
          <div className="text-sm text-slate-300">
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
            onEditWeeklyRequirements={handleEditWeeklyRequirements}
            onEditHalfdayRequirements={handleEditHalfdayRequirements}
            onEditUnified={handleEditUnified}
            enableInlineEdit={true}
            onInlineUpdate={handleInlineUpdate}
            inlineUpdatingId={inlineUpdatingId}
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
        onBulkEditPatterns={handleBulkEditPatterns}
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
                  <p className="text-sm text-slate-300">{editingTemplate.name}</p>
                </div>
              </div>
              <button
                onClick={handleCloseEditor}
                className="p-2 text-slate-300 hover:text-white transition-colors"
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
                <div className="mt-4 flex items-center gap-2 text-sm text-slate-300">
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
                  <p className="text-sm text-slate-300">{editingTemplate.name}</p>
                </div>
              </div>
              <button
                onClick={handleCloseEditor}
                className="p-2 text-slate-300 hover:text-white transition-colors"
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

      {/* Weekly Requirements Editor Modal */}
      {editorMode === 'weekly-requirements' && editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-cyan-400" />
                <div>
                  <h2 className="text-lg font-semibold text-white">Weekly Requirements</h2>
                  <p className="text-sm text-slate-300">{editingTemplate.name}</p>
                </div>
              </div>
              <button
                onClick={handleCloseEditor}
                className="p-2 text-slate-300 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <WeeklyRequirementsEditor
                templateId={editingTemplate.id}
                templateName={editingTemplate.name}
                onSave={handleWeeklyRequirementsSave}
                onClose={handleCloseEditor}
              />
            </div>
          </div>
        </div>
      )}

      {/* Half-Day Requirements Editor Modal */}
      {editorMode === 'halfday-requirements' && editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800">
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-emerald-400" />
                <div>
                  <h2 className="text-lg font-semibold text-white">Half-Day Requirements</h2>
                  <p className="text-sm text-slate-300">{editingTemplate.name}</p>
                </div>
              </div>
              <button
                onClick={handleCloseEditor}
                className="p-2 text-slate-300 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <HalfDayRequirementsEditor
                requirements={halfdayData ?? null}
                isLoading={halfdayLoading}
                isSaving={updateHalfday.isPending}
                onSave={handleHalfdaySave}
                onCancel={handleCloseEditor}
              />
            </div>
          </div>
        </div>
      )}

      {/* Unified Rotation Editor Modal */}
      {editorMode === 'unified-editor' && editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800">
              <div className="flex items-center gap-3">
                <Sliders className="w-5 h-5 text-violet-400" />
                <div>
                  <h2 className="text-lg font-semibold text-white">Edit Rotation</h2>
                  <p className="text-sm text-slate-300">{editingTemplate.name}</p>
                </div>
              </div>
              <button
                onClick={handleCloseEditor}
                className="p-2 text-slate-300 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              {(patternLoading || activitiesLoading || activityRequirementsLoading) ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                </div>
              ) : (
                <RotationEditor
                  templateId={editingTemplate.id}
                  pattern={patternData?.pattern || { slots: [] }}
                  activities={activitiesData?.activities || []}
                  requirements={activityRequirementsData || []}
                  isLoading={false}
                  isSaving={updatePattern.isPending || replaceActivityRequirements.isPending}
                  readOnly={false}
                  onPatternChange={handlePatternChange}
                  onRequirementsChange={handleActivityRequirementsSave}
                  onSave={handleCloseEditor}
                  onCancel={handleCloseEditor}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Archived Templates Drawer */}
      <ArchivedTemplatesDrawer
        isOpen={showArchivedDrawer}
        templates={archivedTemplates}
        isLoading={archivedTemplatesLoading}
        onClose={() => setShowArchivedDrawer(false)}
        onRestore={handleRestoreTemplates}
        isRestoring={bulkRestore.isPending}
      />

      {/* Bulk Weekly Pattern Modal */}
      <BulkWeeklyPatternModal
        isOpen={showBulkPatternModal}
        selectedTemplates={templates.filter((t) => selectedIds.includes(t.id))}
        onClose={handleBulkPatternModalClose}
        onComplete={handleBulkPatternComplete}
      />

      {/* Bulk Create Modal */}
      <BulkCreateModal
        isOpen={showBulkCreateModal}
        onClose={() => setShowBulkCreateModal(false)}
        onSubmit={async (templates) => {
          await bulkCreate.mutateAsync(templates);
          setShowBulkCreateModal(false);
        }}
        isSubmitting={bulkCreate.isPending}
      />
    </div>
  );
}
