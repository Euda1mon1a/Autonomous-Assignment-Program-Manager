/**
 * useDebounce Hooks Tests
 *
 * Tests for debouncing utilities including useDebounce, useDebouncedCallback,
 * and useDebouncedState.
 */
import { renderHook, act } from '@testing-library/react';
import {
  useDebounce,
  useDebouncedCallback,
  useDebouncedState,
} from '@/hooks/useDebounce';

// Enable fake timers for all tests
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

describe('useDebounce', () => {
  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));

    expect(result.current).toBe('initial');
  });

  it('should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );

    expect(result.current).toBe('initial');

    // Update value
    rerender({ value: 'updated', delay: 300 });

    // Value should not change immediately
    expect(result.current).toBe('initial');

    // Fast forward time
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Value should now be updated
    expect(result.current).toBe('updated');
  });

  it('should reset timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'v1', delay: 300 } }
    );

    expect(result.current).toBe('v1');

    // Rapid updates
    rerender({ value: 'v2', delay: 300 });
    act(() => {
      jest.advanceTimersByTime(100);
    });

    rerender({ value: 'v3', delay: 300 });
    act(() => {
      jest.advanceTimersByTime(100);
    });

    rerender({ value: 'v4', delay: 300 });

    // Should still be initial value
    expect(result.current).toBe('v1');

    // Complete the delay
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Should now be the last value
    expect(result.current).toBe('v4');
  });

  it('should handle number values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 0 } }
    );

    expect(result.current).toBe(0);

    rerender({ value: 42 });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe(42);
  });

  it('should use default delay of 300ms', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'updated' });

    act(() => {
      jest.advanceTimersByTime(299);
    });

    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(1);
    });

    expect(result.current).toBe('updated');
  });

  it('should clean up timer on unmount', () => {
    const { rerender, unmount } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'updated' });

    unmount();

    // Should not throw when advancing timers after unmount
    expect(() => {
      act(() => {
        jest.advanceTimersByTime(300);
      });
    }).not.toThrow();
  });
});

describe('useDebouncedCallback', () => {
  it('should debounce callback execution', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current.debouncedCallback('arg1');
    });

    expect(callback).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledWith('arg1');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should cancel pending callback', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current.debouncedCallback('arg1');
    });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    act(() => {
      result.current.cancel();
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).not.toHaveBeenCalled();
  });

  it('should flush pending callback immediately', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current.debouncedCallback('arg1');
    });

    act(() => {
      result.current.flush();
    });

    expect(callback).toHaveBeenCalledWith('arg1');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should reset timer on rapid calls', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current.debouncedCallback('arg1');
    });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    act(() => {
      result.current.debouncedCallback('arg2');
    });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    act(() => {
      result.current.debouncedCallback('arg3');
    });

    expect(callback).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledWith('arg3');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should preserve callback arguments', () => {
    const callback = jest.fn();
    const { result } = renderHook(() =>
      useDebouncedCallback(
        (...args: unknown[]) => callback(args[0], args[1], args[2]),
        300
      )
    );

    act(() => {
      result.current.debouncedCallback('test', 42, true);
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledWith('test', 42, true);
  });

  it('should update callback reference on each render', () => {
    let callCount = 0;
    const { rerender } = renderHook(
      ({ callback }) => useDebouncedCallback(callback, 300),
      {
        initialProps: {
          callback: () => {
            callCount += 1;
          },
        },
      }
    );

    // Update callback
    rerender({
      callback: () => {
        callCount += 10;
      },
    });

    const { result } = renderHook(() =>
      useDebouncedCallback(() => {
        callCount += 10;
      }, 300)
    );

    act(() => {
      result.current.debouncedCallback();
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callCount).toBe(10);
  });

  it('should clean up on unmount', () => {
    const callback = jest.fn();
    const { result, unmount } = renderHook(() =>
      useDebouncedCallback(callback, 300)
    );

    act(() => {
      result.current.debouncedCallback('arg1');
    });

    unmount();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).not.toHaveBeenCalled();
  });
});

describe('useDebouncedState', () => {
  it('should return immediate and debounced values', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    const [immediate, debounced] = result.current;

    expect(immediate).toBe('initial');
    expect(debounced).toBe('initial');
  });

  it('should update immediate value immediately', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    act(() => {
      const [, , setValue] = result.current;
      setValue('updated');
    });

    const [immediate, debounced] = result.current;

    expect(immediate).toBe('updated');
    expect(debounced).toBe('initial');
  });

  it('should update debounced value after delay', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    act(() => {
      const [, , setValue] = result.current;
      setValue('updated');
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    const [immediate, debounced] = result.current;

    expect(immediate).toBe('updated');
    expect(debounced).toBe('updated');
  });

  it('should handle multiple rapid updates', () => {
    const { result } = renderHook(() => useDebouncedState('v1', 300));

    act(() => {
      const [, , setValue] = result.current;
      setValue('v2');
    });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    act(() => {
      const [, , setValue] = result.current;
      setValue('v3');
    });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    act(() => {
      const [, , setValue] = result.current;
      setValue('v4');
    });

    const [immediate, debounced] = result.current;

    expect(immediate).toBe('v4');
    expect(debounced).toBe('v1');

    act(() => {
      jest.advanceTimersByTime(300);
    });

    const [finalImmediate, finalDebounced] = result.current;

    expect(finalImmediate).toBe('v4');
    expect(finalDebounced).toBe('v4');
  });

  it('should use default delay of 300ms', () => {
    const { result } = renderHook(() => useDebouncedState('initial'));

    act(() => {
      const [, , setValue] = result.current;
      setValue('updated');
    });

    act(() => {
      jest.advanceTimersByTime(299);
    });

    expect(result.current[1]).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(1);
    });

    expect(result.current[1]).toBe('updated');
  });

  it('should handle number values', () => {
    const { result } = renderHook(() => useDebouncedState(0, 300));

    act(() => {
      const [, , setValue] = result.current;
      setValue(42);
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    const [immediate, debounced] = result.current;

    expect(immediate).toBe(42);
    expect(debounced).toBe(42);
  });
});
