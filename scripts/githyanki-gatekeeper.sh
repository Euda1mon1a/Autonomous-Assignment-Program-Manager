#!/usr/bin/env bash
# ============================================================================
# GITHYANKI GATEKEEPER - Blocks dangerous pushes to main/master
# ============================================================================
#
# Named after D&D's Githyanki - astral warriors who guard their fortresses
# with legendary vigilance. They never allow unauthorized entry to their
# sacred strongholds, just as this hook protects main/master from direct
# and force pushes.
#
# The Gatekeeper's duty: Main branches are sacred. All changes must enter
# through the Pull Request ritual. Direct pushes bypass review and force
# pushes rewrite history - both are forbidden by the Githyanki code.
#
# What this hook blocks:
#   - Force push to main/master (rewrites history)
#   - Direct push to main/master (bypasses PR review)
#
# Emergency bypass: GITHYANKI_BYPASS=1 (use with extreme caution)
#
# See CLAUDE.md "AI Rules of Engagement - Core Policy" for PR workflow.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Check for emergency bypass
if [ "${GITHYANKI_BYPASS:-0}" = "1" ]; then
  echo -e "${RED}⚠️  WARNING: GITHYANKI GATEKEEPER BYPASSED ⚠️${NC}"
  echo -e "${YELLOW}This should only be used in emergency situations!${NC}"
  echo -e "${YELLOW}Proceeding with push...${NC}"
  exit 0
fi

echo -e "${MAGENTA}Githyanki Gatekeeper: Inspecting push targets...${NC}"

# Pre-push hook receives remote name and URL as args
remote_name="${1:-}"
remote_url="${2:-}"

# Parse stdin for push details
# Format: <local_ref> <local_sha> <remote_ref> <remote_sha>
while read local_ref local_sha remote_ref remote_sha; do
  # Skip deleted refs (all zeros)
  if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
    continue
  fi

  # Extract branch name from ref (refs/heads/branch-name -> branch-name)
  if [[ "$remote_ref" =~ ^refs/heads/(.*)$ ]]; then
    branch="${BASH_REMATCH[1]}"
  else
    # Not a branch push, allow it
    continue
  fi

  # Check if pushing to protected branch
  if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then

    # Check for force push attempt
    # A force push is when remote_sha is not an ancestor of local_sha
    # (or remote_sha is 0000... for new branches)
    if [ "$remote_sha" != "0000000000000000000000000000000000000000" ]; then
      # Remote branch exists - check if this would be a fast-forward
      if ! git merge-base --is-ancestor "$remote_sha" "$local_sha" 2>/dev/null; then
        # Not a fast-forward = force push attempt
        echo -e "${RED}BLOCKED! Force push to $branch detected!${NC}"
        echo -e "${YELLOW}The Githyanki forbid rewriting history on protected branches.${NC}"
        echo ""
        echo -e "${CYAN}What happened:${NC}"
        echo "  You attempted to force push to $branch, which would rewrite history."
        echo "  This is dangerous and bypasses the safety of collaborative review."
        echo ""
        echo -e "${CYAN}How to fix:${NC}"
        echo "  1. Create a feature branch: git checkout -b feat/your-feature"
        echo "  2. Push to feature branch: git push -u origin feat/your-feature"
        echo "  3. Open a Pull Request on GitHub"
        echo "  4. Merge after review and tests pass"
        echo ""
        echo -e "${YELLOW}Emergency bypass: GITHYANKI_BYPASS=1 git push${NC}"
        echo -e "${YELLOW}(Use only if you understand the consequences)${NC}"
        exit 1
      fi
    fi

    # Block direct push to main/master (even fast-forward)
    echo -e "${RED}BLOCKED! Direct push to $branch detected!${NC}"
    echo -e "${YELLOW}The Githyanki require all changes pass through the Pull Request gates.${NC}"
    echo ""
    echo -e "${CYAN}What happened:${NC}"
    echo "  You attempted to push directly to $branch."
    echo "  Direct pushes bypass code review and automated checks."
    echo ""
    echo -e "${CYAN}Correct workflow:${NC}"
    echo "  1. Create a feature branch: git checkout -b feat/your-feature"
    echo "  2. Push to feature branch: git push -u origin feat/your-feature"
    echo "  3. Open a Pull Request: gh pr create"
    echo "  4. Merge after approval and CI passes"
    echo ""
    echo -e "${CYAN}If you're on $branch by mistake:${NC}"
    echo "  git checkout -b feat/your-feature  # Move commits to feature branch"
    echo "  git push -u origin feat/your-feature"
    echo "  git checkout $branch"
    echo "  git reset --hard origin/$branch  # Reset $branch to match remote"
    echo ""
    echo -e "${YELLOW}Emergency bypass: GITHYANKI_BYPASS=1 git push${NC}"
    echo -e "${YELLOW}(Use only if you understand the consequences)${NC}"
    exit 1
  fi
done

echo -e "${GREEN}✓ Push target validated - proceeding${NC}"
exit 0
