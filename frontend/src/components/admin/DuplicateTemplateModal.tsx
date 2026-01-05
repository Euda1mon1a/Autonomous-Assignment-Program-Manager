'use client';

/**
 * DuplicateTemplateModal Component
 *
 * Modal for duplicating one or more selected templates with modifications.
 * Supports batch duplication with optional naming patterns and property overrides.
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  X,
  Copy,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import type {
  RotationTemplate,
  TemplateCreateRequest,
  ActivityType,
} from '@/types/admin-templates';
import { ACTIVITY_TYPE_CONFIGS, getActivityTypeConfig } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface DuplicateTemplateModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Templates to duplicate */
  templates: RotationTemplate[];
  /** Callback to close modal */
  onClose: () => void;
  /** Callback when duplicates are created */
  onDuplicate: (templates: TemplateCreateRequest[]) => Promise<void>;
  /** Whether duplication is in progress */
  isDuplicating?: boolean;
}

interface DuplicateConfig {
  namingPattern: 'copy' | 'suffix' | 'prefix';
  suffix: string;
  prefix: string;
  includeOverrides: boolean;
  overrideActivityType: ActivityType | null;
  overrideMaxResidents: number | null;
  overrideSupervision: boolean | null;
}

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_CONFIG: DuplicateConfig = {
  namingPattern: 'copy',
  suffix: '',
  prefix: '',
  includeOverrides: false,
  overrideActivityType: null,
  overrideMaxResidents: null,
  overrideSupervision: null,
};

// ============================================================================
// Subcomponents
// ============================================================================

interface TemplatePreviewCardProps {
  template: RotationTemplate;
  newName: string;
}

