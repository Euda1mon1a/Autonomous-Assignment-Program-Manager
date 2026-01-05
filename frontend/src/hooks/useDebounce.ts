/**
 * useDebounce Hooks
 *
 * Provides debouncing utilities for search inputs and other frequently-changing values.
 * Helps reduce API calls and improve perceived performance.
 *
 * @example
 * ```tsx
 * // Debounce a search value
 * const [search, setSearch] = useState('');
 * const debouncedSearch = useDebounce(search, 300);
 *
 * // Use debouncedSearch in your query
 * useQuery({
 *   queryKey: ['items', debouncedSearch],
 *   queryFn: () => fetchItems(debouncedSearch),
 * });
 * ```
 */
import { useState, useEffect, useCallback, useRef } from 'react';

// ============================================================================
// useDebounce - Debounce a value
// ============================================================================

/**
 * Debounces a value, returning the debounced version after the specified delay.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns The debounced value
 *
 * @example
 * ```tsx
 * const [search, setSearch] = useState('');
 * const debouncedSearch = useDebounce(search, 300);
 *
 * // debouncedSearch updates 300ms after the last search change
 * ```
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set up the debounce timer
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up timer on value change or unmount
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

// ============================================================================
// useDebouncedCallback - Debounce a callback function
// ============================================================================

/**
 * Creates a debounced version of a callback function.
 * The callback will only be invoked after the specified delay has passed
 * since the last call.
 *
 * @param callback - The function to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns Object with debounced function and cancel method
 *
 * @example
 * ```tsx
 * const { debouncedCallback, cancel } = useDebouncedCallback(
 *   (value: string) => {
 *     console.log('Search:', value);
 *     performSearch(value);
 *   },
 *   300
 * );
 *
 * // In onChange handler
 * <input onChange={(e) => debouncedCallback(e.target.value)} />
 * ```
 */
export function useDebouncedCallback<T extends (...args: Parameters<T>) => void>(
  callback: T,
  delay: number = 300
): {
  debouncedCallback: (...args: Parameters<T>) => void;
  cancel: () => void;
  flush: () => void;
} {
  const callbackRef = useRef(callback);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const argsRef = useRef<Parameters<T> | null>(null);

  // Update callback ref on each render
  callbackRef.current = callback;

  const cancel = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    argsRef.current = null;
  }, []);

  const flush = useCallback(() => {
    if (timerRef.current && argsRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
      callbackRef.current(...argsRef.current);
      argsRef.current = null;
    }
  }, []);

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      argsRef.current = args;

      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }

      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        callbackRef.current(...args);
        argsRef.current = null;
      }, delay);
    },
    [delay]
  );

  // Clean up on unmount
  useEffect(() => {
    return cancel;
  }, [cancel]);

  return { debouncedCallback, cancel, flush };
}

// ============================================================================
// useDebouncedState - State with built-in debouncing
// ============================================================================

/**
 * Like useState, but with a debounced version of the value.
 * Returns both immediate and debounced values, plus a setter.
 *
 * @param initialValue - Initial value
 * @param delay - Debounce delay in milliseconds (default: 300ms)
 * @returns Tuple of [immediateValue, debouncedValue, setValue]
 *
 * @example
 * ```tsx
 * const [search, debouncedSearch, setSearch] = useDebouncedState('', 300);
 *
 * // Show immediate value in input
 * <input value={search} onChange={(e) => setSearch(e.target.value)} />
 *
 * // Use debounced value for API calls
 * useQuery({
 *   queryKey: ['search', debouncedSearch],
 *   queryFn: () => search(debouncedSearch),
 * });
 * ```
 */
export function useDebouncedState<T>(
  initialValue: T,
  delay: number = 300
): [T, T, React.Dispatch<React.SetStateAction<T>>] {
  const [value, setValue] = useState<T>(initialValue);
  const debouncedValue = useDebounce(value, delay);

  return [value, debouncedValue, setValue];
}

export default useDebounce;
