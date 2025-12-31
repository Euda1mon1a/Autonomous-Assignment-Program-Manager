import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnalyticsDashboard } from '@/features/analytics/AnalyticsDashboard';
import { analyticsMockFactories, analyticsMockResponses } from './analytics-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

/**
 * Helper function to set up mock API responses based on URL
 * This ensures all endpoints return appropriate data types
 */
function setupDefaultMocks() {
  mockedApi.get.mockImplementation((url: string) => {
    if (url.includes('/analytics/metrics/current')) {
      return Promise.resolve(analyticsMockResponses.currentMetrics);
    }
    if (url.includes('/analytics/alerts')) {
      return Promise.resolve(analyticsMockResponses.alerts);
    }
    if (url.includes('/analytics/trends/fairness')) {
      return Promise.resolve(analyticsMockResponses.fairnessTrend);
    }
    if (url.includes('/analytics/equity/pgy')) {
      return Promise.resolve(analyticsMockResponses.pgyEquity);
    }
    if (url.includes('/analytics/versions')) {
      return Promise.resolve(analyticsMockResponses.versions);
    }
    return Promise.resolve([]);
  });
}

describe('AnalyticsDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    beforeEach(() => {
      setupDefaultMocks();
    });

    it('should render dashboard title', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
      });
    });

    it('should render dashboard description', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText('Monitor schedule fairness, coverage, and compliance metrics')
        ).toBeInTheDocument();
      });
    });

    it('should render refresh button', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });
    });

    it('should render export button', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Export')).toBeInTheDocument();
      });
    });
  });

  describe('View Navigation', () => {
    beforeEach(() => {
      setupDefaultMocks();
    });

    it('should render all view tabs', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Trends')).toBeInTheDocument();
        expect(screen.getByText('Compare Versions')).toBeInTheDocument();
        expect(screen.getByText('What-If Analysis')).toBeInTheDocument();
      });
    });

    it('should default to overview tab', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Use getByRole to get the actual button element, not the text span
        const overviewButton = screen.getByRole('tab', { name: /overview/i });
        expect(overviewButton).toHaveClass('bg-white');
        expect(overviewButton).toHaveClass('text-blue-600');
      });
    });

    it('should switch to trends view when clicked', async () => {
      const user = userEvent.setup();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /trends/i })).toBeInTheDocument();
      });

      // Use getByRole to get the actual button element
      const trendsButton = screen.getByRole('tab', { name: /trends/i });
      await user.click(trendsButton);

      await waitFor(() => {
        expect(trendsButton).toHaveClass('bg-white');
        expect(trendsButton).toHaveClass('text-blue-600');
      });
    });
  });

  describe('Quick Stats', () => {
    beforeEach(() => {
      setupDefaultMocks();
    });

    it('should display total metrics count', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Total Metrics')).toBeInTheDocument();
        expect(screen.getByText('7')).toBeInTheDocument();
      });
    });

    it('should display excellent metrics count', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Excellent')).toBeInTheDocument();
      });
    });

    it('should display warning metrics count', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Warnings')).toBeInTheDocument();
      });
    });

    it('should display critical metrics count', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Critical')).toBeInTheDocument();
      });
    });
  });

  describe('Metrics Display', () => {
    beforeEach(() => {
      setupDefaultMocks();
    });

    it('should render key metrics section', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Key Metrics')).toBeInTheDocument();
      });
    });

    it('should display all metric cards', async () => {
      const { container } = render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      // Wait for metrics to load by checking for a specific metric card
      await waitFor(() => {
        const metricCards = container.querySelectorAll('button[id^="metric-card-"]');
        expect(metricCards.length).toBe(7); // 7 metric cards
      }, { timeout: 3000 });

      // Verify the heading is present
      expect(screen.getByText('Key Metrics')).toBeInTheDocument();
    });

    it('should show loading skeletons while fetching metrics', async () => {
      // Override default mocks to never resolve metrics but resolve alerts
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]); // Return empty alerts to avoid filter error
        }
        return new Promise(() => {}); // Never resolves for other endpoints
      });

      const { container } = render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });

    it('should show error message when metrics fail to load', async () => {
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]);
        }
        return Promise.reject(new Error('API Error'));
      });

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load metrics')).toBeInTheDocument();
      });
    });
  });

  describe('Alerts Section', () => {
    beforeEach(() => {
      setupDefaultMocks();
    });

    it('should render metric alerts section', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Metric Alerts')).toBeInTheDocument();
      });
    });

    it('should display alert count', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/active alert/)).toBeInTheDocument();
      });
    });

    it('should show toggle for acknowledged alerts', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Show Acknowledged')).toBeInTheDocument();
      });
    });

    it('should toggle acknowledged alerts visibility', async () => {
      const user = userEvent.setup();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Show Acknowledged')).toBeInTheDocument();
      });

      const toggleButton = screen.getByText('Show Acknowledged');
      await user.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText('Hide Acknowledged')).toBeInTheDocument();
      });
    });

    it('should display empty state when no alerts', async () => {
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/analytics/metrics/current')) {
          return Promise.resolve(analyticsMockResponses.currentMetrics);
        }
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]); // Empty alerts
        }
        if (url.includes('/analytics/trends/fairness')) {
          return Promise.resolve(analyticsMockResponses.fairnessTrend);
        }
        if (url.includes('/analytics/equity/pgy')) {
          return Promise.resolve(analyticsMockResponses.pgyEquity);
        }
        return Promise.resolve([]);
      });

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('No alerts at this time')).toBeInTheDocument();
      });
    });
  });

  describe('Fairness Trends Preview', () => {
    beforeEach(() => {
      setupDefaultMocks();
      // Override alerts to be empty for this section
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/analytics/metrics/current')) {
          return Promise.resolve(analyticsMockResponses.currentMetrics);
        }
        if (url.includes('/analytics/trends/fairness')) {
          return Promise.resolve(analyticsMockResponses.fairnessTrend);
        }
        if (url.includes('/analytics/equity/pgy')) {
          return Promise.resolve(analyticsMockResponses.pgyEquity);
        }
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]);
        }
        return Promise.resolve([]);
      });
    });

    it('should render fairness trends section in overview', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Fairness Trends')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    beforeEach(() => {
      setupDefaultMocks();
      mockedApi.post.mockResolvedValue(analyticsMockResponses.currentMetrics);
    });

    it('should call refresh API when refresh button clicked', async () => {
      const user = userEvent.setup();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('Refresh');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mockedApi.post).toHaveBeenCalledWith('/analytics/metrics/refresh', {});
      });
    });

    it('should show loading state when refreshing', async () => {
      const user = userEvent.setup();
      mockedApi.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });

      // Get the button element (not just the text node)
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(refreshButton).toBeDisabled();
      });
    });
  });

  describe('Export Functionality', () => {
    beforeEach(() => {
      setupDefaultMocks();
      mockedApi.post.mockResolvedValue(new Blob(['test data']));
    });

    it('should call export API when export button clicked', async () => {
      const user = userEvent.setup();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Export')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export');
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockedApi.post).toHaveBeenCalledWith(
          '/analytics/export',
          expect.objectContaining({
            format: 'pdf',
            include_charts: true,
          }),
          expect.any(Object)
        );
      });
    });
  });

  describe('View Content Rendering', () => {
    beforeEach(() => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/analytics/metrics/current')) {
          return Promise.resolve(analyticsMockResponses.currentMetrics);
        }
        if (url.includes('/analytics/trends/fairness')) {
          return Promise.resolve(analyticsMockResponses.fairnessTrend);
        }
        if (url.includes('/analytics/equity/pgy')) {
          return Promise.resolve(analyticsMockResponses.pgyEquity);
        }
        if (url.includes('/analytics/versions')) {
          return Promise.resolve(analyticsMockResponses.versions);
        }
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]);
        }
        return Promise.resolve([]);
      });
    });

    it('should show overview content by default', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Key Metrics')).toBeInTheDocument();
        expect(screen.getByText('Metric Alerts')).toBeInTheDocument();
      });
    });

    it('should show trends content when trends tab selected', async () => {
      const user = userEvent.setup();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Trends')).toBeInTheDocument();
      });

      const trendsButton = screen.getByText('Trends');
      await user.click(trendsButton);

      await waitFor(() => {
        expect(screen.getByText('Detailed Trends')).toBeInTheDocument();
      });
    });

    it('should show comparison content when comparison tab selected', async () => {
      const user = userEvent.setup();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Compare Versions')).toBeInTheDocument();
      });

      const comparisonButton = screen.getByText('Compare Versions');
      await user.click(comparisonButton);

      await waitFor(() => {
        expect(screen.getByText('Compare Schedule Versions')).toBeInTheDocument();
      });
    });

    it('should show what-if content when what-if tab selected', async () => {
      const user = userEvent.setup();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('What-If Analysis')).toBeInTheDocument();
      });

      const whatIfButton = screen.getByText('What-If Analysis');
      await user.click(whatIfButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Predict the impact of proposed changes to your schedule/)
        ).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    it('should fetch current metrics on mount', async () => {
      setupDefaultMocks();

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith('/analytics/metrics/current');
      });
    });

    it('should fetch alerts on mount', async () => {
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/analytics/metrics/current')) {
          return Promise.resolve(analyticsMockResponses.currentMetrics);
        }
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]);
        }
        if (url.includes('/analytics/trends/fairness')) {
          return Promise.resolve(analyticsMockResponses.fairnessTrend);
        }
        if (url.includes('/analytics/equity/pgy')) {
          return Promise.resolve(analyticsMockResponses.pgyEquity);
        }
        return Promise.resolve([]);
      });

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/alerts')
        );
      });
    });
  });

  describe('Custom ClassName', () => {
    beforeEach(() => {
      setupDefaultMocks();
    });

    it('should apply custom className', async () => {
      const { container } = render(<AnalyticsDashboard className="custom-dashboard" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const element = container.querySelector('.custom-dashboard');
        expect(element).toBeInTheDocument();
      });
    });
  });
});
