/**
 * Tests for useExport hook.
 */

import { act, renderHook, waitFor } from '@/test-utils';
import { useExport } from '@/features/import-export/useExport';
import type { ExportColumn, ExportOptions } from '@/features/import-export/types';
import * as exportUtils from '@/features/import-export/utils';
import * as XLSX from 'xlsx';

jest.mock('xlsx', () => ({
  utils: {
    aoa_to_sheet: jest.fn(),
    book_new: jest.fn(),
    book_append_sheet: jest.fn(),
  },
  write: jest.fn(),
}));

jest.mock('@/features/import-export/utils', () => {
  const actual = jest.requireActual('@/features/import-export/utils');
  return {
    ...actual,
    downloadFile: jest.fn(),
  };
});

const mockedDownloadFile = exportUtils.downloadFile as jest.MockedFunction<
  typeof exportUtils.downloadFile
>;
const mockedAoaToSheet = XLSX.utils.aoa_to_sheet as jest.Mock;
const mockedBookNew = XLSX.utils.book_new as jest.Mock;
const mockedBookAppendSheet = XLSX.utils.book_append_sheet as jest.Mock;
const mockedXlsxWrite = XLSX.write as jest.Mock;

const TEST_COLUMNS: ExportColumn[] = [
  { key: 'name', header: 'Name' },
  { key: 'active', header: 'Active' },
];

const BASE_OPTIONS: ExportOptions = {
  format: 'xlsx',
  filename: 'schedule-export',
  columns: TEST_COLUMNS,
  includeHeaders: true,
  dateFormat: 'YYYY-MM-DD',
};

describe('useExport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedAoaToSheet.mockReturnValue({});
    mockedBookNew.mockReturnValue({ Sheets: {}, SheetNames: [] });
    mockedXlsxWrite.mockReturnValue(new Uint8Array([0x50, 0x4b, 0x03, 0x04]).buffer);
  });

  it('initializes with idle state', () => {
    const { result } = renderHook(() => useExport());

    expect(result.current.progress.status).toBe('idle');
    expect(result.current.isExporting).toBe(false);
    expect(result.current.isComplete).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('rejects export when data is empty', async () => {
    const { result } = renderHook(() => useExport());

    await expect(result.current.exportData([], BASE_OPTIONS)).rejects.toThrow(
      'No data to export'
    );
  });

  it('exports a true xlsx workbook and downloads .xlsx', async () => {
    const { result } = renderHook(() => useExport());
    const data = [{ name: 'Dr. Smith', active: true }];

    await act(async () => {
      await result.current.exportData(data, BASE_OPTIONS);
    });

    expect(mockedAoaToSheet).toHaveBeenCalledWith([
      ['Name', 'Active'],
      ['Dr. Smith', 'Yes'],
    ]);
    expect(mockedBookAppendSheet).toHaveBeenCalledWith(
      expect.any(Object),
      expect.any(Object),
      'Export'
    );
    expect(mockedXlsxWrite).toHaveBeenCalledWith(
      expect.any(Object),
      expect.objectContaining({
        bookType: 'xlsx',
        type: 'array',
        compression: true,
      })
    );
    expect(mockedDownloadFile).toHaveBeenCalledWith(
      expect.any(Blob),
      'schedule-export.xlsx',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    );
    expect(mockedDownloadFile.mock.calls[0][0]).toBeInstanceOf(Blob);

    await waitFor(() => {
      expect(result.current.progress.status).toBe('complete');
    });
  });

  it('omits header row when includeHeaders is false', async () => {
    const { result } = renderHook(() => useExport());
    const data = [{ name: 'Dr. Adams', active: false }];

    await act(async () => {
      await result.current.exportData(data, {
        ...BASE_OPTIONS,
        includeHeaders: false,
      });
    });

    expect(mockedAoaToSheet).toHaveBeenCalledWith([['Dr. Adams', 'No']]);
  });
});
