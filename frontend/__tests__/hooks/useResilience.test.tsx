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
          utilizationRate: 0.75,
          level: "YELLOW",
          buffer_remaining: 0.05,
          wait_time_multiplier: 1.2,
          safe_capacity: 100,
          current_demand: 75,
          theoretical_capacity: 120,
        },
        defenseLevel: "PREVENTION",
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisisMode: false,
        n1Pass: true,
        n2Pass: true,
        phaseTransitionRisk: "low",
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
        defenseLevel: "PREVENTION",
        utilization: { utilizationRate: 0.6, level: "GREEN" },
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisisMode: false,
        n1Pass: true,
        n2Pass: true,
        phaseTransitionRisk: "low",
        immediate_actions: [],
        watch_items: [],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.defenseLevel).toBe("PREVENTION");
    });

    it("should report EMERGENCY defense level", async () => {
      mockedFetchSystemHealth.mockResolvedValueOnce({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "emergency",
        defenseLevel: "EMERGENCY",
        utilization: { utilizationRate: 0.95, level: "BLACK" },
        redundancy_status: [],
        load_shedding_level: "CRITICAL",
        active_fallbacks: ["fallback-1"],
        crisisMode: true,
        n1Pass: false,
        n2Pass: false,
        phaseTransitionRisk: "critical",
        immediate_actions: ["Activate emergency coverage"],
        watch_items: [],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.defenseLevel).toBe("EMERGENCY");
      expect(result.current.data?.crisisMode).toBe(true);
    });
  });

  describe("N-1/N-2 Contingency", () => {
    it("should report n1Pass and n2Pass status", async () => {
      mockedFetchSystemHealth.mockResolvedValueOnce({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "healthy",
        defenseLevel: "PREVENTION",
        utilization: { utilizationRate: 0.7, level: "GREEN" },
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisisMode: false,
        n1Pass: true,
        n2Pass: true,
        phaseTransitionRisk: "low",
        immediate_actions: [],
        watch_items: [],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.n1Pass).toBe(true);
      expect(result.current.data?.n2Pass).toBe(true);
    });

    it("should report n1Pass failure", async () => {
      mockedFetchSystemHealth.mockResolvedValueOnce({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "warning",
        defenseLevel: "CONTROL",
        utilization: { utilizationRate: 0.85, level: "ORANGE" },
        redundancy_status: [],
        load_shedding_level: "YELLOW",
        active_fallbacks: [],
        crisisMode: false,
        n1Pass: false,
        n2Pass: false,
        phaseTransitionRisk: "medium",
        immediate_actions: ["Review coverage gaps"],
        watch_items: ["Faculty utilization high"],
      });

      const { result } = renderHook(() => useSystemHealth(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.n1Pass).toBe(false);
    });
  });

  describe("Auto-refresh", () => {
    it("should support refetch", async () => {
      mockedFetchSystemHealth.mockResolvedValue({
        timestamp: "2025-01-01T00:00:00Z",
        overall_status: "healthy",
        defenseLevel: "PREVENTION",
        utilization: { utilizationRate: 0.7, level: "GREEN" },
        redundancy_status: [],
        load_shedding_level: "NORMAL",
        active_fallbacks: [],
        crisisMode: false,
        n1Pass: true,
        n2Pass: true,
        phaseTransitionRisk: "low",
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
      periodStart: "2025-01-01",
      periodEnd: "2025-01-31",
      n1Pass: true,
      n2Pass: true,
      phaseTransitionRisk: "low",
      n1_vulnerabilities: [],
      n2_fatal_pairs: [],
      mostCriticalFaculty: [],
      recommendedActions: [],
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
      startDate: "2025-01-01",
      endDate: "2025-01-31",
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
      personId: "person-123",
      startDate: "2025-01-15",
      endDate: "2025-01-20",
      reason: "Military deployment",
      isDeployment: true,
    };
    const mockResponse = {
      status: "success" as const,
      replacementsFound: 5,
      coverageGaps: 0,
      requiresManualReview: false,
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
      personId: "person-123",
      startDate: "2025-01-15",
      endDate: "2025-01-20",
      reason: "Medical emergency",
      isDeployment: false,
    };
    const mockResponse = {
      status: "partial" as const,
      replacementsFound: 3,
      coverageGaps: 2,
      requiresManualReview: true,
      details: [
        {
          date: "2025-01-18",
          originalAssignment: "Morning Shift",
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
    expect(response.requiresManualReview).toBe(true);
    expect(response.coverageGaps).toBe(2);
  });

  it("should handle failed coverage request", async () => {
    const mockRequest = {
      personId: "person-123",
      startDate: "2025-01-15",
      endDate: "2025-01-20",
      reason: "TDY",
      isDeployment: false,
    };
    const mockResponse = {
      status: "failed" as const,
      replacementsFound: 0,
      coverageGaps: 5,
      requiresManualReview: true,
      details: [],
    };
    mockedRequestEmergencyCoverage.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(queryClient),
    });

    const response = await result.current.mutateAsync(mockRequest);

    expect(response.status).toBe("failed");
    expect(response.coverageGaps).toBe(5);
  });
});
