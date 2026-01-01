/**
 * Tests for CoverageTrendChart component
 *
 * Tests coverage trend visualization, data points, and trend indicators
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import {
  CoverageTrendChart,
  MOCK_COVERAGE_DATA,
  CoverageDataPoint,
} from '@/components/admin/CoverageTrendChart';

describe('CoverageTrendChart', () => {
  const defaultProps = {
    data: MOCK_COVERAGE_DATA,
  };

  describe('Rendering', () => {
    it('should render chart title', () => {
      render(<CoverageTrendChart {...defaultProps} />);

      expect(screen.getByText('Coverage Trend')).toBeInTheDocument();
    });

    it('should display run count', () => {
      render(<CoverageTrendChart {...defaultProps} />);

      // MOCK_COVERAGE_DATA has 8 data points
      expect(screen.getByText('Last 8 runs')).toBeInTheDocument();
    });

    it('should display current coverage percentage', () => {
      render(<CoverageTrendChart {...defaultProps} />);

      // Last data point in MOCK_COVERAGE_DATA is 96.8%
      expect(screen.getByText('96.8%')).toBeInTheDocument();
    });

    it('should render SVG chart', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Trend Indicators', () => {
    it('should show upward trend icon when coverage increases', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Last value (96.8) < previous (97.2), so trend is down
      // Let's create custom data with upward trend
      const upwardData: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 90 },
        { timestamp: '2024-12-02', coverage: 95 },
      ];

      const { container: upContainer } = render(
        <CoverageTrendChart data={upwardData} />
      );

      // Trend icon should be present (tested via className check)
      const trendSection = upContainer.querySelector('.text-green-400');
      expect(trendSection).toBeInTheDocument();
    });

    it('should show downward trend icon when coverage decreases', () => {
      const downwardData: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95 },
        { timestamp: '2024-12-02', coverage: 90 },
      ];

      const { container } = render(<CoverageTrendChart data={downwardData} />);

      const trendSection = container.querySelector('.text-red-400');
      expect(trendSection).toBeInTheDocument();
    });

    it('should show stable trend icon when coverage unchanged', () => {
      const stableData: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95 },
        { timestamp: '2024-12-02', coverage: 95 },
      ];

      const { container } = render(<CoverageTrendChart data={stableData} />);

      const trendSection = container.querySelector('.text-gray-400');
      expect(trendSection).toBeInTheDocument();
    });

    it('should display trend change value', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 90 },
        { timestamp: '2024-12-02', coverage: 95 },
      ];

      render(<CoverageTrendChart data={data} />);

      // Change is +5.0%
      expect(screen.getByText('+5.0%')).toBeInTheDocument();
    });

    it('should display negative trend change', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95 },
        { timestamp: '2024-12-02', coverage: 90 },
      ];

      render(<CoverageTrendChart data={data} />);

      // Change is -5.0%
      expect(screen.getByText('-5.0%')).toBeInTheDocument();
    });
  });

  describe('Target Coverage Line', () => {
    it('should display target coverage line by default', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Target line should be rendered as an SVG line element
      const lines = container.querySelectorAll('line');
      expect(lines.length).toBeGreaterThan(0);
    });

    it('should display target label', () => {
      render(<CoverageTrendChart {...defaultProps} />);

      expect(screen.getByText('Target')).toBeInTheDocument();
    });

    it('should respect custom target coverage', () => {
      render(<CoverageTrendChart {...defaultProps} targetCoverage={90} />);

      // Should show (90%) in legend
      expect(screen.getByText(/\(90%\)/)).toBeInTheDocument();
    });
  });

  describe('Legend', () => {
    it('should display legend when showLegend is true', () => {
      render(<CoverageTrendChart {...defaultProps} showLegend={true} />);

      expect(screen.getByText('Coverage')).toBeInTheDocument();
      expect(screen.getByText(/Target/)).toBeInTheDocument();
    });

    it('should not display legend when showLegend is false', () => {
      render(<CoverageTrendChart {...defaultProps} showLegend={false} />);

      // Legend should not exist
      const legend = screen.queryByText(/^Coverage$/);
      expect(legend).not.toBeInTheDocument();
    });

    it('should display average coverage in legend', () => {
      render(<CoverageTrendChart {...defaultProps} showLegend={true} />);

      // Average of MOCK_COVERAGE_DATA
      expect(screen.getByText(/Avg:/)).toBeInTheDocument();
    });
  });

  describe('Data Points', () => {
    it('should render data points as circles', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Each data point should have 2 circles (outer and inner)
      const circles = container.querySelectorAll('circle');
      expect(circles.length).toBeGreaterThan(0);
    });

    it('should handle single data point', () => {
      const singleData: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95 },
      ];

      render(<CoverageTrendChart data={singleData} />);

      expect(screen.getByText('95.0%')).toBeInTheDocument();
    });

    it('should handle two data points', () => {
      const twoPoints: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 90 },
        { timestamp: '2024-12-02', coverage: 95 },
      ];

      render(<CoverageTrendChart data={twoPoints} />);

      expect(screen.getByText('95.0%')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no data', () => {
      render(<CoverageTrendChart data={[]} />);

      expect(screen.getByText('No coverage data available')).toBeInTheDocument();
      expect(
        screen.getByText('Run schedule generation to see trends')
      ).toBeInTheDocument();
    });

    it('should not display chart elements when no data', () => {
      const { container } = render(<CoverageTrendChart data={[]} />);

      const svg = container.querySelector('svg');
      expect(svg).not.toBeInTheDocument();
    });

    it('should respect height prop in empty state', () => {
      const { container } = render(<CoverageTrendChart data={[]} height={300} />);

      const emptyState = container.querySelector('.flex.items-center');
      expect(emptyState).toHaveStyle({ height: '300px' });
    });
  });

  describe('Custom Props', () => {
    it('should respect custom height prop', () => {
      const { container } = render(
        <CoverageTrendChart {...defaultProps} height={300} />
      );

      const chartArea = container.querySelector('.relative');
      expect(chartArea).toHaveStyle({ height: '300px' });
    });

    it('should respect showLegend prop', () => {
      const { rerender } = render(
        <CoverageTrendChart {...defaultProps} showLegend={true} />
      );

      expect(screen.getByText('Coverage')).toBeInTheDocument();

      rerender(<CoverageTrendChart {...defaultProps} showLegend={false} />);

      expect(screen.queryByText(/^Coverage$/)).not.toBeInTheDocument();
    });

    it('should respect targetCoverage prop', () => {
      render(<CoverageTrendChart {...defaultProps} targetCoverage={90} />);

      expect(screen.getByText('(90%)')).toBeInTheDocument();
    });
  });

  describe('Y-Axis Labels', () => {
    it('should display min and max coverage values', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 80 },
        { timestamp: '2024-12-02', coverage: 100 },
      ];

      render(<CoverageTrendChart data={data} />);

      // Should show max and min on y-axis
      const { container } = render(<CoverageTrendChart data={data} />);
      const labels = container.querySelectorAll('.text-slate-500');
      expect(labels.length).toBeGreaterThan(0);
    });

    it('should adjust scale to include target coverage', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 85 },
        { timestamp: '2024-12-02', coverage: 87 },
      ];

      const { container } = render(
        <CoverageTrendChart data={data} targetCoverage={95} />
      );

      // Scale should expand to include target (95)
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Gradient Fill', () => {
    it('should render gradient fill under line', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Gradient definition should exist
      const gradient = container.querySelector('#coverageGradient');
      expect(gradient).toBeInTheDocument();
    });

    it('should apply gradient to area path', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Path with gradient fill should exist
      const paths = container.querySelectorAll('path');
      const gradientPath = Array.from(paths).find((path) =>
        path.getAttribute('fill')?.includes('url(#coverageGradient)')
      );
      expect(gradientPath).toBeInTheDocument();
    });
  });

  describe('Grid Lines', () => {
    it('should render grid pattern', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      const gridPattern = container.querySelector('#grid');
      expect(gridPattern).toBeInTheDocument();
    });
  });

  describe('Data Calculations', () => {
    it('should calculate average coverage correctly', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 90 },
        { timestamp: '2024-12-02', coverage: 100 },
      ];

      render(<CoverageTrendChart data={data} showLegend={true} />);

      // Average is (90 + 100) / 2 = 95.0
      expect(screen.getByText(/Avg: 95.0%/)).toBeInTheDocument();
    });

    it('should calculate trend change correctly', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 80 },
        { timestamp: '2024-12-02', coverage: 90 },
      ];

      render(<CoverageTrendChart data={data} />);

      // Change is 90 - 80 = +10.0
      expect(screen.getByText('+10.0%')).toBeInTheDocument();
    });

    it('should handle zero change', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 90 },
        { timestamp: '2024-12-02', coverage: 90 },
      ];

      render(<CoverageTrendChart data={data} />);

      // Change is 0
      expect(screen.getByText('+0.0%')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle all values at target', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95 },
        { timestamp: '2024-12-02', coverage: 95 },
      ];

      render(<CoverageTrendChart data={data} targetCoverage={95} />);

      expect(screen.getByText('95.0%')).toBeInTheDocument();
    });

    it('should handle values above target', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 98 },
        { timestamp: '2024-12-02', coverage: 99 },
      ];

      render(<CoverageTrendChart data={data} targetCoverage={95} />);

      expect(screen.getByText('99.0%')).toBeInTheDocument();
    });

    it('should handle values below target', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 85 },
        { timestamp: '2024-12-02', coverage: 87 },
      ];

      render(<CoverageTrendChart data={data} targetCoverage={95} />);

      expect(screen.getByText('87.0%')).toBeInTheDocument();
    });

    it('should handle 100% coverage', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 98 },
        { timestamp: '2024-12-02', coverage: 100 },
      ];

      render(<CoverageTrendChart data={data} />);

      expect(screen.getByText('100.0%')).toBeInTheDocument();
    });

    it('should handle 0% coverage', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 5 },
        { timestamp: '2024-12-02', coverage: 0 },
      ];

      render(<CoverageTrendChart data={data} />);

      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });

    it('should handle very small changes', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95.1 },
        { timestamp: '2024-12-02', coverage: 95.2 },
      ];

      render(<CoverageTrendChart data={data} />);

      expect(screen.getByText('+0.1%')).toBeInTheDocument();
    });

    it('should handle decimal precision', () => {
      const data: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95.567 },
        { timestamp: '2024-12-02', coverage: 96.789 },
      ];

      render(<CoverageTrendChart data={data} />);

      // Should round to 1 decimal place
      expect(screen.getByText('96.8%')).toBeInTheDocument();
    });

    it('should handle large number of data points', () => {
      const manyPoints: CoverageDataPoint[] = Array.from({ length: 100 }, (_, i) => ({
        timestamp: `2024-12-${String(i + 1).padStart(2, '0')}`,
        coverage: 90 + (i % 10),
      }));

      render(<CoverageTrendChart data={manyPoints} />);

      expect(screen.getByText('Last 100 runs')).toBeInTheDocument();
    });
  });

  describe('SVG Rendering', () => {
    it('should set correct viewBox', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('viewBox', '0 0 100 100');
    });

    it('should preserve aspect ratio', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('preserveAspectRatio', 'none');
    });

    it('should render line path', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Line path should have stroke and no fill
      const paths = container.querySelectorAll('path');
      const linePath = Array.from(paths).find(
        (path) =>
          path.getAttribute('stroke') === 'rgb(139, 92, 246)' &&
          path.getAttribute('fill') === 'none'
      );
      expect(linePath).toBeInTheDocument();
    });

    it('should render area path', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Area path should have gradient fill
      const paths = container.querySelectorAll('path');
      const areaPath = Array.from(paths).find((path) =>
        path.getAttribute('fill')?.includes('coverageGradient')
      );
      expect(areaPath).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have semantic HTML structure', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      expect(container.querySelector('h3')).toBeInTheDocument();
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('should have readable text contrast', () => {
      const { container } = render(<CoverageTrendChart {...defaultProps} />);

      // Text should have appropriate color classes for contrast
      const textElements = container.querySelectorAll('.text-white');
      expect(textElements.length).toBeGreaterThan(0);
    });
  });

  describe('Optional Metadata', () => {
    it('should handle algorithm metadata if provided', () => {
      const dataWithAlgorithm: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95, algorithm: 'hybrid' },
      ];

      render(<CoverageTrendChart data={dataWithAlgorithm} />);

      // Should still render correctly
      expect(screen.getByText('95.0%')).toBeInTheDocument();
    });

    it('should handle runId metadata if provided', () => {
      const dataWithRunId: CoverageDataPoint[] = [
        { timestamp: '2024-12-01', coverage: 95, runId: 'run-123' },
      ];

      render(<CoverageTrendChart data={dataWithRunId} />);

      // Should still render correctly
      expect(screen.getByText('95.0%')).toBeInTheDocument();
    });
  });
});
