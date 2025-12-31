/**
 * Tests for UtilizationGauge Component
 * Component: 26 - 80% threshold gauge
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { UtilizationGauge } from '../UtilizationGauge';

describe('UtilizationGauge', () => {
  // Test 26.1: Render test - renders with default props
  describe('Rendering', () => {
    it('renders with default props', () => {
      render(<UtilizationGauge current={60} />);

      expect(screen.getByText('60.0%')).toBeInTheDocument();
      expect(screen.getByText('of 80% threshold')).toBeInTheDocument();
      expect(screen.getByText(/Within Safe Limits/)).toBeInTheDocument();
    });

    it('displays utilization percentage correctly', () => {
      render(<UtilizationGauge current={45.7} />);

      expect(screen.getByText('45.7%')).toBeInTheDocument();
    });

    it('renders drill down button when callback provided', () => {
      const onDrillDown = jest.fn();
      render(<UtilizationGauge current={50} onDrillDown={onDrillDown} />);

      expect(screen.getByText('View Detailed Utilization Breakdown')).toBeInTheDocument();
    });

    it('does not render drill down button when callback not provided', () => {
      render(<UtilizationGauge current={50} />);

      expect(screen.queryByText('View Detailed Utilization Breakdown')).not.toBeInTheDocument();
    });
  });

  // Test 26.2: Variant test - all status levels render correctly
  describe('Status Levels', () => {
    it('displays green status when utilization is safe (< 72%)', () => {
      render(<UtilizationGauge current={60} threshold={80} />);

      expect(screen.getByText(/Within Safe Limits/)).toBeInTheDocument();
      expect(screen.getByText('Very Low')).toBeInTheDocument(); // Cascade risk
    });

    it('displays yellow warning when approaching threshold (72-79%)', () => {
      render(<UtilizationGauge current={75} threshold={80} />);

      expect(screen.getByText(/Approaching Threshold/)).toBeInTheDocument();
      expect(screen.getByText('Moderate')).toBeInTheDocument(); // Cascade risk
    });

    it('displays red critical when above threshold (>= 80%)', () => {
      render(<UtilizationGauge current={85} threshold={80} />);

      expect(screen.getByText(/Above Threshold/)).toBeInTheDocument();
      expect(screen.getByText(/Cascade failure risk is elevated/)).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument(); // Cascade risk
    });

    it('displays critical risk when utilization >= 90%', () => {
      render(<UtilizationGauge current={92} />);

      expect(screen.getByText('Critical')).toBeInTheDocument();
    });

    it('respects custom threshold', () => {
      render(<UtilizationGauge current={60} threshold={50} />);

      expect(screen.getByText(/Above Threshold/)).toBeInTheDocument();
      expect(screen.getByText('of 50% threshold')).toBeInTheDocument();
    });
  });

  // Test 26.3: Accessibility test
  describe('Accessibility', () => {
    it('has proper ARIA labels on SVG elements', () => {
      const { container } = render(<UtilizationGauge current={75} />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('drill down button has proper focus management', () => {
      const onDrillDown = jest.fn();
      render(<UtilizationGauge current={50} onDrillDown={onDrillDown} />);

      const button = screen.getByText('View Detailed Utilization Breakdown');
      button.focus();

      expect(button).toHaveFocus();
    });

    it('drill down button responds to click', () => {
      const onDrillDown = jest.fn();
      render(<UtilizationGauge current={50} onDrillDown={onDrillDown} />);

      fireEvent.click(screen.getByText('View Detailed Utilization Breakdown'));
      expect(onDrillDown).toHaveBeenCalledTimes(1);
    });

    it('drill down button responds to Enter key', () => {
      const onDrillDown = jest.fn();
      render(<UtilizationGauge current={50} onDrillDown={onDrillDown} />);

      const button = screen.getByText('View Detailed Utilization Breakdown');
      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });

      expect(onDrillDown).toHaveBeenCalledTimes(1);
    });
  });

  // Test 26.4: Edge cases
  describe('Edge Cases', () => {
    it('handles 0% utilization', () => {
      render(<UtilizationGauge current={0} />);

      expect(screen.getByText('0.0%')).toBeInTheDocument();
      expect(screen.getByText('Very Low')).toBeInTheDocument();
    });

    it('handles 100% utilization', () => {
      render(<UtilizationGauge current={100} />);

      expect(screen.getByText('100.0%')).toBeInTheDocument();
      expect(screen.getByText('Critical')).toBeInTheDocument();
    });

    it('handles exact threshold value', () => {
      render(<UtilizationGauge current={80} threshold={80} />);

      expect(screen.getByText(/Above Threshold/)).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('calculates safety margin correctly', () => {
      render(<UtilizationGauge current={65} threshold={80} />);

      expect(screen.getByText('15.0%')).toBeInTheDocument(); // 80 - 65
    });

    it('shows 0% safety margin when above threshold', () => {
      render(<UtilizationGauge current={85} threshold={80} />);

      expect(screen.getByText('0.0%')).toBeInTheDocument(); // max(0, 80 - 85)
    });

    it('renders with all trend variants', () => {
      const { rerender } = render(<UtilizationGauge current={50} trend="increasing" />);
      expect(screen.getByText('Increasing')).toBeInTheDocument();

      rerender(<UtilizationGauge current={50} trend="stable" />);
      expect(screen.getByText('Stable')).toBeInTheDocument();

      rerender(<UtilizationGauge current={50} trend="decreasing" />);
      expect(screen.getByText('Decreasing')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<UtilizationGauge current={50} className="custom-class" />);

      expect(container.querySelector('.utilization-gauge.custom-class')).toBeInTheDocument();
    });

    it('displays framework explanation', () => {
      render(<UtilizationGauge current={50} />);

      expect(screen.getByText(/80% Utilization Threshold/)).toBeInTheDocument();
      expect(screen.getByText(/queuing theory/)).toBeInTheDocument();
    });
  });

  describe('Cascade Risk Calculation', () => {
    it('correctly categorizes cascade risk levels', () => {
      const { rerender } = render(<UtilizationGauge current={55} />);
      expect(screen.getByText('Very Low')).toBeInTheDocument();

      rerender(<UtilizationGauge current={65} />);
      expect(screen.getByText('Low')).toBeInTheDocument();

      rerender(<UtilizationGauge current={75} />);
      expect(screen.getByText('Moderate')).toBeInTheDocument();

      rerender(<UtilizationGauge current={85} />);
      expect(screen.getByText('High')).toBeInTheDocument();

      rerender(<UtilizationGauge current={95} />);
      expect(screen.getByText('Critical')).toBeInTheDocument();
    });
  });
});
