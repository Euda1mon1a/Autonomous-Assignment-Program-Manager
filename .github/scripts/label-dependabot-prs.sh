***REMOVED***!/bin/bash
***REMOVED*** ============================================================
***REMOVED*** Script: label-dependabot-prs.sh
***REMOVED*** Purpose: Label and manage Dependabot PRs automatically
***REMOVED*** Usage: bash .github/scripts/label-dependabot-prs.sh
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Automatically labels Dependabot pull requests and triggers
***REMOVED***   auto-merge for safe dependency updates. Creates labels if
***REMOVED***   they don't exist and applies appropriate merge strategy.
***REMOVED***
***REMOVED*** Labels Created/Applied:
***REMOVED***   - safe-to-merge       - Can auto-merge after CI passes
***REMOVED***   - needs-investigation - Requires manual review
***REMOVED***   - breaking-change     - Do not auto-merge
***REMOVED***   - blocked             - External dependency blocking
***REMOVED***   - dependencies        - Dependency update PR
***REMOVED***   - javascript/frontend - Technology-specific labels
***REMOVED***
***REMOVED*** Requirements:
***REMOVED***   - gh CLI installed and authenticated
***REMOVED***   - Repository write access
***REMOVED***   - GITHUB_TOKEN with repo scope
***REMOVED***
***REMOVED*** Safety Features:
***REMOVED***   - Labels breaking changes as needs-investigation
***REMOVED***   - Skips auto-merge for major version bumps
***REMOVED***   - Adds review notes for complex updates
***REMOVED*** ============================================================

set -euo pipefail

REPO="Euda1mon1a/Autonomous-Assignment-Program-Manager"

***REMOVED*** Verify gh CLI is installed and authenticated
if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: GitHub CLI (gh) not found" >&2
    echo "Install from: https://cli.github.com/" >&2
    exit 1
fi

***REMOVED*** Verify gh is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: GitHub CLI not authenticated" >&2
    echo "Run: gh auth login" >&2
    exit 1
fi

echo "🏷️  Creating labels if they don't exist..."

***REMOVED*** Create labels (will silently fail if they exist)
gh label create "safe-to-merge" --color "0e8a16" --description "PR is safe to merge after CI passes" --repo "$REPO" 2>/dev/null || true
gh label create "needs-investigation" --color "fbca04" --description "Requires manual review before merging" --repo "$REPO" 2>/dev/null || true
gh label create "breaking-change" --color "b60205" --description "Contains breaking changes - do not auto-merge" --repo "$REPO" 2>/dev/null || true
gh label create "blocked" --color "d93f0b" --description "Blocked by external dependency or requirement" --repo "$REPO" 2>/dev/null || true
gh label create "dependencies" --color "0366d6" --description "Pull requests that update a dependency file" --repo "$REPO" 2>/dev/null || true
gh label create "javascript" --color "f1e05a" --description "JavaScript/TypeScript related changes" --repo "$REPO" 2>/dev/null || true
gh label create "frontend" --color "7057ff" --description "Frontend related changes" --repo "$REPO" 2>/dev/null || true

echo ""
echo "📝 Labeling PR ***REMOVED***106 (date-fns 3→4) - SAFE TO MERGE"
gh pr edit 106 --add-label "dependencies,javascript,frontend,safe-to-merge" --repo "$REPO"
gh pr comment 106 --body "@dependabot merge" --repo "$REPO"
echo "   ✅ Added 'safe-to-merge' label and auto-merge command"

echo ""
echo "📝 Labeling PR ***REMOVED***108 (@testing-library/react 14→16) - NEEDS INVESTIGATION"
gh pr edit 108 --add-label "dependencies,javascript,frontend,needs-investigation" --repo "$REPO"
gh pr comment 108 --body "⚠️ **Review Note**: This upgrade requires installing \`@testing-library/dom\` as a peer dependency before merging.

\`\`\`bash
npm install --save-dev @testing-library/dom
\`\`\`

Run tests after merge to verify compatibility." --repo "$REPO"
echo "   ⚠️  Added 'needs-investigation' label with instructions"

echo ""
echo "📝 Labeling PR ***REMOVED***99 (jest-environment-jsdom 29→30) - NEEDS INVESTIGATION"
gh pr edit 99 --add-label "dependencies,javascript,frontend,needs-investigation,breaking-change" --repo "$REPO"
gh pr comment 99 --body "⚠️ **Review Note**: Jest 30 includes significant breaking changes:

- JSDOM upgraded from v21 to v26 (DOM behavior changes)
- \`window.location\` mocking may need adjustment
- Deprecated matcher aliases removed (\`toBeCalled\` → \`toHaveBeenCalled\`)
- Node.js 18+ required

**Required**: Run full test suite locally before merging." --repo "$REPO"
echo "   ⚠️  Added 'needs-investigation' and 'breaking-change' labels"

echo ""
echo "📝 Labeling PR ***REMOVED***102 (eslint 8→9) - BLOCKED"
gh pr edit 102 --add-label "dependencies,javascript,frontend,breaking-change,blocked" --repo "$REPO"
gh pr comment 102 --body "🚫 **BLOCKED**: Cannot merge this PR.

**Reason**: Next.js 14.x does not support ESLint 9. The \`next lint\` command will fail.

**Required before merging**:
1. Upgrade Next.js from 14.x to 15.x
2. Migrate ESLint config to flat config format
3. Update eslint-config-next to compatible version

See: https://github.com/vercel/next.js/issues/64409

@dependabot ignore this major version" --repo "$REPO"
echo "   🚫 Added 'blocked' label and told Dependabot to ignore this major version"

echo ""
echo "✅ Done! Summary:"
echo "   PR ***REMOVED***106 (date-fns):      safe-to-merge + auto-merge enabled"
echo "   PR ***REMOVED***108 (testing-lib):   needs-investigation"
echo "   PR ***REMOVED***99  (jest):          needs-investigation + breaking-change"
echo "   PR ***REMOVED***102 (eslint):        blocked + breaking-change + ignored"
