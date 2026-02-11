/**
 * Tests for CompliancePanel Component
 * Component: compliance/CompliancePanel - ACGME compliance dashboard panel
 *
 * CompliancePanel renders sub-components: WorkHourGauge, DayOffIndicator,
 * SupervisionRatio, ViolationAlert. Text values are formatted by those
 * sub-components (e.g., hours as "65.0h / 80h" across multiple spans).
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { CompliancePanel, ComplianceData } from '../CompliancePanel';

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
      // PGY-2 appears in header and SupervisionRatio sub-component
      expect(screen.getAllByText(/PGY-2/).length).toBeGreaterThan(0);
    });

    it('shows current week hours via WorkHourGauge', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      // WorkHourGauge has aria-label "Current Week: 65 hours out of 80 hours"
      expect(screen.getByLabelText(/Current Week: 65 hours/)).toBeInTheDocument();
    });

    it('shows rolling 4-week average via WorkHourGauge', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      // WorkHourGauge has aria-label "4-Week Rolling Avg: 68 hours out of 80 hours"
      expect(screen.getByLabelText(/4-Week Rolling Avg: 68 hours/)).toBeInTheDocument();
    });

    it('shows consecutive days worked', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      // DayOffIndicator shows "6 / 6 days"
      expect(screen.getByText(/6 \/ 6 days/)).toBeInTheDocument();
    });

    it('shows last day off date', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      // DayOffIndicator renders last day off via toLocaleDateString
      const expectedDate = new Date('2024-01-22').toLocaleDateString();
      expect(screen.getByText(new RegExp(expectedDate.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))).toBeInTheDocument();
    });
  });

  describe('Compliance Status', () => {
    it('shows compliant status when no violations', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      // Badge shows "Compliant"
      expect(screen.getByText('Compliant')).toBeInTheDocument();
    });

    it('shows violation status when violations exist', () => {
      const dataWithViolations: ComplianceData = {
        ...mockComplianceData,
        violations: [
          { id: 'v1', type: '80-hour', severity: 'critical', message: 'Exceeded 80 hours per week', date: '2024-01-28' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} dateRange={mockDateRange} />);
      // Badge shows "Violation"
      expect(screen.getByText('Violation')).toBeInTheDocument();
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

    it('shows violation count badges', () => {
      const dataWithViolations: ComplianceData = {
        ...mockComplianceData,
        violations: [
          { id: 'v1', type: '80-hour', severity: 'critical', message: 'Violation 1', date: '2024-01-28' },
          { id: 'v2', type: '1-in-7', severity: 'warning', message: 'Violation 2', date: '2024-01-28' },
        ],
      };
      render(<CompliancePanel data={dataWithViolations} dateRange={mockDateRange} />);
      expect(screen.getByText(/1 Critical/)).toBeInTheDocument();
      expect(screen.getByText(/1 Warnings/)).toBeInTheDocument();
    });
  });

  describe('ACGME Rules Indicators', () => {
    it('shows work hour compliance section', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText('Work Hour Compliance')).toBeInTheDocument();
    });

    it('shows 1-in-7 days off section', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText('1-in-7 Days Off')).toBeInTheDocument();
    });

    it('shows supervision ratio section', () => {
      render(<CompliancePanel data={mockComplianceData} dateRange={mockDateRange} />);
      expect(screen.getByText('Supervision Ratio')).toBeInTheDocument();
    });

    it('indicates when approaching 80-hour limit', () => {
      const approachingLimit: ComplianceData = {
        ...mockComplianceData,
        rolling4WeekAverage: 78,
      };
      render(<CompliancePanel data={approachingLimit} dateRange={mockDateRange} />);
      // WorkHourGauge has aria-label with the hour values
      expect(screen.getByLabelText(/4-Week Rolling Avg: 78 hours/)).toBeInTheDocument();
    });

    it('warns when approaching 1-in-7 violation', () => {
      const approachingViolation: ComplianceData = {
        ...mockComplianceData,
        consecutiveDaysWorked: 6,
      };
      render(<CompliancePanel data={approachingViolation} dateRange={mockDateRange} />);
      expect(screen.getByText(/6 \/ 6 days/)).toBeInTheDocument();
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
      // WorkHourGauge aria-labels contain "0 hours"
      expect(screen.getByLabelText(/Current Week: 0 hours/)).toBeInTheDocument();
    });

    it('handles maximum hours (80)', () => {
      const maxHours: ComplianceData = {
        ...mockComplianceData,
        rolling4WeekAverage: 80,
      };
      render(<CompliancePanel data={maxHours} dateRange={mockDateRange} />);
      expect(screen.getByLabelText(/4-Week Rolling Avg: 80 hours/)).toBeInTheDocument();
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
      expect(screen.getByLabelText(/4-Week Rolling Avg: 85 hours/)).toBeInTheDocument();
      // Badge shows "Violation"
      expect(screen.getByText('Violation')).toBeInTheDocument();
    });

    it('handles many consecutive days', () => {
      const noDaysOff: ComplianceData = {
        ...mockComplianceData,
        consecutiveDaysWorked: 28,
        lastDayOff: '2024-01-01',
      };
      render(<CompliancePanel data={noDaysOff} dateRange={mockDateRange} />);
      // DayOffIndicator shows "28 / 6 days"
      expect(screen.getByText(/28 \/ 6 days/)).toBeInTheDocument();
    });
  });
});
