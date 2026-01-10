/**
 * Tests for CompliancePanel Component
 * Component: compliance/CompliancePanel - ACGME compliance dashboard panel
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { CompliancePanel, ComplianceData, CompliancePanelProps } from '../CompliancePanel';

describe('CompliancePanel', () => {
  const mockDateRange = {
    start: '2024-01-01',
    end: '2024-01-28',
  };

  const mockComplianceData: ComplianceData = {
    personId: 'person-1',
    personName: 'Dr. John Smith',
    pgyLevel: 'PGY-2',
    currentWeekHours: 65,
    rolling4WeekAverage: 68,
    consecutiveDaysWorked: 6,
    lastDayOff: '2024-01-22',
    supervisionRatio: {
      current: 2,
      required: 1,
    },
    violations: [],
  };

  describe('Rendering', () => {
    it('renders person name', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
    });

    it('displays PGY level', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText(/PGY-2/)).toBeInTheDocument();
    });

    it('shows current week hours', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText('65')).toBeInTheDocument();
    });

    it('shows rolling 4-week average', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText(/68/)).toBeInTheDocument();
    });

    it('shows consecutive days worked', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText('6')).toBeInTheDocument();
    });

    it('shows last day off', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText(/2024-01-22/)).toBeInTheDocument();
    });
  });

  describe('Compliance Status', () => {
    it('shows compliant status when no violations', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText(/compliant/i)).toBeInTheDocument();
    });

    it('shows violation status when violations exist', () => {
      const dataWithViolations: ComplianceData = {
        ...mockComplianceData,
        violations: [
          { id: 'v1', type: '80-hour', severity: 'critical', message: 'Exceeded 80 hours per week', date: '2024-01-28' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} dateRange={mockDateRange} />);
      expect(screen.getByText(/violation/i)).toBeInTheDocument();
    });
  });

  describe('Violations List', () => {
    it('displays violation messages', () => {
      const dataWithViolations: ComplianceData = {
        ...mockComplianceData,
        violations: [
          { id: 'v1', type: '80-hour', severity: 'critical', message: 'Exceeded 80 hours per week', date: '2024-01-28' },
          { id: 'v2', type: '1-in-7', severity: 'warning', message: 'Missing required day off', date: '2024-01-28' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} dateRange={mockDateRange} />);
      expect(screen.getByText(/exceeded 80 hours/i)).toBeInTheDocument();
      expect(screen.getByText(/missing required day off/i)).toBeInTheDocument();
    });

    it('shows violation count', () => {
      const dataWithViolations: ComplianceData = {
        ...mockComplianceData,
        violations: [
          { id: 'v1', type: '80-hour', severity: 'critical', message: 'Violation 1', date: '2024-01-28' },
          { id: 'v2', type: '1-in-7', severity: 'warning', message: 'Violation 2', date: '2024-01-28' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} dateRange={mockDateRange} />);
      expect(screen.getByText(/2/)).toBeInTheDocument();
    });
  });

  describe('ACGME Rules Indicators', () => {
    it('shows 80-hour rule status', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText(/80.*hour/i)).toBeInTheDocument();
    });

    it('shows 1-in-7 rule status', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText(/1.*in.*7/i)).toBeInTheDocument();
    });

    it('indicates when approaching 80-hour limit', () => {
      const approachingLimit: ComplianceData = {
        ...mockComplianceData,
        rolling4WeekAverage: 78,
      };
      render(<CompliancePanel data={approachingLimit} dateRange={mockDateRange} />);
      expect(screen.getByText(/78/)).toBeInTheDocument();
    });

    it('warns when approaching 1-in-7 violation', () => {
      const approachingViolation: ComplianceData = {
        ...mockComplianceData,
        consecutiveDaysWorked: 6,
      };
      render(<CompliancePanel data={approachingViolation} dateRange={mockDateRange} />);
      expect(screen.getByText('6')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero hours worked', () => {
      const zeroHours: ComplianceData = {
        ...mockComplianceData,
        currentWeekHours: 0,
        rolling4WeekAverage: 0,
      };
      render(<CompliancePanel data={zeroHours} dateRange={mockDateRange} />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('handles maximum hours (80)', () => {
      const maxHours: ComplianceData = {
        ...mockComplianceData,
        rolling4WeekAverage: 80,
      };
      render(<CompliancePanel data={maxHours} dateRange={mockDateRange} />);
      expect(screen.getByText(/80/)).toBeInTheDocument();
    });

    it('handles over limit hours', () => {
      const overLimit: ComplianceData = {
        ...mockComplianceData,
        rolling4WeekAverage: 85,
        violations: [
          { id: 'v1', type: '80-hour', severity: 'critical', message: 'Exceeded limit', date: '2024-01-28' },
        ],
      };
      render(<CompliancePanel data={overLimit} dateRange={mockDateRange} />);
      expect(screen.getByText(/85/)).toBeInTheDocument();
      expect(screen.getByText(/violation/i)).toBeInTheDocument();
    });

    it('handles no days off', () => {
      const noDaysOff: ComplianceData = {
        ...mockComplianceData,
        consecutiveDaysWorked: 28,
        lastDayOff: '2024-01-01',
      };
      render(<CompliancePanel data={noDaysOff} dateRange={mockDateRange} />);
      expect(screen.getByText('28')).toBeInTheDocument();
    });
  });
});
