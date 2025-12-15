# File Ownership Matrix - Template Library Feature

## Territory: frontend/src/features/templates/*

### File Inventory

| File Path | Purpose | Dependencies | Owner |
|-----------|---------|--------------|-------|
| `index.ts` | Feature barrel export | All feature files | Template Library |
| `types.ts` | TypeScript type definitions | None | Template Library |
| `constants.ts` | Configuration and predefined data | `types.ts` | Template Library |
| `hooks.ts` | React Query hooks and state management | `types.ts`, `constants.ts`, `@tanstack/react-query` | Template Library |
| `components/index.ts` | Components barrel export | All component files | Template Library |
| `components/TemplateCard.tsx` | Template card display component | `types.ts`, `constants.ts`, `lucide-react` | Template Library |
| `components/TemplateSearch.tsx` | Search and filter component | `types.ts`, `constants.ts`, `lucide-react` | Template Library |
| `components/TemplateCategories.tsx` | Category filter component | `types.ts`, `constants.ts`, `lucide-react` | Template Library |
| `components/PatternEditor.tsx` | Assignment pattern editor | `types.ts`, `constants.ts`, `lucide-react` | Template Library |
| `components/TemplateEditor.tsx` | Template create/edit form | `types.ts`, `constants.ts`, `hooks.ts`, `PatternEditor.tsx`, `lucide-react` | Template Library |
| `components/TemplatePreview.tsx` | Template preview modal | `types.ts`, `constants.ts`, `lucide-react` | Template Library |
| `components/TemplateShareModal.tsx` | Share and duplicate modal | `types.ts`, `constants.ts`, `lucide-react` | Template Library |
| `components/TemplateList.tsx` | Template list/grid view | `types.ts`, `TemplateCard.tsx`, `lucide-react` | Template Library |
| `components/TemplateLibrary.tsx` | Main library component | All components, `hooks.ts`, `types.ts` | Template Library |

### Feature Summary

**Total Files**: 14
**Components**: 9
**Hooks**: 1 (with multiple exports)
**Types**: 1
**Constants**: 1
**Index/Exports**: 2

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^18.x | Core React |
| `@tanstack/react-query` | ^5.x | Data fetching and caching |
| `lucide-react` | ^0.x | Icons |

### Integration Points

1. **Data Storage**: Uses localStorage for demo (can be replaced with API calls)
2. **Query Keys**: Exports `templateQueryKeys` for cache invalidation
3. **Main Component**: `TemplateLibrary` is the primary entry point
4. **Types**: All types exported for external use

### Usage Example

```tsx
// In app/templates/page.tsx or similar
import { TemplateLibrary } from '@/features/templates';

export default function TemplatesLibraryPage() {
  const handleTemplateApplied = (result: { success: boolean; message: string }) => {
    // Handle template application result
    console.log(result);
  };

  return (
    <TemplateLibrary onTemplateApplied={handleTemplateApplied} />
  );
}
```

### Component Hierarchy

```
TemplateLibrary
├── TemplateSearch
├── TemplateCategories
├── TemplateList
│   └── TemplateCard (multiple)
├── TemplateEditor (modal)
│   └── PatternEditor
├── TemplatePreview (modal)
├── TemplateShareModal (modal)
└── PredefinedTemplateCard (multiple)
```

### API/Hook Exports

| Hook | Purpose | Returns |
|------|---------|---------|
| `useTemplates` | Fetch templates with filters | Query result with template list |
| `useTemplate` | Fetch single template | Query result with template |
| `usePredefinedTemplates` | Fetch system templates | Query result with predefined list |
| `useTemplateStatistics` | Fetch usage statistics | Query result with stats |
| `useCreateTemplate` | Create new template | Mutation |
| `useUpdateTemplate` | Update existing template | Mutation |
| `useDeleteTemplate` | Delete template | Mutation |
| `useDuplicateTemplate` | Duplicate template | Mutation |
| `useShareTemplate` | Update sharing settings | Mutation |
| `useApplyTemplate` | Apply template to schedule | Mutation |
| `useImportPredefinedTemplate` | Import system template | Mutation |
| `useTemplateFilters` | Filter state management | Filter state + handlers |
| `usePatternEditor` | Pattern editing state | Pattern state + handlers |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-15 | Initial implementation |
