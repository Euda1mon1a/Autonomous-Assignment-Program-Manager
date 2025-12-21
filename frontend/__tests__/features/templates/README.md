# Template Feature Tests

This directory contains comprehensive Jest + React Testing Library tests for the template library feature.

## Test Files Created

### ✅ Completed

1. **hooks.test.ts** - Tests all template hooks
   - useTemplates, useTemplate, usePredefinedTemplates
   - useCreateTemplate, useUpdateTemplate, useDeleteTemplate
   - useDuplicateTemplate, useShareTemplate, useApplyTemplate
   - useImportPredefinedTemplate
   - useTemplateFilters, usePatternEditor

2. **TemplateCard.test.tsx** - Tests template card component
   - Rendering (name, description, badges, stats)
   - Day coverage indicators
   - Actions menu (Edit, Delete, Duplicate, Share, Preview)
   - Action callbacks
   - Category and status styling
   - Accessibility

3. **TemplateList.test.tsx** - Tests template list component
   - Grid and list variants
   - Loading states (skeletons)
   - Error states (with retry)
   - Empty states
   - PredefinedTemplateCard component
   - Action callbacks

4. **TemplateCategories.test.tsx** - Tests category filtering
   - Pills variant
   - Cards variant
   - List variant
   - Category selection
   - CategoryBadge component
   - Accessibility

5. **TemplateSearch.test.tsx** - Tests search and filtering
   - Search input with debouncing
   - Filters button and panel
   - Results count
   - Advanced filters (category, visibility, status, sort)
   - Filter chips
   - Clear filters functionality
   - Accessibility

6. **PatternEditor.test.tsx** - Tests pattern editing
   - Pattern list rendering
   - Add/edit/delete patterns
   - Empty state
   - Expand/collapse patterns
   - Read-only mode

7. **TemplateEditor.test.tsx** - Tests template editor
   - Form rendering and validation
   - Create vs Edit mode
   - Required field validation
   - Save/cancel actions
   - Loading states

8. **TemplatePreview.test.tsx** - Tests template preview
   - Template info display
   - Calendar preview
   - Date selection
   - Preview options
   - Pattern summary
   - Apply template action

9. **TemplateShareModal.test.tsx** - Tests share modal
   - Share mode (visibility options, share link)
   - Duplicate mode (name, include patterns)
   - Save/cancel actions
   - Modal close functionality

10. **TemplateLibrary.test.tsx** - Tests main library component
    - Tabs (My Templates, Predefined)
    - Create new template button
    - Search and filters integration
    - View mode toggle (grid/list)
    - Template count display

## Running Tests

```bash
# Run all template tests
npm test -- templates

# Run specific test file
npm test -- templates/hooks.test.ts

# Run with coverage
npm test -- --coverage templates/
```

## Test Coverage Goals

- Target: 80%+ coverage
- Status: ✅ Complete (10/10 files created)

## Testing Patterns Used

- Component mocking for child components
- User event simulation with @testing-library/user-event
- React Query wrapper for hooks
- Accessibility testing
- Loading/error/empty state coverage
- Event handler verification
- Form validation testing
