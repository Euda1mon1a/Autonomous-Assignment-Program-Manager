'use client';

/**
 * RotationsPanel - Rotation templates list with view/edit modes
 *
 * Tier 0: View-only list of rotation templates
 * Tier 1+: Can edit templates via inline editing
 */

import { useState, useCallback, useMemo } from 'react';
import { Search, Filter, Loader2, RefreshCw, LayoutTemplate } from 'lucide-react';
import { TemplateTable } from '@/components/admin/TemplateTable';
import { useAdminTemplates, useInlineUpdateTemplate } from '@/hooks/useAdminTemplates';
import type {
  ActivityType,
  SortField,
  TemplateSort,
  TemplateUpdateRequest,
} from '@/types/admin-templates';
import { ACTIVITY_TYPE_CONFIGS } from '@/types/admin-templates';

interface RotationsPanelProps {
  canEdit: boolean;
}

export function RotationsPanel({ canEdit }: RotationsPanelProps) {
  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [activityTypeFilter, setActivityTypeFilter] = useState<ActivityType | ''>('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [sort, setSort] = useState<TemplateSort>({
    field: 'name',
    direction: 'asc',
  });
  const [inlineUpdatingId, setInlineUpdatingId] = useState<string | null>(null);

  // Queries
  const {
    data: templatesData,
    isLoading,
    refetch,
  } = useAdminTemplates(activityTypeFilter);

  // Mutations
  const inlineUpdate = useInlineUpdateTemplate();

  // Filter and sort templates
  const templates = useMemo(() => {
    let filtered = templatesData?.items ?? [];

    // Filter by search term
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.name.toLowerCase().includes(search) ||
          t.abbreviation?.toLowerCase().includes(search)
      );
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      const field = sort.field;
      const direction = sort.direction === 'asc' ? 1 : -1;

      const aVal = a[field] ?? '';
      const bVal = b[field] ?? '';

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return aVal.localeCompare(bVal) * direction;
      }
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * direction;
      }
      return 0;
    });

    return filtered;
  }, [templatesData, searchTerm, sort]);

  // Handlers
  const handleSortChange = useCallback((field: SortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handleInlineUpdate = useCallback(
    async (templateId: string, updates: TemplateUpdateRequest) => {
      if (!canEdit) return;
      setInlineUpdatingId(templateId);
      try {
        // Process each field update individually
        const entries = Object.entries(updates) as [string, unknown][];
        for (const [field, value] of entries) {
          await inlineUpdate.mutateAsync({ templateId, field, value });
        }
      } finally {
        setInlineUpdatingId(null);
      }
    },
    [canEdit, inlineUpdate]
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search rotations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
          />
        </div>

        {/* Activity Type Filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={activityTypeFilter}
            onChange={(e) => setActivityTypeFilter(e.target.value as ActivityType | '')}
            className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 appearance-none bg-white"
          >
            <option value="">All Types</option>
            {Object.entries(ACTIVITY_TYPE_CONFIGS).map(([key, config]) => (
              <option key={key} value={key}>
                {config.label}
              </option>
            ))}
          </select>
        </div>

        {/* Refresh */}
        <button
          onClick={() => refetch()}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Count */}
        <span className="text-sm text-gray-500">
          {templates.length} template{templates.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* View-only notice for Tier 0 */}
      {!canEdit && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center gap-2 text-sm text-blue-700">
          <LayoutTemplate className="w-4 h-4 flex-shrink-0" />
          <span>
            You are viewing rotation templates in read-only mode. Contact a coordinator to
            request changes.
          </span>
        </div>
      )}

      {/* Template Table */}
      {templates.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <LayoutTemplate className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Templates Found</h3>
          <p className="text-gray-500">
            {searchTerm || activityTypeFilter
              ? 'Try adjusting your filters.'
              : 'No rotation templates have been created yet.'}
          </p>
        </div>
      ) : (
        <TemplateTable
          templates={templates}
          selectedIds={selectedIds}
          onSelectionChange={canEdit ? setSelectedIds : () => {}}
          sort={sort}
          onSortChange={handleSortChange}
          enableInlineEdit={canEdit}
          onInlineUpdate={canEdit ? handleInlineUpdate : undefined}
          inlineUpdatingId={inlineUpdatingId}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
