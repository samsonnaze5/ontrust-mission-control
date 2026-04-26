# Brainstorming Session — 2026-04-26

**Topic:** Create README.md + update CLAUDE.md for `ontrust-mission-control`
**Approach:** Full BMAD divergent (4 rounds, ~80 ideas)
**Facilitator:** Claude (Opus 4.7)
**Owner:** Kittiphong

---

## Session Overview

Goals:

1. Draft a README.md that serves 4 personas (owner, team, Claude, outsider)
2. Update CLAUDE.md from generic behavioral guide → Mission Control operating manual
3. Establish artifact taxonomy + lifecycle protocols

Project context: `ontrust-mission-control` is a centralized artifact hub
for 6 backend repos. Claude reads artifacts here, then writes code in
target repos via absolute paths from `services.csv`.

---

## Round 1: First Principles

**Method:** Peel layers of "why this exists" to find irreducible truth.

### Core Truth (3 layers deep)

| Layer | Truth |
|---|---|
| WHAT | Claude must be able to write/edit code in any service without re-exploring |
| WHY | Quality — Claude misses convention → revise multiple rounds |
| HOW | Via 4 conventions that hurt most: Dependencies, Structure, Logging, Testing |

### Convention source-of-truth audit

| Convention | Where it lives today | Strategy |
|---|---|---|
| Dependencies | `go.mod` + tribal knowledge | Semi-extract from `go.mod` + interview |
| Structure | tribal only | Elicit + verify from code |
| Logging | tribal only | Elicit + verify from code |
| Testing | does not exist yet | DESIGN from scratch (separate session) |

### Mental model shift

Mission Control is **NOT** just a "knowledge cache" — it is a
**"convention authority"** that operates in 2 modes:

1. **Cache** existing knowledge (schemas, enums)
2. **Incubate** new conventions (testing, structure, logging)

---

## Round 2: Persona-Based Brainstorming

**Method:** 4 personas each ask "what do I need?" + "what do I never want?"

### 4 personas mapped

| Persona | Top question | Format that works |
|---|---|---|
| P1 — Owner (Monday morning) | "What's pending? What changed last week?" | Dashboard / status table |
| P2 — Team dev (day 1) | "Tool or codebase? My role?" | What/Why/Your role + diagram |
| P3 — Claude (fresh session) | "Which artifacts to read for task X in service Y?" | Decision tree / lookup table |
| P4 — Outsider (60s scan) | "Problem solved? Production-grade?" | Elevator pitch + visible signals |

### Critical insight

Claude (P3) is the **primary** persona per Round 1 truth. README + CLAUDE.md
must be optimized for AI consumption first; humans benefit secondarily.

### Derived sections

- **README** → 8 sections: pitch, status, what/not, architecture, Claude path,
  human workflow, taxonomy, setup, glossary, privacy
- **CLAUDE.md** → add "Mission Control Operating Manual" as §8 with 7 sub-sections

---

## Round 3: Reverse Brainstorming

**Method:** Generate 30+ failure modes → invert to rules.

### 7 failure clusters (40 modes total)

