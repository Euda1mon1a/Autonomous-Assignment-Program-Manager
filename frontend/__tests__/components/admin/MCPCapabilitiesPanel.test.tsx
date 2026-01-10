/**
 * Tests for MCPCapabilitiesPanel component
 *
 * Tests MCP tool display, categories, search functionality, and interactions
 */
import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MCPCapabilitiesPanel from '@/components/admin/MCPCapabilitiesPanel';

describe('MCPCapabilitiesPanel', () => {
  const mockOnSelectPrompt = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render panel header with title and tool count', () => {
      render(<MCPCapabilitiesPanel />);

      expect(screen.getByText('MCP Capabilities')).toBeInTheDocument();
      expect(screen.getByText(/tools available/i)).toBeInTheDocument();
    });

    it('should render search input', () => {
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      expect(searchInput).toBeInTheDocument();
    });

    it('should render all categories', () => {
      render(<MCPCapabilitiesPanel />);

      expect(screen.getByText('Scheduling & Compliance')).toBeInTheDocument();
      expect(screen.getByText('Resilience Framework')).toBeInTheDocument();
      expect(screen.getByText('Background Tasks')).toBeInTheDocument();
      expect(screen.getByText('Deployment & CI/CD')).toBeInTheDocument();
      expect(screen.getByText('Advanced Analytics')).toBeInTheDocument();
    });

    it('should display category icons', () => {
      render(<MCPCapabilitiesPanel />);

      // Category icons are rendered as emoji text
      expect(screen.getByText('📅')).toBeInTheDocument();
      expect(screen.getByText('🛡️')).toBeInTheDocument();
      expect(screen.getByText('⚡')).toBeInTheDocument();
      expect(screen.getByText('🚀')).toBeInTheDocument();
      expect(screen.getByText('🔬')).toBeInTheDocument();
    });

    it('should expand first category by default in normal mode', () => {
      render(<MCPCapabilitiesPanel />);

      // First category (Scheduling & Compliance) should be expanded
      expect(screen.getByText('validateSchedule')).toBeInTheDocument();
      expect(screen.getByText('detect_conflicts')).toBeInTheDocument();
    });

    it('should not expand any category by default in compact mode', () => {
      render(<MCPCapabilitiesPanel compact={true} />);

      // No tools should be visible initially
      expect(screen.queryByText('validateSchedule')).not.toBeInTheDocument();
    });

    it('should display tool count for each category', () => {
      render(<MCPCapabilitiesPanel />);

      // Scheduling & Compliance has 4 tools
      const schedulingCategory = screen.getByText('Scheduling & Compliance').closest('.mcp-category');
      expect(schedulingCategory).toHaveTextContent('4 tools');
    });
  });

  describe('Category Expansion', () => {
    it('should toggle category when header is clicked', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel compact={true} />);

      // Initially collapsed
      expect(screen.queryByText('validateSchedule')).not.toBeInTheDocument();

      // Click to expand
      const categoryHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(categoryHeader!);

      // Now expanded
      expect(screen.getByText('validateSchedule')).toBeInTheDocument();

      // Click to collapse
      await user.click(categoryHeader!);

      // Now collapsed again
      expect(screen.queryByText('validateSchedule')).not.toBeInTheDocument();
    });

    it('should show toggle indicator', () => {
      render(<MCPCapabilitiesPanel />);

      // First category is expanded, should show minus
      const expandedToggle = screen.getAllByText('−')[0];
      expect(expandedToggle).toBeInTheDocument();

      // Other categories are collapsed, should show plus
      const collapsedToggles = screen.getAllByText('+');
      expect(collapsedToggles.length).toBeGreaterThan(0);
    });

    it('should only expand one category at a time', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      // First category is expanded
      expect(screen.getByText('validateSchedule')).toBeInTheDocument();
      expect(screen.queryByText('check_utilization_threshold')).not.toBeInTheDocument();

      // Click second category
      const resilienceHeader = screen.getByText('Resilience Framework').closest('button');
      await user.click(resilienceHeader!);

      // Second category is expanded, first is collapsed
      expect(screen.queryByText('validateSchedule')).not.toBeInTheDocument();
      expect(screen.getByText('check_utilization_threshold')).toBeInTheDocument();
    });
  });

  describe('Tool Display', () => {
    it('should display tool name as code', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      // Expand category to see tools
      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(schedulingHeader!);

      const toolName = screen.getByText('validateSchedule');
      expect(toolName.tagName).toBe('CODE');
      expect(toolName.className).toContain('mcp-tool-name');
    });

    it('should display tool description', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(schedulingHeader!);

      expect(
        screen.getByText(/Validates schedule against ACGME regulations/i)
      ).toBeInTheDocument();
    });

    it('should display when to use information', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(schedulingHeader!);

      expect(
        screen.getByText(/Before finalizing any schedule/i)
      ).toBeInTheDocument();
    });

    it('should display try button when onSelectPrompt is provided', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel onSelectPrompt={mockOnSelectPrompt} />);

      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(schedulingHeader!);

      // Should have try buttons for tools with example prompts
      const tryButtons = screen.getAllByText(/Try:/i);
      expect(tryButtons.length).toBeGreaterThan(0);
    });

    it('should not display try button when onSelectPrompt is not provided', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(schedulingHeader!);

      // Should not have try buttons
      const tryButtons = screen.queryAllByText(/Try:/i);
      expect(tryButtons.length).toBe(0);
    });
  });

  describe('Search Functionality', () => {
    it('should filter tools by name', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'validate');

      // Should find validateSchedule and validate_deployment
      expect(screen.getByText('validateSchedule')).toBeInTheDocument();
      expect(screen.getByText('validate_deployment')).toBeInTheDocument();

      // Should not find other tools
      expect(screen.queryByText('detect_conflicts')).not.toBeInTheDocument();
    });

    it('should filter tools by description', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'coverage');

      // Should find tools with "coverage" in description
      expect(screen.getByText('run_contingency_analysis')).toBeInTheDocument();
    });

    it('should filter tools by when to use text', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'emergency');

      // Should find tools with "emergency" in whenToUse
      expect(screen.getByText('get_static_fallbacks')).toBeInTheDocument();
    });

    it('should be case insensitive', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'ACGME');

      // Should find tools mentioning ACGME
      expect(screen.getByText('validateSchedule')).toBeInTheDocument();
    });

    it('should show clear button when search has text', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');

      // No clear button initially
      expect(screen.queryByText('✕')).not.toBeInTheDocument();

      await user.type(searchInput, 'validate');

      // Clear button appears
      expect(screen.getByText('✕')).toBeInTheDocument();
    });

    it('should clear search when clear button is clicked', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'validate');

      expect(searchInput).toHaveValue('validate');

      const clearButton = screen.getByText('✕').closest('button');
      await user.click(clearButton!);

      expect(searchInput).toHaveValue('');
    });

    it('should show no results message when search has no matches', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'nonexistenttoolthatdoesntexist');

      expect(
        screen.getByText(/No tools found matching/i)
      ).toBeInTheDocument();
    });

    it('should hide categories with no matching tools', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      // Initially all categories visible
      expect(screen.getByText('Scheduling & Compliance')).toBeInTheDocument();
      expect(screen.getByText('Background Tasks')).toBeInTheDocument();

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'validateSchedule');

      // Only category with matching tool should be visible
      expect(screen.getByText('Scheduling & Compliance')).toBeInTheDocument();
      expect(screen.queryByText('Background Tasks')).not.toBeInTheDocument();
    });

    it('should auto-expand categories with matching tools', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel compact={true} />);

      // Initially no tools visible
      expect(screen.queryByText('check_utilization_threshold')).not.toBeInTheDocument();

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'utilization');

      // Tool becomes visible because its category has a match
      expect(screen.getByText('check_utilization_threshold')).toBeInTheDocument();
    });
  });

  describe('Example Prompt Interaction', () => {
    it('should call onSelectPrompt when try button is clicked', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel onSelectPrompt={mockOnSelectPrompt} />);

      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(schedulingHeader!);

      const tryButton = screen.getAllByText(/Try:/i)[0].closest('button');
      await user.click(tryButton!);

      expect(mockOnSelectPrompt).toHaveBeenCalledTimes(1);
      expect(mockOnSelectPrompt).toHaveBeenCalledWith(
        expect.stringContaining('Validate the schedule')
      );
    });

    it('should pass correct prompt for each tool', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel onSelectPrompt={mockOnSelectPrompt} />);

      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      await user.click(schedulingHeader!);

      // Find the "Try" button for detect_conflicts
      const tryButtons = screen.getAllByText(/Try:/i);
      const detectConflictsButton = tryButtons.find((btn) =>
        btn.textContent?.includes('Check for any scheduling conflicts')
      );

      await user.click(detectConflictsButton!.closest('button')!);

      expect(mockOnSelectPrompt).toHaveBeenCalledWith(
        'Check for any scheduling conflicts in the next 2 weeks'
      );
    });
  });

  describe('Footer', () => {
    it('should display helpful instruction in footer', () => {
      render(<MCPCapabilitiesPanel />);

      expect(
        screen.getByText(/Ask Claude natural questions/i)
      ).toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('should apply compact class when compact prop is true', () => {
      const { container } = render(<MCPCapabilitiesPanel compact={true} />);

      const panel = container.querySelector('.mcp-capabilities-panel');
      expect(panel?.className).toContain('compact');
    });

    it('should not apply compact class when compact prop is false', () => {
      const { container } = render(<MCPCapabilitiesPanel compact={false} />);

      const panel = container.querySelector('.mcp-capabilities-panel');
      expect(panel?.className).not.toContain('compact');
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid category toggling', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const schedulingHeader = screen.getByText('Scheduling & Compliance').closest('button');
      const resilienceHeader = screen.getByText('Resilience Framework').closest('button');

      // Rapid clicking
      await user.click(resilienceHeader!);
      await user.click(schedulingHeader!);
      await user.click(resilienceHeader!);

      // Should still work correctly
      expect(screen.getByText('check_utilization_threshold')).toBeInTheDocument();
    });

    it('should handle search with special characters', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'N-1/N-2');

      // Should find contingency analysis
      expect(screen.getByText('run_contingency_analysis_resilience')).toBeInTheDocument();
    });

    it('should handle empty search gracefully', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, '   ');

      // Should show all categories (whitespace-only search treated as empty)
      expect(screen.getByText('Scheduling & Compliance')).toBeInTheDocument();
    });
  });

  describe('Tool Count Calculation', () => {
    it('should display correct total tool count', () => {
      render(<MCPCapabilitiesPanel />);

      // Total: 4 + 8 + 4 + 7 + 5 = 28 tools
      const toolCount = screen.getByText(/tools available/i);
      expect(toolCount.textContent).toContain('28');
    });

    it('should update category tool count when filtering', async () => {
      const user = userEvent.setup();
      render(<MCPCapabilitiesPanel />);

      const searchInput = screen.getByPlaceholderText('Search tools...');
      await user.type(searchInput, 'validate');

      // Only 2 validate tools (validateSchedule, validate_deployment)
      const schedulingCategory = screen.getByText('Scheduling & Compliance').closest('.mcp-category');
      expect(schedulingCategory).toHaveTextContent('1 tool');

      const deploymentCategory = screen.getByText('Deployment & CI/CD').closest('.mcp-category');
      expect(deploymentCategory).toHaveTextContent('1 tool');
    });
  });
});
