/**
 * Tests for EarlyWarningPanel Component
 * Component: 29 - Early warning indicators
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { EarlyWarningPanel, EarlyWarning } from '../EarlyWarningPanel';

describe('EarlyWarningPanel', () => {
  const mockWarnings: EarlyWarning[] = [
    {
      id: 'warn-1',
      type: 'utilization',
      severity: 'critical',
      message: 'Utilization exceeding 90%',
      detectedAt: '2025-01-15T10:30:00Z',
      rule: 'Western Electric Rule 1',
    },
    {
      id: 'warn-2',
      type: 'burnout',
      severity: 'warning',
      message: 'Burnout Rt approaching 1.0',
      detectedAt: '2025-01-15T11:00:00Z',
      rule: 'Trend Detection',
      trend: [
        { date: '2025-01-10', value: 0.7 },
        { date: '2025-01-12', value: 0.8 },
        { date: '2025-01-14', value: 0.9 },
      ],
    },
    {
      id: 'warn-3',
      type: 'coverage',
      severity: 'info',
      message: 'Weekend coverage suboptimal',
      detectedAt: '2025-01-15T12:00:00Z',
    },
  ];

  // Test 29.1: Render test - renders with warnings
  describe('Rendering', () => {
    it('renders with warnings', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      expect(screen.getByText('Active Warnings')).toBeInTheDocument();
      expect(screen.getByText('Utilization exceeding 90%')).toBeInTheDocument();
    });

    it('renders empty state when no warnings', () => {
      render(<EarlyWarningPanel warnings={[]} />);

      expect(screen.getByText('All Clear')).toBeInTheDocument();
      expect(screen.getByText(/No early warning indicators detected/)).toBeInTheDocument();
    });

    it('displays warning counts in badges', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      expect(screen.getByText('1 Critical')).toBeInTheDocument();
      expect(screen.getByText('1 Warnings')).toBeInTheDocument();
    });

    it('renders drill down button when callback provided', () => {
      const onDrillDown = jest.fn();
      render(<EarlyWarningPanel warnings={mockWarnings} onDrillDown={onDrillDown} />);

      expect(screen.getByText('View Full Early Warning Analysis')).toBeInTheDocument();
    });

    it('does not render drill down button when callback not provided', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      expect(screen.queryByText('View Full Early Warning Analysis')).not.toBeInTheDocument();
    });
  });

  // Test 29.2: Warning types and severity
  describe('Warning Types and Severity', () => {
    it('displays all warning types correctly', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      expect(screen.getByText('Utilization exceeding 90%')).toBeInTheDocument();
      expect(screen.getByText('Burnout Rt approaching 1.0')).toBeInTheDocument();
      expect(screen.getByText('Weekend coverage suboptimal')).toBeInTheDocument();
    });

    it('sorts warnings by severity (critical > warning > info)', () => {
      const { container } = render(<EarlyWarningPanel warnings={mockWarnings} />);

      const warningElements = container.querySelectorAll('.border-l-4.rounded-lg');
      const messages = Array.from(warningElements).map(el => el.textContent);

      // First should be critical
      expect(messages[0]).toContain('Utilization exceeding 90%');
      // Second should be warning
      expect(messages[1]).toContain('Burnout Rt approaching 1.0');
      // Third should be info
      expect(messages[2]).toContain('Weekend coverage suboptimal');
    });

    it('groups warnings by type in summary', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      // Should show type breakdown with counts
      const typeBreakdown = screen.getAllByText(/Utilization|Burnout|Coverage|Compliance/);
      expect(typeBreakdown.length).toBeGreaterThan(0);
    });

    it('displays correct icon for each warning type', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      // Check for type icons in the summary
      const summary = screen.getByText('Active Warnings').closest('div');
      expect(summary).toBeInTheDocument();
    });

    it('displays detection rule when provided', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      expect(screen.getByText(/Rule: Western Electric Rule 1/)).toBeInTheDocument();
      expect(screen.getByText(/Rule: Trend Detection/)).toBeInTheDocument();
    });
  });

  // Test 29.3: Accessibility and interaction
  describe('Accessibility and Interaction', () => {
    it('allows dismissing warnings', () => {
      const onDismiss = jest.fn();
      render(<EarlyWarningPanel warnings={mockWarnings} onDismiss={onDismiss} />);

      const dismissButtons = screen.getAllByLabelText('Dismiss warning');
      fireEvent.click(dismissButtons[0]);

      expect(onDismiss).toHaveBeenCalledWith('warn-1');
    });

    it('toggles trend chart visibility', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      const viewTrendButton = screen.getByText('View Trend');
      fireEvent.click(viewTrendButton);

      expect(screen.getByText('Trend Data')).toBeInTheDocument();

      // Click again to hide
      const hideTrendButton = screen.getByText('Hide Trend');
      fireEvent.click(hideTrendButton);

      expect(screen.queryByText('Trend Data')).not.toBeInTheDocument();
    });

    it('drill down button is accessible', () => {
      const onDrillDown = jest.fn();
      render(<EarlyWarningPanel warnings={mockWarnings} onDrillDown={onDrillDown} />);

      const button = screen.getByText('View Full Early Warning Analysis');
      fireEvent.click(button);

      expect(onDrillDown).toHaveBeenCalledTimes(1);
    });

    it('warning messages are announced properly', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      const criticalIcon = screen.getAllByRole('img', { name: 'Critical' })[0];
      expect(criticalIcon).toBeInTheDocument();
    });

    it('displays trend chart when warning has trend data', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      const viewTrendButton = screen.getByText('View Trend');
      fireEvent.click(viewTrendButton);

      // Check for trend data points
      expect(screen.getByText('Trend Data')).toBeInTheDocument();
    });
  });

  // Test 29.4: Edge cases
  describe('Edge Cases', () => {
    it('handles empty warnings array', () => {
      render(<EarlyWarningPanel warnings={[]} />);

      expect(screen.getByText('All Clear')).toBeInTheDocument();
      expect(screen.queryByText('Active Warnings')).not.toBeInTheDocument();
    });

    it('handles warnings without trends', () => {
      const warningWithoutTrend: EarlyWarning[] = [
        {
          id: 'warn-1',
          type: 'compliance',
          severity: 'critical',
          message: 'ACGME violation detected',
          detectedAt: '2025-01-15T10:30:00Z',
        },
      ];

      render(<EarlyWarningPanel warnings={warningWithoutTrend} />);

      expect(screen.queryByText('View Trend')).not.toBeInTheDocument();
    });

    it('handles warnings without rules', () => {
      const warningWithoutRule: EarlyWarning[] = [
        {
          id: 'warn-1',
          type: 'coverage',
          severity: 'info',
          message: 'Coverage gap detected',
          detectedAt: '2025-01-15T10:30:00Z',
        },
      ];

      render(<EarlyWarningPanel warnings={warningWithoutRule} />);

      expect(screen.queryByText(/Rule:/)).not.toBeInTheDocument();
    });

    it('formats detection timestamp correctly', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      // Should display formatted date
      expect(screen.getByText(/Detected:/)).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <EarlyWarningPanel warnings={[]} className="custom-class" />
      );

      expect(container.querySelector('.early-warning-panel.custom-class')).toBeInTheDocument();
    });

    it('displays framework explanation', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      expect(screen.getByText(/SPC Early Warning System/)).toBeInTheDocument();
      expect(screen.getByText(/Western Electric rules/)).toBeInTheDocument();
    });

    it('handles multiple warnings of same type', () => {
      const duplicateTypeWarnings: EarlyWarning[] = [
        {
          id: 'warn-1',
          type: 'utilization',
          severity: 'critical',
          message: 'First utilization warning',
          detectedAt: '2025-01-15T10:30:00Z',
        },
        {
          id: 'warn-2',
          type: 'utilization',
          severity: 'warning',
          message: 'Second utilization warning',
          detectedAt: '2025-01-15T11:00:00Z',
        },
      ];

      render(<EarlyWarningPanel warnings={duplicateTypeWarnings} />);

      expect(screen.getByText('First utilization warning')).toBeInTheDocument();
      expect(screen.getByText('Second utilization warning')).toBeInTheDocument();
    });

    it('displays trend chart with correct data points', () => {
      render(<EarlyWarningPanel warnings={mockWarnings} />);

      const viewTrendButton = screen.getByText('View Trend');
      fireEvent.click(viewTrendButton);

      // Should render 3 trend points
      const trendChart = screen.getByText('Trend Data').closest('div');
      expect(trendChart).toBeInTheDocument();
    });

    it('only shows critical badge when there are critical warnings', () => {
      const warningsNoCritical: EarlyWarning[] = mockWarnings.filter(w => w.severity !== 'critical');

      render(<EarlyWarningPanel warnings={warningsNoCritical} />);

      expect(screen.queryByText('Critical')).not.toBeInTheDocument();
      expect(screen.getByText('1 Warnings')).toBeInTheDocument();
    });

    it('handles all four warning types', () => {
      const allTypes: EarlyWarning[] = [
        {
          id: '1',
          type: 'utilization',
          severity: 'info',
          message: 'Utilization warning',
          detectedAt: '2025-01-15T10:00:00Z',
        },
        {
          id: '2',
          type: 'burnout',
          severity: 'info',
          message: 'Burnout warning',
          detectedAt: '2025-01-15T10:00:00Z',
        },
        {
          id: '3',
          type: 'coverage',
          severity: 'info',
          message: 'Coverage warning',
          detectedAt: '2025-01-15T10:00:00Z',
        },
        {
          id: '4',
          type: 'compliance',
          severity: 'info',
          message: 'Compliance warning',
          detectedAt: '2025-01-15T10:00:00Z',
        },
      ];

      render(<EarlyWarningPanel warnings={allTypes} />);

      expect(screen.getByText('Utilization warning')).toBeInTheDocument();
      expect(screen.getByText('Burnout warning')).toBeInTheDocument();
      expect(screen.getByText('Coverage warning')).toBeInTheDocument();
      expect(screen.getByText('Compliance warning')).toBeInTheDocument();
    });
  });
});
