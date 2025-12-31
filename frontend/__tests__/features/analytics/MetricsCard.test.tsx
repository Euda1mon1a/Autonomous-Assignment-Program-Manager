import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { MetricsCard, MetricsCardSkeleton } from '@/features/analytics/MetricsCard';
import { analyticsMockFactories } from './analytics-mocks';

describe('MetricsCard', () => {
  describe('Rendering', () => {
    it('should render metric name', () => {
      const metric = analyticsMockFactories.metric({ name: 'Fairness Score' });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText('Fairness Score')).toBeInTheDocument();
    });

    it('should render metric value', () => {
      const metric = analyticsMockFactories.metric({ value: 85.5 });

      render(<MetricsCard metric={metric} />);

      // The MetricsCard formats 'score' unit with 2 decimal places
      expect(screen.getByText('85.50')).toBeInTheDocument();
    });

    it('should render metric description', () => {
      const metric = analyticsMockFactories.metric({
        description: 'Overall schedule fairness metric',
      });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText('Overall schedule fairness metric')).toBeInTheDocument();
    });

    it('should format percentage values correctly', () => {
      const metric = analyticsMockFactories.metric({ value: 92.3, unit: '%' });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText('92.3%')).toBeInTheDocument();
    });

    it('should format score values correctly', () => {
      const metric = analyticsMockFactories.metric({ value: 85.567, unit: 'score' });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText('85.57')).toBeInTheDocument();
    });

    it('should format integer values correctly', () => {
      const metric = analyticsMockFactories.metric({ value: 3, unit: 'violations' });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  describe('Status Indicators', () => {
    it('should show CheckCircle icon for excellent status', () => {
      const metric = analyticsMockFactories.metric({ status: 'excellent' });
      const { container } = render(<MetricsCard metric={metric} />);

      const icon = container.querySelector('.text-green-600');
      expect(icon).toBeInTheDocument();
    });

    it('should show CheckCircle icon for good status', () => {
      const metric = analyticsMockFactories.metric({ status: 'good' });
      const { container } = render(<MetricsCard metric={metric} />);

      const icon = container.querySelector('.text-blue-600');
      expect(icon).toBeInTheDocument();
    });

    it('should show AlertTriangle icon for warning status', () => {
      const metric = analyticsMockFactories.metric({ status: 'warning' });
      const { container } = render(<MetricsCard metric={metric} />);

      const icon = container.querySelector('.text-yellow-600');
      expect(icon).toBeInTheDocument();
    });

    it('should show AlertCircle icon for critical status', () => {
      const metric = analyticsMockFactories.metric({ status: 'critical' });
      const { container } = render(<MetricsCard metric={metric} />);

      const icon = container.querySelector('.text-red-600');
      expect(icon).toBeInTheDocument();
    });

    it('should apply green background for excellent status', () => {
      const metric = analyticsMockFactories.metric({ status: 'excellent' });
      const { container } = render(<MetricsCard metric={metric} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-green-50');
      expect(card).toHaveClass('border-green-200');
    });

    it('should apply yellow background for warning status', () => {
      const metric = analyticsMockFactories.metric({ status: 'warning' });
      const { container } = render(<MetricsCard metric={metric} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-yellow-50');
      expect(card).toHaveClass('border-yellow-200');
    });

    it('should apply red background for critical status', () => {
      const metric = analyticsMockFactories.metric({ status: 'critical' });
      const { container } = render(<MetricsCard metric={metric} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('bg-red-50');
      expect(card).toHaveClass('border-red-200');
    });
  });

  describe('Trend Indicators', () => {
    it('should show TrendingUp icon for upward trend', () => {
      const metric = analyticsMockFactories.metric({ trend: 'up', trendValue: 2.5 });
      const { container } = render(<MetricsCard metric={metric} />);

      const trendIcon = container.querySelector('.text-green-600');
      expect(trendIcon).toBeInTheDocument();
    });

    it('should show TrendingDown icon for downward trend', () => {
      const metric = analyticsMockFactories.metric({ trend: 'down', trendValue: -2.5 });
      const { container } = render(<MetricsCard metric={metric} />);

      const trendIcon = container.querySelector('.text-red-600');
      expect(trendIcon).toBeInTheDocument();
    });

    it('should show Minus icon for stable trend', () => {
      const metric = analyticsMockFactories.metric({ trend: 'stable', trendValue: 0.1 });
      const { container } = render(<MetricsCard metric={metric} />);

      const trendIcon = container.querySelector('.text-gray-600');
      expect(trendIcon).toBeInTheDocument();
    });

    it('should display trend value with positive sign for upward trend', () => {
      const metric = analyticsMockFactories.metric({ trend: 'up', trendValue: 2.5 });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText(/\+2\.5% from last period/)).toBeInTheDocument();
    });

    it('should display trend value with negative sign for downward trend', () => {
      const metric = analyticsMockFactories.metric({ trend: 'down', trendValue: -2.5 });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText(/-2\.5% from last period/)).toBeInTheDocument();
    });

    it('should display absolute trend value', () => {
      const metric = analyticsMockFactories.metric({ trend: 'up', trendValue: 3.14 });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText(/3\.1%/)).toBeInTheDocument();
    });
  });

  describe('Threshold Display', () => {
    it('should display warning and critical thresholds', () => {
      const metric = analyticsMockFactories.metric({
        threshold: { warning: 70, critical: 50 },
      });

      render(<MetricsCard metric={metric} />);

      expect(screen.getByText('70')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
    });

    it('should display threshold progress bar', () => {
      const metric = analyticsMockFactories.metric({
        value: 75,
        threshold: { warning: 70, critical: 50 },
      });
      const { container } = render(<MetricsCard metric={metric} />);

      const progressBar = container.querySelector('.h-2.bg-gray-200');
      expect(progressBar).toBeInTheDocument();
    });

    it('should not display threshold section when no threshold provided', () => {
      const metric = analyticsMockFactories.metric({ threshold: undefined });

      render(<MetricsCard metric={metric} />);

      expect(screen.queryByText('Threshold')).not.toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('should render in compact mode', () => {
      const metric = analyticsMockFactories.metric();

      render(<MetricsCard metric={metric} compact={true} />);

      expect(screen.getByText(metric.name)).toBeInTheDocument();
    });

    it('should not display description in compact mode', () => {
      const metric = analyticsMockFactories.metric({
        description: 'Overall schedule fairness metric',
      });

      render(<MetricsCard metric={metric} compact={true} />);

      expect(screen.queryByText('Overall schedule fairness metric')).not.toBeInTheDocument();
    });

    it('should not display threshold in compact mode', () => {
      const metric = analyticsMockFactories.metric({
        threshold: { warning: 70, critical: 50 },
      });

      render(<MetricsCard metric={metric} compact={true} />);

      expect(screen.queryByText('Threshold')).not.toBeInTheDocument();
    });

    it('should apply compact styling', () => {
      const metric = analyticsMockFactories.metric();
      const { container } = render(<MetricsCard metric={metric} compact={true} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('p-3');
    });
  });

  describe('Click Interaction', () => {
    it('should call onClick handler when clicked', async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();
      const metric = analyticsMockFactories.metric();

      render(<MetricsCard metric={metric} onClick={handleClick} />);

      const card = screen.getByRole('button');
      await user.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should apply hover styles when clickable', () => {
      const handleClick = jest.fn();
      const metric = analyticsMockFactories.metric();
      const { container } = render(<MetricsCard metric={metric} onClick={handleClick} />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('hover:shadow-lg');
      expect(card).toHaveClass('cursor-pointer');
    });

    it('should not be clickable when no onClick provided', () => {
      const metric = analyticsMockFactories.metric();
      const { container } = render(<MetricsCard metric={metric} />);

      const card = container.querySelector('button');
      expect(card).toBeDisabled();
      expect(card).toHaveClass('cursor-default');
    });
  });

  describe('Custom ClassName', () => {
    it('should apply custom className', () => {
      const metric = analyticsMockFactories.metric();
      const { container } = render(<MetricsCard metric={metric} className="custom-class" />);

      const card = container.querySelector('button');
      expect(card).toHaveClass('custom-class');
    });
  });
});

describe('MetricsCardSkeleton', () => {
  describe('Loading State', () => {
    it('should render loading skeleton', () => {
      const { container } = render(<MetricsCardSkeleton />);

      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('should render compact skeleton', () => {
      const { container } = render(<MetricsCardSkeleton compact={true} />);

      const skeleton = container.querySelector('.p-3');
      expect(skeleton).toBeInTheDocument();
    });

    it('should have proper skeleton structure for full mode', () => {
      const { container } = render(<MetricsCardSkeleton />);

      const placeholders = container.querySelectorAll('.bg-gray-300');
      expect(placeholders.length).toBeGreaterThan(0);
    });

    it('should have proper skeleton structure for compact mode', () => {
      const { container } = render(<MetricsCardSkeleton compact={true} />);

      const placeholders = container.querySelectorAll('.bg-gray-300');
      expect(placeholders.length).toBeGreaterThan(0);
    });
  });
});
