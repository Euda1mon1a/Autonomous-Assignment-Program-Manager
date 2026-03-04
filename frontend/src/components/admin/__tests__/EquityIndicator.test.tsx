/**
 * EquityIndicator Component Tests
 *
 * Tests for the Gini coefficient / workload equity indicator.
 * This component uses the useEquityMetrics hook which must be mocked.
 */
import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { EquityIndicator } from '../EquityIndicator';

// ============================================================================
// Mocks
// ============================================================================

const mockUseEquityMetrics = jest.fn();
const mockGetGiniColorClass = jest.fn();
const mockGetGiniLabel = jest.fn();

jest.mock('@/hooks/useEquityMetrics', () => ({
  useEquityMetrics: (...args: unknown[]) => mockUseEquityMetrics(...args),
  getGiniColorClass: (...args: unknown[]) => mockGetGiniColorClass(...args),
  getGiniLabel: (...args: unknown[]) => mockGetGiniLabel(...args),
}));

// ============================================================================
// Test Data
// ============================================================================

const equitableResponse = {
  giniCoefficient: 0.1,
  isEquitable: true,
  meanWorkload: 40,
  stdWorkload: 2,
  mostOverloadedProvider: null,
  mostUnderloadedProvider: null,
  maxWorkload: 42,
  minWorkload: 38,
  recommendations: [],
  interpretation: 'Workload is equitable',
};

const inequitableResponse = {
  giniCoefficient: 0.35,
  isEquitable: false,
  meanWorkload: 40,
  stdWorkload: 12,
  mostOverloadedProvider: 'provider-a',
  mostUnderloadedProvider: 'provider-b',
  maxWorkload: 60,
  minWorkload: 20,
  recommendations: ['Rebalance workload between providers', 'Reduce hours for provider-a'],
  interpretation: 'High inequality detected',
};

// ============================================================================
// Tests
// ============================================================================

describe('EquityIndicator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetGiniColorClass.mockReturnValue('text-green-500');
    mockGetGiniLabel.mockReturnValue('Equitable');
  });

  describe('Loading State', () => {
    it('shows loading indicator while equity metrics load', () => {
      mockUseEquityMetrics.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      render(
        <EquityIndicator currentProviderHours={{ 'p1': 40, 'p2': 42 }} />
      );

      expect(screen.getByText('Calculating equity...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows unavailable message on error', () => {
      mockUseEquityMetrics.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed'),
      });

      render(
        <EquityIndicator currentProviderHours={{ 'p1': 40 }} />
      );

      expect(screen.getByText('Equity data unavailable')).toBeInTheDocument();
    });

    it('shows unavailable message when data is null', () => {
      mockUseEquityMetrics.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      });

      render(
        <EquityIndicator currentProviderHours={{ 'p1': 40 }} />
      );

      expect(screen.getByText('Equity data unavailable')).toBeInTheDocument();
    });
  });

  describe('Full Mode', () => {
    it('displays current Gini coefficient', () => {
      mockUseEquityMetrics
        .mockReturnValueOnce({
          data: equitableResponse,
          isLoading: false,
          error: null,
        })
        .mockReturnValueOnce({
          data: undefined,
          isLoading: false,
          error: null,
        });

      render(
        <EquityIndicator currentProviderHours={{ 'p1': 40, 'p2': 42 }} />
      );

      expect(screen.getByText('Current Equity:')).toBeInTheDocument();
      expect(screen.getByText(/Gini: 0.100/)).toBeInTheDocument();
    });

    it('displays Gini label from helper', () => {
      mockGetGiniLabel.mockReturnValue('Equitable');
      mockUseEquityMetrics
        .mockReturnValueOnce({
          data: equitableResponse,
          isLoading: false,
          error: null,
        })
        .mockReturnValueOnce({
          data: undefined,
          isLoading: false,
          error: null,
        });

      render(
        <EquityIndicator currentProviderHours={{ 'p1': 40, 'p2': 42 }} />
      );

      expect(screen.getByText('Equitable')).toBeInTheDocument();
    });

    it('displays recommendations when present', () => {
      mockUseEquityMetrics
        .mockReturnValueOnce({
          data: inequitableResponse,
          isLoading: false,
          error: null,
        })
        .mockReturnValueOnce({
          data: undefined,
          isLoading: false,
          error: null,
        });

      render(
        <EquityIndicator currentProviderHours={{ 'p1': 60, 'p2': 20 }} />
      );

      expect(screen.getByText('Recommendations:')).toBeInTheDocument();
      expect(screen.getByText('Rebalance workload between providers')).toBeInTheDocument();
      expect(screen.getByText('Reduce hours for provider-a')).toBeInTheDocument();
    });

    it('displays projected equity when provided', () => {
      const projectedResponse = {
        ...equitableResponse,
        giniCoefficient: 0.05,
      };

      mockUseEquityMetrics
        .mockReturnValueOnce({
          data: equitableResponse,
          isLoading: false,
          error: null,
        })
        .mockReturnValueOnce({
          data: projectedResponse,
          isLoading: false,
          error: null,
        });

      render(
        <EquityIndicator
          currentProviderHours={{ 'p1': 40, 'p2': 42 }}
          projectedProviderHours={{ 'p1': 41, 'p2': 41 }}
        />
      );

      expect(screen.getByText('After Changes:')).toBeInTheDocument();
      expect(screen.getByText(/Gini: 0.050/)).toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('renders compact layout with Gini label', () => {
      mockUseEquityMetrics
        .mockReturnValueOnce({
          data: equitableResponse,
          isLoading: false,
          error: null,
        })
        .mockReturnValueOnce({
          data: undefined,
          isLoading: false,
          error: null,
        });

      render(
        <EquityIndicator
          currentProviderHours={{ 'p1': 40, 'p2': 42 }}
          compact
        />
      );

      expect(screen.getByText('Gini:')).toBeInTheDocument();
      expect(screen.getByText('0.100')).toBeInTheDocument();
    });

    it('does not show recommendations in compact mode', () => {
      mockUseEquityMetrics
        .mockReturnValueOnce({
          data: inequitableResponse,
          isLoading: false,
          error: null,
        })
        .mockReturnValueOnce({
          data: undefined,
          isLoading: false,
          error: null,
        });

      render(
        <EquityIndicator
          currentProviderHours={{ 'p1': 60, 'p2': 20 }}
          compact
        />
      );

      expect(screen.queryByText('Recommendations:')).not.toBeInTheDocument();
    });
  });
});
