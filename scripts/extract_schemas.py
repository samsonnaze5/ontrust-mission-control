#!/usr/bin/env python3
"""
Extract full database schemas from PostgreSQL and ClickHouse to CSV.

Reads connection credentials from `.env` at the repo root and writes
schema CSVs into `artifacts/schemas/<database>/...`.

Run:
    pip install -r scripts/requirements.txt
    python scripts/extract_schemas.py
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    from dotenv import load_dotenv
except ImportError:
    print(
        "Missing dependency: python-dotenv. Run: pip install -r scripts/requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"
OUTPUT_ROOT = REPO_ROOT / "artifacts" / "schemas"


@dataclass
class DatabaseConfig:
    name: str
    kind: str          # 'postgres' | 'clickhouse'
    env_prefix: str    # e.g. 'DATABASE_' or 'CLICKHOUSE_CLIENT_'


# Logical name → engine + env prefix.
# Mirrors artifacts/databases.csv. env_prefix matches artifacts/envs.csv exactly.
DATABASES: list[DatabaseConfig] = [
    DatabaseConfig("crm_central",          "postgres",   "DATABASE_"),
    DatabaseConfig("balance",              "postgres",   "DATABASE_TRADING_BALANCE_"),
    DatabaseConfig("crm_trading_open",     "postgres",   "DATABASE_TRADING_IN_"),
    DatabaseConfig("crm_trading_closed",   "postgres",   "DATABASE_TRADING_OUT_"),
    DatabaseConfig("crm_trading_complete", "postgres",   "DATABASE_POSITION_COMPLETE_"),
    DatabaseConfig("crm_financial",        "postgres",   "DATABASE_FINANCIAL_"),
    DatabaseConfig("clickhouse_client",    "clickhouse", "CLICKHOUSE_CLIENT_"),
    DatabaseConfig("clickhouse_ib",        "clickhouse", "CLICKHOUSE_IB_"),
]

# Postgres FK action codes → readable names.
FK_ACTION = {"a": "NO ACTION", "r": "RESTRICT", "c": "CASCADE", "n": "SET NULL", "d": "SET DEFAULT"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_state(repo_path: str) -> tuple[str, str]:
    """Return (sha, branch) for repo_path, or ("UNKNOWN", "UNKNOWN") on any failure."""
    if not repo_path or not Path(repo_path).is_dir():
        return "UNKNOWN", "UNKNOWN"
    try:
        sha = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        branch = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return sha, branch
    except Exception:
        return "UNKNOWN", "UNKNOWN"


def _service_path(service_name: str) -> str:
    """Look up a service's absolute path from artifacts/services.csv."""
    services_csv = REPO_ROOT / "artifacts" / "services.csv"
    if not services_csv.is_file():
        return ""
    with services_csv.open() as f:
        for row in csv.DictReader(f):
            if row["service"] == service_name:
                return row["path"]
    return ""


def _db_source_repo(db_name: str) -> str:
    """Look up the service that owns a DB (via artifacts/databases.csv)."""
    databases_csv = REPO_ROOT / "artifacts" / "databases.csv"
    if not databases_csv.is_file():
        return ""
    with databases_csv.open() as f:
        for row in csv.DictReader(f):
            if row["database"] == db_name:
                return row.get("migration_project_source", "")
    return ""


def _write_meta(out_dir: Path, db_name: str, extracted_by: str, notes: str = "") -> None:
    """Write `_meta.csv` for one DB with current timestamp + source SHA + branch."""
    source_repo = _db_source_repo(db_name) or "UNKNOWN"
    repo_path = _service_path(source_repo) if source_repo != "UNKNOWN" else ""
    sha, branch = _git_state(repo_path)

    meta_path = out_dir / "_meta.csv"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["last_extracted_at", "extracted_by", "source_commit_sha",
              "source_repo", "source_branch", "notes"]
    with meta_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerow({
            "last_extracted_at": _now_iso(),
            "extracted_by": extracted_by,
            "source_commit_sha": sha,
            "source_repo": source_repo,
            "source_branch": branch,
            "notes": notes,
        })


def _safe_filename(s: str) -> str:
    return s.replace("/", "_").replace("\\", "_")


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fieldnames})


