import { renderHook, act } from '@testing-library/react';
import {
  useGridKeyboardNavigation,
  type GridPosition,
} from '@/hooks/useGridKeyboardNavigation';

describe('useGridKeyboardNavigation', () => {
  const defaultOptions = {
    rowCount: 3,
    colCount: 4,
  };

  describe('initialization', () => {
    it('starts with no focused cell', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      expect(result.current.focusedCell).toBeNull();
    });

    it('returns grid props with role and onKeyDown', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      expect(result.current.gridProps.role).toBe('grid');
      expect(typeof result.current.gridProps.onKeyDown).toBe('function');
    });

    it('returns getCellProps function', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      expect(typeof result.current.getCellProps).toBe('function');
    });
  });

  describe('getCellProps', () => {
    it('returns tabIndex 0 for first cell when nothing is focused', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      const props = result.current.getCellProps(0, 0);
      expect(props.tabIndex).toBe(0);
      expect(props.role).toBe('gridcell');
      expect(props['data-row']).toBe(0);
      expect(props['data-col']).toBe(0);
    });

    it('returns tabIndex -1 for non-first cells when nothing is focused', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      const props = result.current.getCellProps(1, 2);
      expect(props.tabIndex).toBe(-1);
    });

    it('returns tabIndex 0 for focused cell and -1 for others', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 1, col: 2 });
      });

      expect(result.current.getCellProps(1, 2).tabIndex).toBe(0);
      expect(result.current.getCellProps(0, 0).tabIndex).toBe(-1);
      expect(result.current.getCellProps(2, 3).tabIndex).toBe(-1);
    });

    it('sets aria-selected true only for focused cell', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 1 });
      });

      expect(result.current.getCellProps(0, 1)['aria-selected']).toBe(true);
      expect(result.current.getCellProps(0, 0)['aria-selected']).toBe(false);
    });

    it('calls onCellActivate when cell is clicked', () => {
      const onCellActivate = jest.fn();
      const { result } = renderHook(() =>
        useGridKeyboardNavigation({ ...defaultOptions, onCellActivate })
      );

      act(() => {
        result.current.getCellProps(1, 2).onClick();
      });

      expect(onCellActivate).toHaveBeenCalledWith({ row: 1, col: 2 });
    });

    it('updates focused cell on focus event', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.getCellProps(2, 1).onFocus();
      });

      expect(result.current.focusedCell).toEqual({ row: 2, col: 1 });
    });
  });

  describe('arrow key navigation', () => {
    function createKeyEvent(key: string): React.KeyboardEvent {
      return {
        key,
        preventDefault: jest.fn(),
        stopPropagation: jest.fn(),
      } as unknown as React.KeyboardEvent;
    }

    it('moves focus right with ArrowRight', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      // Set initial focus
      act(() => {
        result.current.setFocusedCell({ row: 0, col: 0 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowRight'));
      });

      expect(result.current.focusedCell).toEqual({ row: 0, col: 1 });
    });

    it('moves focus left with ArrowLeft', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 2 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowLeft'));
      });

      expect(result.current.focusedCell).toEqual({ row: 0, col: 1 });
    });

    it('moves focus down with ArrowDown', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 0 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowDown'));
      });

      expect(result.current.focusedCell).toEqual({ row: 1, col: 0 });
    });

    it('moves focus up with ArrowUp', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 2, col: 0 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowUp'));
      });

      expect(result.current.focusedCell).toEqual({ row: 1, col: 0 });
    });

    it('does not move past last column', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 3 }); // last column
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowRight'));
      });

      // Should stay at col 3 (last column)
      expect(result.current.focusedCell).toEqual({ row: 0, col: 3 });
    });

    it('does not move past first column', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 0 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowLeft'));
      });

      expect(result.current.focusedCell).toEqual({ row: 0, col: 0 });
    });

    it('does not move past last row', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 2, col: 0 }); // last row
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowDown'));
      });

      expect(result.current.focusedCell).toEqual({ row: 2, col: 0 });
    });

    it('does not move past first row', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 0 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowUp'));
      });

      expect(result.current.focusedCell).toEqual({ row: 0, col: 0 });
    });

    it('prevents default on arrow keys', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 1, col: 1 });
      });

      const event = createKeyEvent('ArrowRight');
      act(() => {
        result.current.gridProps.onKeyDown(event);
      });

      expect(event.preventDefault).toHaveBeenCalled();
    });
  });

  describe('Home and End keys', () => {
    function createKeyEvent(key: string): React.KeyboardEvent {
      return {
        key,
        preventDefault: jest.fn(),
        stopPropagation: jest.fn(),
      } as unknown as React.KeyboardEvent;
    }

    it('moves to first column with Home key', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 1, col: 3 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('Home'));
      });

      expect(result.current.focusedCell).toEqual({ row: 1, col: 0 });
    });

    it('moves to last column with End key', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 1, col: 0 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('End'));
      });

      expect(result.current.focusedCell).toEqual({ row: 1, col: 3 });
    });
  });

  describe('Enter and Space activation', () => {
    function createKeyEvent(key: string): React.KeyboardEvent {
      return {
        key,
        preventDefault: jest.fn(),
        stopPropagation: jest.fn(),
      } as unknown as React.KeyboardEvent;
    }

    it('calls onCellActivate on Enter key', () => {
      const onCellActivate = jest.fn();
      const { result } = renderHook(() =>
        useGridKeyboardNavigation({ ...defaultOptions, onCellActivate })
      );

      act(() => {
        result.current.setFocusedCell({ row: 1, col: 2 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('Enter'));
      });

      expect(onCellActivate).toHaveBeenCalledWith({ row: 1, col: 2 });
    });

    it('calls onCellActivate on Space key', () => {
      const onCellActivate = jest.fn();
      const { result } = renderHook(() =>
        useGridKeyboardNavigation({ ...defaultOptions, onCellActivate })
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 3 });
      });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent(' '));
      });

      expect(onCellActivate).toHaveBeenCalledWith({ row: 0, col: 3 });
    });

    it('does not call onCellActivate when no cell is focused', () => {
      const onCellActivate = jest.fn();
      const { result } = renderHook(() =>
        useGridKeyboardNavigation({ ...defaultOptions, onCellActivate })
      );

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('Enter'));
      });

      expect(onCellActivate).not.toHaveBeenCalled();
    });

    it('prevents default on Enter and Space', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 0 });
      });

      const enterEvent = createKeyEvent('Enter');
      const spaceEvent = createKeyEvent(' ');

      act(() => {
        result.current.gridProps.onKeyDown(enterEvent);
      });

      act(() => {
        result.current.gridProps.onKeyDown(spaceEvent);
      });

      expect(enterEvent.preventDefault).toHaveBeenCalled();
      expect(spaceEvent.preventDefault).toHaveBeenCalled();
    });
  });

  describe('setFocusedCell', () => {
    it('allows programmatic focus setting', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 2, col: 3 });
      });

      expect(result.current.focusedCell).toEqual({ row: 2, col: 3 });
    });

    it('allows clearing focus', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 1, col: 1 });
      });

      act(() => {
        result.current.setFocusedCell(null);
      });

      expect(result.current.focusedCell).toBeNull();
    });
  });

  describe('edge cases', () => {
    function createKeyEvent(key: string): React.KeyboardEvent {
      return {
        key,
        preventDefault: jest.fn(),
        stopPropagation: jest.fn(),
      } as unknown as React.KeyboardEvent;
    }

    it('handles zero rows gracefully', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation({ rowCount: 0, colCount: 4 })
      );

      // Should not throw
      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowDown'));
      });

      expect(result.current.focusedCell).toBeNull();
    });

    it('handles zero columns gracefully', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation({ rowCount: 3, colCount: 0 })
      );

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowRight'));
      });

      expect(result.current.focusedCell).toBeNull();
    });

    it('handles single cell grid', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation({ rowCount: 1, colCount: 1 })
      );

      act(() => {
        result.current.setFocusedCell({ row: 0, col: 0 });
      });

      // All arrow keys should keep focus on the only cell
      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowRight'));
      });
      expect(result.current.focusedCell).toEqual({ row: 0, col: 0 });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowDown'));
      });
      expect(result.current.focusedCell).toEqual({ row: 0, col: 0 });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowLeft'));
      });
      expect(result.current.focusedCell).toEqual({ row: 0, col: 0 });

      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowUp'));
      });
      expect(result.current.focusedCell).toEqual({ row: 0, col: 0 });
    });

    it('ignores unrecognized keys', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      act(() => {
        result.current.setFocusedCell({ row: 1, col: 1 });
      });

      const event = createKeyEvent('a');
      act(() => {
        result.current.gridProps.onKeyDown(event);
      });

      // Should not change focus
      expect(result.current.focusedCell).toEqual({ row: 1, col: 1 });
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('starts navigation from 0,0 when no cell was previously focused', () => {
      const { result } = renderHook(() =>
        useGridKeyboardNavigation(defaultOptions)
      );

      // Press ArrowDown without prior focus - should start from 0,0 and move to 1,0
      act(() => {
        result.current.gridProps.onKeyDown(createKeyEvent('ArrowDown'));
      });

      expect(result.current.focusedCell).toEqual({ row: 1, col: 0 });
    });
  });
});
