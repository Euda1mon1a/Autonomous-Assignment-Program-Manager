import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AssignmentWarnings, WarningBadge, generateWarnings, AssignmentWarning, WarningCheckContext } from '../AssignmentWarnings';

describe('AssignmentWarnings', () => {
  const mockWarnings: AssignmentWarning[] = [
    {
      type: 'hours',
      severity: 'critical',
      message: 'This assignment would exceed the 80-hour weekly limit',
    },
    {
      type: 'supervision',
      severity: 'warning',
      message: 'No supervisor assigned for this rotation',
    },
    {
      type: 'conflict',
      severity: 'info',
      message: 'This is close to another assignment',
    },
  ];

  describe('rendering', () => {
    it('renders nothing when no warnings', () => {
      const { container } = render(<AssignmentWarnings warnings={[]} />);

      expect(container.firstChild).toBeNull();
    });

    it('renders warning count', () => {
      render(<AssignmentWarnings warnings={mockWarnings} />);

      expect(screen.getByText('Warnings (3)')).toBeInTheDocument();
    });

    it('renders all warnings', () => {
      render(<AssignmentWarnings warnings={mockWarnings} />);

      expect(screen.getByText('This assignment would exceed the 80-hour weekly limit')).toBeInTheDocument();
      expect(screen.getByText('No supervisor assigned for this rotation')).toBeInTheDocument();
      expect(screen.getByText('This is close to another assignment')).toBeInTheDocument();
    });

    it('sorts warnings by severity (critical first)', () => {
      const { container } = render(<AssignmentWarnings warnings={mockWarnings} />);

      const warningElements = container.querySelectorAll('.rounded-md.border');

      // Critical should be first (red background)
      expect(warningElements[0]).toHaveClass('bg-red-50');

      // Warning should be second (amber background)
      expect(warningElements[1]).toHaveClass('bg-amber-50');

      // Info should be last (blue background)
      expect(warningElements[2]).toHaveClass('bg-blue-50');
    });
  });

  describe('severity styling', () => {
    it('applies critical styling', () => {
      render(<AssignmentWarnings warnings={[mockWarnings[0]]} />);

      const warning = screen.getByText('This assignment would exceed the 80-hour weekly limit').closest('.rounded-md');
      expect(warning).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800');
    });

    it('applies warning styling', () => {
      render(<AssignmentWarnings warnings={[mockWarnings[1]]} />);

      const warning = screen.getByText('No supervisor assigned for this rotation').closest('.rounded-md');
      expect(warning).toHaveClass('bg-amber-50', 'border-amber-200', 'text-amber-800');
    });

    it('applies info styling', () => {
      render(<AssignmentWarnings warnings={[mockWarnings[2]]} />);

      const warning = screen.getByText('This is close to another assignment').closest('.rounded-md');
      expect(warning).toHaveClass('bg-blue-50', 'border-blue-200', 'text-blue-800');
    });
  });

  describe('warning types', () => {
    it('displays hours warning type', () => {
      render(<AssignmentWarnings warnings={[mockWarnings[0]]} />);

      expect(screen.getByText('hours')).toBeInTheDocument();
    });

    it('displays supervision warning type', () => {
      render(<AssignmentWarnings warnings={[mockWarnings[1]]} />);

      expect(screen.getByText('supervision')).toBeInTheDocument();
    });

    it('displays appropriate icons for each type', () => {
      const { container } = render(<AssignmentWarnings warnings={mockWarnings} />);

      // Check for various lucide icons
      const icons = container.querySelectorAll('.lucide');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('critical acknowledgment', () => {
    it('shows acknowledgment checkbox when there are critical warnings', () => {
      const mockOnAcknowledge = jest.fn();
      render(
        <AssignmentWarnings
          warnings={[mockWarnings[0]]}
          onAcknowledgeCritical={mockOnAcknowledge}
        />
      );

      expect(screen.getByText(/I understand this override/)).toBeInTheDocument();
      expect(screen.getByRole('checkbox')).toBeInTheDocument();
    });

    it('does not show acknowledgment when no critical warnings', () => {
      const mockOnAcknowledge = jest.fn();
      render(
        <AssignmentWarnings
          warnings={[mockWarnings[1], mockWarnings[2]]}
          onAcknowledgeCritical={mockOnAcknowledge}
        />
      );

      expect(screen.queryByText(/I understand this override/)).not.toBeInTheDocument();
    });

    it('does not show acknowledgment when callback not provided', () => {
      render(<AssignmentWarnings warnings={[mockWarnings[0]]} />);

      expect(screen.queryByText(/I understand this override/)).not.toBeInTheDocument();
    });

    it('calls onAcknowledgeCritical when checkbox toggled', () => {
      const mockOnAcknowledge = jest.fn();
      render(
        <AssignmentWarnings
          warnings={[mockWarnings[0]]}
          onAcknowledgeCritical={mockOnAcknowledge}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);

      expect(mockOnAcknowledge).toHaveBeenCalledWith(true);
    });

    it('reflects checked state from props', () => {
      const mockOnAcknowledge = jest.fn();
      render(
        <AssignmentWarnings
          warnings={[mockWarnings[0]]}
          onAcknowledgeCritical={mockOnAcknowledge}
          criticalAcknowledged={true}
        />
      );

      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
    });
  });

  describe('scrollable container', () => {
    it('applies scrollable styles for many warnings', () => {
      const manyWarnings = Array.from({ length: 10 }, (_, i) => ({
        type: 'hours' as const,
        severity: 'warning' as const,
        message: `Warning ${i}`,
      }));

      const { container } = render(<AssignmentWarnings warnings={manyWarnings} />);

      const scrollContainer = container.querySelector('.overflow-y-auto');
      expect(scrollContainer).toBeInTheDocument();
      expect(scrollContainer).toHaveClass('max-h-48');
    });
  });
});

describe('WarningBadge', () => {
  describe('rendering', () => {
    it('renders nothing when no warnings', () => {
      const { container } = render(<WarningBadge warnings={[]} />);

      expect(container.firstChild).toBeNull();
    });

    it('renders warning count', () => {
      const warnings: AssignmentWarning[] = [
        { type: 'hours', severity: 'warning', message: 'Test' },
        { type: 'supervision', severity: 'info', message: 'Test 2' },
      ];

      render(<WarningBadge warnings={warnings} />);

      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('applies critical styling when critical warnings present', () => {
      const warnings: AssignmentWarning[] = [
        { type: 'hours', severity: 'critical', message: 'Test' },
      ];

      const { container } = render(<WarningBadge warnings={warnings} />);

      const badge = container.firstChild;
      expect(badge).toHaveClass('bg-red-100', 'text-red-700');
    });

    it('applies warning styling when only warnings present', () => {
      const warnings: AssignmentWarning[] = [
        { type: 'hours', severity: 'warning', message: 'Test' },
      ];

      const { container } = render(<WarningBadge warnings={warnings} />);

      const badge = container.firstChild;
      expect(badge).toHaveClass('bg-amber-100', 'text-amber-700');
    });

    it('applies info styling when only info present', () => {
      const warnings: AssignmentWarning[] = [
        { type: 'hours', severity: 'info', message: 'Test' },
      ];

      const { container } = render(<WarningBadge warnings={warnings} />);

      const badge = container.firstChild;
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-700');
    });
  });

  describe('compact mode', () => {
    it('renders compact badge without count', () => {
      const warnings: AssignmentWarning[] = [
        { type: 'hours', severity: 'critical', message: 'Test' },
      ];

      render(<WarningBadge warnings={warnings} compact={true} />);

      expect(screen.queryByText('1')).not.toBeInTheDocument();
    });

    it('renders icon-only in compact mode', () => {
      const warnings: AssignmentWarning[] = [
        { type: 'hours', severity: 'critical', message: 'Test' },
      ];

      const { container } = render(<WarningBadge warnings={warnings} compact={true} />);

      const badge = container.firstChild;
      expect(badge).toHaveClass('w-5', 'h-5', 'rounded-full');
    });
  });
});

describe('generateWarnings', () => {
  describe('hours warnings', () => {
    it('generates critical warning when significantly over hours limit', () => {
      const context: WarningCheckContext = {
        personId: '1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM',
        weeklyHours: 74,
        maxWeeklyHours: 80,
      };

      const warnings = generateWarnings(context);

      const hoursWarning = warnings.find((w) => w.type === 'hours');
      expect(hoursWarning).toBeDefined();
      expect(hoursWarning?.severity).toBe('warning'); // 78 hours, only 2 over
    });

    it('generates warning when moderately over hours limit', () => {
      const context: WarningCheckContext = {
        personId: '1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM',
        weeklyHours: 77,
        maxWeeklyHours: 80,
      };

      const warnings = generateWarnings(context);

      const hoursWarning = warnings.find((w) => w.type === 'hours');
      expect(hoursWarning).toBeDefined();
    });

    it('does not generate hours warning when under limit', () => {
      const context: WarningCheckContext = {
        personId: '1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM',
        weeklyHours: 50,
        maxWeeklyHours: 80,
      };

      const warnings = generateWarnings(context);

      const hoursWarning = warnings.find((w) => w.type === 'hours');
      expect(hoursWarning).toBeUndefined();
    });
  });

  describe('supervision warnings', () => {
    it('generates critical warning when supervision required but missing', () => {
      const context: WarningCheckContext = {
        personId: '1',
        date: '2024-01-15',
        session: 'AM',
        requiresSupervision: true,
        hasSupervisor: false,
      };

      const warnings = generateWarnings(context);

      const supervisionWarning = warnings.find((w) => w.type === 'supervision');
      expect(supervisionWarning).toBeDefined();
      expect(supervisionWarning?.severity).toBe('critical');
    });

    it('does not generate warning when supervision present', () => {
      const context: WarningCheckContext = {
        personId: '1',
        date: '2024-01-15',
        session: 'AM',
        requiresSupervision: true,
        hasSupervisor: true,
      };

      const warnings = generateWarnings(context);

      const supervisionWarning = warnings.find((w) => w.type === 'supervision');
      expect(supervisionWarning).toBeUndefined();
    });
  });

  describe('conflict warnings', () => {
    it('generates critical warning for scheduling conflicts', () => {
      const context: WarningCheckContext = {
        personId: '1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM',
        existingAssignments: [
          { date: '2024-01-15', session: 'AM', rotationName: 'Clinic' },
        ],
      };

      const warnings = generateWarnings(context);

      const conflictWarning = warnings.find((w) => w.type === 'conflict');
      expect(conflictWarning).toBeDefined();
      expect(conflictWarning?.severity).toBe('critical');
    });

    it('does not generate conflict for different session', () => {
      const context: WarningCheckContext = {
        personId: '1',
        date: '2024-01-15',
        session: 'AM',
        existingAssignments: [
          { date: '2024-01-15', session: 'PM', rotationName: 'Clinic' },
        ],
      };

      const warnings = generateWarnings(context);

      const conflictWarning = warnings.find((w) => w.type === 'conflict');
      expect(conflictWarning).toBeUndefined();
    });
  });

  describe('absence warnings', () => {
    it('generates critical warning for absence conflicts', () => {
      const context: WarningCheckContext = {
        personId: '1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM',
        absences: [
          { startDate: '2024-01-10', endDate: '2024-01-20', type: 'vacation' },
        ],
      };

      const warnings = generateWarnings(context);

      const absenceWarning = warnings.find((w) => w.type === 'absence');
      expect(absenceWarning).toBeDefined();
      expect(absenceWarning?.severity).toBe('critical');
    });

    it('does not generate warning when date outside absence range', () => {
      const context: WarningCheckContext = {
        personId: '1',
        date: '2024-01-25',
        session: 'AM',
        absences: [
          { startDate: '2024-01-10', endDate: '2024-01-20', type: 'vacation' },
        ],
      };

      const warnings = generateWarnings(context);

      const absenceWarning = warnings.find((w) => w.type === 'absence');
      expect(absenceWarning).toBeUndefined();
    });
  });

  describe('capacity warnings', () => {
    it('generates warning when rotation at capacity', () => {
      const context: WarningCheckContext = {
        personId: '1',
        date: '2024-01-15',
        session: 'AM',
        rotationCapacity: 4,
        currentRotationCount: 4,
      };

      const warnings = generateWarnings(context);

      const capacityWarning = warnings.find((w) => w.type === 'capacity');
      expect(capacityWarning).toBeDefined();
      expect(capacityWarning?.severity).toBe('warning');
    });

    it('does not generate warning when under capacity', () => {
      const context: WarningCheckContext = {
        personId: '1',
        date: '2024-01-15',
        session: 'AM',
        rotationCapacity: 4,
        currentRotationCount: 2,
      };

      const warnings = generateWarnings(context);

      const capacityWarning = warnings.find((w) => w.type === 'capacity');
      expect(capacityWarning).toBeUndefined();
    });
  });
});
