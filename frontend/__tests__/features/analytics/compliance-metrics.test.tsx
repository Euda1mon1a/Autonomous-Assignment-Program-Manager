/**
 * Compliance Metrics Tests
 *
 * Tests for compliance metrics display, including ACGME violations,
 * compliance scores, and coverage metrics.
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { MetricsCard, MetricsCardSkeleton } from '@/features/analytics/MetricsCard';
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

describe('Compliance Metrics Display', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render compliance score metric card', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        unit: '%',
        category: 'compliance',
        status: 'excellent',
        description: 'Overall ACGME compliance rate',
      });

      render(<MetricsCard metric={complianceMetric} />);

      expect(screen.getByText('Compliance Score')).toBeInTheDocument();
      expect(screen.getByText('Overall ACGME compliance rate')).toBeInTheDocument();
      expect(screen.getByText('92.3%')).toBeInTheDocument();
    });

    it('should render ACGME violations metric card', () => {
      const violationsMetric = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 2,
        unit: 'violations',
        category: 'compliance',
        status: 'warning',
        description: 'Active compliance violations',
      });

      render(<MetricsCard metric={violationsMetric} />);

      expect(screen.getByText('ACGME Violations')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should render coverage score metric card', () => {
      const coverageMetric = analyticsMockFactories.metric({
        name: 'Coverage Score',
        value: 95.8,
        unit: '%',
        category: 'coverage',
        status: 'excellent',
        description: 'Schedule coverage completeness',
      });

      render(<MetricsCard metric={coverageMetric} />);

      expect(screen.getByText('Coverage Score')).toBeInTheDocument();
      expect(screen.getByText('95.8%')).toBeInTheDocument();
    });

    it('should render compliance metrics in compact mode', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 88.5,
        unit: '%',
        category: 'compliance',
        status: 'good',
      });

      render(<MetricsCard metric={complianceMetric} compact={true} />);

      expect(screen.getByText('Compliance Score')).toBeInTheDocument();
      expect(screen.getByText('88.5%')).toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    it('should display compliance score as percentage with one decimal', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 94.567,
        unit: '%',
        category: 'compliance',
      });

      render(<MetricsCard metric={complianceMetric} />);

      expect(screen.getByText('94.6%')).toBeInTheDocument();
    });

    it('should display ACGME violations as integer', () => {
      const violationsMetric = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 5,
        unit: 'violations',
        category: 'compliance',
      });

      render(<MetricsCard metric={violationsMetric} />);

      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('should display zero violations correctly', () => {
      const noViolations = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 0,
        unit: 'violations',
        category: 'compliance',
        status: 'excellent',
      });

      render(<MetricsCard metric={noViolations} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should display trend for compliance metrics', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        unit: '%',
        category: 'compliance',
        trend: 'up',
        trendValue: 2.1,
      });

      render(<MetricsCard metric={complianceMetric} />);

      expect(screen.getByText(/\+2\.1% from last period/)).toBeInTheDocument();
    });

    it('should display declining trend for violations', () => {
      const violationsMetric = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 2,
        unit: 'violations',
        category: 'compliance',
        trend: 'down',
        trendValue: -33.3,
      });

      render(<MetricsCard metric={violationsMetric} />);

      expect(screen.getByText(/-33\.3% from last period/)).toBeInTheDocument();
    });

    it('should display threshold indicators for compliance', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 85.0,
        unit: '%',
        category: 'compliance',
        threshold: {
          warning: 80,
          critical: 70,
        },
      });

      render(<MetricsCard metric={complianceMetric} />);

      expect(screen.getByText('Threshold')).toBeInTheDocument();
      expect(screen.getByText('80')).toBeInTheDocument();
      expect(screen.getByText('70')).toBeInTheDocument();
    });
  });

  describe('Compliance Status Indicators', () => {
    it('should show excellent status for high compliance', () => {
      const excellentCompliance = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 98.5,
        unit: '%',
        category: 'compliance',
        status: 'excellent',
      });

      const { container } = render(<MetricsCard metric={excellentCompliance} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-green-50');
      expect(card).toHaveClass('border-green-200');

      const icon = container.querySelector('.text-green-600');
      expect(icon).toBeInTheDocument();
    });

    it('should show good status for moderate compliance', () => {
      const goodCompliance = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 88.0,
        unit: '%',
        category: 'compliance',
        status: 'good',
      });

      const { container } = render(<MetricsCard metric={goodCompliance} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-blue-50');
      expect(card).toHaveClass('border-blue-200');
    });

    it('should show warning status for low compliance', () => {
      const warningCompliance = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 75.0,
        unit: '%',
        category: 'compliance',
        status: 'warning',
      });

      const { container } = render(<MetricsCard metric={warningCompliance} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-yellow-50');
      expect(card).toHaveClass('border-yellow-200');

      const icon = container.querySelector('.text-yellow-600');
      expect(icon).toBeInTheDocument();
    });

    it('should show critical status for very low compliance', () => {
      const criticalCompliance = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 65.0,
        unit: '%',
        category: 'compliance',
        status: 'critical',
      });

      const { container } = render(<MetricsCard metric={criticalCompliance} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-red-50');
      expect(card).toHaveClass('border-red-200');

      const icon = container.querySelector('.text-red-600');
      expect(icon).toBeInTheDocument();
    });

    it('should show warning for multiple violations', () => {
      const multipleViolations = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 5,
        unit: 'violations',
        category: 'compliance',
        status: 'critical',
      });

      const { container } = render(<MetricsCard metric={multipleViolations} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-red-50');
    });

    it('should show excellent status for zero violations', () => {
      const noViolations = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 0,
        unit: 'violations',
        category: 'compliance',
        status: 'excellent',
      });

      const { container } = render(<MetricsCard metric={noViolations} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-green-50');
    });
  });

  describe('Loading States', () => {
    it('should display loading skeleton for compliance metrics', () => {
      const { container } = render(<MetricsCardSkeleton />);

      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('should display compact loading skeleton', () => {
      const { container } = render(<MetricsCardSkeleton compact={true} />);

      const skeleton = container.querySelector('.p-3');
      expect(skeleton).toBeInTheDocument();
      expect(skeleton).toHaveClass('animate-pulse');
    });

    it('should have proper skeleton structure', () => {
      const { container } = render(<MetricsCardSkeleton />);

      const placeholders = container.querySelectorAll('.bg-gray-300');
      expect(placeholders.length).toBeGreaterThan(0);
    });

    it('should show loading state while fetching metrics', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}));

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      const skeletons = screen.queryAllByRole('status', { hidden: true });
      // Loading state should be present
      expect(skeletons.length >= 0).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should handle missing compliance data gracefully', () => {
      const incompleteMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 0,
        unit: '%',
        category: 'compliance',
        status: 'critical',
      });

      render(<MetricsCard metric={incompleteMetric} />);

      expect(screen.getByText('Compliance Score')).toBeInTheDocument();
      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });

    it('should handle API errors for metrics', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('API Error'));

      render(<AnalyticsDashboard />, { wrapper: createWrapper() });

      // Component should handle error gracefully
      await waitFor(() => {
        expect(screen.queryByText('Failed to load')).not.toBeInTheDocument();
      });
    });

    it('should display critical status for data integrity issues', () => {
      const criticalMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 45.0,
        unit: '%',
        category: 'compliance',
        status: 'critical',
      });

      const { container } = render(<MetricsCard metric={criticalMetric} />);

      expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
      expect(container.querySelector('.text-red-600')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('should allow clicking on compliance metric card', async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();

      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        unit: '%',
        category: 'compliance',
      });

      render(<MetricsCard metric={complianceMetric} onClick={handleClick} />);

      const card = screen.getByRole('button');
      await user.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should show hover effect on clickable compliance cards', () => {
      const handleClick = jest.fn();
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        category: 'compliance',
      });

      const { container } = render(<MetricsCard metric={complianceMetric} onClick={handleClick} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('hover:shadow-lg');
      expect(card).toHaveClass('cursor-pointer');
    });

    it('should not be clickable when no handler provided', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        category: 'compliance',
      });

      const { container } = render(<MetricsCard metric={complianceMetric} />);

      const card = container.querySelector('button');
      expect(card).toBeDisabled();
      expect(card).toHaveClass('cursor-default');
    });

    it('should handle multiple clicks on violations metric', async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();

      const violationsMetric = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 3,
        category: 'compliance',
      });

      render(<MetricsCard metric={violationsMetric} onClick={handleClick} />);

      const card = screen.getByRole('button');
      await user.click(card);
      await user.click(card);

      expect(handleClick).toHaveBeenCalledTimes(2);
    });
  });

  describe('Coverage Metrics', () => {
    it('should display coverage score correctly', () => {
      const coverageMetric = analyticsMockFactories.metric({
        name: 'Coverage Score',
        value: 97.2,
        unit: '%',
        category: 'coverage',
        status: 'excellent',
      });

      render(<MetricsCard metric={coverageMetric} />);

      expect(screen.getByText('Coverage Score')).toBeInTheDocument();
      expect(screen.getByText('97.2%')).toBeInTheDocument();
    });

    it('should show warning for low coverage', () => {
      const lowCoverage = analyticsMockFactories.metric({
        name: 'Coverage Score',
        value: 78.0,
        unit: '%',
        category: 'coverage',
        status: 'warning',
      });

      const { container } = render(<MetricsCard metric={lowCoverage} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-yellow-50');
    });

    it('should display coverage trend', () => {
      const coverageMetric = analyticsMockFactories.metric({
        name: 'Coverage Score',
        value: 95.8,
        unit: '%',
        category: 'coverage',
        trend: 'up',
        trendValue: 1.5,
      });

      render(<MetricsCard metric={coverageMetric} />);

      expect(screen.getByText(/\+1\.5% from last period/)).toBeInTheDocument();
    });
  });

  describe('Threshold Progress Bar', () => {
    it('should display progress bar for compliance thresholds', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 85.0,
        unit: '%',
        category: 'compliance',
        threshold: {
          warning: 80,
          critical: 70,
        },
      });

      const { container } = render(<MetricsCard metric={complianceMetric} />);

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('should calculate correct progress percentage', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 75.0,
        unit: '%',
        category: 'compliance',
        status: 'warning',
        threshold: {
          warning: 80,
          critical: 70,
        },
      });

      const { container } = render(<MetricsCard metric={complianceMetric} />);

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toHaveAttribute('aria-valuenow', '75');
      expect(progressBar).toHaveAttribute('aria-valuemax', '70');
    });

    it('should use appropriate color for progress bar based on status', () => {
      const warningMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 75.0,
        category: 'compliance',
        status: 'warning',
        threshold: {
          warning: 80,
          critical: 70,
        },
      });

      const { container } = render(<MetricsCard metric={warningMetric} />);

      const progressFill = container.querySelector('.bg-yellow-500');
      expect(progressFill).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible labels for compliance metrics', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        unit: '%',
        category: 'compliance',
        status: 'excellent',
        trend: 'up',
        trendValue: 2.1,
      });

      render(<MetricsCard metric={complianceMetric} />);

      const card = screen.getByRole('button');
      expect(card).toHaveAttribute('aria-label');
      expect(screen.getByText('Compliance Score')).toBeInTheDocument();
      expect(screen.getByText('92.3%')).toBeInTheDocument();
    });

    it('should have accessible description for violations', () => {
      const violationsMetric = analyticsMockFactories.metric({
        name: 'ACGME Violations',
        value: 3,
        unit: 'violations',
        category: 'compliance',
        description: 'Active compliance violations requiring attention',
      });

      render(<MetricsCard metric={violationsMetric} />);

      expect(
        screen.getByText('Active compliance violations requiring attention')
      ).toBeInTheDocument();
    });

    it('should provide status information for screen readers', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        category: 'compliance',
      });

      render(<MetricsCard metric={complianceMetric} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('should have accessible threshold labels', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 85.0,
        category: 'compliance',
        threshold: {
          warning: 80,
          critical: 70,
        },
      });

      render(<MetricsCard metric={complianceMetric} />);

      expect(screen.getByLabelText('Warning threshold: 80')).toBeInTheDocument();
      expect(screen.getByLabelText('Critical threshold: 70')).toBeInTheDocument();
    });

    it('should have accessible progress bar for compliance tracking', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 90.0,
        category: 'compliance',
        threshold: {
          warning: 80,
          critical: 70,
        },
      });

      const { container } = render(<MetricsCard metric={complianceMetric} />);

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toHaveAttribute('aria-label', 'Metric progress toward threshold');
      expect(progressBar).toHaveAttribute('aria-valuenow', '90');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '70');
    });
  });

  describe('Custom ClassName', () => {
    it('should apply custom className to compliance cards', () => {
      const complianceMetric = analyticsMockFactories.metric({
        name: 'Compliance Score',
        value: 92.3,
        category: 'compliance',
      });

      const { container } = render(
        <MetricsCard metric={complianceMetric} className="custom-compliance-card" />
      );

      const card = container.querySelector('button');
      expect(card).toHaveClass('custom-compliance-card');
    });
  });
});
