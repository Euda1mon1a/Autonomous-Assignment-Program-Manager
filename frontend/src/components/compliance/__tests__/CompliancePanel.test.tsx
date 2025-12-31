/**
 * Tests for CompliancePanel Component
 * Component: compliance/CompliancePanel - ACGME compliance dashboard panel
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { CompliancePanel } from '../CompliancePanel';

describe('CompliancePanel', () => {
  const mockComplianceData = {
    personId: 'person-1',
    personName: 'Dr. John Smith',
    periodStart: '2024-01-01',
    periodEnd: '2024-01-28',
    totalHours: 65,
    avgHoursPerWeek: 65,
    maxHoursInWeek: 72,
    daysOff: 4,
    consecutiveDaysWorked: 6,
    violations: [],
    isCompliant: true,
  };

  describe('Rendering', () => {
    it('renders person name', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
    });

    it('displays period dates', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText(/Jan 1, 2024/)).toBeInTheDocument();
      expect(screen.getByText(/Jan 28, 2024/)).toBeInTheDocument();
    });

    it('shows total hours worked', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText('65')).toBeInTheDocument();
      expect(screen.getByText(/total hours/i)).toBeInTheDocument();
    });

    it('shows average hours per week', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText(/65.*hours/i)).toBeInTheDocument();
      expect(screen.getByText(/avg.*week/i)).toBeInTheDocument();
    });

    it('shows days off count', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText(/days off/i)).toBeInTheDocument();
    });

    it('shows consecutive days worked', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText('6')).toBeInTheDocument();
      expect(screen.getByText(/consecutive days/i)).toBeInTheDocument();
    });
  });

  describe('Compliance Status', () => {
    it('shows compliant badge when no violations', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText(/compliant/i)).toBeInTheDocument();
    });

    it('shows compliant badge in green', () => {
      const { container } = render(<CompliancePanel data={mockComplianceData} />);
      const badge = screen.getByText(/compliant/i);
      expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('shows violation badge when violations exist', () => {
      const dataWithViolations = {
        ...mockComplianceData,
        isCompliant: false,
        violations: [
          { rule: '80-hour', severity: 'high', message: 'Exceeded 80 hours per week' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} />);
      expect(screen.getByText(/violation/i)).toBeInTheDocument();
    });

    it('shows violation badge in red', () => {
      const dataWithViolations = {
        ...mockComplianceData,
        isCompliant: false,
        violations: [
          { rule: '80-hour', severity: 'high', message: 'Exceeded 80 hours per week' },
        ],
      };
      const { container } = render(<CompliancePanel data={dataWithViolations} />);
      const badge = screen.getByText(/violation/i);
      expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });
  });

  describe('Violations List', () => {
    it('displays violation messages', () => {
      const dataWithViolations = {
        ...mockComplianceData,
        isCompliant: false,
        violations: [
          { rule: '80-hour', severity: 'high', message: 'Exceeded 80 hours per week' },
          { rule: '1-in-7', severity: 'medium', message: 'Missing required day off' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} />);
      expect(screen.getByText(/exceeded 80 hours/i)).toBeInTheDocument();
      expect(screen.getByText(/missing required day off/i)).toBeInTheDocument();
    });

    it('shows violation count', () => {
      const dataWithViolations = {
        ...mockComplianceData,
        isCompliant: false,
        violations: [
          { rule: '80-hour', severity: 'high', message: 'Violation 1' },
          { rule: '1-in-7', severity: 'medium', message: 'Violation 2' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} />);
      expect(screen.getByText(/2.*violations?/i)).toBeInTheDocument();
    });

    it('hides violations section when compliant', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.queryByText(/violation/i)).not.toBeInTheDocument();
    });
  });

  describe('ACGME Rules Indicators', () => {
    it('shows 80-hour rule status', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText(/80.*hour/i)).toBeInTheDocument();
    });

    it('shows 1-in-7 rule status', () => {
      render(<CompliancePanel data={mockComplianceData} />);
      expect(screen.getByText(/1.*in.*7/i)).toBeInTheDocument();
    });

    it('indicates when approaching 80-hour limit', () => {
      const approachingLimit = {
        ...mockComplianceData,
        avgHoursPerWeek: 78,
      };
      render(<CompliancePanel data={approachingLimit} />);
      expect(screen.getByText(/78.*hours/i)).toBeInTheDocument();
    });

    it('warns when approaching 1-in-7 violation', () => {
      const approachingViolation = {
        ...mockComplianceData,
        consecutiveDaysWorked: 6,
      };
      render(<CompliancePanel data={approachingViolation} />);
      // Should show warning
      const consecutiveDays = screen.getByText('6');
      expect(consecutiveDays.closest('div')).toHaveClass('text-amber-600');
    });
  });

  describe('Edge Cases', () => {
    it('handles zero hours worked', () => {
      const zeroHours = {
        ...mockComplianceData,
        totalHours: 0,
        avgHoursPerWeek: 0,
      };
      render(<CompliancePanel data={zeroHours} />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('handles maximum hours (80)', () => {
      const maxHours = {
        ...mockComplianceData,
        avgHoursPerWeek: 80,
        maxHoursInWeek: 80,
      };
      render(<CompliancePanel data={maxHours} />);
      expect(screen.getByText(/80.*hours/i)).toBeInTheDocument();
    });

    it('handles over limit hours', () => {
      const overLimit = {
        ...mockComplianceData,
        avgHoursPerWeek: 85,
        isCompliant: false,
        violations: [
          { rule: '80-hour', severity: 'high', message: 'Exceeded limit' },
        ],
      };
      render(<CompliancePanel data={overLimit} />);
      expect(screen.getByText(/85.*hours/i)).toBeInTheDocument();
      expect(screen.getByText(/violation/i)).toBeInTheDocument();
    });

    it('handles no days off', () => {
      const noDaysOff = {
        ...mockComplianceData,
        daysOff: 0,
        consecutiveDaysWorked: 28,
        isCompliant: false,
      };
      render(<CompliancePanel data={noDaysOff} />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading skeleton when loading', () => {
      render(<CompliancePanel data={null} isLoading={true} />);
      const { container } = render(<CompliancePanel data={null} isLoading={true} />);
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error message when error occurs', () => {
      render(<CompliancePanel data={null} error="Failed to load compliance data" />);
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });
});
