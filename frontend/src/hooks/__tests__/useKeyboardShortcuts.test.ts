/**
 * Tests for useKeyboardShortcuts Hook
 *
 * Tests keyboard shortcut registration, modifier handling,
 * and cross-platform compatibility.
 */
import { renderHook, act } from '@testing-library/react';
import { useKeyboardShortcuts, useKeyboardShortcut, getShortcutDisplay } from '../useKeyboardShortcuts';

// Mock navigator.platform
const mockPlatform = (platform: string) => {
  Object.defineProperty(navigator, 'platform', {
    value: platform,
    writable: true,
  });
};

describe('useKeyboardShortcuts', () => {
  beforeEach(() => {
    // Default to Windows/Linux platform
    mockPlatform('Win32');
  });

  afterEach(() => {
    // Clean up any event listeners
    jest.clearAllMocks();
  });

  describe('Basic Key Handling', () => {
    it('calls handler when matching key is pressed', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'k', handler }],
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });

      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('does not call handler for non-matching key', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'k', handler }],
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'j' })
        );
      });

      expect(handler).not.toHaveBeenCalled();
    });

    it('handles Escape key', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'Escape', handler }],
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'Escape' })
        );
      });

      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('is case-insensitive for single character keys', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'K', handler }],
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });

      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe('Modifier Keys', () => {
    it('requires Ctrl modifier on Windows/Linux', () => {
      mockPlatform('Win32');
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'k', modifiers: ['cmd'], handler }],
        })
      );

      // Without modifier
      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });
      expect(handler).not.toHaveBeenCalled();

      // With Ctrl modifier
      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
        );
      });
      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('requires Meta modifier on Mac', () => {
      mockPlatform('MacIntel');
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'k', modifiers: ['cmd'], handler }],
        })
      );

      // Without modifier
      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });
      expect(handler).not.toHaveBeenCalled();

      // With Meta modifier
      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k', metaKey: true })
        );
      });
      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('handles shift modifier', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: '?', modifiers: ['shift'], handler }],
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: '?', shiftKey: true })
        );
      });

      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('handles alt modifier', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'a', modifiers: ['alt'], handler }],
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'a', altKey: true })
        );
      });

      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('handles multiple modifiers', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 's', modifiers: ['cmd', 'shift'], handler }],
        })
      );

      // Missing shift
      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 's', ctrlKey: true })
        );
      });
      expect(handler).not.toHaveBeenCalled();

      // With both modifiers
      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 's', ctrlKey: true, shiftKey: true })
        );
      });
      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe('ignoreInputs Option', () => {
    it('ignores shortcuts when focused on input element', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'r', handler, ignoreInputs: true }],
        })
      );

      const input = document.createElement('input');
      document.body.appendChild(input);
      input.focus();

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'r' });
        Object.defineProperty(event, 'target', { value: input });
        document.dispatchEvent(event);
      });

      expect(handler).not.toHaveBeenCalled();

      document.body.removeChild(input);
    });

    it('triggers shortcuts in inputs when ignoreInputs is false', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'Escape', handler, ignoreInputs: false }],
        })
      );

      const input = document.createElement('input');
      document.body.appendChild(input);
      input.focus();

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'Escape' });
        Object.defineProperty(event, 'target', { value: input });
        document.dispatchEvent(event);
      });

      expect(handler).toHaveBeenCalledTimes(1);

      document.body.removeChild(input);
    });
  });

  describe('enabled Option', () => {
    it('does not register shortcuts when disabled', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'k', handler }],
          enabled: false,
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });

      expect(handler).not.toHaveBeenCalled();
    });

    it('registers shortcuts when enabled', () => {
      const handler = jest.fn();

      const { rerender } = renderHook(
        ({ enabled }) =>
          useKeyboardShortcuts({
            shortcuts: [{ key: 'k', handler }],
            enabled,
          }),
        { initialProps: { enabled: false } }
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });
      expect(handler).not.toHaveBeenCalled();

      rerender({ enabled: true });

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });
      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe('preventDefault Option', () => {
    it('prevents default by default', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'k', handler }],
        })
      );

      const event = new KeyboardEvent('keydown', { key: 'k' });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

      act(() => {
        document.dispatchEvent(event);
      });

      expect(preventDefaultSpy).toHaveBeenCalled();
    });

    it('does not prevent default when preventDefault is false', () => {
      const handler = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [{ key: 'k', handler, preventDefault: false }],
        })
      );

      const event = new KeyboardEvent('keydown', { key: 'k' });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

      act(() => {
        document.dispatchEvent(event);
      });

      expect(preventDefaultSpy).not.toHaveBeenCalled();
    });
  });

  describe('Multiple Shortcuts', () => {
    it('only triggers first matching shortcut', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [
            { key: 'k', handler: handler1 },
            { key: 'k', handler: handler2 },
          ],
        })
      );

      act(() => {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'k' })
        );
      });

      expect(handler1).toHaveBeenCalledTimes(1);
      expect(handler2).not.toHaveBeenCalled();
    });

    it('triggers different handlers for different keys', () => {
      const handlerK = jest.fn();
      const handlerR = jest.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          shortcuts: [
            { key: 'k', handler: handlerK },
            { key: 'r', handler: handlerR },
          ],
        })
      );

      act(() => {
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k' }));
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'r' }));
      });

      expect(handlerK).toHaveBeenCalledTimes(1);
      expect(handlerR).toHaveBeenCalledTimes(1);
    });
  });
});

