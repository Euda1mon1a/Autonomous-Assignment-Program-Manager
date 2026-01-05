/**
 * Tests for useDebounce Hooks
 *
 * Tests value debouncing, callback debouncing, and debounced state.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import {
  useDebounce,
  useDebouncedCallback,
  useDebouncedState,
} from '../useDebounce';

// Use fake timers for precise control
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('useDebounce', () => {
  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));
    expect(result.current).toBe('initial');
  });

  it('returns debounced value after delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    expect(result.current).toBe('initial');

    rerender({ value: 'updated' });

    // Value should not update immediately
    expect(result.current).toBe('initial');

    // Advance timer
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe('updated');
  });

  it('resets timer on new value before delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'update1' });

    act(() => {
      jest.advanceTimersByTime(200);
    });

    // Change value again before delay completes
    rerender({ value: 'update2' });

    act(() => {
      jest.advanceTimersByTime(200);
    });

    // Should still be initial (timer reset)
    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(100);
    });

    // Now should be update2
    expect(result.current).toBe('update2');
  });

  it('uses default delay of 300ms', () => {
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

  it('works with different types', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 42 } }
    );

    expect(result.current).toBe(42);

    rerender({ value: 100 });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe(100);
  });

  it('works with objects', () => {
    const initial = { name: 'John' };
    const updated = { name: 'Jane' };

    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: initial } }
    );

    expect(result.current).toBe(initial);

    rerender({ value: updated });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe(updated);
  });

  it('cleans up timer on unmount', () => {
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');

    const { unmount } = renderHook(() => useDebounce('test', 300));

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();

    clearTimeoutSpy.mockRestore();
  });
});

describe('useDebouncedCallback', () => {
  it('debounces callback execution', () => {
    const callback = jest.fn();

    const { result } = renderHook(() =>
      useDebouncedCallback(callback, 300)
    );

    act(() => {
      result.current.debouncedCallback('test');
    });

    expect(callback).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledWith('test');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('only calls callback once for rapid calls', () => {
    const callback = jest.fn();

    const { result } = renderHook(() =>
      useDebouncedCallback(callback, 300)
    );

    act(() => {
      result.current.debouncedCallback('first');
      result.current.debouncedCallback('second');
      result.current.debouncedCallback('third');
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('third');
  });

  it('cancel prevents callback execution', () => {
    const callback = jest.fn();

    const { result } = renderHook(() =>
      useDebouncedCallback(callback, 300)
    );

    act(() => {
      result.current.debouncedCallback('test');
    });

    act(() => {
      result.current.cancel();
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).not.toHaveBeenCalled();
  });

  it('flush immediately executes pending callback', () => {
    const callback = jest.fn();

    const { result } = renderHook(() =>
      useDebouncedCallback(callback, 300)
    );

    act(() => {
      result.current.debouncedCallback('test');
    });

    act(() => {
      result.current.flush();
    });

    expect(callback).toHaveBeenCalledWith('test');

    // Should not be called again after delay
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('updates callback reference without breaking debounce', () => {
    const callback1 = jest.fn();
    const callback2 = jest.fn();

    const { result, rerender } = renderHook(
      ({ cb }) => useDebouncedCallback(cb, 300),
      { initialProps: { cb: callback1 } }
    );

    act(() => {
      result.current.debouncedCallback('test');
    });

    rerender({ cb: callback2 });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Should call the updated callback
    expect(callback1).not.toHaveBeenCalled();
    expect(callback2).toHaveBeenCalledWith('test');
  });

  it('cleans up on unmount', () => {
    const callback = jest.fn();

    const { result, unmount } = renderHook(() =>
      useDebouncedCallback(callback, 300)
    );

    act(() => {
      result.current.debouncedCallback('test');
    });

    unmount();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).not.toHaveBeenCalled();
  });

  it('handles callbacks with multiple arguments', () => {
    const callback = jest.fn();

    const { result } = renderHook(() =>
      useDebouncedCallback(callback, 300)
    );

    act(() => {
      result.current.debouncedCallback('arg1', 'arg2', 'arg3');
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledWith('arg1', 'arg2', 'arg3');
  });
});

describe('useDebouncedState', () => {
  it('returns immediate value, debounced value, and setter', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    const [immediate, debounced, setter] = result.current;

    expect(immediate).toBe('initial');
    expect(debounced).toBe('initial');
    expect(typeof setter).toBe('function');
  });

  it('updates immediate value synchronously', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    act(() => {
      result.current[2]('updated');
    });

    expect(result.current[0]).toBe('updated');
    expect(result.current[1]).toBe('initial');
  });

  it('updates debounced value after delay', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    act(() => {
      result.current[2]('updated');
    });

    expect(result.current[1]).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current[1]).toBe('updated');
  });

  it('supports function updater', () => {
    const { result } = renderHook(() => useDebouncedState(0, 300));

    act(() => {
      result.current[2]((prev) => prev + 1);
      result.current[2]((prev) => prev + 1);
      result.current[2]((prev) => prev + 1);
    });

    expect(result.current[0]).toBe(3);

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current[1]).toBe(3);
  });

  it('works with complex objects', () => {
    const { result } = renderHook(() =>
      useDebouncedState({ name: 'John', age: 30 }, 300)
    );

    act(() => {
      result.current[2]({ name: 'Jane', age: 25 });
    });

    expect(result.current[0]).toEqual({ name: 'Jane', age: 25 });
    expect(result.current[1]).toEqual({ name: 'John', age: 30 });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current[1]).toEqual({ name: 'Jane', age: 25 });
  });

  it('debounces rapid updates', () => {
    const { result } = renderHook(() => useDebouncedState('', 300));

    act(() => {
      result.current[2]('a');
      jest.advanceTimersByTime(100);
      result.current[2]('ab');
      jest.advanceTimersByTime(100);
      result.current[2]('abc');
    });

    expect(result.current[0]).toBe('abc');
    expect(result.current[1]).toBe('');

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current[1]).toBe('abc');
  });
});
