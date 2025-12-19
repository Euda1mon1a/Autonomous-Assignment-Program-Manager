'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment,
} from '@/lib/hooks';
import { AssignmentRole, type Assignment, type AssignmentCreate, type AssignmentUpdate } from '@/types/api';

// ============================================================================
// Types
// ============================================================================

export interface CellClickData {
  personId: string;
  personName?: string;
  date: string;
  session: 'AM' | 'PM';
  blockId?: string;
  assignment?: Assignment | null;
}

export interface CellActionHandlers {
  onCellClick: (data: CellClickData) => void;
  onCellRightClick: (event: React.MouseEvent, data: CellClickData) => void;
  onCellLongPress: (event: { clientX: number; clientY: number }, data: CellClickData) => void;
}

export interface UseCellActionsOptions {
  onEditModalOpen?: (data: CellClickData) => void;
  onQuickMenuOpen?: (event: { clientX: number; clientY: number }, data: CellClickData) => void;
  longPressDelay?: number;
}

export interface UseCellActionsReturn {
  handlers: CellActionHandlers;
  canEdit: boolean;
  isLoading: boolean;
  createAssignment: (data: AssignmentCreate) => Promise<Assignment>;
  updateAssignment: (id: string, data: AssignmentUpdate) => Promise<Assignment>;
  deleteAssignment: (id: string) => Promise<void>;
  clearAssignment: (assignmentId: string) => Promise<void>;
  markAsOff: (blockId: string, personId: string) => Promise<void>;
}

// ============================================================================
// Main Hook
// ============================================================================

export function useCellActions(options: UseCellActionsOptions = {}): UseCellActionsReturn {
  const {
    onEditModalOpen,
    onQuickMenuOpen,
    longPressDelay = 500,
  } = options;

  const { user } = useAuth();
  const canEdit = user?.role === 'admin' || user?.role === 'coordinator';

  const createMutation = useCreateAssignment();
  const updateMutation = useUpdateAssignment();
  const deleteMutation = useDeleteAssignment();

  const isLoading =
    createMutation.isPending || updateMutation.isPending || deleteMutation.isPending;

  // Create assignment
  const createAssignment = useCallback(
    async (data: AssignmentCreate): Promise<Assignment> => {
      if (!canEdit) {
        throw new Error('You do not have permission to create assignments');
      }
      return createMutation.mutateAsync(data);
    },
    [canEdit, createMutation]
  );

  // Update assignment
  const updateAssignment = useCallback(
    async (id: string, data: AssignmentUpdate): Promise<Assignment> => {
      if (!canEdit) {
        throw new Error('You do not have permission to update assignments');
      }
      return updateMutation.mutateAsync({ id, data });
    },
    [canEdit, updateMutation]
  );

  // Delete assignment
  const deleteAssignment = useCallback(
    async (id: string): Promise<void> => {
      if (!canEdit) {
        throw new Error('You do not have permission to delete assignments');
      }
      return deleteMutation.mutateAsync(id);
    },
    [canEdit, deleteMutation]
  );

  // Clear assignment (alias for delete)
  const clearAssignment = useCallback(
    async (assignmentId: string): Promise<void> => {
      return deleteAssignment(assignmentId);
    },
    [deleteAssignment]
  );

  // Mark as off (create assignment with off/leave activity)
  const markAsOff = useCallback(
    async (blockId: string, personId: string): Promise<void> => {
      if (!canEdit) {
        throw new Error('You do not have permission to modify assignments');
      }
      // Create an assignment with "off" as activity override
      await createMutation.mutateAsync({
        block_id: blockId,
        person_id: personId,
        role: AssignmentRole.PRIMARY,
        activity_override: 'OFF',
        created_by: user?.id,
      });
    },
    [canEdit, createMutation, user]
  );

  // Click handler - opens edit modal
  const onCellClick = useCallback(
    (data: CellClickData) => {
      if (!canEdit) return;
      onEditModalOpen?.(data);
    },
    [canEdit, onEditModalOpen]
  );

  // Right-click handler - opens quick menu
  const onCellRightClick = useCallback(
    (event: React.MouseEvent, data: CellClickData) => {
      if (!canEdit) return;
      event.preventDefault();
      event.stopPropagation();
      onQuickMenuOpen?.(event, data);
    },
    [canEdit, onQuickMenuOpen]
  );

  // Long press handler - opens quick menu (for touch devices)
  const onCellLongPress = useCallback(
    (event: { clientX: number; clientY: number }, data: CellClickData) => {
      if (!canEdit) return;
      onQuickMenuOpen?.(event, data);
    },
    [canEdit, onQuickMenuOpen]
  );

  return {
    handlers: {
      onCellClick,
      onCellRightClick,
      onCellLongPress,
    },
    canEdit,
    isLoading,
    createAssignment,
    updateAssignment,
    deleteAssignment,
    clearAssignment,
    markAsOff,
  };
}

// ============================================================================
// Long Press Detection Hook
// ============================================================================

