'use client';

/**
 * Rotation Templates Tab Component
 *
 * Displays and manages rotation templates for resident scheduling.
 * Templates define activity patterns with constraints like max residents,
 * supervision requirements, and specialty prerequisites.
 *
 * Permission-gated actions:
 * - Tier 0: View only
 * - Tier 1: Create and edit templates
 * - Tier 2: Create, edit, and delete templates
 */

import { useState } from 'react';
import { Plus, RefreshCw, FileText, Calendar, Eye } from 'lucide-react';
import { useRotationTemplates, useDeleteTemplate } from '@/lib/hooks';
import { CardSkeleton } from '@/components/skeletons';
import { CreateTemplateModal } from '@/components/CreateTemplateModal';
import { EditTemplateModal } from '@/components/EditTemplateModal';
import { TemplatePatternModal } from '@/components/TemplatePatternModal';
import { EmptyState } from '@/components/EmptyState';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import type { RotationTemplate } from '@/types/api';

// ============================================================================
// Types
// ============================================================================

export interface RotationTemplatesTabProps {
  /** Whether the user can create/edit templates */
  canEdit: boolean;
  /** Whether the user can delete templates */
  canDelete: boolean;
}

// ============================================================================
// Activity Colors
// ============================================================================

const ACTIVITY_COLORS: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-800',
  inpatient: 'bg-purple-100 text-purple-800',
  procedure: 'bg-red-100 text-red-800',
  conference: 'bg-gray-100 text-gray-800',
  elective: 'bg-green-100 text-green-800',
  call: 'bg-orange-100 text-orange-800',
};

// ============================================================================
// Template Card Component
// ============================================================================

interface TemplateCardProps {
  template: RotationTemplate;
  canEdit: boolean;
  canDelete: boolean;
  onView: () => void;
  onEdit: () => void;
  onEditPattern: () => void;
  onDelete: () => void;
}

function TemplateCard({
  template,
  canEdit,
  canDelete,
  onView,
  onEdit,
  onEditPattern,
  onDelete,
}: TemplateCardProps) {
  const colorClass = ACTIVITY_COLORS[template.activityType] || 'bg-gray-100 text-gray-800';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-gray-900">{template.name}</h3>
          <span className={`inline-block px-2 py-1 rounded text-xs mt-1 ${colorClass}`}>
            {template.activityType}
          </span>
        </div>
        {template.abbreviation && (
          <span className="bg-gray-100 px-2 py-1 rounded text-sm font-mono">
            {template.abbreviation}
          </span>
        )}
      </div>

      <div className="space-y-2 text-sm">
        {template.maxResidents && (
          <div className="flex justify-between">
            <span className="text-gray-500">Max Residents:</span>
            <span className="font-medium">{template.maxResidents}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-500">Supervision Ratio:</span>
          <span className="font-medium">1:{template.maxSupervisionRatio}</span>
        </div>
        {template.requiresSpecialty && (
          <div className="flex justify-between">
            <span className="text-gray-500">Requires:</span>
            <span className="font-medium text-amber-700">{template.requiresSpecialty}</span>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t flex gap-2 flex-wrap">
        <button
          onClick={onView}
          className="text-gray-600 hover:text-gray-900 hover:underline text-sm flex items-center gap-1"
        >
          <Eye className="w-3 h-3" />
          View
        </button>
        {canEdit && (
          <>
            <button
              onClick={onEdit}
              className="text-blue-600 hover:underline text-sm"
            >
              Edit
            </button>
            <button
              onClick={onEditPattern}
              className="text-green-600 hover:underline text-sm flex items-center gap-1"
            >
              <Calendar className="w-3 h-3" />
              Pattern
            </button>
          </>
        )}
        {canDelete && (
          <button
            onClick={onDelete}
            className="text-red-600 hover:underline text-sm"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Main Tab Component
// ============================================================================

export function RotationTemplatesTab({ canEdit, canDelete }: RotationTemplatesTabProps) {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<RotationTemplate | null>(null);
  const [viewingTemplate, setViewingTemplate] = useState<RotationTemplate | null>(null);
  const [patternTemplate, setPatternTemplate] = useState<RotationTemplate | null>(null);
  const [templateToDelete, setTemplateToDelete] = useState<RotationTemplate | null>(null);

  const { data, isLoading, isError, error, refetch } = useRotationTemplates();
  const deleteTemplate = useDeleteTemplate();

  const handleDeleteClick = (template: RotationTemplate) => {
    setTemplateToDelete(template);
  };

  const handleConfirmDelete = () => {
    if (templateToDelete) {
      deleteTemplate.mutate(templateToDelete.id);
    }
    setTemplateToDelete(null);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 flex flex-col items-center justify-center text-center">
        <p className="text-gray-600 mb-4">
          {error?.message || 'Failed to load rotation templates'}
        </p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Action Bar */}
      {canEdit && (
        <div className="mb-6 flex justify-between items-center">
          <p className="text-sm text-gray-600">
            {data?.items?.length ?? 0} template{data?.items?.length !== 1 ? 's' : ''} defined
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Template
          </button>
        </div>
      )}

      {/* Templates Grid */}
      {data?.items?.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <EmptyState
            icon={FileText}
            title="No rotation templates"
            description={
              canEdit
                ? 'Create templates to define reusable activity patterns with constraints'
                : 'No rotation templates have been created yet. Contact an administrator to set up templates.'
            }
            action={
              canEdit
                ? {
                    label: 'Create Template',
                    onClick: () => setIsCreateModalOpen(true),
                  }
                : undefined
            }
          />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.items?.map((template: RotationTemplate) => (
            <TemplateCard
              key={template.id}
              template={template}
              canEdit={canEdit}
              canDelete={canDelete}
              onView={() => setViewingTemplate(template)}
              onEdit={() => setEditingTemplate(template)}
              onEditPattern={() => setPatternTemplate(template)}
              onDelete={() => handleDeleteClick(template)}
            />
          ))}
        </div>
      )}

      {/* Create Template Modal */}
      {canEdit && (
        <CreateTemplateModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}

      {/* Edit Template Modal */}
      {canEdit && (
        <EditTemplateModal
          isOpen={editingTemplate !== null}
          onClose={() => setEditingTemplate(null)}
          template={editingTemplate}
        />
      )}

      {/* View Template Modal (Read-only) */}
      {viewingTemplate && !canEdit && (
        <EditTemplateModal
          isOpen={viewingTemplate !== null}
          onClose={() => setViewingTemplate(null)}
          template={viewingTemplate}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {canDelete && (
        <ConfirmDialog
          isOpen={templateToDelete !== null}
          onClose={() => setTemplateToDelete(null)}
          onConfirm={handleConfirmDelete}
          title="Delete Template"
          message={`Are you sure you want to delete "${templateToDelete?.name || 'this template'}"? This action cannot be undone and may affect existing schedule assignments.`}
          confirmLabel="Delete"
          cancelLabel="Cancel"
          variant="danger"
          isLoading={deleteTemplate.isPending}
        />
      )}

      {/* Edit Pattern Modal */}
      {canEdit && patternTemplate && (
        <TemplatePatternModal
          isOpen={patternTemplate !== null}
          onClose={() => setPatternTemplate(null)}
          templateId={patternTemplate.id}
          templateName={patternTemplate.name}
          onSaved={() => refetch()}
        />
      )}
    </div>
  );
}
