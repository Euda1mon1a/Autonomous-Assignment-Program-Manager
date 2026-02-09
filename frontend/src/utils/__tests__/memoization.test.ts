import {
  memoize,
  memoizeMulti,
  LRUCache,
  memoizeLRU,
  MemoizationMonitor,
  memoizeWithMonitoring,
  SelectiveMemoCache,
} from '../memoization';

describe('memoize', () => {
  it('caches result for same argument', () => {
    let callCount = 0;
    const fn = memoize((x: number) => {
      callCount++;
      return x * 2;
    });

    expect(fn(5)).toBe(10);
    expect(fn(5)).toBe(10);
    expect(callCount).toBe(1);
  });

  it('computes for different arguments', () => {
    let callCount = 0;
    const fn = memoize((x: number) => {
      callCount++;
      return x * 2;
    });

    fn(1);
    fn(2);
    expect(callCount).toBe(2);
  });

  it('works with string arguments', () => {
    const fn = memoize((s: string) => s.toUpperCase());
    expect(fn('hello')).toBe('HELLO');
    expect(fn('hello')).toBe('HELLO');
  });
});

describe('memoizeMulti', () => {
  it('caches result for same arguments', () => {
    let callCount = 0;
    const fn = memoizeMulti((a: number, b: number) => {
      callCount++;
      return a + b;
    });

    expect(fn(1, 2)).toBe(3);
    expect(fn(1, 2)).toBe(3);
    expect(callCount).toBe(1);
  });

  it('computes for different argument combinations', () => {
    let callCount = 0;
    const fn = memoizeMulti((a: number, b: number) => {
      callCount++;
      return a + b;
    });

    fn(1, 2);
    fn(2, 1);
    expect(callCount).toBe(2);
  });
});

describe('LRUCache', () => {
  it('stores and retrieves values', () => {
    const cache = new LRUCache<string, number>(10);
    cache.set('a', 1);
    expect(cache.get('a')).toBe(1);
  });

  it('returns undefined for missing keys', () => {
    const cache = new LRUCache<string, number>(10);
    expect(cache.get('missing')).toBeUndefined();
  });

  it('evicts oldest when over capacity', () => {
    const cache = new LRUCache<string, number>(2);
    cache.set('a', 1);
    cache.set('b', 2);
    cache.set('c', 3); // Should evict 'a'

    expect(cache.get('a')).toBeUndefined();
    expect(cache.get('b')).toBe(2);
    expect(cache.get('c')).toBe(3);
  });

  it('accessing a key refreshes its position', () => {
    const cache = new LRUCache<string, number>(2);
    cache.set('a', 1);
    cache.set('b', 2);
    cache.get('a'); // Refresh 'a'
    cache.set('c', 3); // Should evict 'b' (oldest)

    expect(cache.get('a')).toBe(1);
    expect(cache.get('b')).toBeUndefined();
    expect(cache.get('c')).toBe(3);
  });

  it('tracks size correctly', () => {
    const cache = new LRUCache<string, number>(10);
    expect(cache.size).toBe(0);
    cache.set('a', 1);
    expect(cache.size).toBe(1);
    cache.set('b', 2);
    expect(cache.size).toBe(2);
  });

  it('clears all entries', () => {
    const cache = new LRUCache<string, number>(10);
    cache.set('a', 1);
    cache.set('b', 2);
    cache.clear();
    expect(cache.size).toBe(0);
    expect(cache.get('a')).toBeUndefined();
  });

  it('updates existing key', () => {
    const cache = new LRUCache<string, number>(10);
    cache.set('a', 1);
    cache.set('a', 2);
    expect(cache.get('a')).toBe(2);
    expect(cache.size).toBe(1);
  });
});

describe('memoizeLRU', () => {
  it('caches with LRU eviction', () => {
    let callCount = 0;
    const fn = memoizeLRU((x: number) => {
      callCount++;
      return x * 2;
    }, 2);

    fn(1);
    fn(2);
    fn(1); // Cache hit
    expect(callCount).toBe(2);

    fn(3); // Evicts oldest (2)
    fn(2); // Cache miss - was evicted
    expect(callCount).toBe(4);
  });
});

describe('SelectiveMemoCache', () => {
  it('stores and retrieves values', () => {
    const cache = new SelectiveMemoCache<string, number>();
    cache.set('a', 1);
    expect(cache.get('a')).toBe(1);
  });

  it('returns undefined for missing keys', () => {
    const cache = new SelectiveMemoCache<string, number>();
    expect(cache.get('missing')).toBeUndefined();
  });

  it('invalidates by group', () => {
    const cache = new SelectiveMemoCache<string, number>();
    cache.set('a', 1, 'group1');
    cache.set('b', 2, 'group1');
    cache.set('c', 3, 'group2');

    cache.invalidateGroup('group1');
    expect(cache.get('a')).toBeUndefined();
    expect(cache.get('b')).toBeUndefined();
    expect(cache.get('c')).toBe(3);
  });

  it('invalidates by key', () => {
    const cache = new SelectiveMemoCache<string, number>();
    cache.set('a', 1, 'group1');
    cache.set('b', 2, 'group1');

    cache.invalidateKey('a');
    expect(cache.get('a')).toBeUndefined();
    expect(cache.get('b')).toBe(2);
  });

  it('clears all', () => {
    const cache = new SelectiveMemoCache<string, number>();
    cache.set('a', 1, 'group1');
    cache.set('b', 2);
    cache.clear();
    expect(cache.get('a')).toBeUndefined();
    expect(cache.get('b')).toBeUndefined();
  });
});

describe('MemoizationMonitor', () => {
  let monitor: MemoizationMonitor;

  beforeEach(() => {
    monitor = new MemoizationMonitor();
  });

  it('starts with zero stats', () => {
    const stats = monitor.getStats();
    expect(stats.hits).toBe(0);
    expect(stats.misses).toBe(0);
    expect(stats.hitRate).toBe(0);
  });

  it('records hits and misses', () => {
    monitor.recordHit();
    monitor.recordHit();
    monitor.recordMiss(10);

    const stats = monitor.getStats();
    expect(stats.hits).toBe(2);
    expect(stats.misses).toBe(1);
  });

  it('calculates hit rate', () => {
    monitor.recordHit();
    monitor.recordHit();
    monitor.recordHit();
    monitor.recordMiss(5);

    expect(monitor.getHitRate()).toBe(75);
  });

  it('calculates average compute time', () => {
    monitor.recordMiss(10);
    monitor.recordMiss(20);
    expect(monitor.getAverageComputeTime()).toBe(15);
  });

  it('returns 0 avg compute time with no misses', () => {
    expect(monitor.getAverageComputeTime()).toBe(0);
  });

  it('resets stats', () => {
    monitor.recordHit();
    monitor.recordMiss(10);
    monitor.reset();

    const stats = monitor.getStats();
    expect(stats.hits).toBe(0);
    expect(stats.misses).toBe(0);
    expect(stats.totalComputeTime).toBe(0);
  });
});

describe('memoizeWithMonitoring', () => {
  it('tracks cache hits and misses', () => {
    const monitor = new MemoizationMonitor();
    const fn = memoizeWithMonitoring((x: number) => x * 2, monitor);

    fn(5); // miss
    fn(5); // hit
    fn(10); // miss

    expect(monitor.getStats().hits).toBe(1);
    expect(monitor.getStats().misses).toBe(2);
  });
});
