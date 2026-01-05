/**
 * useKeyboardShortcuts Hook
 *
 * Provides keyboard navigation and shortcuts for power users.
 * Supports Cmd/Ctrl modifiers for cross-platform compatibility.
 *
 * @example
 * ```tsx
 * // In a component
 * useKeyboardShortcuts({
 *   shortcuts: [
 *     { key: 'k', modifiers: ['cmd'], handler: () => focusSearch(), description: 'Focus search' },
 *     { key: 'n', handler: () => openNewModal(), description: 'New item', ignoreInputs: true },
 *     { key: 'Escape', handler: () => closeModal(), description: 'Close modal' },
 *     { key: 'r', handler: () => refetch(), description: 'Refresh data', ignoreInputs: true },
 *   ],
 *   enabled: true,
 * });
 * ```
 */
import { useEffect, useCallback, useRef } from 'react';

// ============================================================================
// Types
// ============================================================================

export type ModifierKey = 'cmd' | 'ctrl' | 'alt' | 'shift' | 'meta';

export interface KeyboardShortcut {
  /** The key to listen for (case-insensitive, e.g., 'k', 'Escape', 'Enter') */
  key: string;
  /** Modifier keys required (cmd/ctrl handled automatically per platform) */
  modifiers?: ModifierKey[];
  /** Handler function when shortcut is triggered */
  handler: (event: KeyboardEvent) => void;
  /** Human-readable description for UI hints */
  description?: string;
  /** If true, don't trigger when focus is in input/textarea/contenteditable */
  ignoreInputs?: boolean;
  /** If true, prevent default browser behavior */
  preventDefault?: boolean;
}

export interface UseKeyboardShortcutsOptions {
  /** List of shortcuts to register */
  shortcuts: KeyboardShortcut[];
  /** Whether shortcuts are currently enabled (default: true) */
  enabled?: boolean;
  /** Scope element - only trigger if focus is within (default: document) */
  scope?: React.RefObject<HTMLElement>;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if the current platform is macOS
 */
function isMac(): boolean {
  if (typeof window === 'undefined') return false;
  return navigator.platform.toUpperCase().indexOf('MAC') >= 0;
}

/**
 * Check if event target is an input element
 */
function isInputElement(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false;

  const tagName = target.tagName.toLowerCase();
  if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
    return true;
  }

  // Check for contenteditable
  if (target.isContentEditable) {
    return true;
  }

  return false;
}

/**
 * Check if all required modifiers are pressed
 */
function checkModifiers(
  event: KeyboardEvent,
  modifiers: ModifierKey[] = []
): boolean {
  const mac = isMac();

  for (const modifier of modifiers) {
    switch (modifier) {
      case 'cmd':
      case 'meta':
        // On Mac, use metaKey (Cmd); on Windows/Linux, use ctrlKey
        if (mac) {
          if (!event.metaKey) return false;
        } else {
          if (!event.ctrlKey) return false;
        }
        break;
      case 'ctrl':
        if (!event.ctrlKey) return false;
        break;
      case 'alt':
        if (!event.altKey) return false;
        break;
      case 'shift':
        if (!event.shiftKey) return false;
        break;
    }
  }

  // If no modifiers required, make sure no modifiers are pressed
  // (except for special keys like Escape that work with modifiers)
  if (modifiers.length === 0) {
    const isSpecialKey = ['Escape', 'Enter', 'Tab'].includes(event.key);
    if (!isSpecialKey && (event.ctrlKey || event.metaKey || event.altKey)) {
      return false;
    }
  }

  return true;
}

/**
 * Normalize key for comparison
 */
function normalizeKey(key: string): string {
  // Handle common aliases
  const keyMap: Record<string, string> = {
    esc: 'Escape',
    escape: 'Escape',
    enter: 'Enter',
    return: 'Enter',
    tab: 'Tab',
    space: ' ',
    spacebar: ' ',
    up: 'ArrowUp',
    down: 'ArrowDown',
    left: 'ArrowLeft',
    right: 'ArrowRight',
  };

  const normalized = keyMap[key.toLowerCase()] || key;
  return normalized.length === 1 ? normalized.toLowerCase() : normalized;
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for registering keyboard shortcuts.
 * Automatically handles Cmd/Ctrl differences between Mac and Windows/Linux.
 */
export function useKeyboardShortcuts({
  shortcuts,
  enabled = true,
  scope,
}: UseKeyboardShortcutsOptions): void {
  // Use ref to avoid re-registering listeners when shortcuts array reference changes
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Check if we're within scope (if specified)
      if (scope?.current) {
        if (!scope.current.contains(event.target as Node)) {
          return;
        }
      }

      const eventKey = normalizeKey(event.key);

      for (const shortcut of shortcutsRef.current) {
        const shortcutKey = normalizeKey(shortcut.key);

        // Check key match
        if (eventKey !== shortcutKey) continue;

        // Check modifiers
        if (!checkModifiers(event, shortcut.modifiers)) continue;

        // Check if we should ignore inputs
        if (shortcut.ignoreInputs && isInputElement(event.target)) {
          continue;
        }

        // Trigger the handler
        if (shortcut.preventDefault !== false) {
          event.preventDefault();
        }
        shortcut.handler(event);
        break; // Only trigger first matching shortcut
      }
    },
    [scope]
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, handleKeyDown]);
}

// ============================================================================
// Utility Hook for Single Shortcut
// ============================================================================

/**
 * Simplified hook for a single keyboard shortcut.
 *
 * @example
 * ```tsx
 * useKeyboardShortcut('Escape', () => closeModal());
 * useKeyboardShortcut('k', () => focusSearch(), { modifiers: ['cmd'] });
 * ```
 */
export function useKeyboardShortcut(
  key: string,
  handler: (event: KeyboardEvent) => void,
  options: Omit<KeyboardShortcut, 'key' | 'handler'> & { enabled?: boolean } = {}
): void {
  const { enabled = true, ...shortcutOptions } = options;

  useKeyboardShortcuts({
    shortcuts: [{ key, handler, ...shortcutOptions }],
    enabled,
  });
}

// ============================================================================
// Utility Function for Display
// ============================================================================

/**
 * Get display string for a keyboard shortcut (for tooltips/hints).
 *
 * @example
 * ```tsx
 * getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })
 * // Returns "Cmd+K" on Mac, "Ctrl+K" on Windows
 * ```
 */
export function getShortcutDisplay(shortcut: {
  key: string;
  modifiers?: ModifierKey[];
}): string {
  const mac = isMac();
  const parts: string[] = [];

  for (const modifier of shortcut.modifiers || []) {
    switch (modifier) {
      case 'cmd':
      case 'meta':
        parts.push(mac ? '\u2318' : 'Ctrl'); // Command symbol on Mac
        break;
      case 'ctrl':
        parts.push(mac ? '\u2303' : 'Ctrl'); // Control symbol on Mac
        break;
      case 'alt':
        parts.push(mac ? '\u2325' : 'Alt'); // Option symbol on Mac
        break;
      case 'shift':
        parts.push(mac ? '\u21E7' : 'Shift'); // Shift symbol on Mac
        break;
    }
  }

  // Format the key
  let keyDisplay = shortcut.key;
  if (keyDisplay.length === 1) {
    keyDisplay = keyDisplay.toUpperCase();
  } else if (keyDisplay === 'Escape') {
    keyDisplay = 'Esc';
  }

  parts.push(keyDisplay);

  return mac ? parts.join('') : parts.join('+');
}

export default useKeyboardShortcuts;
