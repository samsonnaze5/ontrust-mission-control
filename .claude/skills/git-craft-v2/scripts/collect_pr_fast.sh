#!/usr/bin/env bash
# collect_pr_fast.sh — Combined fast PR data collection
# Gathers branch changes + test file detection in a single optimized script.
# Minimizes git calls (~4 vs ~12 in v1) and excludes generated files from diffs.
#
# Usage: bash collect_pr_fast.sh [base-branch] [repo-path]

set -uo pipefail

REPO_PATH="${2:-.}"
cd "$REPO_PATH"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "ERROR: Not a git repository: $REPO_PATH"
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
if [ -z "$CURRENT_BRANCH" ]; then
    echo "ERROR: Detached HEAD state."
    exit 1
fi

if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" || "$CURRENT_BRANCH" == "develop" ]]; then
    echo "ERROR: Current branch is '$CURRENT_BRANCH' (base branch). Checkout a feature branch first."
    exit 1
fi

# Auto-detect base branch
if [ -n "${1:-}" ]; then
    BASE_BRANCH="$1"
else
    for candidate in develop main master; do
        if git rev-parse --verify "$candidate" &>/dev/null; then
            BASE_BRANCH="$candidate"
            break
        fi
    done
    if [ -z "${BASE_BRANCH:-}" ]; then
        echo "ERROR: Could not auto-detect base branch."
        exit 1
    fi
fi

MERGE_BASE=$(git merge-base "$BASE_BRANCH" HEAD 2>/dev/null || echo "")
if [ -z "$MERGE_BASE" ]; then
    echo "ERROR: Cannot find common ancestor between '$BASE_BRANCH' and '$CURRENT_BRANCH'."
    exit 1
fi

# --- Header ---
BRANCH_PREFIX=$(echo "$CURRENT_BRANCH" | cut -d'/' -f1)
case "$BRANCH_PREFIX" in
    feature|feat) BRANCH_TYPE="New Feature" ;;
    fix) BRANCH_TYPE="Bug Fix" ;;
    hotfix) BRANCH_TYPE="Critical Bug Fix" ;;
    refactor) BRANCH_TYPE="Refactoring" ;;
    chore) BRANCH_TYPE="Maintenance" ;;
    docs) BRANCH_TYPE="Documentation" ;;
    *) BRANCH_TYPE="$BRANCH_PREFIX" ;;
esac

echo "=== PR DATA (fast) ==="
echo "Branch: $CURRENT_BRANCH"
echo "Base: $BASE_BRANCH"
echo "Type: $BRANCH_TYPE"
echo ""

# --- [1/4] Commits (single git log call) ---
COMMIT_COUNT=$(git rev-list --count "$MERGE_BASE"..HEAD 2>/dev/null || echo "0")
echo "=== COMMITS ($COMMIT_COUNT) ==="
git log "$MERGE_BASE"..HEAD --no-merges --format="%h %s" 2>/dev/null
echo ""

# --- [2/4] File status + stats (single git diff call, cached in tmpfile) ---
NUMSTAT_FILE=$(mktemp)
NAME_STATUS_FILE=$(mktemp)
trap "rm -f $NUMSTAT_FILE $NAME_STATUS_FILE" EXIT

git diff "$MERGE_BASE"..HEAD --numstat 2>/dev/null > "$NUMSTAT_FILE"
git diff "$MERGE_BASE"..HEAD --name-status 2>/dev/null > "$NAME_STATUS_FILE"

FILES_CHANGED=$(wc -l < "$NUMSTAT_FILE" | tr -d ' ')
ADDITIONS=$(awk '{s+=$1} END {print s+0}' "$NUMSTAT_FILE")
DELETIONS=$(awk '{s+=$2} END {print s+0}' "$NUMSTAT_FILE")

