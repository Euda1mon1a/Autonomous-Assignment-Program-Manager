/**
 * Tests for WorkHourGauge Component
 * Component: compliance/WorkHourGauge - Visual gauge for work hour tracking (80-hour ACGME limit)
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { WorkHourGauge } from '../WorkHourGauge';

describe('WorkHourGauge', () => {
  const defaultProps = {
    label: 'Weekly Hours',
    hours: 40,
    maxHours: 80,
  };

  describe('Rendering', () => {
    it('renders with required props', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByText('Weekly Hours')).toBeInTheDocument();
    });

    it('displays hours and max hours', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByText('40.0h / 80h')).toBeInTheDocument();
    });

    it('displays percentage', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <WorkHourGauge {...defaultProps} className="custom-class" />
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Green State (Within Limits)', () => {
    it('shows "Within Limits" when hours are below warningThreshold', () => {
      render(<WorkHourGauge {...defaultProps} hours={40} />);
      expect(screen.getByText('Within Limits')).toBeInTheDocument();
    });

    it('applies green text color', () => {
      render(<WorkHourGauge {...defaultProps} hours={40} />);
      const hoursDisplay = screen.getByText('40.0h / 80h');
      expect(hoursDisplay).toHaveClass('text-green-700');
    });

    it('does not show warning or violation indicators', () => {
      render(<WorkHourGauge {...defaultProps} hours={40} />);
      expect(screen.queryByText('Approaching Limit')).not.toBeInTheDocument();
      expect(screen.queryByText('ACGME Violation')).not.toBeInTheDocument();
    });
  });

  describe('Yellow State (Approaching Limit)', () => {
    it('shows "Approaching Limit" when hours >= warningThreshold but < maxHours', () => {
      render(<WorkHourGauge {...defaultProps} hours={75} />);
      expect(screen.getByText('Approaching Limit')).toBeInTheDocument();
    });

    it('applies yellow text color', () => {
      render(<WorkHourGauge {...defaultProps} hours={75} />);
      const hoursDisplay = screen.getByText('75.0h / 80h');
      expect(hoursDisplay).toHaveClass('text-yellow-700');
    });

    it('shows warning at exactly the warningThreshold (default 70)', () => {
      render(<WorkHourGauge {...defaultProps} hours={70} />);
      expect(screen.getByText('Approaching Limit')).toBeInTheDocument();
    });

    it('does not show violation indicator', () => {
      render(<WorkHourGauge {...defaultProps} hours={75} />);
      expect(screen.queryByText('ACGME Violation')).not.toBeInTheDocument();
    });
  });

  describe('Red State (ACGME Violation)', () => {
    it('shows "ACGME Violation" when hours >= maxHours', () => {
      render(<WorkHourGauge {...defaultProps} hours={80} />);
      expect(screen.getByText('ACGME Violation')).toBeInTheDocument();
    });

    it('applies red text color', () => {
      render(<WorkHourGauge {...defaultProps} hours={85} />);
      const hoursDisplay = screen.getByText('85.0h / 80h');
      expect(hoursDisplay).toHaveClass('text-red-700');
    });

    it('shows violation when hours exceed maxHours', () => {
      render(<WorkHourGauge {...defaultProps} hours={90} />);
      expect(screen.getByText('ACGME Violation')).toBeInTheDocument();
    });

    it('does not show warning or within limits', () => {
      render(<WorkHourGauge {...defaultProps} hours={85} />);
      expect(screen.queryByText('Approaching Limit')).not.toBeInTheDocument();
      expect(screen.queryByText('Within Limits')).not.toBeInTheDocument();
    });
  });

  describe('Percentage Capping', () => {
    it('caps percentage at 100% when hours exceed maxHours', () => {
      render(<WorkHourGauge {...defaultProps} hours={100} />);
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('caps the progress bar width at 100%', () => {
      render(<WorkHourGauge {...defaultProps} hours={120} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveStyle({ width: '100%' });
    });

    it('displays correct percentage below 100%', () => {
      render(<WorkHourGauge {...defaultProps} hours={60} />);
      expect(screen.getByText('75%')).toBeInTheDocument();
    });
  });

  describe('Custom warningThreshold', () => {
    it('uses custom warningThreshold for state determination', () => {
      render(
        <WorkHourGauge {...defaultProps} hours={55} warningThreshold={50} />
      );
      expect(screen.getByText('Approaching Limit')).toBeInTheDocument();
    });

    it('shows green when below custom warningThreshold', () => {
      render(
        <WorkHourGauge {...defaultProps} hours={45} warningThreshold={50} />
      );
      expect(screen.getByText('Within Limits')).toBeInTheDocument();
    });

    it('shows warning at exactly the custom warningThreshold', () => {
      render(
        <WorkHourGauge {...defaultProps} hours={50} warningThreshold={50} />
      );
      expect(screen.getByText('Approaching Limit')).toBeInTheDocument();
    });
  });

  describe('Progressbar ARIA Attributes', () => {
    it('has role="progressbar"', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('sets aria-valuenow to current hours', () => {
      render(<WorkHourGauge {...defaultProps} hours={55} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-valuenow',
        '55'
      );
    });

    it('sets aria-valuemin to 0', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-valuemin',
        '0'
      );
    });

    it('sets aria-valuemax to maxHours', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-valuemax',
        '80'
      );
    });

    it('sets descriptive aria-label on the progressbar', () => {
      render(<WorkHourGauge {...defaultProps} hours={55} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute(
        'aria-label',
        'Weekly Hours: 55 hours out of 80 hours'
      );
    });
  });

  describe('Region and Status ARIA', () => {
    it('wraps gauge in a region with aria-label', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByRole('region')).toHaveAttribute(
        'aria-label',
        'Weekly Hours work hour gauge'
      );
    });

    it('has a status area with aria-live="polite"', () => {
      render(<WorkHourGauge {...defaultProps} />);
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-live',
        'polite'
      );
    });
  });

  describe('Threshold Marker', () => {
    it('renders threshold marker by default', () => {
      const { container } = render(<WorkHourGauge {...defaultProps} />);
      // The threshold marker is a div with specific class and style
      const marker = container.querySelector('.bg-gray-400');
      expect(marker).toBeInTheDocument();
    });

    it('hides threshold marker when showThreshold is false', () => {
      const { container } = render(
        <WorkHourGauge {...defaultProps} showThreshold={false} />
      );
      const marker = container.querySelector('.bg-gray-400');
      expect(marker).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero hours', () => {
      render(<WorkHourGauge {...defaultProps} hours={0} />);
      expect(screen.getByText('0.0h / 80h')).toBeInTheDocument();
      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('Within Limits')).toBeInTheDocument();
    });

    it('handles decimal hours', () => {
      render(<WorkHourGauge {...defaultProps} hours={67.5} />);
      expect(screen.getByText('67.5h / 80h')).toBeInTheDocument();
    });
  });
});
