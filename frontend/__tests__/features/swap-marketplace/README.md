# Swap Marketplace Test Suite

Comprehensive test coverage for the Swap Marketplace feature module.

## Test Files Created

### 1. mockData.ts
Mock data utilities for testing swap marketplace components.

**Includes:**
- Mock swap requests (incoming, outgoing, approved, rejected, absorb types)
- Mock marketplace entries (compatible and non-compatible)
- Mock API responses (marketplace, my swaps, create/respond operations)
- Mock available weeks and faculty members
- Empty state mocks for edge case testing

---

### 2. SwapRequestCard.test.tsx (442 lines)
Tests for the `SwapRequestCard` component displaying individual swap requests.

**Test Coverage (28 test cases):**

#### Marketplace Entry Rendering (6 tests)
- ✓ Renders marketplace entry with faculty name
- ✓ Displays week available date
- ✓ Shows compatible badge when isCompatible is true
- ✓ Hides compatible badge when isCompatible is false
- ✓ Displays reason when provided
- ✓ Renders view details button

#### Swap Request Rendering (8 tests)
- ✓ Renders swap type label
- ✓ Shows incoming request label
- ✓ Shows outgoing request label
- ✓ Displays status badge
- ✓ Displays source faculty name
- ✓ Displays target faculty name for one-to-one swap
- ✓ Does not display target faculty for absorb swap
- ✓ Displays requested date

#### Action Buttons (8 tests)
- ✓ Shows Accept button when canAccept is true
- ✓ Shows Reject button when canReject is true
- ✓ Shows Cancel button when canCancel is true
- ✓ Hides inappropriate buttons based on permissions
- ✓ No action buttons when status is approved

#### Accept/Reject/Cancel Flows (5 tests)
- ✓ Shows notes textarea when Accept button is clicked
- ✓ Shows notes textarea when Reject button is clicked
- ✓ Allows typing notes
- ✓ Cancels action mode correctly
- ✓ Shows confirmation dialog for cancel

#### Edge Cases (1 test)
- ✓ Handles empty state when no data provided

---

### 3. SwapFilters.test.tsx (539 lines)
Tests for the `SwapFilters` component with search and filtering capabilities.

**Test Coverage (43 test cases):**

#### Rendering (6 tests)
- ✓ Renders filters heading
- ✓ Renders search input
- ✓ Renders My Postings Only button
- ✓ Renders Compatible Only button
- ✓ Shows active filter count
- ✓ Hides count when no filters active

#### Search Functionality (3 tests)
- ✓ Calls onFiltersChange when search query is entered
- ✓ Clears search query when input is emptied
- ✓ Displays existing search query

#### Quick Toggle Buttons (8 tests)
- ✓ Toggles My Postings Only filter on/off
- ✓ Toggles Compatible Only filter on/off
- ✓ Highlights active toggle buttons

#### Expand/Collapse (3 tests)
- ✓ Initially hides expanded filters
- ✓ Shows expanded filters when Expand is clicked
- ✓ Hides filters when Collapse is clicked

#### Date Range Filter (6 tests)
- ✓ Shows quick date range buttons when expanded
- ✓ Applies date range when quick button is clicked
- ✓ Shows Clear button when date range is active
- ✓ Displays selected date range
- ✓ Clears date range when Clear is clicked

#### Status Filter (5 tests)
- ✓ Shows all status options when expanded
- ✓ Toggles status filter on
- ✓ Allows multiple status selections
- ✓ Toggles status filter off
- ✓ Highlights selected status buttons

#### Swap Type Filter (4 tests)
- ✓ Shows swap type options when expanded
- ✓ Toggles swap type filter on/off
- ✓ Highlights selected swap type buttons

#### Reset Functionality (3 tests)
- ✓ Shows Reset button when filters are active
- ✓ Hides Reset button when no filters active
- ✓ Resets all filters when Reset is clicked

#### Loading State (2 tests)
- ✓ Disables inputs when isLoading is true
- ✓ Disables toggle buttons when isLoading is true

---

### 4. SwapRequestForm.test.tsx (686 lines)
Tests for the `SwapRequestForm` component for creating new swap requests.

**Test Coverage (48 test cases):**

#### Loading State (2 tests)
- ✓ Shows loading spinner when weeks are loading
- ✓ Shows loading spinner when faculty are loading

#### Error State (3 tests)
- ✓ Shows error when weeks fail to load
- ✓ Shows error when faculty fail to load
- ✓ Shows Go Back button in error state

