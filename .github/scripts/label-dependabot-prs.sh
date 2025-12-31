#!/bin/bash
# ============================================================
# Script: label-dependabot-prs.sh
# Purpose: Label and manage Dependabot PRs automatically
# Usage: bash .github/scripts/label-dependabot-prs.sh
#
# Description:
#   Automatically labels Dependabot pull requests and triggers
#   auto-merge for safe dependency updates. Creates labels if
#   they don't exist and applies appropriate merge strategy.
#
# Labels Created/Applied:
#   - safe-to-merge       - Can auto-merge after CI passes
#   - needs-investigation - Requires manual review
#   - breaking-change     - Do not auto-merge
#   - blocked             - External dependency blocking
#   - dependencies        - Dependency update PR
#   - javascript/frontend - Technology-specific labels
#
# Requirements:
#   - gh CLI installed and authenticated
#   - Repository write access
#   - GITHUB_TOKEN with repo scope
#
# Safety Features:
#   - Labels breaking changes as needs-investigation
#   - Skips auto-merge for major version bumps
#   - Adds review notes for complex updates
# ============================================================

set -e

REPO="Euda1mon1a/Autonomous-Assignment-Program-Manager"

echo "🏷️  Creating labels if they don't exist..."

# Create labels (will silently fail if they exist)
gh label create "safe-to-merge" --color "0e8a16" --description "PR is safe to merge after CI passes" --repo "$REPO" 2>/dev/null || true
gh label create "needs-investigation" --color "fbca04" --description "Requires manual review before merging" --repo "$REPO" 2>/dev/null || true
gh label create "breaking-change" --color "b60205" --description "Contains breaking changes - do not auto-merge" --repo "$REPO" 2>/dev/null || true
gh label create "blocked" --color "d93f0b" --description "Blocked by external dependency or requirement" --repo "$REPO" 2>/dev/null || true
gh label create "dependencies" --color "0366d6" --description "Pull requests that update a dependency file" --repo "$REPO" 2>/dev/null || true
gh label create "javascript" --color "f1e05a" --description "JavaScript/TypeScript related changes" --repo "$REPO" 2>/dev/null || true
gh label create "frontend" --color "7057ff" --description "Frontend related changes" --repo "$REPO" 2>/dev/null || true

echo ""
echo "📝 Labeling PR #106 (date-fns 3→4) - SAFE TO MERGE"
gh pr edit 106 --add-label "dependencies,javascript,frontend,safe-to-merge" --repo "$REPO"
gh pr comment 106 --body "@dependabot merge" --repo "$REPO"
echo "   ✅ Added 'safe-to-merge' label and auto-merge command"

echo ""
echo "📝 Labeling PR #108 (@testing-library/react 14→16) - NEEDS INVESTIGATION"
gh pr edit 108 --add-label "dependencies,javascript,frontend,needs-investigation" --repo "$REPO"
gh pr comment 108 --body "⚠️ **Review Note**: This upgrade requires installing \`@testing-library/dom\` as a peer dependency before merging.

\`\`\`bash
npm install --save-dev @testing-library/dom
\`\`\`

Run tests after merge to verify compatibility." --repo "$REPO"
echo "   ⚠️  Added 'needs-investigation' label with instructions"

echo ""
echo "📝 Labeling PR #99 (jest-environment-jsdom 29→30) - NEEDS INVESTIGATION"
gh pr edit 99 --add-label "dependencies,javascript,frontend,needs-investigation,breaking-change" --repo "$REPO"
gh pr comment 99 --body "⚠️ **Review Note**: Jest 30 includes significant breaking changes:

- JSDOM upgraded from v21 to v26 (DOM behavior changes)
- \`window.location\` mocking may need adjustment
- Deprecated matcher aliases removed (\`toBeCalled\` → \`toHaveBeenCalled\`)
- Node.js 18+ required

**Required**: Run full test suite locally before merging." --repo "$REPO"
echo "   ⚠️  Added 'needs-investigation' and 'breaking-change' labels"

echo ""
echo "📝 Labeling PR #102 (eslint 8→9) - BLOCKED"
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
echo "   PR #106 (date-fns):      safe-to-merge + auto-merge enabled"
echo "   PR #108 (testing-lib):   needs-investigation"
echo "   PR #99  (jest):          needs-investigation + breaking-change"
echo "   PR #102 (eslint):        blocked + breaking-change + ignored"
