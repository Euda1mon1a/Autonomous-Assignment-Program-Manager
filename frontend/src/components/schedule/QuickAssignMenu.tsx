'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { useRotationTemplates, useDeleteAssignment } from '@/lib/hooks';
import type { Assignment, RotationTemplate } from '@/types/api';
import {
  Clock,
  Edit3,
  Trash2,
  X,
  Calendar,
  ChevronRight,
  History,
  Loader2,
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface QuickAssignMenuProps {
  isOpen: boolean;
  onClose: () => void;
  position: { x: number; y: number };
  personId: string;
  personName?: string;
  date: string;
  session: 'AM' | 'PM';
  blockId?: string;
  assignment?: Assignment | null;
  recentRotations?: string[]; // IDs of recently used rotations
  onQuickAssign?: (rotationTemplateId: string) => void;
  onMarkAsOff?: () => void;
  onClearAssignment?: () => void;
  onEditDetails?: () => void;
}

interface MenuItemProps {
  icon?: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
  loading?: boolean;
}

// ============================================================================
// Menu Item Component
// ============================================================================

function MenuItem({ icon, label, onClick, disabled, danger, loading }: MenuItemProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        w-full flex items-center gap-3 px-3 py-2 text-sm text-left
        transition-colors duration-150
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${danger
          ? 'text-red-700 hover:bg-red-50'
          : 'text-gray-700 hover:bg-gray-100'
        }
      `}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : icon ? (
        <span className="w-4 h-4 flex items-center justify-center">{icon}</span>
      ) : (
        <span className="w-4 h-4" />
      )}
      <span className="flex-1">{label}</span>
    </button>
  );
}

// ============================================================================
// Rotation Submenu
// ============================================================================

interface RotationSubmenuProps {
  rotations: RotationTemplate[];
  recentRotationIds: string[];
  onSelect: (rotationId: string) => void;
  isLoading: boolean;
}

function RotationSubmenu({
  rotations,
  recentRotationIds,
  onSelect,
  isLoading,
}: RotationSubmenuProps) {
  // Get recent rotations (top 5)
  const recentRotations = recentRotationIds
    .slice(0, 5)
    .map((id) => rotations.find((r) => r.id === id))
    .filter((r): r is RotationTemplate => r !== undefined);

  // Get remaining rotations for "All" section
  const otherRotations = rotations.filter(
    (r) => !recentRotationIds.includes(r.id)
  );

  if (isLoading) {
    return (
      <div className="p-4 text-center text-sm text-gray-500">
        <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
        Loading rotations...
      </div>
    );
  }

  return (
    <div className="max-h-64 overflow-y-auto">
      {/* Recent rotations */}
      {recentRotations.length > 0 && (
        <>
          <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide bg-gray-50">
            <div className="flex items-center gap-1.5">
              <History className="w-3 h-3" />
              Recent
            </div>
          </div>
          {recentRotations.map((rotation) => (
            <button
              key={rotation.id}
              onClick={() => onSelect(rotation.id)}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left text-gray-700 hover:bg-gray-100"
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{
                  backgroundColor: getActivityColor(rotation.activity_type),
                }}
              />
              <span className="truncate">
                {rotation.abbreviation || rotation.name}
              </span>
            </button>
          ))}
        </>
      )}

      {/* Separator */}
      {recentRotations.length > 0 && otherRotations.length > 0 && (
        <div className="border-t border-gray-200 my-1" />
      )}

      {/* All rotations */}
      {otherRotations.length > 0 && (
        <>
          <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide bg-gray-50">
            All Rotations
          </div>
          {otherRotations.map((rotation) => (
            <button
              key={rotation.id}
              onClick={() => onSelect(rotation.id)}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left text-gray-700 hover:bg-gray-100"
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{
                  backgroundColor: getActivityColor(rotation.activity_type),
                }}
              />
              <span className="truncate">
                {rotation.abbreviation || rotation.name}
              </span>
            </button>
          ))}
        </>
      )}

      {rotations.length === 0 && (
        <div className="p-4 text-center text-sm text-gray-500">
          No rotations available
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function getActivityColor(activityType: string): string {
  const colors: Record<string, string> = {
    clinic: '#3B82F6', // blue
    inpatient: '#10B981', // green
    call: '#F59E0B', // amber
    leave: '#6B7280', // gray
    conference: '#8B5CF6', // purple
    procedure: '#EF4444', // red
    admin: '#64748B', // slate
  };
  return colors[activityType.toLowerCase()] || '#9CA3AF';
}

// ============================================================================
// Main Component
// ============================================================================

export function QuickAssignMenu({
  isOpen,
  onClose,
  position,
  personId,
  personName,
  date,
  session,
  blockId,
  assignment,
  recentRotations = [],
  onQuickAssign,
  onMarkAsOff,
  onClearAssignment,
  onEditDetails,
}: QuickAssignMenuProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const canEdit = user?.role === 'admin' || user?.role === 'coordinator';

  const menuRef = useRef<HTMLDivElement>(null);
  const [showRotationSubmenu, setShowRotationSubmenu] = useState(false);
  const [adjustedPosition, setAdjustedPosition] = useState(position);

  // Fetch rotation templates
  const { data: rotationTemplatesData, isLoading: templatesLoading } = useRotationTemplates();
  const deleteAssignment = useDeleteAssignment();

  // Adjust position to stay within viewport
  useEffect(() => {
    if (!isOpen || !menuRef.current) return;

    const menu = menuRef.current;
    const rect = menu.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let newX = position.x;
    let newY = position.y;

    // Adjust horizontal position
    if (position.x + rect.width > viewportWidth - 16) {
      newX = viewportWidth - rect.width - 16;
    }

    // Adjust vertical position
    if (position.y + rect.height > viewportHeight - 16) {
      newY = viewportHeight - rect.height - 16;
    }

    setAdjustedPosition({ x: Math.max(16, newX), y: Math.max(16, newY) });
  }, [isOpen, position]);

  // Close menu on outside click
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  // Reset submenu state when menu closes
  useEffect(() => {
    if (!isOpen) {
      setShowRotationSubmenu(false);
    }
  }, [isOpen]);

  const handleQuickAssign = useCallback(
    (rotationId: string) => {
      onQuickAssign?.(rotationId);
      onClose();
    },
    [onQuickAssign, onClose]
  );

  const handleClearAssignment = useCallback(async () => {
    if (assignment) {
      try {
        await deleteAssignment.mutateAsync(assignment.id);
        onClearAssignment?.();
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Failed to clear assignment');
      }
    }
    onClose();
  }, [assignment, deleteAssignment, onClearAssignment, onClose, toast]);

  const handleEditDetails = useCallback(() => {
    onEditDetails?.();
    onClose();
  }, [onEditDetails, onClose]);

  const handleMarkAsOff = useCallback(() => {
    onMarkAsOff?.();
    onClose();
  }, [onMarkAsOff, onClose]);

  if (!isOpen || !canEdit) {
    return null;
  }

  const rotations = rotationTemplatesData?.items || [];
  const hasAssignment = !!assignment;

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-white rounded-lg shadow-lg border border-gray-200 min-w-[200px] overflow-hidden"
      style={{
        left: adjustedPosition.x,
        top: adjustedPosition.y,
      }}
    >
      {/* Header */}
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-900 truncate max-w-[180px]">
            {personName || 'Unknown'}
          </span>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
          <Calendar className="w-3 h-3" />
          <span>
            {new Date(date).toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            })}
          </span>
          <span>&bull;</span>
          <Clock className="w-3 h-3" />
          <span>{session}</span>
        </div>
      </div>

      {/* Menu Items */}
      <div className="py-1">
        {/* Quick Assign Submenu Toggle */}
        <button
          onClick={() => setShowRotationSubmenu(!showRotationSubmenu)}
          className="w-full flex items-center justify-between gap-3 px-3 py-2 text-sm text-left text-gray-700 hover:bg-gray-100"
        >
          <div className="flex items-center gap-3">
            <Calendar className="w-4 h-4" />
            <span>Quick Assign</span>
          </div>
          <ChevronRight
            className={`w-4 h-4 transition-transform ${
              showRotationSubmenu ? 'rotate-90' : ''
            }`}
          />
        </button>

        {/* Rotation Submenu */}
        {showRotationSubmenu && (
          <div className="border-t border-b border-gray-100 bg-gray-50">
            <RotationSubmenu
              rotations={rotations}
              recentRotationIds={recentRotations}
              onSelect={handleQuickAssign}
              isLoading={templatesLoading}
            />
          </div>
        )}

        <div className="border-t border-gray-200 my-1" />

        {/* Mark as Off */}
        <MenuItem
          icon={<X className="w-4 h-4" />}
          label="Mark as Off"
          onClick={handleMarkAsOff}
        />

        {/* Clear Assignment (only if there's an existing assignment) */}
        {hasAssignment && (
          <MenuItem
            icon={<Trash2 className="w-4 h-4" />}
            label="Clear Assignment"
            onClick={handleClearAssignment}
            danger
            loading={deleteAssignment.isPending}
          />
        )}

        <div className="border-t border-gray-200 my-1" />

        {/* Edit Details */}
        <MenuItem
          icon={<Edit3 className="w-4 h-4" />}
          label="Edit Details..."
          onClick={handleEditDetails}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Hook for Managing Quick Assign Menu State
// ============================================================================

export interface QuickAssignMenuState {
  isOpen: boolean;
  position: { x: number; y: number };
  personId: string;
  personName?: string;
  date: string;
  session: 'AM' | 'PM';
  blockId?: string;
  assignment?: Assignment | null;
}

export function useQuickAssignMenu() {
  const [menuState, setMenuState] = useState<QuickAssignMenuState | null>(null);

  const openMenu = useCallback(
    (
      event: React.MouseEvent | { clientX: number; clientY: number },
      data: Omit<QuickAssignMenuState, 'isOpen' | 'position'>
    ) => {
      // Prevent default context menu
      if ('preventDefault' in event) {
        event.preventDefault();
      }

      setMenuState({
        isOpen: true,
        position: { x: event.clientX, y: event.clientY },
        ...data,
      });
    },
    []
  );

  const closeMenu = useCallback(() => {
    setMenuState(null);
  }, []);

  return {
    menuState,
    openMenu,
    closeMenu,
    isOpen: !!menuState?.isOpen,
  };
}
