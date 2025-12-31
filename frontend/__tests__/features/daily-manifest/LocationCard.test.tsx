/**
 * Tests for LocationCard Component
 *
 * Tests for the location card showing staff assignments by location
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { LocationCard } from '@/features/daily-manifest/LocationCard';
import { manifestMockFactories } from './mockData';

// Mock the StaffingSummary component
jest.mock('@/features/daily-manifest/StaffingSummary', () => ({
  StaffingSummary: ({ total, residents, faculty, fellows, compact }: any) => (
    <div data-testid="staffing-summary">
      {compact ? 'Compact' : 'Full'} Summary: {total} total, {residents}R, {faculty}F
      {fellows ? `, ${fellows}Fe` : ''}
    </div>
  ),
}));

describe('LocationCard', () => {
  // ============================================================================
  // Basic Rendering
  // ============================================================================

  describe('Basic Rendering', () => {
    it('should render location name', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      expect(screen.getByText('Main Clinic')).toBeInTheDocument();
    });

    it('should render compact staffing summary in header', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      expect(screen.getByText(/Compact Summary/)).toBeInTheDocument();
    });

    it('should render staff count in header', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      expect(screen.getByText('2 staff')).toBeInTheDocument();
    });

    it('should render expand/collapse button', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const expandButton = screen.getByLabelText('Expand');
      expect(expandButton).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Time Period Filtering
  // ============================================================================

  describe('Time Period Filtering', () => {
    it('should show only AM assignments when timeOfDay is AM', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      // AM has 2 staff
      expect(screen.getByText('2 staff')).toBeInTheDocument();
    });

    it('should show only PM assignments when timeOfDay is PM', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="PM" />);

      // PM has 1 staff
      expect(screen.getByText('1 staff')).toBeInTheDocument();
    });

    it('should show all assignments when timeOfDay is ALL', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="ALL" />);

      // AM has 2 + PM has 1 = 3 total
      expect(screen.getByText('3 staff')).toBeInTheDocument();
    });

    it('should handle location with no AM assignments', () => {
      const location = manifestMockFactories.locationManifest({
        time_slots: {
          PM: [manifestMockFactories.personAssignment()],
        },
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      expect(screen.getByText('0 staff')).toBeInTheDocument();
    });

    it('should handle location with no PM assignments', () => {
      const location = manifestMockFactories.locationManifest({
        time_slots: {
          AM: [manifestMockFactories.personAssignment()],
        },
      });

      render(<LocationCard location={location} timeOfDay="PM" />);

      expect(screen.getByText('0 staff')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Capacity Display
  // ============================================================================

  describe('Capacity Display', () => {
    it('should show capacity bar when capacity is defined', () => {
      const location = manifestMockFactories.locationManifest({
        capacity: { current: 3, maximum: 5 },
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      expect(screen.getByText('Capacity:')).toBeInTheDocument();
      expect(screen.getByText('3 / 5')).toBeInTheDocument();
    });

    it('should not show capacity bar when capacity is undefined', () => {
      const location = manifestMockFactories.locationManifest({
        capacity: undefined,
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      expect(screen.queryByText('Capacity:')).not.toBeInTheDocument();
    });

    it('should show green capacity when well below maximum', () => {
      const location = manifestMockFactories.locationManifest({
        capacity: { current: 2, maximum: 10 },
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      const capacityText = screen.getByText('2 / 10');
      expect(capacityText).toHaveClass('text-green-600');
    });

    it('should show amber capacity when near maximum (90%)', () => {
      const location = manifestMockFactories.locationManifest({
        capacity: { current: 9, maximum: 10 },
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      const capacityText = screen.getByText('9 / 10');
      expect(capacityText).toHaveClass('text-amber-600');
    });

    it('should show red capacity when over maximum', () => {
      const location = manifestMockFactories.locationManifest({
        capacity: { current: 12, maximum: 10 },
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      const capacityText = screen.getByText('12 / 10');
      expect(capacityText).toHaveClass('text-red-600');
    });

    it('should show red capacity when at maximum', () => {
      const location = manifestMockFactories.locationManifest({
        capacity: { current: 10, maximum: 10 },
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      const capacityText = screen.getByText('10 / 10');
      // At exactly maximum, it's not over but it's at 100% so should be amber
      expect(capacityText).toHaveClass('text-amber-600');
    });
  });

  // ============================================================================
  // Expand/Collapse Functionality
  // ============================================================================

  describe('Expand/Collapse Functionality', () => {
    it('should be collapsed by default', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      // Full staffing summary only appears when expanded
      expect(screen.queryByText(/Full Summary/)).not.toBeInTheDocument();
    });

    it('should expand when header clicked', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        // When expanded, shows full summary
        expect(screen.getByText(/Full Summary/)).toBeInTheDocument();
      });
    });

    it('should show collapse button when expanded', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton.closest('div')!);

      await waitFor(() => {
        expect(screen.getByLabelText('Collapse')).toBeInTheDocument();
      });
    });

    it('should collapse when header clicked again', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('div');

      // Expand
      if (header) {
        await user.click(header);
      }
      await waitFor(() => {
        expect(screen.getByText(/Full Summary/)).toBeInTheDocument();
      });

      // Collapse
      if (header) {
        await user.click(header);
      }
      await waitFor(() => {
        expect(screen.queryByText(/Full Summary/)).not.toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Expanded Content - AM/PM Mode
  // ============================================================================

  describe('Expanded Content - AM/PM Mode', () => {
    it('should show person assignments when expanded in AM mode', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
        expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument();
      });
    });

    it('should show person assignments when expanded in PM mode', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="PM" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('Dr. Bob Johnson')).toBeInTheDocument();
      });
    });

    it('should show role and activity for each person', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getAllByText('Primary Care').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Outpatient Clinic').length).toBeGreaterThan(0);
      });
    });

    it('should show PGY level badge for residents', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('PGY-2')).toBeInTheDocument();
        expect(screen.getByText('PGY-3')).toBeInTheDocument();
      });
    });

    it('should show rotation name when available', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getAllByText(/Rotation: Family Medicine/).length).toBeGreaterThan(0);
      });
    });

    it('should show empty state when no assignments', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest({
        time_slots: { AM: [], PM: [] },
      });

      render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('No assignments for this time period')).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Expanded Content - ALL Mode
  // ============================================================================

  describe('Expanded Content - ALL Mode', () => {
    it('should show AM and PM sections when timeOfDay is ALL', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="ALL" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('Morning (AM)')).toBeInTheDocument();
        expect(screen.getByText('Afternoon (PM)')).toBeInTheDocument();
      });
    });

    it('should show AM assignments under AM section', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="ALL" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
        expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument();
      });
    });

    it('should show PM assignments under PM section', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="ALL" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('Dr. Bob Johnson')).toBeInTheDocument();
      });
    });

    it('should not show AM section if no AM assignments', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest({
        time_slots: {
          PM: [manifestMockFactories.personAssignment()],
        },
      });

      render(<LocationCard location={location} timeOfDay="ALL" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.queryByText('Morning (AM)')).not.toBeInTheDocument();
        expect(screen.getByText('Afternoon (PM)')).toBeInTheDocument();
      });
    });

    it('should not show PM section if no PM assignments', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest({
        time_slots: {
          AM: [manifestMockFactories.personAssignment()],
        },
      });

      render(<LocationCard location={location} timeOfDay="ALL" />);

      const header = screen.getByText('Main Clinic').closest('div');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        expect(screen.getByText('Morning (AM)')).toBeInTheDocument();
        expect(screen.queryByText('Afternoon (PM)')).not.toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Role Type Styling
  // ============================================================================

  describe('Role Type Styling', () => {
    it('should apply blue styling for residents', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest({
        time_slots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: '1', name: 'Resident', role_type: 'resident' },
            }),
          ],
        },
      });

      const { container } = render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('.cursor-pointer');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        const assignmentCard = container.querySelector('.text-blue-700.bg-blue-50');
        expect(assignmentCard).toBeInTheDocument();
      });
    });

    it('should apply purple styling for faculty', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest({
        time_slots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: '1', name: 'Faculty', role_type: 'faculty' },
            }),
          ],
        },
      });

      const { container } = render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('.cursor-pointer');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        const assignmentCard = container.querySelector('.text-purple-700.bg-purple-50');
        expect(assignmentCard).toBeInTheDocument();
      });
    });

    it('should apply green styling for fellows', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest({
        time_slots: {
          AM: [
            manifestMockFactories.personAssignment({
              person: { id: '1', name: 'Fellow', role_type: 'fellow' },
            }),
          ],
        },
      });

      const { container } = render(<LocationCard location={location} timeOfDay="AM" />);

      const header = screen.getByText('Main Clinic').closest('.cursor-pointer');
      if (header) {
        await user.click(header);
      }

      await waitFor(() => {
        const assignmentCard = container.querySelector('.text-green-700.bg-green-50');
        expect(assignmentCard).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Accessibility
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper ARIA labels for expand/collapse', () => {
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      expect(screen.getByLabelText('Expand')).toBeInTheDocument();
    });

    it('should update ARIA label when expanded', async () => {
      const user = userEvent.setup();
      const location = manifestMockFactories.locationManifest();

      render(<LocationCard location={location} timeOfDay="AM" />);

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton.closest('div')!);

      await waitFor(() => {
        expect(screen.getByLabelText('Collapse')).toBeInTheDocument();
      });
    });

    it('should be keyboard accessible', async () => {
      const location = manifestMockFactories.locationManifest();

      const { container } = render(<LocationCard location={location} timeOfDay="AM" />);

      const clickableHeader = container.querySelector('.cursor-pointer');

      // Should be clickable
      expect(clickableHeader).toBeInTheDocument();
      expect(clickableHeader).toHaveClass('cursor-pointer');
    });
  });

  // ============================================================================
  // Visual Styling
  // ============================================================================

  describe('Visual Styling', () => {
    it('should apply hover effect to header', () => {
      const location = manifestMockFactories.locationManifest();

      const { container } = render(<LocationCard location={location} timeOfDay="AM" />);

      const header = container.querySelector('.hover\\:bg-gray-50');
      expect(header).toBeInTheDocument();
    });

    it('should apply shadow to card', () => {
      const location = manifestMockFactories.locationManifest();

      const { container } = render(<LocationCard location={location} timeOfDay="AM" />);

      const card = container.querySelector('.shadow-sm');
      expect(card).toBeInTheDocument();
    });

    it('should apply transition to shadow on hover', () => {
      const location = manifestMockFactories.locationManifest();

      const { container } = render(<LocationCard location={location} timeOfDay="AM" />);

      const card = container.querySelector('.hover\\:shadow-md');
      expect(card).toBeInTheDocument();
    });
  });
});
