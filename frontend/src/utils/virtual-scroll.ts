/**
 * Virtual scrolling utilities for rendering large lists efficiently.
 *
 * Only renders visible items plus a buffer, dramatically improving
 * performance for large datasets.
 */

export interface VirtualScrollOptions {
  /** Total number of items */
  itemCount: number;
  /** Height of each item in pixels */
  itemHeight: number;
  /** Height of the viewport in pixels */
  viewportHeight: number;
  /** Number of items to render above/below viewport (buffer) */
  overscan?: number;
}

export interface VirtualScrollState {
  /** Index of first visible item */
  startIndex: number;
  /** Index of last visible item */
  endIndex: number;
  /** Total height of all items */
  totalHeight: number;
  /** Offset from top for positioning */
  offsetTop: number;
  /** Visible item indices */
  visibleIndices: number[];
}

/**
 * Calculate which items should be rendered based on scroll position.
 */
export function calculateVirtualScroll(
  scrollTop: number,
  options: VirtualScrollOptions
): VirtualScrollState {
  const { itemCount, itemHeight, viewportHeight, overscan = 3 } = options;

  // Calculate visible range
  const startIndex = Math.max(
    0,
    Math.floor(scrollTop / itemHeight) - overscan
  );
  const endIndex = Math.min(
    itemCount - 1,
    Math.ceil((scrollTop + viewportHeight) / itemHeight) + overscan
  );

  // Calculate positioning
  const totalHeight = itemCount * itemHeight;
  const offsetTop = startIndex * itemHeight;

  // Generate visible indices array
  const visibleIndices = Array.from(
    { length: endIndex - startIndex + 1 },
    (_, i) => startIndex + i
  );

  return {
    startIndex,
    endIndex,
    totalHeight,
    offsetTop,
    visibleIndices,
  };
}

/**
 * React hook for virtual scrolling.
 */
export function useVirtualScroll<T>(
  items: T[],
  options: Omit<VirtualScrollOptions, 'itemCount'>
) {
  const [scrollTop, setScrollTop] = React.useState(0);

  const virtualState = React.useMemo(
    () =>
      calculateVirtualScroll(scrollTop, {
        ...options,
        itemCount: items.length,
      }),
    [scrollTop, items.length, options]
  );

  const handleScroll = React.useCallback(
    (event: React.UIEvent<HTMLElement>) => {
      setScrollTop(event.currentTarget.scrollTop);
    },
    []
  );

  const visibleItems = React.useMemo(
    () =>
      virtualState.visibleIndices.map((index) => ({
        index,
        item: items[index],
      })),
    [virtualState.visibleIndices, items]
  );

  return {
    ...virtualState,
    visibleItems,
    handleScroll,
  };
}

/**
 * Variable height virtual scrolling for items with different heights.
 */
export interface VariableHeightOptions {
  itemCount: number;
  viewportHeight: number;
  getItemHeight: (index: number) => number;
  overscan?: number;
}

export function calculateVariableHeightScroll(
  scrollTop: number,
  options: VariableHeightOptions
): VirtualScrollState {
  const { itemCount, viewportHeight, getItemHeight, overscan = 3 } = options;

  let currentHeight = 0;
  let startIndex = 0;
  let endIndex = 0;
  let offsetTop = 0;
  let totalHeight = 0;

  // Calculate total height and find start index
  for (let i = 0; i < itemCount; i++) {
    const itemHeight = getItemHeight(i);
    totalHeight += itemHeight;

    if (currentHeight + itemHeight < scrollTop && startIndex === i) {
      startIndex = i + 1;
      offsetTop = currentHeight + itemHeight;
    }

    if (currentHeight < scrollTop + viewportHeight) {
      endIndex = i;
    }

    currentHeight += itemHeight;
  }

  // Apply overscan
  startIndex = Math.max(0, startIndex - overscan);
  endIndex = Math.min(itemCount - 1, endIndex + overscan);

  const visibleIndices = Array.from(
    { length: endIndex - startIndex + 1 },
    (_, i) => startIndex + i
  );

  return {
    startIndex,
    endIndex,
    totalHeight,
    offsetTop,
    visibleIndices,
  };
}

/**
 * Performance metrics for virtual scrolling.
 */
export class VirtualScrollMetrics {
  private renderCounts: number[] = [];
  private lastRenderTime = 0;

  recordRender(itemCount: number): void {
    this.renderCounts.push(itemCount);
    this.lastRenderTime = Date.now();

    // Keep only last 100 measurements
    if (this.renderCounts.length > 100) {
      this.renderCounts.shift();
    }
  }

  getAverageRenderCount(): number {
    if (this.renderCounts.length === 0) return 0;
    return (
      this.renderCounts.reduce((a, b) => a + b, 0) / this.renderCounts.length
    );
  }

  getStats() {
    return {
      averageRenderedItems: this.getAverageRenderCount(),
      totalMeasurements: this.renderCounts.length,
      lastRenderTime: this.lastRenderTime,
    };
  }
}

// Ensure React is imported (user should have it in their project)
import * as React from 'react';
