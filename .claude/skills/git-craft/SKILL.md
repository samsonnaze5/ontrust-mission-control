---
name: git-craft
description: >
  Git workflow assistant that crafts high-quality commit messages, PR descriptions, and
  reverse-engineered ClickUp tickets. Use this skill whenever the user wants to: generate
  commit messages, split changes into logical commits, write pull request descriptions,
  prepare a PR, review uncommitted changes, organize git history, create tickets from code
  changes, or anything related to "commit", "PR", "pull request", "merge request",
  "git message", "git description", "ticket", "task", "ClickUp". Also trigger when the user
  says things like "ช่วยเขียน commit", "เตรียม PR", "แบ่ง commit", "สรุปการเปลี่ยนแปลง",
  "เขียน PR description", "สร้าง ticket", "เขียน ticket ให้หน่อย", or mentions preparing
  changes for code review. Even casual requests like "commit นี้ตั้งชื่อว่าอะไรดี",
  "เตรียม PR ให้หน่อย", or "สร้าง ticket จาก PR นี้" should trigger this skill.
---

# git-craft

A Git workflow skill that does three things well:
1. **Commit Craft** — Analyzes uncommitted changes, suggests well-named commits (using Conventional Commits), and splits them logically when needed. Outputs ready-to-run git commands.
2. **PR Craft** — Analyzes the current feature branch against its base, then writes a detailed, consistent PR description in Thai with a standardized template.
3. **Ticket Craft** — Reverse-engineers a PR description back into a ClickUp-style ticket with sub-tasks, acceptance criteria, and story points. Useful when developers write code before PM/PO creates the ticket.

All modes output markdown files to the `outputs/` folder so the user can review before taking action. The skill never auto-commits or auto-pushes — it only produces recommendations and ready-to-use commands.

## Output Directory

**ทุก output ต้องถูก save ที่ `<project-root>/outputs/` เสมอ** (absolute path: `{PROJECT_ROOT}/outputs/`)

| Mode         | Output File                                |
|--------------|--------------------------------------------|
| Commit Craft | `<project-root>/outputs/commit-plan.md`    |
| PR Craft     | `<project-root>/outputs/pr-description.md` |
| Ticket Craft | `<project-root>/outputs/ticket.md`         |

**ห้าม** save output ไว้ใน `.claude/skills/git-craft/outputs/` หรือที่อื่น — ต้องอยู่ใน `<project-root>/outputs/` เท่านั้น สร้าง folder ถ้ายังไม่มี

## Emoji Policy

**ต้องใส่ emoji ตาม template เสมอ** — PR template (`references/pr-template.md`) มี emoji ในทุก section header (เช่น 📋, 🔗, 🎯, 💡, ⚠️, 🧪, 📸, 💥, 🔐 ฯลฯ) ให้คง emoji ไว้ตาม template ทุกครั้ง ห้ามตัดออก เพราะ emoji เป็นส่วนหนึ่งของ template format ไม่ใช่การตกแต่ง

## How It Works

This skill bundles shell scripts that do the heavy lifting of gathering git data. This is important because running `git diff`, `git log`, and `git status` can produce a lot of output — by using scripts to pre-process and summarize the data, we avoid flooding the context with raw diffs and save tokens significantly.

### Available Scripts

All scripts are in the `scripts/` directory relative to this skill file. Run them with `bash`:

| Script                      | Purpose                                                                                            |
|-----------------------------|----------------------------------------------------------------------------------------------------|
| `collect_uncommitted.sh`    | Gathers all uncommitted changes: file list, diff stats, and abbreviated diffs grouped by directory |
| `collect_branch_changes.sh` | Gathers all changes on the current branch vs base branch: commits, file stats, and diffs           |
| `detect_change_groups.sh`   | Analyzes uncommitted files and suggests logical groupings for splitting into multiple commits      |
| `collect_test_results.sh`   | Detects test files in branch changes, runs them if possible, and reports results + coverage gaps   |

---

## Mode 1: Commit Craft

Use this mode when the user wants to generate commit messages for uncommitted changes.

### Step-by-step process

1. **Run the collection script** to gather uncommitted change data:
   ```bash
   bash <skill-path>/scripts/collect_uncommitted.sh
   ```
   This outputs a structured summary of all staged and unstaged changes, including file paths, change types (added/modified/deleted), line counts, and abbreviated diffs.

