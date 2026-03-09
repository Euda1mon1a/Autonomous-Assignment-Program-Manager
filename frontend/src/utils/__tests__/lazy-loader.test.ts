import { RouteLazyLoader, BundleSizeMonitor } from '../lazy-loader';
import type { RouteConfig } from '../lazy-loader';

describe('RouteLazyLoader', () => {
  const mockComponent = () =>
    Promise.resolve({ default: (() => null) as React.ComponentType<unknown> });

  const routes: RouteConfig[] = [
    { path: '/home', component: mockComponent },
    { path: '/about', component: mockComponent, preload: true },
    { path: '/settings', component: mockComponent, preload: true },
    { path: '/profile', component: mockComponent },
  ];

  it('returns lazy component for valid path', () => {
    const loader = new RouteLazyLoader(routes);
    const component = loader.getComponent('/home');
    expect(component).not.toBeNull();
  });

  it('returns null for unknown path', () => {
    const loader = new RouteLazyLoader(routes);
    expect(loader.getComponent('/unknown')).toBeNull();
  });

  it('preloads a specific route', async () => {
    const loadFn = jest.fn().mockResolvedValue({ default: () => null });
    const loader = new RouteLazyLoader([
      { path: '/test', component: loadFn },
    ]);

    await loader.preloadRoute('/test');
    expect(loadFn).toHaveBeenCalledTimes(1);
  });

  it('skips preload for already loaded route', async () => {
    const loadFn = jest.fn().mockResolvedValue({ default: () => null });
    const loader = new RouteLazyLoader([
      { path: '/test', component: loadFn },
    ]);

    await loader.preloadRoute('/test');
    await loader.preloadRoute('/test');
    expect(loadFn).toHaveBeenCalledTimes(1);
  });

  it('skips preload for unknown route', async () => {
    const loader = new RouteLazyLoader(routes);
    // Should not throw
    await loader.preloadRoute('/nonexistent');
  });

  it('handles preload failure silently', async () => {
    const loadFn = jest.fn().mockRejectedValue(new Error('Network error'));
    const loader = new RouteLazyLoader([
      { path: '/fail', component: loadFn },
    ]);

    // Should not throw
    await loader.preloadRoute('/fail');
    expect(loadFn).toHaveBeenCalled();
  });

  it('preloads only marked routes', async () => {
    const preloadFn = jest.fn().mockResolvedValue({ default: () => null });
    const noPreloadFn = jest.fn().mockResolvedValue({ default: () => null });

    const loader = new RouteLazyLoader([
      { path: '/a', component: preloadFn, preload: true },
      { path: '/b', component: noPreloadFn },
      { path: '/c', component: preloadFn, preload: true },
    ]);

    await loader.preloadMarkedRoutes();
    expect(preloadFn).toHaveBeenCalledTimes(2);
    expect(noPreloadFn).not.toHaveBeenCalled();
  });
});

describe('BundleSizeMonitor', () => {
  let monitor: BundleSizeMonitor;

  beforeEach(() => {
    monitor = new BundleSizeMonitor();
  });

  it('starts with zero total size', () => {
    expect(monitor.getTotalSize()).toBe(0);
  });

  it('records component sizes', () => {
    monitor.recordComponentLoad('Dashboard', 50000);
    monitor.recordComponentLoad('Settings', 30000);
    expect(monitor.getTotalSize()).toBe(80000);
  });

  it('overwrites size for same component', () => {
    monitor.recordComponentLoad('Dashboard', 50000);
    monitor.recordComponentLoad('Dashboard', 45000);
    expect(monitor.getTotalSize()).toBe(45000);
  });

  it('returns largest components', () => {
    monitor.recordComponentLoad('Small', 1000);
    monitor.recordComponentLoad('Large', 100000);
    monitor.recordComponentLoad('Medium', 50000);

    const largest = monitor.getLargestComponents(2);
    expect(largest).toEqual([
      ['Large', 100000],
      ['Medium', 50000],
    ]);
  });

  it('returns all components if fewer than count', () => {
    monitor.recordComponentLoad('Only', 5000);
    const largest = monitor.getLargestComponents(5);
    expect(largest).toHaveLength(1);
  });

  it('returns stats', () => {
    monitor.recordComponentLoad('A', 10000);
    monitor.recordComponentLoad('B', 20000);

    const stats = monitor.getStats();
    expect(stats.totalSize).toBe(30000);
    expect(stats.componentCount).toBe(2);
    expect(stats.averageSize).toBe(15000);
    expect(stats.largestComponents).toHaveLength(2);
  });

  it('returns zero average with no components', () => {
    const stats = monitor.getStats();
    expect(stats.averageSize).toBe(0);
    expect(stats.componentCount).toBe(0);
  });
});
