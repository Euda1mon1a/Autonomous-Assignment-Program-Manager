'use client';

/**
 * ColorPickerCell Component
 *
 * A click-to-edit color picker cell for inline editing of color values.
 * Supports font_color and background_color fields with preset colors and custom hex input.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Check, X, Loader2, Palette } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface ColorPickerCellProps {
  /** Current color value (hex string or null) */
  value: string | null;
  /** Callback when color is saved */
  onSave: (value: string | null) => void;
  /** Whether save is in progress */
  isSaving?: boolean;
  /** Whether cell is disabled */
  disabled?: boolean;
  /** Label for accessibility */
  ariaLabel?: string;
  /** Additional className */
  className?: string;
  /** Show "Clear" option to remove color */
  allowClear?: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const PRESET_COLORS = [
  // Row 1: Neutral colors
  { hex: '#FFFFFF', name: 'White' },
  { hex: '#94A3B8', name: 'Slate' },
  { hex: '#64748B', name: 'Dark Slate' },
  { hex: '#1E293B', name: 'Navy' },
  { hex: '#0F172A', name: 'Dark Navy' },
  { hex: '#000000', name: 'Black' },
  // Row 2: Primary colors
  { hex: '#EF4444', name: 'Red' },
  { hex: '#F97316', name: 'Orange' },
  { hex: '#EAB308', name: 'Yellow' },
  { hex: '#22C55E', name: 'Green' },
  { hex: '#3B82F6', name: 'Blue' },
  { hex: '#8B5CF6', name: 'Purple' },
  // Row 3: Light variants
  { hex: '#FEE2E2', name: 'Light Red' },
  { hex: '#FFEDD5', name: 'Light Orange' },
  { hex: '#FEF9C3', name: 'Light Yellow' },
  { hex: '#DCFCE7', name: 'Light Green' },
  { hex: '#DBEAFE', name: 'Light Blue' },
  { hex: '#EDE9FE', name: 'Light Purple' },
];

// ============================================================================
// Utility Functions
// ============================================================================

function isValidHexColor(color: string): boolean {
  return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(color);
}

function getContrastColor(hexColor: string): string {
  // Remove # if present
  const hex = hexColor.replace('#', '');

  // Parse RGB values
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return luminance > 0.5 ? '#000000' : '#FFFFFF';
}

// ============================================================================
// Main Component
// ============================================================================

