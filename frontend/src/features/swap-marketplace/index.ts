/**
 * Swap Marketplace Feature Module
 *
 * Provides comprehensive swap marketplace UI components for faculty
 * to browse available swap opportunities, create swap requests,
 * and manage incoming/outgoing swap requests.
 *
 * Components:
 * - SwapMarketplace: Main page component integrating all features
 * - SwapRequestCard: Display card for swap requests
 * - SwapRequestForm: Form to create new swap requests
 * - SwapFilters: Advanced filtering capabilities
 * - MySwapRequests: User's swap request management view
 *
 * Hooks:
 * - useSwapMarketplace: Fetch available swap opportunities
 * - useMySwapRequests: Fetch user's swap requests
 * - useCreateSwapRequest: Create new swap request mutation
 * - useAcceptSwap: Accept incoming swap request mutation
 * - useRejectSwap: Reject incoming swap request mutation
 * - useCancelSwap: Cancel outgoing swap request mutation
 * - useFacultyPreferences: Fetch faculty preferences
 */

// Components
export { SwapMarketplace } from './SwapMarketplace';
export { SwapRequestCard } from './SwapRequestCard';
export { SwapRequestForm } from './SwapRequestForm';
export { SwapFilters } from './SwapFilters';
export { MySwapRequests } from './MySwapRequests';

// Hooks
export {
  useSwapMarketplace,
  useMySwapRequests,
  useCreateSwapRequest,
  useAcceptSwap,
  useRejectSwap,
  useCancelSwap,
  useFacultyPreferences,
  useAvailableWeeks,
  useFacultyMembers,
  swapQueryKeys,
} from './hooks';

// Types
export type {
  SwapRequest,
  MarketplaceEntry,
  FacultyPreference,
  SwapFilters as SwapFiltersType,
  SwapSort,
  SwapPagination,
  SwapQueryParams,
  CreateSwapRequest,
  CreateSwapResponse,
  SwapRespondRequest,
  SwapRespondResponse,
  MySwapsResponse,
  MarketplaceResponse,
  MarketplaceTab,
  MyRequestsTab,
  MarketplacePageState,
  DateRange,
} from './types';

// Enums
export { SwapStatus, SwapType } from './types';

// Constants
export {
  SWAP_STATUS_LABELS,
  SWAP_TYPE_LABELS,
  SWAP_STATUS_COLORS,
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS,
  DEFAULT_SORT,
} from './types';
