#!/usr/bin/env bash
# collect_uncommitted.sh
# Gathers all uncommitted changes (staged + unstaged + untracked) and outputs
# a structured summary optimized for AI consumption (minimal tokens, maximum signal).
#
# Usage: bash collect_uncommitted.sh [repo-path]
# If repo-path is omitted, uses current directory.

set -euo pipefail

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

# Verify we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "ERROR: Not a git repository: $REPO_PATH"
    exit 1
fi

BRANCH=$(git branch --show-current 2>/dev/null || echo "DETACHED")

echo "=== UNCOMMITTED CHANGES REPORT ==="
echo "Repository: $(basename "$(git rev-parse --show-toplevel)")"
echo "Branch: $BRANCH"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- Staged changes ---
STAGED=$(git diff --cached --stat --stat-width=120 2>/dev/null)
STAGED_FILES=$(git diff --cached --name-status 2>/dev/null)
if [ -n "$STAGED_FILES" ]; then
    echo "=== STAGED CHANGES ==="
    echo "$STAGED_FILES" | while IFS=$'\t' read -r status file rest; do
        case "$status" in
            A) echo "  [ADDED]    $file" ;;
            M) echo "  [MODIFIED] $file" ;;
            D) echo "  [DELETED]  $file" ;;
            R*) echo "  [RENAMED]  $rest <- $file" ;;
            C*) echo "  [COPIED]   $rest <- $file" ;;
            *) echo "  [$status]  $file" ;;
        esac
    done
    echo ""
    echo "--- Staged Diff Stats ---"
    echo "$STAGED"
    echo ""

    # Abbreviated diffs for staged (max 30 lines per file, max 500 lines total)
    echo "--- Staged Diffs (abbreviated) ---"
    git diff --cached -U3 2>/dev/null | head -500
    echo ""
fi

# --- Unstaged changes ---
UNSTAGED_FILES=$(git diff --name-status 2>/dev/null)
if [ -n "$UNSTAGED_FILES" ]; then
    echo "=== UNSTAGED CHANGES ==="
    echo "$UNSTAGED_FILES" | while IFS=$'\t' read -r status file rest; do
        case "$status" in
            M) echo "  [MODIFIED] $file" ;;
            D) echo "  [DELETED]  $file" ;;
            R*) echo "  [RENAMED]  $rest <- $file" ;;
            *) echo "  [$status]  $file" ;;
        esac
    done
    echo ""
    echo "--- Unstaged Diff Stats ---"
    git diff --stat --stat-width=120 2>/dev/null
    echo ""

    # Abbreviated diffs for unstaged
    echo "--- Unstaged Diffs (abbreviated) ---"
    git diff -U3 2>/dev/null | head -500
    echo ""
fi

# --- Untracked files ---
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null)
if [ -n "$UNTRACKED" ]; then
    echo "=== UNTRACKED FILES ==="
    echo "$UNTRACKED" | while read -r file; do
        if [ -f "$file" ]; then
            LINES=$(wc -l < "$file" 2>/dev/null || echo "?")
            SIZE=$(wc -c < "$file" 2>/dev/null || echo "?")
            echo "  [NEW] $file ($LINES lines, $SIZE bytes)"
        else
            echo "  [NEW] $file"
        fi
    done
    echo ""
fi

# --- Summary ---
if [ -n "$STAGED_FILES" ]; then
    STAGED_COUNT=$(echo "$STAGED_FILES" | wc -l | tr -d ' ')
else
    STAGED_COUNT=0
fi
if [ -n "$UNSTAGED_FILES" ]; then
    UNSTAGED_COUNT=$(echo "$UNSTAGED_FILES" | wc -l | tr -d ' ')
else
    UNSTAGED_COUNT=0
fi
if [ -n "$UNTRACKED" ]; then
    UNTRACKED_COUNT=$(echo "$UNTRACKED" | wc -l | tr -d ' ')
else
    UNTRACKED_COUNT=0
fi
TOTAL=$((STAGED_COUNT + UNSTAGED_COUNT + UNTRACKED_COUNT))

echo "=== SUMMARY ==="
echo "Staged:    $STAGED_COUNT files"
echo "Unstaged:  $UNSTAGED_COUNT files"
echo "Untracked: $UNTRACKED_COUNT files"
echo "Total:     $TOTAL files with changes"

if [ "$TOTAL" -eq 0 ]; then
    echo ""
    echo "NOTE: Working directory is clean. No changes to commit."
fi
