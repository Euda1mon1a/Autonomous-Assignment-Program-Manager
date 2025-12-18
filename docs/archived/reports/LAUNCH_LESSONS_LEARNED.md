***REMOVED*** Launch Lessons Learned

Documentation of issues encountered while launching the Autonomous Assignment Program Manager on macOS, with recommendations for preventing similar issues.

***REMOVED******REMOVED*** Table of Contents
- [1. Dependabot + Frontend = Danger](***REMOVED***1-dependabot--frontend--danger)
- [2. TypeScript Strict Mode Gotchas](***REMOVED***2-typescript-strict-mode-gotchas)
- [3. Docker Build Issues](***REMOVED***3-docker-build-issues)
- [4. Frontend/Backend Schema Drift](***REMOVED***4-frontendbackend-schema-drift)
- [5. Process Improvements](***REMOVED***5-process-improvements)
- [Recommended Next Steps](***REMOVED***recommended-next-steps)

---

***REMOVED******REMOVED*** 1. Dependabot + Frontend = Danger

***REMOVED******REMOVED******REMOVED*** Problem
Tailwind CSS v4 is a complete rewrite with breaking CSS syntax changes. Auto-merging frontend dependency updates without testing broke builds.

***REMOVED******REMOVED******REMOVED*** Root Cause
- Dependabot auto-merge was enabled for minor/patch updates
- Frontend framework updates (Tailwind, Next.js ecosystem) often have breaking changes even in minor versions
- No build verification step before auto-merge

***REMOVED******REMOVED******REMOVED*** Recommendation
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

***REMOVED******REMOVED*** 2. TypeScript Strict Mode Gotchas

***REMOVED******REMOVED******REMOVED*** Problem 1: Set iteration fails
```typescript
// FAILS without downlevelIteration
const unique = [...new Set(items)];

// WORKS
const unique = Array.from(new Set(items));
```

**Fix:** Either enable `downlevelIteration` in `tsconfig.json` or use `Array.from()`.

***REMOVED******REMOVED******REMOVED*** Problem 2: Naming conflicts
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

***REMOVED******REMOVED******REMOVED*** Problem 3: Type casting
```typescript
// Sometimes fails
const value = someValue as TargetType;

// May need double-cast
const value = someValue as unknown as TargetType;
```

**Recommendation:** Enable `noImplicitAny` and stricter ESLint rules to catch these at lint time.

---

***REMOVED******REMOVED*** 3. Docker Build Issues

***REMOVED******REMOVED******REMOVED*** Problem 1: Missing devDependencies
```dockerfile
***REMOVED*** FAILS - skips TypeScript, build tools
RUN npm ci --only=production

***REMOVED*** WORKS - install all, then build
RUN npm ci
RUN npm run build
```

***REMOVED******REMOVED******REMOVED*** Problem 2: Peer dependency conflicts
```dockerfile
***REMOVED*** Add when peer dependency conflicts exist
RUN npm ci --legacy-peer-deps
```

***REMOVED******REMOVED******REMOVED*** Recommended Dockerfile Pattern
```dockerfile
***REMOVED*** Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

***REMOVED*** Production stage
FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
CMD ["node", "server.js"]
```

---

***REMOVED******REMOVED*** 4. Frontend/Backend Schema Drift

***REMOVED******REMOVED******REMOVED*** Problem
API types get out of sync between frontend and backend, causing runtime errors.

***REMOVED******REMOVED******REMOVED*** Examples
- Algorithm options enum mismatches
- Request/response field changes
- Optional vs required field differences

***REMOVED******REMOVED******REMOVED*** Recommendations

**Short-term:** Manual sync checklist
- [ ] Update backend schema
- [ ] Update frontend types
- [ ] Update API documentation
- [ ] Test both ends

**Long-term:** Generate frontend types from backend

**IMPLEMENTED:** Type generation from OpenAPI spec
```bash
***REMOVED*** Export OpenAPI spec from backend (run from backend/)
python scripts/export_openapi.py

***REMOVED*** Generate TypeScript types (run from frontend/)
npm run generate:types       ***REMOVED*** From running backend
npm run generate:types:file  ***REMOVED*** From exported openapi.json
```

The generated types are saved to `frontend/src/types/generated-api.ts`.

---

***REMOVED******REMOVED*** 5. Process Improvements

***REMOVED******REMOVED******REMOVED*** Pre-merge Checklist
- [ ] Test builds locally before merging dependency updates
- [ ] Run `npm run build` for frontend changes
- [ ] Run `pytest` for backend changes
- [ ] Test Docker builds: `docker compose build`

***REMOVED******REMOVED******REMOVED*** CI Enhancements
1. **Add frontend build to CI** (already present in current ci.yml)
2. **Add Docker build verification**
3. **Consider staging branch for dependency updates**

***REMOVED******REMOVED******REMOVED*** Dependency Update Workflow
```
dependabot PR → CI runs → build test → manual review → merge
                ↓
            Auto-merge ONLY for:
            - Backend patch updates
            - GitHub Actions updates
            - Security fixes
```

---

***REMOVED******REMOVED*** Recommended Next Steps

***REMOVED******REMOVED******REMOVED*** Immediate Actions

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

***REMOVED******REMOVED******REMOVED*** Medium-term Actions

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

***REMOVED******REMOVED******REMOVED*** Future Considerations

7. **Monorepo with Shared Types**
   - Consider migrating to Nx or Turborepo
   - Share type definitions between frontend/backend

8. **Contract Testing**
   - Add Pact or similar for API contract testing
   - Catch schema drift before deployment

---

***REMOVED******REMOVED*** Quick Reference Commands

```bash
***REMOVED*** Test frontend build locally
cd frontend && npm run build

***REMOVED*** Test Docker build
docker compose build --no-cache

***REMOVED*** Check for TypeScript errors
cd frontend && npx tsc --noEmit

***REMOVED*** Run all tests
cd backend && pytest
cd frontend && npm test

***REMOVED*** Update dependencies safely
npm update --save  ***REMOVED*** Updates within semver range
npm outdated       ***REMOVED*** See what needs updating
```

---

*Last updated: December 2024*
*Document created from launch experience on macOS*
