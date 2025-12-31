/**
 * Tests for AlgorithmComparisonChart Component
 * Component: admin/AlgorithmComparisonChart - Chart comparing scheduling algorithms
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { AlgorithmComparisonChart } from '../AlgorithmComparisonChart';

describe('AlgorithmComparisonChart', () => {
  const mockData = [
    {
      algorithm: 'Greedy',
      coverageRate: 95,
      avgHoursPerWeek: 65,
      violationCount: 2,
      executionTime: 1.2,
    },
    {
      algorithm: 'OR-Tools',
      coverageRate: 98,
      avgHoursPerWeek: 68,
      violationCount: 0,
      executionTime: 5.8,
    },
    {
      algorithm: 'Genetic',
      coverageRate: 96,
      avgHoursPerWeek: 66,
      violationCount: 1,
      executionTime: 12.4,
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
      expect(screen.getByText(/or-tools/i)).toBeInTheDocument();
      expect(screen.getByText(/genetic/i)).toBeInTheDocument();
    });

    it('shows coverage rate metric', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/coverage rate/i)).toBeInTheDocument();
    });

    it('shows violation count metric', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/violations/i)).toBeInTheDocument();
    });

    it('shows execution time metric', () => {
      render(<AlgorithmComparisonChart data={mockData} />);
      expect(screen.getByText(/execution time/i)).toBeInTheDocument();
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
      const perfectData = [
        {
          algorithm: 'Perfect',
          coverageRate: 100,
          avgHoursPerWeek: 60,
          violationCount: 0,
          executionTime: 1.0,
        },
      ];
      render(<AlgorithmComparisonChart data={perfectData} />);
      expect(screen.getByText(/100%/)).toBeInTheDocument();
    });

    it('handles algorithms with high violations', () => {
      const highViolationData = [
        {
          algorithm: 'Poor',
          coverageRate: 75,
          avgHoursPerWeek: 70,
          violationCount: 15,
          executionTime: 2.0,
        },
      ];
      render(<AlgorithmComparisonChart data={highViolationData} />);
      expect(screen.getByText('15')).toBeInTheDocument();
    });
  });
});
