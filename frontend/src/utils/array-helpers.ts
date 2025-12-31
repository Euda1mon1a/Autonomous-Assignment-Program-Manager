/**
 * Array manipulation utilities for common operations.
 */

/**
 * Group array items by a key function.
 *
 * @param items - Array of items to group
 * @param keyFn - Function that extracts the grouping key from an item
 * @returns Object with keys mapped to arrays of items
 */
export function groupBy<T>(
  items: T[],
  keyFn: (item: T) => string
): Record<string, T[]> {
  const groups: Record<string, T[]> = {};

  for (const item of items) {
    const key = keyFn(item);
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
  }

  return groups;
}

/**
 * Sort array by a key function.
 *
 * @param items - Array of items to sort
 * @param keyFn - Function that extracts the sort key from an item
 * @param order - Sort order ('asc' or 'desc', default: 'asc')
 * @returns New sorted array
 */
export function sortBy<T>(
  items: T[],
  keyFn: (item: T) => number | string,
  order: 'asc' | 'desc' = 'asc'
): T[] {
  const sorted = [...items].sort((a, b) => {
    const keyA = keyFn(a);
    const keyB = keyFn(b);

    if (keyA < keyB) {
      return order === 'asc' ? -1 : 1;
    }
    if (keyA > keyB) {
      return order === 'asc' ? 1 : -1;
    }
    return 0;
  });

  return sorted;
}

/**
 * Get unique items based on a key function, preserving order.
 *
 * @param items - Array of items
 * @param keyFn - Function that extracts the uniqueness key from an item
 * @returns Array of unique items (first occurrence kept)
 */
export function uniqueBy<T>(
  items: T[],
  keyFn: (item: T) => string | number
): T[] {
  const seen = new Set<string | number>();
  const result: T[] = [];

  for (const item of items) {
    const key = keyFn(item);
    if (!seen.has(key)) {
      seen.add(key);
      result.push(item);
    }
  }

  return result;
}

/**
 * Partition an array into two arrays based on a predicate.
 *
 * @param items - Array of items to partition
 * @param predicate - Function that returns true for first array, false for second
 * @returns Tuple of [matching items, non-matching items]
 */
export function partition<T>(
  items: T[],
  predicate: (item: T) => boolean
): [T[], T[]] {
  const truthy: T[] = [];
  const falsy: T[] = [];

  for (const item of items) {
    if (predicate(item)) {
      truthy.push(item);
    } else {
      falsy.push(item);
    }
  }

  return [truthy, falsy];
}
