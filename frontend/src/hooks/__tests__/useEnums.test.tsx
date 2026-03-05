/**
 * Tests for useEnums hooks
 *
 * Tests all 7 enum fetching hooks: query keys, success, and error handling.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useSchedulingAlgorithms,
  useActivityCategories,
  useRotationTypes,
  usePgyLevels,
  useConstraintCategories,
  usePersonTypes,
  useFreezeScopes,
  enumKeys,
  EnumOption,
} from '@/hooks/useEnums';

jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const mockAlgorithms: EnumOption[] = [
  { value: 'greedy', label: 'Greedy (fast)' },
  { value: 'cp_sat', label: 'CP-SAT (optimal)' },
  { value: 'hybrid', label: 'Hybrid (balanced)' },
];

const mockCategories: EnumOption[] = [
  { value: 'clinical', label: 'Clinical' },
  { value: 'educational', label: 'Educational' },
  { value: 'administrative', label: 'Administrative' },
];

describe('useEnums hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('enumKeys', () => {
    it('should have correct query key for scheduling algorithms', () => {
      expect(enumKeys.schedulingAlgorithms).toEqual(['enums', 'scheduling-algorithms']);
    });

    it('should have correct query key for activity categories', () => {
      expect(enumKeys.activityCategories).toEqual(['enums', 'activity-categories']);
    });

    it('should have correct query key for rotation types', () => {
      expect(enumKeys.rotationTypes).toEqual(['enums', 'rotation-types']);
    });

    it('should have correct query key for pgy levels', () => {
      expect(enumKeys.pgyLevels).toEqual(['enums', 'pgy-levels']);
    });

    it('should have correct query key for constraint categories', () => {
      expect(enumKeys.constraintCategories).toEqual(['enums', 'constraint-categories']);
    });

    it('should have correct query key for person types', () => {
      expect(enumKeys.personTypes).toEqual(['enums', 'person-types']);
    });

    it('should have correct query key for freeze scopes', () => {
      expect(enumKeys.freezeScopes).toEqual(['enums', 'freeze-scopes']);
    });
  });

  describe('useSchedulingAlgorithms', () => {
    it('should fetch algorithms successfully', async () => {
      mockedApi.get.mockResolvedValue(mockAlgorithms);

      const { result } = renderHook(() => useSchedulingAlgorithms(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockAlgorithms);
      expect(mockedApi.get).toHaveBeenCalledWith('/enums/scheduling-algorithms');
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch algorithms');
      mockedApi.get.mockRejectedValue(error);

      const { result } = renderHook(() => useSchedulingAlgorithms(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('useActivityCategories', () => {
    it('should fetch activity categories successfully', async () => {
      mockedApi.get.mockResolvedValue(mockCategories);

      const { result } = renderHook(() => useActivityCategories(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockCategories);
      expect(mockedApi.get).toHaveBeenCalledWith('/enums/activity-categories');
    });
  });

  describe('useRotationTypes', () => {
    it('should fetch rotation types successfully', async () => {
      const mockRotations: EnumOption[] = [
        { value: 'inpatient', label: 'Inpatient' },
        { value: 'outpatient', label: 'Outpatient' },
      ];
      mockedApi.get.mockResolvedValue(mockRotations);

      const { result } = renderHook(() => useRotationTypes(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockRotations);
      expect(mockedApi.get).toHaveBeenCalledWith('/enums/rotation-types');
    });
  });

  describe('usePgyLevels', () => {
    it('should fetch PGY levels successfully', async () => {
      const mockLevels: EnumOption[] = [
        { value: '1', label: 'PGY-1' },
        { value: '2', label: 'PGY-2' },
        { value: '3', label: 'PGY-3' },
      ];
      mockedApi.get.mockResolvedValue(mockLevels);

      const { result } = renderHook(() => usePgyLevels(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockLevels);
      expect(mockedApi.get).toHaveBeenCalledWith('/enums/pgy-levels');
    });
  });

  describe('useConstraintCategories', () => {
    it('should fetch constraint categories successfully', async () => {
      const mockConstraints: EnumOption[] = [
        { value: 'acgme', label: 'ACGME Compliance' },
        { value: 'coverage', label: 'Coverage' },
      ];
      mockedApi.get.mockResolvedValue(mockConstraints);

      const { result } = renderHook(() => useConstraintCategories(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockConstraints);
      expect(mockedApi.get).toHaveBeenCalledWith('/enums/constraint-categories');
    });
  });

  describe('usePersonTypes', () => {
    it('should fetch person types successfully', async () => {
      const mockTypes: EnumOption[] = [
        { value: 'resident', label: 'Resident' },
        { value: 'faculty', label: 'Faculty' },
      ];
      mockedApi.get.mockResolvedValue(mockTypes);

      const { result } = renderHook(() => usePersonTypes(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockTypes);
      expect(mockedApi.get).toHaveBeenCalledWith('/enums/person-types');
    });
  });

  describe('useFreezeScopes', () => {
    it('should fetch freeze scopes successfully', async () => {
      const mockScopes: EnumOption[] = [
        { value: 'block', label: 'Block' },
        { value: 'person', label: 'Person' },
      ];
      mockedApi.get.mockResolvedValue(mockScopes);

      const { result } = renderHook(() => useFreezeScopes(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockScopes);
      expect(mockedApi.get).toHaveBeenCalledWith('/enums/freeze-scopes');
    });
  });
});
