#!/bin/bash
# collect_test_results.sh — Detects test files in the branch changes and attempts to run them
# Usage: bash collect_test_results.sh [repo-path] [base-branch]
# Output: Structured report of test files found and test execution results

REPO_PATH="${1:-.}"
BASE_BRANCH="${2:-}"

cd "$REPO_PATH" 2>/dev/null || { echo "ERROR: Cannot access repo at $REPO_PATH"; exit 1; }

# Auto-detect base branch if not specified
if [ -z "$BASE_BRANCH" ]; then
    for candidate in develop main master; do
        if git rev-parse --verify "$candidate" >/dev/null 2>&1; then
            BASE_BRANCH="$candidate"
            break
        fi
    done
fi

if [ -z "$BASE_BRANCH" ]; then
    echo "ERROR: Could not detect base branch. None of develop, main, master exist." >&2
    echo "Usage: $0 [repo-path] [base-branch]" >&2
    exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
MERGE_BASE=$(git merge-base "$BASE_BRANCH" HEAD 2>/dev/null)

echo "=== TEST ANALYSIS REPORT ==="
echo "Branch: $CURRENT_BRANCH"
echo "Base: $BASE_BRANCH"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- Detect test files changed in this branch ---
echo "=== TEST FILES CHANGED IN BRANCH ==="

if [ -n "$MERGE_BASE" ]; then
    CHANGED_FILES=$(git diff --name-only "$MERGE_BASE"..HEAD 2>/dev/null)
else
    CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null)
fi

# Also include uncommitted test files
UNCOMMITTED_FILES=$(git status --porcelain 2>/dev/null | awk '{print $NF}')
ALL_FILES=$(echo -e "$CHANGED_FILES\n$UNCOMMITTED_FILES" | sort -u | grep -v '^$')

