/**
 * Tests for HeatmapView component
 * Tests rendering, loading states, error states, and user interactions
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HeatmapView, HeatmapViewSkeleton } from '@/features/heatmap/HeatmapView';
import { heatmapMockFactories } from './heatmap-mocks';
import { createWrapper } from '../../utils/test-utils';

// Store the onClick handler for later invocation in tests
let capturedOnClick: ((event: any) => void) | null = null;

// Mock react-plotly.js to avoid SSR issues and simplify testing
jest.mock('react-plotly.js', () => ({
  __esModule: true,
  default: jest.fn(({ data, layout, config, onClick, style }: any) => {
    const React = require('react');
    capturedOnClick = onClick;
    return React.createElement('div', {
      'data-testid': 'plotly-plot',
      'data-plot-data': JSON.stringify(data),
      'data-plot-layout': JSON.stringify(layout),
      'data-plot-config': JSON.stringify(config),
      style,
    }, 'Plotly Mock');
  }),
}));

// Mock dynamic import for next/dynamic - returns the mocked Plot component
jest.mock('next/dynamic', () => ({
  __esModule: true,
  default: () => {
    const React = require('react');
    return jest.fn(({ data, layout, config, onClick, style }: any) => {
      capturedOnClick = onClick;
      return React.createElement('div', {
        'data-testid': 'plotly-plot',
        'data-plot-data': JSON.stringify(data),
        'data-plot-layout': JSON.stringify(layout),
        'data-plot-config': JSON.stringify(config),
        style,
      }, 'Plotly Mock');
    });
  },
}));

// Helper to get the captured onClick handler
export function getCapturedOnClick() {
  return capturedOnClick;
}

// Reset captured handler before each test
beforeEach(() => {
  capturedOnClick = null;
});

describe('HeatmapView', () => {
  const mockData = heatmapMockFactories.heatmapData();

  describe('Rendering', () => {
    it('should render heatmap with data', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      expect(screen.getByTestId('plotly-plot')).toBeInTheDocument();
    });

    it('should render with custom height', () => {
      const { container } = render(<HeatmapView data={mockData} height={800} />, {
        wrapper: createWrapper(),
      });

      const plotlyElement = screen.getByTestId('plotly-plot');
      expect(plotlyElement).toHaveStyle({ height: '800px' });
    });

    it('should render with custom width', () => {
      const { container } = render(<HeatmapView data={mockData} width="50%" />, {
        wrapper: createWrapper(),
      });

      const plotlyElement = screen.getByTestId('plotly-plot');
      expect(plotlyElement).toHaveStyle({ width: '50%' });
    });

    it('should apply default dimensions', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const plotlyElement = screen.getByTestId('plotly-plot');
      expect(plotlyElement).toHaveStyle({ height: '600px', width: '100%' });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when isLoading is true', () => {
      render(<HeatmapView data={mockData} isLoading={true} />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading heatmap...')).toBeInTheDocument();
      expect(screen.queryByTestId('plotly-plot')).not.toBeInTheDocument();
    });

    it('should show Loader2 icon when loading', () => {
      const { container } = render(<HeatmapView data={mockData} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const loadingIcon = container.querySelector('.animate-spin');
      expect(loadingIcon).toBeInTheDocument();
    });

    it('should have correct loading container height', () => {
      const { container } = render(<HeatmapView data={mockData} isLoading={true} height={700} />, {
        wrapper: createWrapper(),
      });

      const loadingContainer = container.querySelector('.flex.items-center.justify-center');
      expect(loadingContainer).toHaveStyle({ height: '700px' });
    });
  });

  describe('Error State', () => {
    it('should show error message when error is provided', () => {
      const error = new Error('Failed to load heatmap data');
      render(<HeatmapView data={mockData} error={error} />, { wrapper: createWrapper() });

      expect(screen.getByText('Failed to load heatmap')).toBeInTheDocument();
      expect(screen.getByText('Failed to load heatmap data')).toBeInTheDocument();
    });

    it('should show AlertCircle icon on error', () => {
      const error = new Error('API Error');
      const { container } = render(<HeatmapView data={mockData} error={error} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Failed to load heatmap')).toBeInTheDocument();
      expect(container.querySelector('.text-red-600')).toBeInTheDocument();
    });

    it('should not render plot when error is present', () => {
      const error = new Error('API Error');
      render(<HeatmapView data={mockData} error={error} />, { wrapper: createWrapper() });

      expect(screen.queryByTestId('plotly-plot')).not.toBeInTheDocument();
    });

    it('should have correct error container height', () => {
      const error = new Error('API Error');
      const { container } = render(<HeatmapView data={mockData} error={error} height={700} />, {
        wrapper: createWrapper(),
      });

      const errorContainer = container.querySelector('.flex.items-center.justify-center');
      expect(errorContainer).toHaveStyle({ height: '700px' });
    });
  });

  describe('Empty Data State', () => {
    it('should show empty state when z_values is empty', () => {
      const emptyData = heatmapMockFactories.heatmapData({
        x_labels: [],
        y_labels: [],
        z_values: [],
      });

      render(<HeatmapView data={emptyData} />, { wrapper: createWrapper() });

      expect(screen.getByText('No data available')).toBeInTheDocument();
      expect(screen.getByText('Adjust your filters or date range to view data')).toBeInTheDocument();
    });

    it('should show empty state when data is null', () => {
      render(<HeatmapView data={null as any} />, { wrapper: createWrapper() });

      expect(screen.getByText('No data available')).toBeInTheDocument();
    });

    it('should show empty state when z_values is undefined', () => {
      const invalidData = heatmapMockFactories.heatmapData();
      delete (invalidData as any).z_values;

      render(<HeatmapView data={invalidData} />, { wrapper: createWrapper() });

      expect(screen.getByText('No data available')).toBeInTheDocument();
    });
  });

  describe('Plotly Data Configuration', () => {
    it('should pass correct data to Plotly', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      expect(plotData).toHaveLength(1);
      expect(plotData[0].type).toBe('heatmap');
      expect(plotData[0].x).toEqual(mockData.x_labels);
      expect(plotData[0].y).toEqual(mockData.y_labels);
      expect(plotData[0].z).toEqual(mockData.z_values);
    });

    it('should use custom color scale when provided', () => {
      const customColorScale = {
        min: 0,
        max: 50,
        colors: ['#000000', '#ffffff'],
        labels: ['Min', 'Max'],
      };

      const dataWithCustomScale = heatmapMockFactories.heatmapData({
        color_scale: customColorScale,
      });

      render(<HeatmapView data={dataWithCustomScale} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      expect(plotData[0].colorscale).toBeDefined();
      expect(plotData[0].colorbar.tickvals).toEqual([0, 50]);
    });

    it('should use default color scale when not provided', () => {
      const dataWithoutScale = heatmapMockFactories.heatmapData();
      delete dataWithoutScale.color_scale;

      render(<HeatmapView data={dataWithoutScale} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      expect(plotData[0].colorscale).toBeDefined();
      expect(plotData[0].colorscale).toHaveLength(3); // Default has 3 colors
    });
  });

  describe('Plotly Layout Configuration', () => {
    it('should include title in layout', () => {
      const dataWithTitle = heatmapMockFactories.heatmapData({
        title: 'Test Heatmap Title',
      });

      render(<HeatmapView data={dataWithTitle} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotLayout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(plotLayout.title.text).toBe('Test Heatmap Title');
    });

    it('should include axis labels in layout', () => {
      const dataWithLabels = heatmapMockFactories.heatmapData({
        x_axis_label: 'X Axis Label',
        y_axis_label: 'Y Axis Label',
      });

      render(<HeatmapView data={dataWithLabels} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotLayout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(plotLayout.xaxis.title.text).toBe('X Axis Label');
      expect(plotLayout.yaxis.title.text).toBe('Y Axis Label');
    });

    it('should include annotations when provided', () => {
      const annotation = heatmapMockFactories.annotation({
        x: 1,
        y: 1,
        text: 'Test Annotation',
      });

      const dataWithAnnotations = heatmapMockFactories.heatmapData({
        annotations: [annotation],
      });

      render(<HeatmapView data={dataWithAnnotations} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotLayout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(plotLayout.annotations).toHaveLength(1);
      expect(plotLayout.annotations[0].text).toBe('Test Annotation');
    });

    it('should have responsive layout', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotLayout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(plotLayout.autosize).toBe(true);
    });
  });

  describe('Plotly Config', () => {
    it('should enable responsive mode', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotConfig = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      expect(plotConfig.responsive).toBe(true);
    });

    it('should hide Plotly logo', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotConfig = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      expect(plotConfig.displaylogo).toBe(false);
    });

    it('should configure image export options', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotConfig = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      expect(plotConfig.toImageButtonOptions).toBeDefined();
      expect(plotConfig.toImageButtonOptions.format).toBe('png');
      expect(plotConfig.toImageButtonOptions.filename).toBe('heatmap');
    });

    it('should remove unnecessary mode bar buttons', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const plotElement = screen.getByTestId('plotly-plot');
      const plotConfig = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      expect(plotConfig.modeBarButtonsToRemove).toContain('pan2d');
      expect(plotConfig.modeBarButtonsToRemove).toContain('select2d');
      expect(plotConfig.modeBarButtonsToRemove).toContain('lasso2d');
    });
  });

  describe('Click Handler', () => {
    it('should call onCellClick with correct data when cell is clicked', () => {
      const onCellClick = jest.fn();
      render(<HeatmapView data={mockData} onCellClick={onCellClick} />, {
        wrapper: createWrapper(),
      });

      // Simulate click event with Plotly event structure
      const mockEvent = {
        points: [
          {
            x: '2024-01-01',
            y: 'Clinic',
            z: 100,
            pointIndex: [0, 0],
          },
        ],
      };

      // Use the captured onClick handler directly
      if (capturedOnClick) {
        capturedOnClick(mockEvent);
      }

      expect(onCellClick).toHaveBeenCalledWith({
        x: '2024-01-01',
        y: 'Clinic',
        value: 100,
        pointIndex: [0, 0],
      });
    });

    it('should not call onCellClick when not provided', () => {
      render(<HeatmapView data={mockData} />, { wrapper: createWrapper() });

      const mockEvent = {
        points: [
          {
            x: '2024-01-01',
            y: 'Clinic',
            z: 100,
            pointIndex: [0, 0],
          },
        ],
      };

      // Should not throw error when capturedOnClick is called without onCellClick
      expect(() => {
        if (capturedOnClick) {
          capturedOnClick(mockEvent);
        }
      }).not.toThrow();
    });

    it('should not call onCellClick when event has no points', () => {
      const onCellClick = jest.fn();
      render(<HeatmapView data={mockData} onCellClick={onCellClick} />, {
        wrapper: createWrapper(),
      });

      const mockEvent = {
        points: [],
      };

      if (capturedOnClick) {
        capturedOnClick(mockEvent);
      }

      expect(onCellClick).not.toHaveBeenCalled();
    });
  });

  describe('Priority: Loading > Error > Empty > Data', () => {
    it('should show loading state when both loading and error are true', () => {
      const error = new Error('API Error');
      render(<HeatmapView data={mockData} isLoading={true} error={error} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Loading heatmap...')).toBeInTheDocument();
      expect(screen.queryByText('Failed to load heatmap')).not.toBeInTheDocument();
    });

    it('should show error state when both error and empty data', () => {
      const error = new Error('API Error');
      const emptyData = heatmapMockFactories.heatmapData({
        z_values: [],
      });

      render(<HeatmapView data={emptyData} error={error} />, { wrapper: createWrapper() });

      expect(screen.getByText('Failed to load heatmap')).toBeInTheDocument();
      expect(screen.queryByText('No data available')).not.toBeInTheDocument();
    });
  });
});

describe('HeatmapViewSkeleton', () => {
  it('should render skeleton with default height', () => {
    const { container } = render(<HeatmapViewSkeleton />);

    const skeletonContainer = container.querySelector('.animate-pulse');
    expect(skeletonContainer).toBeInTheDocument();
    expect(skeletonContainer).toHaveStyle({ height: '600px' });
  });

  it('should render skeleton with custom height', () => {
    const { container } = render(<HeatmapViewSkeleton height={800} />);

    const skeletonContainer = container.querySelector('.animate-pulse');
    expect(skeletonContainer).toHaveStyle({ height: '800px' });
  });

  it('should render skeleton boxes', () => {
    const { container } = render(<HeatmapViewSkeleton />);

    const skeletonBoxes = container.querySelectorAll('.bg-gray-200');
    expect(skeletonBoxes.length).toBeGreaterThan(0);
  });

  it('should render 50 skeleton cells', () => {
    const { container } = render(<HeatmapViewSkeleton />);

    const cells = container.querySelectorAll('.h-12.bg-gray-200.rounded');
    expect(cells).toHaveLength(50);
  });
});
