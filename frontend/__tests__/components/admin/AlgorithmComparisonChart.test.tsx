/**
 * Tests for AlgorithmComparisonChart component
 *
 * Tests algorithm comparison visualization, metrics display, and interactions
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  AlgorithmComparisonChart,
  MOCK_ALGORITHM_DATA,
  AlgorithmMetrics,
} from '@/components/admin/AlgorithmComparisonChart';

describe('AlgorithmComparisonChart', () => {
  const defaultProps = {
    data: MOCK_ALGORITHM_DATA,
  };

  describe('Rendering', () => {
    it('should render chart title', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      expect(screen.getByText('Algorithm Comparison')).toBeInTheDocument();
    });

    it('should display total run count', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      // Total runs: 45 + 38 + 22 + 67 = 172
      expect(screen.getByText(/Based on 172 runs/i)).toBeInTheDocument();
    });

    it('should render metric selector dropdown', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
    });

    it('should have coverage as default metric', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox') as HTMLSelectElement;
      expect(select.value).toBe('coverage');
    });

    it('should display all metric options', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox');
      expect(select).toHaveTextContent('Coverage');
      expect(select).toHaveTextContent('ACGME Violations');
      expect(select).toHaveTextContent('Fairness Score');
      expect(select).toHaveTextContent('Runtime');
      expect(select).toHaveTextContent('Stability');
    });
  });

  describe('Algorithm Bars', () => {
    it('should display all algorithm names', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      expect(screen.getByText('Greedy')).toBeInTheDocument();
      expect(screen.getByText('CP-SAT')).toBeInTheDocument();
      expect(screen.getByText('PuLP')).toBeInTheDocument();
      expect(screen.getByText('Hybrid')).toBeInTheDocument();
    });

    it('should display run count for each algorithm', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      expect(screen.getByText('45 runs')).toBeInTheDocument();
      expect(screen.getByText('38 runs')).toBeInTheDocument();
      expect(screen.getByText('22 runs')).toBeInTheDocument();
      expect(screen.getByText('67 runs')).toBeInTheDocument();
    });

    it('should display metric values', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      // Coverage values with % suffix
      expect(screen.getByText('89.5%')).toBeInTheDocument();
      expect(screen.getByText('96.2%')).toBeInTheDocument();
      expect(screen.getByText('91.8%')).toBeInTheDocument();
      expect(screen.getByText('97.5%')).toBeInTheDocument();
    });

    it('should mark best performer with star', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      // Hybrid has highest coverage (97.5%), should have star
      const hybridValue = screen.getByText('97.5%');
      expect(hybridValue.textContent).toContain('★');
    });
  });

  describe('Metric Switching', () => {
    it('should change displayed metric when selector changes', async () => {
      const user = userEvent.setup();
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'violations');

      // Should now show violation counts
      expect(screen.getByText('12')).toBeInTheDocument(); // greedy
      expect(screen.getByText('2')).toBeInTheDocument(); // cp_sat
      expect(screen.getByText('5')).toBeInTheDocument(); // pulp
      expect(screen.getByText('1')).toBeInTheDocument(); // hybrid
    });

    it('should update best performer when metric changes', async () => {
      const user = userEvent.setup();
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox');

      // For violations (lower is better), hybrid with 1 should be best
      await user.selectOptions(select, 'violations');
      const hybridViolations = screen.getByText('1');
      expect(hybridViolations.textContent).toContain('★');

      // For runtime (lower is better), greedy with 2.5s should be best
      await user.selectOptions(select, 'runtime');
      const greedyRuntime = screen.getByText('2.5s');
      expect(greedyRuntime.textContent).toContain('★');
    });

    it('should display correct units for each metric', async () => {
      const user = userEvent.setup();
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox');

      // Coverage: percentage
      await user.selectOptions(select, 'coverage');
      expect(screen.getByText('97.5%')).toBeInTheDocument();

      // Violations: no unit
      await user.selectOptions(select, 'violations');
      expect(screen.getByText('1')).toBeInTheDocument();

      // Runtime: seconds
      await user.selectOptions(select, 'runtime');
      expect(screen.getByText('2.5s')).toBeInTheDocument();

      // Fairness: percentage
      await user.selectOptions(select, 'fairness');
      expect(screen.getByText('91.5%')).toBeInTheDocument();
    });
  });

  describe('Legend', () => {
    it('should display legend with all algorithms', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const legends = screen.getAllByText('Greedy');
      expect(legends.length).toBeGreaterThan(0);
    });

    it('should display higher/lower is better indicator', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      // Coverage: higher is better
      expect(screen.getByText('Higher is better')).toBeInTheDocument();
    });

    it('should update better indicator when metric changes', async () => {
      const user = userEvent.setup();
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox');

      // Violations: lower is better
      await user.selectOptions(select, 'violations');
      expect(screen.getByText('Lower is better')).toBeInTheDocument();

      // Coverage: higher is better
      await user.selectOptions(select, 'coverage');
      expect(screen.getByText('Higher is better')).toBeInTheDocument();
    });
  });

  describe('Hover Interactions', () => {
    it('should highlight bar on hover', async () => {
      const user = userEvent.setup();
      const { container } = render(<AlgorithmComparisonChart {...defaultProps} />);

      // Find a bar element by looking for algorithm-specific containers
      const bars = container.querySelectorAll('.flex-1');
      const firstBar = bars[0] as HTMLElement;

      await user.hover(firstBar);

      // The bar should have higher opacity when hovered
      const barElement = firstBar.querySelector('[class*="bg-"]');
      expect(barElement?.className).toContain('opacity');
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no data', () => {
      render(<AlgorithmComparisonChart data={[]} />);

      expect(screen.getByText('No algorithm data available')).toBeInTheDocument();
      expect(
        screen.getByText('Run experiments to compare algorithms')
      ).toBeInTheDocument();
    });

    it('should not display chart elements when no data', () => {
      render(<AlgorithmComparisonChart data={[]} />);

      expect(screen.queryByText('Greedy')).not.toBeInTheDocument();
      expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    });
  });

  describe('Custom Props', () => {
    it('should respect custom metric prop', () => {
      render(<AlgorithmComparisonChart {...defaultProps} metric="violations" />);

      const select = screen.getByRole('combobox') as HTMLSelectElement;
      expect(select.value).toBe('violations');

      // Should display violation counts
      expect(screen.getByText('12')).toBeInTheDocument();
    });

    it('should respect custom height prop', () => {
      const { container } = render(
        <AlgorithmComparisonChart {...defaultProps} height={300} />
      );

      const chartContainer = container.querySelector('.relative');
      expect(chartContainer).toHaveStyle({ height: '220px' }); // 300 - 80 = 220
    });
  });

  describe('Data Calculations', () => {
    it('should correctly identify best performer for higher-is-better metrics', () => {
      render(<AlgorithmComparisonChart {...defaultProps} metric="coverage" />);

      // Hybrid has 97.5% coverage (highest)
      const hybridValue = screen.getByText('97.5%');
      expect(hybridValue.textContent).toContain('★');
    });

    it('should correctly identify best performer for lower-is-better metrics', () => {
      render(<AlgorithmComparisonChart {...defaultProps} metric="violations" />);

      // Hybrid has 1 violation (lowest)
      const hybridValue = screen.getByText('1');
      expect(hybridValue.textContent).toContain('★');
    });

    it('should handle bar height calculations', () => {
      const { container } = render(<AlgorithmComparisonChart {...defaultProps} />);

      // Bars should have heights proportional to their values
      const bars = container.querySelectorAll('[class*="bg-"]');
      bars.forEach((bar) => {
        const style = (bar as HTMLElement).style;
        expect(style.height).toBeTruthy();
      });
    });

    it('should set minimum bar height', () => {
      const customData: AlgorithmMetrics[] = [
        {
          algorithm: 'greedy',
          coverage: 0.1,
          violations: 0,
          fairness: 0,
          runtime: 0,
          stability: 0,
          runCount: 1,
        },
        {
          algorithm: 'cp_sat',
          coverage: 100,
          violations: 0,
          fairness: 0,
          runtime: 0,
          stability: 0,
          runCount: 1,
        },
      ];

      const { container } = render(<AlgorithmComparisonChart data={customData} />);

      const bars = container.querySelectorAll('[style*="height"]');
      bars.forEach((bar) => {
        const height = (bar as HTMLElement).style.height;
        expect(height).toBeTruthy();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have accessible metric selector', () => {
      render(<AlgorithmComparisonChart {...defaultProps} />);

      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
      expect(select).toHaveAccessibleName();
    });

    it('should have semantic HTML structure', () => {
      const { container } = render(<AlgorithmComparisonChart {...defaultProps} />);

      expect(container.querySelector('h3')).toBeInTheDocument();
      expect(container.querySelector('select')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle single algorithm data', () => {
      const singleData: AlgorithmMetrics[] = [MOCK_ALGORITHM_DATA[0]];

      render(<AlgorithmComparisonChart data={singleData} />);

      expect(screen.getByText('Greedy')).toBeInTheDocument();
      expect(screen.getByText('89.5%')).toBeInTheDocument();
    });

    it('should handle zero values gracefully', () => {
      const zeroData: AlgorithmMetrics[] = [
        {
          algorithm: 'greedy',
          coverage: 0,
          violations: 0,
          fairness: 0,
          runtime: 0,
          stability: 0,
          runCount: 1,
        },
      ];

      render(<AlgorithmComparisonChart data={zeroData} />);

      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });

    it('should handle very large values', () => {
      const largeData: AlgorithmMetrics[] = [
        {
          algorithm: 'greedy',
          coverage: 100,
          violations: 1000,
          fairness: 100,
          runtime: 9999,
          stability: 100,
          runCount: 999999,
        },
      ];

      render(<AlgorithmComparisonChart data={largeData} />);

      expect(screen.getByText('100.0%')).toBeInTheDocument();
      expect(screen.getByText('999999 runs')).toBeInTheDocument();
    });

    it('should handle decimal precision', () => {
      const decimalData: AlgorithmMetrics[] = [
        {
          algorithm: 'greedy',
          coverage: 89.567,
          violations: 0,
          fairness: 72.345,
          runtime: 2.567,
          stability: 78.234,
          runCount: 1,
        },
      ];

      render(<AlgorithmComparisonChart data={decimalData} />);

      // Should round to 1 decimal place
      expect(screen.getByText('89.6%')).toBeInTheDocument();
    });

    it('should handle equal values (no clear winner)', () => {
      const equalData: AlgorithmMetrics[] = [
        {
          algorithm: 'greedy',
          coverage: 90,
          violations: 0,
          fairness: 0,
          runtime: 0,
          stability: 0,
          runCount: 1,
        },
        {
          algorithm: 'cp_sat',
          coverage: 90,
          violations: 0,
          fairness: 0,
          runtime: 0,
          stability: 0,
          runCount: 1,
        },
      ];

      render(<AlgorithmComparisonChart data={equalData} />);

      // Both should show 90.0%, first one gets the star
      const values = screen.getAllByText('90.0%');
      expect(values.length).toBe(2);
    });
  });

  describe('Responsive Behavior', () => {
    it('should render with custom height', () => {
      const { container } = render(
        <AlgorithmComparisonChart {...defaultProps} height={400} />
      );

      const chartArea = container.querySelector('.relative');
      expect(chartArea).toHaveStyle({ height: '320px' }); // 400 - 80
    });

    it('should maintain aspect ratio', () => {
      const { container } = render(<AlgorithmComparisonChart {...defaultProps} />);

      const chartContainer = container.querySelector('.bg-slate-800\\/50');
      expect(chartContainer).toBeInTheDocument();
    });
  });

  describe('Color Coding', () => {
    it('should use consistent colors for each algorithm', () => {
      const { container } = render(<AlgorithmComparisonChart {...defaultProps} />);

      // Each algorithm should have its specific color class
      expect(container.querySelector('.bg-orange-500')).toBeInTheDocument(); // greedy
      expect(container.querySelector('.bg-blue-500')).toBeInTheDocument(); // cp_sat
      expect(container.querySelector('.bg-green-500')).toBeInTheDocument(); // pulp
      expect(container.querySelector('.bg-violet-500')).toBeInTheDocument(); // hybrid
    });
  });
});
