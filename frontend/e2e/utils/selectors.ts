/**
 * Page Object Selectors
 *
 * Centralized selectors for all pages to avoid duplication
 * and make tests more maintainable.
 */

export const selectors = {
  // Common UI elements
  common: {
    loadingSpinner: '[data-testid="loading-spinner"]',
    toast: '[data-testid="toast"]',
    toastClose: '[data-testid="toast-close"]',
    errorMessage: '[data-testid="error-message"]',
    successMessage: '[data-testid="success-message"]',
    modal: '[role="dialog"]',
    modalClose: '[role="dialog"] button:has-text("Close")',
    confirmButton: 'button:has-text("Confirm")',
    cancelButton: 'button:has-text("Cancel")',
    saveButton: 'button:has-text("Save")',
    deleteButton: 'button:has-text("Delete")',
    editButton: 'button:has-text("Edit")',
    backButton: 'button:has-text("Back")',
  },

  // Navigation
  nav: {
    userMenu: '[data-testid="user-menu"]',
    logoutButton: 'button:has-text("Logout")',
    dashboardLink: 'a:has-text("Dashboard")',
    scheduleLink: 'a:has-text("Schedule")',
    swapLink: 'a:has-text("Swaps")',
    complianceLink: 'a:has-text("Compliance")',
    resilienceLink: 'a:has-text("Resilience")',
    settingsLink: 'a:has-text("Settings")',
  },

  // Login page
  login: {
    emailInput: 'input[name="email"]',
    passwordInput: 'input[name="password"]',
    submitButton: 'button[type="submit"]',
    forgotPasswordLink: 'a:has-text("Forgot Password")',
    errorMessage: '[data-testid="login-error"]',
    rememberMeCheckbox: 'input[name="remember"]',
  },

  // Dashboard
  dashboard: {
    welcomeMessage: '[data-testid="welcome-message"]',
    upcomingShifts: '[data-testid="upcoming-shifts"]',
    recentAlerts: '[data-testid="recent-alerts"]',
    quickStats: '[data-testid="quick-stats"]',
    complianceWidget: '[data-testid="compliance-widget"]',
    resilienceWidget: '[data-testid="resilience-widget"]',
  },

  // Schedule page
  schedule: {
    calendar: '[data-testid="schedule-calendar"]',
    calendarDay: '[data-testid="calendar-day"]',
    calendarBlock: '[data-testid="calendar-block"]',
    assignment: '[data-testid="assignment"]',
    assignmentCard: '[data-testid="assignment-card"]',
    createAssignmentButton: 'button:has-text("Create Assignment")',
    filterButton: '[data-testid="filter-button"]',
    exportButton: '[data-testid="export-button"]',
    printButton: '[data-testid="print-button"]',
    viewModeToggle: '[data-testid="view-mode-toggle"]',
    dateRangePicker: '[data-testid="date-range-picker"]',
    personFilter: '[data-testid="person-filter"]',
    rotationFilter: '[data-testid="rotation-filter"]',
    conflictIndicator: '[data-testid="conflict-indicator"]',
    emptyState: '[data-testid="schedule-empty-state"]',
  },

  // Assignment form
  assignment: {
    personSelect: 'select[name="personId"]',
    blockSelect: 'select[name="blockId"]',
    rotationSelect: 'select[name="rotationId"]',
    statusSelect: 'select[name="status"]',
    notesTextarea: 'textarea[name="notes"]',
    submitButton: 'button[type="submit"]',
    deleteButton: '[data-testid="delete-assignment"]',
    conflictWarning: '[data-testid="conflict-warning"]',
    validationError: '[data-testid="validation-error"]',
  },

  // Swap page
  swap: {
    swapList: '[data-testid="swap-list"]',
    swapCard: '[data-testid="swap-card"]',
    createSwapButton: 'button:has-text("Create Swap")',
    swapStatus: '[data-testid="swap-status"]',
    approveButton: '[data-testid="approve-swap"]',
    rejectButton: '[data-testid="reject-swap"]',
    rollbackButton: '[data-testid="rollback-swap"]',
    autoMatchButton: '[data-testid="auto-match"]',
    matchesList: '[data-testid="matches-list"]',
    swapHistory: '[data-testid="swap-history"]',
    filterStatus: '[data-testid="filter-status"]',
    filterPerson: '[data-testid="filter-person"]',
  },

  // Swap form
  swapForm: {
    swapType: 'select[name="swapType"]',
    requestorAssignment: 'select[name="requestor_assignmentId"]',
    targetAssignment: 'select[name="target_assignmentId"]',
    reason: 'textarea[name="reason"]',
    submitButton: 'button[type="submit"]',
    cancelButton: 'button:has-text("Cancel")',
    validationError: '[data-testid="swap-validation-error"]',
  },

  // Compliance page
  compliance: {
    complianceSummary: '[data-testid="compliance-summary"]',
    violationsList: '[data-testid="violations-list"]',
    violationCard: '[data-testid="violation-card"]',
    workHoursChart: '[data-testid="work-hours-chart"]',
    dayOffIndicator: '[data-testid="day-off-indicator"]',
    supervisionRatio: '[data-testid="supervision-ratio"]',
    filterPerson: '[data-testid="compliance-filter-person"]',
    filterDateRange: '[data-testid="compliance-filter-date"]',
    exportReport: '[data-testid="export-compliance-report"]',
    violationSeverity: '[data-testid="violation-severity"]',
  },

  // Resilience dashboard
  resilience: {
    dashboard: '[data-testid="resilience-dashboard"]',
    defenseLevel: '[data-testid="defense-level"]',
    defenseLevelBadge: '[data-testid="defense-level-badge"]',
    utilizationChart: '[data-testid="utilization-chart"]',
    utilizationValue: '[data-testid="utilization-value"]',
    n1Contingency: '[data-testid="n1-contingency"]',
    alertsList: '[data-testid="alerts-list"]',
    alertCard: '[data-testid="alert-card"]',
    burnoutRt: '[data-testid="burnout-rt"]',
    criticalIndex: '[data-testid="critical-index"]',
    coverageGaps: '[data-testid="coverage-gaps"]',
    refreshButton: '[data-testid="refresh-dashboard"]',
  },

  // Settings page
  settings: {
    profileTab: '[data-testid="profile-tab"]',
    securityTab: '[data-testid="security-tab"]',
    notificationsTab: '[data-testid="notifications-tab"]',
    preferencesTab: '[data-testid="preferences-tab"]',
    saveSettings: 'button:has-text("Save Settings")',
    changePassword: '[data-testid="change-password"]',
    oldPassword: 'input[name="old_password"]',
    newPassword: 'input[name="newPassword"]',
    confirmPassword: 'input[name="confirmPassword"]',
  },

  // Table components
  table: {
    header: 'thead',
    body: 'tbody',
    row: 'tbody tr',
    cell: 'td',
    sortButton: '[data-testid="sort-button"]',
    paginationNext: '[data-testid="pagination-next"]',
    paginationPrev: '[data-testid="pagination-prev"]',
    paginationPage: '[data-testid="pagination-page"]',
    rowsPerPage: 'select[name="rows_per_page"]',
  },

  // Form validation
  validation: {
    required: '.error:has-text("required")',
    invalid: '.error:has-text("invalid")',
    fieldError: '[data-testid="field-error"]',
  },

  // Accessibility
  a11y: {
    skipToMain: '[href="#main-content"]',
    mainContent: '#main-content',
    ariaLive: '[aria-live]',
    ariaLabel: '[aria-label]',
    ariaDescribedby: '[aria-describedby]',
  },

  // Drag and drop
  dragDrop: {
    draggable: '[draggable="true"]',
    dropzone: '[data-dropzone]',
    dragHandle: '[data-testid="drag-handle"]',
    dragPreview: '[data-testid="drag-preview"]',
  },

  // Calendar specific
  calendar: {
    month: '[data-testid="calendar-month"]',
    week: '[data-testid="calendar-week"]',
    day: '[data-testid="calendar-day"]',
    prevMonth: '[data-testid="prev-month"]',
    nextMonth: '[data-testid="next-month"]',
    today: '[data-testid="today-button"]',
    dateCell: '[data-testid="date-cell"]',
  },
};

