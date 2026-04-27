---
name: git-craft-v2
description: >
  Optimized PR description generator (v2). Analyzes feature branch changes and generates
  detailed PR descriptions in Thai. Uses a single fast script and slim template to minimize
  tokens and maximize speed. Trigger: "เตรียม PR", "เขียน PR", "PR description", "git-pr-2".
---

# git-craft-v2 — PR Craft (Optimized)

Generates PR descriptions from feature branch analysis. Optimized for speed and token efficiency.

## Output

Save to `<project-root>/outputs/pr-description.md` (create `outputs/` if needed).

## Process

1. **Run fast collection script** (1 script replaces 2):
   ```bash
   bash <skill-path>/scripts/collect_pr_fast.sh [base-branch]
   ```
   This gathers: commits, file changes, breaking indicators, filtered diffs, and test file detection — all in one pass with minimal git calls.

2. **Read skeleton template**:
   ```bash
   cat <skill-path>/references/pr-template-skeleton.md
   ```

3. **Fill every section** using the writing rules below. Never skip sections — write "ไม่มี" if not applicable.

4. **Save** to `./outputs/pr-description.md`.

## Writing Rules

**Language**: Thai narrative + English technical terms. Emoji headers must be preserved from template.

### Section Guidelines (condensed)

- **Summary**: 2-3 sentences max. Elevator pitch.
- **Background**: Story before this PR. Link issues/tickets if available.
- **Objective**: Specific, measurable. Not "ปรับปรุงระบบ" but "เพิ่ม X เพื่อ Y".
- **Motivation**: The deeper "why" — what problem drove this solution.
- **Purpose & Value**: Outcome focus. What the team/product gains.
- **Risk of Not Doing**: Concrete impact. Numbers if possible.
- **Changes Detail**: Group by module. Explain what + why, not just list files.
- **Diagrams**: 1-3 Mermaid diagrams. Pick from: Flowchart, Sequence, User Journey, Mindmap, Architecture. English labels, max 15-20 nodes. Skip for config/docs changes.
- **Impact Analysis**: Direct + indirect effects on downstream services, DB, API consumers.
- **Breaking Changes**: Fill if script detected indicators. Include migration steps.
- **How to Test**: Clear, reproducible steps with commands/endpoints.
- **Testing Results**: Use test file data from script. If no tests → mark 📝 + recommend specific tests.
- **Screenshots**: Smart placeholders based on change type (API→curl, UI→before/after, DB→migration).
- **Improvement Suggestions**: Act as senior engineer. 3-5 items per level (ควรทำ/น่าทำ). Reference specific files/functions. Each item includes `<details>` AI prompt with Target/Action/Context/Dependencies.
- **Pentest Suggestions**: 3-6 attack surfaces grounded in actual changes. Priority 🔴/🟠/🟡. Each 🔴/🟠 gets `<details>` AI prompt.
- **Test Cases**: High Priority (5-10), Regression (3-5), Edge Cases (3-5). Each with `<details>` AI prompt block.

### AI Prompt Format (for Improvement/Security/Test `<details>` blocks)

```
**── Base ──**
- **Target:** `path/file.go` → `func Name()` (lines X-Y)
- **Action:** [refactor|add-test|fix-security|optimize]
- **Context:** what the code does + why it needs change
- **Dependencies:** related files/interfaces

**── Extension ──**  (pick one: Improvement/Security/Test)
- Improvement: ImprovementType, CurrentBehavior, DesiredBehavior
- Security: VulnerabilityType (OWASP), AttackVector, Severity, Remediation
- Test: TestType, Framework, Scenarios (✅❌🔲), Mocking code, Assertions code

**── Execution Protocol ──**
1. Read target → verify finding exists
2. Implement fix/change
3. If not found → skip with explanation
4. Run `task format`
5. Verify no regression

**── Validation Checklist ──**
- [ ] specific verifiable conditions
```