2. **Run the grouping script** if the changes look like they span multiple concerns:
   ```bash
   bash <skill-path>/scripts/detect_change_groups.sh
   ```
   This script analyzes the file paths and diff content to suggest logical groups. It looks at directory structure, file types, and common patterns (e.g., test files grouped with their source files, migration files grouped together).

3. **Analyze the output** and determine:
   - How many commits are appropriate? A single coherent change = 1 commit. Multiple unrelated changes = split into logical commits.
   - What is the scope of each commit? Look at which module/package/feature area the files belong to.
   - What type is each commit? Map to Conventional Commits types.

4. **Generate the commit plan** as a markdown file at the output path.

### Conventional Commits Format

Every commit message follows this pattern:
```
type(scope): short description in imperative mood
```

**Types** (in order of frequency):
- `feat` — A new feature or capability
- `fix` — A bug fix
- `refactor` — Code restructuring without changing behavior
- `docs` — Documentation changes only
- `test` — Adding or updating tests
- `chore` — Maintenance tasks (deps, configs, CI)
- `style` — Formatting, whitespace, linting (no logic change)
- `perf` — Performance improvements
- `ci` — CI/CD pipeline changes
- `build` — Build system or dependency changes

**Scope** is derived from the primary module, package, or feature area affected. For example:
- Files in `src/auth/` → scope is `auth`
- Files in `internal/api/handler/` → scope is `api` or `handler` depending on specificity
- Files in `cmd/server/` → scope is `server`
- Multiple areas → use the most prominent one, or omit scope if truly cross-cutting

**Description** guidelines:
- Use imperative mood: "add", "fix", "update" — not "added", "fixes", "updated"
- Keep under 72 characters
- Be specific: "add JWT refresh token rotation" not "update auth"
- No period at the end

### Deciding When to Split Commits

Split when changes serve genuinely different purposes. Here's the mental model:

**One commit** when:
- All changes work toward a single goal (e.g., adding a new endpoint including its handler, route, tests, and docs)
- Changes are so intertwined that splitting would leave individual commits in a broken state

**Multiple commits** when:
- There's a mix of feature work and unrelated fixes
- Refactoring was done as groundwork before the actual feature
- Test additions are independent of the feature (e.g., backfilling tests for existing code)
- Configuration/infrastructure changes are separate from application logic

The goal is that each commit can be understood on its own and, ideally, could be reverted independently without breaking things.

### Output Format for Commit Craft

Generate a markdown file with this structure:

```markdown
# Git Commit Plan

> Generated by git-craft | <current date>
> Branch: `<current-branch>`
> Total files changed: <N> | Total commits suggested: <M>

---

## Commit 1 of M: `type(scope): description`

**Reason:** Brief explanation of why these files are grouped together.

**Files:**
| File | Status | Changes |
|------|--------|---------|
| path/to/file1.go | Modified | +25 -10 |
| path/to/file2.go | Added | +80 -0 |

**Commands:**
\`\`\`bash
git add path/to/file1.go path/to/file2.go
git commit -m "type(scope): description"
\`\`\`

---

## Commit 2 of M: `type(scope): description`

... (same structure)

---

## Quick Run (All Commits)

Copy-paste this entire block to execute all commits in sequence:

\`\`\`bash
# Commit 1: type(scope): description
git add path/to/file1.go path/to/file2.go
git commit -m "type(scope): description"

# Commit 2: type(scope): description
git add path/to/file3.go
git commit -m "type(scope): description"
\`\`\`
```

Save this file to `./outputs/commit-plan.md`. Create the `outputs/` directory if it doesn't exist.

---

## Mode 2: PR Craft

Use this mode when the user wants to generate a PR description for the current branch.

### Step-by-step process

1. **Run the branch analysis script**:
   ```bash
   bash <skill-path>/scripts/collect_branch_changes.sh [base-branch]
   ```
   If no base branch is specified, the script auto-detects it (tries `develop` first, then `main`, then `master`).

   This outputs: branch name, base branch, commit list, file change summary, and abbreviated diffs.

2. **Read the PR template** from the references directory:
   ```bash
   cat <skill-path>/references/pr-template.md
   ```
   This template defines the exact structure and sections that every PR description must follow.

3. **Analyze the collected data** and fill in the template. The key thinking process:
   - Look at the branch name to understand intent (e.g., `feature/add-user-auth` → adding user authentication)
   - Read through commit messages chronologically to understand the development story
   - Examine the diff summary to understand scope and impact
   - Consider what could break and what dependencies are affected

