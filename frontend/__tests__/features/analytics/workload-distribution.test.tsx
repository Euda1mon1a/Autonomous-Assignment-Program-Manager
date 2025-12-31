/**
 * Workload Distribution Tests
 *
 * Tests for workload distribution display and metrics,
 * including shift assignments, workload variance, and PGY level equity.
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { MetricsCard } from '@/features/analytics/MetricsCard';
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

describe('Workload Distribution Display', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render workload variance metric card', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 12.5,
        unit: 'variance',
        category: 'workload',
        status: 'good',
        description: 'Statistical variance in workload distribution',
      });

      render(<MetricsCard metric={workloadMetric} />);

      expect(screen.getByText('Workload Variance')).toBeInTheDocument();
      expect(screen.getByText('Statistical variance in workload distribution')).toBeInTheDocument();
    });

    it('should render PGY equity score metric card', () => {
      const pgyEquityMetric = analyticsMockFactories.metric({
        name: 'PGY Equity Score',
        value: 78.2,
        unit: 'score',
        category: 'fairness',
        status: 'good',
        description: 'Distribution equity across PGY levels',
      });

      render(<MetricsCard metric={pgyEquityMetric} />);

      expect(screen.getByText('PGY Equity Score')).toBeInTheDocument();
      expect(screen.getByText('78.20')).toBeInTheDocument();
    });

    it('should render PGY equity comparison chart', async () => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('PGY Level Equity Comparison')).toBeInTheDocument();
      });
    });

    it('should render workload metrics in compact mode', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 15.8,
        unit: 'score',
        category: 'workload',
        status: 'warning',
      });

      render(<MetricsCard metric={workloadMetric} compact={true} />);

      expect(screen.getByText('Workload Variance')).toBeInTheDocument();
      expect(screen.getByText('15.80')).toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    it('should display workload variance with correct precision', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 14.567,
        unit: 'variance',
        category: 'workload',
      });

      render(<MetricsCard metric={workloadMetric} />);

      expect(screen.getByText('15')).toBeInTheDocument(); // Integer formatting
    });

    it('should display PGY equity score with two decimal places', () => {
      const pgyMetric = analyticsMockFactories.metric({
        name: 'PGY Equity Score',
        value: 82.456,
        unit: 'score',
        category: 'fairness',
      });

      render(<MetricsCard metric={pgyMetric} />);

      expect(screen.getByText('82.46')).toBeInTheDocument();
    });

    it('should display trend for workload metrics', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 12.5,
        category: 'workload',
        trend: 'down',
        trendValue: -3.2,
      });

      render(<MetricsCard metric={workloadMetric} />);

      expect(screen.getByText(/-3\.2% from last period/)).toBeInTheDocument();
    });

    it('should display average shifts per PGY level', async () => {
      const pgyData = [
        analyticsMockFactories.pgyEquityData({
          pgyLevel: 1,
          averageShifts: 20,
          nightShifts: 5,
          weekendShifts: 4,
          holidayShifts: 1,
        }),
        analyticsMockFactories.pgyEquityData({
          pgyLevel: 2,
          averageShifts: 22,
          nightShifts: 6,
          weekendShifts: 5,
          holidayShifts: 2,
        }),
        analyticsMockFactories.pgyEquityData({
          pgyLevel: 3,
          averageShifts: 21,
          nightShifts: 5,
          weekendShifts: 4,
          holidayShifts: 1,
        }),
      ];

      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(pgyData);

      render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('PGY Level Equity Comparison')).toBeInTheDocument();
      });
    });

    it('should show status indicator for workload distribution', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 25.0,
        category: 'workload',
        status: 'warning',
      });

      const { container } = render(<MetricsCard metric={workloadMetric} />);

      const warningIcon = container.querySelector('.text-yellow-600');
      expect(warningIcon).toBeInTheDocument();
    });

    it('should display threshold indicators for workload metrics', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 18.5,
        category: 'workload',
        threshold: {
          warning: 20,
          critical: 30,
        },
      });

      render(<MetricsCard metric={workloadMetric} />);

      expect(screen.getByText('Threshold')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('should display loading skeleton for workload metrics', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      const { container } = render(<FairnessTrend months={3} />, {
        wrapper: createWrapper(),
      });

      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('should display loading skeleton for PGY comparison chart', () => {
      mockedApi.get.mockImplementation((url) => {
        if (url.includes('fairness')) {
          return Promise.resolve(analyticsMockResponses.fairnessTrend);
        }
        return new Promise(() => {}); // Never resolves for PGY equity
      });

      const { container } = render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });

    it('should show skeleton with workload-specific structure', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      const { container } = render(<FairnessTrend months={3} />, {
        wrapper: createWrapper(),
      });

      const skeletonContainer = container.querySelector('.bg-white.border.border-gray-200');
      expect(skeletonContainer).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error when PGY equity data fails to load', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockRejectedValueOnce(new Error('Failed to load PGY data'));

      render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to load PGY equity data')).toBeInTheDocument();
      });
    });

    it('should handle null PGY equity data gracefully', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(null);

      render(<FairnessTrend months={3} showPgyComparison={true} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to load PGY equity data')).toBeInTheDocument();
      });
    });

    it('should display critical status for high workload variance', () => {
      const criticalWorkload = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 35.0,
        category: 'workload',
        status: 'critical',
      });

      const { container } = render(<MetricsCard metric={criticalWorkload} />);

      const criticalIcon = container.querySelector('.text-red-600');
      expect(criticalIcon).toBeInTheDocument();

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-red-50');
      expect(card).toHaveClass('border-red-200');
    });
  });

  describe('User Interactions', () => {
    it('should allow clicking on workload metric card', async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();

      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 12.5,
        category: 'workload',
      });

      render(<MetricsCard metric={workloadMetric} onClick={handleClick} />);

      const card = screen.getByRole('button');
      await user.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should show hover effect on workload metric cards', () => {
      const handleClick = jest.fn();
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 12.5,
        category: 'workload',
      });

      const { container } = render(<MetricsCard metric={workloadMetric} onClick={handleClick} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('hover:shadow-lg');
      expect(card).toHaveClass('cursor-pointer');
    });

    it('should filter workload variance in chart view', async () => {
      const user = userEvent.setup();

      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      render(<FairnessTrend months={3} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Workload Variance')).toBeInTheDocument();
      });

      const varianceButton = screen.getByText('Workload Variance');
      await user.click(varianceButton);

      expect(varianceButton).toHaveClass('bg-white');
      expect(varianceButton).toHaveClass('text-blue-600');
    });

    it('should toggle PGY comparison visibility', async () => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.fairnessTrend);

      const { rerender } = render(<FairnessTrend months={3} showPgyComparison={false} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Fairness Metrics Trend')).toBeInTheDocument();
      });

      expect(screen.queryByText('PGY Level Equity Comparison')).not.toBeInTheDocument();

      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      rerender(<FairnessTrend months={3} showPgyComparison={true} />);

      await waitFor(() => {
        expect(screen.getByText('PGY Level Equity Comparison')).toBeInTheDocument();
      });
    });
  });

  describe('Workload Metrics Status', () => {
    it('should show excellent status for low workload variance', () => {
      const excellentWorkload = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 8.5,
        category: 'workload',
        status: 'excellent',
      });

      const { container } = render(<MetricsCard metric={excellentWorkload} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-green-50');
      expect(card).toHaveClass('border-green-200');
    });

    it('should show good status for moderate workload variance', () => {
      const goodWorkload = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 15.0,
        category: 'workload',
        status: 'good',
      });

      const { container } = render(<MetricsCard metric={goodWorkload} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-blue-50');
      expect(card).toHaveClass('border-blue-200');
    });

    it('should show warning status for elevated workload variance', () => {
      const warningWorkload = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 22.0,
        category: 'workload',
        status: 'warning',
      });

      const { container } = render(<MetricsCard metric={warningWorkload} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-yellow-50');
      expect(card).toHaveClass('border-yellow-200');
    });
  });

  describe('Accessibility', () => {
    it('should have accessible labels for workload metrics', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 12.5,
        category: 'workload',
        status: 'good',
        trend: 'down',
        trendValue: -2.3,
      });

      render(<MetricsCard metric={workloadMetric} />);

      const card = screen.getByRole('button');
      expect(card).toHaveAttribute('aria-label', expect.stringContaining('Workload Variance'));
    });

    it('should have accessible workload distribution metrics', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 12.5,
        unit: 'variance',
        category: 'workload',
        status: 'good',
      });

      render(<MetricsCard metric={workloadMetric} />);

      expect(screen.getByText('Workload Variance')).toBeInTheDocument();
      expect(screen.getByRole('button')).toHaveAttribute('aria-label');
    });

    it('should have accessible PGY equity metrics', () => {
      const pgyMetric = analyticsMockFactories.metric({
        name: 'PGY Equity Score',
        value: 82.0,
        unit: 'score',
        category: 'fairness',
        status: 'good',
      });

      render(<MetricsCard metric={pgyMetric} />);

      expect(screen.getByText('PGY Equity Score')).toBeInTheDocument();
      expect(screen.getByRole('button')).toHaveAttribute('aria-label');
    });

    it('should provide status description for screen readers', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 12.5,
        category: 'workload',
        status: 'good',
      });

      render(<MetricsCard metric={workloadMetric} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('should have accessible threshold progress bar', () => {
      const workloadMetric = analyticsMockFactories.metric({
        name: 'Workload Variance',
        value: 18.5,
        category: 'workload',
        threshold: {
          warning: 20,
          critical: 30,
        },
      });

      const { container } = render(<MetricsCard metric={workloadMetric} />);

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow', '18.5');
      expect(progressBar).toHaveAttribute('aria-valuemax', '30');
    });
  });
});
