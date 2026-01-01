import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScheduleLegend, ScheduleLegendInline, rotationLegendItems } from '../ScheduleLegend';

describe('ScheduleLegend', () => {
  describe('default rendering', () => {
    it('renders legend title', () => {
      render(<ScheduleLegend />);

      expect(screen.getByText('Activity Legend')).toBeInTheDocument();
    });

    it('renders all rotation types when not compact', () => {
      render(<ScheduleLegend compact={false} />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      expect(screen.getByText('Procedure')).toBeInTheDocument();
      expect(screen.getByText('Conference')).toBeInTheDocument();
      expect(screen.getByText('Elective')).toBeInTheDocument();
      expect(screen.getByText('Call')).toBeInTheDocument();
      expect(screen.getByText('Off')).toBeInTheDocument();
      expect(screen.getByText('Leave/Vacation')).toBeInTheDocument();
    });

    it('renders abbreviations for each rotation type', () => {
      render(<ScheduleLegend />);

      expect(screen.getByText('CLI')).toBeInTheDocument();
      expect(screen.getByText('INP')).toBeInTheDocument();
      expect(screen.getByText('PRO')).toBeInTheDocument();
      expect(screen.getByText('CON')).toBeInTheDocument();
      expect(screen.getByText('ELE')).toBeInTheDocument();
      expect(screen.getByText('CAL')).toBeInTheDocument();
      expect(screen.getByText('OFF')).toBeInTheDocument();
      expect(screen.getByText('LEA')).toBeInTheDocument();
    });

    it('applies correct color classes to badges', () => {
      const { container } = render(<ScheduleLegend />);

      const clinicBadge = screen.getByText('CLI').parentElement;
      expect(clinicBadge).toHaveClass('bg-blue-100', 'text-blue-800', 'border-blue-300');

      const inpatientBadge = screen.getByText('INP').parentElement;
      expect(inpatientBadge).toHaveClass('bg-purple-100', 'text-purple-800', 'border-purple-300');
    });
  });

  describe('compact mode', () => {
    it('shows only first 4 items initially when compact', () => {
      render(<ScheduleLegend compact={true} />);

      // Should show first 4
      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      expect(screen.getByText('Procedure')).toBeInTheDocument();
      expect(screen.getByText('Conference')).toBeInTheDocument();

      // Should not show remaining items
      expect(screen.queryByText('Elective')).not.toBeInTheDocument();
      expect(screen.queryByText('Call')).not.toBeInTheDocument();
    });

    it('shows expand/collapse button in compact mode', () => {
      render(<ScheduleLegend compact={true} />);

      expect(screen.getByLabelText('Expand legend')).toBeInTheDocument();
    });

    it('does not show expand/collapse button when not compact', () => {
      render(<ScheduleLegend compact={false} />);

      expect(screen.queryByLabelText('Expand legend')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Collapse legend')).not.toBeInTheDocument();
    });

    it('shows "more" link when collapsed', () => {
      render(<ScheduleLegend compact={true} />);

      const moreButton = screen.getByText(/\+\d+ more.../);
      expect(moreButton).toBeInTheDocument();
    });

    it('expands to show all items when expand button clicked', () => {
      render(<ScheduleLegend compact={true} />);

      const expandButton = screen.getByLabelText('Expand legend');
      fireEvent.click(expandButton);

      // Now all items should be visible
      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      expect(screen.getByText('Procedure')).toBeInTheDocument();
      expect(screen.getByText('Conference')).toBeInTheDocument();
      expect(screen.getByText('Elective')).toBeInTheDocument();
      expect(screen.getByText('Call')).toBeInTheDocument();
      expect(screen.getByText('Off')).toBeInTheDocument();
      expect(screen.getByText('Leave/Vacation')).toBeInTheDocument();
    });

    it('collapses when collapse button clicked', () => {
      render(<ScheduleLegend compact={true} />);

      // Expand first
      const expandButton = screen.getByLabelText('Expand legend');
      fireEvent.click(expandButton);

      // Then collapse
      const collapseButton = screen.getByLabelText('Collapse legend');
      fireEvent.click(collapseButton);

      // Should be back to showing only 4 items
      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.queryByText('Elective')).not.toBeInTheDocument();
    });

    it('expands when "more" link clicked', () => {
      render(<ScheduleLegend compact={true} />);

      const moreButton = screen.getByText(/\+\d+ more.../);
      fireEvent.click(moreButton);

      // Should show all items
      expect(screen.getByText('Elective')).toBeInTheDocument();
      expect(screen.getByText('Call')).toBeInTheDocument();
    });
  });

  describe('orientation', () => {
    it('renders horizontally by default', () => {
      const { container } = render(<ScheduleLegend />);

      const itemsContainer = container.querySelector('.flex-wrap');
      expect(itemsContainer).toBeInTheDocument();
      expect(itemsContainer).not.toHaveClass('flex-col');
    });

    it('renders vertically when orientation is vertical', () => {
      const { container } = render(<ScheduleLegend orientation="vertical" />);

      const itemsContainer = container.querySelector('.flex-col');
      expect(itemsContainer).toBeInTheDocument();
    });
  });

  describe('custom className', () => {
    it('applies custom className', () => {
      const { container } = render(<ScheduleLegend className="custom-legend" />);

      expect(container.firstChild).toHaveClass('custom-legend');
    });
  });

  describe('accessibility', () => {
    it('has proper button labels', () => {
      render(<ScheduleLegend compact={true} />);

      expect(screen.getByLabelText('Expand legend')).toBeInTheDocument();
    });

    it('toggles aria-label when expanding/collapsing', () => {
      render(<ScheduleLegend compact={true} />);

      const button = screen.getByLabelText('Expand legend');
      fireEvent.click(button);

      expect(screen.getByLabelText('Collapse legend')).toBeInTheDocument();
    });
  });

  describe('icon display', () => {
    it('shows info icon', () => {
      const { container } = render(<ScheduleLegend />);

      const infoIcon = container.querySelector('.lucide-info');
      expect(infoIcon).toBeInTheDocument();
    });
  });
});

describe('ScheduleLegendInline', () => {
  describe('rendering', () => {
    it('renders first 6 rotation types', () => {
      render(<ScheduleLegendInline />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      expect(screen.getByText('Procedure')).toBeInTheDocument();
      expect(screen.getByText('Conference')).toBeInTheDocument();
      expect(screen.getByText('Elective')).toBeInTheDocument();
      expect(screen.getByText('Call')).toBeInTheDocument();

      // Should not show items beyond first 6
      expect(screen.queryByText('Off')).not.toBeInTheDocument();
      expect(screen.queryByText('Leave/Vacation')).not.toBeInTheDocument();
    });

    it('renders color indicators', () => {
      const { container } = render(<ScheduleLegendInline />);

      const colorIndicators = container.querySelectorAll('.w-3.h-3.rounded.border');
      expect(colorIndicators.length).toBe(6);
    });

    it('applies horizontal flex layout', () => {
      const { container } = render(<ScheduleLegendInline />);

      expect(container.firstChild).toHaveClass('flex', 'flex-wrap', 'gap-3');
    });
  });

  describe('custom className', () => {
    it('applies custom className', () => {
      const { container } = render(<ScheduleLegendInline className="custom-inline" />);

      expect(container.firstChild).toHaveClass('custom-inline');
    });
  });

  describe('compact display', () => {
    it('uses compact color squares instead of full badges', () => {
      const { container } = render(<ScheduleLegendInline />);

      // Should have small color squares
      const colorSquares = container.querySelectorAll('.w-3.h-3');
      expect(colorSquares.length).toBeGreaterThan(0);
    });

    it('shows labels next to color indicators', () => {
      render(<ScheduleLegendInline />);

      const labels = screen.getAllByText(/^(Clinic|Inpatient|Procedure|Conference|Elective|Call)$/);
      expect(labels.length).toBe(6);
    });
  });
});

describe('rotationLegendItems export', () => {
  it('exports rotation legend items array', () => {
    expect(rotationLegendItems).toBeDefined();
    expect(Array.isArray(rotationLegendItems)).toBe(true);
    expect(rotationLegendItems.length).toBe(8);
  });

  it('has correct structure for each item', () => {
    rotationLegendItems.forEach((item) => {
      expect(item).toHaveProperty('type');
      expect(item).toHaveProperty('label');
      expect(item).toHaveProperty('color');
    });
  });
});
