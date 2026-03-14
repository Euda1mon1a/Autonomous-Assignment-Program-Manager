#!/usr/bin/env bash
# GlassWorm Defense — Credential Exposure Check
#
# GlassWorm harvests npm, GitHub, Git, and OpenVSX credentials after infection.
# This script checks for credential hygiene issues that would maximize damage
# if a developer's machine were compromised.
#
# Usage: ./scripts/check-credential-exposure.sh
#
# Reference: https://www.koi.ai/blog/glassworm-first-self-propagating-worm-using-invisible-code-hits-openvsx-marketplace

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

WARNINGS=0
CHECKS=0

check() {
    local label="$1"
    CHECKS=$((CHECKS + 1))
    echo -e "${CYAN}[$CHECKS]${NC} $label"
}

warn() {
    WARNINGS=$((WARNINGS + 1))
    echo -e "    ${YELLOW}WARNING${NC} $1"
}

ok() {
    echo -e "    ${GREEN}OK${NC} $1"
}

info() {
    echo -e "    $1"
}

echo "=== Credential Exposure Check (GlassWorm Defense) ==="
echo ""

# 1. npm tokens in ~/.npmrc
check "npm authentication tokens"
if [ -f "$HOME/.npmrc" ]; then
    if grep -q '_authToken' "$HOME/.npmrc" 2>/dev/null; then
        warn "~/.npmrc contains auth tokens"
        info "  Remediation: Use short-lived tokens (npm token create --read-only)"
        info "  List tokens: npm token list"
        info "  Revoke old:  npm token revoke <token>"
    else
        ok "~/.npmrc exists but has no auth tokens"
    fi
else
    ok "No ~/.npmrc file (no npm tokens exposed)"
fi
echo ""

# 2. Git credential storage
check "Git credential storage"
GIT_CRED_HELPER=$(git config --global credential.helper 2>/dev/null || echo "")
if [ -z "$GIT_CRED_HELPER" ]; then
    ok "No global credential helper configured"
elif [ "$GIT_CRED_HELPER" = "store" ]; then
    warn "Git credential helper is 'store' (plaintext in ~/.git-credentials)"
    info "  Remediation: Switch to macOS Keychain:"
    info "    git config --global credential.helper osxkeychain"
elif [ "$GIT_CRED_HELPER" = "osxkeychain" ]; then
    ok "Using macOS Keychain (encrypted storage)"
elif echo "$GIT_CRED_HELPER" | grep -q "cache"; then
    local_timeout=$(git config --global credential.helper 2>/dev/null | sed -n 's/.*timeout=\([0-9]*\).*/\1/p')
    local_timeout="${local_timeout:-900}"
    ok "Using cache helper (timeout: ${local_timeout}s)"
else
    info "Using credential helper: $GIT_CRED_HELPER"
fi
echo ""

# 3. GitHub CLI token scope
check "GitHub CLI token scopes"
if command -v gh &>/dev/null; then
    GH_STATUS=$(gh auth status 2>&1 || true)
    if echo "$GH_STATUS" | grep -q "Logged in"; then
        local_scopes=$(echo "$GH_STATUS" | grep "Token scopes:" | sed 's/.*Token scopes:/Token scopes:/' || echo "")
        if [ -n "$local_scopes" ]; then
            info "  $local_scopes"
            # Check for overly broad scopes
            if echo "$local_scopes" | grep -q "admin"; then
                warn "Token has admin scope — minimize with: gh auth refresh -s 'repo,read:org'"
            else
                ok "Token scopes look reasonable"
            fi
        else
            ok "Authenticated (scopes not displayed — likely fine-grained PAT)"
        fi
    else
        ok "Not logged into GitHub CLI (no token to steal)"
    fi
else
    info "gh CLI not installed (skipping)"
fi
echo ""

# 4. SSH key passphrase protection
check "SSH key passphrase protection"
SSH_KEYS_FOUND=0
SSH_KEYS_UNPROTECTED=0
for key_file in "$HOME/.ssh/id_"*; do
    [ -f "$key_file" ] || continue
    # Skip .pub files
    [[ "$key_file" == *.pub ]] && continue
    SSH_KEYS_FOUND=$((SSH_KEYS_FOUND + 1))

    # Check if key has a passphrase by trying to parse it
    # ssh-keygen -y -P "" will succeed only if there's no passphrase
    if ssh-keygen -y -P "" -f "$key_file" &>/dev/null; then
        warn "SSH key has no passphrase: $(basename "$key_file")"
        info "  Remediation: ssh-keygen -p -f $key_file"
        SSH_KEYS_UNPROTECTED=$((SSH_KEYS_UNPROTECTED + 1))
    fi
done

if [ "$SSH_KEYS_FOUND" -eq 0 ]; then
    ok "No SSH private keys found in ~/.ssh/"
elif [ "$SSH_KEYS_UNPROTECTED" -eq 0 ]; then
    ok "All $SSH_KEYS_FOUND SSH key(s) are passphrase-protected"
fi
echo ""

# 5. OpenVSX / VS Code marketplace tokens
check "VS Code marketplace tokens"
VSCE_TOKEN_FILES=(
    "$HOME/.vsce"
    "$HOME/.ovsx"
)
VSCE_FOUND=false
for token_file in "${VSCE_TOKEN_FILES[@]}"; do
    if [ -f "$token_file" ]; then
        warn "Marketplace token file exists: $token_file"
        info "  If you don't publish extensions, delete it: rm $token_file"
        VSCE_FOUND=true
    fi
done
if ! $VSCE_FOUND; then
    ok "No marketplace token files found"
fi
echo ""

# 6. .env files with secrets
check ".env files in project"
ENV_FILES=$(find . -maxdepth 3 -name '.env*' -not -name '.env.example' -not -name '.env.template' -not -name '*.example' 2>/dev/null || true)
if [ -n "$ENV_FILES" ]; then
    info "Found .env files (ensure they're in .gitignore):"
    echo "$ENV_FILES" | while read -r f; do
        if git ls-files --error-unmatch "$f" &>/dev/null 2>&1; then
            warn "TRACKED by git: $f"
        else
            ok "  gitignored: $f"
        fi
    done
else
    ok "No .env files found in project tree"
fi
echo ""

# Summary
echo "=== Summary ==="
echo "Checks performed: $CHECKS"
if [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo ""
    echo "These warnings indicate credential exposure vectors that GlassWorm"
    echo "or similar malware could exploit after infecting your machine via"
    echo "a compromised VS Code extension."
    exit 1
else
    echo -e "${GREEN}No warnings. Credential hygiene looks good.${NC}"
    exit 0
fi
