/**
 * Tests for Procedures and Credentialing Hooks
 *
 * Tests procedure catalog management, credential tracking,
 * and qualified faculty lookups.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useProcedures,
  useProcedure,
  useCredentials,
  useFacultyCredentials,
  useQualifiedFaculty,
  useCreateProcedure,
  useUpdateProcedure,
  useDeleteProcedure,
  useCreateCredential,
  useUpdateCredential,
  useDeleteCredential,
  useExpiringCredentials,
} from './useProcedures';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data
const mockProcedure = {
  id: 'proc-123',
  name: 'Knee Arthroscopy',
  description: 'Arthroscopic knee procedure',
  category: 'Orthopedics',
  specialty: 'Sports Medicine',
  supervision_ratio: 2,
  requires_certification: true,
  complexity_level: 'advanced' as const,
  min_pgy_level: 2,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockCredential = {
  id: 'cred-123',
  person_id: 'person-456',
  procedure_id: 'proc-123',
  status: 'active' as const,
  competency_level: 'qualified' as const,
  issued_date: '2024-01-01',
  expiration_date: '2025-01-01',
  last_verified_date: '2024-01-01',
  max_concurrent_residents: 2,
  max_per_week: 5,
  max_per_academic_year: 200,
  notes: null,
  is_valid: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useProcedures', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches procedures list successfully', async () => {
    const mockResponse = {
      items: [mockProcedure],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useProcedures(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
    expect(mockedApi.get).toHaveBeenCalledWith('/procedures');
  });

  it('applies specialty filter', async () => {
    const mockResponse = {
      items: [mockProcedure],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useProcedures({ specialty: 'Sports Medicine' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/procedures?specialty=Sports%20Medicine'
    );
  });

  it('applies category and complexity filters', async () => {
    const mockResponse = {
      items: [mockProcedure],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useProcedures({
          category: 'Orthopedics',
          complexity_level: 'advanced',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/procedures?category=Orthopedics&complexity_level=advanced'
    );
  });
});

describe('useProcedure', () => {
  it('fetches single procedure successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockProcedure);

    const { result } = renderHook(() => useProcedure('proc-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockProcedure);
    expect(mockedApi.get).toHaveBeenCalledWith('/procedures/proc-123');
  });

  it('does not fetch when id is empty', async () => {
    const { result } = renderHook(() => useProcedure(''), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).not.toHaveBeenCalled();
  });
});

describe('useCredentials', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches credentials list successfully', async () => {
    const mockResponse = {
      items: [mockCredential],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useCredentials(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
  });

  it('fetches credentials by person ID', async () => {
    const mockResponse = {
      items: [mockCredential],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useCredentials({ person_id: 'person-456' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/credentials/by-person/person-456'
    );
  });

  it('fetches credentials by procedure ID', async () => {
    const mockResponse = {
      items: [mockCredential],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useCredentials({ procedure_id: 'proc-123' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/credentials/by-procedure/proc-123'
    );
  });
});

describe('useFacultyCredentials', () => {
  it('fetches faculty credentials successfully', async () => {
    const mockResponse = {
      items: [mockCredential],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useFacultyCredentials('faculty-123'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
  });

  it('applies status filter', async () => {
    const mockResponse = {
      items: [mockCredential],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useFacultyCredentials('faculty-123', { status: 'active' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/credentials/by-person/faculty-123?status=active'
    );
  });
});

describe('useQualifiedFaculty', () => {
  it('fetches qualified faculty for procedure', async () => {
    const mockResponse = {
      procedure_id: 'proc-123',
      procedure_name: 'Knee Arthroscopy',
      qualified_faculty: [
        { id: 'faculty-1', name: 'Dr. Smith', type: 'FACULTY' },
        { id: 'faculty-2', name: 'Dr. Jones', type: 'FACULTY' },
      ],
      total: 2,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useQualifiedFaculty('proc-123'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
    expect(result.current.data?.total).toBe(2);
  });
});

describe('useCreateProcedure', () => {
  it('creates procedure successfully', async () => {
    const newProcedure = { ...mockProcedure, id: 'proc-456' };
    mockedApi.post.mockResolvedValueOnce(newProcedure);

    const { result } = renderHook(() => useCreateProcedure(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        name: 'New Procedure',
        specialty: 'Orthopedics',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(newProcedure);
  });
});

describe('useUpdateProcedure', () => {
  it('updates procedure successfully', async () => {
    const updatedProcedure = {
      ...mockProcedure,
      name: 'Updated Procedure',
    };
    mockedApi.put.mockResolvedValueOnce(updatedProcedure);

    const { result } = renderHook(() => useUpdateProcedure(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'proc-123',
        data: { name: 'Updated Procedure' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(updatedProcedure);
  });
});

describe('useDeleteProcedure', () => {
  it('deletes procedure successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteProcedure(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('proc-123');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.del).toHaveBeenCalledWith('/procedures/proc-123');
  });
});

describe('useCreateCredential', () => {
  it('creates credential successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockCredential);

    const { result } = renderHook(() => useCreateCredential(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        person_id: 'person-456',
        procedure_id: 'proc-123',
        competency_level: 'qualified',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockCredential);
  });
});

describe('useUpdateCredential', () => {
  it('updates credential successfully', async () => {
    const updatedCredential = {
      ...mockCredential,
      competency_level: 'expert' as const,
    };
    mockedApi.put.mockResolvedValueOnce(updatedCredential);

    const { result } = renderHook(() => useUpdateCredential(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'cred-123',
        data: { competency_level: 'expert' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(updatedCredential);
  });
});

describe('useDeleteCredential', () => {
  it('deletes credential successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteCredential(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('cred-123');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.del).toHaveBeenCalledWith('/credentials/cred-123');
  });
});

describe('useExpiringCredentials', () => {
  it('fetches expiring credentials successfully', async () => {
    const mockResponse = {
      items: [mockCredential],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useExpiringCredentials(30),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/credentials/expiring?days=30'
    );
  });

  it('uses default 30-day window', async () => {
    const mockResponse = {
      items: [mockCredential],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useExpiringCredentials(),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/credentials/expiring?days=30'
    );
  });
});
