#!/usr/bin/env bash
set -euo pipefail

echo "PII history rewrite helper (DO NOT RUN WITHOUT COORDINATION)"
echo "This script will rewrite git history using git filter-repo."
echo "Ensure backup branch exists and collaborators are notified."
echo

# Example 1: Remove a sensitive file by path (edit as needed)
# git filter-repo --path "path/to/sensitive_file.ext" --invert-paths

# Example 2: Remove multiple paths (repeat --path as needed)
# git filter-repo \
#   --path "path/to/sensitive_file.ext" \
#   --path "path/to/another_sensitive_file.ext" \
#   --invert-paths

# Example 3: Replace PII content by pattern (edit or add patterns)
# Create a replacements file:
#   cat <<'EOF' > /tmp/replacements.txt
#   regex:<EMAIL_REGEX>==>[REDACTED_EMAIL]
#   regex:<PHONE_REGEX>==>[REDACTED_PHONE]
#   EOF
# Then run:
#   git filter-repo --replace-text /tmp/replacements.txt

echo "No actions executed. Edit this script to target your PII, then re-run."
exit 0
