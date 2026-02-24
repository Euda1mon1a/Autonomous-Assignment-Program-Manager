/**
 * Tests for Schedule Draft Hooks
 *
 * Covers list/detail/preview queries and break-glass approval mutation.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  scheduleDraftKeys,
  useApproveBreakGlass,
  useScheduleDraft,
  useScheduleDraftPreview,
  useScheduleDrafts,
} from './useScheduleDrafts';
import type {
  BreakGlassApprovalResponse,
  DraftPreviewResponse,
  ScheduleDraftListResponse,
  ScheduleDraftResponse,
} from '@/types/schedule-draft';

const mockListScheduleDrafts = jest.fn();
const mockGetScheduleDraft = jest.fn();
const mockPreviewScheduleDraft = jest.fn();
const mockApproveBreakGlass = jest.fn();

jest.mock('@/api/schedule-drafts', () => ({
  listScheduleDrafts: (...args: unknown[]) => mockListScheduleDrafts(...args),
  getScheduleDraft: (...args: unknown[]) => mockGetScheduleDraft(...args),
  previewScheduleDraft: (...args: unknown[]) => mockPreviewScheduleDraft(...args),
  approveBreakGlass: (...args: unknown[]) => mockApproveBreakGlass(...args),
  acknowledgeDraftFlag: jest.fn(),
  bulkAcknowledgeDraftFlags: jest.fn(),
  discardScheduleDraft: jest.fn(),
  publishScheduleDraft: jest.fn(),
  rollbackScheduleDraft: jest.fn(),
}));

const mockCounts = {
  assignmentsTotal: 0,
  added: 0,
  modified: 0,
  deleted: 0,
  flagsTotal: 0,
  flagsAcknowledged: 0,
  flagsUnacknowledged: 0,
};

const mockListResponse: ScheduleDraftListResponse = {
  items: [
    {
      id: 'draft-1',
      createdAt: '2026-02-18T00:00:00Z',
      status: 'draft',
      sourceType: 'solver',
      targetStartDate: '2026-02-01',
      targetEndDate: '2026-02-28',
      flagsTotal: 1,
      flagsAcknowledged: 0,
      counts: mockCounts,
    },
  ],
  total: 1,
  page: 1,
  pageSize: 20,
  hasNext: false,
  hasPrevious: false,
};

const mockDraft: ScheduleDraftResponse = {
  id: 'draft-1',
  createdAt: '2026-02-18T00:00:00Z',
  targetStartDate: '2026-02-01',
  targetEndDate: '2026-02-28',
  status: 'draft',
  sourceType: 'solver',
  rollbackAvailable: false,
  flagsTotal: 1,
  flagsAcknowledged: 0,
  counts: mockCounts,
};

const mockPreview: DraftPreviewResponse = {
  draftId: 'draft-1',
  addCount: 0,
  modifyCount: 0,
  deleteCount: 0,
  flagsTotal: 1,
  flagsAcknowledged: 0,
  acgmeViolations: [],
  assignments: [],
  flags: [],
};

const mockApproval: BreakGlassApprovalResponse = {
  draftId: 'draft-1',
  approvedAt: '2026-02-18T12:00:00Z',
  approvedById: 'admin-1',
  approvalReason: 'Lock window exception for coverage',
  message: 'Approved',
};

function createWrapper(queryClient?: QueryClient) {
  const client =
    queryClient ??
    new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

describe('useScheduleDrafts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches schedule draft list with params', async () => {
    mockListScheduleDrafts.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(
      () => useScheduleDrafts(2, 'draft', 10),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockListResponse);
    expect(mockListScheduleDrafts).toHaveBeenCalledWith({
      page: 2,
      pageSize: 10,
      status: 'draft',
    });
  });
});

describe('useScheduleDraft', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not fetch when draftId is null', async () => {
    const { result } = renderHook(() => useScheduleDraft(null), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetScheduleDraft).not.toHaveBeenCalled();
  });

  it('fetches draft details when draftId is provided', async () => {
    mockGetScheduleDraft.mockResolvedValueOnce(mockDraft);

    const { result } = renderHook(() => useScheduleDraft('draft-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockDraft);
    expect(mockGetScheduleDraft).toHaveBeenCalledWith('draft-1');
  });
});

describe('useScheduleDraftPreview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches draft preview when draftId is provided', async () => {
    mockPreviewScheduleDraft.mockResolvedValueOnce(mockPreview);

    const { result } = renderHook(() => useScheduleDraftPreview('draft-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockPreview);
    expect(mockPreviewScheduleDraft).toHaveBeenCalledWith('draft-1');
  });
});

describe('useApproveBreakGlass', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('invalidates detail and preview caches on approval', async () => {
    mockApproveBreakGlass.mockResolvedValueOnce(mockApproval);

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useApproveBreakGlass(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      await result.current.mutateAsync({
        draftId: 'draft-1',
        reason: 'Lock window exception for coverage',
      });
    });

    expect(mockApproveBreakGlass).toHaveBeenCalledWith('draft-1', {
      reason: 'Lock window exception for coverage',
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: scheduleDraftKeys.detail('draft-1'),
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: scheduleDraftKeys.preview('draft-1'),
    });
  });
});
