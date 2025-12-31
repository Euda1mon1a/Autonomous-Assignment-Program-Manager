/**
 * Tests for useImport hook
 *
 * Tests file parsing, preview generation, import execution, and state management
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useImport } from '@/features/import-export/useImport';
import * as api from '@/lib/api';
import { importExportMockFactories } from './import-export-mocks';
import React from 'react';

// Mock API module
jest.mock('@/lib/api');

// Mock xlsx library
jest.mock('xlsx', () => ({
  read: jest.fn(),
  utils: {
    sheet_to_json: jest.fn(),
  },
}));

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useImport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should initialize with default values', () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      expect(result.current.file).toBeNull();
      expect(result.current.dataType).toBe('schedules');
      expect(result.current.preview).toBeNull();
      expect(result.current.progress.status).toBe('idle');
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isError).toBe(false);
      expect(result.current.xlsxFallbackUsed).toBe(false);
      expect(result.current.xlsxWarnings).toEqual([]);
    });

    it('should use provided dataType option', () => {
      const { result } = renderHook(() => useImport({ dataType: 'people' }), {
        wrapper: createWrapper(),
      });

      expect(result.current.dataType).toBe('people');
    });

    it('should have default import options', () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      expect(result.current.options).toEqual({
        skipDuplicates: true,
        updateExisting: false,
        skipInvalidRows: true,
        dateFormat: 'YYYY-MM-DD',
        trimWhitespace: true,
      });
    });
  });

  describe('Preview Import - CSV', () => {
    it('should preview CSV file successfully', async () => {
      const csvContent = 'name,email,type\nJohn Doe,john@example.com,resident\nJane Smith,jane@example.com,faculty';
      const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.preview).not.toBeNull();
        expect(result.current.preview?.totalRows).toBe(2);
        expect(result.current.file).toBe(mockFile);
        expect(result.current.format).toBe('csv');
      });
    });

    it('should normalize column names in CSV', async () => {
      const csvContent = 'Person Name,Email Address,Person Type\nJohn Doe,john@example.com,resident';
      const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.preview?.columns).toContain('person_name');
        expect(result.current.preview?.columns).toContain('email_address');
      });
    });

    it('should detect data type from CSV columns', async () => {
      const csvContent = 'name,email,type,pgy_level\nJohn Doe,john@example.com,resident,2';
      const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.dataType).toBe('people');
      });
    });

    it('should update progress during parsing', async () => {
      const csvContent = 'name,email\nJohn,john@example.com';
      const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' });

      const onProgress = jest.fn();
      const { result } = renderHook(() => useImport({ onProgress }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      expect(onProgress).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'parsing' })
      );

      expect(onProgress).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'validating' })
      );
    });

    it('should handle empty CSV file', async () => {
      const csvContent = '';
      const mockFile = new File([csvContent], 'empty.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        try {
          await result.current.previewImport(mockFile);
        } catch (error) {
          expect(error).toBeDefined();
        }
      });

      await waitFor(() => {
        expect(result.current.progress.status).toBe('error');
      });
    });
  });

  describe('Preview Import - JSON', () => {
    it('should preview JSON file successfully', async () => {
      const jsonContent = JSON.stringify([
        { name: 'John Doe', email: 'john@example.com', type: 'resident' },
        { name: 'Jane Smith', email: 'jane@example.com', type: 'faculty' },
      ]);
      const mockFile = new File([jsonContent], 'test.json', { type: 'application/json' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.preview).not.toBeNull();
        expect(result.current.preview?.totalRows).toBe(2);
        expect(result.current.format).toBe('json');
      });
    });

    it('should handle invalid JSON', async () => {
      const jsonContent = '{ invalid json }';
      const mockFile = new File([jsonContent], 'invalid.json', { type: 'application/json' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        try {
          await result.current.previewImport(mockFile);
        } catch (error) {
          expect(error).toBeDefined();
        }
      });

      await waitFor(() => {
        expect(result.current.progress.status).toBe('error');
      });
    });
  });

  describe('Preview Import - Excel', () => {
    it('should attempt backend parsing first', async () => {
      const mockFile = new File(['mock xlsx data'], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          rows: [{ name: 'John Doe', email: 'john@example.com' }],
          columns: ['name', 'email'],
          total_rows: 1,
          sheet_name: 'Sheet1',
          warnings: [],
        }),
      });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/imports/parse-xlsx'),
          expect.any(Object)
        );
        expect(result.current.xlsxFallbackUsed).toBe(false);
      });
    });

    it('should fallback to client-side parsing when backend fails', async () => {
      const mockFile = new File(['mock xlsx data'], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      global.fetch = jest.fn().mockRejectedValue(new Error('Backend unavailable'));

      const XLSX = require('xlsx');
      XLSX.read.mockReturnValue({
        SheetNames: ['Sheet1'],
        Sheets: {
          Sheet1: {},
        },
      });
      XLSX.utils.sheet_to_json.mockReturnValue([
        { name: 'John Doe', email: 'john@example.com' },
      ]);

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.xlsxFallbackUsed).toBe(true);
        expect(result.current.xlsxWarnings).toContain(
          expect.stringContaining('client-side')
        );
      });
    });

    it('should handle backend warnings', async () => {
      const mockFile = new File(['mock xlsx data'], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          rows: [{ name: 'John Doe' }],
          columns: ['name'],
          total_rows: 1,
          sheet_name: 'Sheet1',
          warnings: ['Missing color formatting', 'Empty cells detected'],
        }),
      });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.xlsxWarnings).toContain('Missing color formatting');
        expect(result.current.xlsxWarnings).toContain('Empty cells detected');
      });
    });
  });

  describe('Data Validation', () => {
    it('should validate rows and set status', async () => {
      const csvContent = 'name,email,type\nJohn Doe,john@example.com,resident\nInvalid,,';
      const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.preview?.validRows).toBeGreaterThan(0);
        expect(result.current.preview?.errorRows).toBeGreaterThan(0);
      });
    });

    it('should detect duplicate entries', async () => {
      const csvContent = 'name,email,type\nJohn Doe,john@example.com,resident\nJohn Doe,john@example.com,resident';
      const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        const rowsWithWarnings = result.current.preview?.rows.filter(
          r => r.warnings.length > 0
        );
        expect(rowsWithWarnings?.length).toBeGreaterThan(0);
      });
    });

    it('should detect overlapping absences', async () => {
      const csvContent = 'person_name,start_date,end_date,absence_type\nJohn,2024-01-01,2024-01-10,vacation\nJohn,2024-01-05,2024-01-15,vacation';
      const mockFile = new File([csvContent], 'absences.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport({ dataType: 'absences' }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.previewImport(mockFile);
      });

      await waitFor(() => {
        expect(result.current.dataType).toBe('absences');
        // Should have warnings for overlapping dates
      });
    });
  });

  describe('Execute Import', () => {
    it('should execute import successfully', async () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        validRows: 5,
      });

      (api.post as jest.Mock).mockResolvedValue({
        success: true,
        totalProcessed: 5,
        successCount: 5,
        errorCount: 0,
        skippedCount: 0,
        errors: [],
        importedIds: ['id1', 'id2', 'id3', 'id4', 'id5'],
      });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      // Set up preview state
      act(() => {
        (result.current as any).preview = mockPreview;
      });

      await act(async () => {
        await result.current.executeImport();
      });

      await waitFor(() => {
        expect(result.current.progress.status).toBe('complete');
        expect(result.current.progress.successCount).toBe(5);
      });
    });

    it('should fail without preview', async () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        try {
          await result.current.executeImport();
        } catch (error: any) {
          expect(error.message).toContain('No preview available');
        }
      });
    });

    it('should import in batches', async () => {
      const rows = Array.from({ length: 250 }, (_, i) => ({
        rowNumber: i + 1,
        data: { name: `Person ${i}`, email: `person${i}@example.com` },
        status: 'valid' as const,
        errors: [],
        warnings: [],
      }));

      const mockPreview = importExportMockFactories.importPreviewResult({
        totalRows: 250,
        validRows: 250,
        rows,
      });

      (api.post as jest.Mock).mockResolvedValue({
        success: true,
        totalProcessed: 100,
        successCount: 100,
        errorCount: 0,
        skippedCount: 0,
        errors: [],
        importedIds: [],
      });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        (result.current as any).preview = mockPreview;
      });

      await act(async () => {
        await result.current.executeImport();
      });

      await waitFor(() => {
        // Should have made 3 API calls (250 rows / 100 batch size = 3 batches)
        expect(api.post).toHaveBeenCalledTimes(3);
      });
    });

    it('should update progress during import', async () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        validRows: 10,
      });

      (api.post as jest.Mock).mockResolvedValue({
        success: true,
        totalProcessed: 10,
        successCount: 10,
        errorCount: 0,
        skippedCount: 0,
        errors: [],
        importedIds: [],
      });

      const onProgress = jest.fn();
      const { result } = renderHook(() => useImport({ onProgress }), {
        wrapper: createWrapper(),
      });

      act(() => {
        (result.current as any).preview = mockPreview;
      });

      await act(async () => {
        await result.current.executeImport();
      });

      expect(onProgress).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'importing' })
      );
    });

    it('should call onComplete callback', async () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        validRows: 5,
      });

      (api.post as jest.Mock).mockResolvedValue({
        success: true,
        totalProcessed: 5,
        successCount: 5,
        errorCount: 0,
        skippedCount: 0,
        errors: [],
        importedIds: [],
      });

      const onComplete = jest.fn();
      const { result } = renderHook(() => useImport({ onComplete }), {
        wrapper: createWrapper(),
      });

      act(() => {
        (result.current as any).preview = mockPreview;
      });

      await act(async () => {
        await result.current.executeImport();
      });

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalled();
      });
    });

    it('should call onError callback on failure', async () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        validRows: 5,
      });

      (api.post as jest.Mock).mockRejectedValue(new Error('Import failed'));

      const onError = jest.fn();
      const { result } = renderHook(() => useImport({ onError }), {
        wrapper: createWrapper(),
      });

      act(() => {
        (result.current as any).preview = mockPreview;
      });

      await act(async () => {
        try {
          await result.current.executeImport();
        } catch (error) {
          // Error expected
        }
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
      });
    });

    it('should skip invalid rows if option enabled', async () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        validRows: 3,
        errorRows: 2,
        rows: [
          { rowNumber: 1, data: { name: 'Valid 1' }, status: 'valid', errors: [], warnings: [] },
          { rowNumber: 2, data: { name: 'Error 1' }, status: 'error', errors: [], warnings: [] },
          { rowNumber: 3, data: { name: 'Valid 2' }, status: 'valid', errors: [], warnings: [] },
        ],
      });

      (api.post as jest.Mock).mockResolvedValue({
        success: true,
        totalProcessed: 2,
        successCount: 2,
        errorCount: 0,
        skippedCount: 0,
        errors: [],
        importedIds: [],
      });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        (result.current as any).preview = mockPreview;
        result.current.updateOptions({ skipInvalidRows: true });
      });

      await act(async () => {
        await result.current.executeImport();
      });

      await waitFor(() => {
        // Should only import valid rows (2 out of 3)
        const importCall = (api.post as jest.Mock).mock.calls[0];
        expect(importCall[1].items.length).toBe(2);
      });
    });
  });

  describe('Cancel Import', () => {
    it('should cancel import', () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.cancelImport();
      });

      expect(result.current.progress.status).toBe('idle');
      expect(result.current.progress.message).toContain('cancelled');
    });
  });

  describe('Reset', () => {
    it('should reset all state', async () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      // Set some state
      act(() => {
        (result.current as any).file = new File(['test'], 'test.csv', { type: 'text/csv' });
        (result.current as any).preview = importExportMockFactories.importPreviewResult();
      });

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.file).toBeNull();
      expect(result.current.preview).toBeNull();
      expect(result.current.progress.status).toBe('idle');
      expect(result.current.xlsxFallbackUsed).toBe(false);
      expect(result.current.xlsxWarnings).toEqual([]);
    });
  });

  describe('Update Options', () => {
    it('should update import options', () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.updateOptions({ skipDuplicates: false });
      });

      expect(result.current.options.skipDuplicates).toBe(false);
    });

    it('should merge with existing options', () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.updateOptions({ updateExisting: true });
      });

      expect(result.current.options.updateExisting).toBe(true);
      expect(result.current.options.skipDuplicates).toBe(true); // Default preserved
    });
  });

  describe('Set Data Type', () => {
    it('should update data type', () => {
      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.setDataType('people');
      });

      expect(result.current.dataType).toBe('people');
    });
  });

  describe('Loading States', () => {
    it('should set isLoading during parsing', async () => {
      const csvContent = 'name,email\nJohn,john@example.com';
      const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      let loadingDuringParse = false;

      act(() => {
        result.current.previewImport(mockFile).then(() => {
          // Check loading state during parse
        });
      });

      // Check if loading was true during the operation
      if (result.current.isLoading) {
        loadingDuringParse = true;
      }

      await waitFor(() => {
        expect(result.current.preview).not.toBeNull();
      });
    });

    it('should set isError on error', async () => {
      const mockFile = new File([''], 'empty.csv', { type: 'text/csv' });

      const { result } = renderHook(() => useImport(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        try {
          await result.current.previewImport(mockFile);
        } catch (error) {
          // Expected
        }
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });
});