export interface UseLongPressOptions {
  onLongPress: (event: { clientX: number; clientY: number }) => void;
  onClick?: () => void;
  delay?: number;
  disabled?: boolean;
}

export interface UseLongPressReturn {
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseUp: () => void;
  onMouseLeave: () => void;
  onTouchStart: (e: React.TouchEvent) => void;
  onTouchEnd: () => void;
}

export function useLongPress({
  onLongPress,
  onClick,
  delay = 500,
  disabled = false,
}: UseLongPressOptions): UseLongPressReturn {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isLongPressRef = useRef(false);
  const positionRef = useRef({ clientX: 0, clientY: 0 });

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startPress = useCallback(
    (clientX: number, clientY: number) => {
      if (disabled) return;

      isLongPressRef.current = false;
      positionRef.current = { clientX, clientY };

      timerRef.current = setTimeout(() => {
        isLongPressRef.current = true;
        onLongPress(positionRef.current);
      }, delay);
    },
    [disabled, delay, onLongPress]
  );

  const endPress = useCallback(() => {
    clearTimer();
    if (!isLongPressRef.current && onClick && !disabled) {
      onClick();
    }
    isLongPressRef.current = false;
  }, [clearTimer, onClick, disabled]);

  // Cleanup on unmount
  useEffect(() => {
    return () => clearTimer();
  }, [clearTimer]);

  return {
    onMouseDown: (e: React.MouseEvent) => startPress(e.clientX, e.clientY),
    onMouseUp: endPress,
    onMouseLeave: () => {
      clearTimer();
      isLongPressRef.current = false;
    },
    onTouchStart: (e: React.TouchEvent) => {
      const touch = e.touches[0];
      startPress(touch.clientX, touch.clientY);
    },
    onTouchEnd: endPress,
  };
}

// ============================================================================
// Schedule Cell Wrapper Component Props
// ============================================================================

export interface ScheduleCellWrapperProps {
  children: React.ReactNode;
  personId: string;
  personName?: string;
  date: string;
  session: 'AM' | 'PM';
  blockId?: string;
  assignment?: Assignment | null;
  onClick?: (data: CellClickData) => void;
  onRightClick?: (event: React.MouseEvent, data: CellClickData) => void;
  onLongPress?: (event: { clientX: number; clientY: number }, data: CellClickData) => void;
  className?: string;
  disabled?: boolean;
}

export function ScheduleCellWrapper({
  children,
  personId,
  personName,
  date,
  session,
  blockId,
  assignment,
  onClick,
  onRightClick,
  onLongPress,
  className = '',
  disabled = false,
}: ScheduleCellWrapperProps) {
  const { user } = useAuth();
  const canEdit = user?.role === 'admin' || user?.role === 'coordinator';
  const isInteractive = canEdit && !disabled;

  const cellData: CellClickData = {
    personId,
    personName,
    date,
    session,
    blockId,
    assignment,
  };

  const longPressHandlers = useLongPress({
    onLongPress: (event) => onLongPress?.(event, cellData),
    onClick: () => onClick?.(cellData),
    disabled: !isInteractive || !onLongPress,
  });

  const handleContextMenu = (e: React.MouseEvent) => {
    if (!isInteractive) return;
    e.preventDefault();
    onRightClick?.(e, cellData);
  };

  return (
    <div
      className={`
        ${className}
        ${isInteractive ? 'cursor-pointer hover:ring-2 hover:ring-blue-300 hover:ring-opacity-50' : ''}
        transition-shadow duration-150
      `}
      onContextMenu={handleContextMenu}
      {...(onLongPress && isInteractive ? longPressHandlers : {})}
      onClick={!onLongPress && isInteractive ? () => onClick?.(cellData) : undefined}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onKeyDown={
        isInteractive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick?.(cellData);
              }
            }
          : undefined
      }
    >
      {children}
    </div>
  );
}

// ============================================================================
// Recent Rotations Storage
// ============================================================================

const RECENT_ROTATIONS_KEY = 'schedule_recent_rotations';
const MAX_RECENT_ROTATIONS = 10;

export function getRecentRotations(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(RECENT_ROTATIONS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

export function addRecentRotation(rotationId: string): void {
  if (typeof window === 'undefined') return;
  try {
    const recent = getRecentRotations();
    // Remove if already exists, then add to front
    const filtered = recent.filter((id) => id !== rotationId);
    const updated = [rotationId, ...filtered].slice(0, MAX_RECENT_ROTATIONS);
    localStorage.setItem(RECENT_ROTATIONS_KEY, JSON.stringify(updated));
  } catch {
    // Silently fail if localStorage is not available
  }
}

export function clearRecentRotations(): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem(RECENT_ROTATIONS_KEY);
  } catch {
    // Silently fail
  }
}

// ============================================================================
// Export Types for ScheduleGrid Integration
// ============================================================================

export type { Assignment, AssignmentCreate, AssignmentUpdate };
