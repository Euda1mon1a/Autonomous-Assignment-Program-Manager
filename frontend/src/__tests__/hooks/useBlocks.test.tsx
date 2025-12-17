/**
 * useBlocks Hook Tests
 *
 * Tests for block fetching and management hooks
 * using jest.mock() for API mocking.
 */
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import type { Block } from '@/types/api'
import type { ListResponse } from '@/lib/hooks'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data for blocks
const mockBlocks: Block[] = [
  {
    id: 'block-1',
    date: '2024-01-01',
    time_of_day: 'AM',
    block_number: 1,
    is_weekend: false,
    is_holiday: false,
    holiday_name: null,
  },
  {
    id: 'block-2',
    date: '2024-01-01',
    time_of_day: 'PM',
    block_number: 1,
    is_weekend: false,
    is_holiday: false,
    holiday_name: null,
  },
  {
    id: 'block-3',
    date: '2024-01-02',
    time_of_day: 'AM',
    block_number: 1,
    is_weekend: false,
    is_holiday: false,
    holiday_name: null,
  },
  {
    id: 'block-4',
    date: '2024-01-06',
    time_of_day: 'AM',
    block_number: 1,
    is_weekend: true,
    is_holiday: false,
    holiday_name: null,
  },
  {
    id: 'block-5',
    date: '2024-01-15',
    time_of_day: 'AM',
    block_number: 2,
    is_weekend: false,
    is_holiday: true,
    holiday_name: 'Martin Luther King Jr. Day',
  },
]

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

// Wrapper component with QueryClientProvider
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

// Hook implementation matching the pattern from ScheduleGrid.tsx
function useBlocks(startDate: string, endDate: string) {
  return useQuery<ListResponse<Block>>({
    queryKey: ['blocks', startDate, endDate],
    queryFn: () =>
      api.get<ListResponse<Block>>(`/blocks?start_date=${startDate}&end_date=${endDate}`),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  })
}

describe('useBlocks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch blocks for a date range successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockBlocks,
      total: mockBlocks.length,
    })

    const { result } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check data
    expect(result.current.data?.items).toHaveLength(mockBlocks.length)
    expect(result.current.data?.total).toBe(mockBlocks.length)
    expect(result.current.data?.items[0].date).toBe('2024-01-01')
    expect(mockedApi.get).toHaveBeenCalledWith('/blocks?start_date=2024-01-01&end_date=2024-01-31')
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockBlocks,
      total: mockBlocks.length,
    })

    const { result } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    // Check initial loading state
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isFetching).toBe(true)

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should return blocks with correct structure', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockBlocks,
      total: mockBlocks.length,
    })

    const { result } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const firstBlock = result.current.data?.items[0]
    expect(firstBlock).toMatchObject({
      id: expect.any(String),
      date: expect.any(String),
      time_of_day: expect.stringMatching(/^(AM|PM)$/),
      block_number: expect.any(Number),
      is_weekend: expect.any(Boolean),
      is_holiday: expect.any(Boolean),
    })
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Network error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should distinguish between AM and PM blocks', async () => {
    const amAndPmBlocks = mockBlocks.filter(b => b.date === '2024-01-01')
    mockedApi.get.mockResolvedValueOnce({
      items: amAndPmBlocks,
      total: amAndPmBlocks.length,
    })

    const { result } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-01'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const blocks = result.current.data?.items || []
    expect(blocks.some(b => b.time_of_day === 'AM')).toBe(true)
    expect(blocks.some(b => b.time_of_day === 'PM')).toBe(true)
  })

  it('should identify weekend blocks correctly', async () => {
    const weekendBlocks = mockBlocks.filter(b => b.is_weekend)
    mockedApi.get.mockResolvedValueOnce({
      items: weekendBlocks,
      total: weekendBlocks.length,
    })

    const { result } = renderHook(
      () => useBlocks('2024-01-06', '2024-01-07'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const blocks = result.current.data?.items || []
    expect(blocks.every(b => b.is_weekend)).toBe(true)
  })

  it('should identify holiday blocks correctly', async () => {
    const holidayBlocks = mockBlocks.filter(b => b.is_holiday)
    mockedApi.get.mockResolvedValueOnce({
      items: holidayBlocks,
      total: holidayBlocks.length,
    })

    const { result } = renderHook(
      () => useBlocks('2024-01-15', '2024-01-15'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const blocks = result.current.data?.items || []
    expect(blocks[0]?.is_holiday).toBe(true)
    expect(blocks[0]?.holiday_name).toBe('Martin Luther King Jr. Day')
  })

  it('should handle empty block results', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [],
      total: 0,
    })

    const { result } = renderHook(
      () => useBlocks('2025-01-01', '2025-01-31'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(0)
    expect(result.current.data?.total).toBe(0)
  })

  it('should support different date ranges', async () => {
    // Test single day
    mockedApi.get.mockResolvedValueOnce({
      items: mockBlocks.slice(0, 2),
      total: 2,
    })

    const { result: singleDay } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-01'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(singleDay.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/blocks?start_date=2024-01-01&end_date=2024-01-01')

    // Test week range
    jest.clearAllMocks()
    mockedApi.get.mockResolvedValueOnce({
      items: mockBlocks,
      total: mockBlocks.length,
    })

    const { result: weekRange } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-07'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(weekRange.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/blocks?start_date=2024-01-01&end_date=2024-01-07')
  })

  it('should group blocks by block number', async () => {
    const multiBlockData = [
      ...mockBlocks.filter(b => b.block_number === 1),
      ...mockBlocks.filter(b => b.block_number === 2),
    ]

    mockedApi.get.mockResolvedValueOnce({
      items: multiBlockData,
      total: multiBlockData.length,
    })

    const { result } = renderHook(
      () => useBlocks('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const blocks = result.current.data?.items || []
    const blockNumbers = [...new Set(blocks.map(b => b.block_number))]
    expect(blockNumbers).toContain(1)
    expect(blockNumbers).toContain(2)
  })

  it('should handle invalid date range error', async () => {
    const apiError = { message: 'Invalid date range: end_date must be after start_date', status: 400 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useBlocks('2024-01-31', '2024-01-01'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('Invalid date range')
  })
})
