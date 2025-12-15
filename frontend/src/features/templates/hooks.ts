/**
 * Template Library Hooks
 *
 * React Query hooks for template library data fetching and mutations.
 * Uses local storage for demo purposes - can be replaced with API calls.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { useState, useCallback, useMemo } from 'react';
import type {
  ScheduleTemplate,
  ScheduleTemplateCreate,
  ScheduleTemplateUpdate,
  TemplateFilters,
  TemplateListResponse,
  TemplateStatistics,
  TemplateDuplicateRequest,
  TemplateShareRequest,
  TemplateApplicationResult,
  TemplatePreviewConfig,
  AssignmentPattern,
} from './types';
import { PREDEFINED_TEMPLATES } from './constants';

// Storage key for local persistence
const STORAGE_KEY = 'template-library';

// Generate unique ID
function generateId(): string {
  return `tpl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Local storage helpers
function getStoredTemplates(): ScheduleTemplate[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function setStoredTemplates(templates: ScheduleTemplate[]): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(templates));
}

// Query keys
export const templateQueryKeys = {
  all: ['templates'] as const,
  list: (filters?: TemplateFilters) => ['templates', 'list', filters] as const,
  detail: (id: string) => ['templates', 'detail', id] as const,
  statistics: () => ['templates', 'statistics'] as const,
  predefined: () => ['templates', 'predefined'] as const,
};

// API simulation functions
async function fetchTemplates(filters?: TemplateFilters): Promise<TemplateListResponse> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 300));

  let templates = getStoredTemplates();

  // Apply filters
  if (filters) {
    if (filters.category) {
      templates = templates.filter((t) => t.category === filters.category);
    }
    if (filters.visibility) {
      templates = templates.filter((t) => t.visibility === filters.visibility);
    }
    if (filters.status) {
      templates = templates.filter((t) => t.status === filters.status);
    }
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      templates = templates.filter(
        (t) =>
          t.name.toLowerCase().includes(query) ||
          t.description?.toLowerCase().includes(query) ||
          t.tags.some((tag) => tag.toLowerCase().includes(query))
      );
    }
    if (filters.tags && filters.tags.length > 0) {
      templates = templates.filter((t) =>
        filters.tags!.some((tag) => t.tags.includes(tag))
      );
    }
    if (filters.createdBy) {
      templates = templates.filter((t) => t.createdBy === filters.createdBy);
    }

    // Sort
    const sortBy = filters.sortBy || 'createdAt';
    const sortOrder = filters.sortOrder || 'desc';
    templates.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'usageCount':
          comparison = a.usageCount - b.usageCount;
          break;
        case 'updatedAt':
          comparison = new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime();
          break;
        case 'createdAt':
        default:
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }

  return {
    items: templates,
    total: templates.length,
    page: 1,
    pageSize: templates.length,
  };
}

async function fetchTemplateById(id: string): Promise<ScheduleTemplate | null> {
  await new Promise((resolve) => setTimeout(resolve, 200));
  const templates = getStoredTemplates();
  return templates.find((t) => t.id === id) || null;
}

async function createTemplate(data: ScheduleTemplateCreate): Promise<ScheduleTemplate> {
  await new Promise((resolve) => setTimeout(resolve, 300));

  const now = new Date().toISOString();
  const newTemplate: ScheduleTemplate = {
    id: generateId(),
    name: data.name,
    description: data.description,
    category: data.category,
    visibility: data.visibility || 'private',
    status: 'draft',
    durationWeeks: data.durationWeeks,
    startDayOfWeek: data.startDayOfWeek || 1,
    patterns: (data.patterns || []).map((p) => ({ ...p, id: generateId() })),
    maxResidentsPerDay: data.maxResidentsPerDay,
    requiresSupervision: data.requiresSupervision ?? true,
    allowWeekends: data.allowWeekends ?? false,
    allowHolidays: data.allowHolidays ?? false,
    tags: data.tags || [],
    createdBy: 'current-user', // Would come from auth context
    createdAt: now,
    updatedAt: now,
    usageCount: 0,
    isPublic: data.visibility === 'public',
    version: 1,
  };

  const templates = getStoredTemplates();
  templates.push(newTemplate);
  setStoredTemplates(templates);

  return newTemplate;
}

async function updateTemplate(
  id: string,
  data: ScheduleTemplateUpdate
): Promise<ScheduleTemplate> {
  await new Promise((resolve) => setTimeout(resolve, 300));

  const templates = getStoredTemplates();
  const index = templates.findIndex((t) => t.id === id);

  if (index === -1) {
    throw new Error('Template not found');
  }

  const updated: ScheduleTemplate = {
    ...templates[index],
    ...data,
    updatedAt: new Date().toISOString(),
    isPublic: data.visibility === 'public' || data.isPublic || templates[index].isPublic,
  };

  templates[index] = updated;
  setStoredTemplates(templates);

  return updated;
}

async function deleteTemplate(id: string): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 300));

  const templates = getStoredTemplates();
  const filtered = templates.filter((t) => t.id !== id);
  setStoredTemplates(filtered);
}

async function duplicateTemplate(request: TemplateDuplicateRequest): Promise<ScheduleTemplate> {
  await new Promise((resolve) => setTimeout(resolve, 300));

  const templates = getStoredTemplates();
  const source = templates.find((t) => t.id === request.templateId);

  if (!source) {
    throw new Error('Source template not found');
  }

  const now = new Date().toISOString();
  const duplicate: ScheduleTemplate = {
    ...source,
    id: generateId(),
    name: request.newName || `${source.name} (Copy)`,
    patterns: request.includePatterns !== false
      ? source.patterns.map((p) => ({ ...p, id: generateId() }))
      : [],
    createdBy: 'current-user',
    createdAt: now,
    updatedAt: now,
    usageCount: 0,
    visibility: 'private',
    isPublic: false,
    sourceTemplateId: source.id,
    version: 1,
  };

  templates.push(duplicate);
  setStoredTemplates(templates);

  return duplicate;
}

async function shareTemplate(request: TemplateShareRequest): Promise<ScheduleTemplate> {
  await new Promise((resolve) => setTimeout(resolve, 300));

  const templates = getStoredTemplates();
  const index = templates.findIndex((t) => t.id === request.templateId);

  if (index === -1) {
    throw new Error('Template not found');
  }

  const updated: ScheduleTemplate = {
    ...templates[index],
    sharedWith: request.userIds || templates[index].sharedWith,
    isPublic: request.makePublic ?? templates[index].isPublic,
    visibility: request.makePublic ? 'public' : request.userIds?.length ? 'shared' : templates[index].visibility,
    updatedAt: new Date().toISOString(),
  };

  templates[index] = updated;
  setStoredTemplates(templates);

  return updated;
}

// Hooks

/**
 * Fetch all templates with optional filters
 */
