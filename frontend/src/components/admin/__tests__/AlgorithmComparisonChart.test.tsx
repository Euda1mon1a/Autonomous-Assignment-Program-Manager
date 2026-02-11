/**
 * Tests for AlgorithmComparisonChart Component
 * Component: admin/AlgorithmComparisonChart - Chart comparing scheduling algorithms
 *
 * The component renders CSS/div-based bars (no canvas/svg).
 * Default metric is 'coverage'. Algorithm labels: Greedy, CP-SAT, PuLP, Hybrid.
 * Values formatted by METRIC_CONFIG (e.g., "98.0%").
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { AlgorithmComparisonChart, type AlgorithmMetrics } from '../AlgorithmComparisonChart';

describe('AlgorithmComparisonChart', () => {
  const mockData: AlgorithmMetrics[] = [
    {
      algorithm: 'greedy',
      coverage: 95,
      violations: 2,
      fairness: 85,
      runtime: 1.2,
      stability: 88,
      runCount: 10,
    },
    {
      algorithm: 'cp_sat',
      coverage: 98,
      violations: 0,
      fairness: 92,
      runtime: 5.8,
      stability: 95,
      runCount: 15,
    },
    {
      algorithm: 'hybrid',
      coverage: 96,
      violations: 1,
      fairness: 89,
      runtime: 12.4,
      stability: 90,
      runCount: 12,
    },
  ];

  describe('Rendering', () => {
    it('renders chart container', () => {
      const { container } = render(<AlgorithmComparisonChart data={mockData} />);
      // Component uses divs for bars (no canvas/svg)
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders title', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText('Algorithm Comparison')).toBeInTheDocument();
    });

    it('displays all algorithms', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      // ALGORITHM_LABELS maps: greedy -> Greedy, cp_sat -> CP-SAT, hybrid -> Hybrid
      expect(screen.getAllByText('Greedy').length).toBeGreaterThan(0);
      expect(screen.getAllByText('CP-SAT').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Hybrid').length).toBeGreaterThan(0);
    });

    it('shows coverage metric option', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      // Coverage is in the metric selector
      expect(screen.getByText('Coverage')).toBeInTheDocument();
    });

    it('shows violation count metric option', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      // "ACGME Violations" is the label in METRIC_CONFIG
      expect(screen.getByText('ACGME Violations')).toBeInTheDocument();
    });

    it('shows runtime metric option', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText('Runtime')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('handles empty data array', () => {
      render(<AlgorithmComparisonChart data={[]} />);
      expect(screen.getByText(/no algorithm data available/i)).toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    it('formats coverage rate as percentage', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      // METRIC_CONFIG.coverage.format = v => `${v.toFixed(1)}%` -> "98.0%"
      expect(screen.getByText('98.0%')).toBeInTheDocument();
    });

    it('shows run counts per algorithm', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText('10 runs')).toBeInTheDocument();
      expect(screen.getByText('15 runs')).toBeInTheDocument();
      expect(screen.getByText('12 runs')).toBeInTheDocument();
    });

    it('shows total run count', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      // Header: "Based on 37 runs"
      expect(screen.getByText(/37 runs/)).toBeInTheDocument();
    });
  });

  describe('Legend', () => {
    it('renders algorithm color indicators', () => {
      const { container } = render(<AlgorithmComparisonChart data={mockData} />);
      // Each algorithm has a color swatch (w-3 h-3 rounded)
      const swatches = container.querySelectorAll('.w-3.h-3.rounded');
      expect(swatches.length).toBe(mockData.length);
    });

    it('shows higher/lower is better indicator', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      // Default metric is coverage (higherIsBetter: true)
      expect(screen.getByText('Higher is better')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles single algorithm', () => {
      const singleData = [mockData[0]];
      render(<AlgorithmComparisonChart data={singleData} />);
      expect(screen.getAllByText('Greedy').length).toBeGreaterThan(0);
    });

    it('handles perfect scores', () => {
      const perfectData: AlgorithmMetrics[] = [
        {
          algorithm: 'hybrid',
          coverage: 100,
          violations: 0,
          fairness: 100,
          runtime: 1.0,
          stability: 100,
          runCount: 5,
        },
      ];
      render(<AlgorithmComparisonChart data={perfectData} />);
      expect(screen.getByText('100.0%')).toBeInTheDocument();
    });

    it('handles algorithms with high violations', () => {
      const highViolationData: AlgorithmMetrics[] = [
        {
          algorithm: 'greedy',
          coverage: 75,
          violations: 15,
          fairness: 60,
          runtime: 2.0,
          stability: 70,
          runCount: 3,
        },
      ];
      render(<AlgorithmComparisonChart data={highViolationData} />);
      // Default metric is coverage, so shows "75.0%"
      expect(screen.getByText('75.0%')).toBeInTheDocument();
    });
  });
});