def _get_pg_creds(prefix: str) -> dict:
    return {
        "host": os.getenv(f"{prefix}HOST", ""),
        "port": int(os.getenv(f"{prefix}PORT") or 5432),
        "user": os.getenv(f"{prefix}USERNAME", ""),
        "password": os.getenv(f"{prefix}PASSWORD", ""),
        "dbname": os.getenv(f"{prefix}DATABASE", ""),
    }


def _get_ch_creds(prefix: str) -> dict:
    # Port resolution (no silent default):
    #   1. explicit `*_PORT` env (override)
    #   2. port embedded in `*_HOST` as "host:port" (per envs.csv convention)
    #   3. None — caller must error out
    host_raw = os.getenv(f"{prefix}HOST", "")
    tls = os.getenv(f"{prefix}TLS", "false").lower() == "true"
    explicit_port = os.getenv(f"{prefix}PORT", "").strip()

    if ":" in host_raw:
        host, port_in_host = host_raw.rsplit(":", 1)
    else:
        host, port_in_host = host_raw, ""

    port_str = explicit_port or port_in_host
    port = int(port_str) if port_str else None

    return {
        "host": host,
        "port": port,
        "username": os.getenv(f"{prefix}USERNAME", ""),
        "password": os.getenv(f"{prefix}PASSWORD", ""),
        "database": os.getenv(f"{prefix}DATABASE", ""),
        "secure": tls,
    }


# ============================================================
# PostgreSQL
# ============================================================

PG_TABLES_SQL = """
SELECT
    n.nspname AS schema,
    c.relname AS table_name,
    CASE c.relkind
        WHEN 'r' THEN 'TABLE'
        WHEN 'v' THEN 'VIEW'
        WHEN 'm' THEN 'MATERIALIZED VIEW'
        WHEN 'p' THEN 'PARTITIONED TABLE'
        WHEN 'f' THEN 'FOREIGN TABLE'
        ELSE c.relkind::text
    END AS kind,
    c.reltuples::bigint AS row_count_estimate,
    pg_total_relation_size(c.oid) AS size_bytes,
    obj_description(c.oid, 'pg_class') AS comment
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r','v','m','p','f')
  AND n.nspname NOT IN ('pg_catalog','information_schema')
  AND n.nspname NOT LIKE 'pg_toast%'
ORDER BY n.nspname, c.relname;
"""

PG_COLUMNS_SQL = """
SELECT
    n.nspname AS schema,
    c.relname AS table_name,
    a.attnum AS ordinal,
    a.attname AS column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
    NOT a.attnotnull AS is_nullable,
    pg_get_expr(d.adbin, d.adrelid) AS column_default,
    col_description(c.oid, a.attnum) AS comment
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
WHERE a.attnum > 0
  AND NOT a.attisdropped
  AND c.relkind IN ('r','v','m','p','f')
  AND n.nspname NOT IN ('pg_catalog','information_schema')
ORDER BY n.nspname, c.relname, a.attnum;
"""

PG_PK_SQL = """
SELECT n.nspname, c.relname, a.attname
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN unnest(con.conkey) AS k(attnum) ON true
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
WHERE con.contype = 'p'
  AND n.nspname NOT IN ('pg_catalog','information_schema');
"""

PG_FK_SQL = """
SELECT
    n.nspname AS schema,
    c.relname AS table_name,
    con.conname AS constraint_name,
    a.attname AS column_name,
    fn.nspname AS referenced_schema,
    fc.relname AS referenced_table,
    fa.attname AS referenced_column,
    con.confupdtype AS on_update_code,
    con.confdeltype AS on_delete_code,
    k.ord AS column_order
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_class fc ON fc.oid = con.confrelid
JOIN pg_namespace fn ON fn.oid = fc.relnamespace
JOIN unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
JOIN pg_attribute fa ON fa.attrelid = fc.oid AND fa.attnum = (con.confkey)[k.ord]
WHERE con.contype = 'f'
  AND n.nspname NOT IN ('pg_catalog','information_schema')
ORDER BY n.nspname, c.relname, con.conname, k.ord;
"""

