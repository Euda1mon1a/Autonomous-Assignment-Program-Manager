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
    const firstPage: ListResponse<Assignment> = {
      items: [{ id: 'a1' } as Assignment],
      total: 600,
    }
    const secondPage: ListResponse<Assignment> = {
      items: [{ id: 'a2' } as Assignment],
      total: 600,
    }

    mockedApi.get
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce(secondPage)

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
    expect(mockedApi.get).toHaveBeenCalledTimes(2)
  })
})
