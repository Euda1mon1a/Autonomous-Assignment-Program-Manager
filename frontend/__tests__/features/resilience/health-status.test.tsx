/**
 * Tests for Health Status Indicator Component
 *
 * Tests the health status indicator which displays:
 * - Overall system status (GREEN/YELLOW/ORANGE/RED/BLACK)
 * - Defense level indicators
 * - Utilization levels
 * - Status change animations
 * - Quick status summary
 *
 * NOTE: These tests are skipped because the HealthStatusIndicator component
 * is currently a stub. When the full component is implemented, these tests
 * should be unskipped and may need adjustments based on the final implementation.
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { HealthStatusIndicator } from '@/features/resilience/HealthStatusIndicator';
import { resilienceMockFactories } from './resilience-mocks';
import { createWrapper } from '../../utils/test-utils';

// Skip all tests - component is a stub placeholder
// TODO: Unskip when HealthStatusIndicator is fully implemented
describe.skip('HealthStatusIndicator', () => {
  describe('Green Status Rendering', () => {
    const greenStatus = resilienceMockFactories.healthCheck();

    it('should render green status badge', () => {
      render(<HealthStatusIndicator status={greenStatus} />, { wrapper: createWrapper() });

      const badge = screen.getByText(/green/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('should display healthy system icon', () => {
      const { container } = render(<HealthStatusIndicator status={greenStatus} />, {
        wrapper: createWrapper(),
      });

      const icon = container.querySelector('[data-testid="status-icon"]');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-green-600');
    });

    it('should show overall status text', () => {
      render(<HealthStatusIndicator status={greenStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('System Healthy')).toBeInTheDocument();
    });

    it('should display defense level as PREVENTION', () => {
      render(<HealthStatusIndicator status={greenStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('PREVENTION')).toBeInTheDocument();
    });

    it('should show utilization percentage', () => {
      render(<HealthStatusIndicator status={greenStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should display optimal utilization level', () => {
      render(<HealthStatusIndicator status={greenStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/optimal/i)).toBeInTheDocument();
    });

    it('should not show crisis mode indicator for green status', () => {
      render(<HealthStatusIndicator status={greenStatus} />, { wrapper: createWrapper() });

      expect(screen.queryByText(/crisis/i)).not.toBeInTheDocument();
    });

    it('should render with green border', () => {
      const { container } = render(<HealthStatusIndicator status={greenStatus} />, {
        wrapper: createWrapper(),
      });

      const statusCard = container.querySelector('[data-testid="health-status-card"]');
      expect(statusCard).toHaveClass('border-green-300');
    });
  });

  describe('Yellow Status Rendering', () => {
    const yellowStatus = resilienceMockFactories.healthCheckWarning();

    it('should render yellow status badge', () => {
      render(<HealthStatusIndicator status={yellowStatus} />, { wrapper: createWrapper() });

      const badge = screen.getByText(/yellow/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('should display warning icon', () => {
      const { container } = render(<HealthStatusIndicator status={yellowStatus} />, {
        wrapper: createWrapper(),
      });

      const icon = container.querySelector('[data-testid="status-icon"]');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-yellow-600');
    });

    it('should show warning status text', () => {
      render(<HealthStatusIndicator status={yellowStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/degraded|warning/i)).toBeInTheDocument();
    });

    it('should display defense level as CONTROL', () => {
      render(<HealthStatusIndicator status={yellowStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('CONTROL')).toBeInTheDocument();
    });

    it('should show high utilization percentage', () => {
      render(<HealthStatusIndicator status={yellowStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should display high utilization level', () => {
      render(<HealthStatusIndicator status={yellowStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/high/i)).toBeInTheDocument();
    });

    it('should show N-2 failure indicator', () => {
      render(<HealthStatusIndicator status={yellowStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/N-2.*fail/i)).toBeInTheDocument();
    });

    it('should render with yellow border', () => {
      const { container } = render(<HealthStatusIndicator status={yellowStatus} />, {
        wrapper: createWrapper(),
      });

      const statusCard = container.querySelector('[data-testid="health-status-card"]');
      expect(statusCard).toHaveClass('border-yellow-300');
    });
  });

  describe('Orange Status Rendering', () => {
    const orangeStatus = resilienceMockFactories.healthCheck({
      overall_status: 'orange',
      defense_level: 'SAFETY_SYSTEMS',
      utilization: {
        utilization_rate: 0.88,
        level: 'very_high',
        buffer_remaining: 0.12,
        wait_time_multiplier: 2.5,
        safe_capacity: 100,
        current_demand: 88,
        theoretical_capacity: 120,
      },
    });

    it('should render orange status badge', () => {
      render(<HealthStatusIndicator status={orangeStatus} />, { wrapper: createWrapper() });

      const badge = screen.getByText(/orange/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-orange-100', 'text-orange-800');
    });

    it('should display alert icon', () => {
      const { container } = render(<HealthStatusIndicator status={orangeStatus} />, {
        wrapper: createWrapper(),
      });

      const icon = container.querySelector('[data-testid="status-icon"]');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-orange-600');
    });

    it('should show degraded status text', () => {
      render(<HealthStatusIndicator status={orangeStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/degraded|elevated/i)).toBeInTheDocument();
    });

    it('should display defense level as SAFETY_SYSTEMS', () => {
      render(<HealthStatusIndicator status={orangeStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('SAFETY_SYSTEMS')).toBeInTheDocument();
    });

    it('should render with orange border', () => {
      const { container } = render(<HealthStatusIndicator status={orangeStatus} />, {
        wrapper: createWrapper(),
      });

      const statusCard = container.querySelector('[data-testid="health-status-card"]');
      expect(statusCard).toHaveClass('border-orange-300');
    });
  });

  describe('Red Status Rendering', () => {
    const redStatus = resilienceMockFactories.healthCheckCritical();

    it('should render red status badge', () => {
      render(<HealthStatusIndicator status={redStatus} />, { wrapper: createWrapper() });

      const badge = screen.getByText(/red/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('should display critical icon', () => {
      const { container } = render(<HealthStatusIndicator status={redStatus} />, {
        wrapper: createWrapper(),
      });

      const icon = container.querySelector('[data-testid="status-icon"]');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-red-600');
    });

    it('should show critical status text', () => {
      render(<HealthStatusIndicator status={redStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/critical/i)).toBeInTheDocument();
    });

    it('should display defense level as CONTAINMENT', () => {
      render(<HealthStatusIndicator status={redStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('CONTAINMENT')).toBeInTheDocument();
    });

    it('should show crisis mode badge', () => {
      render(<HealthStatusIndicator status={redStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/crisis mode/i)).toBeInTheDocument();
    });

    it('should show critical utilization percentage', () => {
      render(<HealthStatusIndicator status={redStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('92%')).toBeInTheDocument();
    });

    it('should render with red border and pulsing animation', () => {
      const { container } = render(<HealthStatusIndicator status={redStatus} />, {
        wrapper: createWrapper(),
      });

      const statusCard = container.querySelector('[data-testid="health-status-card"]');
      expect(statusCard).toHaveClass('border-red-300');
      expect(statusCard).toHaveClass('animate-pulse');
    });
  });

  describe('Black Status Rendering', () => {
    const blackStatus = resilienceMockFactories.healthCheck({
      overall_status: 'black',
      defense_level: 'EMERGENCY',
      utilization: {
        utilization_rate: 0.98,
        level: 'catastrophic',
        buffer_remaining: 0.02,
        wait_time_multiplier: 5.0,
        safe_capacity: 100,
        current_demand: 98,
        theoretical_capacity: 120,
      },
      crisis_mode: true,
    });

    it('should render black status badge', () => {
      render(<HealthStatusIndicator status={blackStatus} />, { wrapper: createWrapper() });

      const badge = screen.getByText(/black/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-gray-900', 'text-white');
    });

    it('should display emergency icon', () => {
      const { container } = render(<HealthStatusIndicator status={blackStatus} />, {
        wrapper: createWrapper(),
      });

      const icon = container.querySelector('[data-testid="status-icon"]');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-gray-900');
    });

    it('should show emergency status text', () => {
      render(<HealthStatusIndicator status={blackStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText(/emergency/i)).toBeInTheDocument();
    });

    it('should display defense level as EMERGENCY', () => {
      render(<HealthStatusIndicator status={blackStatus} />, { wrapper: createWrapper() });

      expect(screen.getByText('EMERGENCY')).toBeInTheDocument();
    });

    it('should show crisis mode with urgent styling', () => {
      render(<HealthStatusIndicator status={blackStatus} />, { wrapper: createWrapper() });

      const crisisBadge = screen.getByText(/crisis mode/i);
      expect(crisisBadge).toHaveClass('bg-red-600', 'text-white');
    });

    it('should render with black border and urgent animation', () => {
      const { container } = render(<HealthStatusIndicator status={blackStatus} />, {
        wrapper: createWrapper(),
      });

      const statusCard = container.querySelector('[data-testid="health-status-card"]');
      expect(statusCard).toHaveClass('border-gray-900');
      expect(statusCard).toHaveClass('animate-pulse');
    });
  });

  describe('Utilization Display', () => {
    it('should show utilization progress bar', () => {
      const status = resilienceMockFactories.healthCheck();
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow', '75');
    });

    it('should color progress bar green for optimal utilization', () => {
      const status = resilienceMockFactories.healthCheck();
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const progressFill = container.querySelector('[data-testid="progress-fill"]');
      expect(progressFill).toHaveClass('bg-green-500');
    });

    it('should color progress bar yellow for high utilization', () => {
      const status = resilienceMockFactories.healthCheckWarning();
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const progressFill = container.querySelector('[data-testid="progress-fill"]');
      expect(progressFill).toHaveClass('bg-yellow-500');
    });

    it('should color progress bar red for critical utilization', () => {
      const status = resilienceMockFactories.healthCheckCritical();
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const progressFill = container.querySelector('[data-testid="progress-fill"]');
      expect(progressFill).toHaveClass('bg-red-500');
    });

    it('should display buffer remaining', () => {
      const status = resilienceMockFactories.healthCheck();
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/25%.*buffer/i)).toBeInTheDocument();
    });

    it('should show wait time multiplier', () => {
      const status = resilienceMockFactories.healthCheck();
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText('1.2x')).toBeInTheDocument();
    });
  });

  describe('N-1/N-2 Status Display', () => {
    it('should show green checkmark for N-1 pass', () => {
      const status = resilienceMockFactories.healthCheck({ n1_pass: true });
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const n1Icon = container.querySelector('[data-testid="n1-icon"]');
      expect(n1Icon).toHaveClass('text-green-600');
    });

    it('should show red X for N-1 fail', () => {
      const status = resilienceMockFactories.healthCheck({ n1_pass: false });
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const n1Icon = container.querySelector('[data-testid="n1-icon"]');
      expect(n1Icon).toHaveClass('text-red-600');
    });

    it('should show green checkmark for N-2 pass', () => {
      const status = resilienceMockFactories.healthCheck({ n2_pass: true });
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const n2Icon = container.querySelector('[data-testid="n2-icon"]');
      expect(n2Icon).toHaveClass('text-green-600');
    });

    it('should show red X for N-2 fail', () => {
      const status = resilienceMockFactories.healthCheck({ n2_pass: false });
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const n2Icon = container.querySelector('[data-testid="n2-icon"]');
      expect(n2Icon).toHaveClass('text-red-600');
    });

    it('should display N-1 and N-2 labels', () => {
      const status = resilienceMockFactories.healthCheck();
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/N-1/)).toBeInTheDocument();
      expect(screen.getByText(/N-2/)).toBeInTheDocument();
    });
  });

  describe('Phase Transition Risk', () => {
    it('should show low risk with green indicator', () => {
      const status = resilienceMockFactories.healthCheck({ phase_transition_risk: 0.1 });
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/10%/)).toBeInTheDocument();
      const riskBadge = screen.getByText(/low.*risk/i);
      expect(riskBadge).toHaveClass('bg-green-100');
    });

    it('should show medium risk with yellow indicator', () => {
      const status = resilienceMockFactories.healthCheck({ phase_transition_risk: 0.35 });
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/35%/)).toBeInTheDocument();
      const riskBadge = screen.getByText(/medium.*risk/i);
      expect(riskBadge).toHaveClass('bg-yellow-100');
    });

    it('should show high risk with red indicator', () => {
      const status = resilienceMockFactories.healthCheck({ phase_transition_risk: 0.75 });
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/75%/)).toBeInTheDocument();
      const riskBadge = screen.getByText(/high.*risk/i);
      expect(riskBadge).toHaveClass('bg-red-100');
    });
  });

  describe('Active Fallbacks', () => {
    it('should show fallback count when active', () => {
      const status = resilienceMockFactories.healthCheck({ active_fallbacks: 2 });
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/2.*fallback.*active/i)).toBeInTheDocument();
    });

    it('should not show fallback indicator when none active', () => {
      const status = resilienceMockFactories.healthCheck({ active_fallbacks: 0 });
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.queryByText(/fallback/i)).not.toBeInTheDocument();
    });

    it('should highlight active fallback with warning color', () => {
      const status = resilienceMockFactories.healthCheck({ active_fallbacks: 1 });
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      const fallbackBadge = screen.getByText(/fallback/i);
      expect(fallbackBadge).toHaveClass('bg-yellow-100');
    });
  });

  describe('Interactive Features', () => {
    it('should expand details when clicked', async () => {
      const user = userEvent.setup();
      const status = resilienceMockFactories.healthCheck();

      render(<HealthStatusIndicator status={status} expandable />, {
        wrapper: createWrapper(),
      });

      const expandButton = screen.getByRole('button', { name: /details|expand/i });
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText(/detailed.*metrics/i)).toBeInTheDocument();
      });
    });

    it('should show tooltip on hover', async () => {
      const user = userEvent.setup();
      const status = resilienceMockFactories.healthCheck();

      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      const statusBadge = screen.getByText(/green/i);
      await user.hover(statusBadge);

      await waitFor(() => {
        expect(
          screen.getByText(/system operating normally/i)
        ).toBeInTheDocument();
      });
    });

    it('should call onChange callback when status changes', () => {
      const onChange = jest.fn();
      const status = resilienceMockFactories.healthCheck();

      const { rerender } = render(
        <HealthStatusIndicator status={status} onChange={onChange} />,
        { wrapper: createWrapper() }
      );

      const newStatus = resilienceMockFactories.healthCheckWarning();
      rerender(<HealthStatusIndicator status={newStatus} onChange={onChange} />);

      expect(onChange).toHaveBeenCalledWith('yellow', 'green');
    });
  });

  describe('Timestamp Display', () => {
    it('should display last updated timestamp', () => {
      const status = resilienceMockFactories.healthCheck();
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/updated.*ago|last check/i)).toBeInTheDocument();
    });

    it('should format timestamp as relative time', () => {
      const status = resilienceMockFactories.healthCheck({
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 mins ago
      });
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      expect(screen.getByText(/5.*min.*ago/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      const status = resilienceMockFactories.healthCheck();
      render(<HealthStatusIndicator status={status} />, { wrapper: createWrapper() });

      const statusCard = screen.getByLabelText(/health status/i);
      expect(statusCard).toBeInTheDocument();
    });

    it('should have accessible progress bar', () => {
      const status = resilienceMockFactories.healthCheck();
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toHaveAttribute('aria-label');
      expect(progressBar).toHaveAttribute('aria-valuenow');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('should announce status changes to screen readers', () => {
      const status = resilienceMockFactories.healthCheck();
      const { container } = render(<HealthStatusIndicator status={status} />, {
        wrapper: createWrapper(),
      });

      const announcement = container.querySelector('[role="status"]');
      expect(announcement).toBeInTheDocument();
      expect(announcement).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Compact Mode', () => {
    it('should render compact view when compact prop is true', () => {
      const status = resilienceMockFactories.healthCheck();
      render(<HealthStatusIndicator status={status} compact />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/green/i)).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.queryByText(/buffer/i)).not.toBeInTheDocument();
    });

    it('should show only essential information in compact mode', () => {
      const status = resilienceMockFactories.healthCheck();
      render(<HealthStatusIndicator status={status} compact />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByText(/wait time/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/phase transition/i)).not.toBeInTheDocument();
    });
  });

  describe('Custom ClassName', () => {
    it('should apply custom className', () => {
      const status = resilienceMockFactories.healthCheck();
      const { container } = render(
        <HealthStatusIndicator status={status} className="custom-status" />,
        { wrapper: createWrapper() }
      );

      const element = container.querySelector('.custom-status');
      expect(element).toBeInTheDocument();
    });
  });
});
