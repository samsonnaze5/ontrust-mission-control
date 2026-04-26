# Ontrust Mission Control

Centralized artifact hub for Ontrust backend services.
**Mission:** enable Claude/AI to write & edit code in any backend service
without re-exploring the project from scratch.

## What this is

A read-only knowledge base that mirrors:

- DB schemas + enums (auto-extracted from live DBs and Go source)
- Service registry, env vars, infrastructure inventory
- Code conventions per service (human-curated)
- Active task queue for AI work

## What this is NOT

- Not a place to write or commit application code (that lives in target repos)
- Not a project management tool (use Linear/Jira for tickets)
- Not a wiki for humans — it's primarily for AI coding agents.
  Humans benefit secondarily.

## Architecture

```
┌──────────────────────────────────┐
│ ontrust-mission-control (this)   │
│  artifacts/   (read-only index)  │
│  tasks/       (work queue)       │
│  scripts/     (extractors)       │
│  CLAUDE.md    (operating manual) │
└──────────────┬───────────────────┘
               │ Claude reads here first
               ▼
┌──────────────────────────────────┐
│ Target repos (writable)          │
│  ├ onetrust-mt5-processor        │
│  ├ onetrust-financial-service    │
│  ├ onetrust-archived             │
│  ├ onetrust-client-portal-api    │
│  ├ onetrust-mt5-proxy-api        │
│  └ aeternixth-go-lib             │
└──────────────────────────────────┘
```

## Quick Status

- Inbox queue: [`tasks/inbox.csv`](./tasks/inbox.csv)
- Recent work: [`tasks/done.csv`](./tasks/done.csv)
- Full artifact index: [`artifacts/INDEX.md`](./artifacts/INDEX.md)

## For Claude / AI Agents

Read in this order when given a task:

1. [`artifacts/INDEX.md`](./artifacts/INDEX.md) — find what artifacts apply
2. [`artifacts/services.csv`](./artifacts/services.csv) — confirm target repo path + branch
3. `artifacts/conventions/<service>/*.md` — code style for that service
4. `artifacts/schemas/<db>/` — only the DBs involved
5. Target repo's own `CLAUDE.md` / `AGENTS.md` (if present)

For the full task bootup procedure (drift check, refresh policy, scope rules)
see [CLAUDE.md §8 "Mission Control Operating Manual"](./CLAUDE.md).

## For Humans

### Adding a task for Claude

Append a row to `tasks/inbox.csv` with:

- `id` — short unique identifier
- `priority` — P0 / P1 / P2 / P3
- `title` — 1-line summary
- `description` — what + which service + acceptance criteria
- `references` — file paths, ticket IDs, related artifacts
- `notes` — optional context for Claude or humans
- `skip` — set to non-empty to make Claude ignore the row

### Verifying Claude's work

1. Check `tasks/done.csv` — Claude logs commit SHA + summary per task
2. Review the commit in the target repo
3. Check `artifacts/<set>/_meta.csv` to see what got refreshed

### Onboarding a new service

1. Add row to `artifacts/services.csv` (service, path, default_branch, description)
2. Add row to `artifacts/databases.csv` if it owns DBs
3. Bootstrap `artifacts/conventions/<service>/` (or copy from a similar service)
4. Run `task schemas:refresh` to pull initial schema

## Setup (humans, first time)

```bash
# 1. install task CLI (https://taskfile.dev)
brew install go-task

# 2. python deps for extractors
task schemas:install

# 3. .env (ask repo owner for the secret values)
cp .env.example .env

# 4. list available tasks
task
```

## Artifact Taxonomy

| Type | Path | Refresh trigger |
|---|---|---|
| Service registry | `artifacts/services.csv` | manual |
| DB registry | `artifacts/databases.csv` | manual |
| Env vars catalog | `artifacts/envs.csv` | manual |
| DB schemas | `artifacts/schemas/<db>/` | `task schemas:refresh` |
| Enums | `artifacts/schemas/<db>/enums/` | `task enums:extract` |
| Pipeline docs | `artifacts/<pipeline>/` | manual |
| Conventions | `artifacts/conventions/<service>/` | human review |
| Infrastructure | `artifacts-infra/` | manual |
| Tasks | `tasks/{inbox,done}.csv` | continuous |

See [`artifacts/INDEX.md`](./artifacts/INDEX.md) for the per-file inventory.

## Glossary

| Term | Meaning |
|---|---|
| Mission Control | This repo — central artifact hub |
| Target repo | An external backend repo where actual code is written |
| Artifact | Any indexed knowledge file (CSV / MD) here |
| Drift | Mismatch between an artifact and its source-of-truth |
| Refresh | Re-extracting an artifact from its source |
| MT5 | MetaTrader 5 (trading platform integration) |
| PSP | Payment Service Provider |
| IB | Introducing Broker (commission/rebate calculations) |

## Status & Privacy

This repo is **private** — it contains internal paths, service taxonomy,
and DB structure of Ontrust backend. Do **not** push to public mirrors.

---

For behavioral guidelines and the full operating manual,
see [CLAUDE.md](./CLAUDE.md).