/**
 * Get selector with dynamic value
 */
export function getSelectorWithText(baseSelector: string, text: string): string {
  return `${baseSelector}:has-text("${text}")`;
}

/**
 * Get selector by test ID
 */
export function getByTestId(testId: string): string {
  return `[data-testid="${testId}"]`;
}

/**
 * Get selector by ARIA label
 */
export function getByAriaLabel(label: string): string {
  return `[aria-label="${label}"]`;
}

/**
 * Get selector by role
 */
export function getByRole(role: string, name?: string): string {
  return name ? `[role="${role}"][aria-label="${name}"]` : `[role="${role}"]`;
}

/**
 * Get nth element selector
 */
export function getNthSelector(baseSelector: string, index: number): string {
  return `${baseSelector}:nth-child(${index})`;
}

/**
 * Get selector by data attribute
 */
export function getByData(attribute: string, value: string): string {
  return `[data-${attribute}="${value}"]`;
}

/**
 * Combine selectors
 */
export function combineSelectors(...selectors: string[]): string {
  return selectors.join(' ');
}

/**
 * Get parent selector
 */
export function getParent(childSelector: string): string {
  return `${childSelector} >> xpath=..`;
}

/**
 * Get sibling selector
 */
export function getSibling(selector: string, siblingSelector: string): string {
  return `${selector} ~ ${siblingSelector}`;
}
