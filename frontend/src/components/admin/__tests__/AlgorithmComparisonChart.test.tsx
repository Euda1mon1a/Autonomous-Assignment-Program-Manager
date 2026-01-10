/**
 * Tests for AlgorithmComparisonChart Component
 * Component: admin/AlgorithmComparisonChart - Chart comparing scheduling algorithms
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
      algorithm: 'cpSat',
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
      expect(container.querySelector('canvas, svg')).toBeInTheDocument();
    });

    it('renders title', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/algorithm comparison/i)).toBeInTheDocument();
    });

    it('displays all algorithms', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/greedy/i)).toBeInTheDocument();
      expect(screen.getByText(/cp-sat/i)).toBeInTheDocument();
      expect(screen.getByText(/hybrid/i)).toBeInTheDocument();
    });

    it('shows coverage rate metric', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/coverage/i)).toBeInTheDocument();
    });

    it('shows violation count metric', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/violations/i)).toBeInTheDocument();
    });

    it('shows execution time metric', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/runtime/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('handles empty data array', () => {
      render(<AlgorithmComparisonChart data={[]} />);
      expect(screen.getByText(/no data available/i)).toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    it('formats coverage rate as percentage', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/98%/)).toBeInTheDocument();
    });

    it('displays violation counts', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  describe('Legend', () => {
    it('renders chart legend', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      const { container } = render(<AlgorithmComparisonChart data={mockData} />);
      expect(container.querySelector('[class*="legend"]')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles single algorithm', () => {
      const singleData = [mockData[0]];
      render(<AlgorithmComparisonChart data={singleData} />);
      expect(screen.getByText(/greedy/i)).toBeInTheDocument();
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
      expect(screen.getByText(/100%/)).toBeInTheDocument();
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
      expect(screen.getByText('15')).toBeInTheDocument();
    });
  });
});