export function ColorPickerCell({
  value,
  onSave,
  isSaving = false,
  disabled = false,
  ariaLabel = 'Color picker',
  className = '',
  allowClear = true,
}: ColorPickerCellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customColor, setCustomColor] = useState(value || '');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Handle click outside to close
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Focus input when opening
  useEffect(() => {
    if (isOpen) {
      setCustomColor(value || '');
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [isOpen, value]);

  const handleOpen = useCallback(() => {
    if (disabled || isSaving) return;
    setIsOpen(true);
  }, [disabled, isSaving]);

  const handleClose = useCallback(() => {
    setIsOpen(false);
    setCustomColor(value || '');
  }, [value]);

  const handleSelectColor = useCallback(
    (color: string | null) => {
      if (color !== value) {
        onSave(color);
      }
      setIsOpen(false);
    },
    [value, onSave]
  );

  const handleCustomColorSave = useCallback(() => {
    const trimmed = customColor.trim();
    if (!trimmed) {
      handleSelectColor(null);
      return;
    }

    // Add # if missing
    const colorWithHash = trimmed.startsWith('#') ? trimmed : `#${trimmed}`;

    if (isValidHexColor(colorWithHash)) {
      handleSelectColor(colorWithHash.toUpperCase());
    }
  }, [customColor, handleSelectColor]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleClose();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        handleCustomColorSave();
      }
    },
    [handleClose, handleCustomColorSave]
  );

  // Render color swatch button
  const renderSwatch = () => (
    <button
      onClick={handleOpen}
      disabled={disabled || isSaving}
      className={`
        flex items-center gap-2 px-2 py-1 rounded transition-colors
        ${disabled ? 'cursor-not-allowed opacity-60' : 'hover:bg-slate-700/50'}
        ${className}
      `}
      aria-label={ariaLabel}
      aria-haspopup="dialog"
      aria-expanded={isOpen}
    >
      {isSaving ? (
        <Loader2 className="w-4 h-4 animate-spin text-violet-400" />
      ) : value ? (
        <span
          className="w-5 h-5 rounded border border-slate-600"
          style={{ backgroundColor: value }}
          aria-label={`Current color: ${value}`}
        />
      ) : (
        <span className="w-5 h-5 rounded border border-slate-600 border-dashed flex items-center justify-center">
          <Palette className="w-3 h-3 text-slate-500" />
        </span>
      )}
      <span className="text-slate-400 text-xs">
        {value || 'None'}
      </span>
    </button>
  );

  return (
    <div ref={containerRef} className="relative">
      {renderSwatch()}

      {isOpen && (
        <div
          className="absolute z-50 top-full left-0 mt-1 p-3 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[240px]"
          role="dialog"
          aria-label="Color picker"
        >
          {/* Preset colors grid */}
          <div className="mb-3">
            <p className="text-xs font-medium text-slate-400 mb-2">Presets</p>
            <div className="grid grid-cols-6 gap-1">
              {PRESET_COLORS.map((color) => (
                <button
                  key={color.hex}
                  onClick={() => handleSelectColor(color.hex)}
                  className={`
                    w-7 h-7 rounded border-2 transition-all
                    ${value === color.hex ? 'border-violet-500 scale-110' : 'border-transparent hover:border-slate-500'}
                  `}
                  style={{ backgroundColor: color.hex }}
                  title={`${color.name} (${color.hex})`}
                  aria-label={`Select ${color.name}`}
                >
                  {value === color.hex && (
                    <Check
                      className="w-4 h-4 mx-auto"
                      style={{ color: getContrastColor(color.hex) }}
                    />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Custom color input */}
          <div className="mb-3">
            <p className="text-xs font-medium text-slate-400 mb-2">Custom</p>
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={customColor}
                onChange={(e) => setCustomColor(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="#RRGGBB"
                className="flex-1 px-2 py-1.5 bg-slate-700 border border-slate-600 rounded text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                aria-label="Custom hex color"
              />
              <button
                onClick={handleCustomColorSave}
                disabled={!customColor.trim() || !isValidHexColor(customColor.startsWith('#') ? customColor : `#${customColor}`)}
                className="p-1.5 text-emerald-400 hover:text-emerald-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Apply custom color"
                aria-label="Apply custom color"
              >
                <Check className="w-4 h-4" />
              </button>
            </div>
            {customColor && !isValidHexColor(customColor.startsWith('#') ? customColor : `#${customColor}`) && (
              <p className="text-xs text-red-400 mt-1">
                Enter a valid hex color (e.g., #FF0000)
              </p>
            )}
          </div>

          {/* Preview */}
          {customColor && isValidHexColor(customColor.startsWith('#') ? customColor : `#${customColor}`) && (
            <div className="mb-3 p-2 rounded border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">Preview</p>
              <div
                className="h-8 rounded flex items-center justify-center text-sm font-medium"
                style={{
                  backgroundColor: customColor.startsWith('#') ? customColor : `#${customColor}`,
                  color: getContrastColor(customColor.startsWith('#') ? customColor : `#${customColor}`),
                }}
              >
                Sample Text
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-700">
            {allowClear && value && (
              <button
                onClick={() => handleSelectColor(null)}
                className="text-xs text-slate-400 hover:text-white transition-colors"
              >
                Clear color
              </button>
            )}
            <button
              onClick={handleClose}
              className="ml-auto flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-3 h-3" />
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ColorPickerCell;
