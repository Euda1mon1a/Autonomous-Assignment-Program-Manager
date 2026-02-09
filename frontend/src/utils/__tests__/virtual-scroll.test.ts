import {
  calculateVirtualScroll,
  calculateVariableHeightScroll,
  VirtualScrollMetrics,
} from '../virtual-scroll';

describe('calculateVirtualScroll', () => {
  const baseOptions = {
    itemCount: 100,
    itemHeight: 40,
    viewportHeight: 200,
  };

  it('returns correct range at top', () => {
    const state = calculateVirtualScroll(0, baseOptions);
    expect(state.startIndex).toBe(0);
    // ceil((0+200)/40) + 3 = 8
    expect(state.endIndex).toBe(8);
    expect(state.totalHeight).toBe(4000);
    expect(state.offsetTop).toBe(0);
  });

  it('returns correct range when scrolled', () => {
    // Scrolled down 400px = 10 items, so first visible is index 10
    const state = calculateVirtualScroll(400, baseOptions);
    // startIndex = floor(400/40) - 3 = 7
    expect(state.startIndex).toBe(7);
    // endIndex = ceil((400+200)/40) + 3 = 18
    expect(state.endIndex).toBe(18);
    expect(state.offsetTop).toBe(7 * 40);
  });

  it('clamps startIndex to 0', () => {
    // With overscan=3, scrollTop near the top should clamp start to 0
    const state = calculateVirtualScroll(40, baseOptions);
    expect(state.startIndex).toBe(0);
  });

  it('clamps endIndex to last item', () => {
    // Scroll near the bottom
    const state = calculateVirtualScroll(3800, baseOptions);
    expect(state.endIndex).toBe(99);
  });

  it('handles custom overscan', () => {
    const state = calculateVirtualScroll(400, { ...baseOptions, overscan: 0 });
    // Without overscan: startIndex = floor(400/40) = 10
    expect(state.startIndex).toBe(10);
    // endIndex = ceil((400+200)/40) = 15
    expect(state.endIndex).toBe(15);
  });

  it('generates correct visibleIndices', () => {
    const state = calculateVirtualScroll(0, { ...baseOptions, overscan: 0 });
    // ceil((0+200)/40) = 5, so indices 0..5
    expect(state.visibleIndices).toEqual([0, 1, 2, 3, 4, 5]);
  });

  it('calculates totalHeight correctly', () => {
    const state = calculateVirtualScroll(0, {
      itemCount: 50,
      itemHeight: 30,
      viewportHeight: 300,
    });
    expect(state.totalHeight).toBe(1500);
  });

  it('handles single item', () => {
    const state = calculateVirtualScroll(0, {
      itemCount: 1,
      itemHeight: 40,
      viewportHeight: 200,
    });
    expect(state.startIndex).toBe(0);
    expect(state.endIndex).toBe(0);
    expect(state.visibleIndices).toEqual([0]);
  });

  it('handles zero items', () => {
    const state = calculateVirtualScroll(0, {
      itemCount: 0,
      itemHeight: 40,
      viewportHeight: 200,
    });
    expect(state.totalHeight).toBe(0);
    // With 0 items, endIndex calculation hits -1
    expect(state.endIndex).toBe(-1);
  });
});

describe('calculateVariableHeightScroll', () => {
  it('handles uniform heights', () => {
    const state = calculateVariableHeightScroll(0, {
      itemCount: 10,
      viewportHeight: 100,
      getItemHeight: () => 25,
      overscan: 0,
    });
    expect(state.startIndex).toBe(0);
    // 100/25 = 4 items visible, endIndex = 3
    expect(state.endIndex).toBe(3);
    expect(state.totalHeight).toBe(250);
  });

  it('handles variable heights', () => {
    // Items: 50, 30, 20, 50, 30, 20, 50, 30, 20, 50
    const heights = [50, 30, 20, 50, 30, 20, 50, 30, 20, 50];
    const state = calculateVariableHeightScroll(0, {
      itemCount: 10,
      viewportHeight: 100,
      getItemHeight: (i) => heights[i],
      overscan: 0,
    });
    expect(state.startIndex).toBe(0);
    expect(state.totalHeight).toBe(350);
  });

  it('calculates correct range when scrolled', () => {
    const state = calculateVariableHeightScroll(100, {
      itemCount: 20,
      viewportHeight: 100,
      getItemHeight: () => 25,
      overscan: 0,
    });
    // Variable-height algo: item at index 3 straddles scrollTop boundary
    expect(state.startIndex).toBe(3);
    expect(state.endIndex).toBe(7);
  });

  it('applies overscan correctly', () => {
    const state = calculateVariableHeightScroll(100, {
      itemCount: 20,
      viewportHeight: 100,
      getItemHeight: () => 25,
      overscan: 2,
    });
    // startIndex = 3 - 2 = 1
    expect(state.startIndex).toBe(1);
    // endIndex = 7 + 2 = 9
    expect(state.endIndex).toBe(9);
  });

  it('clamps overscan to bounds', () => {
    const state = calculateVariableHeightScroll(0, {
      itemCount: 5,
      viewportHeight: 200,
      getItemHeight: () => 25,
      overscan: 10,
    });
    expect(state.startIndex).toBe(0);
    expect(state.endIndex).toBe(4);
  });

  it('generates visibleIndices', () => {
    const state = calculateVariableHeightScroll(0, {
      itemCount: 5,
      viewportHeight: 100,
      getItemHeight: () => 50,
      overscan: 0,
    });
    // viewport=100, items=50 each → 2 visible (index 0,1)
    expect(state.visibleIndices).toEqual([0, 1]);
  });
});

describe('VirtualScrollMetrics', () => {
  let metrics: VirtualScrollMetrics;

  beforeEach(() => {
    metrics = new VirtualScrollMetrics();
  });

  it('starts with zero average', () => {
    expect(metrics.getAverageRenderCount()).toBe(0);
  });

  it('records render counts', () => {
    metrics.recordRender(10);
    metrics.recordRender(20);
    expect(metrics.getAverageRenderCount()).toBe(15);
  });

  it('returns stats', () => {
    metrics.recordRender(5);
    metrics.recordRender(15);
    const stats = metrics.getStats();
    expect(stats.averageRenderedItems).toBe(10);
    expect(stats.totalMeasurements).toBe(2);
    expect(stats.lastRenderTime).toBeGreaterThan(0);
  });

  it('limits to 100 measurements', () => {
    for (let i = 0; i < 110; i++) {
      metrics.recordRender(i);
    }
    const stats = metrics.getStats();
    expect(stats.totalMeasurements).toBe(100);
  });

  it('averages only last 100 after overflow', () => {
    for (let i = 0; i < 110; i++) {
      metrics.recordRender(i);
    }
    // Items 10-109, avg = (10+109)/2 = 59.5
    expect(metrics.getAverageRenderCount()).toBe(59.5);
  });
});
