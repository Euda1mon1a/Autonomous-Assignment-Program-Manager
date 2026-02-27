import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import { useExportData } from '@/hooks/useExportData'

jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        refetchOnWindowFocus: false,
      },
    },
  })
}

function createWrapper() {
  const queryClient = createTestQueryClient()
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useExportData', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('does not fetch schedules without required date filters', async () => {
    const { result } = renderHook(() => useExportData('schedules'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isFetching).toBe(false)
    })

    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('fetches people export data with format json', async () => {
    mockedApi.get.mockResolvedValueOnce([{ id: 'p1' }])

    const { result } = renderHook(() => useExportData('people'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.data?.length).toBe(1)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/export/people', {
      params: { format: 'json' },
    })
  })

  it('fetches schedules with snake_case date params', async () => {
    mockedApi.get.mockResolvedValueOnce([{ id: 'a1' }])

    const { result } = renderHook(
      () =>
        useExportData('schedules', {
          startDate: '2026-02-01',
          endDate: '2026-02-28',
        }),
      {
        wrapper: createWrapper(),
      }
    )

    await waitFor(() => {
      expect(result.current.data?.length).toBe(1)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/export/schedule', {
      params: {
        format: 'json',
        start_date: '2026-02-01',
        end_date: '2026-02-28',
      },
    })
  })
})
