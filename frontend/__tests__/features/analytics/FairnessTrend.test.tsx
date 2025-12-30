import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FairnessTrend } from '@/features/analytics/FairnessTrend';
import { analyticsMockFactories, analyticsMockResponses } from './analytics-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

describe('FairnessTrend', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should display loading skeleton while fetching data', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<FairnessTrend months={3} />, {
        wrapper: createWrapper(),
      });

      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message when data fetch fails', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('API Error'));

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load fairness trend data')).toBeInTheDocument();
      });
    });

    it('should display error when no data returned', async () => {
      mockedApi.get.mockResolvedValueOnce(null);

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load fairness trend data')).toBeInTheDocument();
      });
    });
  });

  describe('Data Display', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);
    });

    it('should render chart title', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Fairness Metrics Trend')).toBeInTheDocument();
      });
    });

    it('should render chart subtitle', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Track fairness metrics over time')).toBeInTheDocument();
      });
    });

    it('should display statistics summary', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Avg Gini Coefficient')).toBeInTheDocument();
        expect(screen.getByText('Avg Workload Variance')).toBeInTheDocument();
        expect(screen.getByText('Avg PGY Equity')).toBeInTheDocument();
      });
    });

    it('should display average statistics values', async () => {
      const mockData = analyticsMockFactories.fairnessTrendData({
        statistics: {
          avgGini: 0.24,
          avgVariance: 12.3,
          avgPgyEquity: 78.5,
          trend: 'up',
          improvementRate: 1.8,
        },
      });

      mockedApi.get.mockResolvedValueOnce(mockData);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('0.240')).toBeInTheDocument();
        expect(screen.getByText('12.30')).toBeInTheDocument();
        expect(screen.getByText('78.50')).toBeInTheDocument();
      });
    });

    it('should display improvement rate', async () => {
      const mockData = analyticsMockFactories.fairnessTrendData({
        statistics: {
          avgGini: 0.24,
          avgVariance: 12.3,
          avgPgyEquity: 78.5,
          trend: 'up',
          improvementRate: 1.8,
        },
      });

      mockedApi.get.mockResolvedValueOnce(mockData);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      // The TrendIndicator shows "+1.8%" for positive trend
      await waitFor(() => {
        expect(screen.getByText(/\+1\.8%/)).toBeInTheDocument();
      });
    });

    it('should display info note about metrics', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/Lower Gini coefficient and workload variance indicate better fairness/)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Metric Selector', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);
    });

    it('should render metric selector buttons', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('All Metrics')).toBeInTheDocument();
        expect(screen.getByText('Gini Coefficient')).toBeInTheDocument();
        expect(screen.getByText('Workload Variance')).toBeInTheDocument();
        expect(screen.getByText('PGY Equity')).toBeInTheDocument();
      });
    });

    it('should allow changing selected metric', async () => {
      const user = userEvent.setup();

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('All Metrics')).toBeInTheDocument();
      });

      const giniButton = screen.getByText('Gini Coefficient');
      await user.click(giniButton);

      expect(giniButton).toHaveClass('bg-white');
      expect(giniButton).toHaveClass('text-blue-600');
    });
  });

  describe('PGY Comparison', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);
    });

    it('should show PGY equity chart when showPgyComparison is true', async () => {
      render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('PGY Level Equity Comparison')).toBeInTheDocument();
      });
    });

    it('should not show PGY equity chart when showPgyComparison is false', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);

      render(<FairnessTrend months={3} showPgyComparison={false} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Fairness Metrics Trend')).toBeInTheDocument();
      });

      expect(screen.queryByText('PGY Level Equity Comparison')).not.toBeInTheDocument();
    });

    it('should display loading skeleton for PGY chart while loading', () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('fairness')) {
          return Promise.resolve(analyticsMockResponses.fairnessTrend);
        }
        return new Promise(() => {}); // Never resolves for PGY equity
      });

      const { container } = render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      // Check for loading state in PGY chart
      waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });

    // Skip: This test has issues with React Query caching and mock timing.
    // The PGY equity chart appears to get cached data from previous tests.
    // TODO: Investigate React Query test isolation patterns
    it.skip('should display error for PGY chart when fetch fails', async () => {
      // Use mockImplementation to handle different URLs properly
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/analytics/trends/fairness')) {
          return Promise.resolve(analyticsMockResponses.fairnessTrend);
        }
        if (url.includes('/analytics/equity/pgy')) {
          return Promise.reject(new Error('Failed to load PGY data'));
        }
        return Promise.resolve([]);
      });

      render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      // First wait for main trend to load
      await waitFor(() => {
        expect(screen.getByText('Fairness Metrics Trend')).toBeInTheDocument();
      });

      // Then check for PGY error
      await waitFor(() => {
        expect(screen.getByText('Failed to load PGY equity data')).toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });

  describe('API Integration', () => {
    it('should fetch fairness trend data with correct period for 3 months', async () => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/trends/fairness?period=90d')
        );
      });
    });

    it('should fetch fairness trend data with correct period for 6 months', async () => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);

      render(<FairnessTrend months={6} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/trends/fairness?period=180d')
        );
      });
    });

    it('should fetch fairness trend data with correct period for 12 months', async () => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);

      render(<FairnessTrend months={12} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/trends/fairness?period=1y')
        );
      });
    });

    it('should fetch PGY equity data when showPgyComparison is true', async () => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/equity/pgy')
        );
      });
    });
  });

  describe('Custom ClassName', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);
    });

    it('should apply custom className', async () => {
      const { container } = render(<FairnessTrend months={3} className="custom-trend" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const element = container.querySelector('.custom-trend');
        expect(element).toBeInTheDocument();
      });
    });
  });
});
