/**
 * Mock Data for Swap Marketplace Tests
 *
 * Provides reusable mock data for testing swap marketplace components
 */

import {
  SwapRequest,
  MarketplaceEntry,
  MySwapsResponse,
  SwapStatus,
  SwapType,
  MarketplaceResponse,
  CreateSwapResponse,
  SwapRespondResponse,
} from '@/features/swap-marketplace/types';

// ============================================================================
// Mock Swap Requests
// ============================================================================

export const mockSwapRequestIncoming: SwapRequest = {
  id: 'swap-1',
  sourceFacultyId: 'faculty-1',
  sourceFacultyName: 'Dr. John Smith',
  sourceWeek: '2025-01-15',
  targetFacultyId: 'faculty-2',
  targetFacultyName: 'Dr. Jane Doe',
  targetWeek: '2025-01-22',
  swapType: SwapType.ONE_TO_ONE,
  status: SwapStatus.PENDING,
  requestedAt: '2025-01-10T10:00:00Z',
  reason: 'Family emergency - need to swap this week',
  isIncoming: true,
  isOutgoing: false,
  canAccept: true,
  canReject: true,
  canCancel: false,
};

export const mockSwapRequestOutgoing: SwapRequest = {
  id: 'swap-2',
  sourceFacultyId: 'faculty-2',
  sourceFacultyName: 'Dr. Jane Doe',
  sourceWeek: '2025-02-05',
  targetFacultyId: 'faculty-3',
  targetFacultyName: 'Dr. Bob Johnson',
  targetWeek: '2025-02-12',
  swapType: SwapType.ONE_TO_ONE,
  status: SwapStatus.PENDING,
  requestedAt: '2025-01-25T14:30:00Z',
  reason: 'Conference attendance',
  isIncoming: false,
  isOutgoing: true,
  canAccept: false,
  canReject: false,
  canCancel: true,
};

export const mockSwapRequestApproved: SwapRequest = {
  id: 'swap-3',
  sourceFacultyId: 'faculty-1',
  sourceFacultyName: 'Dr. John Smith',
  sourceWeek: '2025-03-10',
  targetFacultyId: 'faculty-2',
  targetFacultyName: 'Dr. Jane Doe',
  targetWeek: '2025-03-17',
  swapType: SwapType.ONE_TO_ONE,
  status: SwapStatus.APPROVED,
  requestedAt: '2025-02-15T09:00:00Z',
  approvedAt: '2025-02-16T11:00:00Z',
  reason: 'Vacation',
  isIncoming: false,
  isOutgoing: true,
  canAccept: false,
  canReject: false,
  canCancel: false,
};

export const mockSwapRequestRejected: SwapRequest = {
  id: 'swap-4',
  sourceFacultyId: 'faculty-3',
  sourceFacultyName: 'Dr. Bob Johnson',
  sourceWeek: '2025-04-01',
  targetFacultyId: 'faculty-2',
  targetFacultyName: 'Dr. Jane Doe',
  targetWeek: '2025-04-08',
  swapType: SwapType.ONE_TO_ONE,
  status: SwapStatus.REJECTED,
  requestedAt: '2025-03-20T16:00:00Z',
  reason: 'Schedule conflict',
  notes: 'Already have commitments that week',
  isIncoming: true,
  isOutgoing: false,
  canAccept: false,
  canReject: false,
  canCancel: false,
};

export const mockSwapRequestAbsorb: SwapRequest = {
  id: 'swap-5',
  sourceFacultyId: 'faculty-1',
  sourceFacultyName: 'Dr. John Smith',
  sourceWeek: '2025-05-15',
  swapType: SwapType.ABSORB,
  status: SwapStatus.PENDING,
  requestedAt: '2025-05-01T08:00:00Z',
  reason: 'Need someone to cover my week',
  isIncoming: false,
  isOutgoing: true,
  canAccept: false,
  canReject: false,
  canCancel: true,
};

// ============================================================================
// Mock Marketplace Entries
// ============================================================================

export const mockMarketplaceEntry1: MarketplaceEntry = {
  requestId: 'swap-10',
  requestingFacultyName: 'Dr. Sarah Williams',
  weekAvailable: '2025-06-01',
  reason: 'Medical conference',
  postedAt: '2025-05-20T10:00:00Z',
  expiresAt: '2025-05-31T23:59:59Z',
  isCompatible: true,
};

export const mockMarketplaceEntry2: MarketplaceEntry = {
  requestId: 'swap-11',
  requestingFacultyName: 'Dr. Michael Chen',
  weekAvailable: '2025-06-15',
  reason: 'Personal leave',
  postedAt: '2025-06-01T12:00:00Z',
  isCompatible: false,
};

export const mockMarketplaceEntry3: MarketplaceEntry = {
  requestId: 'swap-12',
  requestingFacultyName: 'Dr. Emily Brown',
  weekAvailable: '2025-07-01',
  postedAt: '2025-06-20T14:00:00Z',
  isCompatible: true,
};

// ============================================================================
// Mock API Responses
// ============================================================================

export const mockMarketplaceResponse: MarketplaceResponse = {
  entries: [mockMarketplaceEntry1, mockMarketplaceEntry2, mockMarketplaceEntry3],
  total: 3,
  myPostings: 1,
};

export const mockEmptyMarketplaceResponse: MarketplaceResponse = {
  entries: [],
  total: 0,
  myPostings: 0,
};

export const mockMySwapsResponse: MySwapsResponse = {
  incomingRequests: [mockSwapRequestIncoming, mockSwapRequestRejected],
  outgoingRequests: [mockSwapRequestOutgoing, mockSwapRequestApproved],
  recentSwaps: [mockSwapRequestApproved, mockSwapRequestRejected],
};

export const mockEmptyMySwapsResponse: MySwapsResponse = {
  incomingRequests: [],
  outgoingRequests: [],
  recentSwaps: [],
};

export const mockCreateSwapResponse: CreateSwapResponse = {
  success: true,
  requestId: 'swap-new-1',
  message: 'Swap request created successfully',
  candidatesNotified: 5,
};

export const mockSwapRespondResponse: SwapRespondResponse = {
  success: true,
  message: 'Swap request accepted successfully',
};

// ============================================================================
// Mock Available Weeks
// ============================================================================

export const mockAvailableWeeks = [
  { date: '2025-07-01', hasConflict: false },
  { date: '2025-07-15', hasConflict: false },
  { date: '2025-08-01', hasConflict: true },
  { date: '2025-08-15', hasConflict: false },
  { date: '2025-09-01', hasConflict: false },
];

export const mockEmptyAvailableWeeks: Array<{ date: string; hasConflict: boolean }> = [];

// ============================================================================
// Mock Faculty Members
// ============================================================================

export const mockFacultyMembers = [
  { id: 'faculty-1', name: 'Dr. John Smith' },
  { id: 'faculty-2', name: 'Dr. Jane Doe' },
  { id: 'faculty-3', name: 'Dr. Bob Johnson' },
  { id: 'faculty-4', name: 'Dr. Sarah Williams' },
  { id: 'faculty-5', name: 'Dr. Michael Chen' },
  { id: 'faculty-6', name: 'Dr. Emily Brown' },
];

export const mockEmptyFacultyMembers: Array<{ id: string; name: string }> = [];