describe('useKeyboardShortcut', () => {
  it('registers a single shortcut', () => {
    const handler = jest.fn();

    renderHook(() => useKeyboardShortcut('k', handler));

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k' }));
    });

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('supports modifiers', () => {
    mockPlatform('Win32');
    const handler = jest.fn();

    renderHook(() =>
      useKeyboardShortcut('k', handler, { modifiers: ['cmd'] })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
      );
    });

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('supports enabled option', () => {
    const handler = jest.fn();

    renderHook(() =>
      useKeyboardShortcut('k', handler, { enabled: false })
    );

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k' }));
    });

    expect(handler).not.toHaveBeenCalled();
  });
});

describe('getShortcutDisplay', () => {
  describe('on Windows/Linux', () => {
    beforeEach(() => {
      mockPlatform('Win32');
    });

    it('displays Ctrl for cmd modifier', () => {
      expect(getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })).toBe('Ctrl+K');
    });

    it('displays Alt for alt modifier', () => {
      expect(getShortcutDisplay({ key: 'a', modifiers: ['alt'] })).toBe('Alt+A');
    });

    it('displays Shift for shift modifier', () => {
      expect(getShortcutDisplay({ key: 's', modifiers: ['shift'] })).toBe('Shift+S');
    });

    it('displays multiple modifiers with +', () => {
      expect(
        getShortcutDisplay({ key: 's', modifiers: ['cmd', 'shift'] })
      ).toBe('Ctrl+Shift+S');
    });

    it('handles special keys', () => {
      expect(getShortcutDisplay({ key: 'Escape' })).toBe('Esc');
    });
  });

  describe('on Mac', () => {
    beforeEach(() => {
      mockPlatform('MacIntel');
    });

    it('displays command symbol for cmd modifier', () => {
      const display = getShortcutDisplay({ key: 'k', modifiers: ['cmd'] });
      expect(display).toContain('\u2318'); // Command symbol
      expect(display).toContain('K');
    });

    it('displays option symbol for alt modifier', () => {
      const display = getShortcutDisplay({ key: 'a', modifiers: ['alt'] });
      expect(display).toContain('\u2325'); // Option symbol
    });

    it('displays shift symbol for shift modifier', () => {
      const display = getShortcutDisplay({ key: 's', modifiers: ['shift'] });
      expect(display).toContain('\u21E7'); // Shift symbol
    });
  });
});
