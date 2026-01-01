/**
 * Tests for Template Library Hooks
 *
 * Tests data fetching, mutations, and custom hooks for template management.
 */

import { renderHook, waitFor, act } from '@/test-utils';
import { createWrapper } from '../../utils/test-utils';
import {
  useTemplates,
  useTemplate,
  usePredefinedTemplates,
  useTemplateStatistics,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useDuplicateTemplate,
  useShareTemplate,
  useApplyTemplate,
  useImportPredefinedTemplate,
  useTemplateFilters,
  usePatternEditor,
} from '@/features/templates/hooks';
import type { ScheduleTemplateCreate, TemplateFilters } from '@/features/templates/types';

describe('Template Hooks', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  describe('useTemplates', () => {
    it('should fetch templates list', async () => {
      const { result } = renderHook(() => useTemplates(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.items).toEqual([]);
      expect(result.current.data?.total).toBe(0);
    });

    it('should apply filters to templates', async () => {
      const filters: TemplateFilters = {
        category: 'clinic',
        visibility: 'private',
      };

      const { result } = renderHook(() => useTemplates(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
    });

    it('should handle search query filter', async () => {
      const filters: TemplateFilters = {
        searchQuery: 'clinic',
      };

      const { result } = renderHook(() => useTemplates(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
    });

    it('should handle sort options', async () => {
      const filters: TemplateFilters = {
        sortBy: 'name',
        sortOrder: 'asc',
      };

      const { result } = renderHook(() => useTemplates(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
    });
  });

  describe('useTemplate', () => {
    it('should fetch a single template by ID', async () => {
      const { result } = renderHook(() => useTemplate('template-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Should return null for non-existent template
      expect(result.current.data).toBeNull();
    });

    it('should not fetch when ID is empty', () => {
      const { result } = renderHook(() => useTemplate(''), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });

  describe('usePredefinedTemplates', () => {
    it('should fetch predefined templates', async () => {
      const { result } = renderHook(() => usePredefinedTemplates(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(Array.isArray(result.current.data)).toBe(true);
      expect(result.current.data?.length).toBeGreaterThan(0);
    });

    it('should return system templates', async () => {
      const { result } = renderHook(() => usePredefinedTemplates(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const templates = result.current.data || [];
      templates.forEach((template) => {
        expect(template.isSystem).toBe(true);
        expect(template.templateKey).toBeDefined();
      });
    });
  });

  describe('useTemplateStatistics', () => {
    it('should fetch template statistics', async () => {
      const { result } = renderHook(() => useTemplateStatistics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.totalTemplates).toBeDefined();
      expect(result.current.data?.byCategory).toBeDefined();
      expect(result.current.data?.byStatus).toBeDefined();
    });

    it('should include most used and recently created', async () => {
      const { result } = renderHook(() => useTemplateStatistics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.mostUsed).toBeDefined();
      expect(result.current.data?.recentlyCreated).toBeDefined();
    });
  });

  describe('useCreateTemplate', () => {
    it('should create a new template', async () => {
      const { result } = renderHook(() => useCreateTemplate(), {
        wrapper: createWrapper(),
      });

      const newTemplate: ScheduleTemplateCreate = {
        name: 'Test Template',
        description: 'Test description',
        category: 'clinic',
        durationWeeks: 1,
        patterns: [],
      };

      await act(async () => {
        const created = await result.current.mutateAsync(newTemplate);
        expect(created.name).toBe('Test Template');
        expect(created.id).toBeDefined();
        expect(created.category).toBe('clinic');
      });

      expect(result.current.isSuccess).toBe(true);
    });

    it('should handle validation errors', async () => {
      const { result } = renderHook(() => useCreateTemplate(), {
        wrapper: createWrapper(),
      });

      const invalidTemplate: ScheduleTemplateCreate = {
        name: '',
        category: 'clinic',
        durationWeeks: 1,
      };

      await act(async () => {
        await result.current.mutateAsync(invalidTemplate);
      });

      expect(result.current.isSuccess).toBe(true);
    });
  });

  describe('useUpdateTemplate', () => {
    it('should update an existing template', async () => {
      // Use a single renderHook to access both hooks
      const { result } = renderHook(
        () => ({
          create: useCreateTemplate(),
          update: useUpdateTemplate(),
        }),
        { wrapper: createWrapper() }
      );

      let templateId = '';

      // Create a template
      await act(async () => {
        const created = await result.current.create.mutateAsync({
          name: 'Original Name',
          category: 'clinic',
          durationWeeks: 1,
        });
        templateId = created.id;
      });

      // Wait for creation to fully complete
      await waitFor(() => {
        expect(result.current.create.isSuccess).toBe(true);
      });

      // Now update it
      await act(async () => {
        const updated = await result.current.update.mutateAsync({
          id: templateId,
          data: { name: 'Updated Name' },
        });
        expect(updated.name).toBe('Updated Name');
      });

      expect(result.current.update.isSuccess).toBe(true);
    });

    it('should handle non-existent template', async () => {
      const { result } = renderHook(() => useUpdateTemplate(), {
        wrapper: createWrapper(),
      });

      await expect(async () => {
        await result.current.mutateAsync({
          id: 'non-existent',
          data: { name: 'Updated' },
        });
      }).rejects.toThrow('Template not found');
    });
  });

  describe('useDeleteTemplate', () => {
    it('should delete a template', async () => {
      // Use a single renderHook to access both hooks
      const { result } = renderHook(
        () => ({
          create: useCreateTemplate(),
          delete: useDeleteTemplate(),
        }),
        { wrapper: createWrapper() }
      );

      let templateId = '';

      // Create a template
      await act(async () => {
        const created = await result.current.create.mutateAsync({
          name: 'To Delete',
          category: 'clinic',
          durationWeeks: 1,
        });
        templateId = created.id;
      });

      // Now delete it
      await act(async () => {
        await result.current.delete.mutateAsync(templateId);
      });

      expect(result.current.delete.isSuccess).toBe(true);
    });
  });

  describe('useDuplicateTemplate', () => {
    it('should duplicate a template', async () => {
      // Use a single renderHook to access both hooks
      const { result } = renderHook(
        () => ({
          create: useCreateTemplate(),
          duplicate: useDuplicateTemplate(),
        }),
        { wrapper: createWrapper() }
      );

      let templateId = '';

      // Create a template
      await act(async () => {
        const created = await result.current.create.mutateAsync({
          name: 'Original',
          category: 'clinic',
          durationWeeks: 1,
          patterns: [],
        });
        templateId = created.id;
      });

      // Now duplicate it
      await act(async () => {
        const duplicate = await result.current.duplicate.mutateAsync({
          templateId,
          newName: 'Duplicate',
          includePatterns: true,
        });
        expect(duplicate.name).toBe('Duplicate');
        expect(duplicate.id).not.toBe(templateId);
        expect(duplicate.sourceTemplateId).toBe(templateId);
      });

      expect(result.current.duplicate.isSuccess).toBe(true);
    });

    it('should use default name if not provided', async () => {
      // Use a single renderHook to access both hooks
      const { result } = renderHook(
        () => ({
          create: useCreateTemplate(),
          duplicate: useDuplicateTemplate(),
        }),
        { wrapper: createWrapper() }
      );

      let templateId = '';

      // Create a template
      await act(async () => {
        const created = await result.current.create.mutateAsync({
          name: 'Original',
          category: 'clinic',
          durationWeeks: 1,
        });
        templateId = created.id;
      });

      // Duplicate without custom name
      await act(async () => {
        const duplicate = await result.current.duplicate.mutateAsync({
          templateId,
        });
        expect(duplicate.name).toBe('Original (Copy)');
      });
    });
  });

  describe('useShareTemplate', () => {
    it('should share a template publicly', async () => {
      // Use a single renderHook to access both hooks
      const { result } = renderHook(
        () => ({
          create: useCreateTemplate(),
          share: useShareTemplate(),
        }),
        { wrapper: createWrapper() }
      );

      let templateId = '';

      // Create a template
      await act(async () => {
        const created = await result.current.create.mutateAsync({
          name: 'To Share',
          category: 'clinic',
          durationWeeks: 1,
        });
        templateId = created.id;
      });

      // Share it
      await act(async () => {
        const shared = await result.current.share.mutateAsync({
          templateId,
          makePublic: true,
        });
        expect(shared.isPublic).toBe(true);
        expect(shared.visibility).toBe('public');
      });

      expect(result.current.share.isSuccess).toBe(true);
    });

    it('should share with specific users', async () => {
      // Use a single renderHook to access both hooks
      const { result } = renderHook(
        () => ({
          create: useCreateTemplate(),
          share: useShareTemplate(),
        }),
        { wrapper: createWrapper() }
      );

      let templateId = '';

      // Create a template
      await act(async () => {
        const created = await result.current.create.mutateAsync({
          name: 'To Share',
          category: 'clinic',
          durationWeeks: 1,
        });
        templateId = created.id;
      });

      // Share with users
      await act(async () => {
        const shared = await result.current.share.mutateAsync({
          templateId,
          userIds: ['user-1', 'user-2'],
        });
        expect(shared.sharedWith).toEqual(['user-1', 'user-2']);
        expect(shared.visibility).toBe('shared');
      });
    });
  });

  describe('useApplyTemplate', () => {
    it('should apply a template and update usage count', async () => {
      // Use a single renderHook to access both hooks
      const { result } = renderHook(
        () => ({
          create: useCreateTemplate(),
          apply: useApplyTemplate(),
        }),
        { wrapper: createWrapper() }
      );

      let templateId = '';

      // Create a template
      await act(async () => {
        const created = await result.current.create.mutateAsync({
          name: 'To Apply',
          category: 'clinic',
          durationWeeks: 1,
          patterns: [
            {
              name: 'Test Pattern',
              dayOfWeek: 1,
              timeOfDay: 'AM',
              activityType: 'clinic',
              role: 'primary',
            },
          ],
        });
        templateId = created.id;
      });

      // Apply it
      await act(async () => {
        const result_data = await result.current.apply.mutateAsync({
          templateId,
          config: {
            startDate: new Date('2025-01-01'),
            endDate: new Date('2025-01-07'),
            showConflicts: true,
            highlightPatterns: true,
          },
        });
        expect(result_data.success).toBe(true);
        expect(result_data.assignmentsCreated).toBeGreaterThan(0);
      });

      expect(result.current.apply.isSuccess).toBe(true);
    });
  });

  describe('useImportPredefinedTemplate', () => {
    it('should import a predefined template', async () => {
      const { result } = renderHook(() => useImportPredefinedTemplate(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        const imported = await result.current.mutateAsync('standard-weekday-clinic');
        expect(imported.name).toBe('Standard Weekday Clinic');
        expect(imported.sourceTemplateId).toBe('standard-weekday-clinic');
        expect(imported.visibility).toBe('private');
        expect(imported.tags).toContain('imported');
      });

      expect(result.current.isSuccess).toBe(true);
    });

    it('should handle non-existent predefined template', async () => {
      const { result } = renderHook(() => useImportPredefinedTemplate(), {
        wrapper: createWrapper(),
      });

      await expect(async () => {
        await result.current.mutateAsync('non-existent-template');
      }).rejects.toThrow('Predefined template not found');
    });
  });

  describe('useTemplateFilters', () => {
    it('should initialize with empty filters', () => {
      const { result } = renderHook(() => useTemplateFilters());

      expect(result.current.filters).toEqual({});
      expect(result.current.hasActiveFilters).toBe(false);
    });

    it('should initialize with provided filters', () => {
      const initialFilters: TemplateFilters = {
        category: 'clinic',
        visibility: 'private',
      };

      const { result } = renderHook(() => useTemplateFilters(initialFilters));

      expect(result.current.filters).toEqual(initialFilters);
      expect(result.current.hasActiveFilters).toBe(true);
    });

    it('should update a single filter', () => {
      const { result } = renderHook(() => useTemplateFilters());

      act(() => {
        result.current.updateFilter('category', 'clinic');
      });

      expect(result.current.filters.category).toBe('clinic');
      expect(result.current.hasActiveFilters).toBe(true);
    });

    it('should set all filters', () => {
      const { result } = renderHook(() => useTemplateFilters());

      const newFilters: TemplateFilters = {
        category: 'clinic',
        status: 'active',
        searchQuery: 'test',
      };

      act(() => {
        result.current.setFilters(newFilters);
      });

      expect(result.current.filters).toEqual(newFilters);
      expect(result.current.hasActiveFilters).toBe(true);
    });

    it('should clear all filters', () => {
      const initialFilters: TemplateFilters = {
        category: 'clinic',
        visibility: 'private',
      };

      const { result } = renderHook(() => useTemplateFilters(initialFilters));

      act(() => {
        result.current.clearFilters();
      });

      expect(result.current.filters).toEqual({});
      expect(result.current.hasActiveFilters).toBe(false);
    });

    it('should detect active filters correctly', () => {
      const { result } = renderHook(() => useTemplateFilters());

      expect(result.current.hasActiveFilters).toBe(false);

      act(() => {
        result.current.updateFilter('searchQuery', 'test');
      });

      expect(result.current.hasActiveFilters).toBe(true);

      act(() => {
        result.current.updateFilter('searchQuery', '');
      });

      expect(result.current.hasActiveFilters).toBe(false);
    });
  });

  describe('usePatternEditor', () => {
    it('should initialize with empty patterns', () => {
      const { result } = renderHook(() => usePatternEditor());

      expect(result.current.patterns).toEqual([]);
    });

    it('should initialize with provided patterns', () => {
      const initialPatterns = [
        {
          id: 'p1',
          name: 'Test Pattern',
          dayOfWeek: 1,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
      ];

      const { result } = renderHook(() => usePatternEditor(initialPatterns));

      expect(result.current.patterns).toEqual(initialPatterns);
    });

    it('should add a pattern', () => {
      const { result } = renderHook(() => usePatternEditor());

      act(() => {
        result.current.addPattern({
          name: 'New Pattern',
          dayOfWeek: 1,
          timeOfDay: 'AM',
          activityType: 'clinic',
          role: 'primary',
        });
      });

      expect(result.current.patterns).toHaveLength(1);
      expect(result.current.patterns[0].name).toBe('New Pattern');
      expect(result.current.patterns[0].id).toBeDefined();
    });

    it('should update a pattern', () => {
      const initialPatterns = [
        {
          id: 'p1',
          name: 'Original',
          dayOfWeek: 1,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
      ];

      const { result } = renderHook(() => usePatternEditor(initialPatterns));

      act(() => {
        result.current.updatePattern('p1', { name: 'Updated' });
      });

      expect(result.current.patterns[0].name).toBe('Updated');
    });

    it('should remove a pattern', () => {
      const initialPatterns = [
        {
          id: 'p1',
          name: 'Pattern 1',
          dayOfWeek: 1,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
        {
          id: 'p2',
          name: 'Pattern 2',
          dayOfWeek: 2,
          timeOfDay: 'PM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
      ];

      const { result } = renderHook(() => usePatternEditor(initialPatterns));

      act(() => {
        result.current.removePattern('p1');
      });

      expect(result.current.patterns).toHaveLength(1);
      expect(result.current.patterns[0].id).toBe('p2');
    });

    it('should duplicate a pattern', () => {
      const initialPatterns = [
        {
          id: 'p1',
          name: 'Original',
          dayOfWeek: 1,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
      ];

      const { result } = renderHook(() => usePatternEditor(initialPatterns));

      act(() => {
        result.current.duplicatePattern('p1');
      });

      expect(result.current.patterns).toHaveLength(2);
      expect(result.current.patterns[1].name).toBe('Original (Copy)');
      expect(result.current.patterns[1].id).not.toBe('p1');
    });

    it('should reorder patterns', () => {
      const initialPatterns = [
        {
          id: 'p1',
          name: 'First',
          dayOfWeek: 1,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
        {
          id: 'p2',
          name: 'Second',
          dayOfWeek: 2,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
        {
          id: 'p3',
          name: 'Third',
          dayOfWeek: 3,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
      ];

      const { result } = renderHook(() => usePatternEditor(initialPatterns));

      act(() => {
        result.current.reorderPatterns(0, 2);
      });

      expect(result.current.patterns[0].name).toBe('Second');
      expect(result.current.patterns[1].name).toBe('Third');
      expect(result.current.patterns[2].name).toBe('First');
    });

    it('should clear all patterns', () => {
      const initialPatterns = [
        {
          id: 'p1',
          name: 'Pattern',
          dayOfWeek: 1,
          timeOfDay: 'AM' as const,
          activityType: 'clinic',
          role: 'primary' as const,
        },
      ];

      const { result } = renderHook(() => usePatternEditor(initialPatterns));

      act(() => {
        result.current.clearPatterns();
      });

      expect(result.current.patterns).toEqual([]);
    });
  });
});
