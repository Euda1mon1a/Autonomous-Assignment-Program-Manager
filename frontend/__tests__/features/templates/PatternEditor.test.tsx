/**
 * Tests for PatternEditor Component
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PatternEditor } from '@/features/templates/components/PatternEditor';
import type { AssignmentPattern } from '@/features/templates/types';

describe('PatternEditor', () => {
  const mockPatterns: AssignmentPattern[] = [
    {
      id: 'p1',
      name: 'Morning Clinic',
      dayOfWeek: 1,
      timeOfDay: 'AM',
      activityType: 'clinic',
      role: 'primary',
    },
  ];

  const mockOnAdd = jest.fn();
  const mockOnUpdate = jest.fn();
  const mockOnRemove = jest.fn();
  const mockOnDuplicate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render pattern list', () => {
    render(
      <PatternEditor
        patterns={mockPatterns}
        onAdd={mockOnAdd}
        onUpdate={mockOnUpdate}
        onRemove={mockOnRemove}
        onDuplicate={mockOnDuplicate}
      />
    );

    expect(screen.getByText(/Assignment Patterns/)).toBeInTheDocument();
    expect(screen.getByText('Morning Clinic')).toBeInTheDocument();
  });

  it('should show add pattern button', () => {
    render(
      <PatternEditor
        patterns={[]}
        onAdd={mockOnAdd}
        onUpdate={mockOnUpdate}
        onRemove={mockOnRemove}
        onDuplicate={mockOnDuplicate}
      />
    );

    expect(screen.getByText('Add Pattern')).toBeInTheDocument();
  });

  it('should show empty state when no patterns', () => {
    render(
      <PatternEditor
        patterns={[]}
        onAdd={mockOnAdd}
        onUpdate={mockOnUpdate}
        onRemove={mockOnRemove}
        onDuplicate={mockOnDuplicate}
      />
    );

    expect(screen.getByText('No patterns defined yet')).toBeInTheDocument();
  });

  it('should expand pattern details when clicked', async () => {
    const user = userEvent.setup();
    render(
      <PatternEditor
        patterns={mockPatterns}
        onAdd={mockOnAdd}
        onUpdate={mockOnUpdate}
        onRemove={mockOnRemove}
        onDuplicate={mockOnDuplicate}
      />
    );

    const patternButton = screen.getByText('Morning Clinic');
    await user.click(patternButton);

    // Verify the expanded form shows role selector and notes field
    // The labels shown are: Name, Time of Day, Role, Notes
    await waitFor(() => {
      expect(screen.getByText('Role')).toBeInTheDocument();
      expect(screen.getByText('Notes')).toBeInTheDocument();
    });
  });

  it('should call onRemove when delete is clicked', async () => {
    const user = userEvent.setup();
    render(
      <PatternEditor
        patterns={mockPatterns}
        onAdd={mockOnAdd}
        onUpdate={mockOnUpdate}
        onRemove={mockOnRemove}
        onDuplicate={mockOnDuplicate}
      />
    );

    const removeButtons = screen.getAllByTitle('Remove');
    await user.click(removeButtons[0]);

    expect(mockOnRemove).toHaveBeenCalledWith('p1');
  });

  it('should hide actions in read-only mode', () => {
    render(
      <PatternEditor
        patterns={mockPatterns}
        onAdd={mockOnAdd}
        onUpdate={mockOnUpdate}
        onRemove={mockOnRemove}
        onDuplicate={mockOnDuplicate}
        readOnly={true}
      />
    );

    expect(screen.queryByText('Add Pattern')).not.toBeInTheDocument();
  });
});
