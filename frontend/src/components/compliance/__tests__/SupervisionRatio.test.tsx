/**
 * Tests for SupervisionRatio Component
 * Component: compliance/SupervisionRatio - Faculty-to-resident supervision ratio compliance
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { SupervisionRatio } from '../SupervisionRatio';

describe('SupervisionRatio', () => {
  const defaultProps = {
    current: 2.0,
    required: 4,
    pgyLevel: 'PGY-2',
  };

  describe('Rendering', () => {
    it('renders with required props', () => {
      render(<SupervisionRatio {...defaultProps} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('displays the ratio as "1:current (max 1:required)"', () => {
      render(<SupervisionRatio {...defaultProps} />);
      expect(screen.getByText('1:2.0 (max 1:4)')).toBeInTheDocument();
    });

    it('displays utilization percentage', () => {
      render(<SupervisionRatio {...defaultProps} />);
      // 2.0 / 4 * 100 = 50%
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <SupervisionRatio {...defaultProps} className="custom-class" />
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Normal State (Adequate Supervision)', () => {
    it('shows "Adequate Supervision" when current < required*0.9', () => {
      render(<SupervisionRatio {...defaultProps} current={3.0} required={4} />);
      // 3.0 < 4 * 0.9 (3.6) is false, 3.0 <= 3.6 is true
      // isWarning: 3.0 > 4*0.9 (3.6) => false
      // isViolation: 3.0 > 4 => false
      // So it should show "Adequate Supervision"
      expect(screen.getByText('Adequate Supervision')).toBeInTheDocument();
    });

    it('shows "Adequate Supervision" at low ratios', () => {
      render(<SupervisionRatio {...defaultProps} current={1.0} required={4} />);
      expect(screen.getByText('Adequate Supervision')).toBeInTheDocument();
    });

    it('applies green styling', () => {
      const { container } = render(
        <SupervisionRatio {...defaultProps} current={1.0} required={4} />
      );
      expect(container.firstChild).toHaveClass('bg-green-100');
      expect(container.firstChild).toHaveClass('border-green-500');
    });
  });

  describe('Warning State (Approaching Limit)', () => {
    it('shows "Approaching Limit" when current > required*0.9 but <= required', () => {
      // required * 0.9 = 3.6; current = 3.8 > 3.6, but 3.8 <= 4 (not violation)
      render(<SupervisionRatio {...defaultProps} current={3.8} required={4} />);
      expect(screen.getByText('Approaching Limit')).toBeInTheDocument();
    });

    it('shows warning at exactly required*0.9 + epsilon', () => {
      // required * 0.9 = 3.6; 3.7 > 3.6 => warning
      render(<SupervisionRatio {...defaultProps} current={3.7} required={4} />);
      expect(screen.getByText('Approaching Limit')).toBeInTheDocument();
    });

    it('applies yellow styling', () => {
      const { container } = render(
        <SupervisionRatio {...defaultProps} current={3.8} required={4} />
      );
      expect(container.firstChild).toHaveClass('bg-yellow-100');
      expect(container.firstChild).toHaveClass('border-yellow-500');
    });
  });

  describe('Violation State (Insufficient Supervision)', () => {
    it('shows "Insufficient Supervision" when current > required', () => {
      render(<SupervisionRatio {...defaultProps} current={5.0} required={4} />);
      expect(screen.getByText('Insufficient Supervision')).toBeInTheDocument();
    });

    it('shows violation at just over the required limit', () => {
      render(<SupervisionRatio {...defaultProps} current={4.1} required={4} />);
      expect(screen.getByText('Insufficient Supervision')).toBeInTheDocument();
    });

    it('applies red styling', () => {
      const { container } = render(
        <SupervisionRatio {...defaultProps} current={5.0} required={4} />
      );
      expect(container.firstChild).toHaveClass('bg-red-100');
      expect(container.firstChild).toHaveClass('border-red-500');
    });

    it('does not show adequate or approaching indicators', () => {
      render(<SupervisionRatio {...defaultProps} current={5.0} required={4} />);
      expect(
        screen.queryByText('Adequate Supervision')
      ).not.toBeInTheDocument();
      expect(screen.queryByText('Approaching Limit')).not.toBeInTheDocument();
    });
  });

  describe('PGY Level Info Display', () => {
    it('displays PGY-1 requirements', () => {
      render(
        <SupervisionRatio {...defaultProps} pgyLevel="PGY-1" required={2} />
      );
      expect(screen.getByText('PGY-1 Requirements:')).toBeInTheDocument();
      expect(
        screen.getByText(
          'Interns require higher supervision (max 1:2 faculty:resident ratio)'
        )
      ).toBeInTheDocument();
    });

    it('displays PGY-2 requirements', () => {
      render(<SupervisionRatio {...defaultProps} pgyLevel="PGY-2" />);
      expect(screen.getByText('PGY-2 Requirements:')).toBeInTheDocument();
      expect(
        screen.getByText(
          'Advanced residents (max 1:4 faculty:resident ratio)'
        )
      ).toBeInTheDocument();
    });

    it('displays PGY-3 requirements', () => {
      render(<SupervisionRatio {...defaultProps} pgyLevel="PGY-3" />);
      expect(screen.getByText('PGY-3 Requirements:')).toBeInTheDocument();
      expect(
        screen.getByText(
          'Senior residents (max 1:4 faculty:resident ratio)'
        )
      ).toBeInTheDocument();
    });

    it('falls back to PGY-2 requirements for unknown PGY levels', () => {
      render(<SupervisionRatio {...defaultProps} pgyLevel="PGY-5" />);
      expect(screen.getByText('PGY-5 Requirements:')).toBeInTheDocument();
      // Falls back to PGY-2 description
      expect(
        screen.getByText(
          'Advanced residents (max 1:4 faculty:resident ratio)'
        )
      ).toBeInTheDocument();
    });
  });

  describe('Progressbar ARIA Attributes', () => {
    it('has role="progressbar"', () => {
      render(<SupervisionRatio {...defaultProps} />);
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('sets aria-valuenow to current ratio', () => {
      render(<SupervisionRatio {...defaultProps} current={2.5} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-valuenow',
        '2.5'
      );
    });

    it('sets aria-valuemin to 0', () => {
      render(<SupervisionRatio {...defaultProps} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-valuemin',
        '0'
      );
    });

    it('sets aria-valuemax to required ratio', () => {
      render(<SupervisionRatio {...defaultProps} required={4} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-valuemax',
        '4'
      );
    });

    it('sets descriptive aria-label on the progressbar', () => {
      render(<SupervisionRatio {...defaultProps} current={2.5} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-label',
        'Supervision ratio: 2.5 residents per faculty'
      );
    });
  });

  describe('Status ARIA Attributes', () => {
    it('has role="status" on the container', () => {
      render(<SupervisionRatio {...defaultProps} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has aria-live="polite" on the container', () => {
      render(<SupervisionRatio {...defaultProps} />);
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-live',
        'polite'
      );
    });

    it('includes status label in aria-label', () => {
      render(<SupervisionRatio {...defaultProps} current={1.0} />);
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        'Supervision ratio compliance: Adequate Supervision'
      );
    });
  });

  describe('Edge Cases', () => {
    it('caps progress bar width at 100%', () => {
      render(<SupervisionRatio {...defaultProps} current={6.0} required={4} />);
      const progressBar = screen.getByRole('progressbar');
      // 6/4 * 100 = 150%, but capped at 100%
      expect(progressBar).toHaveStyle({ width: '100%' });
    });

    it('handles zero current ratio', () => {
      render(<SupervisionRatio {...defaultProps} current={0} />);
      expect(screen.getByText('1:0.0 (max 1:4)')).toBeInTheDocument();
      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('Adequate Supervision')).toBeInTheDocument();
    });

    it('displays percentage above 100% in text but caps bar', () => {
      render(<SupervisionRatio {...defaultProps} current={5.0} required={4} />);
      // 5/4 * 100 = 125%
      expect(screen.getByText('125%')).toBeInTheDocument();
    });
  });
});
