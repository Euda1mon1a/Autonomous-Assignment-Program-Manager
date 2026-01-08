'use client';

/**
 * BulkActionsToolbar Component
 *
 * Floating toolbar that appears when templates are selected, providing
 * bulk operations like delete and property updates.
 */
import React, { useState } from 'react';
import {
  Trash2,
  Edit2,
  X,
  AlertTriangle,
  Loader2,
  ChevronDown,
  Calendar,
} from 'lucide-react';
import type {
  ActivityType,
  BulkActionType,
} from '@/types/admin-templates';
import { ACTIVITY_TYPE_CONFIGS } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface BulkActionsToolbarProps {
  /** Number of selected templates */
  selectedCount: number;
  /** Callback to clear selection */
  onClearSelection: () => void;
  /** Callback for bulk delete */
  onBulkDelete: () => void;
  /** Callback for bulk activity type update */
  onBulkUpdateActivityType: (activityType: ActivityType) => void;
  /** Callback for bulk supervision update */
  onBulkUpdateSupervision: (required: boolean) => void;
  /** Callback for bulk max residents update */
  onBulkUpdateMaxResidents: (maxResidents: number) => void;
  /** Callback for bulk pattern editing */
  onBulkEditPatterns?: () => void;
  /** Whether any bulk action is pending */
  isPending?: boolean;
  /** Current action being performed */
  pendingAction?: BulkActionType | null;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface ConfirmModalProps {
  title: string;
  message: string;
  isDangerous?: boolean;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isPending?: boolean;
}

function ConfirmModal({
  title,
  message,
  isDangerous = false,
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
  isPending = false,
}: ConfirmModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-md w-full p-6">
        <div className="flex items-center gap-3 mb-4">
          <div
            className={`p-2 rounded-lg ${isDangerous ? 'bg-red-500/20' : 'bg-amber-500/20'}`}
          >
            <AlertTriangle
              className={`w-5 h-5 ${isDangerous ? 'text-red-400' : 'text-amber-400'}`}
            />
          </div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>

        <p className="text-slate-300 mb-6">{message}</p>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={isPending}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isPending}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
              ${
                isDangerous
                  ? 'bg-red-600 hover:bg-red-500 text-white'
                  : 'bg-violet-600 hover:bg-violet-500 text-white'
              }
            `}
          >
            {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

interface DropdownMenuProps {
  label: string;
  children: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
}

function DropdownMenu({ label, children, isOpen, onToggle }: DropdownMenuProps) {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <Edit2 className="w-4 h-4" />
        {label}
        <ChevronDown
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10">
          {children}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function BulkActionsToolbar({
  selectedCount,
  onClearSelection,
  onBulkDelete,
  onBulkUpdateActivityType,
  onBulkUpdateSupervision,
  onBulkUpdateMaxResidents,
  onBulkEditPatterns,
  isPending = false,
  pendingAction = null,
}: BulkActionsToolbarProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [showMaxResidentsModal, setShowMaxResidentsModal] = useState(false);
  const [maxResidentsValue, setMaxResidentsValue] = useState<number>(4);

  // Don't render if nothing selected
  if (selectedCount === 0) {
    return null;
  }

  const handleDelete = () => {
    onBulkDelete();
    setShowDeleteConfirm(false);
  };

  const handleActivityTypeSelect = (type: ActivityType) => {
    onBulkUpdateActivityType(type);
    setOpenDropdown(null);
  };

  const handleSupervisionSelect = (required: boolean) => {
    onBulkUpdateSupervision(required);
    setOpenDropdown(null);
  };

  const handleMaxResidentsConfirm = () => {
    onBulkUpdateMaxResidents(maxResidentsValue);
    setShowMaxResidentsModal(false);
  };

  return (
    <>
      {/* Floating toolbar */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40">
        <div className="flex items-center gap-3 px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl">
          {/* Selection count */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-violet-500/20 text-violet-300 rounded-lg text-sm font-medium">
            <span>{selectedCount}</span>
            <span>selected</span>
          </div>

          <div className="w-px h-8 bg-slate-700" />

          {/* Activity Type dropdown */}
          <DropdownMenu
            label="Activity Type"
            isOpen={openDropdown === 'activity'}
            onToggle={() =>
              setOpenDropdown(openDropdown === 'activity' ? null : 'activity')
            }
          >
            <div className="py-1">
              {ACTIVITY_TYPE_CONFIGS.map((config) => (
                <button
                  key={config.type}
                  onClick={() => handleActivityTypeSelect(config.type)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  <span
                    className={`w-2 h-2 rounded-full ${config.bgColor.replace('/20', '')}`}
                  />
                  {config.label}
                </button>
              ))}
            </div>
          </DropdownMenu>

          {/* Supervision dropdown */}
          <DropdownMenu
            label="Supervision"
            isOpen={openDropdown === 'supervision'}
            onToggle={() =>
              setOpenDropdown(
                openDropdown === 'supervision' ? null : 'supervision'
              )
            }
          >
            <div className="py-1">
              <button
                onClick={() => handleSupervisionSelect(true)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Required
              </button>
              <button
                onClick={() => handleSupervisionSelect(false)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
              >
                <span className="w-2 h-2 rounded-full bg-slate-500" />
                Not Required
              </button>
            </div>
          </DropdownMenu>

          {/* Max Residents button */}
          <button
            onClick={() => setShowMaxResidentsModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Edit2 className="w-4 h-4" />
            Max Residents
          </button>

          {/* Edit Patterns button */}
          {onBulkEditPatterns && (
            <button
              onClick={onBulkEditPatterns}
              className="flex items-center gap-1.5 px-3 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Calendar className="w-4 h-4" />
              Edit Patterns
            </button>
          )}

          <div className="w-px h-8 bg-slate-700" />

          {/* Delete button */}
          <button
            onClick={() => setShowDeleteConfirm(true)}
            disabled={isPending && pendingAction === 'delete'}
            className="flex items-center gap-1.5 px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isPending && pendingAction === 'delete' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
            Delete
          </button>

          <div className="w-px h-8 bg-slate-700" />

          {/* Clear selection */}
          <button
            onClick={onClearSelection}
            className="p-2 text-slate-400 hover:text-white transition-colors"
            title="Clear selection"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <ConfirmModal
          title="Delete Templates"
          message={`Are you sure you want to delete ${selectedCount} template${selectedCount !== 1 ? 's' : ''}? This action cannot be undone.`}
          isDangerous
          confirmLabel="Delete"
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
          isPending={isPending && pendingAction === 'delete'}
        />
      )}

      {/* Max Residents modal */}
      {showMaxResidentsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-sm w-full p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              Set Max Residents
            </h3>

            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Maximum Residents
              </label>
              <input
                type="number"
                value={maxResidentsValue}
                onChange={(e) =>
                  setMaxResidentsValue(Math.max(1, parseInt(e.target.value) || 1))
                }
                min={1}
                max={20}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              />
              <p className="mt-1 text-xs text-slate-500">
                This will update {selectedCount} template
                {selectedCount !== 1 ? 's' : ''}
              </p>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowMaxResidentsModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleMaxResidentsConfirm}
                disabled={isPending}
                className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                {isPending && pendingAction === 'update_max_residents' && (
                  <Loader2 className="w-4 h-4 animate-spin" />
                )}
                Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default BulkActionsToolbar;
