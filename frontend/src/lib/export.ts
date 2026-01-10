// Export utility functions for CSV and JSON data export

export interface Column {
  key: string;
  header: string;
}

/**
 * Downloads a file with the given content
 */
export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Escapes a value for CSV format
 */
function escapeCSVValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  const stringValue = String(value);

  // If the value contains comma, newline, or quote, wrap in quotes
  if (stringValue.includes(',') || stringValue.includes('\n') || stringValue.includes('"')) {
    return `"${stringValue.replace(/"/g, '""')}"`;
  }

  return stringValue;
}

/**
 * Gets a nested value from an object using dot notation
 */
function getNestedValue(obj: Record<string, unknown>, key: string): unknown {
  return key.split('.').reduce((acc: unknown, part: string) => {
    if (acc && typeof acc === 'object' && part in acc) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, obj);
}

/**
 * Exports data to CSV format and triggers download
 */
export function exportToCSV(data: Record<string, unknown>[], filename: string, columns: Column[]): void {
  if (!data || data.length === 0) {
    return;
  }

  // Create header row
  const headerRow = columns.map(col => escapeCSVValue(col.header)).join(',');

  // Create data rows
  const dataRows = data.map(item => {
    return columns.map(col => {
      const value = getNestedValue(item, col.key);
      return escapeCSVValue(value);
    }).join(',');
  });

  const csvContent = [headerRow, ...dataRows].join('\n');

  // Add .csv extension if not present
  const csvFilename = filename.endsWith('.csv') ? filename : `${filename}.csv`;

  downloadFile(csvContent, csvFilename, 'text/csv;charset=utf-8;');
}

/**
 * Exports data to JSON format and triggers download
 */
export function exportToJSON(data: unknown[], filename: string): void {
  if (!data || data.length === 0) {
    return;
  }

  const jsonContent = JSON.stringify(data, null, 2);

  // Add .json extension if not present
  const jsonFilename = filename.endsWith('.json') ? filename : `${filename}.json`;

  downloadFile(jsonContent, jsonFilename, 'application/json');
}

/**
 * Export schedule to legacy Excel format via backend API
 */
export async function exportToLegacyXlsx(
  startDate: string,
  endDate: string,
  blockNumber?: number,
  federalHolidays?: string[]
): Promise<void> {
  const params = new URLSearchParams({
    startDate: startDate,
    endDate: endDate,
  });

  if (blockNumber !== undefined) {
    params.append('blockNumber', blockNumber.toString());
  }

  if (federalHolidays && federalHolidays.length > 0) {
    params.append('federal_holidays', federalHolidays.join(','));
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = `${apiUrl}/export/schedule/xlsx?${params.toString()}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to export Excel file');
    }

    // Get the blob from response
    const blob = await response.blob();

    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `schedule_${startDate}_${endDate}.xlsx`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=([^;]+)/);
      if (match) {
        filename = match[1].replace(/"/g, '');
      }
    }

    // Create download link
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    // Re-throw to allow UI components to handle the error with user-facing notifications
    throw error instanceof Error
      ? error
      : new Error(`Excel export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}
