/**
 * Tests for BurnoutRtDisplay Component
 * Component: 27 - Rt reproduction number display
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { BurnoutRtDisplay } from '../BurnoutRtDisplay';

describe('BurnoutRtDisplay', () => {
  // Test 27.1: Render test - renders with default props
  describe('Rendering', () => {
    it('renders with default props', () => {
      render(<BurnoutRtDisplay value={0.8} />);

      expect(screen.getByText(/Rt = 0.80/)).toBeInTheDocument();
      expect(screen.getByText('Burnout Contained')).toBeInTheDocument();
    });

    it('displays Rt value with 2 decimal places', () => {
      render(<BurnoutRtDisplay value={1.234} />);

      expect(screen.getByText(/Rt = 1.23/)).toBeInTheDocument();
    });

    it('renders drill down button when callback provided', () => {
      const onDrillDown = jest.fn();
      render(<BurnoutRtDisplay value={0.5} onDrillDown={onDrillDown} />);

      expect(screen.getByText('View Burnout Transmission Network')).toBeInTheDocument();
    });

    it('does not render drill down button when callback not provided', () => {
      render(<BurnoutRtDisplay value={0.5} />);

      expect(screen.queryByText('View Burnout Transmission Network')).not.toBeInTheDocument();
    });

    it('displays trend indicator', () => {
      render(<BurnoutRtDisplay value={0.8} trend="decreasing" />);

      expect(screen.getByText('decreasing')).toBeInTheDocument();
    });
  });

  // Test 27.2: Variant test - all status levels render correctly
  describe('Status Levels', () => {
    it('displays contained status when Rt < 0.9', () => {
      render(<BurnoutRtDisplay value={0.7} threshold={1.0} />);

      expect(screen.getByText('Burnout Contained')).toBeInTheDocument();
      expect(screen.getByText(/Rt < 1: Burnout is declining/)).toBeInTheDocument();
      expect(screen.getByRole('img', { name: 'Burnout Contained' })).toHaveTextContent('🟢');
    });

    it('displays warning status when Rt is 0.9-1.0', () => {
      render(<BurnoutRtDisplay value={0.95} threshold={1.0} />);

      expect(screen.getByText('Approaching Epidemic')).toBeInTheDocument();
      expect(screen.getByText(/approaching critical transition point/)).toBeInTheDocument();
      expect(screen.getByRole('img', { name: 'Approaching Epidemic' })).toHaveTextContent('🟡');
    });

    it('displays epidemic status when Rt > threshold', () => {
      render(<BurnoutRtDisplay value={1.5} threshold={1.0} />);

      expect(screen.getByText('Burnout Spreading')).toBeInTheDocument();
      expect(screen.getByText(/Burnout is spreading exponentially/)).toBeInTheDocument();
      expect(screen.getByRole('img', { name: 'Burnout Spreading' })).toHaveTextContent('🔴');
    });

    it('respects custom threshold', () => {
      render(<BurnoutRtDisplay value={0.8} threshold={0.7} />);

      expect(screen.getByText('Burnout Spreading')).toBeInTheDocument();
    });

    it('displays all trend variants correctly', () => {
      const { rerender } = render(<BurnoutRtDisplay value={1.0} trend="increasing" />);
      expect(screen.getByText('increasing')).toBeInTheDocument();

      rerender(<BurnoutRtDisplay value={1.0} trend="stable" />);
      expect(screen.getByText('stable')).toBeInTheDocument();

      rerender(<BurnoutRtDisplay value={1.0} trend="decreasing" />);
      expect(screen.getByText('decreasing')).toBeInTheDocument();
    });
  });

  // Test 27.3: Accessibility test
  describe('Accessibility', () => {
    it('has proper ARIA labels for status icons', () => {
      render(<BurnoutRtDisplay value={0.5} />);

      const icon = screen.getByRole('img', { name: 'Burnout Contained' });
      expect(icon).toBeInTheDocument();
    });

    it('drill down button has proper focus management', () => {
      const onDrillDown = jest.fn();
      render(<BurnoutRtDisplay value={0.8} onDrillDown={onDrillDown} />);

      const button = screen.getByText('View Burnout Transmission Network');
      button.focus();

      expect(button).toHaveFocus();
    });

    it('drill down button responds to click', () => {
      const onDrillDown = jest.fn();
      render(<BurnoutRtDisplay value={0.8} onDrillDown={onDrillDown} />);

      fireEvent.click(screen.getByText('View Burnout Transmission Network'));
      expect(onDrillDown).toHaveBeenCalledTimes(1);
    });

    it('has semantic heading for status label', () => {
      render(<BurnoutRtDisplay value={0.8} />);

      const heading = screen.getByRole('heading', { level: 3 });
      expect(heading).toHaveTextContent('Rt = 0.80');
    });
  });

  // Test 27.4: Edge cases and calculations
  describe('Edge Cases and Calculations', () => {
    it('handles Rt = 0', () => {
      render(<BurnoutRtDisplay value={0} />);

      expect(screen.getByText(/Rt = 0.00/)).toBeInTheDocument();
      expect(screen.getByText('Burnout Contained')).toBeInTheDocument();
    });

    it('handles Rt = 1.0 (equilibrium)', () => {
      render(<BurnoutRtDisplay value={1.0} />);

      expect(screen.getByText(/N\/A \(equilibrium\)/)).toBeInTheDocument();
    });

    it('calculates doubling time for Rt > 1', () => {
      render(<BurnoutRtDisplay value={1.5} />);

      // Should show "Doubles every X days"
      expect(screen.getByText(/Doubles every \d+ days/)).toBeInTheDocument();
    });

    it('calculates halving time for Rt < 1', () => {
      render(<BurnoutRtDisplay value={0.5} />);

      // Should show "Halves every X days"
      expect(screen.getByText(/Halves every \d+ days/)).toBeInTheDocument();
    });

    it('handles very high Rt values', () => {
      render(<BurnoutRtDisplay value={5.0} />);

      expect(screen.getByText(/Rt = 5.00/)).toBeInTheDocument();
      expect(screen.getByText('Burnout Spreading')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<BurnoutRtDisplay value={0.8} className="custom-class" />);

      expect(container.querySelector('.burnout-rt-display.custom-class')).toBeInTheDocument();
    });

    it('displays interpretation guide', () => {
      render(<BurnoutRtDisplay value={0.8} />);

      expect(screen.getByText('Interpretation Guide')).toBeInTheDocument();
      expect(screen.getByText(/Rt > 1:/)).toBeInTheDocument();
      expect(screen.getByText(/Rt = 1:/)).toBeInTheDocument();
      expect(screen.getByText(/Rt < 1:/)).toBeInTheDocument();
    });

    it('displays framework explanation', () => {
      render(<BurnoutRtDisplay value={0.8} />);

      expect(screen.getByText(/Burnout Epidemiology/)).toBeInTheDocument();
      expect(screen.getByText(/SIR \(Susceptible-Infected-Recovered\) model/)).toBeInTheDocument();
    });

    it('displays legend with all states', () => {
      render(<BurnoutRtDisplay value={0.8} />);

      expect(screen.getByText('Declining')).toBeInTheDocument();
      expect(screen.getByText('Equilibrium')).toBeInTheDocument();
      expect(screen.getByText('Spreading')).toBeInTheDocument();
    });

    it('positions gauge indicator correctly for different Rt values', () => {
      const { container, rerender } = render(<BurnoutRtDisplay value={0.5} />);

      // Value at 0.5 should be at 25% (0.5/2 * 100)
      let indicator = container.querySelector('.absolute.top-0.bottom-0.w-1');
      expect(indicator).toHaveStyle({ left: '25%' });

      rerender(<BurnoutRtDisplay value={1.0} />);
      indicator = container.querySelector('.absolute.top-0.bottom-0.w-1');
      expect(indicator).toHaveStyle({ left: '50%' });

      rerender(<BurnoutRtDisplay value={2.0} />);
      indicator = container.querySelector('.absolute.top-0.bottom-0.w-1');
      expect(indicator).toHaveStyle({ left: '100%' });
    });
  });
});
