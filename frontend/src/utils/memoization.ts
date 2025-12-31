/**
 * Memoization utilities for performance optimization.
 *
 * Caches expensive computations to avoid re-computation.
 */

/**
 * Simple memoization for functions with single argument.
 */
export function memoize<T, R>(fn: (arg: T) => R): (arg: T) => R {
  const cache = new Map<T, R>();

  return (arg: T): R => {
    if (cache.has(arg)) {
      return cache.get(arg)!;
    }

    const result = fn(arg);
    cache.set(arg, result);
    return result;
  };
}

/**
 * Memoization with multiple arguments using JSON serialization.
 */
export function memoizeMulti<T extends any[], R>(
  fn: (...args: T) => R
): (...args: T) => R {
  const cache = new Map<string, R>();

  return (...args: T): R => {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key)!;
    }

    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

/**
 * LRU (Least Recently Used) cache for memoization.
 */
export class LRUCache<K, V> {
  private cache = new Map<K, V>();
  private maxSize: number;

  constructor(maxSize = 100) {
    this.maxSize = maxSize;
  }

  get(key: K): V | undefined {
    if (!this.cache.has(key)) {
      return undefined;
    }

    // Move to end (most recent)
    const value = this.cache.get(key)!;
    this.cache.delete(key);
    this.cache.set(key, value);

    return value;
  }

  set(key: K, value: V): void {
    // Remove if exists (to update position)
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }

    // Add to end
    this.cache.set(key, value);

    // Evict oldest if over size
    if (this.cache.size > this.maxSize) {
      const firstKey = this.cache.keys().next().value;
<<<<<<< HEAD
      if (firstKey !== undefined) {
        this.cache.delete(firstKey);
      }
=======
      this.cache.delete(firstKey);
>>>>>>> origin/main
    }
  }

  clear(): void {
    this.cache.clear();
  }

  get size(): number {
    return this.cache.size;
  }
}

/**
 * Memoization with LRU cache.
 */
export function memoizeLRU<T extends any[], R>(
  fn: (...args: T) => R,
  maxSize = 100
): (...args: T) => R {
  const cache = new LRUCache<string, R>(maxSize);

  return (...args: T): R => {
    const key = JSON.stringify(args);
    const cached = cache.get(key);

    if (cached !== undefined) {
      return cached;
    }

    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

/**
 * Memoization with TTL (Time To Live).
 */
export function memoizeWithTTL<T extends any[], R>(
  fn: (...args: T) => R,
  ttlMs = 60000 // 1 minute default
): (...args: T) => R {
  const cache = new Map<string, { value: R; expiry: number }>();

  return (...args: T): R => {
    const key = JSON.stringify(args);
    const now = Date.now();

    const cached = cache.get(key);
    if (cached && cached.expiry > now) {
      return cached.value;
    }

    const result = fn(...args);
    cache.set(key, {
      value: result,
      expiry: now + ttlMs,
    });

    // Clean up expired entries
    for (const [k, v] of cache.entries()) {
      if (v.expiry <= now) {
        cache.delete(k);
      }
    }

    return result;
  };
}

/**
 * React hook for memoized computations with dependencies.
 */
import { useMemo, useRef } from 'react';

export function useDeepMemo<T>(
  factory: () => T,
  deps: any[]
): T {
  const ref = useRef<{ deps: any[]; value: T }>();

  if (
    !ref.current ||
    !shallowEqual(ref.current.deps, deps)
  ) {
    ref.current = {
      deps,
      value: factory(),
    };
  }

  return ref.current.value;
}

/**
 * Shallow equality check for arrays.
 */
function shallowEqual(arr1: any[], arr2: any[]): boolean {
  if (arr1.length !== arr2.length) return false;

  for (let i = 0; i < arr1.length; i++) {
    if (!Object.is(arr1[i], arr2[i])) {
      return false;
    }
  }

  return true;
}

/**
 * Memoization with selective invalidation.
 */
export class SelectiveMemoCache<K, V> {
  private cache = new Map<K, V>();
  private groups = new Map<string, Set<K>>();

  set(key: K, value: V, group?: string): void {
    this.cache.set(key, value);

    if (group) {
      if (!this.groups.has(group)) {
        this.groups.set(group, new Set());
      }
      this.groups.get(group)!.add(key);
    }
  }

  get(key: K): V | undefined {
    return this.cache.get(key);
  }

  invalidateGroup(group: string): void {
    const keys = this.groups.get(group);
    if (keys) {
      for (const key of keys) {
        this.cache.delete(key);
      }
      this.groups.delete(group);
    }
  }

  invalidateKey(key: K): void {
    this.cache.delete(key);

    // Remove from all groups
    for (const [, keys] of this.groups) {
      keys.delete(key);
    }
  }

  clear(): void {
    this.cache.clear();
    this.groups.clear();
  }
}

/**
 * Performance monitoring for memoized functions.
 */
export class MemoizationMonitor {
  private stats = {
    hits: 0,
    misses: 0,
    totalComputeTime: 0,
  };

  recordHit(): void {
    this.stats.hits++;
  }

  recordMiss(computeTime: number): void {
    this.stats.misses++;
    this.stats.totalComputeTime += computeTime;
  }

  getHitRate(): number {
    const total = this.stats.hits + this.stats.misses;
    return total > 0 ? (this.stats.hits / total) * 100 : 0;
  }

  getAverageComputeTime(): number {
    return this.stats.misses > 0
      ? this.stats.totalComputeTime / this.stats.misses
      : 0;
  }

  getStats() {
    return {
      ...this.stats,
      hitRate: this.getHitRate(),
      averageComputeTime: this.getAverageComputeTime(),
    };
  }

  reset(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      totalComputeTime: 0,
    };
  }
}

/**
 * Monitored memoization.
 */
export function memoizeWithMonitoring<T extends any[], R>(
  fn: (...args: T) => R,
  monitor: MemoizationMonitor
): (...args: T) => R {
  const cache = new Map<string, R>();

  return (...args: T): R => {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      monitor.recordHit();
      return cache.get(key)!;
    }

    const start = performance.now();
    const result = fn(...args);
    const computeTime = performance.now() - start;

    monitor.recordMiss(computeTime);
    cache.set(key, result);
    return result;
  };
}
