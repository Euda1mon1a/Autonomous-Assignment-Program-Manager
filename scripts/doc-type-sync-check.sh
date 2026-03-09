#!/usr/bin/env bash
# doc-type-sync-check.sh — Pre-commit hook to detect DOC_TYPE_MAP drift
#
# Cross-checks:
#   1. scripts/init_rag_embeddings.py  DOC_TYPE_MAP
#   2. backend/app/tasks/rag_tasks.py  DOC_TYPE_MAP
#   3. backend/app/schemas/rag.py      allowed_types
#   4. docs/rag-knowledge/*.md          actual files on disk
#
# Exit 0 = clean, Exit 1 = drift detected

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
INIT_SCRIPT="$REPO_ROOT/scripts/init_rag_embeddings.py"
RAG_TASKS="$REPO_ROOT/backend/app/tasks/rag_tasks.py"
RAG_SCHEMA="$REPO_ROOT/backend/app/schemas/rag.py"
RAG_DOCS_DIR="$REPO_ROOT/docs/rag-knowledge"

ERRORS=0

# --- Check A: Both DOC_TYPE_MAPs are identical ---
if [ -f "$INIT_SCRIPT" ] && [ -f "$RAG_TASKS" ]; then
    # Extract DOC_TYPE_MAP blocks and compare
    INIT_MAP=$(python3 -c "
import ast, sys
with open('$INIT_SCRIPT') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == 'DOC_TYPE_MAP':
                print(ast.dump(node.value))
")
    TASKS_MAP=$(python3 -c "
import ast, sys
with open('$RAG_TASKS') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == 'DOC_TYPE_MAP':
                print(ast.dump(node.value))
")
    if [ "$INIT_MAP" != "$TASKS_MAP" ]; then
        echo "ERROR: DOC_TYPE_MAP differs between init_rag_embeddings.py and rag_tasks.py"
        ERRORS=$((ERRORS + 1))
    fi
fi

# --- Check B: Every .md in docs/rag-knowledge/ has a mapping ---
if [ -d "$RAG_DOCS_DIR" ] && [ -f "$INIT_SCRIPT" ]; then
    for md_file in "$RAG_DOCS_DIR"/*.md; do
        basename_file=$(basename "$md_file")
        if [ "$basename_file" = "README.md" ]; then
            continue
        fi
        if ! grep -q "\"$basename_file\"" "$INIT_SCRIPT" 2>/dev/null; then
            echo "WARNING: Orphan file — $basename_file has no DOC_TYPE_MAP entry"
            ERRORS=$((ERRORS + 1))
        fi
    done
fi

# --- Check C: Every DOC_TYPE_MAP value is in allowed_types ---
if [ -f "$INIT_SCRIPT" ] && [ -f "$RAG_SCHEMA" ]; then
    DOC_TYPES=$(python3 -c "
import ast
with open('$INIT_SCRIPT') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == 'DOC_TYPE_MAP':
                if isinstance(node.value, ast.Dict):
                    for v in node.value.values:
                        if isinstance(v, ast.Constant):
                            print(v.value)
" 2>/dev/null | sort -u)

    for dtype in $DOC_TYPES; do
        if ! grep -q "\"$dtype\"" "$RAG_SCHEMA" 2>/dev/null; then
            echo "ERROR: doc_type '$dtype' used in DOC_TYPE_MAP but missing from allowed_types in rag.py"
            ERRORS=$((ERRORS + 1))
        fi
    done
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "doc-type-sync-check: $ERRORS issue(s) found. Fix before committing."
    echo "Run /doc-type-sync for detailed diagnosis."
    exit 1
fi

exit 0
