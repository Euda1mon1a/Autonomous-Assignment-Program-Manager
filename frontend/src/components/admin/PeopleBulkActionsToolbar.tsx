'use client';

/**
 * PeopleBulkActionsToolbar Component
 *
 * Fixed toolbar that appears when people are selected, showing bulk action options.
 * Follows the dark theme pattern from admin pages.
 */
import { useState } from 'react';
import {
  X,
  Trash2,
  GraduationCap,
  UserCog,
  Loader2,
  ChevronDown,
} from 'lucide-react';
import type { PersonType } from '@/hooks/usePeople';

// ============================================================================
// Types
// ============================================================================

type BulkActionType = 'delete' | 'update_pgy' | 'update_type';

export interface PeopleBulkActionsToolbarProps {
  /** Number of selected people */
  selectedCount: number;
  /** Callback to clear selection */
  onClearSelection: () => void;
  /** Callback for bulk delete */
  onBulkDelete: () => void;
  /** Callback for bulk PGY level update */
  onBulkUpdatePGY: (pgyLevel: number) => void;
  /** Callback for bulk type update */
  onBulkUpdateType: (type: PersonType) => void;
  /** Whether an action is in progress */
  isPending: boolean;
  /** Which action is currently pending */
  pendingAction: BulkActionType | null;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface DropdownProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

function Dropdown({ trigger, children, isOpen, onOpenChange }: DropdownProps) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => onOpenChange(!isOpen)}
        className="flex items-center"
      >
        {trigger}
      </button>
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => onOpenChange(false)}
          />
          <div className="absolute bottom-full left-0 mb-2 z-50 bg-slate-700 border border-slate-600 rounded-lg shadow-xl py-1 min-w-[160px]">
            {children}
          </div>
        </>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function PeopleBulkActionsToolbar({
  selectedCount,
  onClearSelection,
  onBulkDelete,
  onBulkUpdatePGY,
  onBulkUpdateType,
  isPending,
  pendingAction,
}: PeopleBulkActionsToolbarProps) {
  const [pgyDropdownOpen, setPgyDropdownOpen] = useState(false);
  const [typeDropdownOpen, setTypeDropdownOpen] = useState(false);

  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-0 inset-x-0 z-40">
      <div className="max-w-7xl mx-auto px-4 pb-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl p-4">
          <div className="flex items-center justify-between">
            {/* Selection Count */}
            <div className="flex items-center gap-4">
              <button
                onClick={onClearSelection}
                disabled={isPending}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors disabled:opacity-50"
                title="Clear selection"
              >
                <X className="w-5 h-5" />
              </button>
              <span className="text-sm font-medium text-white">
                {selectedCount} {selectedCount === 1 ? 'person' : 'people'} selected
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* Update PGY Level Dropdown */}
              <Dropdown
                isOpen={pgyDropdownOpen}
                onOpenChange={setPgyDropdownOpen}
                trigger={
                  <span className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                    {pendingAction === 'update_pgy' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <GraduationCap className="w-4 h-4" />
                    )}
                    Set PGY
                    <ChevronDown className="w-4 h-4" />
                  </span>
                }
              >
                {[1, 2, 3, 4, 5].map((level) => (
                  <button
                    key={level}
                    onClick={() => {
                      setPgyDropdownOpen(false);
                      onBulkUpdatePGY(level);
                    }}
                    disabled={isPending}
                    className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-600 disabled:opacity-50"
                  >
                    PGY-{level}
                  </button>
                ))}
              </Dropdown>

              {/* Update Type Dropdown */}
              <Dropdown
                isOpen={typeDropdownOpen}
                onOpenChange={setTypeDropdownOpen}
                trigger={
                  <span className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                    {pendingAction === 'update_type' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <UserCog className="w-4 h-4" />
                    )}
                    Set Type
                    <ChevronDown className="w-4 h-4" />
                  </span>
                }
              >
                <button
                  onClick={() => {
                    setTypeDropdownOpen(false);
                    onBulkUpdateType('resident');
                  }}
                  disabled={isPending}
                  className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-600 disabled:opacity-50"
                >
                  Resident
                </button>
                <button
                  onClick={() => {
                    setTypeDropdownOpen(false);
                    onBulkUpdateType('faculty');
                  }}
                  disabled={isPending}
                  className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-600 disabled:opacity-50"
                >
                  Faculty
                </button>
              </Dropdown>

              {/* Delete Button */}
              <button
                onClick={onBulkDelete}
                disabled={isPending}
                className="flex items-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                {pendingAction === 'delete' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
