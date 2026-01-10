/**
 * Tests for HolidayEditModal Component
 * Component: HolidayEditModal - Modal for editing federal holidays
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { HolidayEditModal } from '../HolidayEditModal';

global.fetch = jest.fn();

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('HolidayEditModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSave = jest.fn();
  const mockHolidays = [
    { id: 'new-years', name: "New Year's Day", date: '2024-01-01' },
    { id: 'christmas', name: 'Christmas Day', date: '2024-12-25' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<HolidayEditModal isOpen={true} onClose={mockOnClose} holidays={mockHolidays} onSave={mockOnSave} />);
    expect(screen.getByText(/holiday/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<HolidayEditModal isOpen={false} onClose={mockOnClose} holidays={mockHolidays} onSave={mockOnSave} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<HolidayEditModal isOpen={true} onClose={mockOnClose} holidays={mockHolidays} onSave={mockOnSave} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