#### Form Rendering (6 tests)
- ✓ Renders form title
- ✓ Renders week selection dropdown
- ✓ Renders swap mode radio buttons
- ✓ Renders reason textarea
- ✓ Renders Create Request button
- ✓ Renders Cancel/Reset button

#### Week Selection (4 tests)
- ✓ Populates week options from available weeks
- ✓ Shows conflict indicator for weeks with conflicts
- ✓ Shows message when no weeks available
- ✓ Disables submit button when no weeks available

#### Swap Mode Selection (4 tests)
- ✓ Has auto-find mode selected by default
- ✓ Hides target faculty field in auto mode
- ✓ Shows target faculty field when specific mode is selected
- ✓ Switches between modes correctly

#### Target Faculty Selection (2 tests)
- ✓ Populates faculty options in specific mode
- ✓ Displays all faculty members as options

#### Reason Text Area (4 tests)
- ✓ Allows typing in reason textarea
- ✓ Shows character count
- ✓ Updates character count when typing
- ✓ Enforces 500 character limit

#### Form Validation (3 tests)
- ✓ Shows error when submitting without week selection
- ✓ Shows error when specific mode but no faculty chosen
- ✓ Does not show faculty error in auto mode

#### Form Submission (8 tests)
- ✓ Submits form with correct data in auto mode
- ✓ Submits form with correct data in specific mode
- ✓ Calls onSuccess after successful submission
- ✓ Resets form after successful submission
- ✓ Shows success message after submission
- ✓ Shows loading state during submission
- ✓ Disables form fields during submission
- ✓ Shows error message on submission failure

#### Cancel/Reset Functionality (2 tests)
- ✓ Calls onCancel when Cancel button is clicked
- ✓ Resets form when Reset button is clicked

#### Help Section (2 tests)
- ✓ Renders help section
- ✓ Shows helpful instructions

---

### 5. MySwapRequests.test.tsx (358 lines)
Tests for the `MySwapRequests` component managing incoming/outgoing requests.

**Test Coverage (23 test cases):**

#### Loading State (1 test)
- ✓ Shows loading spinner when data is loading

#### Error State (3 tests)
- ✓ Shows error message when request fails
- ✓ Shows retry button in error state
- ✓ Calls refetch when retry button is clicked

#### Tabs Rendering (5 tests)
- ✓ Renders all three tabs (Incoming, Outgoing, Recent)
- ✓ Shows count badges on tabs
- ✓ Highlights active tab
- ✓ Switches tabs when clicked

#### Incoming Tab (3 tests)
- ✓ Displays incoming requests by default
- ✓ Renders incoming request cards
- ✓ Shows empty state when no incoming requests

#### Outgoing Tab (3 tests)
- ✓ Displays outgoing requests when tab is clicked
- ✓ Renders outgoing request cards
- ✓ Shows empty state when no outgoing requests

#### Recent Tab (3 tests)
- ✓ Displays recent swaps when tab is clicked
- ✓ Renders recent swap cards
- ✓ Shows empty state when no recent swaps

#### Summary Stats (3 tests)
- ✓ Displays summary section when there are requests
- ✓ Shows correct counts in summary
- ✓ Does not display summary when no requests exist

#### Action Completion (1 test)
- ✓ Calls refetch when swap card action is completed

#### Tab Badge Visibility (1 test)
- ✓ Shows badge only when count is greater than 0

---

### 6. SwapMarketplace.test.tsx (517 lines)
Tests for the main `SwapMarketplace` component integrating all features.

**Test Coverage (28 test cases):**

#### Page Header (2 tests)
- ✓ Renders page title
- ✓ Renders page description

#### Tab Navigation (4 tests)
- ✓ Renders all three main tabs
- ✓ Has Browse Swaps tab active by default
- ✓ Switches to My Requests tab when clicked
- ✓ Switches to Create Request tab when clicked

#### Browse Tab - Loading/Error States (4 tests)
- ✓ Shows loading spinner when marketplace data is loading
- ✓ Shows error message when marketplace fails to load
- ✓ Shows retry button in error state
- ✓ Calls refetch when retry button is clicked

#### Browse Tab - Stats Display (3 tests)
- ✓ Displays total available swaps
- ✓ Displays compatible swaps count
- ✓ Displays my postings count

#### Browse Tab - Marketplace Entries (3 tests)
- ✓ Renders SwapFilters component
- ✓ Renders marketplace entry cards
- ✓ Shows entry count in heading

