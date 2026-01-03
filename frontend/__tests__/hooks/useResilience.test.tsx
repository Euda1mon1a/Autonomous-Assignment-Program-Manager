import { renderHook, waitFor } from "@testing-library/react";
import {
  useSystemHealth,
  useVulnerabilityReport,
  useEmergencyCoverage,
} from "@/hooks/useResilience";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";

// Mock the api module
jest.mock("@/api/resilience", () => ({
  fetchSystemHealth: jest.fn(),
  fetchVulnerabilityReport: jest.fn(),
  requestEmergencyCoverage: jest.fn(),
}));

import {
  fetchSystemHealth,
  fetchVulnerabilityReport,
  requestEmergencyCoverage,
} from "@/api/resilience";

const mockedFetchSystemHealth = fetchSystemHealth as jest.Mock;
const mockedFetchVulnerabilityReport = fetchVulnerabilityReport as jest.Mock;
const mockedRequestEmergencyCoverage = requestEmergencyCoverage as jest.Mock;

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const createWrapper = (queryClient: QueryClient) => {
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return Wrapper;
};

describe("useSystemHealth", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe("Fetching System Health Data", () => {
    it("should fetch system health metrics", async () => {
      const mockData = {
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "healthy",
        utilization: {
          utilization_rate: 0.75,
          level: "YELLOW",
          buffer_remaining: 0.05,
          wait_time_multiplier: 1.2,
          safe_capacity: 100,
          current_demand: 75,
          theoretical_capacity: 120,
        },
        defense_level: "PREVENTION",
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisis_mode: false,
        n1_pass: true,
        n2_pass: true,
        phase_transition_risk: "low",
        immediate_actions: [],
        watch_items: [],
      };
      mockedFetchSystemHealth.mockResolvedValueOnce(mockData);

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockData);
    });

    it("should handle loading state", () => {
      mockedFetchSystemHealth.mockImplementation(() => new Promise(() => {}));

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });

    it("should handle error state", async () => {
      mockedFetchSystemHealth.mockRejectedValueOnce(new Error("API Error"));

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeDefined();
    });
  });

  describe("Defense Level Classification", () => {
    it("should report PREVENTION defense level", async () => {
      mockedFetchSystemHealth.mockResolvedValueOnce({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "healthy",
        defense_level: "PREVENTION",
        utilization: { utilization_rate: 0.6, level: "GREEN" },
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisis_mode: false,
        n1_pass: true,
        n2_pass: true,
        phase_transition_risk: "low",
        immediate_actions: [],
        watch_items: [],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.defense_level).toBe("PREVENTION");
    });

    it("should report EMERGENCY defense level", async () => {
      mockedFetchSystemHealth.mockResolvedValueOnce({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "emergency",
        defense_level: "EMERGENCY",
        utilization: { utilization_rate: 0.95, level: "BLACK" },
        redundancy_status: [],
        load_shedding_level: "CRITICAL",
        active_fallbacks: ["fallback-1"],
        crisis_mode: true,
        n1_pass: false,
        n2_pass: false,
        phase_transition_risk: "critical",
        immediate_actions: ["Activate emergency coverage"],
        watch_items: [],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.defense_level).toBe("EMERGENCY");
      expect(result.current.data?.crisis_mode).toBe(true);
    });
  });

  describe("N-1/N-2 Contingency", () => {
    it("should report n1_pass and n2_pass status", async () => {
      mockedFetchSystemHealth.mockResolvedValueOnce({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "healthy",
        defense_level: "PREVENTION",
        utilization: { utilization_rate: 0.7, level: "GREEN" },
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisis_mode: false,
        n1_pass: true,
        n2_pass: true,
        phase_transition_risk: "low",
        immediate_actions: [],
        watch_items: [],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.n1_pass).toBe(true);
      expect(result.current.data?.n2_pass).toBe(true);
    });

    it("should report n1_pass failure", async () => {
      mockedFetchSystemHealth.mockResolvedValueOnce({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "warning",
        defense_level: "CONTROL",
        utilization: { utilization_rate: 0.85, level: "ORANGE" },
        redundancy_status: [],
        load_shedding_level: "YELLOW",
        active_fallbacks: [],
        crisis_mode: false,
        n1_pass: false,
        n2_pass: false,
        phase_transition_risk: "medium",
        immediate_actions: ["Review coverage gaps"],
        watch_items: ["Faculty utilization high"],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.n1_pass).toBe(false);
    });
  });

  describe("Auto-refresh", () => {
    it("should support refetch", async () => {
      mockedFetchSystemHealth.mockResolvedValue({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "healthy",
        defense_level: "PREVENTION",
        utilization: { utilization_rate: 0.7, level: "GREEN" },
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisis_mode: false,
        n1_pass: true,
        n2_pass: true,
        phase_transition_risk: "low",
        immediate_actions: [],
        watch_items: [],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      await result.current.refetch();

      expect(mockedFetchSystemHealth).toHaveBeenCalledTimes(2);
    });
  });
});

describe("useVulnerabilityReport", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  it("should fetch vulnerability report", async () => {
    const mockData = {
      analyzed_at: "2025-01-01T00:00:00Z",
      period_start: "2025-01-01",
      period_end: "2025-01-31",
      n1_pass: true,
      n2_pass: true,
      phase_transition_risk: "low",
      n1_vulnerabilities: [],
      n2_fatal_pairs: [],
      most_critical_faculty: [],
      recommended_actions: [],
    };
    mockedFetchVulnerabilityReport.mockResolvedValueOnce(mockData);

    const { result } = renderHook(() => useVulnerabilityReport(), {
      wrapper: createWrapper(queryClient),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockData);
  });

  it("should pass params to fetch function", async () => {
    const params = {
      start_date: "2025-01-01",
      end_date: "2025-01-31",
      include_n2: true,
    };
    mockedFetchVulnerabilityReport.mockResolvedValueOnce({});

    renderHook(() => useVulnerabilityReport(params), {
      wrapper: createWrapper(queryClient),
    });

    await waitFor(() => {
      expect(mockedFetchVulnerabilityReport).toHaveBeenCalledWith(params);
    });
  });
});

describe("useEmergencyCoverage", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  it("should request emergency coverage successfully", async () => {
    const mockRequest = {
      person_id: "person-123",
      start_date: "2025-01-15",
      end_date: "2025-01-20",
      reason: "Military deployment",
      is_deployment: true,
    };
    const mockResponse = {
      status: "success" as const,
      replacements_found: 5,
      coverage_gaps: 0,
      requires_manual_review: false,
      details: [],
    };
    mockedRequestEmergencyCoverage.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(queryClient),
    });

    const response = await result.current.mutateAsync(mockRequest);

    expect(mockedRequestEmergencyCoverage).toHaveBeenCalled();
    expect(response).toEqual(mockResponse);
  });

  it("should handle partial coverage status", async () => {
    const mockRequest = {
      person_id: "person-123",
      start_date: "2025-01-15",
      end_date: "2025-01-20",
      reason: "Medical emergency",
      is_deployment: false,
    };
    const mockResponse = {
      status: "partial" as const,
      replacements_found: 3,
      coverage_gaps: 2,
      requires_manual_review: true,
      details: [
        {
          date: "2025-01-18",
          original_assignment: "Morning Shift",
          status: "gap" as const,
        },
      ],
    };
    mockedRequestEmergencyCoverage.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(queryClient),
    });

    const response = await result.current.mutateAsync(mockRequest);

    expect(response.status).toBe("partial");
    expect(response.requires_manual_review).toBe(true);
    expect(response.coverage_gaps).toBe(2);
  });

  it("should handle failed coverage request", async () => {
    const mockRequest = {
      person_id: "person-123",
      start_date: "2025-01-15",
      end_date: "2025-01-20",
      reason: "TDY",
      is_deployment: false,
    };
    const mockResponse = {
      status: "failed" as const,
      replacements_found: 0,
      coverage_gaps: 5,
      requires_manual_review: true,
      details: [],
    };
    mockedRequestEmergencyCoverage.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(queryClient),
    });

    const response = await result.current.mutateAsync(mockRequest);

    expect(response.status).toBe("failed");
    expect(response.coverage_gaps).toBe(5);
  });
});
