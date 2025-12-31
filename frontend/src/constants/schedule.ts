/**
 * Constants for Schedule Components
 *
 * This module centralizes magic numbers used across schedule grid,
 * views, and related UI components.
 */

// ==============================================================================
// React Query Cache Configuration
// ==============================================================================

/**
 * Cache time for blocks data (5 minutes)
 * Blocks change infrequently, so longer cache is acceptable
 */
export const BLOCKS_STALE_TIME_MS = 5 * 60 * 1000;

/**
 * Garbage collection time for blocks (30 minutes)
 * Keep blocks in cache for 30 minutes after last use
 */
export const BLOCKS_GC_TIME_MS = 30 * 60 * 1000;

/**
 * Cache time for assignments data (1 minute)
 * Assignments change more frequently, shorter cache
 */
export const ASSIGNMENTS_STALE_TIME_MS = 60 * 1000;

/**
 * Garbage collection time for assignments (30 minutes)
 */
export const ASSIGNMENTS_GC_TIME_MS = 30 * 60 * 1000;

/**
 * Cache time for people/residents data (10 minutes)
 */
export const PEOPLE_STALE_TIME_MS = 10 * 60 * 1000;

/**
 * Garbage collection time for people data (1 hour)
 */
export const PEOPLE_GC_TIME_MS = 60 * 60 * 1000;

// ==============================================================================
// PGY Level Constants
// ==============================================================================

/**
 * Post-Graduate Year 1 (Intern)
 */
export const PGY_LEVEL_1 = 1;

/**
 * Post-Graduate Year 2
 */
export const PGY_LEVEL_2 = 2;

/**
 * Post-Graduate Year 3
 */
export const PGY_LEVEL_3 = 3;

/**
 * Post-Graduate Year 4
 */
export const PGY_LEVEL_4 = 4;

/**
 * Post-Graduate Year 5
 */
export const PGY_LEVEL_5 = 5;

// ==============================================================================
// Text Display Constants
// ==============================================================================

/**
 * Number of characters to use for rotation template abbreviation
 * when no explicit abbreviation is provided
 */
export const ABBREVIATION_LENGTH = 3;

/**
 * Maximum length for person name display before truncation
 */
export const MAX_PERSON_NAME_LENGTH = 30;

/**
 * Maximum length for rotation template name display
 */
export const MAX_TEMPLATE_NAME_LENGTH = 50;

// ==============================================================================
// Grid Layout Constants
// ==============================================================================

/**
 * Maximum height for schedule grid viewport
 * calc(100vh - header - padding) ≈ 100vh - 220px
 */
export const SCHEDULE_GRID_MAX_HEIGHT = 'calc(100vh - 220px)';

/**
 * Maximum height for mobile schedule grid
 */
export const SCHEDULE_GRID_MAX_HEIGHT_MOBILE = 'calc(100vh - 180px)';

/**
 * Sticky column z-index for person name column
 */
export const STICKY_COLUMN_Z_INDEX = 10;

/**
 * Grid cell minimum width (pixels)
 */
export const GRID_CELL_MIN_WIDTH = 60;

/**
 * Grid cell minimum height (pixels)
 */
export const GRID_CELL_MIN_HEIGHT = 40;

// ==============================================================================
// Animation Constants
// ==============================================================================

/**
 * Duration for fade-in animation (seconds)
 */
export const FADE_IN_DURATION = 0.5;

/**
 * Duration for row hover transition (milliseconds)
 */
export const ROW_HOVER_TRANSITION_MS = 150;

/**
 * Duration for cell highlight transition (milliseconds)
 */
export const CELL_HIGHLIGHT_TRANSITION_MS = 200;

/**
 * Opacity for loading state
 */
export const LOADING_OPACITY = 0.6;

// ==============================================================================
// Color and Style Constants
// ==============================================================================

/**
 * Opacity for weekend cell backgrounds
 */
export const WEEKEND_CELL_OPACITY = 0.5;

/**
 * Opacity for hover effects
 */
export const HOVER_OPACITY = 0.8;

/**
 * Border radius for badges (pixels)
 */
export const BADGE_BORDER_RADIUS = 4;

/**
 * Padding for cell content (pixels)
 */
export const CELL_PADDING = 8;

// ==============================================================================
// Date Range Constants
// ==============================================================================

/**
 * Default number of days to show in week view
 */
export const WEEK_VIEW_DAYS = 7;

/**
 * Default number of days to show in month view
 */
export const MONTH_VIEW_DAYS = 30;

/**
 * Default number of days to show in day view
 */
export const DAY_VIEW_DAYS = 1;

/**
 * Number of weeks to show in multi-week view
 */
export const MULTI_WEEK_VIEW_WEEKS = 4;

// ==============================================================================
// Performance Constants
// ==============================================================================

/**
 * Maximum number of rows to render before virtualization
 */
export const VIRTUALIZATION_THRESHOLD = 50;

/**
 * Number of items to render above/below viewport
 */
export const VIRTUAL_OVERSCAN_COUNT = 5;

/**
 * Debounce delay for filter inputs (milliseconds)
 */
export const FILTER_DEBOUNCE_MS = 300;

/**
 * Throttle delay for scroll events (milliseconds)
 */
export const SCROLL_THROTTLE_MS = 100;

// ==============================================================================
// Accessibility Constants
// ==============================================================================

/**
 * Minimum touch target size (pixels) for mobile
 */
export const MIN_TOUCH_TARGET_SIZE = 44;

/**
 * Focus ring width (pixels)
 */
export const FOCUS_RING_WIDTH = 2;

/**
 * Minimum color contrast ratio (WCAG AA)
 */
export const MIN_CONTRAST_RATIO = 4.5;

// ==============================================================================
// Validation Constants
// ==============================================================================

/**
 * Maximum number of assignments per person per day
 */
export const MAX_ASSIGNMENTS_PER_DAY = 2;  // AM and PM

/**
 * Maximum number of consecutive days without a break
 */
export const MAX_CONSECUTIVE_DAYS = 6;  // Must have 1 in 7 off

/**
 * Maximum hours per week (ACGME 80-hour rule)
 */
export const MAX_HOURS_PER_WEEK = 80;

// ==============================================================================
// Error and Empty States
// ==============================================================================

/**
 * Retry delay for failed requests (milliseconds)
 */
export const RETRY_DELAY_MS = 1000;

/**
 * Maximum number of retry attempts
 */
export const MAX_RETRY_ATTEMPTS = 3;

/**
 * Timeout for data fetching (milliseconds)
 */
export const FETCH_TIMEOUT_MS = 30000;  // 30 seconds
