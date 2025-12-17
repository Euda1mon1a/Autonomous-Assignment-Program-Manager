/**
 * Swap Marketplace Types and Interfaces
 *
 * Defines the data structures for swap marketplace functionality,
 * including swap requests, filters, and faculty preferences.
 */

// ============================================================================
// Core Swap Types
// ============================================================================

/**
 * Status of a swap request
 */
export enum SwapStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXECUTED = 'executed',
  CANCELLED = 'cancelled',
}

/**
 * Type of swap being requested
 */
export enum SwapType {
  ONE_TO_ONE = 'one_to_one',
  ABSORB = 'absorb',
}

/**
 * Single swap request entry
 */
export interface SwapRequest {
  id: string;
  sourceFacultyId: string;
  sourceFacultyName: string;
  sourceWeek: string; // ISO date string
  targetFacultyId?: string;
  targetFacultyName?: string;
  targetWeek?: string; // ISO date string
  swapType: SwapType;
  status: SwapStatus;
  requestedAt: string; // ISO datetime string
  requestedById?: string;
  approvedAt?: string;
  approvedById?: string;
  executedAt?: string;
  executedById?: string;
  reason?: string;
  notes?: string;
  isIncoming: boolean; // True if this request is directed to current user
  isOutgoing: boolean; // True if this request is from current user
  canAccept: boolean; // True if current user can accept this request
  canReject: boolean; // True if current user can reject this request
  canCancel: boolean; // True if current user can cancel this request
}

/**
 * Marketplace entry (simplified swap request for browsing)
 */
export interface MarketplaceEntry {
  requestId: string;
  requestingFacultyName: string;
  weekAvailable: string; // ISO date string
  reason?: string;
  postedAt: string; // ISO datetime string
  expiresAt?: string; // ISO datetime string
  isCompatible: boolean; // Based on viewer's schedule
}

/**
 * Faculty preference information
 */
export interface FacultyPreference {
  facultyId: string;
  preferredWeeks: string[]; // ISO date strings
  blockedWeeks: string[]; // ISO date strings
  maxWeeksPerMonth: number;
  maxConsecutiveWeeks: number;
  minGapBetweenWeeks: number;
  targetWeeksPerYear: number;
  notifySwapRequests: boolean;
  notifyScheduleChanges: boolean;
  notifyConflictAlerts: boolean;
  notifyReminderDays: number;
  notes?: string;
  updatedAt: string; // ISO datetime string
}

// ============================================================================
// Filter and Search Types
// ============================================================================

/**
 * Date range for filtering
 */
export interface DateRange {
  start: string; // ISO date string
  end: string; // ISO date string
}

/**
 * Swap marketplace filters
 */
export interface SwapFilters {
  dateRange?: DateRange;
  statuses?: SwapStatus[];
  swapTypes?: SwapType[];
  facultyIds?: string[];
  searchQuery?: string;
  showMyPostingsOnly?: boolean;
  showCompatibleOnly?: boolean;
}

/**
 * Sort configuration
 */
export interface SwapSort {
  field: 'requestedAt' | 'sourceWeek' | 'status' | 'sourceFacultyName';
  direction: 'asc' | 'desc';
}

/**
 * Pagination configuration
 */
export interface SwapPagination {
  page: number;
  pageSize: number;
}

/**
 * Complete query parameters for fetching swaps
 */
export interface SwapQueryParams {
  filters?: SwapFilters;
  sort?: SwapSort;
  pagination?: SwapPagination;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Request to create a new swap
 */
export interface CreateSwapRequest {
  weekToOffload: string; // ISO date string
  preferredTargetFacultyId?: string;
  reason?: string;
  autoFindCandidates?: boolean;
}

/**
 * Response after creating a swap request
 */
export interface CreateSwapResponse {
  success: boolean;
  requestId?: string;
  message: string;
  candidatesNotified: number;
}

/**
 * Request to respond to a swap (accept/reject)
 */
export interface SwapRespondRequest {
  accept: boolean;
  counterOfferWeek?: string; // ISO date string
  notes?: string;
}

/**
 * Response from swap respond operation
 */
export interface SwapRespondResponse {
  success: boolean;
  message: string;
}

/**
 * My swaps response (incoming, outgoing, recent)
 */
export interface MySwapsResponse {
  incomingRequests: SwapRequest[];
  outgoingRequests: SwapRequest[];
  recentSwaps: SwapRequest[];
}

/**
 * Marketplace response
 */
export interface MarketplaceResponse {
  entries: MarketplaceEntry[];
  total: number;
  myPostings: number;
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Tab mode for marketplace view
 */
export type MarketplaceTab = 'browse' | 'my-requests' | 'create';

/**
 * Tab mode for my requests view
 */
export type MyRequestsTab = 'outgoing' | 'incoming';

/**
 * Marketplace page state
 */
export interface MarketplacePageState {
  activeTab: MarketplaceTab;
  myRequestsTab: MyRequestsTab;
  filters: SwapFilters;
  sort: SwapSort;
  pagination: SwapPagination;
  selectedSwap?: SwapRequest;
  isFilterPanelOpen: boolean;
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Display labels for swap status
 */
export const SWAP_STATUS_LABELS: Record<SwapStatus, string> = {
  [SwapStatus.PENDING]: 'Pending',
  [SwapStatus.APPROVED]: 'Approved',
  [SwapStatus.REJECTED]: 'Rejected',
  [SwapStatus.EXECUTED]: 'Executed',
  [SwapStatus.CANCELLED]: 'Cancelled',
};

/**
 * Display labels for swap type
 */
export const SWAP_TYPE_LABELS: Record<SwapType, string> = {
  [SwapType.ONE_TO_ONE]: 'One-to-One Swap',
  [SwapType.ABSORB]: 'Absorb Week',
};

/**
 * Colors for swap status badges
 */
export const SWAP_STATUS_COLORS: Record<SwapStatus, string> = {
  [SwapStatus.PENDING]: 'yellow',
  [SwapStatus.APPROVED]: 'blue',
  [SwapStatus.REJECTED]: 'red',
  [SwapStatus.EXECUTED]: 'green',
  [SwapStatus.CANCELLED]: 'gray',
};

/**
 * Default pagination settings
 */
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

/**
 * Default sort configuration
 */
export const DEFAULT_SORT: SwapSort = {
  field: 'requestedAt',
  direction: 'desc',
};
