/**
 * Tests for TemplatePreview Component
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TemplatePreview } from '@/features/templates/components/TemplatePreview';
import type { ScheduleTemplate } from '@/features/templates/types';

describe('TemplatePreview', () => {
  const mockTemplate: ScheduleTemplate = {
    id: 't1',
    name: 'Clinic Template',
    description: 'Weekly clinic schedule',
    category: 'clinic',
    visibility: 'private',
    status: 'active',
    durationWeeks: 1,
    startDayOfWeek: 1,
    patterns: [
      {
        id: 'p1',
        name: 'Morning Clinic',
        dayOfWeek: 1,
        timeOfDay: 'AM',
        activityType: 'clinic',
        role: 'primary',
      },
    ],
    requiresSupervision: true,
    allowWeekends: false,
    allowHolidays: false,
    tags: [],
    createdBy: 'user-1',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    usageCount: 0,
    isPublic: false,
    version: 1,
  };

  const mockOnApply = jest.fn();
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render template name', () => {
    render(<TemplatePreview template={mockTemplate} />);
    expect(screen.getByText('Clinic Template')).toBeInTheDocument();
  });

  it('should render template description', () => {
    render(<TemplatePreview template={mockTemplate} />);
    expect(screen.getByText('Weekly clinic schedule')).toBeInTheDocument();
  });

  it('should show calendar preview', () => {
    render(<TemplatePreview template={mockTemplate} />);
    expect(screen.getByText('Schedule Preview')).toBeInTheDocument();
  });

  it('should show pattern summary', () => {
    render(<TemplatePreview template={mockTemplate} />);
    expect(screen.getByText('Patterns by Day')).toBeInTheDocument();
    expect(screen.getByText('Patterns by Activity')).toBeInTheDocument();
  });

  it('should call onApply when apply button is clicked', async () => {
    const user = userEvent.setup();
    render(<TemplatePreview template={mockTemplate} onApply={mockOnApply} />);

    const applyButton = screen.getByText('Apply Template');
    await user.click(applyButton);

    expect(mockOnApply).toHaveBeenCalled();
  });

  it('should call onClose when close is clicked', async () => {
    const user = userEvent.setup();
    render(<TemplatePreview template={mockTemplate} onClose={mockOnClose} />);

    const closeButton = screen.getByLabelText('Close');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should disable apply button while loading', () => {
    render(<TemplatePreview template={mockTemplate} onApply={mockOnApply} isLoading={true} />);

    const applyButton = screen.getByText('Applying...');
    expect(applyButton).toBeDisabled();
  });

  it('should allow changing start date', async () => {
    const { container } = render(<TemplatePreview template={mockTemplate} />);

    const dateInput = container.querySelector('input[type="date"]') as HTMLInputElement;
    expect(dateInput).toBeInTheDocument();

    // Use fireEvent.change for date inputs as user.clear causes Invalid time value errors
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

    expect(dateInput).toHaveValue('2025-02-01');
  });
});