export function useTemplates(
  filters?: TemplateFilters,
  options?: Omit<UseQueryOptions<TemplateListResponse, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<TemplateListResponse, Error>({
    queryKey: templateQueryKeys.list(filters),
    queryFn: () => fetchTemplates(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Fetch a single template by ID
 */
export function useTemplate(
  id: string,
  options?: Omit<UseQueryOptions<ScheduleTemplate | null, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ScheduleTemplate | null, Error>({
    queryKey: templateQueryKeys.detail(id),
    queryFn: () => fetchTemplateById(id),
    staleTime: 2 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch predefined system templates
 */
export function usePredefinedTemplates() {
  return useQuery({
    queryKey: templateQueryKeys.predefined(),
    queryFn: async () => {
      await new Promise((resolve) => setTimeout(resolve, 100));
      return PREDEFINED_TEMPLATES;
    },
    staleTime: Infinity, // Never refetch predefined templates
  });
}

/**
 * Fetch template statistics
 */
export function useTemplateStatistics() {
  return useQuery<TemplateStatistics, Error>({
    queryKey: templateQueryKeys.statistics(),
    queryFn: async () => {
      await new Promise((resolve) => setTimeout(resolve, 200));
      const templates = getStoredTemplates();

      const byCategory = templates.reduce(
        (acc, t) => {
          acc[t.category] = (acc[t.category] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>
      );

      const byStatus = templates.reduce(
        (acc, t) => {
          acc[t.status] = (acc[t.status] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>
      );

      const sortedByUsage = [...templates].sort((a, b) => b.usageCount - a.usageCount);
      const sortedByDate = [...templates].sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );

      return {
        totalTemplates: templates.length,
        byCategory: byCategory as Record<string, number>,
        byStatus: byStatus as Record<string, number>,
        mostUsed: sortedByUsage.slice(0, 5),
        recentlyCreated: sortedByDate.slice(0, 5),
      };
    },
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Create a new template
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<ScheduleTemplate, Error, ScheduleTemplateCreate>({
    mutationFn: createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.all });
    },
  });
}

/**
 * Update an existing template
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<ScheduleTemplate, Error, { id: string; data: ScheduleTemplateUpdate }>({
    mutationFn: ({ id, data }) => updateTemplate(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.all });
      queryClient.setQueryData(templateQueryKeys.detail(data.id), data);
    },
  });
}

/**
 * Delete a template
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.all });
    },
  });
}

/**
 * Duplicate a template
 */
export function useDuplicateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<ScheduleTemplate, Error, TemplateDuplicateRequest>({
    mutationFn: duplicateTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.all });
    },
  });
}

/**
 * Share a template
 */
export function useShareTemplate() {
  const queryClient = useQueryClient();

  return useMutation<ScheduleTemplate, Error, TemplateShareRequest>({
    mutationFn: shareTemplate,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.all });
      queryClient.setQueryData(templateQueryKeys.detail(data.id), data);
    },
  });
}

/**
 * Apply a template to generate assignments
 * This would typically call the backend schedule generation API
 */
export function useApplyTemplate() {
  const queryClient = useQueryClient();

  return useMutation<
    TemplateApplicationResult,
    Error,
    { templateId: string; config: TemplatePreviewConfig }
  >({
    mutationFn: async ({ templateId, config }) => {
      // Simulate template application
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const templates = getStoredTemplates();
      const template = templates.find((t) => t.id === templateId);

      if (!template) {
        throw new Error('Template not found');
      }

      // Update usage count
      const index = templates.findIndex((t) => t.id === templateId);
      templates[index] = {
        ...templates[index],
        usageCount: templates[index].usageCount + 1,
        updatedAt: new Date().toISOString(),
      };
      setStoredTemplates(templates);

      // Simulate result
      return {
        success: true,
        assignmentsCreated: template.patterns.length * template.durationWeeks,
        assignmentsFailed: 0,
        conflicts: [],
        warnings: [],
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.all });
      // Also invalidate assignments if this were connected to the real API
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
    },
  });
}

/**
 * Import a predefined template into the user's library
 */
export function useImportPredefinedTemplate() {
  const queryClient = useQueryClient();

  return useMutation<ScheduleTemplate, Error, string>({
    mutationFn: async (templateKey: string) => {
      await new Promise((resolve) => setTimeout(resolve, 300));

      const predefined = PREDEFINED_TEMPLATES.find((t) => t.templateKey === templateKey);
      if (!predefined) {
        throw new Error('Predefined template not found');
      }

      const now = new Date().toISOString();
      const imported: ScheduleTemplate = {
        id: generateId(),
        name: predefined.name,
        description: predefined.description,
        category: predefined.category,
        visibility: 'private',
        status: 'active',
        durationWeeks: predefined.durationWeeks,
        startDayOfWeek: predefined.startDayOfWeek,
        patterns: predefined.patterns.map((p) => ({ ...p, id: generateId() })),
        maxResidentsPerDay: predefined.maxResidentsPerDay,
        requiresSupervision: predefined.requiresSupervision,
        allowWeekends: predefined.allowWeekends,
        allowHolidays: predefined.allowHolidays,
        tags: [...predefined.tags, 'imported'],
        createdBy: 'current-user',
        createdAt: now,
        updatedAt: now,
        usageCount: 0,
        isPublic: false,
        sourceTemplateId: templateKey,
        version: 1,
      };

      const templates = getStoredTemplates();
      templates.push(imported);
      setStoredTemplates(templates);

      return imported;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.all });
    },
  });
}

