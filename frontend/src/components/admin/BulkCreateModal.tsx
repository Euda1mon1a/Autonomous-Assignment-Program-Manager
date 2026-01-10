'use client';

/**
 * BulkCreateModal Component
 *
 * Modal for creating multiple rotation templates at once via a form.
 * Users can add multiple template rows, configure each one, and submit all at once.
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  X,
  Plus,
  Trash2,
  Loader2,
  AlertTriangle,
  Copy,
  ChevronDown,
  ChevronUp,
  Upload,
} from 'lucide-react';
import type {
  TemplateCreateRequest,
  ActivityType,
} from '@/types/admin-templates';
import { ACTIVITY_TYPE_CONFIGS } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface BulkCreateModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Callback to close modal */
  onClose: () => void;
  /** Callback when templates are submitted */
  onSubmit: (templates: TemplateCreateRequest[]) => Promise<void>;
  /** Whether submission is in progress */
  isSubmitting?: boolean;
  /** Callback to open CSV import modal */
  onOpenCSVImport?: () => void;
}

interface TemplateRow extends TemplateCreateRequest {
  id: string;
  isExpanded: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_TEMPLATE: Omit<TemplateRow, 'id' | 'isExpanded'> = {
  name: '',
  activityType: 'clinic',
  abbreviation: null,
  displayAbbreviation: null,
  fontColor: null,
  backgroundColor: null,
  clinicLocation: null,
  maxResidents: null,
  requiresSpecialty: null,
  requiresProcedureCredential: false,
  supervisionRequired: false,
  maxSupervisionRatio: null,
};

// ============================================================================
// Subcomponents
// ============================================================================

interface TemplateRowFormProps {
  template: TemplateRow;
  index: number;
  onChange: (id: string, updates: Partial<TemplateRow>) => void;
  onRemove: (id: string) => void;
  onDuplicate: (id: string) => void;
  onToggleExpand: (id: string) => void;
  isOnly: boolean;
}

function TemplateRowForm({
  template,
  index,
  onChange,
  onRemove,
  onDuplicate,
  onToggleExpand,
  isOnly,
}: TemplateRowFormProps) {
  const activityTypeConfig = useMemo(
    () => ACTIVITY_TYPE_CONFIGS.find((c) => c.type === template.activityType),
    [template.activityType]
  );

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
      {/* Row header */}
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={() => onToggleExpand(template.id)}
      >
        <button
          type="button"
          className="p-1 text-slate-400"
          aria-label={template.isExpanded ? 'Collapse' : 'Expand'}
        >
          {template.isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        <span className="text-sm font-medium text-slate-400">#{index + 1}</span>

        <div className="flex-1 min-w-0">
          <input
            type="text"
            value={template.name}
            onChange={(e) => onChange(template.id, { name: e.target.value })}
            onClick={(e) => e.stopPropagation()}
            placeholder="Template name *"
            className="w-full bg-transparent border-none text-white placeholder-slate-500 focus:outline-none focus:ring-0 text-sm font-medium"
            required
          />
        </div>

        {activityTypeConfig && (
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${activityTypeConfig.bgColor} ${activityTypeConfig.color}`}
          >
            {activityTypeConfig.label}
          </span>
        )}

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDuplicate(template.id);
            }}
            className="p-1.5 text-slate-400 hover:text-violet-400 transition-colors"
            title="Duplicate"
            aria-label="Duplicate template"
          >
            <Copy className="w-4 h-4" />
          </button>
          {!isOnly && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(template.id);
              }}
              className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
              title="Remove"
              aria-label="Remove template"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expanded content */}
      {template.isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-slate-700/50 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Activity Type */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Activity Type *
              </label>
              <select
                value={template.activityType}
                onChange={(e) =>
                  onChange(template.id, {
                    activityType: e.target.value as ActivityType,
                  })
                }
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                required
              >
                {ACTIVITY_TYPE_CONFIGS.map((config) => (
                  <option key={config.type} value={config.type}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Abbreviation */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Abbreviation
              </label>
              <input
                type="text"
                value={template.abbreviation || ''}
                onChange={(e) =>
                  onChange(template.id, {
                    abbreviation: e.target.value || null,
                  })
                }
                placeholder="e.g., CLIN"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            {/* Display Abbreviation */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Display Abbreviation
              </label>
              <input
                type="text"
                value={template.displayAbbreviation || ''}
                onChange={(e) =>
                  onChange(template.id, {
                    displayAbbreviation: e.target.value || null,
                  })
                }
                placeholder="e.g., Clinic"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            {/* Max Residents */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Max Residents
              </label>
              <input
                type="number"
                value={template.maxResidents ?? ''}
                onChange={(e) =>
                  onChange(template.id, {
                    maxResidents: e.target.value ? parseInt(e.target.value) : null,
                  })
                }
                min={1}
                max={50}
                placeholder="No limit"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            {/* Clinic Location */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Clinic Location
              </label>
              <input
                type="text"
                value={template.clinicLocation || ''}
                onChange={(e) =>
                  onChange(template.id, {
                    clinicLocation: e.target.value || null,
                  })
                }
                placeholder="e.g., Building A, Room 101"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            {/* Requires Specialty */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Required Specialty
              </label>
              <input
                type="text"
                value={template.requiresSpecialty || ''}
                onChange={(e) =>
                  onChange(template.id, {
                    requiresSpecialty: e.target.value || null,
                  })
                }
                placeholder="e.g., Cardiology"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>
          </div>

          {/* Checkboxes row */}
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={template.supervisionRequired}
                onChange={(e) =>
                  onChange(template.id, {
                    supervisionRequired: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
              />
              Supervision Required
            </label>

            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={template.requiresProcedureCredential}
                onChange={(e) =>
                  onChange(template.id, {
                    requiresProcedureCredential: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
              />
              Requires Procedure Credential
            </label>
          </div>

          {/* Color pickers row */}
          <div className="flex gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Background Color
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={template.backgroundColor || '#6366F1'}
                  onChange={(e) =>
                    onChange(template.id, { backgroundColor: e.target.value })
                  }
                  className="w-8 h-8 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={template.backgroundColor || ''}
                  onChange={(e) =>
                    onChange(template.id, {
                      backgroundColor: e.target.value || null,
                    })
                  }
                  placeholder="#RRGGBB"
                  className="w-24 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Font Color
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={template.fontColor || '#FFFFFF'}
                  onChange={(e) =>
                    onChange(template.id, { fontColor: e.target.value })
                  }
                  className="w-8 h-8 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={template.fontColor || ''}
                  onChange={(e) =>
                    onChange(template.id, {
                      fontColor: e.target.value || null,
                    })
                  }
                  placeholder="#RRGGBB"
                  className="w-24 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function BulkCreateModal({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
  onOpenCSVImport,
}: BulkCreateModalProps) {
  const [templates, setTemplates] = useState<TemplateRow[]>(() => [
    {
      ...DEFAULT_TEMPLATE,
      id: `new-${Date.now()}`,
      isExpanded: true,
    },
  ]);

  // Validation
  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    const names = new Set<string>();

    templates.forEach((t, index) => {
      if (!t.name.trim()) {
        errors.push(`Template #${index + 1} requires a name`);
      } else if (names.has(t.name.trim().toLowerCase())) {
        errors.push(`Duplicate name: "${t.name.trim()}"`);
      } else {
        names.add(t.name.trim().toLowerCase());
      }
    });

    return errors;
  }, [templates]);

  const isValid = validationErrors.length === 0 && templates.length > 0;

  const handleAddTemplate = useCallback(() => {
    setTemplates((prev) => [
      ...prev,
      {
        ...DEFAULT_TEMPLATE,
        id: `new-${Date.now()}`,
        isExpanded: true,
      },
    ]);
  }, []);

  const handleRemoveTemplate = useCallback((id: string) => {
    setTemplates((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const handleDuplicateTemplate = useCallback((id: string) => {
    setTemplates((prev) => {
      const index = prev.findIndex((t) => t.id === id);
      if (index === -1) return prev;

      const original = prev[index];
      const duplicate: TemplateRow = {
        ...original,
        id: `new-${Date.now()}`,
        name: `${original.name} (Copy)`,
        isExpanded: true,
      };

      const newTemplates = [...prev];
      newTemplates.splice(index + 1, 0, duplicate);
      return newTemplates;
    });
  }, []);

  const handleUpdateTemplate = useCallback(
    (id: string, updates: Partial<TemplateRow>) => {
      setTemplates((prev) =>
        prev.map((t) => (t.id === id ? { ...t, ...updates } : t))
      );
    },
    []
  );

  const handleToggleExpand = useCallback((id: string) => {
    setTemplates((prev) =>
      prev.map((t) => (t.id === id ? { ...t, isExpanded: !t.isExpanded } : t))
    );
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!isValid || isSubmitting) return;

    // Convert to TemplateCreateRequest format
    const requests: TemplateCreateRequest[] = templates.map((t) => ({
      name: t.name.trim(),
      activityType: t.activityType,
      abbreviation: t.abbreviation || null,
      displayAbbreviation: t.displayAbbreviation || null,
      fontColor: t.fontColor || null,
      backgroundColor: t.backgroundColor || null,
      clinicLocation: t.clinicLocation || null,
      maxResidents: t.maxResidents,
      requiresSpecialty: t.requiresSpecialty || null,
      requiresProcedureCredential: t.requiresProcedureCredential,
      supervisionRequired: t.supervisionRequired,
      maxSupervisionRatio: t.maxSupervisionRatio,
    }));

    await onSubmit(requests);
  }, [templates, isValid, isSubmitting, onSubmit]);

  const handleClose = useCallback(() => {
    if (isSubmitting) return;
    onClose();
    // Reset form
    setTemplates([
      {
        ...DEFAULT_TEMPLATE,
        id: `new-${Date.now()}`,
        isExpanded: true,
      },
    ]);
  }, [isSubmitting, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="bulk-create-title"
    >
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div>
            <h2 id="bulk-create-title" className="text-lg font-semibold text-white">
              Create Multiple Templates
            </h2>
            <p className="text-sm text-slate-400 mt-0.5">
              Add {templates.length} template{templates.length !== 1 ? 's' : ''} at once
            </p>
          </div>
          <div className="flex items-center gap-2">
            {onOpenCSVImport && (
              <button
                type="button"
                onClick={onOpenCSVImport}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-300 hover:text-white transition-colors"
              >
                <Upload className="w-4 h-4" />
                Import CSV
              </button>
            )}
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {templates.map((template, index) => (
            <TemplateRowForm
              key={template.id}
              template={template}
              index={index}
              onChange={handleUpdateTemplate}
              onRemove={handleRemoveTemplate}
              onDuplicate={handleDuplicateTemplate}
              onToggleExpand={handleToggleExpand}
              isOnly={templates.length === 1}
            />
          ))}

          {/* Add button */}
          <button
            type="button"
            onClick={handleAddTemplate}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-slate-600 hover:border-violet-500/50 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Template
          </button>
        </div>

        {/* Validation errors */}
        {validationErrors.length > 0 && (
          <div className="mx-4 mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-red-300">
                <p className="font-medium mb-1">Please fix the following:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {validationErrors.map((error, i) => (
                    <li key={i}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-700">
          <span className="text-sm text-slate-400">
            {templates.length} template{templates.length !== 1 ? 's' : ''} to create
          </span>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!isValid || isSubmitting}
              className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  Create {templates.length} Template{templates.length !== 1 ? 's' : ''}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BulkCreateModal;
