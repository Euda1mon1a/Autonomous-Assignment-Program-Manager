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
