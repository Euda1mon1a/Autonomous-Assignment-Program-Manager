/**
 * useDebounce Hook Tests
 *
 * Tests for debouncing utility hooks including useDebounce,
 * useDebouncedCallback, and useDebouncedState.
 */
import { renderHook, act } from '@testing-library/react';
import { useDebounce, useDebouncedCallback, useDebouncedState } from '@/hooks/useDebounce';

// Use fake timers for debounce tests
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

// ============================================================================
// useDebounce Tests
// ============================================================================

describe('useDebounce', () => {
  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));
    expect(result.current).toBe('initial');
  });

  it('should debounce value updates', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    expect(result.current).toBe('initial');

    // Update value
    rerender({ value: 'updated' });

    // Value should not change immediately
    expect(result.current).toBe('initial');

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Now value should be updated
    expect(result.current).toBe('updated');
  });

  it('should reset timer on rapid value changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    // Rapid updates
    rerender({ value: 'update1' });
    act(() => {
      jest.advanceTimersByTime(100);
    });

    rerender({ value: 'update2' });
    act(() => {
      jest.advanceTimersByTime(100);
    });

    rerender({ value: 'update3' });
    act(() => {
      jest.advanceTimersByTime(100);
    });

    // Should still be initial because timer keeps resetting
    expect(result.current).toBe('initial');

    // Now let timer complete
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Should show the last value
    expect(result.current).toBe('update3');
  });

  it('should use custom delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 1000),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'updated' });

    // Still initial after 300ms
    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(result.current).toBe('initial');

    // Still initial after 900ms
    act(() => {
      jest.advanceTimersByTime(600);
    });
    expect(result.current).toBe('initial');

    // Updated after 1000ms
    act(() => {
      jest.advanceTimersByTime(100);
    });
    expect(result.current).toBe('updated');
  });

  it('should cleanup timer on unmount', () => {
    const { rerender, unmount } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'updated' });
    unmount();

    // Timer should be cleared, no errors
    expect(() => {
      jest.advanceTimersByTime(300);
    }).not.toThrow();
  });

  it('should work with different value types', () => {
    // Number
    const { result: numResult, rerender: numRerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 0 } }
    );
    numRerender({ value: 42 });
    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(numResult.current).toBe(42);

    // Boolean
    const { result: boolResult, rerender: boolRerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: false } }
    );
    boolRerender({ value: true });
    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(boolResult.current).toBe(true);

    // Object
    const { result: objResult, rerender: objRerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: { key: 'initial' } } }
    );
    const newObj = { key: 'updated' };
    objRerender({ value: newObj });
    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(objResult.current).toBe(newObj);
  });
});

// ============================================================================
// useDebouncedCallback Tests
// ============================================================================

describe('useDebouncedCallback', () => {
  it('should debounce callback invocation', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current.debouncedCallback('arg1');
    });

    // Callback not called immediately
    expect(callback).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Now callback is called
    expect(callback).toHaveBeenCalledWith('arg1');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should cancel pending callback on cancel', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current.debouncedCallback('arg1');
    });

    act(() => {
      result.current.cancel();
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Callback should not be called
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

    // Callback should be called immediately without waiting
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

    // Not called yet
    expect(callback).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Only the last call should execute
    expect(callback).toHaveBeenCalledWith('arg3');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should cleanup timer on unmount', () => {
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

    // Callback should not be called after unmount
    expect(callback).not.toHaveBeenCalled();
  });

  it('should handle multiple arguments', () => {
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

// ============================================================================
// useDebouncedState Tests
// ============================================================================

describe('useDebouncedState', () => {
  it('should return immediate and debounced values', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    const [immediateValue, debouncedValue] = result.current;
    expect(immediateValue).toBe('initial');
    expect(debouncedValue).toBe('initial');
  });

  it('should update immediate value synchronously', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    act(() => {
      const [, , setValue] = result.current;
      setValue('updated');
    });

    const [immediateValue, debouncedValue] = result.current;
    expect(immediateValue).toBe('updated');
    expect(debouncedValue).toBe('initial'); // Still old value
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

    const [immediateValue, debouncedValue] = result.current;
    expect(immediateValue).toBe('updated');
    expect(debouncedValue).toBe('updated');
  });

  it('should handle rapid value changes', () => {
    const { result } = renderHook(() => useDebouncedState('initial', 300));

    act(() => {
      const [, , setValue] = result.current;
      setValue('update1');
    });
    act(() => {
      jest.advanceTimersByTime(100);
    });

    act(() => {
      const [, , setValue] = result.current;
      setValue('update2');
    });
    act(() => {
      jest.advanceTimersByTime(100);
    });

    act(() => {
      const [, , setValue] = result.current;
      setValue('update3');
    });

    const [immediateValue, debouncedValue] = result.current;
    expect(immediateValue).toBe('update3');
    expect(debouncedValue).toBe('initial'); // Timer keeps resetting

    act(() => {
      jest.advanceTimersByTime(300);
    });

    const [finalImmediate, finalDebounced] = result.current;
    expect(finalImmediate).toBe('update3');
    expect(finalDebounced).toBe('update3');
  });

  it('should work with functional updates', () => {
    const { result } = renderHook(() => useDebouncedState(0, 300));

    act(() => {
      const [, , setValue] = result.current;
      setValue((prev) => prev + 1);
    });

    const [immediateValue] = result.current;
    expect(immediateValue).toBe(1);

    act(() => {
      jest.advanceTimersByTime(300);
    });

    const [, debouncedValue] = result.current;
    expect(debouncedValue).toBe(1);
  });

  it('should cleanup timer on unmount', () => {
    const { result, unmount } = renderHook(() =>
      useDebouncedState('initial', 300)
    );

    act(() => {
      const [, , setValue] = result.current;
      setValue('updated');
    });

    unmount();

    // Should not throw
    expect(() => {
      jest.advanceTimersByTime(300);
    }).not.toThrow();
  });
});
