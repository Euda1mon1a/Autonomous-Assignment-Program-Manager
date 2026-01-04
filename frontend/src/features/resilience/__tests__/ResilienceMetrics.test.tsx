import { useSystemHealth } from "@/hooks/useResilience";
import { OverallStatus, UtilizationLevel, DefenseLevel } from "@/types/resilience";
import { render, screen } from "@testing-library/react";
import { ResilienceMetrics } from "../components/ResilienceMetrics";

jest.mock("@/hooks/useResilience", () => ({
  useSystemHealth: jest.fn(),
}));

describe("ResilienceMetrics", () => {
  const mockHealthData = {
    timestamp: new Date().toISOString(),
    overall_status: OverallStatus.HEALTHY,
    defense_level: DefenseLevel.PREVENTION as any,
    utilization: {
      utilization_rate: 0.65,
      level: UtilizationLevel.GREEN,
      buffer_remaining: 3.5,
      wait_time_multiplier: 1.2,
      safe_capacity: 100,
      current_demand: 65,
      theoretical_capacity: 100,
    },
    active_fallbacks: [],
    n1_pass: true,
    n2_pass: true,
    phase_transition_risk: "low",
    redundancy_status: [],
    load_shedding_level: "NORMAL" as any,
    crisis_mode: false,
    immediate_actions: [],
    watch_items: [],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders four metric cards", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });

    render(<ResilienceMetrics />);

    expect(screen.getByText("System Health")).toBeInTheDocument();
    expect(screen.getByText("Utilization")).toBeInTheDocument();
    expect(screen.getByText("N-1 Compliance")).toBeInTheDocument();
    expect(screen.getByText("Active Fallbacks")).toBeInTheDocument();
  });

  it("displays correct health status", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });

    render(<ResilienceMetrics />);

    expect(screen.getByText("HEALTHY")).toBeInTheDocument();
    expect(screen.getByText(/Defense:/)).toBeInTheDocument();
  });

  it("displays utilization percentage", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });

    render(<ResilienceMetrics />);

    expect(screen.getByText("65.0%")).toBeInTheDocument();
  });

  it("displays N-1 compliance status", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });

    render(<ResilienceMetrics />);

    expect(screen.getByText("PASS")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    const { container } = render(<ResilienceMetrics />);

    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows error state", () => {
    const errorMessage = "Failed to load resilience metrics";
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error(errorMessage),
    });

    render(<ResilienceMetrics />);

    expect(screen.getByText(/Unable to load resilience metrics/)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("handles N-2 failing while N-1 passes", () => {
    const dataWithN2Fail = {
      ...mockHealthData,
      n2_pass: false,
    };

    (useSystemHealth as jest.Mock).mockReturnValue({
      data: dataWithN2Fail,
      isLoading: false,
      error: null,
    });

    render(<ResilienceMetrics />);

    expect(screen.getByText("N-2 Failing")).toBeInTheDocument();
  });

  it("shows when fallbacks are active", () => {
    const dataWithFallbacks = {
      ...mockHealthData,
      active_fallbacks: ["Fallback-1", "Fallback-2"],
    };

    (useSystemHealth as jest.Mock).mockReturnValue({
      data: dataWithFallbacks,
      isLoading: false,
      error: null,
    });

    render(<ResilienceMetrics />);

    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Contingencies Active")).toBeInTheDocument();
  });
});
