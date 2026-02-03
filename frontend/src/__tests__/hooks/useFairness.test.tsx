/**
 * Tests for fairness audit hooks.
 */
import { renderHook, waitFor } from '@/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useFairnessAudit,
  useFairnessSummary,
  useFacultyWorkload,
} from '@/hooks/useFairness';
import * as api from '@/lib/api';

jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useFairnessAudit', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches audit data when dates provided', async () => {
    mockedApi.get.mockResolvedValueOnce({
      period: { start: '2025-01-01', end: '2025-01-07' },
      facultyCount: 2,
      categoryStats: {
        call: { min: 0, max: 1, mean: 0.5, spread: 1 },
        fmit: { min: 0, max: 1, mean: 0.5, spread: 1 },
        clinic: { min: 1, max: 2, mean: 1.5, spread: 1 },
        admin: { min: 0, max: 1, mean: 0.5, spread: 1 },
        academic: { min: 0, max: 1, mean: 0.5, spread: 1 },
      },
      workloadStats: { min: 1, max: 3, mean: 2, spread: 2 },
      fairnessIndex: 0.9,
      jainIndex: 0.95,
      giniCoefficient: 0.1,
      outliers: { high: [], low: [] },
      workloads: [],
      facultyWorkloads: [],
      weights: { call: 1, fmit: 1, clinic: 1, admin: 1, academic: 1 },
    });

    const { result } = renderHook(
      () => useFairnessAudit('2025-01-01', '2025-01-07', true),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/fairness/audit?start_date=2025-01-01&end_date=2025-01-07&include_titled_faculty=true'
    );
  });

  it('does not run when dates are missing', async () => {
    renderHook(() => useFairnessAudit(null, null), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(mockedApi.get).not.toHaveBeenCalled();
    });
  });
});

describe('useFairnessSummary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches summary data when dates provided', async () => {
    mockedApi.get.mockResolvedValueOnce({
      period: { start: '2025-01-01', end: '2025-01-07' },
      facultyCount: 2,
      fairnessIndex: 0.9,
      workloadSpread: 1.2,
      outlierCount: { high: 0, low: 0 },
    });

    const { result } = renderHook(
      () => useFairnessSummary('2025-01-01', '2025-01-07'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/fairness/summary?start_date=2025-01-01&end_date=2025-01-07'
    );
  });
});

describe('useFacultyWorkload', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches faculty workload when id and dates provided', async () => {
    mockedApi.get.mockResolvedValueOnce({
      personId: 'faculty-1',
      personName: 'Dr. Fair',
      name: 'Dr. Fair',
      callCount: 1,
      fmitWeeks: 0,
      clinicHalfdays: 4,
      adminHalfdays: 1,
      academicHalfdays: 0,
      totalScore: 6,
      totalHalfDays: 5,
      callHalfDays: 1,
      fmitHalfDays: 0,
      clinicHalfDays: 4,
      adminHalfDays: 1,
    });

    const { result } = renderHook(
      () => useFacultyWorkload('faculty-1', '2025-01-01', '2025-01-07'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/fairness/faculty/faculty-1/workload?start_date=2025-01-01&end_date=2025-01-07'
    );
  });
});
