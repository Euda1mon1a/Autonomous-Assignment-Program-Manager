import { groupBy, sortBy, uniqueBy, partition } from '../array-helpers';

describe('groupBy', () => {
  it('groups by key function', () => {
    const items = [
      { type: 'a', value: 1 },
      { type: 'b', value: 2 },
      { type: 'a', value: 3 },
    ];
    const result = groupBy(items, (item) => item.type);
    expect(result['a']).toHaveLength(2);
    expect(result['b']).toHaveLength(1);
  });

  it('returns empty object for empty array', () => {
    expect(groupBy([], (x) => String(x))).toEqual({});
  });

  it('handles all items in one group', () => {
    const result = groupBy([1, 2, 3], () => 'all');
    expect(result['all']).toEqual([1, 2, 3]);
  });

  it('handles each item in own group', () => {
    const result = groupBy(['a', 'b', 'c'], (x) => x);
    expect(Object.keys(result)).toHaveLength(3);
  });
});

describe('sortBy', () => {
  it('sorts ascending by default', () => {
    const items = [{ n: 3 }, { n: 1 }, { n: 2 }];
    const result = sortBy(items, (item) => item.n);
    expect(result.map((x) => x.n)).toEqual([1, 2, 3]);
  });

  it('sorts descending', () => {
    const items = [{ n: 1 }, { n: 3 }, { n: 2 }];
    const result = sortBy(items, (item) => item.n, 'desc');
    expect(result.map((x) => x.n)).toEqual([3, 2, 1]);
  });

  it('does not mutate original array', () => {
    const items = [{ n: 3 }, { n: 1 }];
    const result = sortBy(items, (item) => item.n);
    expect(items[0].n).toBe(3);
    expect(result[0].n).toBe(1);
  });

  it('sorts strings', () => {
    const items = ['banana', 'apple', 'cherry'];
    const result = sortBy(items, (x) => x);
    expect(result).toEqual(['apple', 'banana', 'cherry']);
  });

  it('returns empty array for empty input', () => {
    expect(sortBy([], (x) => x)).toEqual([]);
  });

  it('handles equal values', () => {
    const items = [{ n: 1 }, { n: 1 }];
    const result = sortBy(items, (item) => item.n);
    expect(result).toHaveLength(2);
  });
});

describe('uniqueBy', () => {
  it('removes duplicates by key', () => {
    const items = [
      { id: 1, name: 'a' },
      { id: 2, name: 'b' },
      { id: 1, name: 'c' },
    ];
    const result = uniqueBy(items, (item) => item.id);
    expect(result).toHaveLength(2);
    expect(result[0].name).toBe('a');
  });

  it('preserves order', () => {
    const result = uniqueBy([3, 1, 2, 1, 3], (x) => x);
    expect(result).toEqual([3, 1, 2]);
  });

  it('returns empty array for empty input', () => {
    expect(uniqueBy([], (x) => x)).toEqual([]);
  });

  it('keeps all unique items', () => {
    const result = uniqueBy([1, 2, 3], (x) => x);
    expect(result).toEqual([1, 2, 3]);
  });
});

describe('partition', () => {
  it('splits array by predicate', () => {
    const [evens, odds] = partition([1, 2, 3, 4, 5], (x) => x % 2 === 0);
    expect(evens).toEqual([2, 4]);
    expect(odds).toEqual([1, 3, 5]);
  });

  it('returns empty arrays for empty input', () => {
    const [a, b] = partition([], () => true);
    expect(a).toEqual([]);
    expect(b).toEqual([]);
  });

  it('puts all in first when all match', () => {
    const [match, noMatch] = partition([1, 2, 3], () => true);
    expect(match).toEqual([1, 2, 3]);
    expect(noMatch).toEqual([]);
  });

  it('puts all in second when none match', () => {
    const [match, noMatch] = partition([1, 2, 3], () => false);
    expect(match).toEqual([]);
    expect(noMatch).toEqual([1, 2, 3]);
  });

  it('preserves order within partitions', () => {
    const items = [
      { type: 'a', v: 1 },
      { type: 'b', v: 2 },
      { type: 'a', v: 3 },
    ];
    const [as, bs] = partition(items, (x) => x.type === 'a');
    expect(as.map((x) => x.v)).toEqual([1, 3]);
    expect(bs.map((x) => x.v)).toEqual([2]);
  });
});
