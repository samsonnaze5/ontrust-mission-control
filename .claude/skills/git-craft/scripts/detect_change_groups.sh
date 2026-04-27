#!/usr/bin/env bash
# detect_change_groups.sh
# Analyzes uncommitted files and suggests logical groupings for splitting into multiple commits.
# Uses directory structure, file types, and naming patterns to infer relationships.
#
# Usage: bash detect_change_groups.sh [repo-path]

set -euo pipefail

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "ERROR: Not a git repository: $REPO_PATH"
    exit 1
fi

echo "=== CHANGE GROUP ANALYSIS ==="
echo ""

# Collect all changed files (staged + unstaged + untracked)
CHANGED_FILES=$(mktemp)
trap "rm -f $CHANGED_FILES" EXIT

# Staged
git diff --cached --name-only 2>/dev/null >> "$CHANGED_FILES"
# Unstaged
git diff --name-only 2>/dev/null >> "$CHANGED_FILES"
# Untracked
git ls-files --others --exclude-standard 2>/dev/null >> "$CHANGED_FILES"

# Deduplicate
sort -u "$CHANGED_FILES" -o "$CHANGED_FILES"

TOTAL=$(wc -l < "$CHANGED_FILES" | tr -d ' ')

if [ "$TOTAL" -eq 0 ]; then
    echo "No changes detected. Working directory is clean."
    exit 0
fi

echo "Total unique files with changes: $TOTAL"
echo ""

# --- Group by top-level directory ---
echo "=== GROUP BY DIRECTORY ==="
while read -r file; do
    dirname "$file"
done < "$CHANGED_FILES" | sort | uniq -c | sort -rn | while read -r count dir; do
    echo "  [$count files] $dir/"
done
echo ""

# --- Group by file extension ---
echo "=== GROUP BY FILE TYPE ==="
while read -r file; do
    ext="${file##*.}"
    if [ "$ext" = "$file" ]; then
        echo "no-extension"
    else
        echo ".$ext"
    fi
done < "$CHANGED_FILES" | sort | uniq -c | sort -rn | while read -r count ext; do
    echo "  [$count files] $ext"
done
echo ""

# --- Detect test files and pair with source ---
echo "=== TEST FILE ASSOCIATIONS ==="
TEST_FILES=$(grep -iE '(_test\.|\.test\.|\.spec\.|test_|tests/)' "$CHANGED_FILES" 2>/dev/null || echo "")
NON_TEST_FILES=$(grep -viE '(_test\.|\.test\.|\.spec\.|test_|tests/)' "$CHANGED_FILES" 2>/dev/null || echo "")

if [ -n "$TEST_FILES" ]; then
    echo "Test files found:"
    echo "$TEST_FILES" | sed 's/^/  /'
    echo ""
    echo "Corresponding source files:"
    echo "$NON_TEST_FILES" | sed 's/^/  /'
else
    echo "No test files detected in changes."
fi
echo ""

# --- Detect config/infra files ---
echo "=== CONFIG/INFRASTRUCTURE FILES ==="
CONFIG_FILES=$(grep -iE '(\.ya?ml$|\.json$|\.toml$|\.env|\.conf|Dockerfile|docker-compose|Makefile|\.mod$|go\.sum|package\.json|requirements\.txt|\.lock$|\.cfg$|\.ini$|\.gitignore)' "$CHANGED_FILES" 2>/dev/null || echo "")
if [ -n "$CONFIG_FILES" ]; then
    echo "$CONFIG_FILES" | sed 's/^/  /'
else
    echo "No config/infrastructure files detected."
fi
echo ""

# --- Detect documentation files ---
echo "=== DOCUMENTATION FILES ==="
DOC_FILES=$(grep -iE '(\.md$|\.rst$|\.txt$|docs/|\.adoc$|CHANGELOG|README|LICENSE)' "$CHANGED_FILES" 2>/dev/null || echo "")
if [ -n "$DOC_FILES" ]; then
    echo "$DOC_FILES" | sed 's/^/  /'
else
    echo "No documentation files detected."
fi
echo ""

