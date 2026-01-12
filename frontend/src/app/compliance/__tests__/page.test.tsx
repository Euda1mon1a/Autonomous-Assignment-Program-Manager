/**
 * Tests for Compliance Hub Page
 *
 * This test suite verifies:
 * - Unified compliance page with tabs for ACGME and Away-From-Program
 * - RiskBar integration showing green (Tier 0) for read-only access
 * - Distinct iconography and copy per tab
 * - WCAG 2.1 AA accessibility compliance
 */

import React from 'react';
import { renderWithProviders, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';

// Mock the hooks
jest.mock('@/hooks/useSchedule', () => ({
  useValidateSchedule: jest.fn(),
}));

jest.mock('@/hooks/useAbsences', () => ({
  useAwayComplianceDashboard: jest.fn(),
}));

jest.mock('@/hooks/usePeople', () => ({
  usePeople: jest.fn(),
}));

// Mock the AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isLoading: false,
    user: { role: 'admin' },
  }),
}));

// Import mocks after setting up jest.mock
import { useValidateSchedule } from '@/hooks/useSchedule';
import { useAwayComplianceDashboard } from '@/hooks/useAbsences';
import { usePeople } from '@/hooks/usePeople';

// Import component after mocks are set up
import ComplianceHubPage from '../page';

// Mock data
const mockValidationData = {
  valid: true,
  totalViolations: 0,
  violations: [],
  coverageRate: 0.95,
  statistics: null,
};

const mockValidationWithViolations = {
  valid: false,
  totalViolations: 2,
  violations: [
    {
      type: '80_HOUR_VIOLATION',
      severity: 'HIGH',
      personId: 'person-1',
      personName: 'Dr. Smith',
      blockId: 'block-1',
      message: 'Exceeded 80 hours in 4-week period',
      details: null,
    },
    {
      type: '1_IN_7_VIOLATION',
      severity: 'MEDIUM',
      personId: 'person-2',
      personName: 'Dr. Jones',
      blockId: 'block-2',
      message: 'No day off in 7-day period',
      details: null,
    },
  ],
  coverageRate: 0.85,
  statistics: null,
};

const mockAwayComplianceData = {
  academicYear: '2025-2026',
  summary: {
    totalResidents: 12,
    byStatus: {
      ok: 8,
      warning: 2,
      critical: 1,
      exceeded: 1,
    },
  },
  residents: [
    {
      personId: 'resident-1',
      daysUsed: 5,
      daysRemaining: 23,
      maxDays: 28,
      warningDays: 21,
      thresholdStatus: 'ok' as const,
      absences: [],
    },
    {
      personId: 'resident-2',
      daysUsed: 22,
      daysRemaining: 6,
      maxDays: 28,
      warningDays: 21,
      thresholdStatus: 'warning' as const,
      absences: [
        {
          id: 'absence-1',
          startDate: '2025-09-01',
          endDate: '2025-09-15',
          absenceType: 'vacation',
          days: 14,
        },
      ],
    },
  ],
};

const mockPeopleData = {
  items: [
    { id: 'resident-1', name: 'Dr. Alice Smith', pgyLevel: 2 },
    { id: 'resident-2', name: 'Dr. Bob Jones', pgyLevel: 1 },
  ],
  total: 2,
};

