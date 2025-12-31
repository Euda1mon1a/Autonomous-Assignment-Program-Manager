/**
 * Tests for ComplianceAlert Component
 * Component: dashboard/ComplianceAlert - Compliance violation alert
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { ComplianceAlert } from '../ComplianceAlert';

describe('ComplianceAlert', () => {
  const mockOnDismiss = jest.fn();
  const mockOnView = jest.fn();

  beforeEach(() => {
    mockOnDismiss.mockClear();
    mockOnView.mockClear();
  });

  describe('Rendering', () => {
    it('renders alert title', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours per week"
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByText(/compliance alert/i)).toBeInTheDocument();
    });

    it('renders person name', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours per week"
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
    });

    it('renders violation message', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours per week"
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByText(/exceeded 80 hours/i)).toBeInTheDocument();
    });

    it('renders dismiss button', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByLabelText(/dismiss/i)).toBeInTheDocument();
    });

    it('renders view details button when onView provided', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
          onView={mockOnView}
        />
      );
      expect(screen.getByText(/view details/i)).toBeInTheDocument();
    });
  });

  describe('Alert Types', () => {
    it('renders high severity alert for 80-hour violation', () => {
      const { container } = render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );
      expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
    });

    it('renders medium severity alert for 1-in-7 violation', () => {
      const { container } = render(
        <ComplianceAlert
          type="1-in-7-violation"
          personName="Dr. John Smith"
          message="Missing required day off"
          onDismiss={mockOnDismiss}
        />
      );
      expect(container.querySelector('.bg-amber-50')).toBeInTheDocument();
    });

    it('renders warning alert for approaching limit', () => {
      const { container } = render(
        <ComplianceAlert
          type="approaching-limit"
          personName="Dr. John Smith"
          message="Approaching 80-hour limit"
          onDismiss={mockOnDismiss}
        />
      );
      expect(container.querySelector('.bg-yellow-50')).toBeInTheDocument();
    });

    it('renders info alert for supervision ratio', () => {
      const { container } = render(
        <ComplianceAlert
          type="supervision-ratio"
          personName="Dr. John Smith"
          message="Supervision ratio concern"
          onDismiss={mockOnDismiss}
        />
      );
      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    });
  });

  describe('Interaction', () => {
    it('calls onDismiss when dismiss button clicked', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );

      fireEvent.click(screen.getByLabelText(/dismiss/i));
      expect(mockOnDismiss).toHaveBeenCalledTimes(1);
    });

    it('calls onView when view details button clicked', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
          onView={mockOnView}
        />
      );

      fireEvent.click(screen.getByText(/view details/i));
      expect(mockOnView).toHaveBeenCalledTimes(1);
    });

    it('does not render view button when onView not provided', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.queryByText(/view details/i)).not.toBeInTheDocument();
    });
  });

  describe('Icons', () => {
    it('renders alert icon for high severity', () => {
      const { container } = render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders warning icon for medium severity', () => {
      const { container } = render(
        <ComplianceAlert
          type="1-in-7-violation"
          personName="Dr. John Smith"
          message="Missing day off"
          onDismiss={mockOnDismiss}
        />
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has alert role', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('has accessible dismiss button', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );
      const dismissButton = screen.getByLabelText(/dismiss/i);
      expect(dismissButton).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles very long person names', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Michael Christopher Smith-Johnson III"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByText(/Dr. John Michael Christopher Smith-Johnson III/)).toBeInTheDocument();
    });

    it('handles very long messages', () => {
      const longMessage =
        'This person has exceeded the 80-hour work week limit for multiple consecutive weeks and needs immediate schedule adjustment.';
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. John Smith"
          message={longMessage}
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('handles special characters in names', () => {
      render(
        <ComplianceAlert
          type="80-hour-violation"
          personName="Dr. O'Brien-Smith"
          message="Exceeded 80 hours"
          onDismiss={mockOnDismiss}
        />
      );
      expect(screen.getByText("Dr. O'Brien-Smith")).toBeInTheDocument();
    });
  });

  describe('Multiple Alerts', () => {
    it('renders multiple alerts independently', () => {
      const { container } = render(
        <>
          <ComplianceAlert
            type="80-hour-violation"
            personName="Dr. John Smith"
            message="Exceeded 80 hours"
            onDismiss={mockOnDismiss}
          />
          <ComplianceAlert
            type="1-in-7-violation"
            personName="Dr. Jane Doe"
            message="Missing day off"
            onDismiss={mockOnDismiss}
          />
        </>
      );

      const alerts = container.querySelectorAll('[role="alert"]');
      expect(alerts.length).toBe(2);
    });
  });
});
