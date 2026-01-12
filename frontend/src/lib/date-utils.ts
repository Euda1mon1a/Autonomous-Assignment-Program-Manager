/**
 * Date Utilities
 *
 * Local date formatting helpers to avoid timezone issues with toISOString().
 * toISOString() converts to UTC which can shift dates in negative timezones.
 */

/**
 * Format a Date to YYYY-MM-DD string using local timezone.
 * Unlike toISOString().split('T')[0], this won't shift to prior day
 * in negative timezones (e.g., HST, AKST).
 */
export function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Get today's date as YYYY-MM-DD string in local timezone.
 */
export function getTodayLocal(): string {
  return formatLocalDate(new Date());
}

/**
 * Get the first day of the current month as YYYY-MM-DD.
 */
export function getFirstOfMonthLocal(): string {
  const today = new Date();
  return formatLocalDate(new Date(today.getFullYear(), today.getMonth(), 1));
}

/**
 * Get the last day of the current month as YYYY-MM-DD.
 */
export function getLastOfMonthLocal(): string {
  const today = new Date();
  return formatLocalDate(new Date(today.getFullYear(), today.getMonth() + 1, 0));
}

/**
 * Add days to a date string and return YYYY-MM-DD.
 * Parses as local time to avoid UTC date shift in negative timezones.
 */
export function addDaysLocal(dateStr: string, days: number): string {
  // Parse as local time by splitting into components
  const [year, month, day] = dateStr.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  date.setDate(date.getDate() + days);
  return formatLocalDate(date);
}

/**
 * Get Monday of the week containing the given date.
 */
export function getMondayOfWeek(date: Date = new Date()): string {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day; // Sunday -> prev Monday, else back to Monday
  d.setDate(d.getDate() + diff);
  return formatLocalDate(d);
}