function TemplatePreviewCard({ template, newName }: TemplatePreviewCardProps) {
  const config = getActivityTypeConfig(template.activity_type as ActivityType);

  return (
    <div className="flex items-center gap-3 p-3 bg-slate-900/50 rounded-lg">
      {template.background_color && (
        <span
          className="w-4 h-4 rounded flex-shrink-0"
          style={{ backgroundColor: template.background_color }}
        />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-sm text-slate-400 line-through truncate">
            {template.name}
          </span>
          <span className="text-slate-600">→</span>
          <span className="text-sm text-white font-medium truncate">
            {newName}
          </span>
        </div>
        <span className={`text-xs ${config.color}`}>{config.label}</span>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DuplicateTemplateModal({
  isOpen,
  templates,
  onClose,
  onDuplicate,
  isDuplicating = false,
}: DuplicateTemplateModalProps) {
  const [config, setConfig] = useState<DuplicateConfig>(DEFAULT_CONFIG);
  const [showOverrides, setShowOverrides] = useState(false);

  // Generate new names based on pattern
  const generateNewName = useCallback(
    (originalName: string): string => {
      switch (config.namingPattern) {
        case 'copy':
          return `${originalName} (Copy)`;
        case 'suffix':
          return config.suffix ? `${originalName}${config.suffix}` : originalName;
        case 'prefix':
          return config.prefix ? `${config.prefix}${originalName}` : originalName;
        default:
          return `${originalName} (Copy)`;
      }
    },
    [config.namingPattern, config.suffix, config.prefix]
  );

  // Preview of templates to be created
  const previewTemplates = useMemo(
    () =>
      templates.map((t) => ({
        original: t,
        newName: generateNewName(t.name),
      })),
    [templates, generateNewName]
  );

  // Check for duplicate names
  const duplicateNames = useMemo(() => {
    const names = previewTemplates.map((p) => p.newName.toLowerCase());
    const seen = new Set<string>();
    const duplicates = new Set<string>();

    names.forEach((name) => {
      if (seen.has(name)) {
        duplicates.add(name);
      }
      seen.add(name);
    });

    return duplicates;
  }, [previewTemplates]);

  const hasErrors = duplicateNames.size > 0;

  const handleConfigChange = useCallback(
    (updates: Partial<DuplicateConfig>) => {
      setConfig((prev) => ({ ...prev, ...updates }));
    },
    []
  );

  const handleDuplicate = useCallback(async () => {
    if (hasErrors || isDuplicating) return;

    const newTemplates: TemplateCreateRequest[] = templates.map((t) => {
      const base: TemplateCreateRequest = {
        name: generateNewName(t.name),
        activity_type: config.overrideActivityType || t.activity_type,
        abbreviation: t.abbreviation,
        display_abbreviation: t.display_abbreviation,
        font_color: t.font_color,
        background_color: t.background_color,
        clinic_location: t.clinic_location,
        max_residents:
          config.overrideMaxResidents !== null
            ? config.overrideMaxResidents
            : t.max_residents,
        requires_specialty: t.requires_specialty,
        requires_procedure_credential: t.requires_procedure_credential,
        supervision_required:
          config.overrideSupervision !== null
            ? config.overrideSupervision
            : t.supervision_required,
        max_supervision_ratio: t.max_supervision_ratio,
      };

      return base;
    });

    await onDuplicate(newTemplates);
  }, [templates, config, generateNewName, hasErrors, isDuplicating, onDuplicate]);

  const handleClose = useCallback(() => {
    if (isDuplicating) return;
    onClose();
    // Reset config
    setConfig(DEFAULT_CONFIG);
    setShowOverrides(false);
  }, [isDuplicating, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="duplicate-modal-title"
    >
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-violet-500/20 rounded-lg">
              <Copy className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h2 id="duplicate-modal-title" className="text-lg font-semibold text-white">
                Duplicate Templates
              </h2>
              <p className="text-sm text-slate-400 mt-0.5">
                Creating {templates.length} cop{templates.length !== 1 ? 'ies' : 'y'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={isDuplicating}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Naming pattern */}
          <div className="p-4 bg-slate-900/50 rounded-lg">
            <h3 className="text-sm font-medium text-white mb-3">Naming Pattern</h3>

            <div className="space-y-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="namingPattern"
                  value="copy"
                  checked={config.namingPattern === 'copy'}
                  onChange={() => handleConfigChange({ namingPattern: 'copy' })}
                  className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                />
                <span className="text-sm text-slate-300">
                  Add &quot;(Copy)&quot; suffix
                </span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="namingPattern"
                  value="suffix"
                  checked={config.namingPattern === 'suffix'}
                  onChange={() => handleConfigChange({ namingPattern: 'suffix' })}
                  className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                />
                <span className="text-sm text-slate-300">Custom suffix:</span>
                <input
                  type="text"
                  value={config.suffix}
                  onChange={(e) => handleConfigChange({ suffix: e.target.value })}
                  placeholder=" - New"
                  disabled={config.namingPattern !== 'suffix'}
                  className="flex-1 max-w-40 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm placeholder-slate-500 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="namingPattern"
                  value="prefix"
                  checked={config.namingPattern === 'prefix'}
                  onChange={() => handleConfigChange({ namingPattern: 'prefix' })}
                  className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                />
                <span className="text-sm text-slate-300">Custom prefix:</span>
                <input
                  type="text"
                  value={config.prefix}
                  onChange={(e) => handleConfigChange({ prefix: e.target.value })}
                  placeholder="Copy of "
                  disabled={config.namingPattern !== 'prefix'}
                  className="flex-1 max-w-40 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm placeholder-slate-500 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </label>
            </div>
          </div>

          {/* Property overrides */}
          <div className="p-4 bg-slate-900/50 rounded-lg">
            <button
              type="button"
              onClick={() => setShowOverrides(!showOverrides)}
              className="w-full flex items-center justify-between"
            >
              <h3 className="text-sm font-medium text-white">Property Overrides</h3>
              {showOverrides ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            {showOverrides && (
              <div className="mt-3 space-y-3 pt-3 border-t border-slate-700/50">
                <div className="flex items-start gap-2 p-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-blue-300">
                    Override properties will be applied to all duplicated templates.
                    Leave empty to keep original values.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      Activity Type
                    </label>
                    <select
                      value={config.overrideActivityType || ''}
                      onChange={(e) =>
                        handleConfigChange({
                          overrideActivityType: (e.target.value as ActivityType) || null,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                    >
                      <option value="">Keep original</option>
                      {ACTIVITY_TYPE_CONFIGS.map((c) => (
                        <option key={c.type} value={c.type}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      Max Residents
                    </label>
                    <input
                      type="number"
                      value={config.overrideMaxResidents ?? ''}
                      onChange={(e) =>
                        handleConfigChange({
                          overrideMaxResidents: e.target.value
                            ? parseInt(e.target.value)
                            : null,
                        })
                      }
                      placeholder="Keep original"
                      min={1}
                      max={50}
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-xs font-medium text-slate-400 mb-2">
                      Supervision Required
                    </label>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="supervision"
                          checked={config.overrideSupervision === null}
                          onChange={() =>
                            handleConfigChange({ overrideSupervision: null })
                          }
                          className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                        />
                        <span className="text-sm text-slate-300">Keep original</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="supervision"
                          checked={config.overrideSupervision === true}
                          onChange={() =>
                            handleConfigChange({ overrideSupervision: true })
                          }
                          className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                        />
                        <span className="text-sm text-slate-300">Required</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="supervision"
                          checked={config.overrideSupervision === false}
                          onChange={() =>
                            handleConfigChange({ overrideSupervision: false })
                          }
                          className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                        />
                        <span className="text-sm text-slate-300">Not Required</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Preview */}
          <div>
            <h3 className="text-sm font-medium text-slate-400 mb-2">Preview</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {previewTemplates.map(({ original, newName }) => (
                <TemplatePreviewCard
                  key={original.id}
                  template={original}
                  newName={newName}
                />
              ))}
            </div>
          </div>

          {/* Errors */}
          {hasErrors && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-red-300">
                  <p className="font-medium">Duplicate names detected</p>
                  <p className="text-xs mt-1">
                    Please choose a different naming pattern to avoid conflicts.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-700">
          <button
            type="button"
            onClick={handleClose}
            disabled={isDuplicating}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDuplicate}
            disabled={hasErrors || isDuplicating}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDuplicating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Duplicating...
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Duplicate {templates.length} Template{templates.length !== 1 ? 's' : ''}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DuplicateTemplateModal;
