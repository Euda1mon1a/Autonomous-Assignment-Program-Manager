/**
 * Tests for StaffingSummary Component
 *
 * Tests for the staffing summary display component showing staff counts
 */

import { render, screen } from '@testing-library/react';
import { StaffingSummary } from '@/features/daily-manifest/StaffingSummary';

describe('StaffingSummary', () => {
  // ============================================================================
  // Compact Mode Tests
  // ============================================================================

  describe('Compact Mode', () => {
    it('should render compact summary with all counts', () => {
      render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
          fellows={1}
          compact
        />
      );

      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('6R')).toBeInTheDocument();
      expect(screen.getByText('3F')).toBeInTheDocument();
      expect(screen.getByText('1Fe')).toBeInTheDocument();
    });

    it('should not show fellows in compact mode when count is 0', () => {
      render(
        <StaffingSummary
          total={9}
          residents={6}
          faculty={3}
          fellows={0}
          compact
        />
      );

      expect(screen.getByText('6R')).toBeInTheDocument();
      expect(screen.getByText('3F')).toBeInTheDocument();
      expect(screen.queryByText(/Fe/)).not.toBeInTheDocument();
    });

    it('should not show fellows when not provided in compact mode', () => {
      render(
        <StaffingSummary
          total={9}
          residents={6}
          faculty={3}
          compact
        />
      );

      expect(screen.getByText('6R')).toBeInTheDocument();
      expect(screen.getByText('3F')).toBeInTheDocument();
      expect(screen.queryByText(/Fe/)).not.toBeInTheDocument();
    });

    it('should apply compact styling classes', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
          compact
        />
      );

      const compactContainer = container.querySelector('.text-xs');
      expect(compactContainer).toBeInTheDocument();
    });

    it('should show separator in compact mode', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
          compact
        />
      );

      const separator = container.querySelector('.text-gray-300');
      expect(separator).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Full Mode Tests
  // ============================================================================

  describe('Full Mode', () => {
    it('should render full summary with all counts', () => {
      render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
          fellows={1}
        />
      );

      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Total')).toBeInTheDocument();

      expect(screen.getByText('6')).toBeInTheDocument();
      expect(screen.getByText('Residents')).toBeInTheDocument();

      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();

      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('Fellows')).toBeInTheDocument();
    });

    it('should not show fellows section when count is 0', () => {
      render(
        <StaffingSummary
          total={9}
          residents={6}
          faculty={3}
          fellows={0}
        />
      );

      expect(screen.getByText('Residents')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
      expect(screen.queryByText('Fellows')).not.toBeInTheDocument();
    });

    it('should not show fellows section when not provided', () => {
      render(
        <StaffingSummary
          total={9}
          residents={6}
          faculty={3}
        />
      );

      expect(screen.getByText('Residents')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
      expect(screen.queryByText('Fellows')).not.toBeInTheDocument();
    });

    it('should show all badges with proper styling', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
        />
      );

      // Check for gray background (total)
      const totalBadge = container.querySelector('.bg-gray-100');
      expect(totalBadge).toBeInTheDocument();

      // Check for blue background (residents)
      const residentsBadge = container.querySelector('.bg-blue-50');
      expect(residentsBadge).toBeInTheDocument();

      // Check for purple background (faculty)
      const facultyBadge = container.querySelector('.bg-purple-50');
      expect(facultyBadge).toBeInTheDocument();
    });

    it('should show fellows badge when fellows > 0', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
          fellows={1}
        />
      );

      // Check for green background (fellows)
      const fellowsBadge = container.querySelector('.bg-green-50');
      expect(fellowsBadge).toBeInTheDocument();
    });

    it('should render icons in full mode', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
        />
      );

      // Check for SVG icons (lucide icons render as SVGs)
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle zero counts', () => {
      render(
        <StaffingSummary
          total={0}
          residents={0}
          faculty={0}
        />
      );

      expect(screen.getAllByText('0')).toHaveLength(3); // Total, Residents, Faculty
      expect(screen.getByText('Total')).toBeInTheDocument();
      expect(screen.getByText('Residents')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
    });

    it('should handle large numbers', () => {
      render(
        <StaffingSummary
          total={999}
          residents={500}
          faculty={499}
        />
      );

      expect(screen.getByText('999')).toBeInTheDocument();
      expect(screen.getByText('500')).toBeInTheDocument();
      expect(screen.getByText('499')).toBeInTheDocument();
    });

    it('should handle single-digit counts in compact mode', () => {
      render(
        <StaffingSummary
          total={3}
          residents={2}
          faculty={1}
          compact
        />
      );

      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('2R')).toBeInTheDocument();
      expect(screen.getByText('1F')).toBeInTheDocument();
    });

    it('should handle all residents, no faculty', () => {
      render(
        <StaffingSummary
          total={5}
          residents={5}
          faculty={0}
        />
      );

      expect(screen.getAllByText('5')).toHaveLength(2); // Total and Residents both show 5
      expect(screen.getByText('Residents')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
      expect(screen.getAllByText('0')).toHaveLength(1); // Faculty shows 0
    });

    it('should handle all faculty, no residents', () => {
      render(
        <StaffingSummary
          total={4}
          residents={0}
          faculty={4}
        />
      );

      expect(screen.getAllByText('4')).toHaveLength(2); // Total and Faculty both show 4
      expect(screen.getByText('Residents')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
      expect(screen.getAllByText('0')).toHaveLength(1); // Residents shows 0
    });

    it('should handle only fellows', () => {
      render(
        <StaffingSummary
          total={3}
          residents={0}
          faculty={0}
          fellows={3}
        />
      );

      expect(screen.getAllByText('3')).toHaveLength(2); // Total and Fellows both show 3
      expect(screen.getAllByText('0')).toHaveLength(2); // Residents and Faculty show 0
      expect(screen.getByText('Fellows')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Default Props
  // ============================================================================

  describe('Default Props', () => {
    it('should default to full mode when compact not specified', () => {
      render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={4}
        />
      );

      // Full mode shows labels
      expect(screen.getByText('Total')).toBeInTheDocument();
      expect(screen.getByText('Residents')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
    });

    it('should default fellows to 0 when not provided', () => {
      render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={4}
        />
      );

      // Fellows section should not appear with default 0 value
      expect(screen.queryByText('Fellows')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper semantic structure in full mode', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={4}
        />
      );

      // Should use proper div structure with flex
      const mainContainer = container.querySelector('.flex.items-center.gap-3');
      expect(mainContainer).toBeInTheDocument();
    });

    it('should have proper semantic structure in compact mode', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={4}
          compact
        />
      );

      // Should use proper div structure with flex
      const mainContainer = container.querySelector('.flex.items-center.gap-2');
      expect(mainContainer).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Visual Styling
  // ============================================================================

  describe('Visual Styling', () => {
    it('should apply correct color classes for residents', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={4}
        />
      );

      const residentsElement = screen.getByText('Residents');
      expect(residentsElement).toHaveClass('text-blue-600');
    });

    it('should apply correct color classes for faculty', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={4}
        />
      );

      const facultyElement = screen.getByText('Faculty');
      expect(facultyElement).toHaveClass('text-purple-600');
    });

    it('should apply correct color classes for fellows', () => {
      const { container } = render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={3}
          fellows={1}
        />
      );

      const fellowsElement = screen.getByText('Fellows');
      expect(fellowsElement).toHaveClass('text-green-600');
    });

    it('should apply compact color classes in compact mode', () => {
      render(
        <StaffingSummary
          total={10}
          residents={6}
          faculty={4}
          compact
        />
      );

      const residentsElement = screen.getByText('6R');
      expect(residentsElement).toHaveClass('text-blue-600');

      const facultyElement = screen.getByText('4F');
      expect(facultyElement).toHaveClass('text-purple-600');
    });
  });
});
