/**
 * Tests for Resilience Hub Visualization
 *
 * Tests the graph visualization component for the resilience hub which displays:
 * - Network graph of faculty dependencies
 * - Vulnerability connections between nodes
 * - Interactive node selection and highlighting
 * - D3/Canvas rendering with graceful failure handling
 *
 * NOTE: These tests are skipped because the HubVisualization component
 * is currently a stub and requires complex D3/Canvas implementation.
 * When the full component is implemented, these tests should be unskipped
 * and may need adjustments based on the final implementation.
 */

import { render, screen, waitFor, fireEvent } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { HubVisualization as HubVisualizationBase } from '@/features/resilience/HubVisualization';

// Cast to any to allow test props that component will accept when fully implemented
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const HubVisualization = HubVisualizationBase as React.FC<any>;
import { resilienceMockFactories, resilienceMockResponses } from './resilience-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

// ============================================================================
// D3/Canvas Mock Setup
// ============================================================================

// Mock canvas context for graph rendering
const mockCanvasContext = {
  canvas: { width: 800, height: 600 },
  clearRect: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  stroke: jest.fn(),
  fill: jest.fn(),
  arc: jest.fn(),
  fillText: jest.fn(),
  measureText: jest.fn(() => ({ width: 50 })),
  save: jest.fn(),
  restore: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  setTransform: jest.fn(),
  getTransform: jest.fn(() => ({ a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 })),
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 1,
  font: '',
  textAlign: 'left',
  textBaseline: 'top',
  globalAlpha: 1,
  globalCompositeOperation: 'source-over',
};

// Mock getContext for canvas elements
const originalGetContext = HTMLCanvasElement.prototype.getContext;

// Track canvas rendering state for tests
let canvasRenderingEnabled = true;
let canvasCreationCount = 0;

beforeAll(() => {
  // Override getContext to return mock context
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (HTMLCanvasElement.prototype as any).getContext = jest.fn(function (
    this: HTMLCanvasElement,
    contextId: string
  ) {
    if (contextId === '2d') {
      canvasCreationCount++;
      if (!canvasRenderingEnabled) {
        return null; // Simulate canvas failure
      }
      return mockCanvasContext as unknown as CanvasRenderingContext2D;
    }
    return originalGetContext.call(this, contextId);
  });
});

afterAll(() => {
  HTMLCanvasElement.prototype.getContext = originalGetContext;
});

beforeEach(() => {
  jest.clearAllMocks();
  canvasRenderingEnabled = true;
  canvasCreationCount = 0;

  // Reset canvas context mock functions
  Object.keys(mockCanvasContext).forEach((key) => {
    if (typeof mockCanvasContext[key as keyof typeof mockCanvasContext] === 'function') {
      (mockCanvasContext[key as keyof typeof mockCanvasContext] as jest.Mock).mockClear?.();
    }
  });
});

// ============================================================================
// Mock Data Factories for Graph Visualization
// ============================================================================

const graphMockFactories = {
  node: (overrides = {}) => ({
    id: 'node-1',
    label: 'Dr. Smith',
    type: 'faculty' as const,
    x: 100,
    y: 100,
    radius: 20,
    color: '#4CAF50',
    criticality: 0.85,
    services: ['Inpatient', 'Procedures'],
    ...overrides,
  }),

  edge: (overrides = {}) => ({
    id: 'edge-1',
    source: 'node-1',
    target: 'node-2',
    weight: 0.75,
    type: 'dependency' as const,
    color: '#999999',
    ...overrides,
  }),

  graphData: (overrides = {}) => ({
    nodes: [
      graphMockFactories.node({ id: 'faculty-1', label: 'Dr. Smith', criticality: 0.85 }),
      graphMockFactories.node({ id: 'faculty-2', label: 'Dr. Johnson', criticality: 0.72, x: 200, y: 150 }),
      graphMockFactories.node({ id: 'faculty-3', label: 'Dr. Williams', criticality: 0.45, x: 150, y: 250 }),
    ],
    edges: [
      graphMockFactories.edge({ id: 'edge-1', source: 'faculty-1', target: 'faculty-2', weight: 0.8 }),
      graphMockFactories.edge({ id: 'edge-2', source: 'faculty-1', target: 'faculty-3', weight: 0.5 }),
      graphMockFactories.edge({ id: 'edge-3', source: 'faculty-2', target: 'faculty-3', weight: 0.3 }),
    ],
    metadata: {
      totalNodes: 3,
      totalEdges: 3,
      avgCriticality: 0.67,
      clusterCount: 1,
    },
    ...overrides,
  }),

  emptyGraph: () => ({
    nodes: [],
    edges: [],
    metadata: {
      totalNodes: 0,
      totalEdges: 0,
      avgCriticality: 0,
      clusterCount: 0,
    },
  }),

  largeGraph: () => {
    const nodes = Array.from({ length: 50 }, (_, i) =>
      graphMockFactories.node({
        id: `faculty-${i}`,
        label: `Dr. Faculty ${i}`,
        criticality: Math.random(),
        x: Math.random() * 800,
        y: Math.random() * 600,
      })
    );
    const edges = Array.from({ length: 100 }, (_, i) =>
      graphMockFactories.edge({
        id: `edge-${i}`,
        source: `faculty-${Math.floor(Math.random() * 50)}`,
        target: `faculty-${Math.floor(Math.random() * 50)}`,
        weight: Math.random(),
      })
    );
    return {
      nodes,
      edges,
      metadata: {
        totalNodes: 50,
        totalEdges: 100,
        avgCriticality: 0.5,
        clusterCount: 5,
      },
    };
  },
};

