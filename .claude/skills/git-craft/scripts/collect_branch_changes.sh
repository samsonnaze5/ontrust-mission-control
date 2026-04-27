#!/usr/bin/env bash
# collect_branch_changes.sh
# Gathers all changes on the current branch compared to a base branch.
# Outputs structured data for PR description generation.
#
# Usage: bash collect_branch_changes.sh [base-branch] [repo-path]
# - base-branch: defaults to auto-detect (develop > main > master)
# - repo-path: defaults to current directory

set -euo pipefail

REPO_PATH="${2:-.}"
cd "$REPO_PATH"

# Verify we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "ERROR: Not a git repository: $REPO_PATH"
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

if [ -z "$CURRENT_BRANCH" ]; then
    echo "ERROR: Detached HEAD state. Please checkout a branch first."
    exit 1
fi

# Check if current branch is a protected branch
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" || "$CURRENT_BRANCH" == "develop" ]]; then
    echo "WARNING: Current branch is '$CURRENT_BRANCH' (a base branch)."
    echo "PR Craft is designed for feature/fix/hotfix branches."
    echo "Please checkout your feature branch first."
    exit 1
fi

# Auto-detect base branch if not specified
if [ -n "${1:-}" ]; then
    BASE_BRANCH="$1"
else
    # Try develop first, then main, then master
    if git rev-parse --verify develop &>/dev/null; then
        BASE_BRANCH="develop"
    elif git rev-parse --verify main &>/dev/null; then
        BASE_BRANCH="main"
    elif git rev-parse --verify master &>/dev/null; then
        BASE_BRANCH="master"
    else
        echo "ERROR: Could not auto-detect base branch. Please specify: bash $0 <base-branch>"
        exit 1
    fi
fi

# Verify base branch exists
if ! git rev-parse --verify "$BASE_BRANCH" &>/dev/null; then
    echo "ERROR: Base branch '$BASE_BRANCH' does not exist."
    exit 1
fi

# Find merge base
MERGE_BASE=$(git merge-base "$BASE_BRANCH" HEAD 2>/dev/null || echo "")
if [ -z "$MERGE_BASE" ]; then
    echo "ERROR: Cannot find common ancestor between '$BASE_BRANCH' and '$CURRENT_BRANCH'."
    exit 1
fi

echo "=== BRANCH ANALYSIS REPORT ==="
echo "Current Branch: $CURRENT_BRANCH"
echo "Base Branch:    $BASE_BRANCH"
echo "Merge Base:     ${MERGE_BASE:0:8}"
echo "Timestamp:      $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- Branch name analysis ---
echo "=== BRANCH TYPE ANALYSIS ==="
BRANCH_PREFIX=$(echo "$CURRENT_BRANCH" | cut -d'/' -f1)
BRANCH_DESCRIPTION=$(echo "$CURRENT_BRANCH" | cut -d'/' -f2- 2>/dev/null || echo "$CURRENT_BRANCH")
echo "Prefix: $BRANCH_PREFIX"
echo "Description: $BRANCH_DESCRIPTION"
case "$BRANCH_PREFIX" in
    feature) echo "Type: New Feature" ;;
    fix) echo "Type: Bug Fix" ;;
    hotfix) echo "Type: Critical Bug Fix (Hotfix)" ;;
    refactor) echo "Type: Code Refactoring" ;;
    chore) echo "Type: Maintenance" ;;
    docs) echo "Type: Documentation" ;;
    *) echo "Type: Unknown (prefix: $BRANCH_PREFIX)" ;;
esac
echo ""

# --- Commit history ---
echo "=== COMMITS ON THIS BRANCH ==="
COMMIT_COUNT=$(git rev-list --count "$MERGE_BASE"..HEAD 2>/dev/null || echo "0")
echo "Total commits: $COMMIT_COUNT"
echo ""

# Show commits (no merges) with stats
git log "$MERGE_BASE"..HEAD --no-merges --format="--- %h | %s | %an | %ar ---" --stat --stat-width=100 2>/dev/null
echo ""

# --- File change summary ---
echo "=== FILE CHANGES SUMMARY ==="
git diff "$MERGE_BASE"..HEAD --stat --stat-width=120 2>/dev/null
echo ""

# Detailed name-status
echo "=== FILE STATUS ==="
git diff "$MERGE_BASE"..HEAD --name-status 2>/dev/null | sort | while IFS=$'\t' read -r status file rest; do
    case "$status" in
        A) echo "  [ADDED]    $file" ;;
        M) echo "  [MODIFIED] $file" ;;
        D) echo "  [DELETED]  $file" ;;
        R*) echo "  [RENAMED]  $rest <- $file" ;;
        *) echo "  [$status]  $file" ;;
    esac
done
echo ""

# --- Directory-level summary ---
echo "=== CHANGES BY DIRECTORY ==="
git diff "$MERGE_BASE"..HEAD --name-only 2>/dev/null | \
    sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -20
echo ""

# --- Abbreviated diffs ---
echo "=== DIFFS (abbreviated, max 800 lines) ==="
git diff "$MERGE_BASE"..HEAD -U3 2>/dev/null | head -800
echo ""

# --- Summary stats ---
ADDITIONS=$(git diff "$MERGE_BASE"..HEAD --numstat 2>/dev/null | awk '{s+=$1} END {print s+0}')
DELETIONS=$(git diff "$MERGE_BASE"..HEAD --numstat 2>/dev/null | awk '{s+=$2} END {print s+0}')
FILES_CHANGED=$(git diff "$MERGE_BASE"..HEAD --name-only 2>/dev/null | wc -l | tr -d ' ')

echo "=== SUMMARY ==="
echo "Files changed: $FILES_CHANGED"
echo "Additions:     +$ADDITIONS"
echo "Deletions:     -$DELETIONS"
echo "Net change:    $(( ADDITIONS - DELETIONS )) lines"
echo "Commits:       $COMMIT_COUNT"

# --- Check for potential breaking changes ---
echo ""
echo "=== BREAKING CHANGE INDICATORS ==="
BREAKING=0

# Check for deleted files
DELETED_COUNT=$(git diff "$MERGE_BASE"..HEAD --name-status 2>/dev/null | grep -c '^D' || echo "0")
if [ "$DELETED_COUNT" -gt 0 ]; then
    echo "  [!] $DELETED_COUNT file(s) deleted"
    BREAKING=1
fi

# Check for renamed files (potential import breaks)
RENAMED_COUNT=$(git diff "$MERGE_BASE"..HEAD --name-status 2>/dev/null | grep -c '^R' || echo "0")
if [ "$RENAMED_COUNT" -gt 0 ]; then
    echo "  [!] $RENAMED_COUNT file(s) renamed"
    BREAKING=1
fi

# Check for migration files
MIGRATION_FILES=$(git diff "$MERGE_BASE"..HEAD --name-only 2>/dev/null | grep -i 'migrat' || echo "")
if [ -n "$MIGRATION_FILES" ]; then
    echo "  [!] Migration files detected:"
    echo "$MIGRATION_FILES" | sed 's/^/      /'
    BREAKING=1
fi

# Check for API/schema changes
API_CHANGES=$(git diff "$MERGE_BASE"..HEAD --name-only 2>/dev/null | grep -iE '(api|schema|proto|graphql|swagger|openapi)' || echo "")
if [ -n "$API_CHANGES" ]; then
    echo "  [!] API/Schema files changed:"
    echo "$API_CHANGES" | sed 's/^/      /'
    BREAKING=1
fi

if [ "$BREAKING" -eq 0 ]; then
    echo "  No obvious breaking change indicators found."
fi
