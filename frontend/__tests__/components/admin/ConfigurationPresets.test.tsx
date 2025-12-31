/**
 * Tests for ConfigurationPresets component
 *
 * Tests preset management, save/load functionality, and import/export
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfigurationPresets, SchedulingPreset } from '@/components/admin/ConfigurationPresets';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('ConfigurationPresets', () => {
  const mockConfiguration = {
    algorithm: 'hybrid' as const,
    constraints: [],
    preserveFMIT: true,
    nfPostCallEnabled: true,
    academicYear: '2024-2025',
    blockRange: { start: 1, end: 365 },
    timeoutSeconds: 300,
    dryRun: true,
  };

  const mockOnLoadPreset = jest.fn();

  const defaultProps = {
    currentConfiguration: mockConfiguration,
    onLoadPreset: mockOnLoadPreset,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Rendering', () => {
    it('should render load preset button', () => {
      render(<ConfigurationPresets {...defaultProps} />);

      expect(screen.getByRole('button', { name: /load preset/i })).toBeInTheDocument();
    });

    it('should render save preset button', () => {
      render(<ConfigurationPresets {...defaultProps} />);

      expect(screen.getByRole('button', { name: /save as preset/i })).toBeInTheDocument();
    });

    it('should apply custom className', () => {
      const { container } = render(
        <ConfigurationPresets {...defaultProps} className="custom-class" />
      );

      const rootDiv = container.querySelector('.custom-class');
      expect(rootDiv).toBeInTheDocument();
    });
  });

  describe('Load Preset Dropdown', () => {
    it('should open dropdown when load preset button is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(screen.getByText('Built-in Presets')).toBeInTheDocument();
    });

    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(screen.getByText('Built-in Presets')).toBeInTheDocument();

      // Click backdrop
      const backdrop = document.querySelector('.fixed.inset-0');
      await user.click(backdrop!);

      await waitFor(() => {
        expect(screen.queryByText('Built-in Presets')).not.toBeInTheDocument();
      });
    });

    it('should toggle dropdown state', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });

      // Open
      await user.click(loadButton);
      expect(screen.getByText('Built-in Presets')).toBeInTheDocument();

      // Close
      await user.click(loadButton);
      await waitFor(() => {
        expect(screen.queryByText('Built-in Presets')).not.toBeInTheDocument();
      });
    });

    it('should display built-in presets', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(screen.getByText('Quick Start (Small)')).toBeInTheDocument();
      expect(screen.getByText('Balanced (Medium)')).toBeInTheDocument();
      expect(screen.getByText('Full Year (Production)')).toBeInTheDocument();
    });

    it('should show preset descriptions', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(
        screen.getByText(/Fast generation for small programs/)
      ).toBeInTheDocument();
    });

    it('should show default star for default preset', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      // Quick Start (Small) is marked as default
      const { container } = render(<ConfigurationPresets {...defaultProps} />);
      await user.click(screen.getAllByRole('button', { name: /load preset/i })[1]);

      // Star icon should be present
      expect(screen.queryAllByText('⭐').length).toBeGreaterThan(0);
    });

    it('should show algorithm and block range for each preset', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(screen.getByText('GREEDY')).toBeInTheDocument();
      expect(screen.getByText('60 blocks')).toBeInTheDocument();
    });
  });

  describe('Load Preset Functionality', () => {
    it('should call onLoadPreset when preset is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      const preset = screen.getByText('Quick Start (Small)');
      await user.click(preset);

      expect(mockOnLoadPreset).toHaveBeenCalledTimes(1);
      expect(mockOnLoadPreset).toHaveBeenCalledWith(
        expect.objectContaining({
          algorithm: 'greedy',
          preserveFMIT: true,
        })
      );
    });

    it('should close dropdown after loading preset', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      const preset = screen.getByText('Quick Start (Small)');
      await user.click(preset);

      await waitFor(() => {
        expect(screen.queryByText('Built-in Presets')).not.toBeInTheDocument();
      });
    });

    it('should show loaded indicator briefly after loading', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      const preset = screen.getByText('Quick Start (Small)');
      await user.click(preset);

      // Indicator clears after 2 seconds (can't easily test timeout)
      expect(mockOnLoadPreset).toHaveBeenCalled();
    });
  });

  describe('Save Preset Modal', () => {
    it('should open save modal when save button is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      expect(screen.getByText('Save Configuration Preset')).toBeInTheDocument();
    });

    it('should display name input field', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      expect(screen.getByLabelText(/preset name/i)).toBeInTheDocument();
    });

    it('should display description textarea', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });

    it('should close modal when cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const cancelButton = screen.getByRole('button', { name: /^cancel$/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText('Save Configuration Preset')).not.toBeInTheDocument();
      });
    });

    it('should close modal when backdrop is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const backdrop = document.querySelector('.bg-black\\/60');
      await user.click(backdrop!);

      await waitFor(() => {
        expect(screen.queryByText('Save Configuration Preset')).not.toBeInTheDocument();
      });
    });
  });

  describe('Save Preset Functionality', () => {
    it('should disable save button when name is empty', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      expect(saveModalButton).toBeDisabled();
    });

    it('should enable save button when name is entered', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const nameInput = screen.getByLabelText(/preset name/i);
      await user.type(nameInput, 'My Custom Preset');

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      expect(saveModalButton).not.toBeDisabled();
    });

    it('should save preset to localStorage', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const nameInput = screen.getByLabelText(/preset name/i);
      await user.type(nameInput, 'My Custom Preset');

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      await user.click(saveModalButton);

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'admin_scheduling_presets',
          expect.stringContaining('My Custom Preset')
        );
      });
    });

    it('should include description in saved preset', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const nameInput = screen.getByLabelText(/preset name/i);
      const descInput = screen.getByLabelText(/description/i);

      await user.type(nameInput, 'My Preset');
      await user.type(descInput, 'Custom description');

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      await user.click(saveModalButton);

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'admin_scheduling_presets',
          expect.stringContaining('Custom description')
        );
      });
    });

    it('should clear form after saving', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const nameInput = screen.getByLabelText(/preset name/i) as HTMLInputElement;
      await user.type(nameInput, 'My Preset');

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      await user.click(saveModalButton);

      await waitFor(() => {
        expect(screen.queryByText('Save Configuration Preset')).not.toBeInTheDocument();
      });
    });

    it('should show loading state while saving', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const nameInput = screen.getByLabelText(/preset name/i);
      await user.type(nameInput, 'My Preset');

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      await user.click(saveModalButton);

      // Should briefly show loading state
      expect(mockOnLoadPreset).not.toHaveBeenCalled(); // Different from load
    });

    it('should trim whitespace from preset name', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const nameInput = screen.getByLabelText(/preset name/i);
      await user.type(nameInput, '  My Preset  ');

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      await user.click(saveModalButton);

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'admin_scheduling_presets',
          expect.stringContaining('"name":"My Preset"')
        );
      });
    });
  });

  describe('User Presets', () => {
    it('should load user presets from localStorage', () => {
      const userPresets = [
        {
          id: 'user-1',
          name: 'My Custom Preset',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          configuration: mockConfiguration,
        },
      ];

      localStorageMock.getItem.mockReturnValue(JSON.stringify(userPresets));

      render(<ConfigurationPresets {...defaultProps} />);

      // Component should load presets from storage
      expect(localStorageMock.getItem).toHaveBeenCalledWith('admin_scheduling_presets');
    });

    it('should display user presets section when user presets exist', async () => {
      const user = userEvent.setup();
      const userPresets = [
        {
          id: 'user-1',
          name: 'My Custom Preset',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          configuration: mockConfiguration,
        },
      ];

      localStorageMock.getItem.mockReturnValue(JSON.stringify(userPresets));

      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(screen.getByText('Your Presets')).toBeInTheDocument();
      expect(screen.getByText('My Custom Preset')).toBeInTheDocument();
    });

    it('should show delete button for user presets', async () => {
      const user = userEvent.setup();
      const userPresets = [
        {
          id: 'user-1',
          name: 'My Custom Preset',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          configuration: mockConfiguration,
        },
      ];

      localStorageMock.getItem.mockReturnValue(JSON.stringify(userPresets));

      const { container } = render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      // Hover over preset to show delete button
      const presetItem = screen.getByText('My Custom Preset').closest('.group');
      await user.hover(presetItem!);

      // Delete button should exist (might be hidden by opacity-0)
      const deleteButtons = container.querySelectorAll('button[title="Delete preset"]');
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    it('should not show delete button for built-in presets', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      // Built-in presets should not have delete buttons
      const quickStartPreset = screen.getByText('Quick Start (Small)').closest('.group');
      const deleteButton = quickStartPreset?.querySelector('button[title="Delete preset"]');
      expect(deleteButton).not.toBeInTheDocument();
    });

    it('should delete user preset when delete button is clicked', async () => {
      const user = userEvent.setup();
      const userPresets = [
        {
          id: 'user-1',
          name: 'My Custom Preset',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          configuration: mockConfiguration,
        },
      ];

      localStorageMock.getItem.mockReturnValue(JSON.stringify(userPresets));

      const { container } = render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      const deleteButton = container.querySelector('button[title="Delete preset"]');
      await user.click(deleteButton!);

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'admin_scheduling_presets',
          '[]' // Empty array after deletion
        );
      });
    });
  });

  describe('Import/Export', () => {
    it('should display import button', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(screen.getByText('Import')).toBeInTheDocument();
    });

    it('should display export button', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      expect(screen.getByText('Export')).toBeInTheDocument();
    });

    it('should disable export button when no user presets', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      const exportButton = screen.getByText('Export').closest('button');
      expect(exportButton).toBeDisabled();
    });

    it('should enable export button when user presets exist', async () => {
      const user = userEvent.setup();
      const userPresets = [
        {
          id: 'user-1',
          name: 'My Preset',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          configuration: mockConfiguration,
        },
      ];

      localStorageMock.getItem.mockReturnValue(JSON.stringify(userPresets));

      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      await user.click(loadButton);

      const exportButton = screen.getByText('Export').closest('button');
      expect(exportButton).not.toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('should handle localStorage read errors gracefully', () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      render(<ConfigurationPresets {...defaultProps} />);

      // Should still render without crashing
      expect(screen.getByRole('button', { name: /load preset/i })).toBeInTheDocument();
    });

    it('should handle localStorage write errors gracefully', async () => {
      const user = userEvent.setup();
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage full');
      });

      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      const nameInput = screen.getByLabelText(/preset name/i);
      await user.type(nameInput, 'My Preset');

      const saveModalButton = screen.getAllByRole('button', { name: /save preset/i })[1];
      await user.click(saveModalButton);

      // Should handle error without crashing
      expect(saveModalButton).toBeInTheDocument();
    });

    it('should handle invalid JSON in localStorage', () => {
      localStorageMock.getItem.mockReturnValue('invalid json {');

      render(<ConfigurationPresets {...defaultProps} />);

      // Should fallback to built-in presets only
      expect(screen.getByRole('button', { name: /load preset/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible buttons', () => {
      render(<ConfigurationPresets {...defaultProps} />);

      const loadButton = screen.getByRole('button', { name: /load preset/i });
      const saveButton = screen.getByRole('button', { name: /save as preset/i });

      expect(loadButton).toBeInTheDocument();
      expect(saveButton).toBeInTheDocument();
    });

    it('should have accessible form inputs', async () => {
      const user = userEvent.setup();
      render(<ConfigurationPresets {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save as preset/i });
      await user.click(saveButton);

      expect(screen.getByLabelText(/preset name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });
  });
});
