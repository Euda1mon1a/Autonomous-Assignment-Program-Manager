'use client';

import React from 'react';

export interface GridProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3 | 4 | 6 | 12;
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  responsive?: boolean;
  className?: string;
}

const columnStyles = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
  6: 'grid-cols-6',
  12: 'grid-cols-12',
};

const responsiveColumnStyles = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 md:grid-cols-2',
  3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  6: 'grid-cols-1 md:grid-cols-3 lg:grid-cols-6',
  12: 'grid-cols-1 md:grid-cols-6 lg:grid-cols-12',
};

const gapStyles = {
  none: 'gap-0',
  xs: 'gap-1',
  sm: 'gap-2',
  md: 'gap-4',
  lg: 'gap-6',
  xl: 'gap-8',
};

/**
 * Grid component for flexible layouts
 *
 * @example
 * ```tsx
 * <Grid columns={3} gap="md" responsive>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </Grid>
 * ```
 */
export function Grid({
  children,
  columns = 3,
  gap = 'md',
  responsive = true,
  className = '',
}: GridProps) {
  const cols = responsive ? responsiveColumnStyles[columns] : columnStyles[columns];

  return (
    <div className={`grid ${cols} ${gapStyles[gap]} ${className}`}>
      {children}
    </div>
  );
}

/**
 * GridItem component for spanning multiple columns
 */
export function GridItem({
  children,
  colSpan = 1,
  rowSpan = 1,
  className = '',
}: {
  children: React.ReactNode;
  colSpan?: number;
  rowSpan?: number;
  className?: string;
}) {
  return (
    <div
      className={className}
      style={{
        gridColumn: colSpan > 1 ? `span ${colSpan}` : undefined,
        gridRow: rowSpan > 1 ? `span ${rowSpan}` : undefined,
      }}
    >
      {children}
    </div>
  );
}

/**
 * Auto-fit grid that automatically adjusts column count
 */
export function AutoGrid({
  children,
  minWidth = 250,
  gap = 'md',
  className = '',
}: {
  children: React.ReactNode;
  minWidth?: number;
  gap?: GridProps['gap'];
  className?: string;
}) {
  return (
    <div
      className={`grid ${gapStyles[gap!]} ${className}`}
      style={{
        gridTemplateColumns: `repeat(auto-fit, minmax(${minWidth}px, 1fr))`,
      }}
    >
      {children}
    </div>
  );
}
