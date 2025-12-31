/**
 * Tests for HeatmapLegend component
 * Tests legend rendering, color scales, and view mode descriptions
 */

import { render, screen } from '@/test-utils';
import { HeatmapLegend, CompactHeatmapLegend } from '@/features/heatmap/HeatmapLegend';
import { heatmapMockFactories } from './heatmap-mocks';
import { createWrapper } from '../../utils/test-utils';
import {
  DEFAULT_COLOR_SCALES,
  ACTIVITY_TYPE_COLORS,
  COVERAGE_INDICATOR_COLORS,
} from '@/features/heatmap/types';

describe('HeatmapLegend', () => {
  describe('Basic Rendering', () => {
    it('should render legend title', () => {
      render(<HeatmapLegend />, { wrapper: createWrapper() });

      expect(screen.getByText('Legend')).toBeInTheDocument();
    });

    it('should render intensity scale section', () => {
      render(<HeatmapLegend />, { wrapper: createWrapper() });

      expect(screen.getByText('Intensity Scale')).toBeInTheDocument();
    });

    it('should render activity types section by default', () => {
      render(<HeatmapLegend />, { wrapper: createWrapper() });

      expect(screen.getByText('Activity Types')).toBeInTheDocument();
    });

    it('should render coverage indicators section by default', () => {
      render(<HeatmapLegend />, { wrapper: createWrapper() });

      expect(screen.getByText('Coverage Status')).toBeInTheDocument();
    });

    it('should hide activity types when showActivityTypes is false', () => {
      render(<HeatmapLegend showActivityTypes={false} />, { wrapper: createWrapper() });

      expect(screen.queryByText('Activity Types')).not.toBeInTheDocument();
    });

    it('should hide coverage indicators when showCoverageIndicators is false', () => {
      render(<HeatmapLegend showCoverageIndicators={false} />, { wrapper: createWrapper() });

      expect(screen.queryByText('Coverage Status')).not.toBeInTheDocument();
    });
  });

  describe('Color Scale Display', () => {
    it('should use default coverage color scale when no custom scale provided', () => {
      const { container } = render(<HeatmapLegend viewMode="coverage" />, {
        wrapper: createWrapper(),
      });

      const gradientBar = container.querySelector('.h-6.rounded-md');
      expect(gradientBar).toBeInTheDocument();

      const expectedGradient = `linear-gradient(to right, ${DEFAULT_COLOR_SCALES.coverage.colors.join(', ')})`;
      expect(gradientBar).toHaveStyle({ background: expectedGradient });
    });

    it('should use default workload color scale for workload view', () => {
      const { container } = render(<HeatmapLegend viewMode="workload" />, {
        wrapper: createWrapper(),
      });

      const gradientBar = container.querySelector('.h-6.rounded-md');
      const expectedGradient = `linear-gradient(to right, ${DEFAULT_COLOR_SCALES.workload.colors.join(', ')})`;
      expect(gradientBar).toHaveStyle({ background: expectedGradient });
    });

    it('should use custom color scale when provided', () => {
      const customScale = heatmapMockFactories.colorScale({
        colors: ['#000000', '#ffffff'],
        min: 0,
        max: 50,
      });

      const { container } = render(<HeatmapLegend colorScale={customScale} />, {
        wrapper: createWrapper(),
      });

      const gradientBar = container.querySelector('.h-6.rounded-md');
      const expectedGradient = 'linear-gradient(to right, #000000, #ffffff)';
      expect(gradientBar).toHaveStyle({ background: expectedGradient });
    });

    it('should display min and max values', () => {
      const customScale = heatmapMockFactories.colorScale({
        min: 0,
        max: 100,
      });

      render(<HeatmapLegend colorScale={customScale} />, { wrapper: createWrapper() });

      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('should display scale labels when provided', () => {
      const customScale = heatmapMockFactories.colorScale({
        labels: ['Low', 'Medium', 'High'],
      });

      render(<HeatmapLegend colorScale={customScale} />, { wrapper: createWrapper() });

      expect(screen.getByText('Low')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
    });
  });

  describe('Activity Type Colors', () => {
    it('should render all activity types', () => {
      render(<HeatmapLegend showActivityTypes={true} />, { wrapper: createWrapper() });

      const activityTypes = Object.keys(ACTIVITY_TYPE_COLORS);
      activityTypes.forEach((type) => {
        const label = type.replace('_', ' ');
        expect(screen.getByText(label)).toBeInTheDocument();
      });
    });

    it('should display correct color for each activity type', () => {
      const { container } = render(<HeatmapLegend showActivityTypes={true} />, {
        wrapper: createWrapper(),
      });

      const colorBoxes = container.querySelectorAll('.w-4.h-4.rounded');

      // Should have color boxes for activity types and coverage indicators
      expect(colorBoxes.length).toBeGreaterThan(0);
    });

    it('should render activity type labels with capitalize class', () => {
      const { container } = render(<HeatmapLegend showActivityTypes={true} />, {
        wrapper: createWrapper(),
      });

      // The capitalize class will make first letter uppercase
      const labels = container.querySelectorAll('.capitalize');
      expect(labels.length).toBeGreaterThan(0);
    });
  });

  describe('Coverage Indicators', () => {
    it('should render all coverage indicators', () => {
      render(<HeatmapLegend showCoverageIndicators={true} />, { wrapper: createWrapper() });

      const indicators = Object.keys(COVERAGE_INDICATOR_COLORS);
      indicators.forEach((indicator) => {
        const label = indicator.replace('_', ' ');
        expect(screen.getByText(label)).toBeInTheDocument();
      });
    });

    it('should display full coverage indicator', () => {
      const { container } = render(<HeatmapLegend showCoverageIndicators={true} />, {
        wrapper: createWrapper(),
      });

      // The capitalize class visually capitalizes, but textContent returns the raw lowercase text
      const indicators = container.querySelectorAll('.capitalize');
      const texts = Array.from(indicators).map((el) => el.textContent);
      expect(texts).toContain('full');
    });

    it('should display partial coverage indicator', () => {
      const { container } = render(<HeatmapLegend showCoverageIndicators={true} />, {
        wrapper: createWrapper(),
      });

      const indicators = container.querySelectorAll('.capitalize');
      const texts = Array.from(indicators).map((el) => el.textContent);
      expect(texts).toContain('partial');
    });

    it('should display gap indicator', () => {
      const { container } = render(<HeatmapLegend showCoverageIndicators={true} />, {
        wrapper: createWrapper(),
      });

      const indicators = container.querySelectorAll('.capitalize');
      const texts = Array.from(indicators).map((el) => el.textContent);
      expect(texts).toContain('gap');
    });

    it('should display overcovered indicator', () => {
      const { container } = render(<HeatmapLegend showCoverageIndicators={true} />, {
        wrapper: createWrapper(),
      });

      const indicators = container.querySelectorAll('.capitalize');
      const texts = Array.from(indicators).map((el) => el.textContent);
      expect(texts).toContain('overcovered');
    });
  });

  describe('View Mode Descriptions', () => {
    it('should show coverage view description', () => {
      render(<HeatmapLegend viewMode="coverage" />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/Shows rotation coverage percentage/)
      ).toBeInTheDocument();
    });

    it('should show workload view description', () => {
      render(<HeatmapLegend viewMode="workload" />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/Shows workload distribution/)
      ).toBeInTheDocument();
    });

    it('should show custom view description', () => {
      render(<HeatmapLegend viewMode="custom" />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/Custom visualization/)
      ).toBeInTheDocument();
    });

    it('should describe coverage color meanings', () => {
      render(<HeatmapLegend viewMode="coverage" />, { wrapper: createWrapper() });

      const description = screen.getByText(/Shows rotation coverage percentage/);
      expect(description).toHaveTextContent('Green = full coverage');
      expect(description).toHaveTextContent('yellow = partial');
      expect(description).toHaveTextContent('red = low coverage');
    });

    it('should describe workload color meanings', () => {
      render(<HeatmapLegend viewMode="workload" />, { wrapper: createWrapper() });

      const description = screen.getByText(/Shows workload distribution/);
      expect(description).toHaveTextContent('Blue = light');
      expect(description).toHaveTextContent('yellow = moderate');
      expect(description).toHaveTextContent('red = heavy');
    });
  });

  describe('Layout and Styling', () => {
    it('should render with proper container styling', () => {
      const { container } = render(<HeatmapLegend />, { wrapper: createWrapper() });

      const legendContainer = container.querySelector('.bg-white.border.border-gray-200');
      expect(legendContainer).toBeInTheDocument();
    });

    it('should render gradient bar with proper height', () => {
      const { container } = render(<HeatmapLegend />, { wrapper: createWrapper() });

      const gradientBar = container.querySelector('.h-6.rounded-md');
      expect(gradientBar).toBeInTheDocument();
    });

    it('should render color boxes with proper size', () => {
      const { container } = render(<HeatmapLegend />, { wrapper: createWrapper() });

      const colorBoxes = container.querySelectorAll('.w-4.h-4.rounded');
      expect(colorBoxes.length).toBeGreaterThan(0);
    });
  });
});

