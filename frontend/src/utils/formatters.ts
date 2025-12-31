/**
 * Formatting utilities for dates, numbers, and text.
 */

/**
 * Format a date according to specified format string.
 *
 * @param date - Date to format
 * @param format - Format string ('short', 'long', 'iso', or custom)
 * @returns Formatted date string
 */
export function formatDate(date: Date | string, format: string = 'short'): string {
  const d = typeof date === 'string' ? new Date(date) : date;

  if (isNaN(d.getTime())) {
    return 'Invalid Date';
  }

  switch (format) {
    case 'short':
      // MM/DD/YYYY
      return d.toLocaleDateString('en-US');

    case 'long':
      // Month DD, YYYY
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });

    case 'iso':
      // YYYY-MM-DD
      return d.toISOString().split('T')[0];

    case 'time':
      // HH:MM AM/PM
      return d.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
      });

    case 'datetime':
      // MM/DD/YYYY HH:MM AM/PM
      return d.toLocaleString('en-US');

    default:
      return d.toLocaleDateString('en-US');
  }
}

/**
 * Format duration in minutes to human-readable string.
 *
 * @param minutes - Duration in minutes
 * @returns Formatted duration (e.g., "2h 30m", "45m")
 */
export function formatDuration(minutes: number): string {
  if (minutes < 0) {
    return '0m';
  }

  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (hours === 0) {
    return `${mins}m`;
  }

  if (mins === 0) {
    return `${hours}h`;
  }

  return `${hours}h ${mins}m`;
}

/**
 * Format a number as a percentage.
 *
 * @param value - Value to format (0-1 for fraction, 0-100 for percentage)
 * @param decimals - Number of decimal places (default: 1)
 * @param isFraction - Whether value is a fraction (0-1) or percentage (0-100)
 * @returns Formatted percentage string (e.g., "75.5%")
 */
export function formatPercentage(
  value: number,
  decimals: number = 1,
  isFraction: boolean = true
): string {
  const percentage = isFraction ? value * 100 : value;
  return `${percentage.toFixed(decimals)}%`;
}

/**
 * Truncate text to maximum length with ellipsis.
 *
 * @param text - Text to truncate
 * @param maxLength - Maximum length (including ellipsis)
 * @param suffix - Suffix to add when truncating (default: "...")
 * @returns Truncated text
 */
export function truncateText(
  text: string,
  maxLength: number,
  suffix: string = '...'
): string {
  if (text.length <= maxLength) {
    return text;
  }

  const truncateAt = maxLength - suffix.length;
  if (truncateAt <= 0) {
    return suffix.slice(0, maxLength);
  }

  return text.slice(0, truncateAt) + suffix;
}

/**
 * Pluralize a word based on count.
 *
 * @param count - Count to determine pluralization
 * @param singular - Singular form of the word
 * @param plural - Plural form (optional, defaults to singular + "s")
 * @returns Pluralized string with count (e.g., "1 item", "2 items")
 */
export function pluralize(
  count: number,
  singular: string,
  plural?: string
): string {
  const word = count === 1 ? singular : (plural || `${singular}s`);
  return `${count} ${word}`;
}
