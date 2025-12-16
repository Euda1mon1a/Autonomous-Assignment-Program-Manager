'use client';

import { useState, useMemo } from 'react';
import { Plus, LayoutGrid, List, BookOpen } from 'lucide-react';
import type { ScheduleTemplate, TemplatePreviewConfig, TemplateCategory } from '../types';
import {
  useTemplates,
  useTemplateFilters,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useDuplicateTemplate,
  useShareTemplate,
  useApplyTemplate,
  usePredefinedTemplates,
  useImportPredefinedTemplate,
} from '../hooks';
import { TemplateSearch } from './TemplateSearch';
import { TemplateCategories } from './TemplateCategories';
import { TemplateList, PredefinedTemplateCard } from './TemplateList';
import { TemplateEditor } from './TemplateEditor';
import { TemplatePreview } from './TemplatePreview';
import { TemplateShareModal } from './TemplateShareModal';

type ViewMode = 'grid' | 'list';
type Tab = 'my-templates' | 'predefined';

interface TemplateLibraryProps {
  onTemplateApplied?: (result: { success: boolean; message: string }) => void;
}

export function TemplateLibrary({ onTemplateApplied }: TemplateLibraryProps) {
  // State
  const [activeTab, setActiveTab] = useState<Tab>('my-templates');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showEditor, setShowEditor] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ScheduleTemplate | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<ScheduleTemplate | null>(null);
  const [shareTemplate, setShareTemplate] = useState<ScheduleTemplate | null>(null);
  const [duplicateTemplate, setDuplicateTemplate] = useState<ScheduleTemplate | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<ScheduleTemplate | null>(null);

  // Filters
  const { filters, setFilters, updateFilter, clearFilters, hasActiveFilters } = useTemplateFilters();

  // Data hooks
  const { data: templatesData, isLoading, isError, error, refetch } = useTemplates(filters);
  const { data: predefinedTemplates } = usePredefinedTemplates();

  // Mutation hooks
  const createTemplate = useCreateTemplate();
  const updateTemplate = useUpdateTemplate();
  const deleteTemplateMutation = useDeleteTemplate();
  const duplicateTemplateMutation = useDuplicateTemplate();
  const shareTemplateMutation = useShareTemplate();
  const applyTemplateMutation = useApplyTemplate();
  const importPredefinedMutation = useImportPredefinedTemplate();

  // Calculate category counts
  const categoryCounts = useMemo(() => {
    if (!templatesData?.items) return {} as Record<TemplateCategory, number>;
    return templatesData.items.reduce((acc, t) => {
      acc[t.category] = (acc[t.category] || 0) + 1;
      return acc;
    }, {} as Record<TemplateCategory, number>);
  }, [templatesData?.items]);

  // Handlers
  const handleCreateNew = () => {
    setEditingTemplate(null);
    setShowEditor(true);
  };

  const handleEdit = (template: ScheduleTemplate) => {
    setEditingTemplate(template);
    setShowEditor(true);
  };

  const handleSave = async (data: Parameters<typeof createTemplate.mutateAsync>[0]) => {
    if (editingTemplate) {
      // Type assertion needed because create and update schemas have slight differences
      // in patterns field (create uses Omit<AssignmentPattern, 'id'>[], update uses AssignmentPattern[])
      await updateTemplate.mutateAsync({ id: editingTemplate.id, data: data as Parameters<typeof updateTemplate.mutateAsync>[0]['data'] });
    } else {
      await createTemplate.mutateAsync(data);
    }
    setShowEditor(false);
    setEditingTemplate(null);
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    await deleteTemplateMutation.mutateAsync(deleteConfirm.id);
    setDeleteConfirm(null);
  };

  const handleDuplicate = async (request: Parameters<typeof duplicateTemplateMutation.mutateAsync>[0]) => {
    await duplicateTemplateMutation.mutateAsync(request);
    setDuplicateTemplate(null);
  };

  const handleShare = async (request: Parameters<typeof shareTemplateMutation.mutateAsync>[0]) => {
    await shareTemplateMutation.mutateAsync(request);
    setShareTemplate(null);
  };

  const handleApply = async (template: ScheduleTemplate, config: TemplatePreviewConfig) => {
    const result = await applyTemplateMutation.mutateAsync({
      templateId: template.id,
      config,
    });
    setPreviewTemplate(null);
    onTemplateApplied?.({
      success: result.success,
      message: result.success
        ? `Created ${result.assignmentsCreated} assignments`
        : `Failed: ${result.assignmentsFailed} assignments failed`,
    });
  };

  const handleImportPredefined = async (templateKey: string) => {
    await importPredefinedMutation.mutateAsync(templateKey);
    setActiveTab('my-templates');
  };

  const handleCategorySelect = (category: TemplateCategory | undefined) => {
    updateFilter('category', category);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Template Library</h1>
          <p className="text-gray-600">Create and manage schedule templates</p>
        </div>
        <button
          onClick={handleCreateNew}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Template
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('my-templates')}
            className={`px-4 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'my-templates'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            My Templates
            {templatesData?.total !== undefined && (
              <span className="ml-2 text-sm bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                {templatesData.total}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('predefined')}
            className={`px-4 py-2 border-b-2 font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'predefined'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            Predefined Templates
          </button>
        </div>
      </div>

      {activeTab === 'my-templates' ? (
        <>
          {/* Search and Filters */}
          <TemplateSearch
            filters={filters}
            onFiltersChange={setFilters}
            totalResults={templatesData?.total}
          />

          {/* Category Pills */}
          <TemplateCategories
            selectedCategory={filters.category}
            onCategorySelect={handleCategorySelect}
            categoryCounts={categoryCounts}
            variant="pills"
          />

          {/* View Toggle */}
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${
                viewMode === 'grid' ? 'bg-gray-200' : 'hover:bg-gray-100'
              }`}
              title="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${
                viewMode === 'list' ? 'bg-gray-200' : 'hover:bg-gray-100'
              }`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Template List */}
          <TemplateList
            templates={templatesData?.items || []}
            isLoading={isLoading}
            isError={isError}
            error={error}
            onRetry={refetch}
            onEdit={handleEdit}
            onDelete={setDeleteConfirm}
            onDuplicate={setDuplicateTemplate}
            onShare={setShareTemplate}
            onPreview={setPreviewTemplate}
            onApply={setPreviewTemplate}
            emptyMessage={
              hasActiveFilters ? 'No templates match your filters' : 'No templates yet'
            }
            emptyAction={{
              label: 'Create Template',
              onClick: handleCreateNew,
            }}
            variant={viewMode}
          />
        </>
      ) : (
        /* Predefined Templates */
        <div className="space-y-4">
          <p className="text-gray-600">
            Import these pre-built templates to your library and customize them to your needs.
          </p>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {predefinedTemplates?.map((template) => (
              <PredefinedTemplateCard
                key={template.templateKey}
                template={template}
                onImport={handleImportPredefined}
                isImporting={importPredefinedMutation.isPending}
              />
            ))}
          </div>
        </div>
      )}

      {/* Editor Modal */}
      {showEditor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowEditor(false)} />
          <div className="relative w-full max-w-3xl max-h-[90vh]">
            <TemplateEditor
              template={editingTemplate}
              onSave={handleSave}
              onCancel={() => {
                setShowEditor(false);
                setEditingTemplate(null);
              }}
              isLoading={createTemplate.isPending || updateTemplate.isPending}
            />
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setPreviewTemplate(null)} />
          <div className="relative">
            <TemplatePreview
              template={previewTemplate}
              onApply={(config) => handleApply(previewTemplate, config)}
              onClose={() => setPreviewTemplate(null)}
              isLoading={applyTemplateMutation.isPending}
            />
          </div>
        </div>
      )}

      {/* Share Modal */}
      {shareTemplate && (
        <TemplateShareModal
          template={shareTemplate}
          mode="share"
          onShare={handleShare}
          onClose={() => setShareTemplate(null)}
          isLoading={shareTemplateMutation.isPending}
        />
      )}

      {/* Duplicate Modal */}
      {duplicateTemplate && (
        <TemplateShareModal
          template={duplicateTemplate}
          mode="duplicate"
          onDuplicate={handleDuplicate}
          onClose={() => setDuplicateTemplate(null)}
          isLoading={duplicateTemplateMutation.isPending}
        />
      )}

      {/* Delete Confirmation */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setDeleteConfirm(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-2">Delete Template</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete "{deleteConfirm.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteTemplateMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deleteTemplateMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