describe('CompactHeatmapLegend', () => {
  describe('Basic Rendering', () => {
    it('should render compact legend', () => {
      render(<CompactHeatmapLegend />, { wrapper: createWrapper() });

      expect(screen.getByText('Scale:')).toBeInTheDocument();
    });

    it('should render gradient bar', () => {
      const { container } = render(<CompactHeatmapLegend />, { wrapper: createWrapper() });

      const gradientBar = container.querySelector('.w-32.h-4.rounded');
      expect(gradientBar).toBeInTheDocument();
    });

    it('should display min and max values', () => {
      render(<CompactHeatmapLegend viewMode="coverage" />, { wrapper: createWrapper() });

      const scale = DEFAULT_COLOR_SCALES.coverage;
      expect(screen.getByText(String(scale.min))).toBeInTheDocument();
      expect(screen.getByText(String(scale.max))).toBeInTheDocument();
    });

    it('should display hyphen separator', () => {
      render(<CompactHeatmapLegend />, { wrapper: createWrapper() });

      expect(screen.getByText('-')).toBeInTheDocument();
    });
  });

  describe('View Mode Support', () => {
    it('should use coverage scale by default', () => {
      const { container } = render(<CompactHeatmapLegend />, { wrapper: createWrapper() });

      const gradientBar = container.querySelector('.w-32.h-4.rounded');
      const expectedGradient = `linear-gradient(to right, ${DEFAULT_COLOR_SCALES.coverage.colors.join(', ')})`;
      expect(gradientBar).toHaveStyle({ background: expectedGradient });
    });

    it('should use workload scale when specified', () => {
      const { container } = render(<CompactHeatmapLegend viewMode="workload" />, {
        wrapper: createWrapper(),
      });

      const gradientBar = container.querySelector('.w-32.h-4.rounded');
      const expectedGradient = `linear-gradient(to right, ${DEFAULT_COLOR_SCALES.workload.colors.join(', ')})`;
      expect(gradientBar).toHaveStyle({ background: expectedGradient });
    });

    it('should use custom scale when specified', () => {
      const { container } = render(<CompactHeatmapLegend viewMode="custom" />, {
        wrapper: createWrapper(),
      });

      const gradientBar = container.querySelector('.w-32.h-4.rounded');
      const expectedGradient = `linear-gradient(to right, ${DEFAULT_COLOR_SCALES.custom.colors.join(', ')})`;
      expect(gradientBar).toHaveStyle({ background: expectedGradient });
    });
  });

  describe('Layout and Styling', () => {
    it('should render with inline-flex layout', () => {
      const { container } = render(<CompactHeatmapLegend />, { wrapper: createWrapper() });

      const legendContainer = container.querySelector('.inline-flex.items-center');
      expect(legendContainer).toBeInTheDocument();
    });

    it('should have gray background', () => {
      const { container } = render(<CompactHeatmapLegend />, { wrapper: createWrapper() });

      const legendContainer = container.querySelector('.bg-gray-50');
      expect(legendContainer).toBeInTheDocument();
    });

    it('should have compact gradient bar', () => {
      const { container } = render(<CompactHeatmapLegend />, { wrapper: createWrapper() });

      const gradientBar = container.querySelector('.w-32.h-4.rounded');
      expect(gradientBar).toBeInTheDocument();
    });
  });
});
