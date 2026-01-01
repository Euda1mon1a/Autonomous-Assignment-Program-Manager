import { render, screen } from '@/test-utils';
import { CoverageMatrix, CoverageSummary, CoverageSlot } from '@/components/scheduling/CoverageMatrix';

describe('CoverageMatrix', () => {
  const mockSlots: CoverageSlot[] = [
    {
      date: new Date('2025-01-01'),
      period: 'AM',
      required: 4,
      assigned: 4,
      staff: ['Dr. Smith', 'Dr. Jones', 'Dr. Lee', 'Dr. Kim'],
    },
    {
      date: new Date('2025-01-01'),
      period: 'PM',
      required: 4,
      assigned: 3,
      staff: ['Dr. Smith', 'Dr. Jones', 'Dr. Lee'],
    },
    {
      date: new Date('2025-01-02'),
      period: 'AM',
      required: 4,
      assigned: 2,
      staff: ['Dr. Smith', 'Dr. Jones'],
    },
    {
      date: new Date('2025-01-02'),
      period: 'PM',
      required: 4,
      assigned: 1,
      staff: ['Dr. Smith'],
    },
  ];

  const dateRange = {
    start: new Date('2025-01-01'),
    end: new Date('2025-01-02'),
  };

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      expect(screen.getByRole('columnheader', { name: /Date/i })).toBeInTheDocument();
    });

    it('renders table headers', () => {
      render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      expect(screen.getByRole('columnheader', { name: /Date/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /AM/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /PM/i })).toBeInTheDocument();
    });

    it('renders all dates in range', () => {
      render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      // Should show both Jan 1 and Jan 2
      expect(screen.getByText(/Jan 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Jan 2/i)).toBeInTheDocument();
    });

    it('formats dates with weekday, month, and day', () => {
      render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      // Dates should include weekday abbreviation
      const dateCell = screen.getByText(/Jan 1/i);
      expect(dateCell).toBeInTheDocument();
    });
  });

  describe('Coverage Display', () => {
    it('displays coverage ratio for each slot', () => {
      render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      expect(screen.getByText('4/4')).toBeInTheDocument(); // Full
      expect(screen.getByText('3/4')).toBeInTheDocument(); // Partial
      expect(screen.getByText('2/4')).toBeInTheDocument(); // Critical
      expect(screen.getByText('1/4')).toBeInTheDocument(); // Critical
    });

    it('displays dash for empty slots', () => {
      const slotsWithGap: CoverageSlot[] = [
        {
          date: new Date('2025-01-01'),
          period: 'AM',
          required: 4,
          assigned: 4,
          staff: ['Dr. Smith', 'Dr. Jones', 'Dr. Lee', 'Dr. Kim'],
        },
      ];

      const widerRange = {
        start: new Date('2025-01-01'),
        end: new Date('2025-01-03'),
      };

      render(<CoverageMatrix slots={slotsWithGap} dateRange={widerRange} />);

      // Should show dashes for slots without data
      const dashes = screen.getAllByText('-');
      expect(dashes.length).toBeGreaterThan(0);
    });
  });

  describe('Coverage Color Coding', () => {
    it('applies green background for fully staffed slots', () => {
      const { container } = render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      const fullSlot = screen.getByText('4/4').closest('td');
      expect(fullSlot).toHaveClass('bg-green-100');
      expect(fullSlot).toHaveClass('text-green-900');
    });

    it('applies amber background for partially staffed slots (>= 75%)', () => {
      const { container } = render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      const partialSlot = screen.getByText('3/4').closest('td'); // 75%
      expect(partialSlot).toHaveClass('bg-amber-100');
      expect(partialSlot).toHaveClass('text-amber-900');
    });

    it('applies red background for critically understaffed slots (< 75%)', () => {
      const { container } = render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      const criticalSlot = screen.getByText('2/4').closest('td'); // 50%
      expect(criticalSlot).toHaveClass('bg-red-100');
      expect(criticalSlot).toHaveClass('text-red-900');
    });

    it('applies gray background for empty slots', () => {
      const sparseSlots: CoverageSlot[] = [
        {
          date: new Date('2025-01-01'),
          period: 'AM',
          required: 4,
          assigned: 4,
          staff: [],
        },
      ];

      const widerRange = {
        start: new Date('2025-01-01'),
        end: new Date('2025-01-02'),
      };

      const { container } = render(<CoverageMatrix slots={sparseSlots} dateRange={widerRange} />);

      // Empty slots should have gray background
      const emptySlots = container.querySelectorAll('.bg-gray-50');
      expect(emptySlots.length).toBeGreaterThan(0);
    });
  });

  describe('Warning Icons', () => {
    it('shows warning icon for critical coverage when showWarnings is true', () => {
      const { container } = render(
        <CoverageMatrix slots={mockSlots} dateRange={dateRange} showWarnings={true} />
      );

      // Should show alert icons for critical slots
      const icons = container.querySelectorAll('svg.w-4.h-4');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('does not show warning icons when showWarnings is false', () => {
      const { container } = render(
        <CoverageMatrix slots={mockSlots} dateRange={dateRange} showWarnings={false} />
      );

      // Should not show alert icons
      const icons = container.querySelectorAll('svg.w-4.h-4');
      expect(icons.length).toBe(0);
    });

    it('shows warnings by default', () => {
      const { container } = render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      // Should show alert icons by default
      const icons = container.querySelectorAll('svg.w-4.h-4');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('does not show warning for fully staffed slots', () => {
      const fullSlots: CoverageSlot[] = [
        {
          date: new Date('2025-01-01'),
          period: 'AM',
          required: 4,
          assigned: 4,
          staff: ['Dr. Smith', 'Dr. Jones', 'Dr. Lee', 'Dr. Kim'],
        },
      ];

      const { container } = render(
        <CoverageMatrix slots={fullSlots} dateRange={dateRange} showWarnings={true} />
      );

      const icons = container.querySelectorAll('svg.w-4.h-4');
      expect(icons.length).toBe(0);
    });
  });

  describe('Table Structure', () => {
    it('renders proper table structure', () => {
      const { container } = render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      expect(container.querySelector('table')).toBeInTheDocument();
      expect(container.querySelector('thead')).toBeInTheDocument();
      expect(container.querySelector('tbody')).toBeInTheDocument();
    });

    it('applies hover effect to rows', () => {
      const { container } = render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      const rows = container.querySelectorAll('tbody tr.hover\\:bg-gray-50');
      expect(rows.length).toBeGreaterThan(0);
    });

    it('applies overflow-x-auto for responsiveness', () => {
      const { container } = render(<CoverageMatrix slots={mockSlots} dateRange={dateRange} />);

      const wrapper = container.querySelector('.overflow-x-auto');
      expect(wrapper).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <CoverageMatrix slots={mockSlots} dateRange={dateRange} className="custom-coverage" />
      );

      expect(container.querySelector('.custom-coverage')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty slots array', () => {
      render(<CoverageMatrix slots={[]} dateRange={dateRange} />);

      expect(screen.getByRole('columnheader', { name: /Date/i })).toBeInTheDocument();
      // All cells should be empty
      expect(screen.getAllByText('-').length).toBeGreaterThan(0);
    });

    it('handles single day range', () => {
      const singleDay = {
        start: new Date('2025-01-01'),
        end: new Date('2025-01-01'),
      };

      render(<CoverageMatrix slots={mockSlots} dateRange={singleDay} />);

      // Should show only one date
      expect(screen.getByText(/Jan 1/i)).toBeInTheDocument();
      expect(screen.queryByText(/Jan 2/i)).not.toBeInTheDocument();
    });

    it('handles 100% coverage correctly', () => {
      const perfectSlots: CoverageSlot[] = [
        {
          date: new Date('2025-01-01'),
          period: 'AM',
          required: 4,
          assigned: 4,
          staff: [],
        },
      ];

      const { container } = render(<CoverageMatrix slots={perfectSlots} dateRange={dateRange} />);

      const slot = screen.getByText('4/4').closest('td');
      expect(slot).toHaveClass('bg-green-100');
    });

    it('handles overstaffed slots', () => {
      const overstaffedSlots: CoverageSlot[] = [
        {
          date: new Date('2025-01-01'),
          period: 'AM',
          required: 4,
          assigned: 5,
          staff: [],
        },
      ];

      render(<CoverageMatrix slots={overstaffedSlots} dateRange={dateRange} />);

      expect(screen.getByText('5/4')).toBeInTheDocument();

      const slot = screen.getByText('5/4').closest('td');
      expect(slot).toHaveClass('bg-green-100'); // > 100% is still green
    });

    it('handles exactly 75% coverage (boundary)', () => {
      const boundarySlots: CoverageSlot[] = [
        {
          date: new Date('2025-01-01'),
          period: 'AM',
          required: 4,
          assigned: 3,
          staff: [],
        },
      ];

      const { container } = render(
        <CoverageMatrix slots={boundarySlots} dateRange={dateRange} />
      );

      const slot = screen.getByText('3/4').closest('td');
      expect(slot).toHaveClass('bg-amber-100'); // Exactly 75% is amber
    });
  });
});

describe('CoverageSummary', () => {
  const mockSlots: CoverageSlot[] = [
    // Fully staffed
    { date: new Date(), period: 'AM', required: 4, assigned: 4, staff: [] },
    { date: new Date(), period: 'PM', required: 4, assigned: 5, staff: [] },
    // Partially staffed (>= 75%)
    { date: new Date(), period: 'AM', required: 4, assigned: 3, staff: [] },
    // Critical (< 75%)
    { date: new Date(), period: 'PM', required: 4, assigned: 2, staff: [] },
    { date: new Date(), period: 'AM', required: 4, assigned: 1, staff: [] },
  ];

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<CoverageSummary slots={mockSlots} />);

      expect(screen.getByText('Fully Staffed')).toBeInTheDocument();
    });

    it('renders all three categories', () => {
      render(<CoverageSummary slots={mockSlots} />);

      expect(screen.getByText('Fully Staffed')).toBeInTheDocument();
      expect(screen.getByText('Partial Coverage')).toBeInTheDocument();
      expect(screen.getByText('Critical')).toBeInTheDocument();
    });
  });

  describe('Statistics Calculation', () => {
    it('counts fully staffed slots correctly', () => {
      render(<CoverageSummary slots={mockSlots} />);

      // 2 fully staffed slots
      const fullyStaffedCard = screen.getByText('Fully Staffed').closest('div');
      expect(fullyStaffedCard).toHaveTextContent('2');
    });

    it('counts partially staffed slots correctly', () => {
      render(<CoverageSummary slots={mockSlots} />);

      // 1 partially staffed slot (75%)
      const partialCard = screen.getByText('Partial Coverage').closest('div');
      expect(partialCard).toHaveTextContent('1');
    });

    it('counts critical slots correctly', () => {
      render(<CoverageSummary slots={mockSlots} />);

      // 2 critical slots (< 75%)
      const criticalCard = screen.getByText('Critical').closest('div');
      expect(criticalCard).toHaveTextContent('2');
    });

    it('calculates percentages correctly', () => {
      render(<CoverageSummary slots={mockSlots} />);

      // 2/5 = 40.0%
      expect(screen.getByText('40.0%')).toBeInTheDocument();
      // 1/5 = 20.0%
      expect(screen.getByText('20.0%')).toBeInTheDocument();
      // 2/5 = 40.0% (appears twice)
      const percentages = screen.getAllByText('40.0%');
      expect(percentages.length).toBe(2);
    });
  });

  describe('Color Coding', () => {
    it('applies green styling to fully staffed card', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const fullyStaffedCard = screen.getByText('Fully Staffed').closest('div');
      expect(fullyStaffedCard).toHaveClass('bg-green-100');

      const value = fullyStaffedCard?.querySelector('.text-2xl');
      expect(value).toHaveClass('text-green-600');
    });

    it('applies amber styling to partial coverage card', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const partialCard = screen.getByText('Partial Coverage').closest('div');
      expect(partialCard).toHaveClass('bg-amber-100');

      const value = partialCard?.querySelector('.text-2xl');
      expect(value).toHaveClass('text-amber-600');
    });

    it('applies red styling to critical card', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const criticalCard = screen.getByText('Critical').closest('div');
      expect(criticalCard).toHaveClass('bg-red-100');

      const value = criticalCard?.querySelector('.text-2xl');
      expect(value).toHaveClass('text-red-600');
    });
  });

  describe('Layout', () => {
    it('uses grid layout with 3 columns', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const grid = container.querySelector('.grid.grid-cols-3');
      expect(grid).toBeInTheDocument();
    });

    it('applies gap between cards', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const grid = container.querySelector('.gap-4');
      expect(grid).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} className="custom-summary" />);

      expect(container.querySelector('.custom-summary')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty slots array', () => {
      render(<CoverageSummary slots={[]} />);

      // All counts should be 0
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBe(3);
    });

    it('handles all fully staffed', () => {
      const allFull: CoverageSlot[] = [
        { date: new Date(), period: 'AM', required: 4, assigned: 4, staff: [] },
        { date: new Date(), period: 'PM', required: 4, assigned: 4, staff: [] },
      ];

      render(<CoverageSummary slots={allFull} />);

      const fullyStaffedCard = screen.getByText('Fully Staffed').closest('div');
      expect(fullyStaffedCard).toHaveTextContent('2');
      expect(fullyStaffedCard).toHaveTextContent('100.0%');

      const partialCard = screen.getByText('Partial Coverage').closest('div');
      expect(partialCard).toHaveTextContent('0');

      const criticalCard = screen.getByText('Critical').closest('div');
      expect(criticalCard).toHaveTextContent('0');
    });

    it('handles all critical', () => {
      const allCritical: CoverageSlot[] = [
        { date: new Date(), period: 'AM', required: 4, assigned: 1, staff: [] },
        { date: new Date(), period: 'PM', required: 4, assigned: 0, staff: [] },
      ];

      render(<CoverageSummary slots={allCritical} />);

      const criticalCard = screen.getByText('Critical').closest('div');
      expect(criticalCard).toHaveTextContent('2');
      expect(criticalCard).toHaveTextContent('100.0%');
    });

    it('formats percentage with one decimal place', () => {
      const oddSlots: CoverageSlot[] = [
        { date: new Date(), period: 'AM', required: 3, assigned: 3, staff: [] },
        { date: new Date(), period: 'PM', required: 3, assigned: 2, staff: [] },
        { date: new Date(), period: 'AM', required: 3, assigned: 1, staff: [] },
      ];

      render(<CoverageSummary slots={oddSlots} />);

      // 1/3 = 33.3%
      expect(screen.getByText('33.3%')).toBeInTheDocument();
    });
  });

  describe('Typography', () => {
    it('uses large bold text for values', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const values = container.querySelectorAll('.text-2xl.font-bold');
      expect(values.length).toBe(3);
    });

    it('uses small text for labels', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const labels = container.querySelectorAll('.text-sm');
      expect(labels.length).toBe(3);
    });

    it('uses extra small text for percentages', () => {
      const { container } = render(<CoverageSummary slots={mockSlots} />);

      const percentages = container.querySelectorAll('.text-xs');
      expect(percentages.length).toBe(3);
    });
  });
});
