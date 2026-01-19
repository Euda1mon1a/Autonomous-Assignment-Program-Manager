/**
 * React Query hooks for Wellness API
 *
 * Provides data fetching and mutation hooks for the wellness/survey system.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  HopfieldAggregates,
  HopfieldPositionCreate,
  HopfieldPositionResult,
  LeaderboardResponse,
  PointHistoryResponse,
  QuickPulseResult,
  QuickPulseSubmit,
  QuickPulseWidgetData,
  Survey,
  SurveyListItem,
  SurveyResponseCreate,
  SurveyResponseSummary,
  SurveySubmissionResult,
  WellnessAccount,
  WellnessAnalytics,
} from '../types';

// ============================================================================
// Query Keys
// ============================================================================

export const wellnessKeys = {
  all: ['wellness'] as const,
  account: () => [...wellnessKeys.all, 'account'] as const,
  surveys: () => [...wellnessKeys.all, 'surveys'] as const,
  surveyDetail: (id: string) => [...wellnessKeys.surveys(), id] as const,
  surveyHistory: (page: number) => [...wellnessKeys.all, 'history', page] as const,
  leaderboard: () => [...wellnessKeys.all, 'leaderboard'] as const,
  pointHistory: (page: number) => [...wellnessKeys.all, 'points', page] as const,
  hopfieldAggregates: (block?: number, year?: number) =>
    [...wellnessKeys.all, 'hopfield', block, year] as const,
  widgetData: () => [...wellnessKeys.all, 'widget'] as const,
  analytics: (block?: number, year?: number) =>
    [...wellnessKeys.all, 'analytics', block, year] as const,
};

// ============================================================================
// Account Hooks
// ============================================================================

/**
 * Fetch the current user's wellness account
 */
export function useWellnessAccount() {
  return useQuery({
    queryKey: wellnessKeys.account(),
    queryFn: async () => {
      const response = await api.get<WellnessAccount>('/wellness/account');
      return response.data;
    },
  });
}

/**
 * Update wellness account settings
 */
export function useUpdateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      leaderboardOptIn?: boolean;
      displayName?: string;
      researchConsent?: boolean;
    }) => {
      const response = await api.patch<WellnessAccount>('/wellness/account', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: wellnessKeys.account() });
      queryClient.invalidateQueries({ queryKey: wellnessKeys.leaderboard() });
    },
  });
}

/**
 * Provide research consent
 */
export function useResearchConsent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { consent: boolean; consentVersion?: string }) => {
      const response = await api.post('/wellness/account/consent', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: wellnessKeys.account() });
    },
  });
}

/**
 * Opt in/out of leaderboard
 */
export function useLeaderboardOptIn() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { optIn: boolean; displayName?: string }) => {
      const response = await api.post('/wellness/account/leaderboard', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: wellnessKeys.account() });
      queryClient.invalidateQueries({ queryKey: wellnessKeys.leaderboard() });
    },
  });
}

// ============================================================================
// Survey Hooks
// ============================================================================

/**
 * Fetch available surveys for the current user
 */
export function useAvailableSurveys() {
  return useQuery({
    queryKey: wellnessKeys.surveys(),
    queryFn: async () => {
      const response = await api.get<SurveyListItem[]>('/wellness/surveys');
      return response.data;
    },
  });
}

/**
 * Fetch a specific survey by ID
 */
export function useSurvey(surveyId: string | undefined) {
  return useQuery({
    queryKey: wellnessKeys.surveyDetail(surveyId || ''),
    queryFn: async () => {
      if (!surveyId) throw new Error('Survey ID required');
      const response = await api.get<Survey>(`/wellness/surveys/${surveyId}`);
      return response.data;
    },
    enabled: !!surveyId,
  });
}

/**
 * Submit a survey response
 */
export function useSubmitSurvey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      surveyId,
      data,
    }: {
      surveyId: string;
      data: SurveyResponseCreate;
    }) => {
      const response = await api.post<SurveySubmissionResult>(
        `/wellness/surveys/${surveyId}/respond`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate all wellness queries to refresh state
      queryClient.invalidateQueries({ queryKey: wellnessKeys.all });
    },
  });
}

/**
 * Fetch survey response history
 */
export function useSurveyHistory(page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: wellnessKeys.surveyHistory(page),
    queryFn: async () => {
      const response = await api.get<{
        responses: SurveyResponseSummary[];
        total: number;
        page: number;
        pageSize: number;
      }>('/wellness/surveys/history', {
        params: { page, pageSize },
      });
      return response.data;
    },
  });
}

// ============================================================================
// Leaderboard Hooks
// ============================================================================

/**
 * Fetch the anonymous leaderboard
 */
export function useLeaderboard() {
  return useQuery({
    queryKey: wellnessKeys.leaderboard(),
    queryFn: async () => {
      const response = await api.get<LeaderboardResponse>('/wellness/leaderboard');
      return response.data;
    },
  });
}

// ============================================================================
// Points Hooks
// ============================================================================

/**
 * Fetch points transaction history
 */
export function usePointHistory(page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: wellnessKeys.pointHistory(page),
    queryFn: async () => {
      const response = await api.get<PointHistoryResponse>('/wellness/points/history', {
        params: { page, pageSize },
      });
      return response.data;
    },
  });
}

// ============================================================================
// Hopfield Hooks
// ============================================================================

/**
 * Submit a Hopfield landscape position
 */
export function useSubmitHopfieldPosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: HopfieldPositionCreate) => {
      const response = await api.post<HopfieldPositionResult>(
        '/wellness/hopfield/position',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: wellnessKeys.all });
    },
  });
}

/**
 * Fetch Hopfield position aggregates
 */
export function useHopfieldAggregates(blockNumber?: number, academicYear?: number) {
  return useQuery({
    queryKey: wellnessKeys.hopfieldAggregates(blockNumber, academicYear),
    queryFn: async () => {
      const response = await api.get<HopfieldAggregates>('/wellness/hopfield/aggregates', {
        params: { blockNumber, academicYear },
      });
      return response.data;
    },
  });
}

// ============================================================================
// Quick Pulse Hooks
// ============================================================================

/**
 * Fetch widget data for dashboard
 */
export function useWidgetData() {
  return useQuery({
    queryKey: wellnessKeys.widgetData(),
    queryFn: async () => {
      const response = await api.get<QuickPulseWidgetData>('/wellness/widget/data');
      return response.data;
    },
    staleTime: 30000, // Consider fresh for 30 seconds
  });
}

/**
 * Submit a quick pulse check-in
 */
export function useSubmitPulse() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: QuickPulseSubmit) => {
      const response = await api.post<QuickPulseResult>('/wellness/pulse', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: wellnessKeys.all });
    },
  });
}

// ============================================================================
// Analytics Hooks (Admin)
// ============================================================================

/**
 * Fetch wellness analytics (admin only)
 */
export function useWellnessAnalytics(blockNumber?: number, academicYear?: number) {
  return useQuery({
    queryKey: wellnessKeys.analytics(blockNumber, academicYear),
    queryFn: async () => {
      const response = await api.get<WellnessAnalytics>('/wellness/admin/analytics', {
        params: { blockNumber, academicYear },
      });
      return response.data;
    },
  });
}
