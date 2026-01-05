'use client';

/**
 * EditableCell Component
 *
 * A click-to-edit cell component for inline editing in tables.
 * Supports text, number, and select field types with keyboard navigation.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Check, X, Loader2 } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export type EditableCellType = 'text' | 'number' | 'select';

export interface SelectOption {
  value: string;
  label: string;
}

export interface EditableCellProps {
  /** Current value */
  value: string | number | null;
  /** Cell type */
  type?: EditableCellType;
  /** Options for select type */
  options?: SelectOption[];
  /** Placeholder text when empty */
  placeholder?: string;
  /** Callback when value is saved */
  onSave: (value: string | number | null) => void;
  /** Whether save is in progress */
  isSaving?: boolean;
  /** Whether cell is disabled */
  disabled?: boolean;
  /** Minimum value for number type */
  min?: number;
  /** Maximum value for number type */
  max?: number;
  /** Custom display renderer */
  renderDisplay?: (value: string | number | null) => React.ReactNode;
  /** Additional className for the cell */
  className?: string;
  /** ARIA label for accessibility */
  ariaLabel?: string;
}

// ============================================================================
// Main Component
// ============================================================================

export function EditableCell({
  value,
  type = 'text',
  options = [],
  placeholder = 'Click to edit',
  onSave,
  isSaving = false,
  disabled = false,
  min,
  max,
  renderDisplay,
  className = '',
  ariaLabel,
}: EditableCellProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState<string>('');
  const inputRef = useRef<HTMLInputElement | HTMLSelectElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize edit value when entering edit mode
  useEffect(() => {
    if (isEditing) {
      setEditValue(value?.toString() ?? '');
      // Focus the input after render
      setTimeout(() => {
        inputRef.current?.focus();
        if (inputRef.current instanceof HTMLInputElement) {
          inputRef.current.select();
        }
      }, 0);
    }
  }, [isEditing, value]);

  const handleStartEdit = useCallback(() => {
    if (disabled || isSaving) return;
    setIsEditing(true);
  }, [disabled, isSaving]);

  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setEditValue(value?.toString() ?? '');
  }, [value]);

  const handleSave = useCallback(() => {
    if (isSaving) return;

    let newValue: string | number | null = editValue.trim();

    // Convert to appropriate type
    if (type === 'number') {
      if (newValue === '') {
        newValue = null;
      } else {
        const numValue = parseFloat(newValue);
        if (isNaN(numValue)) {
          handleCancel();
          return;
        }
        if (min !== undefined && numValue < min) {
          newValue = min;
        } else if (max !== undefined && numValue > max) {
          newValue = max;
        } else {
          newValue = numValue;
        }
      }
    } else if (type === 'text' && newValue === '') {
      newValue = null;
    }

    // Only save if value changed
    if (newValue !== value) {
      onSave(newValue);
    }
    setIsEditing(false);
  }, [editValue, type, min, max, value, onSave, isSaving, handleCancel]);

  // Handle click outside to cancel
  useEffect(() => {
    if (!isEditing) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        handleCancel();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isEditing, handleCancel]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSave();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        handleCancel();
      }
    },
    [handleSave, handleCancel]
  );

  // Get display value
  const displayValue = renderDisplay
    ? renderDisplay(value)
    : value?.toString() || (
        <span className="text-slate-500 italic">{placeholder}</span>
      );

  // Render editing state
  if (isEditing) {
    return (
      <div
        ref={containerRef}
        className={`flex items-center gap-1 ${className}`}
        role="group"
        aria-label={ariaLabel || 'Edit cell'}
      >
        {type === 'select' ? (
          <select
            ref={inputRef as React.RefObject<HTMLSelectElement>}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 px-2 py-1 bg-slate-700 border border-violet-500 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            aria-label={ariaLabel || 'Select value'}
          >
            <option value="">-- Select --</option>
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type={type}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            min={min}
            max={max}
            className="flex-1 min-w-0 px-2 py-1 bg-slate-700 border border-violet-500 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            placeholder={placeholder}
            aria-label={ariaLabel || 'Edit value'}
          />
        )}

        <button
          onClick={handleSave}
          disabled={isSaving}
          className="p-1 text-emerald-400 hover:text-emerald-300 transition-colors disabled:opacity-50"
          title="Save (Enter)"
          aria-label="Save"
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Check className="w-4 h-4" />
          )}
        </button>

        <button
          onClick={handleCancel}
          disabled={isSaving}
          className="p-1 text-slate-400 hover:text-slate-300 transition-colors disabled:opacity-50"
          title="Cancel (Escape)"
          aria-label="Cancel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  // Render display state
  return (
    <div
      ref={containerRef}
      onClick={handleStartEdit}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleStartEdit();
        }
      }}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label={ariaLabel || `Click to edit: ${value ?? 'empty'}`}
      className={`
        cursor-pointer rounded px-1 py-0.5 -mx-1 transition-colors
        ${disabled ? 'cursor-not-allowed opacity-60' : 'hover:bg-slate-700/50'}
        ${isSaving ? 'opacity-60' : ''}
        ${className}
      `}
    >
      {isSaving ? (
        <span className="flex items-center gap-1">
          <Loader2 className="w-3 h-3 animate-spin text-violet-400" />
          {displayValue}
        </span>
      ) : (
        displayValue
      )}
    </div>
  );
}

export default EditableCell;
