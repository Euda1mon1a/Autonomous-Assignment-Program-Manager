/**
 * Tests for N1ContingencyMap Component
 * Component: 28 - N-1 vulnerability detection
 */

import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { N1ContingencyMap } from '../N1ContingencyMap';

describe('N1ContingencyMap', () => {
  const mockPropsNormal = {
    criticalResources: [],
    vulnerableRotations: [],
    recoveryDistance: 0,
  };

  const mockPropsVulnerable = {
    criticalResources: ['Dr. Smith', 'Dr. Jones'],
    vulnerableRotations: ['Night Float', 'ICU Coverage'],
    recoveryDistance: 5,
  };

  const mockPropsHighVulnerability = {
    criticalResources: ['Dr. Smith', 'Dr. Jones', 'Dr. Brown', 'Dr. Davis'],
    vulnerableRotations: ['Night Float', 'ICU Coverage', 'ER Backup'],
    recoveryDistance: 12,
  };

  // Test 28.1: Render test - renders with default props
  describe('Rendering', () => {
    it('renders with no vulnerabilities', () => {
      render(<N1ContingencyMap {...mockPropsNormal} />);

      expect(screen.getByText('Low Vulnerability')).toBeInTheDocument();
      expect(screen.getByText(/good redundancy/)).toBeInTheDocument();
    });

    it('displays critical resource count', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('Critical Resources')).toBeInTheDocument();
    });

    it('displays vulnerable rotation count', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      expect(screen.getByText('Vulnerable Rotations')).toBeInTheDocument();
    });

    it('displays recovery distance', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('Recovery Distance')).toBeInTheDocument();
    });

    it('renders drill down button when callback provided', () => {
      const onDrillDown = jest.fn();
      render(<N1ContingencyMap {...mockPropsNormal} onDrillDown={onDrillDown} />);

      expect(screen.getByText('View Full Contingency Analysis')).toBeInTheDocument();
    });
  });

  // Test 28.2: Variant test - all severity levels
  describe('Severity Levels', () => {
    it('displays low vulnerability when no critical resources', () => {
      render(<N1ContingencyMap {...mockPropsNormal} />);

      expect(screen.getByText('Low Vulnerability')).toBeInTheDocument();
      expect(screen.getByRole('img', { name: 'Low Vulnerability' })).toHaveTextContent('✅');
    });

    it('displays medium vulnerability with 1-3 critical resources', () => {
      const props = {
        ...mockPropsVulnerable,
        criticalResources: ['Dr. Smith'],
      };
      render(<N1ContingencyMap {...props} />);

      expect(screen.getByText('Medium Vulnerability')).toBeInTheDocument();
      expect(screen.getByRole('img', { name: 'Medium Vulnerability' })).toHaveTextContent('⚠️');
    });

    it('displays high vulnerability with 4+ critical resources', () => {
      render(<N1ContingencyMap {...mockPropsHighVulnerability} />);

      expect(screen.getByText('High Vulnerability')).toBeInTheDocument();
      expect(screen.getByRole('img', { name: 'High Vulnerability' })).toHaveTextContent('🚨');
      expect(screen.getByText(/Multiple single points of failure/)).toBeInTheDocument();
    });

    it('shows recommendations for vulnerable systems', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      expect(screen.getByText(/Recommended Mitigations/)).toBeInTheDocument();
      expect(screen.getByText(/Cross-train personnel/)).toBeInTheDocument();
    });

    it('does not show recommendations for healthy systems', () => {
      render(<N1ContingencyMap {...mockPropsNormal} />);

      expect(screen.queryByText(/Recommended Mitigations/)).not.toBeInTheDocument();
    });
  });

  // Test 28.3: Accessibility and interaction
  describe('Accessibility and Interaction', () => {
    it('critical resource buttons are keyboard accessible', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      const buttons = screen.getAllByRole('button').filter(btn =>
        btn.textContent?.includes('Dr.')
      );

      buttons[0].focus();
      expect(buttons[0]).toHaveFocus();
    });

    it('expands critical resource details on click', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      const resourceButton = screen.getByText('Dr. Smith').closest('button');
      expect(resourceButton).toBeInTheDocument();

      fireEvent.click(resourceButton!);

      expect(screen.getByText(/Impact:/)).toBeInTheDocument();
      expect(screen.getByText(/Removing this resource would cause schedule failure/)).toBeInTheDocument();
    });

    it('toggles resource details on multiple clicks', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      const resourceButton = screen.getByText('Dr. Smith').closest('button');

      // Click to expand
      fireEvent.click(resourceButton!);
      expect(screen.getByText(/Impact:/)).toBeInTheDocument();

      // Click to collapse
      fireEvent.click(resourceButton!);
      expect(screen.queryByText(/Impact:/)).not.toBeInTheDocument();
    });

    it('drill down button is accessible', () => {
      const onDrillDown = jest.fn();
      render(<N1ContingencyMap {...mockPropsVulnerable} onDrillDown={onDrillDown} />);

      const button = screen.getByText('View Full Contingency Analysis');
      fireEvent.click(button);

      expect(onDrillDown).toHaveBeenCalledTimes(1);
    });

    it('displays SPOF badge for critical resources', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      const badges = screen.getAllByText('SPOF');
      expect(badges).toHaveLength(2); // One for each critical resource
    });
  });

  // Test 28.4: Edge cases
  describe('Edge Cases', () => {
    it('handles zero recovery distance', () => {
      const props = { ...mockPropsNormal, recoveryDistance: 0 };
      render(<N1ContingencyMap {...props} />);

      expect(screen.getByText(/System can auto-recover/)).toBeInTheDocument();
    });

    it('handles low recovery distance (1-3)', () => {
      const props = { ...mockPropsVulnerable, recoveryDistance: 2 };
      render(<N1ContingencyMap {...props} />);

      expect(screen.getByText(/Minor adjustments needed/)).toBeInTheDocument();
    });

    it('handles moderate recovery distance (4-10)', () => {
      const props = { ...mockPropsVulnerable, recoveryDistance: 7 };
      render(<N1ContingencyMap {...props} />);

      expect(screen.getByText(/Moderate rescheduling required/)).toBeInTheDocument();
    });

    it('handles high recovery distance (>10)', () => {
      const props = { ...mockPropsVulnerable, recoveryDistance: 15 };
      render(<N1ContingencyMap {...props} />);

      expect(screen.getByText(/Extensive rescheduling required/)).toBeInTheDocument();
    });

    it('displays all critical resources', () => {
      render(<N1ContingencyMap {...mockPropsHighVulnerability} />);

      expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Jones')).toBeInTheDocument();
      expect(screen.getByText('Dr. Brown')).toBeInTheDocument();
      expect(screen.getByText('Dr. Davis')).toBeInTheDocument();
    });

    it('displays all vulnerable rotations', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      expect(screen.getByText('Night Float')).toBeInTheDocument();
      expect(screen.getByText('ICU Coverage')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <N1ContingencyMap {...mockPropsNormal} className="custom-class" />
      );

      expect(container.querySelector('.n1-contingency-map.custom-class')).toBeInTheDocument();
    });

    it('displays framework explanation', () => {
      render(<N1ContingencyMap {...mockPropsNormal} />);

      expect(screen.getByText(/N-1 Contingency/)).toBeInTheDocument();
      expect(screen.getByText(/power grid reliability engineering/)).toBeInTheDocument();
    });

    it('shows correct plural/singular for recovery distance', () => {
      const { rerender } = render(
        <N1ContingencyMap {...mockPropsNormal} recoveryDistance={1} />
      );

      expect(screen.getByText(/1 edit required/)).toBeInTheDocument();

      rerender(<N1ContingencyMap {...mockPropsNormal} recoveryDistance={5} />);

      expect(screen.getByText(/5 edits required/)).toBeInTheDocument();
    });

    it('hides critical resources section when empty', () => {
      render(<N1ContingencyMap {...mockPropsNormal} />);

      expect(screen.queryByText('Critical Resources (Single Points of Failure)')).not.toBeInTheDocument();
    });

    it('hides vulnerable rotations section when empty', () => {
      render(<N1ContingencyMap {...mockPropsNormal} />);

      expect(screen.queryByText(/Vulnerable Rotations/)).not.toBeInTheDocument();
    });

    it('shows all recommendation items', () => {
      render(<N1ContingencyMap {...mockPropsVulnerable} />);

      expect(screen.getByText(/Cross-train personnel/)).toBeInTheDocument();
      expect(screen.getByText(/Develop contingency schedules/)).toBeInTheDocument();
      expect(screen.getByText(/Consider hiring additional staff/)).toBeInTheDocument();
      expect(screen.getByText(/rotation sharing agreements/)).toBeInTheDocument();
    });
  });
});
