# Bh5nGcT2vKsP — Refactor symbol_custom_group schema (FK + symbol_id uuid)

> Spec for task `Bh5nGcT2vKsP` (priority **P0**). Companion to `tasks/inbox.csv`.

## Context

- **Database**: `crm_central`
- **Owner repo**: `onetrust-client-portal-api` (per `artifacts/databases.csv`)
- **Migration path in repo**: `migrations/`
- **Environment**: DEV-only — both target tables empty per user (2026-04-27)
- **Trigger**: User request 2026-04-27 — clean up `symbol_custom_group_*` schema before any data loads

## Schema changes

### `public.symbol_custom_groups`

**Drop**:

- Column `symbol_group_id uuid NOT NULL`
- FK constraint `symbol_custom_groups_symbol_group_id_fkey` (→ `public.symbol_groups.id`)

**Keep**:

- PK `symbol_custom_groups_pkey`
- Unique index `symbol_custom_groups_name_key` on `(name)`
- All other columns (`name`, `description`, `is_active`, `sort_order`, `created_at`, `updated_at`)

### `public.symbol_custom_group_items`

**Drop**:

- Column `symbol varchar(50) NOT NULL`
- Unique index `uq_symbol_custom_group_items_symbol`

**Add**:

- Column `symbol_id uuid NOT NULL`
- FK constraint → `public.symbols.id` (proposed name: `symbol_custom_group_items_symbol_id_fkey`)
- Composite unique index on `(symbol_custom_group_id, symbol_id)` (proposed name: `uq_symbol_custom_group_items_group_symbol`)

**Keep**:

- PK `symbol_custom_group_items_pkey`
- Index `idx_symbol_custom_group_items_group` on `(symbol_custom_group_id)`
- FK `symbol_custom_group_items_symbol_custom_group_id_fkey` (→ `symbol_custom_groups.id`, ON DELETE CASCADE)

## Impact analysis (deliverable BEFORE migration)

### Artifact files to scan in `artifacts/schemas/crm_central/`

Don't rely only on `tables/<name>.csv` — extra constraints / indexes / FKs live in DB-level files:

- `tables/public.symbol_custom_groups.csv`
- `tables/public.symbol_custom_group_items.csv`
- `tables/public.symbols.csv` (target of new FK)
- `_constraints.csv` (CHECK / additional UNIQUE)
- `_indexes.csv` (all indexes incl. uniques)
- `_foreign_keys.csv` — **especially**: cross-table FKs that reference `symbol_custom_groups.id` (downstream consumers):
  - `rebate_scheme_caps.symbol_custom_group_id`
  - `rebate_scheme_rates.symbol_custom_group_id`
  - These reference the PK and are **unaffected** by dropping `symbol_group_id` column, but business logic that joined through the dropped FK may need refactor

### Repos to grep

Run grep for `symbol_custom_groups`, `symbol_custom_group_items`, and the dropped column names. Don't pre-filter; report actual hits.

| Repo (path from `services.csv`) | Likelihood | Why |
|---|---|---|
| `onetrust-client-portal-api` | certain | Owner of crm_central master data |
| `onetrust-financial-service` | high | Rebate logic uses `rebate_scheme_caps`/`rebate_scheme_rates` (which FK to `symbol_custom_groups`) |
| `onetrust-mt5-processor` | medium | Trading deal processing may reference symbol metadata |
| `onetrust-archiver` | low | Sink-only; may have model definitions |
| `aeternixth-go-lib` | low | Shared lib; may contain shared models |
| `onetrust-mt5-proxy-api` | skip | No crm_central access (proxy MT5 API only) |

### Report format

For each hit, record:

- File path + line number
- Code excerpt (function / struct / SQL)
- Required action: `rename` / `remove` / `refactor` / `no-action`

Deliver the report as a doc commit in mission-control at `tasks/specs/Bh5nGcT2vKsP-impact-report.md` **before** writing the migration.

## Migration

After impact report is approved:

1. Write migration in `onetrust-client-portal-api/migrations/` — number/name per repo convention (read existing migrations first to match style; do not assume `goose` vs `golang-migrate` — verify)
2. Migration body (DEV-only, no backfill):
   - `ALTER TABLE symbol_custom_groups DROP CONSTRAINT symbol_custom_groups_symbol_group_id_fkey;`
   - `ALTER TABLE symbol_custom_groups DROP COLUMN symbol_group_id;`
   - `DROP INDEX uq_symbol_custom_group_items_symbol;`
   - `ALTER TABLE symbol_custom_group_items DROP COLUMN symbol;`
   - `ALTER TABLE symbol_custom_group_items ADD COLUMN symbol_id uuid NOT NULL REFERENCES public.symbols(id);`
   - `CREATE UNIQUE INDEX uq_symbol_custom_group_items_group_symbol ON symbol_custom_group_items (symbol_custom_group_id, symbol_id);`
3. Down migration only if repo convention requires (DEV-only, but follow repo standards)
4. Apply on DEV; verify via `psql` or repo migration tool

## GORM model + code update

In `onetrust-client-portal-api`:

- `SymbolCustomGroup` model: drop `SymbolGroupID` field + relation
- `SymbolCustomGroupItem` model: drop `Symbol string` field, add `SymbolID uuid.UUID` + relation tag → `Symbol`
- Update repos / handlers / validators per impact report findings
- Re-run code generation if applicable

## Success criteria

- [ ] Impact analysis report committed at `tasks/specs/Bh5nGcT2vKsP-impact-report.md`
- [ ] Migration applied on DEV
- [ ] `task schemas:refresh:db -- crm_central` run; `_meta.csv` updated; artifact diff matches expected:
  - `tables/public.symbol_custom_groups.csv`: `symbol_group_id` row removed
  - `tables/public.symbol_custom_group_items.csv`: `symbol` row removed, `symbol_id` row added (data_type=uuid, NOT NULL, FK→symbols.id)
  - `_indexes.csv`: `uq_symbol_custom_group_items_symbol` removed; new composite unique index appears
  - `_foreign_keys.csv`: `symbol_custom_groups_symbol_group_id_fkey` removed; new FK on `symbol_custom_group_items.symbol_id` appears
- [ ] All GORM models + referencing Go code updated
- [ ] Grep across all 6 repos returns zero hits for dropped column names (`symbol_custom_groups.symbol_group_id`, `symbol_custom_group_items.symbol` as a column reference — not the table)
- [ ] `go build ./...` + repo lint pass in `onetrust-client-portal-api` (and any other repo that needed updates)
- [ ] If `EST-TEST-001` (testing convention) is closed by execution time → tests added per convention; otherwise STOP & ASK per CLAUDE.md §8.5

## Notes

- DEV-only assumption holds because user confirmed both tables empty (2026-04-27). If status changes before this ships, refine migration to backfill `symbol_id` via `JOIN public.symbols ON public.symbols.symbol = public.symbol_custom_group_items.symbol` before dropping the old column
- Downstream FKs on `rebate_scheme_caps` / `rebate_scheme_rates` reference `symbol_custom_groups.id` (PK) — unaffected by the column drop. Business logic, however, may have joined through the soon-to-be-dropped `symbol_custom_groups.symbol_group_id` (e.g., to derive a symbol_group from a custom_group); flag those joins in the impact report

## Provenance

- Created via `/task-add` on 2026-04-27
- Spec file added per retro item `later#84621` (split detailed spec out of CSV)
- Constraint detail per retro item `soon#39574`
- Multi-file scan scope per retro item `soon#52193`
- Service scope refinement per retro item `fyi#67428`
