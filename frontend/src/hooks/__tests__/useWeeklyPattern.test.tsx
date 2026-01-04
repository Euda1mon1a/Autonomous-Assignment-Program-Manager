/**
 * Tests for useWeeklyPattern hook.
 *
 * Tests cover:
 * - Data fetching and transformation
 * - Mutation success/error handling
 * - Query key management
 * - API integration
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { createEmptyPattern } from "@/types/weekly-pattern";
import {
  useAvailableTemplates,
  useUpdateWeeklyPattern,
  useWeeklyPattern,
  weeklyPatternQueryKeys,
} from "../useWeeklyPattern";

// ============================================================================
// Test Setup
// ============================================================================

const API_BASE = "http://localhost:8000/api";

const mockBackendPatterns = [
  {
    id: "pattern-1",
    rotation_template_id: "template-1",
    day_of_week: 1,
    time_of_day: "AM" as const,
    activity_type: "fm_clinic",
    linked_template_id: "linked-1",
    is_protected: false,
    notes: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "pattern-2",
    rotation_template_id: "template-1",
    day_of_week: 1,
    time_of_day: "PM" as const,
    activity_type: "specialty",
    linked_template_id: "linked-2",
    is_protected: true,
    notes: "Protected slot",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
];

const mockTemplates = {
  items: [
    {
      id: "template-1",
      name: "Clinic",
      activity_type: "clinic",
      abbreviation: "C",
      display_abbreviation: "Clinic",
      font_color: "text-blue-800",
      background_color: "bg-blue-100",
    },
    {
      id: "template-2",
      name: "Inpatient",
      activity_type: "inpatient",
      abbreviation: "IP",
      display_abbreviation: null,
      font_color: null,
      background_color: null,
    },
  ],
  total: 2,
};

// MSW Server setup
const server = setupServer(
  http.get(`${API_BASE}/rotation-templates/:id/patterns`, () => {
    return HttpResponse.json(mockBackendPatterns);
  }),
  http.put(
    `${API_BASE}/rotation-templates/:id/patterns`,
    async ({ request }) => {
      const body = (await request.json()) as { patterns: unknown[] };
      const now = new Date().toISOString();
      const created = body.patterns.map(
        (p: Record<string, unknown>, i: number) => ({
          id: `pattern-new-${i}`,
          rotation_template_id: "template-1",
          ...p,
          created_at: now,
          updated_at: now,
        })
      );
      return HttpResponse.json(created);
    }
  ),
  http.get(`${API_BASE}/rotation-templates`, () => {
    return HttpResponse.json(mockTemplates);
  })
);

beforeEach(() => {
  server.listen({ onUnhandledRequest: "bypass" });
});

afterEach(() => {
  server.resetHandlers();
  server.close();
});

// Query client wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ============================================================================
// Tests
// ============================================================================

describe("useWeeklyPattern", () => {
  it("should fetch and transform patterns correctly", async () => {
    const { result } = renderHook(() => useWeeklyPattern("template-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data?.templateId).toBe("template-1");
    expect(data?.pattern.slots).toHaveLength(14);

    // Check Monday AM slot (day=1, time=AM, index=2)
    const mondayAm = data?.pattern.slots[2];
    expect(mondayAm?.dayOfWeek).toBe(1);
    expect(mondayAm?.timeOfDay).toBe("AM");
    expect(mondayAm?.rotationTemplateId).toBe("linked-1");
  });

  it("should not fetch when templateId is empty", async () => {
    const { result } = renderHook(() => useWeeklyPattern(""), {
      wrapper: createWrapper(),
    });

    // Should not be loading because query is disabled
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it("should handle API error", async () => {
    server.use(
      http.get(`${API_BASE}/rotation-templates/:id/patterns`, () => {
        return HttpResponse.json(
          { detail: "Template not found" },
          { status: 404 }
        );
      })
    );

    const { result } = renderHook(() => useWeeklyPattern("nonexistent"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });

  it("should use correct query keys", () => {
    expect(weeklyPatternQueryKeys.all).toEqual(["weekly-patterns"]);
    expect(weeklyPatternQueryKeys.pattern("test-id")).toEqual([
      "weekly-patterns",
      "test-id",
    ]);
    expect(weeklyPatternQueryKeys.templates()).toEqual([
      "weekly-patterns",
      "templates",
    ]);
  });
});

describe("useUpdateWeeklyPattern", () => {
  it("should update patterns and return transformed result", async () => {
    const { result } = renderHook(() => useUpdateWeeklyPattern(), {
      wrapper: createWrapper(),
    });

    const pattern = createEmptyPattern();
    pattern.slots[2].rotationTemplateId = "new-template";

    result.current.mutate({
      templateId: "template-1",
      pattern,
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.templateId).toBe("template-1");
  });

  it("should handle mutation error", async () => {
    server.use(
      http.put(`${API_BASE}/rotation-templates/:id/patterns`, () => {
        return HttpResponse.json(
          { detail: "Validation error" },
          { status: 400 }
        );
      })
    );

    const { result } = renderHook(() => useUpdateWeeklyPattern(), {
      wrapper: createWrapper(),
    });

    const pattern = createEmptyPattern();

    result.current.mutate({
      templateId: "template-1",
      pattern,
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("useAvailableTemplates", () => {
  it("should fetch and transform templates correctly", async () => {
    const { result } = renderHook(() => useAvailableTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data).toHaveLength(2);

    const firstTemplate = data?.[0];
    expect(firstTemplate?.id).toBe("template-1");
    expect(firstTemplate?.name).toBe("Clinic");
    expect(firstTemplate?.displayAbbreviation).toBe("Clinic");
    expect(firstTemplate?.backgroundColor).toBe("bg-blue-100");

    // Second template should use abbreviation as fallback
    const secondTemplate = data?.[1];
    expect(secondTemplate?.displayAbbreviation).toBe("IP");
  });

  it("should handle API error", async () => {
    server.use(
      http.get(`${API_BASE}/rotation-templates`, () => {
        return HttpResponse.json({ detail: "Server error" }, { status: 500 });
      })
    );

    const { result } = renderHook(() => useAvailableTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
