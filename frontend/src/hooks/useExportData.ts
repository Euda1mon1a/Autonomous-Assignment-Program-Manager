/**
 * Hook for fetching data from backend export endpoints.
 *
 * Provides React Query integration for the three export types:
 * - people: GET /export/people?format=json
 * - schedules: GET /export/schedule?format=json&start_date=...&end_date=...
 * - assignments: GET /export/absences?format=json
 *
 * Schedule queries require start_date and end_date filters.
 * The hook auto-fetches when required parameters are available.
 */
import { useQuery } from '@tanstack/react-query';
import { get, type ApiError } from '@/lib/api';

export type ExportDataType = 'schedules' | 'people' | 'assignments';

export interface ExportFilters {
  startDate?: string;
  endDate?: string;
}

const exportEndpoints: Record<ExportDataType, string> = {
  people: '/export/people',
  schedules: '/export/schedule',
  assignments: '/export/absences',
};

export const exportQueryKeys = {
  export: (type: ExportDataType, filters?: ExportFilters) => ['export', type, filters] as const,
};

export function useExportData(type: ExportDataType, filters?: ExportFilters) {
  // Schedule endpoint requires start_date and end_date
  const hasRequiredParams =
    type !== 'schedules' || (!!filters?.startDate && !!filters?.endDate);

  return useQuery<Record<string, unknown>[], ApiError>({
    queryKey: exportQueryKeys.export(type, filters),
    queryFn: async () => {
      const params: Record<string, string> = { format: 'json' };
      // URL query params use snake_case (Couatl Killer rule)
      if (filters?.startDate) params.start_date = filters.startDate;
      if (filters?.endDate) params.end_date = filters.endDate;
      return get<Record<string, unknown>[]>(exportEndpoints[type], { params });
    },
    enabled: hasRequiredParams,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}
