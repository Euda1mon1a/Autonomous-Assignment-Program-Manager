import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import { useAssignmentsForRange } from '@/hooks/useAssignmentsForRange'
import type { ListResponse } from '@/lib/hooks'
import type { Assignment } from '@/types/api'

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

describe('useAssignmentsForRange', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('memoizes combined data when page data is unchanged', async () => {
    // Use total within a single page (<=500) to avoid the multi-step
    // useEffect -> setState -> useQueries async chain that is fragile in tests.
    // The memoization being tested is the useMemo reference stability, not pagination.
    const response: ListResponse<Assignment> = {
      items: [{ id: 'a1' } as Assignment, { id: 'a2' } as Assignment],
      total: 2,
    }

    mockedApi.get.mockResolvedValueOnce(response)

    const { result, rerender } = renderHook(
      () => useAssignmentsForRange('2026-02-01', '2026-02-28', true),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.data?.items.length).toBe(2)
    })

    const initialData = result.current.data
    rerender()

    expect(result.current.data).toBe(initialData)
    expect(mockedApi.get).toHaveBeenCalledTimes(1)
  })
})