# Detect test files by common patterns
TEST_FILES=""
while IFS= read -r file; do
    [ -z "$file" ] && continue
    case "$file" in
        *_test.go) TEST_FILES="$TEST_FILES$file\n" ;;
        *.test.ts|*.test.tsx|*.test.js|*.test.jsx) TEST_FILES="$TEST_FILES$file\n" ;;
        *.spec.ts|*.spec.tsx|*.spec.js|*.spec.jsx) TEST_FILES="$TEST_FILES$file\n" ;;
        *test_*.py|*_test.py|*/tests/*.py|*/test/*.py) TEST_FILES="$TEST_FILES$file\n" ;;
        *Test.java|*Tests.java|*/test/*) TEST_FILES="$TEST_FILES$file\n" ;;
        *_test.rs) TEST_FILES="$TEST_FILES$file\n" ;;
    esac
done <<< "$ALL_FILES"

TEST_FILES=$(echo -e "$TEST_FILES" | grep -v '^$' | sort -u)

if [ -z "$TEST_FILES" ]; then
    echo "No test files detected in changed files."
    echo ""
    echo "=== TEST FILE RECOMMENDATIONS ==="
    echo "NOTE: No test files were added or modified in this branch."

    # Check which source files changed
    SOURCE_FILES=""
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        case "$file" in
            *.go|*.ts|*.tsx|*.js|*.jsx|*.py|*.java|*.rs)
                # Exclude test files themselves
                case "$file" in
                    *_test.*|*.test.*|*.spec.*|*test_*|*Test.*) ;;
                    *) SOURCE_FILES="$SOURCE_FILES  - $file\n" ;;
                esac
                ;;
        esac
    done <<< "$ALL_FILES"

    if [ -n "$SOURCE_FILES" ]; then
        echo "Source files changed that might need tests:"
        echo -e "$SOURCE_FILES"
    fi
else
    echo -e "$TEST_FILES" | while IFS= read -r tf; do
        [ -z "$tf" ] && continue
        if [ -f "$tf" ]; then
            LINES=$(wc -l < "$tf" | tr -d ' ')
            echo "  [FOUND] $tf ($LINES lines)"
        else
            echo "  [DELETED] $tf"
        fi
    done
fi

echo ""

# --- Detect project type and run tests ---
echo "=== TEST EXECUTION ==="

RAN_TESTS=false

# Go tests
if echo -e "$TEST_FILES" | grep -q '_test.go$'; then
    echo "--- Go Tests ---"
    RAN_TESTS=true

    # Find unique packages that have test files
    GO_TEST_PKGS=$(echo -e "$TEST_FILES" | grep '_test.go$' | while read -r f; do dirname "$f"; done | sort -u)

    echo "Test packages detected:"
    echo "$GO_TEST_PKGS" | while read -r pkg; do
        echo "  - ./$pkg"
    done
    echo ""

    # Try to run go test (with timeout)
    if command -v go >/dev/null 2>&1; then
        echo "Running: go test ./..."
        GO_TEST_OUTPUT=$(timeout 120 go test ./... 2>&1)
        GO_EXIT=$?
        echo "$GO_TEST_OUTPUT"
        echo ""
        if [ $GO_EXIT -eq 0 ]; then
            echo "Result: PASS"
        elif [ $GO_EXIT -eq 124 ]; then
            echo "Result: TIMEOUT (exceeded 120s)"
        else
            echo "Result: FAIL (exit code: $GO_EXIT)"
        fi
    else
        echo "NOTE: go command not available. Cannot run tests automatically."
        echo "Manual command: go test ./..."
    fi
    echo ""
fi

# Node.js tests (jest, vitest, mocha)
if echo -e "$TEST_FILES" | grep -qE '\.(test|spec)\.(ts|tsx|js|jsx)$'; then
    echo "--- JavaScript/TypeScript Tests ---"
    RAN_TESTS=true

    TEST_COUNT=$(echo -e "$TEST_FILES" | grep -cE '\.(test|spec)\.(ts|tsx|js|jsx)$')
    echo "Test files detected: $TEST_COUNT"

    if [ -f "package.json" ]; then
        # Detect test runner
        if grep -q '"vitest"' package.json 2>/dev/null; then
            RUNNER="vitest"
        elif grep -q '"jest"' package.json 2>/dev/null; then
            RUNNER="jest"
        elif grep -q '"mocha"' package.json 2>/dev/null; then
            RUNNER="mocha"
        else
            RUNNER="unknown"
        fi
        echo "Detected test runner: $RUNNER"

        # Try to run tests
        if command -v npx >/dev/null 2>&1 && [ "$RUNNER" != "unknown" ]; then
            RUN_ARGS=""
            if [ "$RUNNER" = "vitest" ]; then
                RUN_ARGS="--run"
            fi
            echo "Running: npx $RUNNER $RUN_ARGS"
            TEST_OUTPUT=$(timeout 120 npx "$RUNNER" $RUN_ARGS 2>&1)
            TEST_EXIT=$?
            echo "$TEST_OUTPUT" | tail -20
            echo ""
            if [ $TEST_EXIT -eq 0 ]; then
                echo "Result: PASS"
            else
                echo "Result: FAIL (exit code: $TEST_EXIT)"
            fi
        else
            echo "NOTE: Cannot determine test runner. Check package.json scripts."
            echo "Manual command: npm test"
        fi
    else
        echo "NOTE: No package.json found."
    fi
    echo ""
fi

# Python tests
if echo -e "$TEST_FILES" | grep -qE '\.py$'; then
    echo "--- Python Tests ---"
    RAN_TESTS=true

    TEST_COUNT=$(echo -e "$TEST_FILES" | grep -cE '\.py$')
    echo "Test files detected: $TEST_COUNT"

    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import pytest" 2>/dev/null; then
            echo "Running: python3 -m pytest"
            TEST_OUTPUT=$(timeout 120 python3 -m pytest -v 2>&1)
            TEST_EXIT=$?
            echo "$TEST_OUTPUT" | tail -20
        else
            echo "Running: python3 -m unittest discover"
            TEST_OUTPUT=$(timeout 120 python3 -m unittest discover 2>&1)
            TEST_EXIT=$?
            echo "$TEST_OUTPUT" | tail -20
        fi
        echo ""
        if [ $TEST_EXIT -eq 0 ]; then
            echo "Result: PASS"
        else
            echo "Result: FAIL (exit code: $TEST_EXIT)"
        fi
    else
        echo "NOTE: python3 not available."
    fi
    echo ""
fi

if [ "$RAN_TESTS" = false ]; then
    if [ -z "$TEST_FILES" ]; then
        echo "No test files detected — nothing to run."
    else
        echo "Test files detected but test runner not recognized."
        echo "Test files:"
        echo -e "$TEST_FILES" | while read -r f; do [ -n "$f" ] && echo "  - $f"; done
    fi
fi

echo ""
echo "=== END TEST ANALYSIS ==="