/**
 * Custom hook for template filtering state
 */
export function useTemplateFilters(initialFilters?: TemplateFilters) {
  const [filters, setFilters] = useState<TemplateFilters>(initialFilters || {});

  const updateFilter = useCallback(<K extends keyof TemplateFilters>(
    key: K,
    value: TemplateFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  const hasActiveFilters = useMemo(() => {
    return Object.values(filters).some(
      (value) => value !== undefined && value !== '' && !(Array.isArray(value) && value.length === 0)
    );
  }, [filters]);

  return {
    filters,
    setFilters,
    updateFilter,
    clearFilters,
    hasActiveFilters,
  };
}

/**
 * Custom hook for pattern editing
 */
export function usePatternEditor(initialPatterns: AssignmentPattern[] = []) {
  const [patterns, setPatterns] = useState<AssignmentPattern[]>(initialPatterns);

  const addPattern = useCallback((pattern: Omit<AssignmentPattern, 'id'>) => {
    const newPattern: AssignmentPattern = {
      ...pattern,
      id: generateId(),
    };
    setPatterns((prev) => [...prev, newPattern]);
    return newPattern;
  }, []);

  const updatePattern = useCallback((id: string, updates: Partial<AssignmentPattern>) => {
    setPatterns((prev) =>
      prev.map((p) => (p.id === id ? { ...p, ...updates } : p))
    );
  }, []);

  const removePattern = useCallback((id: string) => {
    setPatterns((prev) => prev.filter((p) => p.id !== id));
  }, []);

  const duplicatePattern = useCallback((id: string) => {
    const source = patterns.find((p) => p.id === id);
    if (source) {
      const duplicate: AssignmentPattern = {
        ...source,
        id: generateId(),
        name: `${source.name} (Copy)`,
      };
      setPatterns((prev) => [...prev, duplicate]);
      return duplicate;
    }
    return null;
  }, [patterns]);

  const reorderPatterns = useCallback((startIndex: number, endIndex: number) => {
    setPatterns((prev) => {
      const result = Array.from(prev);
      const [removed] = result.splice(startIndex, 1);
      result.splice(endIndex, 0, removed);
      return result;
    });
  }, []);

  const clearPatterns = useCallback(() => {
    setPatterns([]);
  }, []);

  return {
    patterns,
    setPatterns,
    addPattern,
    updatePattern,
    removePattern,
    duplicatePattern,
    reorderPatterns,
    clearPatterns,
  };
}
