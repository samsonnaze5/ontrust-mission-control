# Artifact Index

Top-level pointer to all knowledge files in mission-control.
Claude reads this **first** per [CLAUDE.md §8.2 step 3a](../CLAUDE.md).

## Registries (manual edit)

| File | Purpose |
|---|---|
| [`services.csv`](./services.csv) | Backend services + absolute paths |
| [`databases.csv`](./databases.csv) | Logical databases + env prefixes |
| [`envs.csv`](./envs.csv) | Env var catalog (names only — no values) |
| [`ignore.csv`](./ignore.csv) | Paths to skip during code scans |
| [`environments.csv`](./environments.csv) | Deployment environments (DEV/SIT/UAT/PROD) + promotion order + infra stack links |
| [`release-workflow.csv`](./release-workflow.csv) | Git branch ↔ environment ↔ CI/CD mapping; release process + approval gates |

## DB Schemas (auto-extracted)

- Source: live PostgreSQL/ClickHouse via `task schemas:refresh`
- Source: Go code parsing via `task enums:extract`

| DB | Path | Notes |
|---|---|---|
| crm_central | `schemas/crm_central/` | master data |
| balance | `schemas/balance/` | account balance |
| crm_trading_open | `schemas/crm_trading_open/` | open positions |
| crm_trading_closed | `schemas/crm_trading_closed/` | closed positions |
| crm_trading_complete | `schemas/crm_trading_complete/` | completed trades |
| crm_financial | `schemas/crm_financial/` | financial transactions |
| clickhouse_client | `schemas/clickhouse_client/` | client analytics |
| clickhouse_ib | `schemas/clickhouse_ib/` | IB analytics |

Per-DB structure:

- `_index.csv` — extraction status (host, port, table count, errors)
- `_tables.csv` — all tables overview (row estimates, sizes)
- `_indexes.csv`, `_foreign_keys.csv`, `_constraints.csv`
- `tables/<table>.csv` — column-level detail per table
- `enums/<table>.csv` — enum constants per table

## Pipeline Docs (manual)

| Pipeline | Path | Status |
|---|---|---|
| MT5 Balance | `mt5-balance-pipeline/` | documented |
| MT5 Deal | `mt5-deal-pipeline/` | documented |
| (other services) | TBD | not yet documented |

Per-pipeline files: `nfr.csv`, `flow.csv`, `backlog-functional.csv`,
`backlog-nonfunctional.csv`, `kafka-*.csv`, `messages/`, `edge-cases.csv`

## Code Conventions (human-curated, NOT YET POPULATED)

Path: `conventions/<service>/{dependencies,structure,logging,testing}.md`

Status: skeleton to be created. See `tasks/inbox.csv` task `EST-TEST-001`
for testing convention; the other 3 conventions (dependencies, structure,
logging) need similar planning sessions before population.

When populated, Claude **must** read these before writing code in that
service per [CLAUDE.md §8.4](../CLAUDE.md).

## Infrastructure (separate root)

`../artifacts-infra/`

- `_index.csv` — Terraform stacks (8 entries: prd, eu-west-2, deploy-base,
  deploy-overlays, kubeflow-manifests, ci-jenkins, ci-github-actions)
- `terraform-modules.csv` — 19 reusable modules

## Glossary

See [README.md → Glossary](../README.md#glossary) for term definitions
(MT5, PSP, IB, Drift, Refresh, etc.).

## Freshness

Each artifact set should have `_meta.csv` with:

- `last_extracted_at` (ISO timestamp)
- `extracted_by` (one of: `user` / `claude` / `ci` / `bootstrap` — see semantics below)
- `source_commit_sha` (target repo's HEAD at extraction time)
- `source_repo` (which target repo owns this artifact set)
- `source_branch` (typically `main`)
- `notes` (freeform — migration context, partial-failure flags, etc.)

**`extracted_by` enum semantics:**

| Value | Meaning |
|---|---|
| `user` | The human owner ran the extractor manually |
| `claude` | Claude ran the extractor as part of a task (auto-refresh on schema change) |
| `ci` | Scheduled CI job ran the extractor (future — not yet implemented) |
| `bootstrap` | Placeholder row from initial setup; SHA is `EXAMPLE_*` and must be replaced on first real refresh |

**Status:** `_meta.csv` exists for **all 8 DBs** under
`schemas/<db>/_meta.csv`. Each row currently contains placeholder values
(`extracted_by=bootstrap`); they will be replaced with real values on the
first `task schemas:refresh` run per DB. Pipeline `_meta.csv` rollout
remains in the v2 backlog (see brainstorming session 2026-04-26 → S2).

**Template:** [`schemas/_meta.template.csv`](./schemas/_meta.template.csv)
is the canonical blueprint. When adding a new database, copy it to
`schemas/<new-db>/_meta.csv` and replace `REPLACE_WITH_SOURCE_REPO`.
Long-term, `extract_schemas.py` should auto-write this file after each
refresh (see `tasks/inbox.csv` task for that follow-up).

---

When in doubt → ASK. Do not guess artifact location or content.
