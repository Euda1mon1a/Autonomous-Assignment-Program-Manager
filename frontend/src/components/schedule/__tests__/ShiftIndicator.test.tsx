import React from 'react';
import { render, screen } from '@testing-library/react';
import { ShiftIndicator } from '../ShiftIndicator';

describe('ShiftIndicator', () => {
  describe('shift types', () => {
    it('renders AM shift', () => {
      render(<ShiftIndicator shift="AM" />);

      expect(screen.getByText('AM')).toBeInTheDocument();
      expect(screen.getByText('☀️')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'AM shift');
    });

    it('renders PM shift', () => {
      render(<ShiftIndicator shift="PM" />);

      expect(screen.getByText('PM')).toBeInTheDocument();
      expect(screen.getByText('🌤️')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'PM shift');
    });

    it('renders Night shift', () => {
      render(<ShiftIndicator shift="Night" />);

      expect(screen.getByText('Night')).toBeInTheDocument();
      expect(screen.getByText('🌙')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Night shift');
    });

    it('renders All-Day shift', () => {
      render(<ShiftIndicator shift="All-Day" />);

      expect(screen.getByText('All Day')).toBeInTheDocument();
      expect(screen.getByText('⏰')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'All Day shift');
    });
  });

  describe('variant: badge (default)', () => {
    it('renders badge variant with icon and label', () => {
      render(<ShiftIndicator shift="AM" variant="badge" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('inline-flex', 'items-center', 'gap-1', 'rounded-full');
      expect(screen.getByText('AM')).toBeInTheDocument();
      expect(screen.getByText('☀️')).toBeInTheDocument();
    });

    it('applies AM colors (yellow)', () => {
      render(<ShiftIndicator shift="AM" variant="badge" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('applies PM colors (orange)', () => {
      render(<ShiftIndicator shift="PM" variant="badge" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-orange-100', 'text-orange-800');
    });

    it('applies Night colors (indigo)', () => {
      render(<ShiftIndicator shift="Night" variant="badge" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-indigo-100', 'text-indigo-800');
    });

    it('applies All-Day colors (purple)', () => {
      render(<ShiftIndicator shift="All-Day" variant="badge" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-purple-100', 'text-purple-800');
    });
  });

  describe('variant: icon', () => {
    it('renders only icon without label', () => {
      render(<ShiftIndicator shift="AM" variant="icon" />);

      expect(screen.getByText('☀️')).toBeInTheDocument();
      expect(screen.queryByText('AM')).not.toBeInTheDocument();
    });

    it('has proper accessibility label', () => {
      render(<ShiftIndicator shift="PM" variant="icon" />);

      const icon = screen.getByLabelText('PM shift');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('variant: full', () => {
    it('renders full variant with border', () => {
      render(<ShiftIndicator shift="AM" variant="full" />);

      const container = screen.getByRole('status');
      expect(container).toHaveClass('border-2', 'rounded-lg');
      expect(screen.getByText('AM Shift')).toBeInTheDocument();
    });

    it('applies border color for AM', () => {
      render(<ShiftIndicator shift="AM" variant="full" />);

      const container = screen.getByRole('status');
      expect(container).toHaveClass('border-yellow-300');
    });

    it('applies border color for PM', () => {
      render(<ShiftIndicator shift="PM" variant="full" />);

      const container = screen.getByRole('status');
      expect(container).toHaveClass('border-orange-300');
    });

    it('applies border color for Night', () => {
      render(<ShiftIndicator shift="Night" variant="full" />);

      const container = screen.getByRole('status');
      expect(container).toHaveClass('border-indigo-300');
    });
  });

  describe('size variants', () => {
    it('renders small size for badge', () => {
      render(<ShiftIndicator shift="AM" size="sm" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('text-xs', 'px-1.5', 'py-0.5');
    });

    it('renders medium size (default) for badge', () => {
      render(<ShiftIndicator shift="AM" size="md" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('text-sm', 'px-2', 'py-1');
    });

    it('renders large size for badge', () => {
      render(<ShiftIndicator shift="AM" size="lg" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('text-base', 'px-3', 'py-1.5');
    });

    it('applies correct icon size for small', () => {
      render(<ShiftIndicator shift="AM" size="sm" variant="icon" />);

      const icon = screen.getByLabelText('AM shift');
      expect(icon).toHaveClass('text-sm');
    });

    it('applies correct icon size for medium', () => {
      render(<ShiftIndicator shift="AM" size="md" variant="icon" />);

      const icon = screen.getByLabelText('AM shift');
      expect(icon).toHaveClass('text-base');
    });

    it('applies correct icon size for large', () => {
      render(<ShiftIndicator shift="AM" size="lg" variant="icon" />);

      const icon = screen.getByLabelText('AM shift');
      expect(icon).toHaveClass('text-xl');
    });
  });

  describe('custom className', () => {
    it('applies custom className to badge variant', () => {
      render(<ShiftIndicator shift="AM" variant="badge" className="custom-class" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('custom-class');
    });

    it('applies custom className to icon variant', () => {
      render(<ShiftIndicator shift="AM" variant="icon" className="custom-class" />);

      const icon = screen.getByLabelText('AM shift');
      expect(icon).toHaveClass('custom-class');
    });

    it('applies custom className to full variant', () => {
      render(<ShiftIndicator shift="AM" variant="full" className="custom-class" />);

      const container = screen.getByRole('status');
      expect(container).toHaveClass('custom-class');
    });
  });

  describe('accessibility', () => {
    it('has proper role and aria-label for badge', () => {
      render(<ShiftIndicator shift="PM" variant="badge" />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'PM shift');
    });

    it('has proper role and aria-label for icon', () => {
      render(<ShiftIndicator shift="Night" variant="icon" />);

      expect(screen.getByLabelText('Night shift')).toBeInTheDocument();
    });

    it('has proper role and aria-label for full', () => {
      render(<ShiftIndicator shift="All-Day" variant="full" />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'All Day shift');
    });

    it('marks icon as decorative in badge variant', () => {
      render(<ShiftIndicator shift="AM" variant="badge" />);

      const icon = screen.getByText('☀️');
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });

    it('marks icon as decorative in full variant', () => {
      render(<ShiftIndicator shift="PM" variant="full" />);

      const icon = screen.getByText('🌤️');
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });
  });
});
