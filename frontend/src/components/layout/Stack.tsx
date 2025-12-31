'use client';

import React from 'react';

export interface StackProps {
  children: React.ReactNode;
  direction?: 'row' | 'column';
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  wrap?: boolean;
  className?: string;
}

const directionStyles = {
  row: 'flex-row',
  column: 'flex-col',
};

const spacingStyles = {
  row: {
    none: 'gap-x-0',
    xs: 'gap-x-1',
    sm: 'gap-x-2',
    md: 'gap-x-4',
    lg: 'gap-x-6',
    xl: 'gap-x-8',
  },
  column: {
    none: 'gap-y-0',
    xs: 'gap-y-1',
    sm: 'gap-y-2',
    md: 'gap-y-4',
    lg: 'gap-y-6',
    xl: 'gap-y-8',
  },
};

const alignStyles = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  stretch: 'items-stretch',
  baseline: 'items-baseline',
};

const justifyStyles = {
  start: 'justify-start',
  center: 'justify-center',
  end: 'justify-end',
  between: 'justify-between',
  around: 'justify-around',
  evenly: 'justify-evenly',
};

/**
 * Stack component for flexible flexbox layouts
 *
 * @example
 * ```tsx
 * <Stack direction="column" spacing="md" align="center">
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 * </Stack>
 *
 * <Stack direction="row" justify="between" align="center">
 *   <div>Left</div>
 *   <div>Right</div>
 * </Stack>
 * ```
 */
export function Stack({
  children,
  direction = 'column',
  spacing = 'md',
  align = 'stretch',
  justify = 'start',
  wrap = false,
  className = '',
}: StackProps) {
  return (
    <div
      className={`flex ${directionStyles[direction]} ${spacingStyles[direction][spacing]} ${alignStyles[align]} ${justifyStyles[justify]} ${
        wrap ? 'flex-wrap' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}

/**
 * Horizontal stack (shorthand)
 */
export function HStack({
  children,
  spacing = 'md',
  align = 'center',
  justify = 'start',
  wrap = false,
  className = '',
}: Omit<StackProps, 'direction'>) {
  return (
    <Stack
      direction="row"
      spacing={spacing}
      align={align}
      justify={justify}
      wrap={wrap}
      className={className}
    >
      {children}
    </Stack>
  );
}

/**
 * Vertical stack (shorthand)
 */
export function VStack({
  children,
  spacing = 'md',
  align = 'stretch',
  justify = 'start',
  className = '',
}: Omit<StackProps, 'direction' | 'wrap'>) {
  return (
    <Stack
      direction="column"
      spacing={spacing}
      align={align}
      justify={justify}
      className={className}
    >
      {children}
    </Stack>
  );
}

/**
 * Spacer component for pushing elements apart
 */
export function Spacer({ className = '' }: { className?: string }) {
  return <div className={`flex-1 ${className}`} />;
}

/**
 * Divider component
 */
export function Divider({
  orientation = 'horizontal',
  className = '',
}: {
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}) {
  return (
    <div
      className={`${
        orientation === 'horizontal'
          ? 'w-full h-px border-t border-gray-200'
          : 'h-full w-px border-l border-gray-200'
      } ${className}`}
    />
  );
}