4. **Run the test analysis script** to detect and run tests:
   ```bash
   bash <skill-path>/scripts/collect_test_results.sh [repo-path] [base-branch]
   ```
   This script does three things:
   - Detects test files that were changed or added in the branch (supports Go, TypeScript/JavaScript, Python, Java, Rust)
   - Attempts to run the tests automatically if the test runner is available
   - Reports which source files lack test coverage and recommends what to add

   The output is used to populate the "ผลการทดสอบ (Testing Results)" and "Screenshots / Evidence" sections in the PR description.

5. **Generate the PR description** using the template, writing all narrative sections in Thai.

### PR Description Rules

- **Language**: All narrative text in Thai. Technical terms (function names, file paths, API endpoints) stay in English.
- **Consistency**: Always follow the template structure from `references/pr-template.md` exactly. Never skip sections — if a section doesn't apply, write "ไม่มี" (N/A) instead.
- **Depth**: Each section should have enough detail that a reviewer who hasn't seen the code can understand the context. Don't just list what changed — explain *why* it changed.
- **Breaking Changes**: If the branch name starts with a type that suggests breaking changes (e.g., major refactoring), or if the diffs show API signature changes, removed exports, or schema migrations, always fill in the Breaking Changes section.
- **Testing Results**: Always run `collect_test_results.sh` and use its output to fill the Testing Results section. If tests pass, show the summary. If tests fail, highlight failures. If no tests exist, recommend specific tests to add based on what source files changed.
- **Screenshots**: Analyze the type of changes to generate smart placeholder suggestions. For API changes suggest curl output screenshots, for UI changes suggest before/after, for DB changes suggest migration output. Don't just write "ไม่มี" — write actionable placeholders like `> 📸 **TODO:** เพิ่ม screenshot แสดง response จาก GET /api/users endpoint`.
- **Improvement Suggestions**: After filling in all other sections, step back and look at the code changes with fresh eyes — as if you're a senior engineer reviewing this PR. Analyze the actual diffs (not just summaries) and provide concrete recommendations split into "ควรทำ" (should do — prevents real problems) and "น่าทำ" (nice to have — makes things cleaner). Every suggestion must reference specific files, functions, or patterns from the actual changes. Avoid generic advice like "add more tests" — instead write "ควรเพิ่ม test case สำหรับ expired token ใน `jwt_test.go` เพราะตอนนี้ test แค่ happy path".
- **Penetration Testing Suggestions**: Analyze the code changes to identify real attack surfaces. Think about what a pentester would try if they saw these changes deployed. Fill in the "Attack Surfaces" table with specific endpoints/functions from the PR, the type of risk, priority, and a brief test method. For example, if the PR adds JWT auth, suggest testing for token forgery, expired token bypass, missing auth on endpoints, etc. Keep it grounded in the actual code — not a generic OWASP checklist.
- **Diagrams**: วิเคราะห์ code changes แล้วเลือก 1-3 Mermaid diagram types ที่เหมาะสมที่สุด: **Flowchart** (business logic, decision flows), **Sequence Diagram** (API call chains, auth flows, multi-component communication), **User Journey** (user-facing features, UX flows), **Mindmap** (changes กระจายหลาย modules), **Architecture Diagram** (structural changes, new modules). ทุก diagram ต้องมี title + คำอธิบาย + Mermaid code block ใช้ภาษาอังกฤษสำหรับ labels Keep diagrams concise (ไม่เกิน 15-20 nodes) ถ้า changes เป็นแค่ config/docs/style → เขียน "ไม่มี"
- **Test Case Scenario Suggestions**: Act as a QA Lead and analyze the code changes to recommend test cases that a QA/Tester should execute for maximum coverage. Split into three categories: **High Priority** (5-10 cases — happy path of new features, critical business logic flows), **Regression** (3-5 cases — existing features that might break based on Impact Analysis), and **Edge Cases** (3-5 cases — boundary conditions, null/empty inputs, concurrent requests, permission boundaries). Every test case must reference a specific endpoint/function from the actual changes, include clear reproducible steps, and have a verifiable expected result. Think like a QA Lead: "If I only have 1 hour to test this PR, what do I test first?" Priority levels: 🔴 = must test before merge, 🟠 = should test, 🟡 = nice to have.

### Output Format for PR Craft