echo "=== FILES ($FILES_CHANGED changed, +$ADDITIONS -$DELETIONS) ==="
while IFS=$'\t' read -r status file rest; do
    [ -z "$status" ] && continue
    # Get line counts from numstat
    LINES=$(grep -P "\t${file}$" "$NUMSTAT_FILE" 2>/dev/null | awk '{printf "+%s -%s", $1, $2}' || echo "")
    case "$status" in
        A) echo "  ADD $file $LINES" ;;
        M) echo "  MOD $file $LINES" ;;
        D) echo "  DEL $file" ;;
        R*) echo "  REN $rest <- $file" ;;
        *) echo "  $status $file" ;;
    esac
done < "$NAME_STATUS_FILE"
echo ""

# --- Directory summary ---
echo "=== BY DIRECTORY ==="
awk -F'\t' '{print $NF}' "$NAME_STATUS_FILE" | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -15
echo ""

# --- [3/4] Breaking change indicators (parsed from cached data, no extra git calls) ---
echo "=== BREAKING CHANGES ==="
DELETED_COUNT=$(grep -c '^D' "$NAME_STATUS_FILE" || true)
DELETED_COUNT=${DELETED_COUNT:-0}
RENAMED_COUNT=$(grep -c '^R' "$NAME_STATUS_FILE" || true)
RENAMED_COUNT=${RENAMED_COUNT:-0}
MIGRATION_FILES=$(awk -F'\t' '{print $NF}' "$NAME_STATUS_FILE" | grep -i 'migrat\|\.sql' || true)
API_FILES=$(awk -F'\t' '{print $NF}' "$NAME_STATUS_FILE" | grep -iE 'swagger|openapi|proto|graphql' || true)

HAS_BREAKING=false
[ "$DELETED_COUNT" -gt 0 ] && echo "  [!] $DELETED_COUNT file(s) deleted" && HAS_BREAKING=true
[ "$RENAMED_COUNT" -gt 0 ] && echo "  [!] $RENAMED_COUNT file(s) renamed" && HAS_BREAKING=true
[ -n "$MIGRATION_FILES" ] && echo "  [!] Migrations: $MIGRATION_FILES" && HAS_BREAKING=true
[ -n "$API_FILES" ] && echo "  [!] API/Schema: $API_FILES" && HAS_BREAKING=true
[ "$HAS_BREAKING" = false ] && echo "  None detected"
echo ""

# --- [4/4] Diffs (single call, filtered, limited) ---
echo "=== DIFFS (filtered, max 400 lines) ==="
DIFF_OUTPUT=$(git diff "$MERGE_BASE"..HEAD -U3 \
    -- . ':!*.gen.go' ':!go.sum' ':!*_mock.go' ':!*.lock' ':!vendor/*' \
    2>/dev/null || true)
echo "$DIFF_OUTPUT" | head -400
echo ""

# --- Test file detection (no execution) ---
echo "=== TEST FILES ==="
ALL_FILES=$(awk -F'\t' '{print $NF}' "$NAME_STATUS_FILE")
TEST_FILES=$(echo "$ALL_FILES" | grep -E '_test\.go$|\.test\.(ts|js)x?$|\.spec\.(ts|js)x?$|test_.*\.py$|.*_test\.py$' || true)
SOURCE_FILES=$(echo "$ALL_FILES" | grep -E '\.(go|ts|tsx|js|jsx|py)$' | grep -vE '_test\.|\.test\.|\.spec\.|test_' || true)

if [ -n "$TEST_FILES" ]; then
    echo "Changed test files:"
    echo "$TEST_FILES" | sed 's/^/  /'
    echo ""
    # Suggest test packages for Go
    GO_TEST_PKGS=$(echo "$TEST_FILES" | grep '_test\.go$' | while read -r f; do dirname "$f"; done | sort -u || true)
    if [ -n "$GO_TEST_PKGS" ]; then
        echo "Run command:"
        echo "  go test -v $(echo "$GO_TEST_PKGS" | sed 's|^|./|' | tr '\n' ' ')"
    fi
else
    echo "No test files in changes."
    if [ -n "$SOURCE_FILES" ]; then
        echo "Source files without tests:"
        echo "$SOURCE_FILES" | sed 's/^/  /'
    fi
fi
echo ""
echo "=== END ==="
