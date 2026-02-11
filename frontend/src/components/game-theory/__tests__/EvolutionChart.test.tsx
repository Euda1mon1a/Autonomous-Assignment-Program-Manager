/**
 * Tests for EvolutionChart Component
 * Component: game-theory/EvolutionChart - Strategy evolution visualization
 *
 * The component uses useEvolutionResults hook (not a data prop),
 * so we mock the hook to control rendered output.
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { EvolutionChart } from '../EvolutionChart';

// Mock the hook
jest.mock('@/hooks/useGameTheory', () => ({
  useEvolutionResults: jest.fn(),
}));

// Mock LoadingSpinner
jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}));

import { useEvolutionResults } from '@/hooks/useGameTheory';
const mockUseEvolutionResults = useEvolutionResults as jest.Mock;

describe('EvolutionChart', () => {
  const mockResults = {
    id: 'evo-1',
    name: 'Test Evolution',
    status: 'completed' as const,
    completedAt: '2024-01-01T00:00:00Z',
    generationsCompleted: 3,
    winnerStrategyName: 'Cooperative',
    isEvolutionarilyStable: true,
    populationHistory: [
      { generation: 0, populations: { Cooperative: 50, Aggressive: 50 } },
      { generation: 1, populations: { Cooperative: 60, Aggressive: 40 } },
      { generation: 2, populations: { Cooperative: 70, Aggressive: 30 } },
    ],
    finalPopulation: { Cooperative: 70, Aggressive: 30 },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders SVG chart', () => {
      mockUseEvolutionResults.mockReturnValue({ data: mockResults, isLoading: false, error: null });
      const { container } = render(<EvolutionChart evolutionId="evo-1" />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders x-axis label (Generations)', () => {
      mockUseEvolutionResults.mockReturnValue({ data: mockResults, isLoading: false, error: null });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText('Generations')).toBeInTheDocument();
    });

    it('renders y-axis percentage labels', () => {
      mockUseEvolutionResults.mockReturnValue({ data: mockResults, isLoading: false, error: null });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('displays strategy names in legend', () => {
      mockUseEvolutionResults.mockReturnValue({ data: mockResults, isLoading: false, error: null });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText('Cooperative')).toBeInTheDocument();
      expect(screen.getByText('Aggressive')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      mockUseEvolutionResults.mockReturnValue({ data: null, isLoading: true, error: null });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error message on error', () => {
      mockUseEvolutionResults.mockReturnValue({ data: null, isLoading: false, error: new Error('fail') });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText('Failed to load results')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('handles empty population history', () => {
      mockUseEvolutionResults.mockReturnValue({
        data: { ...mockResults, populationHistory: [] },
        isLoading: false,
        error: null,
      });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText('No data')).toBeInTheDocument();
    });

    it('handles null results', () => {
      mockUseEvolutionResults.mockReturnValue({ data: null, isLoading: false, error: null });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText('No data')).toBeInTheDocument();
    });
  });

  describe('Winner Display', () => {
    it('shows winner announcement', () => {
      mockUseEvolutionResults.mockReturnValue({ data: mockResults, isLoading: false, error: null });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText(/Winner:/)).toBeInTheDocument();
      // "Cooperative" appears in both legend and winner - use getAllByText
      expect(screen.getAllByText(/Cooperative/).length).toBeGreaterThanOrEqual(2);
    });

    it('shows evolutionarily stable indicator', () => {
      mockUseEvolutionResults.mockReturnValue({ data: mockResults, isLoading: false, error: null });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.getByText(/Evolutionarily Stable/)).toBeInTheDocument();
    });

    it('does not show winner when none', () => {
      mockUseEvolutionResults.mockReturnValue({
        data: { ...mockResults, winnerStrategyName: null },
        isLoading: false,
        error: null,
      });
      render(<EvolutionChart evolutionId="evo-1" />);
      expect(screen.queryByText(/Winner:/)).not.toBeInTheDocument();
    });
  });

  describe('Legend', () => {
    it('renders color swatches for each strategy', () => {
      mockUseEvolutionResults.mockReturnValue({ data: mockResults, isLoading: false, error: null });
      const { container } = render(<EvolutionChart evolutionId="evo-1" />);
      // Each strategy gets a color swatch div (w-3 h-3 rounded)
      const swatches = container.querySelectorAll('.w-3.h-3.rounded');
      expect(swatches.length).toBe(2); // Cooperative + Aggressive
    });
  });

  describe('Edge Cases', () => {
    it('handles single generation', () => {
      mockUseEvolutionResults.mockReturnValue({
        data: {
          ...mockResults,
          populationHistory: [
            { generation: 0, populations: { Cooperative: 100 } },
          ],
        },
        isLoading: false,
        error: null,
      });
      const { container } = render(<EvolutionChart evolutionId="evo-1" />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('handles many strategies', () => {
      mockUseEvolutionResults.mockReturnValue({
        data: {
          ...mockResults,
          populationHistory: [
            { generation: 0, populations: { A: 25, B: 25, C: 25, D: 25 } },
            { generation: 1, populations: { A: 30, B: 20, C: 30, D: 20 } },
          ],
        },
        isLoading: false,
        error: null,
      });
      render(<EvolutionChart evolutionId="evo-1" />);
      // All 4 strategies should appear in legend
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('B')).toBeInTheDocument();
      expect(screen.getByText('C')).toBeInTheDocument();
      expect(screen.getByText('D')).toBeInTheDocument();
    });
  });
});