1. Stale & wrong artifacts (trust collapse)
2. Information overload (Claude can't find what matters)
3. Convention drift (rules vs reality)
4. Concurrency / multi-session conflicts
5. Path / scope confusion
6. Onboarding cliff
7. Catastrophic events

### 30 inverted rules

Grouped under 7 categories: A (Trust), B (Conciseness), C (Convention),
D (Concurrency), E (Path), F (Onboarding), G (Catastrophe).
Full list captured in CLAUDE.md §8 + Convergence MoSCoW below.

### Cross-cutting insight

Some rules belong in CLAUDE.md (behavior); others belong in
scripts/CI (enforcement). Splitting them prevents over-relying on
Claude trust for things that should be mechanically guarded.

---

## Round 4: What If Scenarios

**Method:** Walk artifact lifecycle (drift → trigger → execution → validation
→ convention drift → catastrophe) → derive contracts.

### 30 what-if scenarios across 6 lifecycle phases

(Full list in session transcript.)

### 10 derived protocols

| Protocol | Subject |
|---|---|
| P-A | Drift Detection at Task Start (the keystone — runs before every task) |
| P-B | Refresh Granularity (command grammar) |
| P-C | Snapshot + Diff (atomic refresh) |
| P-D | Branch Discipline (default_branch verification) |
| P-E | Schema Source-of-Truth (live DB vs migrations folder) |
| P-F | Partial Failure Protocol (per-table status, no silent skip) |
| P-G | Cross-Session Cache Invalidation |
| P-H | Convention Drift Detection (status, applies_to, exceptions) |
| P-I | Rollback (snapshot history) |
| P-J | Catastrophic Recovery (archived flag, remote backup) |

### Two big insights

- **Insight #7:** Refresh is not an event — it is the **standard task bootup
  procedure**. Every task starts with drift check (P-A).
- **Insight #8:** Conventions have a different lifecycle than data —
  human-curated, never auto-updated. Must be treated separately from
  schema-style auto-extracted artifacts.

---

## Convergence — MoSCoW Triage

### MUST (v1, shipped this session)

| # | Item | Status |
|---|---|---|
| M1 | README.md (8 sections) | done |
| M2 | CLAUDE.md §8 "Mission Control Operating Manual" | done |
| M3 | CLAUDE.md §9 "Files to Read at Session Start" | done |
| M4 | Task Bootup Procedure (P-A) | done — in §8.2 |
| M5 | Refresh Granularity (P-B) | done — in §8.6 |
| M6 | Path/Scope Discipline | done — in §8.3 |
| M7 | Convention Authority — STOP & ASK if conflict | done — in §8.4 |
| M8 | Testing — STOP & ASK guard rail | done — in §8.5 |
| M9 | Auto-refreshable vs Human-curated distinction | done — in §8.7 |
| M10 | `artifacts/INDEX.md` | done |
| M11 | `AGENTS.md` → 1-line stub pointing to CLAUDE.md | done |
| M12 | `tasks/inbox.csv` row for testing convention | done — `EST-TEST-001` |

### SHOULD (v2 backlog)

- S1 — `default_branch`, `repo_url`, `language` columns in services.csv
- S2 — `_meta.csv` infrastructure + populate existing artifact sets
- S3 — `_schema.md` per CSV (column descriptions)
- S4 — `artifacts/GLOSSARY.md` (currently inline in README)
- S5 — Per-service convention skeletons in `artifacts/conventions/<service>/`
- S6 — `assigned_to`, `status` columns in `inbox.csv`
- S7 — Snapshot + diff script (P-C)

### COULD (v3 backlog)

- C1 — Atomic write protocol + secret regex pre-commit check
- C2 — Schema split: `live/` vs `migrations/` (P-E)
- C3 — Rollback command (P-I)
- C4 — Per-service convention drift cross-check
- C5 — Convention status flags (stable / draft / deprecated)
- C6 — File lock for extract scripts (D16)

### WON'T (out of scope)

- W1 — CI/CD pipeline (separate effort)
- W2 — Web UI / dashboard
- W3 — Slack notifications
- W4 — Multi-instance sync (assume single user)

---

## Outputs

- `README.md` — created (top-level)
- `CLAUDE.md` — added §8 (Mission Control Operating Manual) and §9
- `AGENTS.md` — replaced with stub pointing to CLAUDE.md
- `tasks/inbox.csv` — appended row `Tk7mNp2VxQwR` (EST-TEST-001)
- `artifacts/INDEX.md` — created
- `docs/brainstorming-session-2026-04-26.md` — this file

---

## Key Insights (saved for future sessions)

1. Mission Control is a **convention authority**, not just a knowledge cache.
2. Claude is the **primary persona**; humans are secondary readers.
3. Refresh is not an event — it is the **standard task bootup procedure**.
4. Conventions have a different lifecycle than data (human-curated vs auto).
5. Some rules belong in CLAUDE.md (behavior); others belong in scripts/CI
   (enforcement). Don't conflate.
