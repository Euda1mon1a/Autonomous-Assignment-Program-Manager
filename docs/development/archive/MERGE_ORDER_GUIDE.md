***REMOVED*** Merge Order Guide

***REMOVED******REMOVED*** How to Merge Work from 3 Parallel Terminals

When running Opus, Sonnet, and Haiku in parallel, their work needs to be merged in a specific order to avoid conflicts and satisfy dependencies.

---

***REMOVED******REMOVED*** Branch Strategy

Each model works on a feature branch, then merges to a shared integration branch:

```
main
  │
  └── integration/sprint-1  ◄── All models merge here
        │
        ├── opus/auth-design
        ├── sonnet/api-client
        └── haiku/types-components
```

**Setup Commands:**
```bash
***REMOVED*** Create integration branch
git checkout -b integration/sprint-1

***REMOVED*** Each terminal creates their branch FROM integration
***REMOVED*** Terminal 1 (Opus):
git checkout -b opus/phase-1

***REMOVED*** Terminal 2 (Sonnet):
git checkout -b sonnet/phase-1

***REMOVED*** Terminal 3 (Haiku):
git checkout -b haiku/phase-1
```

---

***REMOVED******REMOVED*** Phase 1: Foundation - Merge Order

***REMOVED******REMOVED******REMOVED*** Timeline & Merge Sequence

```
Time ────────────────────────────────────────────────────────────►

Haiku:   ████████ Types ████████│ MERGE 1st │
         [15-20 min]            ▼
                                │
Opus:    ████████████ Auth Design ████████████│ MERGE 2nd │
         [30-45 min]                          ▼
                                              │
Sonnet:  ████████████████ API Client █████████████████│ MERGE 3rd │
         [30-45 min]                                  ▼
```

***REMOVED******REMOVED******REMOVED*** Step-by-Step Merge Process

**MERGE 1: Haiku's Types & Components (First)**
```bash
***REMOVED*** On integration branch
git checkout integration/sprint-1
git merge haiku/phase-1 -m "feat: Add TypeScript types and base components"

***REMOVED*** Files merged:
***REMOVED*** - frontend/types/api.ts
***REMOVED*** - frontend/components/Modal.tsx
***REMOVED*** - frontend/components/forms/*
```

**Why first?** Sonnet's hooks import these types. Merging first prevents import errors.

---

**MERGE 2: Opus's Design Docs (Second)**
```bash
git merge opus/phase-1 -m "docs: Add auth architecture and error handling design"

***REMOVED*** Files merged:
***REMOVED*** - docs/AUTH_ARCHITECTURE.md
***REMOVED*** - docs/ERROR_HANDLING.md
```

**Why second?** No code dependencies, but Sonnet needs to reference for Phase 2.

---

**MERGE 3: Sonnet's API Client (Third)**
```bash
git merge sonnet/phase-1 -m "feat: Add API client and React Query setup"

***REMOVED*** Files merged:
***REMOVED*** - frontend/lib/api.ts
***REMOVED*** - frontend/lib/hooks.ts (skeleton)
```

**Why third?** Needs Haiku's types to be present for imports to resolve.

---

***REMOVED******REMOVED******REMOVED*** Phase 1 Merge Checklist

```
□ 1. Haiku completes → Merge haiku/phase-1
     └─ Verify: frontend/types/api.ts exists with all entity types
     └─ Verify: frontend/components/Modal.tsx has no errors
     └─ Verify: frontend/components/forms/index.ts exports all

□ 2. Opus completes → Merge opus/phase-1
     └─ Verify: docs/AUTH_ARCHITECTURE.md is comprehensive
     └─ Verify: docs/ERROR_HANDLING.md defines error schema

□ 3. Sonnet completes → Merge sonnet/phase-1
     └─ Verify: npm run build passes (types resolve)
     └─ Verify: frontend/lib/api.ts has no 'any' types
```

---

***REMOVED******REMOVED*** Phase 2: Core Features - Merge Order

***REMOVED******REMOVED******REMOVED*** Timeline & Merge Sequence