#### Browse Tab - Empty State (3 tests)
- ✓ Shows empty state when no swaps available
- ✓ Shows Create a Request button in empty state
- ✓ Navigates to create tab when button clicked

#### My Requests Tab (1 test)
- ✓ Renders MySwapRequests component when tab is clicked

#### Create Request Tab (3 tests)
- ✓ Renders SwapRequestForm when tab is clicked
- ✓ Navigates to My Requests after successful submission
- ✓ Navigates to Browse when cancel is clicked

#### Filter Updates (2 tests)
- ✓ Passes filters to useSwapMarketplace hook
- ✓ Updates filters when SwapFilters emits changes

#### Help Section (2 tests)
- ✓ Renders help section at bottom of page
- ✓ Shows three-step guide with descriptions

#### Conditional Query Enabling (2 tests)
- ✓ Enables marketplace query only on browse tab
- ✓ Re-enables query when returning to browse tab

#### Responsive Design (1 test)
- ✓ Has proper spacing classes for responsive layout

---

### 7. hooks.test.ts (532 lines)
Tests for React Query hooks managing data fetching and mutations.

**Test Coverage (26 test cases):**

#### useSwapMarketplace (4 tests)
- ✓ Fetches marketplace data successfully
- ✓ Passes filters to API call
- ✓ Handles API errors
- ✓ Uses correct query key

#### useMySwapRequests (2 tests)
- ✓ Fetches my swaps data successfully
- ✓ Handles API errors

#### useFacultyPreferences (1 test)
- ✓ Fetches faculty preferences successfully

#### useAvailableWeeks (2 tests)
- ✓ Fetches available weeks successfully
- ✓ Handles empty weeks array

#### useFacultyMembers (1 test)
- ✓ Fetches faculty members successfully

#### useCreateSwapRequest (3 tests)
- ✓ Creates swap request successfully
- ✓ Handles creation errors
- ✓ Invalidates queries after successful creation

#### useAcceptSwap (2 tests)
- ✓ Accepts swap request successfully
- ✓ Accepts without notes

#### useRejectSwap (1 test)
- ✓ Rejects swap request successfully

#### useCancelSwap (1 test)
- ✓ Cancels swap request successfully

#### Query Keys (6 tests)
- ✓ Generates correct query key for all swaps
- ✓ Generates correct query key for marketplace without filters
- ✓ Generates correct query key for marketplace with filters
- ✓ Generates correct query key for my swaps
- ✓ Generates correct query key for specific swap request
- ✓ Generates correct query key for preferences

---

## Test Statistics

- **Total Test Files**: 6
- **Total Test Cases**: 186
- **Total Lines of Test Code**: ~3,074 (excluding mockData.ts)
- **Coverage Areas**:
  - Component Rendering
  - User Interactions
  - Form Validation
  - API Integration
  - State Management
  - Error Handling
  - Loading States
  - Empty States
  - Modal Interactions
  - Tab Navigation
  - Search & Filtering
  - Data Transformations
  - Cache Invalidation

## Running Tests

```bash
# Run all swap marketplace tests
npm test -- swap-marketplace

# Run specific test file
npm test -- SwapRequestCard.test.tsx

# Run with coverage
npm test -- --coverage swap-marketplace

# Run in watch mode
npm test -- --watch swap-marketplace
```

## Test Patterns Used

1. **React Testing Library** - User-centric testing approach
2. **Jest** - Test framework and assertions
3. **@tanstack/react-query** - Mocking data fetching hooks
4. **userEvent** - Simulating user interactions
5. **waitFor** - Handling asynchronous operations
6. **Mock Service Worker (conceptual)** - API mocking via jest.mock

## Key Testing Principles

- ✓ Test user behavior, not implementation details
- ✓ Use semantic queries (getByRole, getByLabelText)
- ✓ Test error states and edge cases
- ✓ Verify accessibility attributes
- ✓ Mock external dependencies
- ✓ Ensure proper cleanup between tests
- ✓ Test async operations with proper waiting
- ✓ Validate form submissions and mutations
- ✓ Check cache invalidation after mutations

## Coverage Goals

- [x] Swap request list rendering
- [x] Creating new swap requests
- [x] Accepting/rejecting swaps
- [x] Filtering by status
- [x] Search functionality
- [x] Modal interactions
- [x] Form validation
- [x] Date range filtering
- [x] Tab navigation
- [x] Empty states
- [x] Loading states
- [x] Error handling
- [x] API integration
- [x] Cache management
- [x] Responsive design