The PR description is generated from the template in `references/pr-template.md`. Save the completed description to `./outputs/pr-description.md`. Create the `outputs/` directory if it doesn't exist.

---

## Mode 3: Ticket Craft

Use this mode when the user wants to generate a ClickUp ticket from the current branch's changes. This is the "reverse-engineering" mode — it takes what developers have already built and works backward to produce the ticket that a PM/PO would normally write *before* development starts.

This is common in fast-moving teams where developers ship first and documentation catches up later. The goal is to produce a ticket that's good enough for PM/PO to review, adjust, and drop straight into ClickUp.

### Step-by-step process

1. **Check if a PR description already exists.** If the user already ran PR Craft in this session (or there's a `pr-description.md` in the outputs folder), use it as the primary input. This avoids re-analyzing the same data.

2. **If no PR description exists, run the PR Craft pipeline first** (steps 1-4 from Mode 2) to gather all the branch analysis data. You don't need to save a separate `pr-description.md` — just use the analysis internally.

3. **Read the ticket template**:
   ```bash
   cat <skill-path>/references/ticket-template.md
   ```
   This template defines the ClickUp ticket structure and contains guidelines for reverse-engineering each section from the PR data.

4. **Reverse-engineer the ticket** by transforming PR-oriented information into PM/PO-oriented information. The key mental shift:
   - PR description explains *what code changed and why* (developer audience)
   - Ticket explains *what needs to be done and what success looks like* (PM/PO audience)

   Specific transformations:
   - **Branch prefix** → Ticket Type (`feature/*` → Feature, `fix/*` → Bug Fix, etc.)
   - **PR "ถ้าไม่ทำจะเป็นยังไง" + Breaking Changes** → Priority estimation
   - **PR file count + complexity** → Story Points estimation
   - **PR "วัตถุประสงค์" + "วิธีการทดสอบ"** → Acceptance Criteria
   - **PR "รายละเอียดการเปลี่ยนแปลง" grouped by module** → Sub-Tasks
   - **Commit scopes + file directories** → Labels/Tags
   - **PR "ผลกระทบ"** → Dependencies

5. **Write sub-tasks** by analyzing the changes grouped by module/concern. Each distinct area of change becomes a sub-task. The breakdown should follow the same logic as commit splitting:
   - Auth/security changes → separate sub-task
   - API endpoint changes → separate sub-task
   - Database migrations → separate sub-task (always, because deploy order matters)
   - Test additions → separate sub-task (if substantial)
   - Documentation → separate sub-task (if substantial)

6. **Generate the ticket** as a markdown file.

### Ticket Writing Rules

- **Language**: All text in Thai, technical terms stay in English (consistent with PR description language).
- **Tone**: Write from PM/PO perspective, not developer perspective. Focus on "what" and "why", minimize "how". Business stakeholders should understand the Description and Objective sections without needing to read code.
- **Acceptance Criteria**: Must be testable and verifiable. Each criterion should be a yes/no question. Derive from PR's "วิธีการทดสอบ" and "วัตถุประสงค์" sections.
- **Sub-Tasks**: Each sub-task should have clear scope and be independently completable. Include related file paths so developers know exactly where to work.
- **Story Points**: Be honest — if the PR is complex, give it a high number. Better to overestimate than underestimate.
- **Consistency**: Always follow the template from `references/ticket-template.md`.

### Output Format for Ticket Craft

Save the completed ticket to `./outputs/ticket.md`. Create the `outputs/` directory if it doesn't exist.

### When to Auto-Chain with PR Craft

If the user asks for "PR description + ticket" or "เตรียม PR แล้วสร้าง ticket ด้วย", run Mode 2 first, save `pr-description.md`, then immediately run Mode 3 using that PR description as input. This produces both files in a single workflow.

---

## Handling Edge Cases

**Empty working directory (no changes):**
If there are no uncommitted changes for Commit Craft, or no branch differences for PR Craft, output a markdown file explaining the situation clearly instead of an empty template.

**Very large changesets (50+ files):**
The scripts already truncate diffs for large files. Focus on the summary statistics and directory-level patterns rather than individual file diffs. Group by directory or module and describe changes at a higher level.

**Merge commits in branch history:**
The branch analysis script filters out merge commits by default to keep the signal clean. The PR description should reflect the actual work done, not merge noise.

**Detached HEAD or unusual git states:**
If the scripts detect an unusual git state, they'll output a warning. Relay this warning to the user and suggest resolving it before proceeding.
