/**
 * PhaseTransitionBanner Component Tests
 *
 * Tests for the phase transition warning banner including:
 * - Rendering for different severity levels
 * - Expand/collapse details
 * - Dismiss behavior
 * - Hidden states (normal, loading, error)
 * - Action required notice
 */
import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { PhaseTransitionBanner } from '../PhaseTransitionBanner';
import type { PhaseTransitionResponse, CriticalSignal } from '@/hooks/usePhaseTransitionRisk';

// ============================================================================
// Mocks
// ============================================================================

const mockUsePhaseTransitionRisk = jest.fn();

jest.mock('@/hooks/usePhaseTransitionRisk', () => ({
  usePhaseTransitionRisk: (...args: unknown[]) => mockUsePhaseTransitionRisk(...args),
  getSeverityColorClass: (severity: string) => {
    const map: Record<string, string> = {
      normal: 'text-green-500',
      elevated: 'text-yellow-500',
      high: 'text-orange-500',
      critical: 'text-red-500',
      imminent: 'text-red-700',
    };
    return map[severity] || 'text-slate-500';
  },
  getSeverityBgClass: (severity: string) => {
    const map: Record<string, string> = {
      normal: 'bg-green-500/20',
      elevated: 'bg-yellow-500/20',
      high: 'bg-orange-500/20',
      critical: 'bg-red-500/20',
      imminent: 'bg-red-700/20',
    };
    return map[severity] || 'bg-slate-500/20';
  },
  requiresAction: (severity: string) => {
    return ['high', 'critical', 'imminent'].includes(severity);
  },
}));

// ============================================================================
// Test Data
// ============================================================================

function makeSignal(overrides?: Partial<CriticalSignal>): CriticalSignal {
  return {
    signal_type: 'variance_increase',
    metric_name: 'workload_variance',
    severity: 'elevated',
    value: 2.5,
    threshold: 2.0,
    description: 'Workload variance exceeds threshold',
    detectedAt: '2024-06-15T10:00:00Z',
    ...overrides,
  };
}

function makeResponse(
  overrides?: Partial<PhaseTransitionResponse>
): PhaseTransitionResponse {
  return {
    overallSeverity: 'elevated',
    signals: [makeSignal()],
    time_to_transition: 48,
    confidence: 0.75,
    recommendations: ['Review current workload distribution'],
    source: 'test',
    ...overrides,
  };
}

// ============================================================================
// Tests
// ============================================================================

describe('PhaseTransitionBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Hidden States', () => {
    it('returns null when loading', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      const { container } = render(<PhaseTransitionBanner />);

      expect(container.firstChild).toBeNull();
    });

    it('returns null on error', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('API error'),
      });

      const { container } = render(<PhaseTransitionBanner />);

      expect(container.firstChild).toBeNull();
    });

    it('returns null when data is null', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      });

      const { container } = render(<PhaseTransitionBanner />);

      expect(container.firstChild).toBeNull();
    });

    it('returns null when severity is normal and hideIfNormal is true', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'normal' }),
        isLoading: false,
        error: null,
      });

      const { container } = render(<PhaseTransitionBanner />);

      expect(container.firstChild).toBeNull();
    });

    it('renders when severity is normal and hideIfNormal is false', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'normal' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner hideIfNormal={false} />);

      expect(screen.getByText('System Stable')).toBeInTheDocument();
    });
  });

  describe('Severity Levels', () => {
    it('renders Elevated Risk for elevated severity', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'elevated' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(screen.getByText('Elevated Risk')).toBeInTheDocument();
    });

    it('renders High Risk heading for high severity', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'high' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(
        screen.getByText('High Risk - Phase Transition Warning')
      ).toBeInTheDocument();
    });

    it('renders CRITICAL heading for critical severity', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'critical' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(
        screen.getByText('CRITICAL - Phase Transition Imminent')
      ).toBeInTheDocument();
    });

    it('renders confidence percentage', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ confidence: 0.85 }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
    });

    it('renders signal count', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({
          signals: [makeSignal(), makeSignal({ signal_type: 'flickering' })],
        }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(
        screen.getByText(/2 early warning signals detected/)
      ).toBeInTheDocument();
    });

    it('renders singular signal text for 1 signal', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({
          signals: [makeSignal()],
        }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(
        screen.getByText(/1 early warning signal detected/)
      ).toBeInTheDocument();
    });

    it('renders time to transition', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ time_to_transition: 24 }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(screen.getByText(/~24h until transition/)).toBeInTheDocument();
    });
  });

  describe('Expand/Collapse', () => {
    it('expands to show signal details', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse(),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      // Click expand button
      fireEvent.click(screen.getByTitle('Expand details'));

      expect(screen.getByText('Detected Signals:')).toBeInTheDocument();
      expect(screen.getByText('variance_increase:')).toBeInTheDocument();
      expect(
        screen.getByText('Workload variance exceeds threshold')
      ).toBeInTheDocument();
    });

    it('shows signal value and threshold in expanded view', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse(),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      fireEvent.click(screen.getByTitle('Expand details'));

      expect(screen.getByText('2.50 / 2.00')).toBeInTheDocument();
    });

    it('shows recommendations in expanded view', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({
          recommendations: ['Reduce workload', 'Add coverage'],
        }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      fireEvent.click(screen.getByTitle('Expand details'));

      expect(screen.getByText('Recommended Actions:')).toBeInTheDocument();
      expect(screen.getByText('Reduce workload')).toBeInTheDocument();
      expect(screen.getByText('Add coverage')).toBeInTheDocument();
    });

    it('collapses when clicked again', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse(),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      fireEvent.click(screen.getByTitle('Expand details'));
      expect(screen.getByText('Detected Signals:')).toBeInTheDocument();

      fireEvent.click(screen.getByTitle('Collapse details'));
      expect(screen.queryByText('Detected Signals:')).not.toBeInTheDocument();
    });
  });

  describe('Dismiss', () => {
    it('shows dismiss button when action is not required', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'elevated' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(screen.getByTitle('Dismiss')).toBeInTheDocument();
    });

    it('does not show dismiss button when action required (high/critical/imminent)', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'high' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(screen.queryByTitle('Dismiss')).not.toBeInTheDocument();
    });

    it('hides banner when dismissed', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'elevated' }),
        isLoading: false,
        error: null,
      });

      const { container } = render(<PhaseTransitionBanner />);

      expect(screen.getByText('Elevated Risk')).toBeInTheDocument();

      fireEvent.click(screen.getByTitle('Dismiss'));

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Action Required', () => {
    it('shows action required notice when expanded and severity is high or above', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'critical' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      fireEvent.click(screen.getByTitle('Expand details'));

      expect(
        screen.getByText(/Immediate action required to prevent system failure/)
      ).toBeInTheDocument();
    });

    it('does not show action required notice for elevated severity', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ overallSeverity: 'elevated' }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      fireEvent.click(screen.getByTitle('Expand details'));

      expect(
        screen.queryByText(/Immediate action required/)
      ).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero signals gracefully', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({
          overallSeverity: 'elevated',
          signals: [],
        }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(
        screen.getByText(/0 early warning signals detected/)
      ).toBeInTheDocument();
      // No expand button when no signals
      expect(screen.queryByTitle('Expand details')).not.toBeInTheDocument();
    });

    it('handles null time_to_transition', () => {
      mockUsePhaseTransitionRisk.mockReturnValue({
        data: makeResponse({ time_to_transition: null }),
        isLoading: false,
        error: null,
      });

      render(<PhaseTransitionBanner />);

      expect(screen.queryByText(/until transition/)).not.toBeInTheDocument();
    });
  });
});
