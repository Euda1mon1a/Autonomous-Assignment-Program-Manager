'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';

export interface ChartWrapperProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  loading?: boolean;
  error?: string;
  className?: string;
}

/**
 * ChartWrapper component for consistent chart presentation
 *
 * @example
 * ```tsx
 * <ChartWrapper
 *   title="Work Hours Trend"
 *   description="Weekly work hours over time"
 *   actions={<Button size="sm">Export</Button>}
 * >
 *   <LineChart data={data} />
 * </ChartWrapper>
 * ```
 */
export function ChartWrapper({
  title,
  description,
  children,
  actions,
  loading = false,
  error,
  className = '',
}: ChartWrapperProps) {
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="animate-pulse space-y-3 w-full">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-red-600">
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          {actions && <div>{actions}</div>}
        </div>
      </CardHeader>
      <CardContent>
        {children}
      </CardContent>
    </Card>
  );
}
