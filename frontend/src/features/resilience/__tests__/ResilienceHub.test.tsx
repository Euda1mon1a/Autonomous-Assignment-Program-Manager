import { useSystemHealth } from "@/hooks/useResilience";
import { OverallStatus, UtilizationLevel } from "@/types/resilience";
import { fireEvent, render, screen } from "@testing-library/react";
import { ResilienceHub } from "../ResilienceHub";

// Mock the hook
jest.mock("@/hooks/useResilience", () => ({
  useSystemHealth: jest.fn(),
}));

// Mock child components to isolate Hub testing
jest.mock("../components/ResilienceMetrics", () => ({
  ResilienceMetrics: () => <div data-testid="metrics-component">Metrics</div>,
}));
jest.mock("../components/UtilizationChart", () => ({
  UtilizationChart: () => <div data-testid="chart-component">Chart</div>,
}));
jest.mock("../components/BurnoutDashboard", () => ({
  BurnoutDashboard: () => <div data-testid="burnout-component">Burnout</div>,
}));

describe("ResilienceHub", () => {
  const mockHealthData = {
    timestamp: new Date().toISOString(),
    overall_status: OverallStatus.HEALTHY,
    defense_level: "CONTROL",
    utilization: {
      utilization_rate: 0.5,
      level: UtilizationLevel.GREEN,
      current_demand: 50,
      safe_capacity: 100,
    },
    active_fallbacks: [],
    n1_pass: true,
    n2_pass: true,
    immediate_actions: [],
    watch_items: [],
  };

  beforeEach(() => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      refetch: jest.fn(),
      isRefetching: false,
    });
  });

  it("renders key components", () => {
    render(<ResilienceHub />);

    expect(screen.getByText("Resilience Command")).toBeInTheDocument();
    expect(screen.getByTestId("metrics-component")).toBeInTheDocument();
    expect(screen.getByTestId("chart-component")).toBeInTheDocument();
    expect(screen.getByTestId("burnout-component")).toBeInTheDocument();
  });

  it("refreshes data when refresh button is clicked", () => {
    const mockRefetch = jest.fn();
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      refetch: mockRefetch,
      isRefetching: false,
    });

    render(<ResilienceHub />);

    // Find the refresh button by logic: standard button, usually first/icon
    const buttons = screen.getAllByRole("button");
    const refreshBtn = buttons[0];

    fireEvent.click(refreshBtn);
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("toggles simulation mode", () => {
    render(<ResilienceHub />);

    const simulateBtn = screen.getByText("Simulate Crisis");
    fireEvent.click(simulateBtn);

    expect(screen.getByText("Deactivate Sims")).toBeInTheDocument();
    expect(screen.getByText("EMERGENCY PROTOCOLS ACTIVE")).toBeInTheDocument();
  });
});