PG_INDEXES_SQL = """
SELECT
    n.nspname AS schema,
    c.relname AS table_name,
    i.relname AS index_name,
    array_agg(a.attname ORDER BY x.ord) AS columns,
    ix.indisunique AS is_unique,
    ix.indisprimary AS is_primary,
    am.amname AS index_type
FROM pg_index ix
JOIN pg_class c ON c.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_am am ON am.oid = i.relam
JOIN unnest(ix.indkey) WITH ORDINALITY AS x(attnum, ord) ON true
LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = x.attnum
WHERE n.nspname NOT IN ('pg_catalog','information_schema')
GROUP BY n.nspname, c.relname, i.relname, ix.indisunique, ix.indisprimary, am.amname
ORDER BY n.nspname, c.relname, i.relname;
"""

PG_CONSTRAINTS_SQL = """
SELECT
    n.nspname AS schema,
    c.relname AS table_name,
    con.conname AS constraint_name,
    CASE con.contype
        WHEN 'c' THEN 'CHECK'
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'x' THEN 'EXCLUSION'
    END AS type,
    pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE con.contype IN ('c','u','x')
  AND n.nspname NOT IN ('pg_catalog','information_schema')
ORDER BY n.nspname, c.relname, con.conname;
"""


def extract_postgres(cfg: DatabaseConfig, out_dir: Path) -> dict:
    try:
        import psycopg
    except ImportError:
        return {"status": "error", "error": "psycopg not installed",
                "table_count": 0, "host": "", "port": "", "database_name": ""}

    creds = _get_pg_creds(cfg.env_prefix)
    summary = {"host": creds["host"], "port": str(creds["port"]), "database_name": creds["dbname"]}

    if not creds["host"] or not creds["dbname"]:
        return {**summary, "status": "skipped (missing env)", "error": "", "table_count": 0}

    try:
        with psycopg.connect(
            host=creds["host"],
            port=creds["port"],
            user=creds["user"],
            password=creds["password"],
            dbname=creds["dbname"],
            connect_timeout=10,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(PG_TABLES_SQL)
                tables = [
                    {"schema": r[0], "table": r[1], "kind": r[2],
                     "row_count_estimate": r[3], "size_bytes": r[4], "comment": r[5]}
                    for r in cur.fetchall()
                ]

                cur.execute(PG_COLUMNS_SQL)
                column_rows = cur.fetchall()

                cur.execute(PG_PK_SQL)
                pks = {(r[0], r[1], r[2]) for r in cur.fetchall()}

                cur.execute(PG_FK_SQL)
                fks_raw = [
                    {"schema": r[0], "table": r[1], "constraint_name": r[2],
                     "column": r[3], "referenced_schema": r[4],
                     "referenced_table": r[5], "referenced_column": r[6],
                     "on_update": FK_ACTION.get(r[7], r[7]),
                     "on_delete": FK_ACTION.get(r[8], r[8])}
                    for r in cur.fetchall()
                ]

                cur.execute(PG_INDEXES_SQL)
                indexes = [
                    {"schema": r[0], "table": r[1], "index_name": r[2],
                     "columns": ",".join(c for c in r[3] if c is not None),
                     "is_unique": r[4], "is_primary": r[5], "index_type": r[6]}
                    for r in cur.fetchall()
                ]

                cur.execute(PG_CONSTRAINTS_SQL)
                constraints = [
                    {"schema": r[0], "table": r[1], "constraint_name": r[2],
                     "type": r[3], "definition": r[4]}
                    for r in cur.fetchall()
                ]

        # Single-column unique indexes → mark column as unique
        unique_cols: set[tuple[str, str, str]] = set()
        for ix in indexes:
            if ix["is_unique"] and not ix["is_primary"]:
                cols = ix["columns"].split(",") if ix["columns"] else []
                if len(cols) == 1 and cols[0]:
                    unique_cols.add((ix["schema"], ix["table"], cols[0]))

        fk_by_col = {(f["schema"], f["table"], f["column"]): f for f in fks_raw}

        # Per-table column CSVs
        cols_by_table: dict[tuple[str, str], list[dict]] = {}
        for r in column_rows:
            schema, table, ordinal, col, dtype, nullable, default, comment = r
            key = (schema, table, col)
            fk = fk_by_col.get(key)
            cols_by_table.setdefault((schema, table), []).append({
                "ordinal": ordinal,
                "column_name": col,
                "data_type": dtype,
                "is_nullable": nullable,
                "default": default,
                "is_primary_key": key in pks,
                "is_unique": key in unique_cols,
                "is_foreign_key": fk is not None,
                "fk_reference": (
                    f"{fk['referenced_schema']}.{fk['referenced_table']}.{fk['referenced_column']}"
                    if fk else ""
                ),
                "comment": comment,
            })

        per_table_dir = out_dir / "tables"
        col_fields = ["ordinal", "column_name", "data_type", "is_nullable", "default",
                      "is_primary_key", "is_unique", "is_foreign_key", "fk_reference", "comment"]
        for (schema, table), rows in cols_by_table.items():
            fname = f"{_safe_filename(schema)}.{_safe_filename(table)}.csv"
            _write_csv(per_table_dir / fname, col_fields, rows)

        # DB-level files
        _write_csv(out_dir / "_tables.csv",
                   ["schema", "table", "kind", "row_count_estimate", "size_bytes", "comment"],
                   tables)
        _write_csv(out_dir / "_indexes.csv",
                   ["schema", "table", "index_name", "columns", "is_unique", "is_primary", "index_type"],
                   indexes)
        _write_csv(out_dir / "_foreign_keys.csv",
                   ["schema", "table", "constraint_name", "column",
                    "referenced_schema", "referenced_table", "referenced_column",
                    "on_update", "on_delete"],
                   fks_raw)
        _write_csv(out_dir / "_constraints.csv",
                   ["schema", "table", "constraint_name", "type", "definition"],
                   constraints)

        return {**summary, "status": "ok", "error": "", "table_count": len(tables)}
    except Exception as e:
        return {**summary, "status": "error", "error": str(e)[:200], "table_count": 0}


# ============================================================
# ClickHouse
# ============================================================

def extract_clickhouse(cfg: DatabaseConfig, out_dir: Path) -> dict:
    try:
        import clickhouse_connect
    except ImportError:
        return {"status": "error", "error": "clickhouse-connect not installed",
                "table_count": 0, "host": "", "port": "", "database_name": ""}

    creds = _get_ch_creds(cfg.env_prefix)
    summary = {
        "host": creds["host"],
        "port": str(creds["port"]) if creds["port"] is not None else "",
        "database_name": creds["database"],
    }

    if not creds["host"] or not creds["database"]:
        return {**summary, "status": "skipped (missing env)", "error": "", "table_count": 0}

    if creds["port"] is None:
        return {
            **summary,
            "status": "error",
            "error": (
                f"port not specified — set {cfg.env_prefix}HOST=host:port "
                f"or {cfg.env_prefix}PORT=<port>"
            ),
            "table_count": 0,
        }

    try:
        client = clickhouse_connect.get_client(
            host=creds["host"],
            port=creds["port"],
            username=creds["username"],
            password=creds["password"],
            database=creds["database"],
            secure=creds["secure"],
            connect_timeout=10,
        )

        tables_res = client.query(
            """
            SELECT database, name, engine, total_rows, total_bytes, comment,
                   partition_key, sorting_key, primary_key, sampling_key
            FROM system.tables
            WHERE database = %(db)s
            ORDER BY name
            """,
            parameters={"db": creds["database"]},
        )
        tables = [
            {"database": r[0], "table": r[1], "engine": r[2],
             "total_rows": r[3], "total_bytes": r[4], "comment": r[5],
             "partition_key": r[6], "sorting_key": r[7],
             "primary_key": r[8], "sampling_key": r[9]}
            for r in tables_res.result_rows
        ]

        cols_res = client.query(
            """
            SELECT database, table, position, name, type,
                   default_kind, default_expression,
                   is_in_primary_key, is_in_partition_key, is_in_sorting_key, comment
            FROM system.columns
            WHERE database = %(db)s
            ORDER BY table, position
            """,
            parameters={"db": creds["database"]},
        )
        cols_by_table: dict[tuple[str, str], list[dict]] = {}
        for r in cols_res.result_rows:
            db, tbl, pos, name, dtype, dk, de, pk, partk, sk, cmt = r
            cols_by_table.setdefault((db, tbl), []).append({
                "ordinal": pos,
                "column_name": name,
                "data_type": dtype,
                "default_kind": dk,
                "default_expression": de,
                "is_in_primary_key": pk,
                "is_in_partition_key": partk,
                "is_in_sorting_key": sk,
                "comment": cmt,
            })

        per_table_dir = out_dir / "tables"
        col_fields = ["ordinal", "column_name", "data_type",
                      "default_kind", "default_expression",
                      "is_in_primary_key", "is_in_partition_key", "is_in_sorting_key", "comment"]
        for (db, tbl), rows in cols_by_table.items():
            fname = f"{_safe_filename(db)}.{_safe_filename(tbl)}.csv"
            _write_csv(per_table_dir / fname, col_fields, rows)

        _write_csv(out_dir / "_tables.csv",
                   ["database", "table", "engine", "total_rows", "total_bytes", "comment",
                    "partition_key", "sorting_key", "primary_key", "sampling_key"],
                   tables)

        client.close()
        return {**summary, "status": "ok", "error": "", "table_count": len(tables)}
    except Exception as e:
        return {**summary, "status": "error", "error": str(e)[:200], "table_count": 0}


# ============================================================
# main
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        help="Limit extraction to a single DB by name (e.g. crm_financial). "
             "Default: extract all 8 DBs.",
    )
    parser.add_argument(
        "--by",
        default="claude",
        choices=["user", "claude", "ci"],
        help="Value written to `extracted_by` in each per-DB _meta.csv (default: claude)",
    )
    args = parser.parse_args()

    if not ENV_FILE.exists():
        print(f"ERROR: .env not found at {ENV_FILE}", file=sys.stderr)
        return 1
    load_dotenv(ENV_FILE)

    if args.only:
        dbs_to_run = [d for d in DATABASES if d.name == args.only]
        if not dbs_to_run:
            valid = ", ".join(d.name for d in DATABASES)
            print(f"ERROR: unknown database '{args.only}'. Valid: {valid}", file=sys.stderr)
            return 1
    else:
        dbs_to_run = list(DATABASES)

    extracted_at = _now_iso()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    index_rows: list[dict] = []
    for cfg in dbs_to_run:
        print(f"[{cfg.kind}] {cfg.name} (prefix={cfg.env_prefix}) ...")
        out_dir = OUTPUT_ROOT / cfg.name

        if cfg.kind == "postgres":
            result = extract_postgres(cfg, out_dir)
        elif cfg.kind == "clickhouse":
            result = extract_clickhouse(cfg, out_dir)
        else:
            result = {"status": f"unknown kind: {cfg.kind}", "table_count": 0,
                      "host": "", "port": "", "database_name": "", "error": ""}

        index_rows.append({
            "database": cfg.name,
            "kind": cfg.kind,
            "host": result.get("host", ""),
            "port": result.get("port", ""),
            "database_name": result.get("database_name", ""),
            "status": result.get("status", ""),
            "table_count": result.get("table_count", 0),
            "extracted_at": extracted_at,
            "error": result.get("error", ""),
            "is_stale": False,
        })
        print(f"  -> {result.get('status')} ({result.get('table_count')} tables)")

        # Auto-write per-DB _meta.csv only when extraction succeeded — failures
        # leave the existing meta untouched (still bootstrap on first run).
        if result.get("status") == "ok":
            _write_meta(out_dir, cfg.name, args.by)

    # _index.csv is full inventory across DBs — when running --only, merge with
    # any pre-existing rows for DBs we didn't touch this run. Pre-existing rows
    # get is_stale=True so users can spot-check freshness in one column.
    if args.only and (OUTPUT_ROOT / "_index.csv").is_file():
        merged: dict[str, dict] = {}
        with (OUTPUT_ROOT / "_index.csv").open() as f:
            for row in csv.DictReader(f):
                row["is_stale"] = "True"  # carried over from prior run
                merged[row["database"]] = row
        for row in index_rows:
            merged[row["database"]] = row  # current run overwrites
        index_rows = [merged[name] for name in sorted(merged)]

    _write_csv(
        OUTPUT_ROOT / "_index.csv",
        ["database", "kind", "host", "port", "database_name",
         "status", "table_count", "extracted_at", "error", "is_stale"],
        index_rows,
    )

    print(f"\nOutput: {OUTPUT_ROOT}")

    failures = [r for r in index_rows if r["status"].startswith("error")
                and r["database"] in {d.name for d in dbs_to_run}]
    if failures:
        print(f"\n{len(failures)} database(s) failed this run:", file=sys.stderr)
        for f in failures:
            print(f"  - {f['database']}: {f['error']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
