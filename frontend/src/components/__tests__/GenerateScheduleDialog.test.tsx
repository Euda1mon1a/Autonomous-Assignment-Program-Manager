/**
 * Tests for GenerateScheduleDialog Component
 * Component: GenerateScheduleDialog - Schedule generation dialog
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { GenerateScheduleDialog } from '../GenerateScheduleDialog';

global.fetch = jest.fn();

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('GenerateScheduleDialog', () => {
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<GenerateScheduleDialog isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByText(/generate schedule/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<GenerateScheduleDialog isOpen={false} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.queryByText(/generate schedule/i)).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<GenerateScheduleDialog isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('has proper dialog structure', () => {
    render(<GenerateScheduleDialog isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
