/**
 * Board Review Curriculum Planner React Query Hooks
 *
 * Mock-first implementation. Toggle NEXT_PUBLIC_BOARD_REVIEW_MOCK_MODE=false
 * when backend routes are ready.
 *
 * @see docs/design/BOARD_REVIEW_CURRICULUM_DESIGN.md
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import type {
  AbfmDomainCode,
  BoardReviewBlock,
  BoardReviewDashboard,
  BoardReviewFilters,
  BoardReviewSession,
  DomainCoverage,
  BlockDomainCount,
  HeatMapCell,
  FmcaGapItem,
  IteScores,
  IteRemediationItem,
  SessionStatus,
  SessionUpdate,
} from '@/types/board-review';
import { DOMAINS, FMCAS, BLOCKS } from '@/data/board-review-data';

// ============ Feature Flag ============

const USE_MOCK_DATA = process.env.NEXT_PUBLIC_BOARD_REVIEW_MOCK_MODE !== 'false';

// ============ Query Keys ============

export const boardReviewQueryKeys = {
  all: ['board-review'] as const,
  dashboard: () => ['board-review', 'dashboard'] as const,
  sessions: (filters?: BoardReviewFilters) => ['board-review', 'sessions', filters] as const,
  blocks: () => ['board-review', 'blocks'] as const,
  analytics: () => ['board-review', 'analytics'] as const,
  ite: (scores?: IteScores) => ['board-review', 'ite', scores] as const,
};

// ============ localStorage Persistence ============

const STORAGE_KEY = 'aapm-board-review-sessions';

function loadPersistedSessions(): Record<number, Partial<BoardReviewSession>> {
  if (typeof window === 'undefined') return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function persistSessionUpdate(sessionId: number, update: Partial<BoardReviewSession>) {
  if (typeof window === 'undefined') return;
  const current = loadPersistedSessions();
  current[sessionId] = { ...current[sessionId], ...update };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
}

function getBlocksWithPersistedState(): BoardReviewBlock[] {
  const persisted = loadPersistedSessions();
  return BLOCKS.map((block) => ({
    ...block,
    sessions: block.sessions.map((session) => ({
      ...session,
      ...persisted[session.id],
    })),
  }));
}

// ============ Mock Computation Functions ============

const mockDelay = (ms: number = 200) => new Promise((resolve) => setTimeout(resolve, ms));

function computeDashboard(blocks: BoardReviewBlock[]): BoardReviewDashboard {
  const allSessions = blocks.flatMap((b) => b.sessions);
  const totalSessions = allSessions.length;
  const completedSessions = allSessions.filter((s) => s.status === 'completed').length;
  const inProgressSessions = allSessions.filter((s) => s.status === 'in_progress').length;
  const notStartedSessions = allSessions.filter((s) => s.status === 'not_started').length;

  const domainCoverage: DomainCoverage[] = Object.values(DOMAINS).map((domain) => {
    const touches = allSessions.filter(
      (s) => s.domains[domain.code] && s.domains[domain.code].length > 0
    ).length;
    const completed = allSessions.filter(
      (s) =>
        s.status === 'completed' &&
        s.domains[domain.code] &&
        s.domains[domain.code].length > 0
    ).length;
    return {
      code: domain.code,
      name: domain.name,
      color: domain.color,
      target: domain.target,
      touches,
      completed,
      percentage: totalSessions > 0 ? Math.round((touches / totalSessions) * 100) : 0,
    };
  });

  // Find current block (first block with in_progress sessions, or first with not_started)
  const currentBlock =
    blocks.find((b) => b.sessions.some((s) => s.status === 'in_progress'))?.name ??
    blocks.find((b) => b.sessions.some((s) => s.status === 'not_started'))?.name ??
    null;

  // Find next session (first not_started session)
  const nextSession =
    allSessions.find((s) => s.status === 'not_started')?.title ?? null;

  return {
    totalSessions,
    completedSessions,
    inProgressSessions,
    notStartedSessions,
    completionRate: totalSessions > 0 ? Math.round((completedSessions / totalSessions) * 100) : 0,
    domainCoverage,
    currentBlock,
    nextSession,
  };
}

function filterSessions(
  blocks: BoardReviewBlock[],
  filters?: BoardReviewFilters
): BoardReviewBlock[] {
  if (!filters) return blocks;

  return blocks
    .map((block) => ({
      ...block,
      sessions: block.sessions.filter((session) => {
        if (filters.domain) {
          const domainFmcas = session.domains[filters.domain];
          if (!domainFmcas || domainFmcas.length === 0) return false;
        }
        if (filters.status) {
          if (session.status !== filters.status) return false;
        }
        if (filters.search && filters.search.trim() !== '') {
          const searchLower = filters.search.toLowerCase();
          const titleMatch = session.title.toLowerCase().includes(searchLower);
          const presenterMatch = session.presenter.toLowerCase().includes(searchLower);
          const fmcaMatch = Object.values(session.domains)
            .flat()
            .some((fmca) => fmca.toLowerCase().includes(searchLower));
          if (!titleMatch && !presenterMatch && !fmcaMatch) return false;
        }
        return true;
      }),
    }))
    .filter((block) => block.sessions.length > 0);
}

function computeBlockDomainCounts(blocks: BoardReviewBlock[]): BlockDomainCount[] {
  return blocks.map((block) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention -- ABFM domain codes
    const counts = { ACD: 0, CCM: 0, UEC: 0, PC: 0, FOC: 0 } as Record<AbfmDomainCode, number>;
    for (const session of block.sessions) {
      for (const domainCode of Object.keys(counts) as AbfmDomainCode[]) {
        if (session.domains[domainCode] && session.domains[domainCode].length > 0) {
          counts[domainCode]++;
        }
      }
    }
    return { blockId: block.id, blockName: block.name, counts };
  });
}

function computeHeatMap(blocks: BoardReviewBlock[]): HeatMapCell[] {
  const cells: HeatMapCell[] = [];
  const domainCodes: AbfmDomainCode[] = ['ACD', 'CCM', 'UEC', 'PC', 'FOC'];
  for (const block of blocks) {
    for (const code of domainCodes) {
      const count = block.sessions.filter(
        (s) => s.domains[code] && s.domains[code].length > 0
      ).length;
      cells.push({ row: block.name, col: code, value: count });
    }
  }
  return cells;
}

function computeFmcaGaps(blocks: BoardReviewBlock[]): FmcaGapItem[] {
  const allSessions = blocks.flatMap((b) => b.sessions);
  const gaps: FmcaGapItem[] = [];

  for (const [domainCode, fmcaList] of Object.entries(FMCAS)) {
    for (const fmca of fmcaList) {
      const sessionIds = allSessions
        .filter(
          (s) =>
            s.domains[domainCode] &&
            s.domains[domainCode].includes(fmca)
        )
        .map((s) => s.id);
      gaps.push({
        fmca,
        domain: domainCode as AbfmDomainCode,
        covered: sessionIds.length > 0,
        sessionIds,
      });
    }
  }
  return gaps;
}

function computeIteRemediation(
  scores: IteScores,
  blocks: BoardReviewBlock[]
): IteRemediationItem[] {
  const allSessions = blocks.flatMap((b) =>
    b.sessions.map((s) => ({
      ...s,
      blockName: blocks.find((bl) => bl.sessions.some((bs) => bs.id === s.id))?.name ?? '',
    }))
  );

  return Object.values(DOMAINS).map((domain) => {
    const score = scores[domain.code];
    let priority: 'low' | 'medium' | 'high' = 'low';
    if (score !== null) {
      if (score < 30) priority = 'high';
      else if (score < 50) priority = 'medium';
    }

    const sessions = allSessions
      .filter(
        (s) =>
          s.domains[domain.code] &&
          s.domains[domain.code].length > 0
      )
      .map((s) => ({
        id: s.id,
        title: s.title,
        blockName: s.blockName,
        status: s.status,
      }));

    return {
      domain: domain.code,
      domainName: domain.name,
      score,
      priority,
      sessions,
    };
  });
}

// ============ Query Hooks ============

export function useBoardReviewDashboard() {
  return useQuery({
    queryKey: boardReviewQueryKeys.dashboard(),
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        await mockDelay();
        return computeDashboard(getBlocksWithPersistedState());
      }
      // TODO: Replace with real API call when backend ready
      return computeDashboard(getBlocksWithPersistedState());
    },
    staleTime: 30 * 1000,
  });
}

export function useBoardReviewBlocks(filters?: BoardReviewFilters) {
  return useQuery({
    queryKey: boardReviewQueryKeys.sessions(filters),
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        await mockDelay();
        return filterSessions(getBlocksWithPersistedState(), filters);
      }
      return filterSessions(getBlocksWithPersistedState(), filters);
    },
    staleTime: 30 * 1000,
  });
}

export function useBoardReviewAnalytics() {
  return useQuery({
    queryKey: boardReviewQueryKeys.analytics(),
    queryFn: async () => {
      await mockDelay();
      const blocks = getBlocksWithPersistedState();
      return {
        blockDomainCounts: computeBlockDomainCounts(blocks),
        heatMap: computeHeatMap(blocks),
        fmcaGaps: computeFmcaGaps(blocks),
      };
    },
    staleTime: 60 * 1000,
  });
}

export function useIteAnalysis(scores: IteScores | null) {
  return useQuery({
    queryKey: boardReviewQueryKeys.ite(scores ?? undefined),
    queryFn: async () => {
      if (!scores) return null;
      await mockDelay();
      return computeIteRemediation(scores, getBlocksWithPersistedState());
    },
    enabled: scores !== null,
    staleTime: 60 * 1000,
  });
}

// ============ Mutation Hooks ============

export function useUpdateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (update: SessionUpdate) => {
      if (USE_MOCK_DATA) {
        await mockDelay(100);
        const partial: Partial<BoardReviewSession> = {};
        if (update.status !== undefined) partial.status = update.status;
        if (update.presenter !== undefined) partial.presenter = update.presenter;
        if (update.date !== undefined) partial.date = update.date;
        if (update.notes !== undefined) partial.notes = update.notes;
        persistSessionUpdate(update.sessionId, partial);
        return partial;
      }
      // TODO: Real API call
      throw new Error('Not implemented - backend required');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: boardReviewQueryKeys.all });
    },
  });
}

// ============ Filter Hook ============

export function useBoardReviewFilters() {
  const [filters, setFilters] = useState<BoardReviewFilters>({});

  const setDomain = useCallback((domain: AbfmDomainCode | '') => {
    setFilters((prev) => ({ ...prev, domain: domain || undefined }));
  }, []);

  const setStatus = useCallback((status: SessionStatus | '') => {
    setFilters((prev) => ({ ...prev, status: status || undefined }));
  }, []);

  const setSearch = useCallback((search: string) => {
    setFilters((prev) => ({ ...prev, search: search || undefined }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  return { filters, setDomain, setStatus, setSearch, clearFilters };
}

// ============ Helper Functions ============

export function getStatusColor(status: SessionStatus): string {
  switch (status) {
    case 'not_started':
      return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    case 'in_progress':
      return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    case 'completed':
      return 'text-green-400 bg-green-500/10 border-green-500/30';
    default:
      return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
  }
}

export function getStatusLabel(status: SessionStatus): string {
  switch (status) {
    case 'not_started':
      return 'Not Started';
    case 'in_progress':
      return 'In Progress';
    case 'completed':
      return 'Completed';
    default:
      return status;
  }
}

export function getDomainColor(code: AbfmDomainCode): string {
  return DOMAINS[code]?.color ?? '#6B7280';
}

export function getDomainBgClass(code: AbfmDomainCode): string {
  switch (code) {
    case 'ACD':
      return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
    case 'CCM':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    case 'UEC':
      return 'bg-red-500/10 text-red-400 border-red-500/30';
    case 'PC':
      return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
    case 'FOC':
      return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    default:
      return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
  }
}

export function getNextStatus(current: SessionStatus): SessionStatus {
  switch (current) {
    case 'not_started':
      return 'in_progress';
    case 'in_progress':
      return 'completed';
    case 'completed':
      return 'not_started';
    default:
      return 'not_started';
  }
}
