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
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<HolidayEditModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByText(/holiday/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<HolidayEditModal isOpen={false} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<HolidayEditModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