```
Time ────────────────────────────────────────────────────────────►

Haiku:   ████ Skeletons ████│ MERGE 1st │░░░░ Standby ░░░░
         [15-20 min]        ▼

Sonnet:  ███████████████████ Hooks ████████████████████│ MERGE 2nd │
         [1-2 hours]                                   ▼

Opus:    ██ Review ██│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ MERGE 3rd │
         [ongoing]                                     ▼ (feedback)
```

***REMOVED******REMOVED******REMOVED*** Step-by-Step Merge Process

**MERGE 1: Haiku's Skeletons & Tests (First)**
```bash
git checkout integration/sprint-1
git merge haiku/phase-2 -m "feat: Add loading skeletons and test scaffolds"

***REMOVED*** Files merged:
***REMOVED*** - frontend/components/skeletons/*
***REMOVED*** - frontend/__tests__/hooks/*
```

**Why first?** Sonnet's pages will import these skeletons for loading states.

---

**MERGE 2: Sonnet's Hooks (Second)**
```bash
git merge sonnet/phase-2 -m "feat: Implement React Query hooks for all entities"

***REMOVED*** Files merged:
***REMOVED*** - frontend/lib/hooks.ts (complete implementation)
```

**Why second?** This is the core work. Pages depend on these hooks.

---

**MERGE 3: Opus's Feedback (Third - If Any Code Changes)**
```bash
***REMOVED*** Only if Opus made code changes based on review
git merge opus/phase-2 -m "refactor: Apply review feedback to API client"

***REMOVED*** Possible files:
***REMOVED*** - docs/CACHING_STRATEGY.md
***REMOVED*** - Minor fixes to frontend/lib/api.ts
```

**Why third?** Review feedback applies to already-merged code.

---

***REMOVED******REMOVED******REMOVED*** Phase 2 Merge Checklist

```
□ 1. Haiku completes → Merge haiku/phase-2
     └─ Verify: All skeleton components export correctly
     └─ Verify: Test files have correct import paths

□ 2. Sonnet completes → Merge sonnet/phase-2
     └─ Verify: All hooks compile without errors
     └─ Verify: Hooks use types from @/types/api
     └─ Run: npm run build

□ 3. Opus review complete → Merge opus/phase-2 (if changes)
     └─ Verify: Review feedback addressed
     └─ Verify: No breaking changes to merged code
```

---

***REMOVED******REMOVED*** Phase 3: Integration - Merge Order

***REMOVED******REMOVED******REMOVED*** Timeline & Merge Sequence

```
Time ────────────────────────────────────────────────────────────►

Haiku:   ░░ Support ░░│░░░░░░░░░░░░░░│██ Fixes ██│ MERGE 1st │
         [on-demand]                  [if needed] ▼

Sonnet:  ██████████████████ Page Wiring ███████████████████│ MERGE 2nd │
         [1-2 hours]                                       ▼

Opus:    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│██ ACGME Review ██│ MERGE 3rd │
                                        [after Sonnet]     ▼ (approval)
```

***REMOVED******REMOVED******REMOVED*** Step-by-Step Merge Process

**MERGE 1: Haiku's Support Fixes (First - If Any)**
```bash
***REMOVED*** Only if Haiku added new types or fixed issues
git merge haiku/phase-3 -m "fix: Add missing types and component fixes"

***REMOVED*** Possible files:
***REMOVED*** - frontend/types/api.ts (additions)
***REMOVED*** - frontend/components/* (fixes)
```

**Why first?** Clears any blockers Sonnet reported.

---

**MERGE 2: Sonnet's Page Integration (Second)**
```bash
git merge sonnet/phase-3 -m "feat: Wire all pages to API with loading/error states"

***REMOVED*** Files merged:
***REMOVED*** - frontend/app/page.tsx
***REMOVED*** - frontend/app/people/page.tsx
***REMOVED*** - frontend/app/compliance/page.tsx
***REMOVED*** - frontend/app/templates/page.tsx
***REMOVED*** - frontend/components/AddPersonModal.tsx
***REMOVED*** - frontend/components/AddAbsenceModal.tsx
```