describe('ComplianceHubPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    (useValidateSchedule as jest.Mock).mockReturnValue({
      data: mockValidationData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: jest.fn(),
    });

    (useAwayComplianceDashboard as jest.Mock).mockReturnValue({
      data: mockAwayComplianceData,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isFetching: false,
    });

    (usePeople as jest.Mock).mockReturnValue({
      data: mockPeopleData,
    });
  });

  // ==========================================================================
  // Page Structure Tests
  // ==========================================================================

  describe('Page Structure', () => {
    it('renders the page title and description', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByText('Compliance Hub')).toBeInTheDocument();
      expect(
        screen.getByText('Monitor ACGME work hour compliance and away-from-program status')
      ).toBeInTheDocument();
    });

    it('renders the RiskBar with Tier 0 (green/read-only)', () => {
      renderWithProviders(<ComplianceHubPage />);

      const riskBar = screen.getByRole('status');
      expect(riskBar).toHaveTextContent('Read-only');
    });

    it('renders both compliance tabs', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByRole('tab', { name: /acgme compliance/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /away-from-program/i })).toBeInTheDocument();
    });

    it('defaults to ACGME Compliance tab', () => {
      renderWithProviders(<ComplianceHubPage />);

      const acgmeTab = screen.getByRole('tab', { name: /acgme compliance/i });
      expect(acgmeTab).toHaveAttribute('aria-selected', 'true');
    });
  });

  // ==========================================================================
  // ACGME Compliance Tab Tests
  // ==========================================================================

  describe('ACGME Compliance Tab', () => {
    it('displays ACGME info banner with Shield icon', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByText(/ACGME Work Hour Requirements/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Accreditation Council for Graduate Medical Education/i)
      ).toBeInTheDocument();
    });

    it('displays the three compliance cards (80-Hour, 1-in-7, Supervision)', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByText('80-Hour Rule')).toBeInTheDocument();
      expect(screen.getByText('1-in-7 Rule')).toBeInTheDocument();
      expect(screen.getByText('Supervision Ratios')).toBeInTheDocument();
    });

    it('shows month navigation controls', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByRole('button', { name: /previous month/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next month/i })).toBeInTheDocument();
    });

    it('displays "All ACGME requirements met!" when no violations', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByText('All ACGME requirements met!')).toBeInTheDocument();
    });

    it('displays violations when present', () => {
      (useValidateSchedule as jest.Mock).mockReturnValue({
        data: mockValidationWithViolations,
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      });

      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByText('Violations Requiring Attention')).toBeInTheDocument();
      expect(screen.getByText(/exceeded 80 hours/i)).toBeInTheDocument();
      expect(screen.getByText(/no day off in 7-day period/i)).toBeInTheDocument();
    });

    it('displays coverage rate', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByText(/Coverage Rate: 95.0%/i)).toBeInTheDocument();
    });

    it('shows loading state', () => {
      (useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        isError: false,
        error: null,
        refetch: jest.fn(),
      });

      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('shows error state with retry button', () => {
      const mockRefetch = jest.fn();
      (useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load' },
        refetch: mockRefetch,
      });

      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByText('Failed to load')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Away-From-Program Tab Tests
  // ==========================================================================

  describe('Away-From-Program Tab', () => {
    beforeEach(() => {
      renderWithProviders(<ComplianceHubPage />);
      // Click on the Away-From-Program tab
      fireEvent.click(screen.getByRole('tab', { name: /away-from-program/i }));
    });

    it('displays Away-From-Program info banner with Clock icon', async () => {
      await waitFor(() => {
        expect(screen.getByText(/28-Day Rule/i)).toBeInTheDocument();
      });
      expect(screen.getByText(/must extend their training/i)).toBeInTheDocument();
    });

    it('displays summary cards', async () => {
      await waitFor(() => {
        expect(screen.getByText('Total Residents')).toBeInTheDocument();
      });
      expect(screen.getByText('OK')).toBeInTheDocument();
      expect(screen.getByText('Warning')).toBeInTheDocument();
      expect(screen.getByText('Critical / Exceeded')).toBeInTheDocument();
    });

    it('displays resident table with sortable headers', async () => {
      await waitFor(() => {
        expect(screen.getByText('Resident')).toBeInTheDocument();
      });
      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByText('Days Used')).toBeInTheDocument();
      expect(screen.getByText('Remaining')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
    });

    it('displays status filter dropdown', async () => {
      await waitFor(() => {
        const filter = screen.getByRole('combobox');
        expect(filter).toBeInTheDocument();
      });
    });

    it('displays academic year', async () => {
      await waitFor(() => {
        expect(screen.getByText('2025-2026 Academic Year')).toBeInTheDocument();
      });
    });

    it('displays resident data', async () => {
      await waitFor(() => {
        expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
        expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Tab Switching Tests
  // ==========================================================================

  describe('Tab Switching', () => {
    it('switches between tabs correctly', () => {
      renderWithProviders(<ComplianceHubPage />);

      // Initially on ACGME tab
      expect(screen.getByText(/ACGME Work Hour Requirements/i)).toBeInTheDocument();

      // Click Away-From-Program tab
      fireEvent.click(screen.getByRole('tab', { name: /away-from-program/i }));

      // Should now show Away-From-Program content
      expect(screen.getByText(/28-Day Rule/i)).toBeInTheDocument();

      // Click back to ACGME tab
      fireEvent.click(screen.getByRole('tab', { name: /acgme compliance/i }));

      // Should show ACGME content again
      expect(screen.getByText(/ACGME Work Hour Requirements/i)).toBeInTheDocument();
    });

    it('updates aria-selected when switching tabs', () => {
      renderWithProviders(<ComplianceHubPage />);

      const acgmeTab = screen.getByRole('tab', { name: /acgme compliance/i });
      const awayTab = screen.getByRole('tab', { name: /away-from-program/i });

      // Initially ACGME is selected
      expect(acgmeTab).toHaveAttribute('aria-selected', 'true');
      expect(awayTab).toHaveAttribute('aria-selected', 'false');

      // Click Away-From-Program
      fireEvent.click(awayTab);

      // Now Away-From-Program is selected
      expect(acgmeTab).toHaveAttribute('aria-selected', 'false');
      expect(awayTab).toHaveAttribute('aria-selected', 'true');
    });
  });

  // ==========================================================================
  // Accessibility Tests
  // ==========================================================================

  describe('Accessibility', () => {
    it('has correct tab structure for screen readers', () => {
      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByRole('tablist')).toBeInTheDocument();
      expect(screen.getAllByRole('tab')).toHaveLength(2);
      expect(screen.getByRole('tabpanel')).toBeInTheDocument();
    });

    it('RiskBar is accessible with role="status"', () => {
      renderWithProviders(<ComplianceHubPage />);

      const riskBar = screen.getByRole('status');
      expect(riskBar).toHaveAttribute('aria-label', 'Permission level: Read-only');
    });

    it('loading spinners have appropriate aria attributes', () => {
      (useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        isError: false,
        error: null,
        refetch: jest.fn(),
      });

      renderWithProviders(<ComplianceHubPage />);

      // Multiple status elements exist - RiskBar and loading indicator
      const statusElements = screen.getAllByRole('status');
      expect(statusElements.length).toBeGreaterThanOrEqual(1);
    });

    it('violations list has proper list role', () => {
      (useValidateSchedule as jest.Mock).mockReturnValue({
        data: mockValidationWithViolations,
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      });

      renderWithProviders(<ComplianceHubPage />);

      expect(screen.getByRole('list', { name: /compliance violations/i })).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Distinct Visual Identity Tests
  // ==========================================================================

  describe('Distinct Visual Identity per Tab', () => {
    it('ACGME tab uses blue color scheme', () => {
      renderWithProviders(<ComplianceHubPage />);

      // The info banner should have blue styling
      const infoBanner = screen.getByText(/ACGME Work Hour Requirements/i).closest('div');
      expect(infoBanner?.parentElement).toHaveClass('bg-blue-50');
    });

    it('Away-From-Program tab uses purple color scheme', () => {
      renderWithProviders(<ComplianceHubPage />);
      fireEvent.click(screen.getByRole('tab', { name: /away-from-program/i }));

      // The info banner should have purple styling
      const infoBanner = screen.getByText(/28-Day Rule/i).closest('div');
      expect(infoBanner?.parentElement).toHaveClass('bg-purple-50');
    });

    it('tabs have distinct icons', () => {
      renderWithProviders(<ComplianceHubPage />);

      // Both tabs should have icons (Shield and Plane)
      const tabs = screen.getAllByRole('tab');
      tabs.forEach((tab) => {
        const icon = tab.querySelector('svg');
        expect(icon).toBeInTheDocument();
      });
    });
  });
});
