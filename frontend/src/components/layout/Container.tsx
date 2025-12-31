'use client';

import React from 'react';

export interface ContainerProps {
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: boolean;
  center?: boolean;
  className?: string;
}

const maxWidthStyles = {
  sm: 'max-w-screen-sm',
  md: 'max-w-screen-md',
  lg: 'max-w-screen-lg',
  xl: 'max-w-screen-xl',
  '2xl': 'max-w-screen-2xl',
  full: 'max-w-full',
};

/**
 * Container component for consistent page layouts
 *
 * @example
 * ```tsx
 * <Container maxWidth="lg" padding center>
 *   <h1>Page Content</h1>
 * </Container>
 * ```
 */
export function Container({
  children,
  maxWidth = 'xl',
  padding = true,
  center = true,
  className = '',
}: ContainerProps) {
  return (
    <div
      className={`w-full ${maxWidthStyles[maxWidth]} ${
        center ? 'mx-auto' : ''
      } ${padding ? 'px-4 sm:px-6 lg:px-8' : ''} ${className}`}
    >
      {children}
    </div>
  );
}

/**
 * Section component with consistent spacing
 */
export function Section({
  children,
  spacing = 'md',
  className = '',
}: {
  children: React.ReactNode;
  spacing?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const spacingStyles = {
    sm: 'py-6',
    md: 'py-12',
    lg: 'py-20',
  };

  return (
    <section className={`${spacingStyles[spacing]} ${className}`}>
      {children}
    </section>
  );
}

/**
 * Page header component
 */
export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  className = '',
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  breadcrumbs?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`border-b border-gray-200 pb-6 mb-6 ${className}`}>
      {breadcrumbs && <div className="mb-4">{breadcrumbs}</div>}

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
          {description && (
            <p className="mt-2 text-gray-600">{description}</p>
          )}
        </div>

        {actions && <div className="ml-4 flex-shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