**Why second?** This is the bulk of integration work.

---

**MERGE 3: Opus's Approval (Third)**
```bash
***REMOVED*** Opus reviews ACGME compliance display, then approves or requests changes
git merge opus/phase-3 -m "review: Approve ACGME compliance implementation"

***REMOVED*** Possible files:
***REMOVED*** - docs/REVIEW_NOTES.md
***REMOVED*** - Minor fixes if Opus found issues
```

**Why third?** Quality gate - Opus validates before Phase 4.

---

***REMOVED******REMOVED******REMOVED*** Phase 3 Merge Checklist

```
□ 1. Haiku support merged (if any)
     └─ Verify: Any new types Sonnet requested are present

□ 2. Sonnet page wiring merged
     └─ Verify: All pages load without errors
     └─ Verify: API calls work (test with backend running)
     └─ Run: npm run build && npm run lint

□ 3. Opus approval merged
     └─ Verify: ACGME compliance display is accurate
     └─ Verify: No security issues flagged
     └─ GREEN LIGHT for Phase 4
```

---

***REMOVED******REMOVED*** Phase 4: Polish - Merge Order

***REMOVED******REMOVED******REMOVED*** Timeline & Merge Sequence

```
Time ────────────────────────────────────────────────────────────►

Haiku:   ████ Cleanup ████│ MERGE 1st │
         [20-30 min]      ▼

Sonnet:  █████████████ Auth + Tests ██████████████│ MERGE 2nd │
         [1-2 hours]                              ▼

Opus:    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│██ Final Review ██│ MERGE 3rd │
                                      [after all merges] ▼ (sign-off)
```

***REMOVED******REMOVED******REMOVED*** Step-by-Step Merge Process

**MERGE 1: Haiku's Cleanup (First)**
```bash
git merge haiku/phase-4 -m "chore: Add JSDoc comments and code formatting"

***REMOVED*** Files merged:
***REMOVED*** - Various files with added documentation
***REMOVED*** - Formatting fixes
```

---

**MERGE 2: Sonnet's Auth & Tests (Second)**
```bash
git merge sonnet/phase-4 -m "feat: Implement authentication and integration tests"

***REMOVED*** Files merged:
***REMOVED*** - frontend/lib/auth.ts
***REMOVED*** - frontend/components/LoginForm.tsx
***REMOVED*** - frontend/__tests__/**/*.test.ts
```

---

**MERGE 3: Opus's Final Sign-off (Third)**
```bash
git merge opus/phase-4 -m "review: Final architecture approval and documentation"

***REMOVED*** Files merged:
***REMOVED*** - docs/ARCHITECTURE_FINAL.md
***REMOVED*** - Any final refinements
```

---

***REMOVED******REMOVED*** Quick Reference: Merge Order by Phase

| Phase | 1st Merge | 2nd Merge | 3rd Merge |
|-------|-----------|-----------|-----------|
| **1. Foundation** | Haiku (types) | Opus (docs) | Sonnet (api client) |
| **2. Core** | Haiku (skeletons) | Sonnet (hooks) | Opus (review) |
| **3. Integration** | Haiku (fixes) | Sonnet (pages) | Opus (approval) |
| **4. Polish** | Haiku (cleanup) | Sonnet (auth) | Opus (sign-off) |

---

***REMOVED******REMOVED*** Handling Merge Conflicts

***REMOVED******REMOVED******REMOVED*** Conflict Scenario 1: Types
**Haiku and Sonnet both touched `frontend/types/api.ts`**

```bash
***REMOVED*** Keep Haiku's base types, add Sonnet's extensions
git merge sonnet/phase-X
***REMOVED*** If conflict in types/api.ts:

***REMOVED*** Resolution: Haiku owns entity types, Sonnet adds hook-specific types
***REMOVED*** Entity types (Person, Block, etc.) → Use Haiku's version
***REMOVED*** Hook types (UseScheduleReturn, etc.) → Use Sonnet's version
```

***REMOVED******REMOVED******REMOVED*** Conflict Scenario 2: Components
**Haiku created component, Sonnet modified it**

