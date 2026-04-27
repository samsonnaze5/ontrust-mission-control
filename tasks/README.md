# Tasks

Lightweight task tracking for Claude (and humans) working in this mission-control repo. Two CSVs only: a queue (`inbox.csv`) and an archive (`done.csv`). All commands operate on these two files.

## Files

| File | Purpose |
|---|---|
| [`inbox.csv`](./inbox.csv) | Active task queue — work pending |
| [`done.csv`](./done.csv) | Completed / cancelled tasks — archive |

## Lifecycle

```
/task-add <description>
        |
        v
   inbox.csv ───── /task-discuss <id>  (refine in place)
        |
        +─── /task-do <id>      ──→ done.csv (commit + summary + retro)
        |
        +─── /task-cancel <id>  ──→ done.csv (commit=(cancelled) + reason)
        |
        +─── /task-skip <id>     (set skip flag, row stays in inbox)
        |
        +─── /task-list [scope]  (read-only summary)
```

| Command | Effect | Mutates |
|---|---|---|
| `/task-add <description>` | Append new row after Claude asks 2-3 clarifying questions and you approve a draft | `inbox.csv` |
| `/task-discuss <id>` | Walk a 6-section template (Goal / Scope / Success Criteria / Edge Cases / References / Constraints) and refine the row | `inbox.csv` |
| `/task-do <id>` | Run the task per [CLAUDE.md §8.2](../CLAUDE.md). Auto-moves row to `done.csv` on success | `inbox.csv`, `done.csv`, target repo |
| `/task-skip <id> <reason>` | Set the `skip` column. Row stays in inbox; Claude won't pick it up automatically | `inbox.csv` |
| `/task-cancel <id> [reason]` | Move row to `done.csv` with `commit=(cancelled)` and `summary=Cancelled: <reason>` | `inbox.csv`, `done.csv` |
| `/task-list [inbox\|done\|all]` | Summary view (default: `inbox`) | nothing — read-only |

## `inbox.csv` columns

| Column | Required | Description |
|---|---|---|
| `id` | yes | Random 12-char alphanumeric, mixing upper + lower + digit, avoiding ambiguous chars `0 O l 1 I`. Example: `Tk7mNp2VxQwR`. Must be unique across `inbox.csv` AND `done.csv` |
| `priority` | yes | `P0` / `P1` / `P2` / `P3` (see below) |
| `title` | yes | Action-oriented summary, ≤ 60 chars, English |
| `description` | yes | Full context including success criteria. English. See [CLAUDE.md §4](../CLAUDE.md) — must be a verifiable goal |
| `references` | no | Files / tickets / PR URLs / brainstorming sessions, separated by `;`. Example: `scripts/extract_schemas.py;CLAUDE.md#85;BL-017` |
| `notes` | no | Spawned-from / extra context. Example: `Spawned from brainstorming 2026-04-26 retrospective #28473` |
| `skip` | no | If non-empty, value is the reason Claude won't pick this row automatically. Set via `/task-skip` |

## `done.csv` columns

All `inbox.csv` columns **plus** these 5:

| Column | Required | Description |
|---|---|---|
| `completed_at` | yes | ISO date `YYYY-MM-DD` of completion |
| `commit` | yes | Target repo short SHA (7 chars) — OR `(cancelled)` if cancelled via `/task-cancel` |
| `summary` | yes | 1-2 sentences of what was done — OR `Cancelled: <reason>` if cancelled |
| `retro_refs` | no | Retrospective item ids from [CLAUDE.md §7](../CLAUDE.md), separated by `;`. Example: `#41827;#62094` |
| `drift_resolution` | no | One of `refreshed` / `proceed-stale` / `none` — captured during [CLAUDE.md §8.2](../CLAUDE.md) drift check |

## ID generation rules

- 12 characters, mixing upper + lower + digit
- Avoid `0 O l 1 I` (visually ambiguous when read aloud or copy-pasted)
- Examples: `Tk7mNp2VxQwR`, `xY9pQrZ4LmKt`
- Must NOT collide with any existing id in `inbox.csv` or `done.csv` (Claude verifies on `/task-add`)

## Priority guideline

| Level | When to use |
|---|---|
| `P0` | Production blocker, data loss, security incident — drop everything |
| `P1` | Blocks another task or person; finish this week |
| `P2` | Important but not urgent — within current sprint |
| `P3` | Backlog, nice-to-have, low-confidence ideas |

## Special row patterns

- **`[EXAMPLE]` prefix in `title`** — sample/template row that Claude will not touch. Used in `done.csv` to demonstrate the format. Delete once the project has real history.
- **`skip` column non-empty** — Claude will not pick the row up automatically. Even if you `/task-do <id>` directly, Claude will surface the skip reason and ask before overriding.
- **Header row (line 1)** — preserved across all edits. Never reorder or rename columns.

## CSV escaping rules

- A field containing `,`, `"`, or newline must be wrapped in `"…"`
- A literal `"` inside a wrapped field becomes `""`
- All commands use the `Edit` tool (not `echo` / `printf`) to preserve formatting

## Drift between artifact and target repo

When `/task-do <id>` runs, Claude follows [CLAUDE.md §8.2](../CLAUDE.md) and checks whether the artifact `_meta.csv` matches the target repo's current commit. The decision (`refreshed` / `proceed-stale` / `none`) is recorded in the `drift_resolution` column of the eventual `done.csv` row.

## See also

- [CLAUDE.md §8.2](../CLAUDE.md) — Task Bootup Procedure (the canonical execution flow for `/task-do`)
- [CLAUDE.md §7](../CLAUDE.md) — End-of-Task Retrospective format (defines `retro_refs` ids)
- [artifacts/INDEX.md](../artifacts/INDEX.md) — Artifact registry that tasks usually reference
- [.claude/commands/](../.claude/commands/) — Source of all task-* slash commands
