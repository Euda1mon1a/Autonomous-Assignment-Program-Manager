'use client';

/**
 * ArchivedTemplatesDrawer Component
 *
 * Slide-out drawer showing archived templates with restore functionality.
 * Provides a way to view and restore soft-deleted templates.
 */
import React, { useState, useCallback } from 'react';
import {
  X,
  Archive,
  RotateCcw,
  Trash2,
  Search,
  Loader2,
  AlertTriangle,
  Calendar,
} from 'lucide-react';
import type {
  RotationTemplate,
  ActivityType,
} from '@/types/admin-templates';
import { getActivityTypeConfig } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface ArchivedTemplatesDrawerProps {
  /** Whether drawer is open */
  isOpen: boolean;
  /** Archived templates */
  templates: RotationTemplate[];
  /** Whether loading */
  isLoading?: boolean;
  /** Callback to close drawer */
  onClose: () => void;
  /** Callback to restore templates */
  onRestore: (templateIds: string[]) => Promise<void>;
  /** Callback to permanently delete */
  onPermanentDelete?: (templateIds: string[]) => Promise<void>;
  /** Whether restore is in progress */
  isRestoring?: boolean;
  /** Whether delete is in progress */
  isDeleting?: boolean;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface ArchivedTemplateRowProps {
  template: RotationTemplate;
  isSelected: boolean;
  onToggleSelect: () => void;
  onRestore: () => void;
  onDelete?: () => void;
  isRestoring?: boolean;
}

function ArchivedTemplateRow({
  template,
  isSelected,
  onToggleSelect,
  onRestore,
  onDelete,
  isRestoring = false,
}: ArchivedTemplateRowProps) {
  const config = getActivityTypeConfig(template.activityType as ActivityType);

  return (
    <div
      className={`
        flex items-center gap-3 p-3 border rounded-lg transition-colors
        ${isSelected ? 'bg-violet-500/10 border-violet-500/30' : 'border-slate-700 hover:bg-slate-700/30'}
      `}
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={onToggleSelect}
        disabled={isRestoring}
        className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
        aria-label={`Select ${template.name}`}
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {template.backgroundColor && (
            <span
              className="w-3 h-3 rounded flex-shrink-0"
              style={{ backgroundColor: template.backgroundColor }}
            />
          )}
          <span className="text-white font-medium truncate">{template.name}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className={`text-xs ${config.color}`}>{config.label}</span>
          <span className="text-xs text-slate-500">•</span>
          <span className="text-xs text-slate-400">
            Archived {new Date(template.createdAt).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={onRestore}
          disabled={isRestoring}
          className="p-1.5 text-emerald-400 hover:text-emerald-300 transition-colors disabled:opacity-50"
          title="Restore template"
          aria-label="Restore"
        >
          {isRestoring ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RotateCcw className="w-4 h-4" />
          )}
        </button>
        {onDelete && (
          <button
            onClick={onDelete}
            disabled={isRestoring}
            className="p-1.5 text-slate-400 hover:text-red-400 transition-colors disabled:opacity-50"
            title="Permanently delete"
            aria-label="Delete permanently"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ArchivedTemplatesDrawer({
  isOpen,
  templates,
  isLoading = false,
  onClose,
  onRestore,
  onPermanentDelete,
  isRestoring = false,
  isDeleting = false,
}: ArchivedTemplatesDrawerProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Filter templates by search
  const filteredTemplates = templates.filter(
    (t) =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.activityType.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedIds.size === filteredTemplates.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredTemplates.map((t) => t.id)));
    }
  }, [filteredTemplates, selectedIds.size]);

  const handleRestoreSelected = useCallback(async () => {
    if (selectedIds.size === 0) return;
    await onRestore(Array.from(selectedIds));
    setSelectedIds(new Set());
  }, [selectedIds, onRestore]);

  const handleRestoreSingle = useCallback(
    async (id: string) => {
      await onRestore([id]);
    },
    [onRestore]
  );

  const handleDeleteSelected = useCallback(async () => {
    if (!onPermanentDelete || selectedIds.size === 0) return;
    await onPermanentDelete(Array.from(selectedIds));
    setSelectedIds(new Set());
    setShowDeleteConfirm(false);
  }, [selectedIds, onPermanentDelete]);

  const handleClose = useCallback(() => {
    if (isRestoring || isDeleting) return;
    onClose();
    setSelectedIds(new Set());
    setSearchQuery('');
    setShowDeleteConfirm(false);
  }, [isRestoring, isDeleting, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40 transition-opacity"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-slate-800 border-l border-slate-700 shadow-2xl flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Archive className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h2 id="drawer-title" className="text-lg font-semibold text-white">
                Archived Templates
              </h2>
              <p className="text-sm text-slate-400">
                {templates.length} template{templates.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isRestoring || isDeleting}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-slate-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search archived templates..."
              className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
        </div>

        {/* Selection actions */}
        {selectedIds.size > 0 && (
          <div className="flex items-center justify-between px-4 py-2 bg-violet-500/10 border-b border-violet-500/30">
            <span className="text-sm text-violet-300">
              {selectedIds.size} selected
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRestoreSelected}
                disabled={isRestoring}
                className="flex items-center gap-1.5 px-3 py-1 text-sm text-emerald-400 hover:text-emerald-300 transition-colors disabled:opacity-50"
              >
                {isRestoring ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RotateCcw className="w-3 h-3" />
                )}
                Restore
              </button>
              {onPermanentDelete && (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  disabled={isDeleting}
                  className="flex items-center gap-1.5 px-3 py-1 text-sm text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-3 h-3" />
                  Delete
                </button>
              )}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
            </div>
          ) : filteredTemplates.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-center">
              <Calendar className="w-10 h-10 text-slate-600 mb-3" />
              <p className="text-slate-400">
                {templates.length === 0
                  ? 'No archived templates'
                  : 'No templates match your search'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Select all */}
              {filteredTemplates.length > 1 && (
                <div className="flex items-center gap-2 pb-2 mb-2 border-b border-slate-700/50">
                  <input
                    type="checkbox"
                    checked={selectedIds.size === filteredTemplates.length}
                    onChange={handleSelectAll}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                  />
                  <span className="text-sm text-slate-400">
                    Select all ({filteredTemplates.length})
                  </span>
                </div>
              )}

              {filteredTemplates.map((template) => (
                <ArchivedTemplateRow
                  key={template.id}
                  template={template}
                  isSelected={selectedIds.has(template.id)}
                  onToggleSelect={() => handleToggleSelect(template.id)}
                  onRestore={() => handleRestoreSingle(template.id)}
                  onDelete={
                    onPermanentDelete
                      ? () => {
                          setSelectedIds(new Set([template.id]));
                          setShowDeleteConfirm(true);
                        }
                      : undefined
                  }
                  isRestoring={isRestoring}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-white">
                Permanently Delete?
              </h3>
            </div>

            <p className="text-slate-300 mb-6">
              This will permanently delete {selectedIds.size} template
              {selectedIds.size !== 1 ? 's' : ''}. This action cannot be undone.
            </p>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteSelected}
                disabled={isDeleting}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete Forever
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default ArchivedTemplatesDrawer;
