import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConflictHighlight, Conflict } from '../ConflictHighlight';

describe('ConflictHighlight', () => {
  const mockConflicts: Conflict[] = [
    {
      id: 'conflict-1',
      type: 'overlap',
      severity: 'critical',
      message: 'Dr. Smith is scheduled for two shifts at the same time',
      affectedPersons: ['Dr. Smith'],
      affectedDates: ['2024-01-15'],
      suggestions: ['Remove one of the assignments', 'Reassign to another provider'],
    },
    {
      id: 'conflict-2',
      type: 'acgmeViolation',
      severity: 'warning',
      message: 'PGY-1 resident exceeds 80-hour work limit',
      affectedPersons: ['Dr. Jones'],
      affectedDates: ['2024-01-10', '2024-01-11', '2024-01-12'],
      suggestions: ['Reduce shift hours', 'Add recovery time'],
    },
    {
      id: 'conflict-3',
      type: 'coverage_gap',
      severity: 'info',
      message: 'No attending coverage for night shift',
      affectedPersons: [],
      affectedDates: ['2024-01-20'],
    },
  ];

  const mockOnResolve = jest.fn();
  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders nothing when no conflicts', () => {
      const { container } = render(
        <ConflictHighlight conflicts={[]} onResolve={mockOnResolve} onDismiss={mockOnDismiss} />
      );

      expect(container.firstChild).toBeNull();
    });

    it('renders summary header when conflicts exist', () => {
      render(<ConflictHighlight conflicts={mockConflicts} />);

      expect(screen.getByText('Schedule Conflicts')).toBeInTheDocument();
    });

    it('displays conflict count in summary', () => {
      render(<ConflictHighlight conflicts={mockConflicts} />);

      expect(screen.getByText(/3 conflicts detected/)).toBeInTheDocument();
    });

    it('uses singular "conflict" for single conflict', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      expect(screen.getByText(/1 conflict detected/)).toBeInTheDocument();
    });

    it('displays all conflicts', () => {
      render(<ConflictHighlight conflicts={mockConflicts} />);

      expect(screen.getByText('Dr. Smith is scheduled for two shifts at the same time')).toBeInTheDocument();
      expect(screen.getByText('PGY-1 resident exceeds 80-hour work limit')).toBeInTheDocument();
      expect(screen.getByText('No attending coverage for night shift')).toBeInTheDocument();
    });
  });

  describe('severity badges', () => {
    it('shows critical badge count in summary', () => {
      render(<ConflictHighlight conflicts={mockConflicts} />);

      expect(screen.getByText('1 Critical')).toBeInTheDocument();
    });

    it('shows warning badge count in summary', () => {
      render(<ConflictHighlight conflicts={mockConflicts} />);

      expect(screen.getByText('1 Warnings')).toBeInTheDocument();
    });

    it('does not show info badge in summary', () => {
      render(<ConflictHighlight conflicts={mockConflicts} />);

      // Info conflicts don't appear in summary badges
      expect(screen.queryByText(/Info/)).not.toBeInTheDocument();
    });

    it('applies critical styling to critical conflicts', () => {
      const { container } = render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      const criticalConflict = container.querySelector('.bg-red-50');
      expect(criticalConflict).toBeInTheDocument();
    });

    it('applies warning styling to warning conflicts', () => {
      const { container } = render(<ConflictHighlight conflicts={[mockConflicts[1]]} />);

      const warningConflict = container.querySelector('.bg-yellow-50');
      expect(warningConflict).toBeInTheDocument();
    });

    it('applies info styling to info conflicts', () => {
      const { container } = render(<ConflictHighlight conflicts={[mockConflicts[2]]} />);

      const infoConflict = container.querySelector('.bg-blue-50');
      expect(infoConflict).toBeInTheDocument();
    });
  });

  describe('conflict types', () => {
    it('displays correct label for overlap conflicts', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      expect(screen.getByText('Schedule Overlap')).toBeInTheDocument();
    });

    it('displays correct label for ACGME violations', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[1]]} />);

      expect(screen.getByText('ACGME Violation')).toBeInTheDocument();
    });

    it('displays correct label for coverage gaps', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[2]]} />);

      expect(screen.getByText('Coverage Gap')).toBeInTheDocument();
    });

    it('displays correct label for missing credentials', () => {
      const credentialConflict: Conflict = {
        id: 'conflict-4',
        type: 'credential_missing',
        severity: 'warning',
        message: 'Missing BLS certification',
        affectedPersons: ['Dr. Lee'],
        affectedDates: ['2024-01-25'],
      };

      render(<ConflictHighlight conflicts={[credentialConflict]} />);

      expect(screen.getByText('Missing Credentials')).toBeInTheDocument();
    });
  });

  describe('severity icons', () => {
    it('shows critical icon (🚨)', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      expect(screen.getByLabelText('Critical')).toHaveTextContent('🚨');
    });

    it('shows warning icon (⚠️)', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[1]]} />);

      expect(screen.getByLabelText('Warning')).toHaveTextContent('⚠️');
    });

    it('shows info icon (ℹ️)', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[2]]} />);

      expect(screen.getByLabelText('Info')).toHaveTextContent('ℹ️');
    });
  });

  describe('affected persons', () => {
    it('displays affected persons', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      expect(screen.getByText('Affected Persons:')).toBeInTheDocument();
      expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    });

    it('displays multiple affected persons', () => {
      const multiPersonConflict: Conflict = {
        ...mockConflicts[0],
        affectedPersons: ['Dr. Smith', 'Dr. Jones', 'Dr. Lee'],
      };

      render(<ConflictHighlight conflicts={[multiPersonConflict]} />);

      expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Jones')).toBeInTheDocument();
      expect(screen.getByText('Dr. Lee')).toBeInTheDocument();
    });
  });

  describe('affected dates', () => {
    it('displays affected dates', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      expect(screen.getByText('Affected Dates:')).toBeInTheDocument();
      expect(screen.getByText('1/15/2024')).toBeInTheDocument();
    });

    it('displays multiple affected dates', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[1]]} />);

      expect(screen.getByText('1/10/2024')).toBeInTheDocument();
      expect(screen.getByText('1/11/2024')).toBeInTheDocument();
      expect(screen.getByText('1/12/2024')).toBeInTheDocument();
    });
  });

  describe('suggestions', () => {
    it('displays suggestions when available', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      expect(screen.getByText('Suggestions:')).toBeInTheDocument();
      expect(screen.getByText('Remove one of the assignments')).toBeInTheDocument();
      expect(screen.getByText('Reassign to another provider')).toBeInTheDocument();
    });

    it('does not show suggestions section when none provided', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[2]]} />);

      expect(screen.queryByText('Suggestions:')).not.toBeInTheDocument();
    });

    it('renders suggestions as list items', () => {
      const { container } = render(<ConflictHighlight conflicts={[mockConflicts[0]]} />);

      const listItems = container.querySelectorAll('ul li');
      expect(listItems.length).toBe(2);
    });
  });

  describe('action buttons', () => {
    it('renders resolve button when onResolve provided', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} onResolve={mockOnResolve} />);

      expect(screen.getByLabelText('Resolve conflict')).toBeInTheDocument();
    });

    it('renders dismiss button when onDismiss provided', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} onDismiss={mockOnDismiss} />);

      expect(screen.getByLabelText('Dismiss conflict')).toBeInTheDocument();
    });

    it('does not render resolve button when onResolve not provided', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} onDismiss={mockOnDismiss} />);

      expect(screen.queryByLabelText('Resolve conflict')).not.toBeInTheDocument();
    });

    it('does not render dismiss button when onDismiss not provided', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} onResolve={mockOnResolve} />);

      expect(screen.queryByLabelText('Dismiss conflict')).not.toBeInTheDocument();
    });

    it('calls onResolve with conflict ID when resolve clicked', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} onResolve={mockOnResolve} />);

      const resolveButton = screen.getByLabelText('Resolve conflict');
      fireEvent.click(resolveButton);

      expect(mockOnResolve).toHaveBeenCalledWith('conflict-1');
      expect(mockOnResolve).toHaveBeenCalledTimes(1);
    });

    it('calls onDismiss with conflict ID when dismiss clicked', () => {
      render(<ConflictHighlight conflicts={[mockConflicts[0]]} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByLabelText('Dismiss conflict');
      fireEvent.click(dismissButton);

      expect(mockOnDismiss).toHaveBeenCalledWith('conflict-1');
      expect(mockOnDismiss).toHaveBeenCalledTimes(1);
    });
  });

  describe('accessibility', () => {
    it('has role="alert" for each conflict', () => {
      const { container } = render(<ConflictHighlight conflicts={mockConflicts} />);

      const alerts = container.querySelectorAll('[role="alert"]');
      expect(alerts.length).toBe(3);
    });

    it('has aria-live="polite" for conflicts', () => {
      const { container } = render(<ConflictHighlight conflicts={mockConflicts} />);

      const liveRegions = container.querySelectorAll('[aria-live="polite"]');
      expect(liveRegions.length).toBe(3);
    });

    it('has proper button labels', () => {
      render(
        <ConflictHighlight
          conflicts={[mockConflicts[0]]}
          onResolve={mockOnResolve}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByLabelText('Resolve conflict')).toBeInTheDocument();
      expect(screen.getByLabelText('Dismiss conflict')).toBeInTheDocument();
    });
  });

  describe('custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <ConflictHighlight conflicts={mockConflicts} className="custom-conflict" />
      );

      expect(container.firstChild).toHaveClass('custom-conflict');
    });
  });

  describe('conflict grouping', () => {
    it('renders conflicts in severity order', () => {
      const { container } = render(<ConflictHighlight conflicts={mockConflicts} />);

      const conflictDivs = container.querySelectorAll('.rounded-lg.border-l-4');

      // Critical first (red background)
      expect(conflictDivs[0]).toHaveClass('bg-red-50');

      // Warning second (yellow background)
      expect(conflictDivs[1]).toHaveClass('bg-yellow-50');

      // Info third (blue background)
      expect(conflictDivs[2]).toHaveClass('bg-blue-50');
    });
  });
});
