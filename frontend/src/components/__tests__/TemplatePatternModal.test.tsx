/**
 * Tests for TemplatePatternModal component.
 *
 * Tests cover:
 * - Modal opening/closing
 * - Loading states
 * - Error handling
 * - Save/cancel functionality
 * - Integration with WeeklyGridEditor
 *
 * Uses jest.mock instead of MSW (MSW v2 requires Response polyfill not
 * available in jsdom). Hooks are mocked to control data flow.
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TemplatePatternModal } from '../TemplatePatternModal';

// Mock the hooks used by TemplatePatternModal
jest.mock('@/hooks/useWeeklyPattern');

import {
  useWeeklyPattern,
  useUpdateWeeklyPattern,
  useAvailableTemplates,
} from '@/hooks/useWeeklyPattern';

const mockUseWeeklyPattern = useWeeklyPattern as jest.MockedFunction<typeof useWeeklyPattern>;
const mockUseUpdateWeeklyPattern = useUpdateWeeklyPattern as jest.MockedFunction<typeof useUpdateWeeklyPattern>;
const mockUseAvailableTemplates = useAvailableTemplates as jest.MockedFunction<typeof useAvailableTemplates>;

// Default mock pattern data
const mockPatternGrid = {
  slots: [
    { dayOfWeek: 1 as const, timeOfDay: 'AM' as const, rotationTemplateId: 'clinic-1', isProtected: false },
    { dayOfWeek: 1 as const, timeOfDay: 'PM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 2 as const, timeOfDay: 'AM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 2 as const, timeOfDay: 'PM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 3 as const, timeOfDay: 'AM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 3 as const, timeOfDay: 'PM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 4 as const, timeOfDay: 'AM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 4 as const, timeOfDay: 'PM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 5 as const, timeOfDay: 'AM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 5 as const, timeOfDay: 'PM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 6 as const, timeOfDay: 'AM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 6 as const, timeOfDay: 'PM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 0 as const, timeOfDay: 'AM' as const, rotationTemplateId: null, isProtected: false },
    { dayOfWeek: 0 as const, timeOfDay: 'PM' as const, rotationTemplateId: null, isProtected: false },
  ],
  samePatternAllWeeks: true,
};

const mockTemplateRefs = [
  {
    id: 'clinic-1',
    name: 'Clinic',
    displayAbbreviation: 'Clinic',
    backgroundColor: 'bg-blue-100',
    fontColor: 'text-blue-800',
  },
];

describe('TemplatePatternModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    templateId: 'template-1',
    templateName: 'Test Template',
    onSaved: jest.fn(),
  };

  const mockMutateAsync = jest.fn().mockResolvedValue(mockPatternGrid);

  beforeEach(() => {
    jest.clearAllMocks();

    // Default hook mock: data loaded successfully
    mockUseWeeklyPattern.mockReturnValue({
      data: { pattern: mockPatternGrid, templateId: 'template-1', updatedAt: '2024-01-01T00:00:00Z' },
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    } as unknown as ReturnType<typeof useWeeklyPattern>);

    mockUseUpdateWeeklyPattern.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateWeeklyPattern>);

    mockUseAvailableTemplates.mockReturnValue({
      data: mockTemplateRefs,
      isLoading: false,
    } as unknown as ReturnType<typeof useAvailableTemplates>);
  });

  describe('Rendering', () => {
    it('should render modal when isOpen is true', () => {
      render(<TemplatePatternModal {...defaultProps} />);

      expect(screen.getByRole('heading', { name: /Edit Weekly Pattern/i })).toBeInTheDocument();
    });

    it('should not render when isOpen is false', () => {
      render(<TemplatePatternModal {...defaultProps} isOpen={false} />);

      expect(
        screen.queryByRole('heading', { name: /Edit Weekly Pattern/i })
      ).not.toBeInTheDocument();
    });

    it('should display template name', () => {
      render(<TemplatePatternModal {...defaultProps} />);

      expect(screen.getByText('Test Template')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator while fetching data', () => {
      mockUseWeeklyPattern.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof useWeeklyPattern>);

      render(<TemplatePatternModal {...defaultProps} />);

      expect(screen.getByText(/Loading pattern/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should show error message when fetch fails', () => {
      mockUseWeeklyPattern.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Template not found' },
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof useWeeklyPattern>);

      render(<TemplatePatternModal {...defaultProps} />);

      expect(screen.getByText(/Failed to load pattern/i)).toBeInTheDocument();
    });

    it('should show retry button on error', () => {
      mockUseWeeklyPattern.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Server error' },
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof useWeeklyPattern>);

      render(<TemplatePatternModal {...defaultProps} />);

      expect(
        screen.getByRole('button', { name: /Retry/i })
      ).toBeInTheDocument();
    });
  });

  describe('Close Behavior', () => {
    it('should call onClose when close button is clicked', async () => {
      const onClose = jest.fn();
      const user = userEvent.setup();

      render(<TemplatePatternModal {...defaultProps} onClose={onClose} />);

      const closeButton = screen.getByRole('button', { name: /Close modal/i });
      await user.click(closeButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('should call onClose when Cancel button is clicked', async () => {
      const onClose = jest.fn();
      const user = userEvent.setup();

      render(<TemplatePatternModal {...defaultProps} onClose={onClose} />);

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Cancel/i })
        ).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Save Behavior', () => {
    it('should call onSaved after successful save', async () => {
      const onSaved = jest.fn();
      const user = userEvent.setup();

      render(<TemplatePatternModal {...defaultProps} onSaved={onSaved} />);

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Save Pattern/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Pattern/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(onSaved).toHaveBeenCalled();
      });
    });

    it('should show success message after save', async () => {
      const user = userEvent.setup();

      render(<TemplatePatternModal {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Save Pattern/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Pattern/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/Pattern saved!/i)).toBeInTheDocument();
      });
    });

    it('should show error message when save fails', async () => {
      mockMutateAsync.mockRejectedValueOnce(new Error('Validation error'));
      const user = userEvent.setup();

      render(<TemplatePatternModal {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Save Pattern/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Pattern/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to save pattern/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Grid Editor Integration', () => {
    it('should show instructions at bottom', () => {
      render(<TemplatePatternModal {...defaultProps} />);

      expect(screen.getByText(/How to use:/i)).toBeInTheDocument();
    });
  });
});