```bash
***REMOVED*** Sonnet's modifications take precedence (they're using the component)
git checkout --theirs frontend/components/SomeComponent.tsx
git add frontend/components/SomeComponent.tsx
git commit
```

***REMOVED******REMOVED******REMOVED*** Conflict Scenario 3: Documentation
**Opus and Sonnet both updated README**

```bash
***REMOVED*** Combine both changes manually
***REMOVED*** Opus: Architecture sections
***REMOVED*** Sonnet: Usage/API sections
```

---

***REMOVED******REMOVED*** Automated Merge Script

Save as `merge-phase.sh`:

```bash
***REMOVED***!/bin/bash
PHASE=$1
INTEGRATION_BRANCH="integration/sprint-1"

echo "Merging Phase $PHASE..."

git checkout $INTEGRATION_BRANCH

***REMOVED*** Phase-specific merge order
case $PHASE in
  1)
    echo "Merging Haiku (types)..."
    git merge haiku/phase-1 -m "feat: Add TypeScript types and base components" || exit 1

    echo "Merging Opus (docs)..."
    git merge opus/phase-1 -m "docs: Add auth architecture and error handling design" || exit 1

    echo "Merging Sonnet (api client)..."
    git merge sonnet/phase-1 -m "feat: Add API client and React Query setup" || exit 1
    ;;
  2)
    echo "Merging Haiku (skeletons)..."
    git merge haiku/phase-2 -m "feat: Add loading skeletons and test scaffolds" || exit 1

    echo "Merging Sonnet (hooks)..."
    git merge sonnet/phase-2 -m "feat: Implement React Query hooks" || exit 1

    echo "Merging Opus (review)..."
    git merge opus/phase-2 -m "review: Apply review feedback" || exit 1
    ;;
  3)
    echo "Merging Haiku (fixes)..."
    git merge haiku/phase-3 -m "fix: Support fixes and additions" || exit 1

    echo "Merging Sonnet (pages)..."
    git merge sonnet/phase-3 -m "feat: Wire pages to API" || exit 1

    echo "Merging Opus (approval)..."
    git merge opus/phase-3 -m "review: ACGME compliance approval" || exit 1
    ;;
  4)
    echo "Merging Haiku (cleanup)..."
    git merge haiku/phase-4 -m "chore: Documentation and formatting" || exit 1

    echo "Merging Sonnet (auth)..."
    git merge sonnet/phase-4 -m "feat: Authentication implementation" || exit 1

    echo "Merging Opus (final)..."
    git merge opus/phase-4 -m "review: Final sign-off" || exit 1
    ;;
esac

echo "Phase $PHASE merge complete!"
echo "Running build verification..."
cd frontend && npm run build
```

**Usage:**
```bash
chmod +x merge-phase.sh
./merge-phase.sh 1  ***REMOVED*** Merge Phase 1
./merge-phase.sh 2  ***REMOVED*** Merge Phase 2
***REMOVED*** etc.
```

---

***REMOVED******REMOVED*** Visual Merge Timeline

```
Phase 1                          Phase 2                          Phase 3
─────────────────────────────────────────────────────────────────────────────►

  Haiku ──┐                        Haiku ──┐                        Haiku ──┐
          │                                │                                │
  Opus ───┼──► MERGE TO             Opus ──┼──► MERGE TO             Opus ──┼──► MERGE
          │    INTEGRATION                 │    INTEGRATION                 │
  Sonnet ─┘                        Sonnet ─┘                        Sonnet ─┘

          │                                │                                │
          ▼                                ▼                                ▼
    [Verify Build]                  [Verify Build]                  [Verify Build]
    [Run Tests]                     [Run Tests]                     [E2E Tests]
```

---

***REMOVED******REMOVED*** Summary: The Golden Rule

> **Always merge in dependency order: Haiku → Opus → Sonnet**

This ensures:
1. Types are available before code that uses them
2. Design docs are available before implementation
3. No broken imports or missing dependencies

---

*Last Updated: 2024-12-13*