const graphMockResponses = {
  standard: graphMockFactories.graphData(),
  empty: graphMockFactories.emptyGraph(),
  large: graphMockFactories.largeGraph(),
};

// ============================================================================
// Test Suites - All skipped as component is a stub
// ============================================================================

// Skip all tests - component is a stub placeholder requiring D3/Canvas implementation
// TODO: Unskip when HubVisualization is fully implemented with D3
describe.skip('HubVisualization', () => {
  describe('Initial Rendering', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);
    });

    it('should render visualization container', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('hub-visualization')).toBeInTheDocument();
      });
    });

    it('should render visualization title', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Dependency Network')).toBeInTheDocument();
      });
    });

    it('should render visualization description', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/Visualize faculty dependencies and vulnerability connections/)
        ).toBeInTheDocument();
      });
    });

    it('should fetch graph data on mount', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/resilience/graph')
        );
      });
    });

    it('should render canvas element for graph', async () => {
      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });
    });

    it('should render control buttons', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /zoom in/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /zoom out/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /reset view/i })).toBeInTheDocument();
      });
    });

    it('should render legend section', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Legend')).toBeInTheDocument();
        expect(screen.getByText(/critical/i)).toBeInTheDocument();
        expect(screen.getByText(/high/i)).toBeInTheDocument();
        expect(screen.getByText(/normal/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading skeleton while fetching graph data', async () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });

    it('should display loading text while graph initializes', async () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
      });
    });

    it('should show progress indicator for large graphs', async () => {
      mockedApi.get.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve(graphMockResponses.large), 100);
          })
      );

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error State', () => {
    it('should show error message when graph data fails to load', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network error'));

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/failed to load.*graph/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      mockedApi.get.mockRejectedValue(new Error('API Error'));

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('should retry fetching data when retry button clicked', async () => {
      const user = userEvent.setup();
      mockedApi.get.mockRejectedValueOnce(new Error('Network error'));
      mockedApi.get.mockResolvedValueOnce(graphMockResponses.standard);

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledTimes(2);
      });
    });

    it('should display specific error message for timeout', async () => {
      mockedApi.get.mockRejectedValue(new Error('Request timeout'));

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });
  });

  describe('D3/Canvas Rendering Failure Modes', () => {
    it('should gracefully handle canvas context unavailable', async () => {
      canvasRenderingEnabled = false;
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/canvas.*not supported/i)).toBeInTheDocument();
      });
    });

    it('should show fallback visualization when canvas fails', async () => {
      canvasRenderingEnabled = false;
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Should show a table-based fallback
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    it('should display node data in fallback table view', async () => {
      canvasRenderingEnabled = false;
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
        expect(screen.getByText('Dr. Johnson')).toBeInTheDocument();
      });
    });

    it('should handle WebGL context loss gracefully', async () => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);

      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      // Simulate WebGL context loss
      const canvas = container.querySelector('canvas');
      if (canvas) {
        const event = new Event('webglcontextlost');
        fireEvent(canvas, event);
      }

      await waitFor(() => {
        // Should show recovery message or fallback
        expect(
          screen.getByText(/rendering.*issue|fallback|table/i)
        ).toBeInTheDocument();
      });
    });

    it('should recover from temporary rendering failure', async () => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);

      // First render fails, then succeeds
      canvasRenderingEnabled = false;

      const { rerender } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/canvas.*not supported/i)).toBeInTheDocument();
      });

      // Re-enable canvas and rerender
      canvasRenderingEnabled = true;

      rerender(<HubVisualization />);

      await waitFor(() => {
        expect(screen.queryByText(/canvas.*not supported/i)).not.toBeInTheDocument();
      });
    });

    it('should show warning for degraded rendering quality', async () => {
      mockedApi.get.mockResolvedValue(graphMockResponses.large);

      render(<HubVisualization performanceMode="low" />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/simplified.*view|performance mode/i)).toBeInTheDocument();
      });
    });

    it('should handle out-of-memory errors gracefully', async () => {
      mockedApi.get.mockResolvedValue(graphMockResponses.large);

      // Simulate memory pressure by making canvas allocation fail after first few attempts
      let allocCount = 0;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (HTMLCanvasElement.prototype as any).getContext = jest.fn(function (contextId: string) {
        if (contextId === '2d') {
          allocCount++;
          if (allocCount > 2) {
            throw new Error('Failed to create canvas context: out of memory');
          }
          return mockCanvasContext as unknown as CanvasRenderingContext2D;
        }
        return null;
      });

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Should gracefully degrade
        expect(
          screen.getByText(/memory|simplified|fallback/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Graph Data Display', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);
    });

    it('should display node count in stats panel', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument(); // 3 nodes
        expect(screen.getByText(/nodes/i)).toBeInTheDocument();
      });
    });

    it('should display edge count in stats panel', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/connections|edges/i)).toBeInTheDocument();
      });
    });

    it('should display average criticality metric', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/avg.*criticality|0\.67/i)).toBeInTheDocument();
      });
    });

    it('should render empty state for no nodes', async () => {
      mockedApi.get.mockResolvedValue(graphMockResponses.empty);

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/no.*data|empty.*graph/i)).toBeInTheDocument();
      });
    });

    it('should highlight critical nodes visually', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Verify canvas drawing was called for critical node
        expect(mockCanvasContext.arc).toHaveBeenCalled();
        expect(mockCanvasContext.fill).toHaveBeenCalled();
      });
    });
  });

  describe('User Interactions', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);
    });

    it('should zoom in when zoom in button clicked', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /zoom in/i })).toBeInTheDocument();
      });

      const zoomInButton = screen.getByRole('button', { name: /zoom in/i });
      await user.click(zoomInButton);

      // Verify scale transform was applied
      await waitFor(() => {
        expect(mockCanvasContext.scale).toHaveBeenCalled();
      });
    });

    it('should zoom out when zoom out button clicked', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /zoom out/i })).toBeInTheDocument();
      });

      const zoomOutButton = screen.getByRole('button', { name: /zoom out/i });
      await user.click(zoomOutButton);

      await waitFor(() => {
        expect(mockCanvasContext.scale).toHaveBeenCalled();
      });
    });

    it('should reset view when reset button clicked', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reset view/i })).toBeInTheDocument();
      });

      const resetButton = screen.getByRole('button', { name: /reset view/i });
      await user.click(resetButton);

      await waitFor(() => {
        expect(mockCanvasContext.setTransform).toHaveBeenCalled();
      });
    });

    it('should show node details on hover', async () => {
      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;

      // Simulate mouse move over a node position
      fireEvent.mouseMove(canvas, { clientX: 100, clientY: 100 });

      await waitFor(() => {
        expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
      });
    });

    it('should select node on click', async () => {
      const onNodeSelect = jest.fn();

      const { container } = render(
        <HubVisualization onNodeSelect={onNodeSelect} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;

      // Simulate click on node position
      fireEvent.click(canvas, { clientX: 100, clientY: 100 });

      await waitFor(() => {
        expect(onNodeSelect).toHaveBeenCalled();
      });
    });

    it('should support drag to pan', async () => {
      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;

      // Simulate drag
      fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
      fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
      fireEvent.mouseUp(canvas, { clientX: 150, clientY: 150 });

      await waitFor(() => {
        expect(mockCanvasContext.translate).toHaveBeenCalled();
      });
    });

    it('should support mouse wheel zoom', async () => {
      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;

      // Simulate wheel zoom
      fireEvent.wheel(canvas, { deltaY: -100 });

      await waitFor(() => {
        expect(mockCanvasContext.scale).toHaveBeenCalled();
      });
    });

    it('should toggle fullscreen mode', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /fullscreen/i })).toBeInTheDocument();
      });

      const fullscreenButton = screen.getByRole('button', { name: /fullscreen/i });
      await user.click(fullscreenButton);

      await waitFor(() => {
        expect(screen.getByTestId('hub-visualization')).toHaveClass('fullscreen');
      });
    });
  });

  describe('Filter and View Options', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);
    });

    it('should filter nodes by criticality level', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Filter by Criticality')).toBeInTheDocument();
      });

      const criticalFilter = screen.getByLabelText(/critical only/i);
      await user.click(criticalFilter);

      await waitFor(() => {
        // Should show only critical nodes (1 node)
        expect(mockCanvasContext.arc).toHaveBeenCalledTimes(1);
      });
    });

    it('should toggle edge visibility', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/show edges/i)).toBeInTheDocument();
      });

      const edgeToggle = screen.getByLabelText(/show edges/i);
      await user.click(edgeToggle);

      await waitFor(() => {
        // Edges should no longer be drawn
        expect(mockCanvasContext.lineTo).not.toHaveBeenCalled();
      });
    });

    it('should toggle node labels', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/show labels/i)).toBeInTheDocument();
      });

      const labelToggle = screen.getByLabelText(/show labels/i);
      await user.click(labelToggle);

      await waitFor(() => {
        // Labels should no longer be drawn
        expect(mockCanvasContext.fillText).not.toHaveBeenCalled();
      });
    });

    it('should switch between layout algorithms', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Layout')).toBeInTheDocument();
      });

      const layoutSelect = screen.getByRole('combobox', { name: /layout/i });
      await user.selectOptions(layoutSelect, 'circular');

      await waitFor(() => {
        // Canvas should be redrawn with new layout
        expect(mockCanvasContext.clearRect).toHaveBeenCalled();
      });
    });
  });

  describe('Performance Optimization', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(graphMockResponses.large);
    });

    it('should throttle redraw on rapid interactions', async () => {
      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;
      const initialClearCount = mockCanvasContext.clearRect.mock.calls.length;

      // Rapid wheel events
      for (let i = 0; i < 10; i++) {
        fireEvent.wheel(canvas, { deltaY: -10 });
      }

      await waitFor(() => {
        // Should not have redrawn 10 times due to throttling
        const finalClearCount = mockCanvasContext.clearRect.mock.calls.length;
        expect(finalClearCount - initialClearCount).toBeLessThan(10);
      });
    });

    it('should use requestAnimationFrame for smooth rendering', async () => {
      const rafSpy = jest.spyOn(window, 'requestAnimationFrame');

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(rafSpy).toHaveBeenCalled();
      });

      rafSpy.mockRestore();
    });

    it('should reduce detail level at low zoom', async () => {
      const user = userEvent.setup();

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /zoom out/i })).toBeInTheDocument();
      });

      // Zoom out multiple times
      const zoomOutButton = screen.getByRole('button', { name: /zoom out/i });
      for (let i = 0; i < 5; i++) {
        await user.click(zoomOutButton);
      }

      await waitFor(() => {
        // Labels should not be drawn at low zoom
        expect(mockCanvasContext.fillText).not.toHaveBeenCalled();
      });
    });

    it('should skip offscreen nodes', async () => {
      mockedApi.get.mockResolvedValue({
        ...graphMockResponses.large,
        nodes: graphMockResponses.large.nodes.map((n, i) => ({
          ...n,
          x: i < 25 ? n.x : 10000, // Half offscreen
          y: i < 25 ? n.y : 10000,
        })),
      });

      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Only visible nodes should be drawn
        expect(mockCanvasContext.arc.mock.calls.length).toBeLessThan(50);
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);
    });

    it('should have proper ARIA labels for the visualization', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('img', { name: /dependency network/i })).toBeInTheDocument();
      });
    });

    it('should provide screen reader description of graph contents', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/3 faculty nodes.*3 connections/i)
        ).toBeInTheDocument();
      });
    });

    it('should have keyboard-navigable controls', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
          expect(button).toHaveAttribute('type');
        });
      });
    });

    it('should support keyboard navigation between nodes', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const visualization = screen.getByTestId('hub-visualization');
        expect(visualization).toBeInTheDocument();
      });

      const visualization = screen.getByTestId('hub-visualization');

      // Tab to focus the visualization
      fireEvent.keyDown(visualization, { key: 'Tab' });

      // Arrow key to navigate nodes
      fireEvent.keyDown(visualization, { key: 'ArrowRight' });

      await waitFor(() => {
        expect(screen.getByText(/selected.*Dr\./i)).toBeInTheDocument();
      });
    });

    it('should announce node selection to screen readers', async () => {
      const { container } = render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;
      fireEvent.click(canvas, { clientX: 100, clientY: 100 });

      await waitFor(() => {
        const liveRegion = screen.getByRole('status');
        expect(liveRegion).toHaveTextContent(/Dr\. Smith/);
      });
    });

    it('should have sufficient color contrast for node colors', async () => {
      render(<HubVisualization />, { wrapper: createWrapper() });

      await waitFor(() => {
        const legend = screen.getByText('Legend').parentElement;
        expect(legend).toBeInTheDocument();

        // Check that legend items have visible text
        const legendItems = legend?.querySelectorAll('[class*="text"]');
        expect(legendItems?.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Custom Props', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);
    });

    it('should apply custom className', async () => {
      const { container } = render(
        <HubVisualization className="custom-viz-class" />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const element = container.querySelector('.custom-viz-class');
        expect(element).toBeInTheDocument();
      });
    });

    it('should respect custom dimensions', async () => {
      const { container } = render(
        <HubVisualization width={1000} height={800} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toHaveAttribute('width', '1000');
        expect(canvas).toHaveAttribute('height', '800');
      });
    });

    it('should call onNodeSelect callback with node data', async () => {
      const onNodeSelect = jest.fn();

      const { container } = render(
        <HubVisualization onNodeSelect={onNodeSelect} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;
      fireEvent.click(canvas, { clientX: 100, clientY: 100 });

      await waitFor(() => {
        expect(onNodeSelect).toHaveBeenCalledWith(
          expect.objectContaining({
            id: expect.any(String),
            label: expect.any(String),
          })
        );
      });
    });

    it('should call onEdgeSelect callback with edge data', async () => {
      const onEdgeSelect = jest.fn();

      const { container } = render(
        <HubVisualization onEdgeSelect={onEdgeSelect} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas')!;
      // Click on edge position (between nodes)
      fireEvent.click(canvas, { clientX: 150, clientY: 125 });

      await waitFor(() => {
        expect(onEdgeSelect).toHaveBeenCalled();
      });
    });

    it('should accept initial zoom level', async () => {
      render(<HubVisualization initialZoom={1.5} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockCanvasContext.scale).toHaveBeenCalledWith(1.5, 1.5);
      });
    });
  });

  describe('Integration with Resilience Data', () => {
    it('should integrate with contingency analysis data', async () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/resilience/graph')) {
          return Promise.resolve(graphMockResponses.standard);
        }
        if (url.includes('/resilience/vulnerability')) {
          return Promise.resolve(resilienceMockResponses.contingencyAnalysis);
        }
        return Promise.resolve({});
      });

      render(<HubVisualization showContingencyOverlay />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/resilience/vulnerability')
        );
      });
    });

    it('should highlight N-1 vulnerable nodes', async () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/resilience/graph')) {
          return Promise.resolve(graphMockResponses.standard);
        }
        if (url.includes('/resilience/vulnerability')) {
          return Promise.resolve({
            ...resilienceMockResponses.contingencyAnalysis,
            n1_vulnerabilities: [{ facultyId: 'faculty-1', affected_blocks: 5, severity: 'high' }],
          });
        }
        return Promise.resolve({});
      });

      render(<HubVisualization showContingencyOverlay />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Should show vulnerability indicator
        expect(screen.getByText(/vulnerable/i)).toBeInTheDocument();
      });
    });

    it('should show N-2 fatal pair connections', async () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/resilience/graph')) {
          return Promise.resolve(graphMockResponses.standard);
        }
        if (url.includes('/resilience/vulnerability')) {
          return Promise.resolve({
            ...resilienceMockResponses.contingencyAnalysis,
            n2_fatal_pairs: [{ faculty1_id: 'faculty-1', faculty2_id: 'faculty-2' }],
          });
        }
        return Promise.resolve({});
      });

      render(<HubVisualization showContingencyOverlay />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Should highlight fatal pair edges
        expect(screen.getByText(/fatal pair/i)).toBeInTheDocument();
      });
    });

    it('should sync selected node with parent component', async () => {
      const onNodeSelect = jest.fn();
      mockedApi.get.mockResolvedValue(graphMockResponses.standard);

      const { rerender, container } = render(
        <HubVisualization onNodeSelect={onNodeSelect} selectedNodeId={undefined} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });

      // Update selected node from parent
      rerender(<HubVisualization onNodeSelect={onNodeSelect} selectedNodeId="faculty-2" />);

      await waitFor(() => {
        // Should highlight the selected node
        expect(screen.getByText('Dr. Johnson')).toBeInTheDocument();
      });
    });
  });
});
