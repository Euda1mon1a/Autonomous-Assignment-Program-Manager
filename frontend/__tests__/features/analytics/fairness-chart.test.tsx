/**
 * Fairness Chart Tests
 *
 * Tests for fairness distribution charts and visualizations,
 * including Gini coefficient, workload variance, and equity scores.
 */

import { render, screen, waitFor, within } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { FairnessTrend } from '@/features/analytics/FairnessTrend';
import { MetricsCard } from '@/features/analytics/MetricsCard';
import { analyticsMockFactories, analyticsMockResponses } from './analytics-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

describe('Fairness Chart Visualizations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);
    });

    it('should render the fairness trend chart container', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Fairness Metrics Trend')).toBeInTheDocument();
      });
    });

    it('should render chart with subtitle description', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Track fairness metrics over time')).toBeInTheDocument();
      });
    });

    it('should render all metric filter buttons', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('All Metrics')).toBeInTheDocument();
        expect(screen.getByText('Gini Coefficient')).toBeInTheDocument();
        expect(screen.getByText('Workload Variance')).toBeInTheDocument();
        expect(screen.getByText('PGY Equity')).toBeInTheDocument();
      });
    });

    it('should render statistics summary section', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Avg Gini Coefficient')).toBeInTheDocument();
        expect(screen.getByText('Avg Workload Variance')).toBeInTheDocument();
        expect(screen.getByText('Avg PGY Equity')).toBeInTheDocument();
        expect(screen.getByText('Overall Trend')).toBeInTheDocument();
      });
    });

    it('should render metric cards for fairness metrics', () => {
      const fairnessMetric = analyticsMockFactories.metric({
        name: 'Fairness Score',
        value: 85.5,
        category: 'fairness',
        status: 'good',
      });

      render(<MetricsCard metric={fairnessMetric} />);

      expect(screen.getByText('Fairness Score')).toBeInTheDocument();
      expect(screen.getByText('85.50')).toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    it('should display Gini coefficient values with proper precision', () => {
      const giniMetric = analyticsMockFactories.metric({
        name: 'Gini Coefficient',
        value: 0.2456,
        unit: 'score',
        category: 'fairness',
        status: 'excellent',
      });

      render(<MetricsCard metric={giniMetric} />);

      expect(screen.getByText('0.25')).toBeInTheDocument();
    });

    it('should display workload variance metric', () => {
      const varianceMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 15.789,
        unit: 'variance',
        category: 'workload',
        status: 'good',
      });

      render(<MetricsCard metric={varianceMetric} />);

      expect(screen.getByText('16')).toBeInTheDocument(); // Integer formatting
    });

    it('should display PGY equity score correctly', () => {
      const pgyMetric = analyticsMockFactories.metric({
        name: 'PGY Equity Score',
        value: 82.456,
        unit: 'score',
        category: 'fairness',
        status: 'good',
      });

      render(<MetricsCard metric={pgyMetric} />);

      expect(screen.getByText('82.46')).toBeInTheDocument();
    });

    it('should display trend direction with percentage', () => {
      const trendMetric = analyticsMockFactories.metric({
        name: 'Fairness Score',
        value: 85.0,
        unit: 'score',
        category: 'fairness',
        status: 'good',
        trend: 'up',
        trendValue: 5.7,
      });

      render(<MetricsCard metric={trendMetric} />);

      expect(screen.getByText(/\+5\.7% from last period/)).toBeInTheDocument();
    });

    it('should display fairness metrics chart when data is available', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      const { container } = render(<FairnessTrend months={3} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(container.querySelector('[role="img"]')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should display loading skeleton while fetching fairness data', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      const { container } = render(<FairnessTrend months={3} />, {
        wrapper: createWrapper(),
      });

      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('should show skeleton with proper structure', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      const { container } = render(<FairnessTrend months={3} />, {
        wrapper: createWrapper(),
      });

      const skeletonElements = container.querySelectorAll('.bg-gray-300, .bg-gray-200');
      expect(skeletonElements.length).toBeGreaterThan(0);
    });

    it('should display loading state for Gini coefficient metric card', () => {
      const giniMetric = analyticsMockFactories.metric({
        name: 'Gini Coefficient',
        value: 0.25,
        category: 'fairness',
        status: 'excellent',
        trend: 'down',
        trendValue: -1.5,
      });

      render(<MetricsCard metric={giniMetric} />);
      expect(screen.getByText('Gini Coefficient')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when fairness data fails to load', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('Network error'));

      render(<FairnessTrend months={3} showPgyComparison={false} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load fairness trend data')).toBeInTheDocument();
      });
    });

    it('should display error when API returns null data', async () => {
      mockedApi.get.mockResolvedValueOnce(null);

      render(<FairnessTrend months={3} showPgyComparison={false} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load fairness trend data')).toBeInTheDocument();
      });
    });

    it('should show error indicator in error boundary', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('API Error'));

      const { container } = render(<FairnessTrend months={3} showPgyComparison={false} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const errorContainer = container.querySelector('.border-red-200');
        expect(errorContainer).toBeInTheDocument();
      });
    });

    it('should render chart successfully even with minimal data', async () => {
      const emptyData = analyticsMockFactories.fairnessTrendData({
        dataPoints: [],
      });

      mockedApi.get.mockResolvedValueOnce(emptyData);

      render(<FairnessTrend months={3} showPgyComparison={false} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Fairness Metrics Trend')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);
    });

    it('should allow selecting Gini Coefficient filter', async () => {
      const user = userEvent.setup();

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Gini Coefficient')).toBeInTheDocument();
      });

      const giniButton = screen.getByText('Gini Coefficient');
      await user.click(giniButton);

      expect(giniButton).toHaveClass('bg-white');
      expect(giniButton).toHaveClass('text-blue-600');
    });

    it('should allow selecting Workload Variance filter', async () => {
      const user = userEvent.setup();

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Workload Variance')).toBeInTheDocument();
      });

      const varianceButton = screen.getByText('Workload Variance');
      await user.click(varianceButton);

      expect(varianceButton).toHaveClass('bg-white');
      expect(varianceButton).toHaveClass('text-blue-600');
    });

    it('should allow selecting PGY Equity filter', async () => {
      const user = userEvent.setup();

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('PGY Equity')).toBeInTheDocument();
      });

      const equityButton = screen.getByText('PGY Equity');
      await user.click(equityButton);

      expect(equityButton).toHaveClass('bg-white');
      expect(equityButton).toHaveClass('text-blue-600');
    });

    it('should allow returning to All Metrics view', async () => {
      const user = userEvent.setup();

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('All Metrics')).toBeInTheDocument();
      });

      const giniButton = screen.getByText('Gini Coefficient');
      await user.click(giniButton);

      const allMetricsButton = screen.getByText('All Metrics');
      await user.click(allMetricsButton);

      expect(allMetricsButton).toHaveClass('bg-white');
      expect(allMetricsButton).toHaveClass('text-blue-600');
    });

    it('should handle metric card click interaction', async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();

      const fairnessMetric = analyticsMockFactories.metric({
        name: 'Fairness Score',
        value: 85.5,
        category: 'fairness',
      });

      render(<MetricsCard metric={fairnessMetric} onClick={handleClick} />);

      const card = screen.getByRole('button');
      await user.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should update aria-pressed state when metric filter is selected', async () => {
      const user = userEvent.setup();

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Gini Coefficient')).toBeInTheDocument();
      });

      const giniButton = screen.getByLabelText('Filter by Gini Coefficient');
      await user.click(giniButton);

      expect(giniButton).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);
    });

    it('should have proper ARIA labels for metric filters', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText('Metric filter selection')).toBeInTheDocument();
      });
    });

    it('should have descriptive ARIA label for statistics summary', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText('Fairness statistics summary')).toBeInTheDocument();
      });
    });

    it('should have ARIA labels for individual statistics', async () => {
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
        expect(
          screen.getByLabelText('Average Gini Coefficient: 0.240')
        ).toBeInTheDocument();
      });
    });

    it('should have accessible chart description', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/Line chart showing fairness metrics/)).toBeInTheDocument();
      });
    });

    it('should provide interpretation guidance', async () => {
      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        const infoNote = screen.getByRole('note');
        expect(infoNote).toBeInTheDocument();
        expect(
          within(infoNote).getByText(/Lower Gini coefficient and workload variance/)
        ).toBeInTheDocument();
      });
    });
  });
});
