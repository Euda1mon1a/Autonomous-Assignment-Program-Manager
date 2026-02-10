/**
 * Tests for ViolationAlert Component
 * Component: compliance/ViolationAlert - ACGME violation display with severity levels
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { ViolationAlert, Violation } from '../ViolationAlert';

// Mock the Badge component to simplify assertions
jest.mock('../../ui/Badge', () => ({
  Badge: ({ children, variant, className }: { children: React.ReactNode; variant?: string; className?: string }) => (
    <span data-testid="badge" data-variant={variant} className={className}>
      {children}
    </span>
  ),
}));

describe('ViolationAlert', () => {
  const criticalViolation: Violation = {
    id: 'v-1',
    type: 'work_hours',
    severity: 'critical',
    message: 'Resident exceeded 80-hour weekly limit',
    date: '2024-06-15T12:00:00',
    details: {
      actual: 85,
      limit: 80,
      unit: 'hours',
    },
    suggestions: [
      'Reduce on-call shifts next week',
      'Consider scheduling a compensatory day off',
    ],
  };

  const warningViolation: Violation = {
    id: 'v-2',
    type: 'days_off',
    severity: 'warning',
    message: 'Approaching 1-in-7 day off limit',
    date: '2024-06-10T12:00:00',
  };

  describe('Rendering', () => {
    it('renders with required props', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('displays violation message', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(
        screen.getByText('Resident exceeded 80-hour weekly limit')
      ).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <ViolationAlert violation={criticalViolation} className="extra-class" />
      );
      expect(container.firstChild).toHaveClass('extra-class');
    });
  });

  describe('Critical Severity', () => {
    it('renders with red styling', () => {
      const { container } = render(
        <ViolationAlert violation={criticalViolation} />
      );
      expect(container.firstChild).toHaveClass('bg-red-50');
      expect(container.firstChild).toHaveClass('border-red-500');
    });

    it('displays "Critical" badge', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      const badges = screen.getAllByTestId('badge');
      const criticalBadge = badges.find(
        (b) => b.getAttribute('data-variant') === 'destructive'
      );
      expect(criticalBadge).toBeInTheDocument();
      expect(criticalBadge).toHaveTextContent('Critical');
    });

    it('has role="alert" with aria-live="assertive"', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'assertive');
    });
  });

  describe('Warning Severity', () => {
    it('renders with yellow styling', () => {
      const { container } = render(
        <ViolationAlert violation={warningViolation} />
      );
      expect(container.firstChild).toHaveClass('bg-yellow-50');
      expect(container.firstChild).toHaveClass('border-yellow-500');
    });

    it('displays "Warning" badge', () => {
      render(<ViolationAlert violation={warningViolation} />);
      const badges = screen.getAllByTestId('badge');
      const warningBadge = badges.find(
        (b) => b.getAttribute('data-variant') === 'warning'
      );
      expect(warningBadge).toBeInTheDocument();
      expect(warningBadge).toHaveTextContent('Warning');
    });
  });

  describe('Compact Mode', () => {
    it('renders compact layout when compact=true', () => {
      const { container } = render(
        <ViolationAlert violation={criticalViolation} compact />
      );
      expect(container.querySelector('.violation-alert-compact')).toBeInTheDocument();
      expect(container.querySelector('.violation-alert:not(.violation-alert-compact)')).not.toBeInTheDocument();
    });

    it('shows truncated message in compact mode', () => {
      render(<ViolationAlert violation={criticalViolation} compact />);
      expect(
        screen.getByText('Resident exceeded 80-hour weekly limit')
      ).toBeInTheDocument();
    });

    it('shows badge in compact mode', () => {
      render(<ViolationAlert violation={criticalViolation} compact />);
      expect(screen.getByTestId('badge')).toHaveTextContent('Critical');
    });

    it('has role="alert" in compact mode', () => {
      render(<ViolationAlert violation={criticalViolation} compact />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('does not show details section in compact mode', () => {
      render(<ViolationAlert violation={criticalViolation} compact />);
      expect(screen.queryByText('Actual:')).not.toBeInTheDocument();
    });

    it('does not show suggestions in compact mode', () => {
      render(<ViolationAlert violation={criticalViolation} compact />);
      expect(
        screen.queryByText('Reduce on-call shifts next week')
      ).not.toBeInTheDocument();
    });
  });

  describe('Full Mode (default)', () => {
    it('renders full layout by default', () => {
      const { container } = render(
        <ViolationAlert violation={criticalViolation} />
      );
      expect(container.querySelector('.violation-alert')).toBeInTheDocument();
    });

    it('shows type label heading', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(screen.getByText('80-Hour Violation')).toBeInTheDocument();
    });

    it('displays the date in formatted form', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      // Date '2024-06-15' formatted as "Saturday, June 15, 2024"
      expect(screen.getByText(/June 15, 2024/)).toBeInTheDocument();
    });
  });

  describe('onDismiss Callback', () => {
    it('renders dismiss button when onDismiss is provided', () => {
      const onDismiss = jest.fn();
      render(
        <ViolationAlert violation={criticalViolation} onDismiss={onDismiss} />
      );
      expect(
        screen.getByLabelText('Dismiss 80-Hour Violation alert')
      ).toBeInTheDocument();
    });

    it('calls onDismiss with violation id when dismiss button is clicked', () => {
      const onDismiss = jest.fn();
      render(
        <ViolationAlert violation={criticalViolation} onDismiss={onDismiss} />
      );
      fireEvent.click(screen.getByLabelText('Dismiss 80-Hour Violation alert'));
      expect(onDismiss).toHaveBeenCalledWith('v-1');
    });

    it('does not render dismiss button when onDismiss is not provided', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(
        screen.queryByLabelText('Dismiss 80-Hour Violation alert')
      ).not.toBeInTheDocument();
    });
  });

  describe('onResolve Callback', () => {
    it('renders resolve button when onResolve is provided', () => {
      const onResolve = jest.fn();
      render(
        <ViolationAlert violation={criticalViolation} onResolve={onResolve} />
      );
      expect(
        screen.getByLabelText('Resolve 80-Hour Violation')
      ).toBeInTheDocument();
    });

    it('calls onResolve with violation id when resolve button is clicked', () => {
      const onResolve = jest.fn();
      render(
        <ViolationAlert violation={criticalViolation} onResolve={onResolve} />
      );
      fireEvent.click(screen.getByLabelText('Resolve 80-Hour Violation'));
      expect(onResolve).toHaveBeenCalledWith('v-1');
    });

    it('does not render resolve button when onResolve is not provided', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(
        screen.queryByLabelText('Resolve 80-Hour Violation')
      ).not.toBeInTheDocument();
    });
  });

  describe('Details Section', () => {
    it('displays actual value with unit', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(screen.getByText('Actual:')).toBeInTheDocument();
      expect(screen.getByText('85 hours')).toBeInTheDocument();
    });

    it('displays limit value with unit', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(screen.getByText('Limit:')).toBeInTheDocument();
      expect(screen.getByText('80 hours')).toBeInTheDocument();
    });

    it('does not render details section when details are absent', () => {
      render(<ViolationAlert violation={warningViolation} />);
      expect(screen.queryByText('Actual:')).not.toBeInTheDocument();
      expect(screen.queryByText('Limit:')).not.toBeInTheDocument();
    });
  });

  describe('Suggestions List', () => {
    it('renders suggestions when provided', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(
        screen.getByText('Reduce on-call shifts next week')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Consider scheduling a compensatory day off')
      ).toBeInTheDocument();
    });

    it('renders "Suggested Actions" heading', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(screen.getByText(/Suggested Actions/)).toBeInTheDocument();
    });

    it('has aria-label on the suggestions region', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(
        screen.getByRole('region', { name: 'Suggested actions' })
      ).toBeInTheDocument();
    });

    it('does not render suggestions when not provided', () => {
      render(<ViolationAlert violation={warningViolation} />);
      expect(screen.queryByText(/Suggested Actions/)).not.toBeInTheDocument();
    });

    it('does not render suggestions when array is empty', () => {
      const violationWithEmptySuggestions: Violation = {
        ...criticalViolation,
        suggestions: [],
      };
      render(<ViolationAlert violation={violationWithEmptySuggestions} />);
      expect(screen.queryByText(/Suggested Actions/)).not.toBeInTheDocument();
    });
  });

  describe('Violation Type Labels Mapping', () => {
    it('maps work_hours to "80-Hour Violation"', () => {
      render(
        <ViolationAlert
          violation={{ ...criticalViolation, type: 'work_hours' }}
        />
      );
      expect(screen.getByText('80-Hour Violation')).toBeInTheDocument();
    });

    it('maps days_off to "1-in-7 Violation"', () => {
      render(
        <ViolationAlert
          violation={{ ...criticalViolation, type: 'days_off' }}
        />
      );
      expect(screen.getByText('1-in-7 Violation')).toBeInTheDocument();
    });

    it('maps supervision to "Supervision Ratio Violation"', () => {
      render(
        <ViolationAlert
          violation={{ ...criticalViolation, type: 'supervision' }}
        />
      );
      expect(
        screen.getByText('Supervision Ratio Violation')
      ).toBeInTheDocument();
    });

    it('maps continuous_duty to "Continuous Duty Violation"', () => {
      render(
        <ViolationAlert
          violation={{ ...criticalViolation, type: 'continuous_duty' }}
        />
      );
      expect(screen.getByText('Continuous Duty Violation')).toBeInTheDocument();
    });

    it('maps rest_period to "Rest Period Violation"', () => {
      render(
        <ViolationAlert
          violation={{ ...criticalViolation, type: 'rest_period' }}
        />
      );
      expect(screen.getByText('Rest Period Violation')).toBeInTheDocument();
    });

    it('falls back to raw type for unknown types', () => {
      render(
        <ViolationAlert
          violation={{ ...criticalViolation, type: 'unknown_type' }}
        />
      );
      expect(screen.getByText('unknown_type')).toBeInTheDocument();
    });
  });

  describe('ARIA Attributes', () => {
    it('has role="alert" in full mode', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('has descriptive aria-label on alert in full mode', () => {
      render(<ViolationAlert violation={criticalViolation} />);
      expect(screen.getByRole('alert')).toHaveAttribute(
        'aria-label',
        'Critical: 80-Hour Violation'
      );
    });

    it('has descriptive aria-label on alert in compact mode', () => {
      render(<ViolationAlert violation={criticalViolation} compact />);
      expect(screen.getByRole('alert')).toHaveAttribute(
        'aria-label',
        'Critical: Resident exceeded 80-hour weekly limit'
      );
    });

    it('has aria-label on violation actions group', () => {
      const onResolve = jest.fn();
      render(
        <ViolationAlert violation={criticalViolation} onResolve={onResolve} />
      );
      expect(
        screen.getByRole('group', { name: 'Violation actions' })
      ).toBeInTheDocument();
    });
  });
});
