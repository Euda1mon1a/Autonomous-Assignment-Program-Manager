'use client';

/**
 * CallBulkActionsToolbar Component
 *
 * Floating toolbar that appears when call assignments are selected, providing
 * bulk operations like reassign, apply PCAT rules, and delete.
 */
import React, { useState } from 'react';
import {
  Trash2,
  UserPlus,
  X,
  AlertTriangle,
  Loader2,
  ChevronDown,
  Clock,
  XCircle,
} from 'lucide-react';
import type { CallBulkActionType } from '@/types/faculty-call';
import type { Person } from '@/types/api';

// ============================================================================
// Types
// ============================================================================

export interface CallBulkActionsToolbarProps {
  /** Number of selected assignments */
  selectedCount: number;
  /** Callback to clear selection */
  onClearSelection: () => void;
  /** Callback for bulk delete (optional - hide delete button if not provided) */
  onBulkDelete?: () => void;
  /** Callback for bulk reassign */
  onBulkReassign: (personId: string) => void;
  /** Callback for applying PCAT rules */
  onApplyPCAT: () => void;
  /** Callback for clearing PCAT status */
  onClearPCAT: () => void;
  /** Whether any bulk action is pending */
  isPending?: boolean;
  /** Current action being performed */
  pendingAction?: CallBulkActionType | null;
  /** List of people available for reassignment */
  availablePeople?: Person[];
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

interface ReassignDropdownProps {
  isOpen: boolean;
  onToggle: () => void;
  availablePeople: Person[];
  onSelect: (personId: string) => void;
}

function ReassignDropdown({
  isOpen,
  onToggle,
  availablePeople,
  onSelect,
}: ReassignDropdownProps) {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <UserPlus className="w-4 h-4" />
        Reassign
        <ChevronDown
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-0 mb-1 w-64 max-h-60 overflow-y-auto bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10">
          <div className="py-1">
            {availablePeople.length === 0 ? (
              <div className="px-3 py-2 text-sm text-slate-400">
                No people available
              </div>
            ) : (
              availablePeople.map((person) => (
                <button
                  key={person.id}
                  onClick={() => onSelect(person.id)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors text-left"
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  {person.name}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function CallBulkActionsToolbar({
  selectedCount,
  onClearSelection,
  onBulkDelete,
  onBulkReassign,
  onApplyPCAT,
  onClearPCAT,
  isPending = false,
  pendingAction = null,
  availablePeople = [],
}: CallBulkActionsToolbarProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showPCATConfirm, setShowPCATConfirm] = useState(false);
  const [showClearPCATConfirm, setShowClearPCATConfirm] = useState(false);
  const [showReassignDropdown, setShowReassignDropdown] = useState(false);

  // Don't render if nothing selected
  if (selectedCount === 0) {
    return null;
  }

  const handleDelete = () => {
    onBulkDelete?.();
    setShowDeleteConfirm(false);
  };

  const handleApplyPCAT = () => {
    onApplyPCAT();
    setShowPCATConfirm(false);
  };

  const handleClearPCAT = () => {
    onClearPCAT();
    setShowClearPCATConfirm(false);
  };

  const handleReassignSelect = (personId: string) => {
    onBulkReassign(personId);
    setShowReassignDropdown(false);
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

          {/* Reassign dropdown */}
          <ReassignDropdown
            isOpen={showReassignDropdown}
            onToggle={() => setShowReassignDropdown(!showReassignDropdown)}
            availablePeople={availablePeople}
            onSelect={handleReassignSelect}
          />

          {/* Apply PCAT button */}
          <button
            onClick={() => setShowPCATConfirm(true)}
            disabled={isPending && pendingAction === 'apply_pcat'}
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isPending && pendingAction === 'apply_pcat' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Clock className="w-4 h-4" />
            )}
            Apply PCAT Rules
          </button>

          {/* Clear PCAT button */}
          <button
            onClick={() => setShowClearPCATConfirm(true)}
            disabled={isPending && pendingAction === 'clear_pcat'}
            className="flex items-center gap-1.5 px-3 py-2 bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isPending && pendingAction === 'clear_pcat' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <XCircle className="w-4 h-4" />
            )}
            Clear PCAT
          </button>

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
          title="Delete Call Assignments"
          message={`Are you sure you want to delete ${selectedCount} call assignment${selectedCount !== 1 ? 's' : ''}? This action cannot be undone.`}
          isDangerous
          confirmLabel="Delete"
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
          isPending={isPending && pendingAction === 'delete'}
        />
      )}

      {/* Apply PCAT confirmation modal */}
      {showPCATConfirm && (
        <ConfirmModal
          title="Apply PCAT Rules"
          message={`This will apply Post-Call Availability Tracking rules to ${selectedCount} call assignment${selectedCount !== 1 ? 's' : ''}. Post-call status will be updated based on institutional policies.`}
          confirmLabel="Apply PCAT"
          onConfirm={handleApplyPCAT}
          onCancel={() => setShowPCATConfirm(false)}
          isPending={isPending && pendingAction === 'apply_pcat'}
        />
      )}

      {/* Clear PCAT confirmation modal */}
      {showClearPCATConfirm && (
        <ConfirmModal
          title="Clear PCAT Status"
          message={`This will clear the post-call status for ${selectedCount} call assignment${selectedCount !== 1 ? 's' : ''}. They will be marked as available.`}
          confirmLabel="Clear Status"
          onConfirm={handleClearPCAT}
          onCancel={() => setShowClearPCATConfirm(false)}
          isPending={isPending && pendingAction === 'clear_pcat'}
        />
      )}
    </>
  );
}

export default CallBulkActionsToolbar;
