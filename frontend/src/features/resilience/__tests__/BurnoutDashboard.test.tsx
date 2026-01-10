import { useSystemHealth, useBurnoutRt } from "@/hooks/useResilience";
import { OverallStatus, UtilizationLevel } from "@/types/resilience";
import { render, screen } from "@testing-library/react";
import { BurnoutDashboard } from "../components/BurnoutDashboard";

jest.mock("@/hooks/useResilience", () => ({
  useSystemHealth: jest.fn(),
  useBurnoutRt: jest.fn(),
}));

describe("BurnoutDashboard", () => {
  const mockHealthData = {
    timestamp: new Date().toISOString(),
    overall_status: OverallStatus.HEALTHY,
    defenseLevel: "PREVENTION" as any,
    utilization: {
      utilizationRate: 0.5,
      level: UtilizationLevel.GREEN,
      buffer_remaining: 5,
      wait_time_multiplier: 1.0,
      safe_capacity: 100,
      current_demand: 50,
      theoretical_capacity: 100,
    },
    active_fallbacks: [],
    n1Pass: true,
    n2Pass: true,
    phaseTransitionRisk: "low",
    redundancy_status: [],
    load_shedding_level: "NORMAL" as any,
    crisisMode: false,
    immediate_actions: ["Monitor utilization levels"],
    watch_items: ["Review N-2 coverage"],
  };

  const mockBurnoutData = {
    rt: 0.85,
    status: "declining",
    secondary_cases: 2,
    interventions: [
      "Increase support for high-risk staff",
      "Review workload distribution",
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders analysis and recommendations title", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard />);

    expect(screen.getByText("Analysis & Recommendations")).toBeInTheDocument();
    expect(
      screen.getByText("Actionable insights for system stability")
    ).toBeInTheDocument();
  });

  it("displays immediate actions", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard />);

    expect(screen.getByText("Immediate Actions Required")).toBeInTheDocument();
    expect(screen.getByText("Monitor utilization levels")).toBeInTheDocument();
  });

  it("displays watch items", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard />);

    expect(screen.getByText("Watch Items")).toBeInTheDocument();
    expect(screen.getByText("Review N-2 coverage")).toBeInTheDocument();
  });

  it("shows all clear when no actions or watch items", () => {
    const emptyData = {
      ...mockHealthData,
      immediate_actions: [],
      watch_items: [],
    };

    (useSystemHealth as jest.Mock).mockReturnValue({
      data: emptyData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard />);

    expect(screen.getByText("All Clear")).toBeInTheDocument();
    expect(screen.getByText("No immediate risks detected.")).toBeInTheDocument();
  });

  it("displays burnout Rt when provider IDs are provided", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: mockBurnoutData,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard burnedOutProviderIds={["provider-1"]} />);

    expect(screen.getByText("Burnout Epidemiology")).toBeInTheDocument();
    expect(screen.getByText("Reproduction Number (Rt)")).toBeInTheDocument();
    expect(screen.getByText(/0.85/)).toBeInTheDocument();
  });

  it("displays Rt status and secondary cases", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: mockBurnoutData,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard burnedOutProviderIds={["provider-1"]} />);

    expect(screen.getByText(/Status:/)).toBeInTheDocument();
    expect(screen.getByText("declining")).toBeInTheDocument();
    expect(screen.getByText(/2 secondary cases/)).toBeInTheDocument();
  });

  it("shows loading state for system health", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    const { container } = render(<BurnoutDashboard />);

    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows error state", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Failed to load"),
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard />);

    expect(screen.getByText("Unable to load data")).toBeInTheDocument();
  });

  it("displays Rt interventions", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: mockBurnoutData,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard burnedOutProviderIds={["provider-1"]} />);

    expect(
      screen.getByText("Increase support for high-risk staff")
    ).toBeInTheDocument();
  });

  it("shows high Rt in red when Rt > 1", () => {
    const highRtData = {
      ...mockBurnoutData,
      rt: 1.5,
      status: "growing",
    };

    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: highRtData,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard burnedOutProviderIds={["provider-1"]} />);

    // The Rt value should be displayed
    expect(screen.getByText(/1.5/)).toBeInTheDocument();
  });

  it("does not fetch Rt when no provider IDs provided", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useBurnoutRt as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<BurnoutDashboard burnedOutProviderIds={[]} />);

    expect(screen.queryByText("Burnout Epidemiology")).not.toBeInTheDocument();
  });
});
