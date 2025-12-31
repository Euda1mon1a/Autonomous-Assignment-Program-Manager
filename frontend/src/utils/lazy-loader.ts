/**
 * Component lazy loading utilities for code splitting.
 *
 * Reduces initial bundle size by loading components on demand.
 */

import React from 'react';

export interface LazyLoadOptions {
  /** Delay before loading in milliseconds */
  delay?: number;
  /** Fallback component while loading */
  fallback?: React.ReactNode;
  /** Error boundary fallback */
  errorFallback?: React.ReactNode;
  /** Preload on hover */
  preloadOnHover?: boolean;
}

/**
 * Lazy load a component with retry logic.
 */
export function lazyLoadWithRetry<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): React.LazyExoticComponent<T> {
  const { delay = 0 } = options;

  return React.lazy(() => {
    return new Promise<{ default: T }>((resolve, reject) => {
      const loadComponent = async (retryCount = 3) => {
        try {
          if (delay > 0) {
            await new Promise((r) => setTimeout(r, delay));
          }

          const loadedModule = await importFn();
          resolve(loadedModule);
        } catch (error) {
          if (retryCount > 0) {
            // Exponential backoff
            const backoffDelay = Math.pow(2, 3 - retryCount) * 1000;
            setTimeout(() => loadComponent(retryCount - 1), backoffDelay);
          } else {
            reject(error);
          }
        }
      };

      loadComponent();
    });
  });
}

/**
 * Preload a lazy component.
 */
export function preloadComponent<T extends React.ComponentType<any>>(
  lazyComponent: React.LazyExoticComponent<T>
): void {
  // Trigger the lazy loading
  const temp = React.createElement(lazyComponent);
  // Component will be cached by React
}

/**
 * Lazy load multiple components in parallel.
 */
export async function preloadMultiple(
  components: React.LazyExoticComponent<any>[]
): Promise<void> {
  await Promise.all(components.map((comp) => preloadComponent(comp)));
}

/**
 * Route-based code splitting helper.
 */
export interface RouteConfig {
  path: string;
  component: () => Promise<{ default: React.ComponentType<any> }>;
  preload?: boolean;
}

export class RouteLazyLoader {
  private loadedRoutes = new Set<string>();
  private preloadQueue: string[] = [];

  constructor(private routes: RouteConfig[]) {}

  /**
   * Get lazy component for route.
   */
  getComponent(path: string): React.LazyExoticComponent<any> | null {
    const route = this.routes.find((r) => r.path === path);
    if (!route) return null;

    return lazyLoadWithRetry(route.component);
  }

  /**
   * Preload route component.
   */
  async preloadRoute(path: string): Promise<void> {
    if (this.loadedRoutes.has(path)) return;

    const route = this.routes.find((r) => r.path === path);
    if (!route) return;

    try {
      await route.component();
      this.loadedRoutes.add(path);
    } catch (error) {
      console.error(`Failed to preload route ${path}:`, error);
    }
  }

  /**
   * Preload all routes marked for preload.
   */
  async preloadMarkedRoutes(): Promise<void> {
    const routesToPreload = this.routes.filter((r) => r.preload);
    await Promise.all(routesToPreload.map((r) => this.preloadRoute(r.path)));
  }
}

/**
 * Intersection Observer-based lazy loading.
 */
export interface IntersectionLazyLoadOptions {
  root?: Element | null;
  rootMargin?: string;
  threshold?: number | number[];
}

export function useIntersectionLazyLoad(
  options: IntersectionLazyLoadOptions = {}
) {
  const [isIntersecting, setIsIntersecting] = React.useState(false);
  const targetRef = React.useRef<HTMLElement>(null);

  React.useEffect(() => {
    const target = targetRef.current;
    if (!target) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      {
        root: options.root,
        rootMargin: options.rootMargin || '50px',
        threshold: options.threshold || 0,
      }
    );

    observer.observe(target);

    return () => {
      observer.disconnect();
    };
  }, [options]);

  return {
    targetRef,
    isIntersecting,
  };
}

/**
 * Image lazy loading helper.
 */
export interface ImageLazyLoadProps {
  src: string;
  alt: string;
  placeholder?: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

export function useImageLazyLoad(props: ImageLazyLoadProps) {
  const { src, placeholder, onLoad, onError } = props;
  const [imageSrc, setImageSrc] = React.useState(placeholder || '');
  const [isLoading, setIsLoading] = React.useState(true);
  const [hasError, setHasError] = React.useState(false);

  const { targetRef, isIntersecting } = useIntersectionLazyLoad();

  React.useEffect(() => {
    if (!isIntersecting) return;

    const img = new Image();
    img.src = src;

    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
      onLoad?.();
    };

    img.onerror = (error) => {
      setHasError(true);
      setIsLoading(false);
      onError?.(new Error('Image failed to load'));
    };

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [isIntersecting, src, onLoad, onError]);

  return {
    targetRef,
    imageSrc,
    isLoading,
    hasError,
  };
}

/**
 * Bundle size monitoring.
 */
export class BundleSizeMonitor {
  private componentSizes = new Map<string, number>();

  recordComponentLoad(name: string, size: number): void {
    this.componentSizes.set(name, size);
  }

  getTotalSize(): number {
    return Array.from(this.componentSizes.values()).reduce(
      (sum, size) => sum + size,
      0
    );
  }

  getLargestComponents(count = 5): Array<[string, number]> {
    return Array.from(this.componentSizes.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, count);
  }

  getStats() {
    return {
      totalSize: this.getTotalSize(),
      componentCount: this.componentSizes.size,
      largestComponents: this.getLargestComponents(),
      averageSize:
        this.componentSizes.size > 0
          ? this.getTotalSize() / this.componentSizes.size
          : 0,
    };
  }
}
