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

describe('AnalyticsDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
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
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
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
      const { container } = render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const overviewButton = screen.getByText('Overview');
        expect(overviewButton).toHaveClass('bg-white');
        expect(overviewButton).toHaveClass('text-blue-600');
      });
    });

    it('should switch to trends view when clicked', async () => {
      const user = userEvent.setup();
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.currentMetrics);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Trends')).toBeInTheDocument();
      });

      const trendsButton = screen.getByText('Trends');
      await user.click(trendsButton);

      await waitFor(() => {
        expect(trendsButton).toHaveClass('bg-white');
        expect(trendsButton).toHaveClass('text-blue-600');
      });
    });
  });

  describe('Quick Stats', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
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
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
    });

    it('should render key metrics section', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Key Metrics')).toBeInTheDocument();
      });
    });

    it('should display all metric cards', async () => {
      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Fairness Score')).toBeInTheDocument();
        expect(screen.getByText('Gini Coefficient')).toBeInTheDocument();
        expect(screen.getByText('Workload Variance')).toBeInTheDocument();
        expect(screen.getByText('PGY Equity Score')).toBeInTheDocument();
        expect(screen.getByText('Coverage Score')).toBeInTheDocument();
        expect(screen.getByText('Compliance Score')).toBeInTheDocument();
        expect(screen.getByText('ACGME Violations')).toBeInTheDocument();
      });
    });

    it('should show loading skeletons while fetching metrics', async () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });

    it('should show error message when metrics fail to load', async () => {
      mockedApi.get.mockRejectedValue(new Error('API Error'));

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load metrics')).toBeInTheDocument();
      });
    });
  });

  describe('Alerts Section', () => {
    beforeEach(() => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/analytics/metrics/current')) {
          return Promise.resolve(analyticsMockResponses.currentMetrics);
        }
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve(analyticsMockResponses.alerts);
        }
        return Promise.resolve([]);
      });
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
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/analytics/metrics/current')) {
          return Promise.resolve(analyticsMockResponses.currentMetrics);
        }
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]);
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
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
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

      const refreshButton = screen.getByText('Refresh');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(refreshButton).toBeDisabled();
      });
    });
  });

  describe('Export Functionality', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
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
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith('/analytics/metrics/current');
      });
    });

    it('should fetch alerts on mount', async () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('/analytics/metrics/current')) {
          return Promise.resolve(analyticsMockResponses.currentMetrics);
        }
        if (url.includes('/analytics/alerts')) {
          return Promise.resolve([]);
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
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);
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
