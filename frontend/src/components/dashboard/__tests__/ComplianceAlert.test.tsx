/**
 * Tests for ComplianceAlert Component
 * Component: dashboard/ComplianceAlert - Compliance violation alert panel
 *
 * The component takes no props. It internally calls useValidateSchedule
 * for the current month and displays the compliance status.
 */

import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { ComplianceAlert } from '../ComplianceAlert';

// ============================================================================
// Mocks
// ============================================================================

const mockUseValidateSchedule = jest.fn();

jest.mock('@/lib/hooks', () => ({
  useValidateSchedule: (...args: unknown[]) => mockUseValidateSchedule(...args),
}));

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...rest}>{children}</a>
  );
});

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { initial, animate, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

// ============================================================================
// Tests
// ============================================================================

beforeEach(() => {
  jest.clearAllMocks();
});

describe('ComplianceAlert', () => {
  describe('Loading state', () => {
    it('shows loading indicator when data is loading', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByLabelText(/loading compliance data/i)).toBeInTheDocument();
    });
  });

  describe('Error state', () => {
    it('shows error message when request fails', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText(/unable to load compliance data/i)).toBeInTheDocument();
    });
  });

  describe('No data state', () => {
    it('shows empty state when no validation data exists', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText(/no compliance data/i)).toBeInTheDocument();
      expect(screen.getByText(/generate a schedule/i)).toBeInTheDocument();
    });

    it('shows empty state when valid is undefined', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: { valid: undefined, totalViolations: 0, violations: [] },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText(/no compliance data/i)).toBeInTheDocument();
    });
  });

  describe('Clean state (no violations)', () => {
    it('shows all clear when schedule is valid', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: true,
          totalViolations: 0,
          violations: [],
          coverageRate: 1.0,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText(/all clear/i)).toBeInTheDocument();
      expect(screen.getByText(/no acgme violations/i)).toBeInTheDocument();
    });
  });

  describe('Violations state', () => {
    it('shows violation count when violations exist', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: false,
          totalViolations: 3,
          violations: [
            { type: '80-hour', severity: 'critical', message: 'Exceeded 80-hour work week', personId: null, personName: null, blockId: null, details: null },
            { type: '1-in-7', severity: 'error', message: 'Missing required day off', personId: null, personName: null, blockId: null, details: null },
            { type: 'supervision', severity: 'warning', message: 'Supervision ratio exceeded', personId: null, personName: null, blockId: null, details: null },
          ],
          coverageRate: 0.85,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText(/violations found/i)).toBeInTheDocument();
    });

    it('shows singular form for single violation', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: false,
          totalViolations: 1,
          violations: [
            { type: '80-hour', severity: 'critical', message: 'Exceeded 80-hour work week', personId: null, personName: null, blockId: null, details: null },
          ],
          coverageRate: 0.95,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText(/violation found/i)).toBeInTheDocument();
      // Should NOT have plural "Violations"
      expect(screen.queryByText(/violations found/i)).not.toBeInTheDocument();
    });

    it('shows top 2 violation messages', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: false,
          totalViolations: 3,
          violations: [
            { type: '80-hour', severity: 'critical', message: 'Exceeded 80-hour work week', personId: null, personName: null, blockId: null, details: null },
            { type: '1-in-7', severity: 'error', message: 'Missing required day off', personId: null, personName: null, blockId: null, details: null },
            { type: 'supervision', severity: 'warning', message: 'Supervision ratio exceeded', personId: null, personName: null, blockId: null, details: null },
          ],
          coverageRate: 0.85,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText('Exceeded 80-hour work week')).toBeInTheDocument();
      expect(screen.getByText('Missing required day off')).toBeInTheDocument();
      // Third violation should not be shown inline
      expect(screen.queryByText('Supervision ratio exceeded')).not.toBeInTheDocument();
      // "+1 more" indicator
      expect(screen.getByText(/\+1 more/)).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('has a link to compliance details page', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: true,
          totalViolations: 0,
          violations: [],
          coverageRate: 1.0,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      const link = screen.getByRole('link', { name: /view detailed compliance report/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/compliance');
    });
  });

  describe('Accessibility', () => {
    it('has compliance status heading', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: true,
          totalViolations: 0,
          violations: [],
          coverageRate: 1.0,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByText('Compliance Status')).toBeInTheDocument();
    });

    it('has region role with label', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: true,
          totalViolations: 0,
          violations: [],
          coverageRate: 1.0,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByRole('region', { name: /compliance status/i })).toBeInTheDocument();
    });

    it('has alert role when violations exist', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: {
          valid: false,
          totalViolations: 2,
          violations: [
            { type: '80-hour', severity: 'critical', message: 'Exceeded 80-hour work week', personId: null, personName: null, blockId: null, details: null },
            { type: '1-in-7', severity: 'error', message: 'Missing required day off', personId: null, personName: null, blockId: null, details: null },
          ],
          coverageRate: 0.9,
          statistics: null,
        },
        isLoading: false,
        isError: false,
      });

      render(<ComplianceAlert />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('has error alert role when request fails', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
      });

      render(<ComplianceAlert />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Hook integration', () => {
    it('passes current month date range to useValidateSchedule', () => {
      mockUseValidateSchedule.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      });

      render(<ComplianceAlert />);

      expect(mockUseValidateSchedule).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/)
      );
    });
  });
});
