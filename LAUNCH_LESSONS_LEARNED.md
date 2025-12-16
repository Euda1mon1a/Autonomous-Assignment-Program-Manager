# Launch Lessons Learned

Documentation of issues encountered while launching the Autonomous Assignment Program Manager on macOS, with recommendations for preventing similar issues.

## Table of Contents
- [1. Dependabot + Frontend = Danger](#1-dependabot--frontend--danger)
- [2. TypeScript Strict Mode Gotchas](#2-typescript-strict-mode-gotchas)
- [3. Docker Build Issues](#3-docker-build-issues)
- [4. Frontend/Backend Schema Drift](#4-frontendbackend-schema-drift)
- [5. Process Improvements](#5-process-improvements)
- [Recommended Next Steps](#recommended-next-steps)

---

## 1. Dependabot + Frontend = Danger

### Problem
Tailwind CSS v4 is a complete rewrite with breaking CSS syntax changes. Auto-merging frontend dependency updates without testing broke builds.

### Root Cause
- Dependabot auto-merge was enabled for minor/patch updates
- Frontend framework updates (Tailwind, Next.js ecosystem) often have breaking changes even in minor versions
- No build verification step before auto-merge

### Recommendation
**Option A: Pin critical frontend dependencies**
```json
{
  "dependencies": {
    "tailwindcss": "3.4.1"  // Exact version, no caret
  }
}
```

**Option B: Disable Dependabot for `/frontend`**
Remove the npm package ecosystem entry from `.github/dependabot.yml`

**Option C (Recommended): Add frontend ignore rules**
Add to `.github/dependabot.yml`:
```yaml
ignore:
  - dependency-name: "tailwindcss"
    update-types: ["version-update:semver-major", "version-update:semver-minor"]
  - dependency-name: "postcss"
    update-types: ["version-update:semver-major"]
  - dependency-name: "autoprefixer"
    update-types: ["version-update:semver-major"]
```

---

## 2. TypeScript Strict Mode Gotchas

### Problem 1: Set iteration fails
```typescript
// FAILS without downlevelIteration
const unique = [...new Set(items)];

// WORKS
const unique = Array.from(new Set(items));
```

**Fix:** Either enable `downlevelIteration` in `tsconfig.json` or use `Array.from()`.

### Problem 2: Naming conflicts
```typescript
// BUG: parameter shadows import
import { format } from 'date-fns';

function formatDate(date: Date, format: string) {  // 'format' shadows import!
  return format(date, format);  // Calls parameter, not function
}

// FIX: Rename parameter
function formatDate(date: Date, formatStr: string) {
  return format(date, formatStr);
}
```

### Problem 3: Type casting
```typescript
// Sometimes fails
const value = someValue as TargetType;

// May need double-cast
const value = someValue as unknown as TargetType;
```

**Recommendation:** Enable `noImplicitAny` and stricter ESLint rules to catch these at lint time.

---

## 3. Docker Build Issues

### Problem 1: Missing devDependencies
```dockerfile
# FAILS - skips TypeScript, build tools
RUN npm ci --only=production

# WORKS - install all, then build
RUN npm ci
RUN npm run build
```

### Problem 2: Peer dependency conflicts
```dockerfile
# Add when peer dependency conflicts exist
RUN npm ci --legacy-peer-deps
```

### Recommended Dockerfile Pattern
```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
CMD ["node", "server.js"]
```

---

## 4. Frontend/Backend Schema Drift

### Problem
API types get out of sync between frontend and backend, causing runtime errors.

### Examples
- Algorithm options enum mismatches
- Request/response field changes
- Optional vs required field differences

### Recommendations

**Short-term:** Manual sync checklist
- [ ] Update backend schema
- [ ] Update frontend types
- [ ] Update API documentation
- [ ] Test both ends

**Long-term:** Generate frontend types from backend

**IMPLEMENTED:** Type generation from OpenAPI spec
```bash
# Export OpenAPI spec from backend (run from backend/)
python scripts/export_openapi.py

# Generate TypeScript types (run from frontend/)
npm run generate:types       # From running backend
npm run generate:types:file  # From exported openapi.json
```

The generated types are saved to `frontend/src/types/generated-api.ts`.

---

## 5. Process Improvements

### Pre-merge Checklist
- [ ] Test builds locally before merging dependency updates
- [ ] Run `npm run build` for frontend changes
- [ ] Run `pytest` for backend changes
- [ ] Test Docker builds: `docker compose build`

### CI Enhancements
1. **Add frontend build to CI** (already present in current ci.yml)
2. **Add Docker build verification**
3. **Consider staging branch for dependency updates**

### Dependency Update Workflow
```
dependabot PR → CI runs → build test → manual review → merge
                ↓
            Auto-merge ONLY for:
            - Backend patch updates
            - GitHub Actions updates
            - Security fixes
```

---

## Recommended Next Steps

### Immediate Actions

1. **Update Dependabot Configuration**
   - Add ignore rules for Tailwind, PostCSS major/minor updates
   - Disable auto-merge for frontend dependencies
   - Keep auto-merge for backend patch updates only

2. **Add Docker Build to CI**
   ```yaml
   docker-build-test:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v6
       - run: docker compose build --no-cache
   ```

3. **Pin Critical Frontend Dependencies**
   - Lock Tailwind to 3.x
   - Lock PostCSS to 8.x
   - Lock autoprefixer to current version

### Medium-term Actions

4. **Generate Frontend Types from Backend**
   - Add OpenAPI spec export to backend
   - Set up type generation script
   - Add to CI to catch drift

5. **Create Staging Branch**
   - Route all dependency updates to `staging`
   - Weekly manual merge to `main` after testing

6. **Add Pre-commit Hooks**
   - Type checking
   - Lint
   - Build verification for frontend changes

### Future Considerations

7. **Monorepo with Shared Types**
   - Consider migrating to Nx or Turborepo
   - Share type definitions between frontend/backend

8. **Contract Testing**
   - Add Pact or similar for API contract testing
   - Catch schema drift before deployment

---

## Quick Reference Commands

```bash
# Test frontend build locally
cd frontend && npm run build

# Test Docker build
docker compose build --no-cache

# Check for TypeScript errors
cd frontend && npx tsc --noEmit

# Run all tests
cd backend && pytest
cd frontend && npm test

# Update dependencies safely
npm update --save  # Updates within semver range
npm outdated       # See what needs updating
```

---

*Last updated: December 2024*
*Document created from launch experience on macOS*
