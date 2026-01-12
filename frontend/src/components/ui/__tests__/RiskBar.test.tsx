/**
 * Tests for RiskBar Component
 * Component: Permission tier indicator bar
 */

import React from 'react';
import { renderWithProviders as render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { RiskBar, useRiskTierFromRoles } from '../RiskBar';
import { renderHook } from '@testing-library/react';

describe('RiskBar', () => {
  // Test: Tier 0 rendering
  describe('Tier 0 (Read-only)', () => {
    it('renders with green background for tier 0', () => {
      const { container } = render(<RiskBar tier={0} />);

      expect(container.querySelector('.bg-green-600')).toBeInTheDocument();
    });

    it('displays "Read-only" default label for tier 0', () => {
      render(<RiskBar tier={0} />);

      expect(screen.getByText('Read-only')).toBeInTheDocument();
    });

    it('has correct ARIA attributes', () => {
      render(<RiskBar tier={0} />);

      const bar = screen.getByRole('status');
      expect(bar).toHaveAttribute('aria-label', 'Permission level: Read-only');
    });
  });

  // Test: Tier 1 rendering
  describe('Tier 1 (Scoped Changes)', () => {
    it('renders with amber background for tier 1', () => {
      const { container } = render(<RiskBar tier={1} />);

      expect(container.querySelector('.bg-amber-500')).toBeInTheDocument();
    });

    it('displays "Scoped Changes" default label for tier 1', () => {
      render(<RiskBar tier={1} />);

      expect(screen.getByText('Scoped Changes')).toBeInTheDocument();
    });
  });

  // Test: Tier 2 rendering
  describe('Tier 2 (High Impact)', () => {
    it('renders with red background for tier 2', () => {
      const { container } = render(<RiskBar tier={2} />);

      expect(container.querySelector('.bg-red-600')).toBeInTheDocument();
    });

    it('displays "High Impact" default label for tier 2', () => {
      render(<RiskBar tier={2} />);

      expect(screen.getByText('High Impact')).toBeInTheDocument();
    });
  });

  // Test: Custom labels
  describe('Custom Labels', () => {
    it('accepts custom label prop', () => {
      render(<RiskBar tier={0} label="Viewer Mode" />);

      expect(screen.getByText('Viewer Mode')).toBeInTheDocument();
      expect(screen.queryByText('Read-only')).not.toBeInTheDocument();
    });

    it('uses custom label in ARIA label', () => {
      render(<RiskBar tier={1} label="Editor Mode" />);

      const bar = screen.getByRole('status');
      expect(bar).toHaveAttribute('aria-label', 'Permission level: Editor Mode');
    });
  });

  // Test: Tooltip functionality
  describe('Tooltip', () => {
    it('shows tooltip on hover', () => {
      render(<RiskBar tier={0} />);

      const bar = screen.getByRole('status');
      fireEvent.mouseEnter(bar);

      expect(screen.getByRole('tooltip')).toBeInTheDocument();
      expect(screen.getByText('You can view data but cannot make changes. Safe browsing mode.')).toBeInTheDocument();
    });

    it('hides tooltip on mouse leave', () => {
      render(<RiskBar tier={0} />);

      const bar = screen.getByRole('status');
      fireEvent.mouseEnter(bar);
      fireEvent.mouseLeave(bar);

      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
    });

    it('shows tooltip on focus', () => {
      render(<RiskBar tier={1} />);

      const bar = screen.getByRole('status');
      fireEvent.focus(bar);

      expect(screen.getByRole('tooltip')).toBeInTheDocument();
    });

    it('hides tooltip on blur', () => {
      render(<RiskBar tier={1} />);

      const bar = screen.getByRole('status');
      fireEvent.focus(bar);
      fireEvent.blur(bar);

      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
    });

    it('accepts custom tooltip content', () => {
      render(<RiskBar tier={2} tooltip="Custom warning message" />);

      const bar = screen.getByRole('status');
      fireEvent.mouseEnter(bar);

      expect(screen.getByText('Custom warning message')).toBeInTheDocument();
    });

    it('shows appropriate default tooltip for each tier', () => {
      const { rerender } = render(<RiskBar tier={0} />);
      let bar = screen.getByRole('status');
      fireEvent.mouseEnter(bar);
      expect(screen.getByText(/Safe browsing mode/)).toBeInTheDocument();
      fireEvent.mouseLeave(bar);

      rerender(<RiskBar tier={1} />);
      bar = screen.getByRole('status');
      fireEvent.mouseEnter(bar);
      expect(screen.getByText(/reversible changes/)).toBeInTheDocument();
      fireEvent.mouseLeave(bar);

      rerender(<RiskBar tier={2} />);
      bar = screen.getByRole('status');
      fireEvent.mouseEnter(bar);
      expect(screen.getByText(/destructive or system-wide/)).toBeInTheDocument();
    });
  });

  // Test: Styling and layout
  describe('Styling', () => {
    it('renders full width', () => {
      const { container } = render(<RiskBar tier={0} />);

      expect(container.querySelector('.w-full')).toBeInTheDocument();
    });

    it('has fixed height of 32px (h-8)', () => {
      const { container } = render(<RiskBar tier={0} />);

      expect(container.querySelector('.h-8')).toBeInTheDocument();
    });

    it('centers content', () => {
      const { container } = render(<RiskBar tier={0} />);

      expect(container.querySelector('.flex.items-center.justify-center')).toBeInTheDocument();
    });

    it('uses white text', () => {
      const { container } = render(<RiskBar tier={0} />);

      expect(container.querySelector('.text-white')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<RiskBar tier={0} className="custom-class" />);

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('is keyboard focusable', () => {
      render(<RiskBar tier={0} />);

      const bar = screen.getByRole('status');
      expect(bar).toHaveAttribute('tabIndex', '0');
    });
  });

  // Test: Accessibility
  describe('Accessibility', () => {
    it('has role="status" for screen readers', () => {
      render(<RiskBar tier={0} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('links tooltip with aria-describedby when visible', () => {
      render(<RiskBar tier={0} />);

      const bar = screen.getByRole('status');
      expect(bar).not.toHaveAttribute('aria-describedby');

      fireEvent.mouseEnter(bar);
      expect(bar).toHaveAttribute('aria-describedby');
    });
  });
});

describe('useRiskTierFromRoles', () => {
  it('returns tier 2 for admin role', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['admin']));
    expect(result.current).toBe(2);
  });

  it('returns tier 2 for coordinator role', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['coordinator']));
    expect(result.current).toBe(2);
  });

  it('returns tier 2 for chief role', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['chief']));
    expect(result.current).toBe(2);
  });

  it('returns tier 1 for faculty role', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['faculty']));
    expect(result.current).toBe(1);
  });

  it('returns tier 1 for resident role', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['resident']));
    expect(result.current).toBe(1);
  });

  it('returns tier 1 for clinical_staff role', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['clinical_staff']));
    expect(result.current).toBe(1);
  });

  it('returns tier 0 for unknown roles', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['viewer', 'guest']));
    expect(result.current).toBe(0);
  });

  it('returns tier 0 for empty roles array', () => {
    const { result } = renderHook(() => useRiskTierFromRoles([]));
    expect(result.current).toBe(0);
  });

  it('prioritizes highest tier when multiple roles present', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['resident', 'admin']));
    expect(result.current).toBe(2);
  });

  it('is case insensitive', () => {
    const { result } = renderHook(() => useRiskTierFromRoles(['ADMIN']));
    expect(result.current).toBe(2);
  });
});
