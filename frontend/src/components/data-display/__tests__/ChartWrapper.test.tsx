/**
 * Tests for ChartWrapper Component
 * Component: data-display/ChartWrapper - Wrapper for chart components
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { ChartWrapper } from '../ChartWrapper';

describe('ChartWrapper', () => {
  const MockChart = () => <div data-testid="mock-chart">Chart Content</div>;

  describe('Rendering', () => {
    it('renders chart title', () => {
      render(
        <ChartWrapper title="Test Chart">
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.getByText('Test Chart')).toBeInTheDocument();
    });

    it('renders children', () => {
      render(
        <ChartWrapper title="Test Chart">
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.getByTestId('mock-chart')).toBeInTheDocument();
    });

    it('renders description when provided', () => {
      render(
        <ChartWrapper title="Test Chart" description="This is a test chart">
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.getByText('This is a test chart')).toBeInTheDocument();
    });

    it('does not render description when not provided', () => {
      const { container } = render(
        <ChartWrapper title="Test Chart">
          <MockChart />
        </ChartWrapper>
      );
      // Description should not be present
      expect(container.querySelector('.text-gray-500')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading skeleton when loading', () => {
      const { container } = render(
        <ChartWrapper title="Test Chart" loading={true}>
          <MockChart />
        </ChartWrapper>
      );
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('hides chart when loading', () => {
      render(
        <ChartWrapper title="Test Chart" loading={true}>
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.queryByTestId('mock-chart')).not.toBeInTheDocument();
    });

    it('shows chart when not loading', () => {
      render(
        <ChartWrapper title="Test Chart" loading={false}>
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.getByTestId('mock-chart')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error message when error provided', () => {
      render(
        <ChartWrapper title="Test Chart" error="Failed to load chart">
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.getByText(/failed to load chart/i)).toBeInTheDocument();
    });

    it('hides chart when error exists', () => {
      render(
        <ChartWrapper title="Test Chart" error="Error occurred">
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.queryByTestId('mock-chart')).not.toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('has card styling', () => {
      const { container } = render(
        <ChartWrapper title="Test Chart">
          <MockChart />
        </ChartWrapper>
      );
      expect(container.firstChild).toHaveClass('card');
    });

    it('applies custom className', () => {
      const { container } = render(
        <ChartWrapper title="Test Chart" className="custom-class">
          <MockChart />
        </ChartWrapper>
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Edge Cases', () => {
    it('handles very long titles', () => {
      const longTitle = 'This is a very long chart title that might wrap to multiple lines';
      render(
        <ChartWrapper title={longTitle}>
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('handles very long descriptions', () => {
      const longDescription =
        'This is a very long description that provides extensive context about the chart data and what it represents.';
      render(
        <ChartWrapper title="Test Chart" description={longDescription}>
          <MockChart />
        </ChartWrapper>
      );
      expect(screen.getByText(longDescription)).toBeInTheDocument();
    });

    it('handles multiple children', () => {
      render(
        <ChartWrapper title="Test Chart">
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
        </ChartWrapper>
      );
      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
    });
  });
});