# --- Detect migration files ---
echo "=== MIGRATION FILES ==="
MIGRATION_FILES=$(grep -iE '(migrat|schema|\.sql$)' "$CHANGED_FILES" 2>/dev/null || echo "")
if [ -n "$MIGRATION_FILES" ]; then
    echo "$MIGRATION_FILES" | sed 's/^/  /'
else
    echo "No migration files detected."
fi
echo ""

# --- Suggested grouping ---
echo "=== SUGGESTED COMMIT GROUPS ==="
echo ""

GROUP_NUM=0

# Group 1: Config/infra (if any)
if [ -n "$CONFIG_FILES" ]; then
    GROUP_NUM=$((GROUP_NUM + 1))
    CONFIG_COUNT=$(echo "$CONFIG_FILES" | wc -l | tr -d ' ')
    echo "Group $GROUP_NUM: Configuration/Infrastructure ($CONFIG_COUNT files)"
    echo "  Suggested type: chore"
    echo "  Files:"
    echo "$CONFIG_FILES" | sed 's/^/    /'
    echo ""
fi

# Group 2: Migrations (if any)
if [ -n "$MIGRATION_FILES" ]; then
    # Don't double-count with config
    UNIQUE_MIGRATIONS=$(echo "$MIGRATION_FILES" | grep -vxF "$(echo "$CONFIG_FILES")" 2>/dev/null || echo "$MIGRATION_FILES")
    if [ -n "$UNIQUE_MIGRATIONS" ]; then
        GROUP_NUM=$((GROUP_NUM + 1))
        MIG_COUNT=$(echo "$UNIQUE_MIGRATIONS" | wc -l | tr -d ' ')
        echo "Group $GROUP_NUM: Database Migrations ($MIG_COUNT files)"
        echo "  Suggested type: feat or fix"
        echo "  Files:"
        echo "$UNIQUE_MIGRATIONS" | sed 's/^/    /'
        echo ""
    fi
fi

# Group 3: Source code (non-test, non-config, non-doc, non-migration)
SOURCE_FILES=$(echo "$NON_TEST_FILES" | grep -vxF "$(echo -e "$CONFIG_FILES\n$DOC_FILES\n$MIGRATION_FILES")" 2>/dev/null || echo "")
if [ -n "$SOURCE_FILES" ]; then
    GROUP_NUM=$((GROUP_NUM + 1))
    SRC_COUNT=$(echo "$SOURCE_FILES" | grep -c '.' 2>/dev/null || echo "0")
    echo "Group $GROUP_NUM: Source Code ($SRC_COUNT files)"
    echo "  Suggested type: feat, fix, or refactor"
    echo "  Files:"
    echo "$SOURCE_FILES" | sed 's/^/    /'
    echo ""
fi

# Group 4: Tests (if any)
if [ -n "$TEST_FILES" ]; then
    GROUP_NUM=$((GROUP_NUM + 1))
    TEST_COUNT=$(echo "$TEST_FILES" | wc -l | tr -d ' ')
    echo "Group $GROUP_NUM: Tests ($TEST_COUNT files)"
    echo "  Suggested type: test"
    echo "  Files:"
    echo "$TEST_FILES" | sed 's/^/    /'
    echo ""
fi

# Group 5: Docs (if any)
if [ -n "$DOC_FILES" ]; then
    GROUP_NUM=$((GROUP_NUM + 1))
    DOC_COUNT=$(echo "$DOC_FILES" | wc -l | tr -d ' ')
    echo "Group $GROUP_NUM: Documentation ($DOC_COUNT files)"
    echo "  Suggested type: docs"
    echo "  Files:"
    echo "$DOC_FILES" | sed 's/^/    /'
    echo ""
fi

if [ "$GROUP_NUM" -eq 0 ]; then
    echo "All files appear to be part of a single logical change."
    echo "Suggest: 1 commit covering all $TOTAL files."
fi

echo ""
echo "=== NOTE ==="
echo "These groups are suggestions based on file patterns."
echo "The AI should use diff content and context to refine these groups."
echo "Total suggested groups: $GROUP_NUM"
