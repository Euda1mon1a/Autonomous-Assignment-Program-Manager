/**
 * Debounce and throttle utilities for performance optimization.
 *
 * Limits function execution frequency to improve performance.
 */

/**
 * Debounce function - delays execution until after wait time has elapsed
 * since the last call.
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    if (timeout) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
      func.apply(context, args);
    }, wait);
  };
}

/**
 * Debounce with immediate execution on leading edge.
 */
export function debounceLeading<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;
    const callNow = !timeout;

    if (timeout) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
      timeout = null;
    }, wait);

    if (callNow) {
      func.apply(context, args);
    }
  };
}

/**
 * Throttle function - limits execution to once per wait period.
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  let lastRan: number | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    if (!lastRan) {
      func.apply(context, args);
      lastRan = Date.now();
    } else {
      if (timeout) {
        clearTimeout(timeout);
      }

      timeout = setTimeout(() => {
        if (Date.now() - lastRan! >= wait) {
          func.apply(context, args);
          lastRan = Date.now();
        }
      }, wait - (Date.now() - lastRan));
    }
  };
}

/**
 * Request Animation Frame throttle for smooth animations.
 */
export function rafThrottle<T extends (...args: any[]) => any>(
  func: T
): (...args: Parameters<T>) => void {
  let rafId: number | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    if (rafId) {
      return;
    }

    rafId = requestAnimationFrame(() => {
      func.apply(context, args);
      rafId = null;
    });
  };
}

/**
 * React hook for debounced value.
 */
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * React hook for debounced callback.
 */
import { useCallback, useRef } from 'react';

export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const callbackRef = useRef(callback);

  // Update callback ref
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args);
      }, delay);
    },
    [delay]
  );
}

/**
 * React hook for throttled callback.
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastRanRef = useRef<number | null>(null);
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();

      if (!lastRanRef.current || now - lastRanRef.current >= delay) {
        callbackRef.current(...args);
        lastRanRef.current = now;
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(() => {
          callbackRef.current(...args);
          lastRanRef.current = Date.now();
        }, delay - (now - lastRanRef.current));
      }
    },
    [delay]
  );
}

/**
 * Smart debounce that adapts delay based on input frequency.
 */
export class AdaptiveDebouncer<T extends (...args: any[]) => any> {
  private timeout: NodeJS.Timeout | null = null;
  private lastCallTime = 0;
  private callFrequencies: number[] = [];
  private minDelay: number;
  private maxDelay: number;

  constructor(
    private func: T,
    minDelay = 100,
    maxDelay = 1000
  ) {
    this.minDelay = minDelay;
    this.maxDelay = maxDelay;
  }

  call(...args: Parameters<T>): void {
    const now = Date.now();

    if (this.lastCallTime > 0) {
      const frequency = now - this.lastCallTime;
      this.callFrequencies.push(frequency);

      // Keep only last 10 measurements
      if (this.callFrequencies.length > 10) {
        this.callFrequencies.shift();
      }
    }

    this.lastCallTime = now;

    if (this.timeout) {
      clearTimeout(this.timeout);
    }

    const adaptiveDelay = this.calculateDelay();

    this.timeout = setTimeout(() => {
      this.func(...args);
    }, adaptiveDelay);
  }

  private calculateDelay(): number {
    if (this.callFrequencies.length === 0) {
      return this.minDelay;
    }

    const avgFrequency =
      this.callFrequencies.reduce((a, b) => a + b, 0) /
      this.callFrequencies.length;

    // Fast typing = longer delay, slow typing = shorter delay
    const delay = Math.min(
      this.maxDelay,
      Math.max(this.minDelay, avgFrequency * 2)
    );

    return delay;
  }
}

/**
 * Performance monitoring for debounce/throttle.
 */
export class DebounceMonitor {
  private stats = {
    totalCalls: 0,
    executedCalls: 0,
    skippedCalls: 0,
  };

  recordCall(executed: boolean): void {
    this.stats.totalCalls++;
    if (executed) {
      this.stats.executedCalls++;
    } else {
      this.stats.skippedCalls++;
    }
  }

  getReductionRate(): number {
    return this.stats.totalCalls > 0
      ? (this.stats.skippedCalls / this.stats.totalCalls) * 100
      : 0;
  }

  getStats() {
    return {
      ...this.stats,
      reductionRate: this.getReductionRate(),
    };
  }

  reset(): void {
    this.stats = {
      totalCalls: 0,
      executedCalls: 0,
      skippedCalls: 0,
    };
  }
}

/**
 * Monitored debounce function.
 */
export function debounceWithMonitoring<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  monitor: DebounceMonitor
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    monitor.recordCall(false);

    if (timeout) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
      monitor.recordCall(true);
      func.apply(context, args);
    }, wait);
  };
}
