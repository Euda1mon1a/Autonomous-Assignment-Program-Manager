/**
 * Tests for EditTemplateModal Component
 * Component: EditTemplateModal - Modal for editing rotation templates
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { EditTemplateModal } from '../EditTemplateModal';

global.fetch = jest.fn();

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('EditTemplateModal', () => {
  const mockTemplate = {
    id: '1',
    name: 'Test Template',
    color: '#FF0000',
  };
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<EditTemplateModal isOpen={true} template={mockTemplate} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByText(/edit template/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<EditTemplateModal isOpen={false} template={mockTemplate} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.queryByText(/edit template/i)).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<EditTemplateModal isOpen={true} template={mockTemplate} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
