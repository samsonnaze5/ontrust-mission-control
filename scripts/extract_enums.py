#!/usr/bin/env python3
"""
Extract enum values from Go code in onetrust-client-portal-api/pkg/database/
and produce per-table CSVs under artifacts/schemas/<db>/enums/.

Strategy:
  1. Parse all `Name = "VALUE"` constants from pkg/database/enum/*.go
  2. Use `IsValid<GroupName>()` validator functions as ground-truth for
     group → members mapping
  3. Parse entity files (pkg/database/entity/*.go) for table_name + GORM
     column → Go field mapping
  4. For each enum group, match group name to entity struct + field name
  5. Write per-table CSV listing each enum-mapped column's allowed values

One CSV per table, only for tables with at least 1 enum-mapped column.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GO_REPO = Path("/Users/kittiphong/Desktop/codes/go/onetrust-client-portal-api/pkg/database")
ENUM_DIR = GO_REPO / "enum"
ENTITY_DIR = GO_REPO / "entity"
OUT_ROOT = REPO_ROOT / "artifacts" / "schemas"


def split_camel(name: str) -> list[str]:
    """Split CamelCase into parts. e.g. WalletTxnRebateCredit -> [Wallet, Txn, Rebate, Credit]."""
    return re.findall(r"[A-Z][a-z0-9]+|[A-Z]+(?=[A-Z]|$)", name)


def parse_consts(text: str) -> dict[str, str]:
    """Return dict of `Name -> "value"` from a Go file."""
    return dict(re.findall(r'^\s*([A-Z]\w*)\s*(?:string)?\s*=\s*"([^"]+)"', text, re.MULTILINE))


def parse_enum_groups(enum_dir: Path) -> tuple[dict[str, list[tuple[str, str]]], dict[str, str]]:
    """Return (groups, all_consts) where:
    - groups: group_name -> list of (const_name, value)
    - all_consts: const_name -> value
    """
    all_consts: dict[str, str] = {}
    for f in enum_dir.glob("*.go"):
        all_consts.update(parse_consts(f.read_text()))

    groups: dict[str, list[tuple[str, str]]] = {}

    for f in enum_dir.glob("*.go"):
        text = f.read_text()

        # IsValid<GroupName>() validator functions — ground truth
        for m in re.finditer(
            r"func IsValid(\w+)\(v string\) bool \{[^}]*?isValidEnum\(v,\s*(?:\[\]string)?\s*\{?([^}]+)\}",
            text,
            re.DOTALL,
        ):
            group = m.group(1)
            list_text = m.group(2)
            # also handle var name reference: e.g. validUpgradeFromStatuses
            members: list[tuple[str, str]] = []
            seen = set()
            for cn in re.findall(r"\b([A-Z][A-Za-z0-9_]+)\b", list_text):
                if cn in all_consts and cn not in seen:
                    members.append((cn, all_consts[cn]))
                    seen.add(cn)
                elif cn in (
                    "validUpgradeFromStatuses",
                    "validUpgradeToStatuses",
                ):
                    # resolve var indirection
                    var_match = re.search(
                        rf"var\s+{cn}\s*=\s*\[\]string\{{([^}}]+)\}}", text
                    )
                    if var_match:
                        for vn in re.findall(r"\b([A-Z]\w+)\b", var_match.group(1)):
                            if vn in all_consts and vn not in seen:
                                members.append((vn, all_consts[vn]))
                                seen.add(vn)
            if members and group not in groups:
                groups[group] = members

    # Fallback: cluster remaining consts by CamelCase prefix (parts[:-1])
    covered = {n for members in groups.values() for n, _ in members}
    cluster: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for n, v in all_consts.items():
        if n in covered:
            continue
        parts = split_camel(n)
        if len(parts) >= 2:
            prefix = "".join(parts[:-1])
            cluster[prefix].append((n, v))

    for prefix, members in cluster.items():
        if len(members) >= 2 and prefix not in groups:
            groups[prefix] = members

    return groups, all_consts


def parse_entities(entity_dir: Path) -> list[dict]:
    """Return list of {struct, table, file, columns: [{column, go_field, go_type}]}"""
    out = []
    for f in sorted(entity_dir.glob("*.go")):
        text = f.read_text()

        m = re.search(r"^type (\w+) struct \{", text, re.MULTILINE)
        if not m:
            continue
        struct = m.group(1)

        m = re.search(rf'func \({struct}\) TableName\(\)\s*string\s*\{{\s*return\s+"([^"]+)"', text)
        if not m:
            continue
        table = m.group(1)

        cols = []
        for line in text.splitlines():
            fm = re.match(r"^\s*(\w+)\s+([\w\.\*\[\]]+)\s+`[^`]*gorm:\"([^\"]+)\"", line)
            if not fm:
                continue
            go_field, go_type, gorm = fm.group(1), fm.group(2), fm.group(3)
            cm = re.search(r"column:(\w+)", gorm)
            if not cm:
                continue
            cols.append({"column": cm.group(1), "go_field": go_field, "go_type": go_type})

        out.append({"struct": struct, "table": table, "file": f.name, "columns": cols})
    return out


def camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def snake_to_camel(name: str) -> str:
    return "".join(p.capitalize() for p in name.split("_"))


def dedupe_overlap(a: str, b: str) -> str:
    """Concatenate a + b, removing overlap if a's suffix == b's prefix.

    Examples:
      dedupe_overlap('WalletTransaction', 'TransactionType') = 'WalletTransactionType'
      dedupe_overlap('Wallet', 'Type') = 'WalletType'
      dedupe_overlap('RebateSettlement', 'Status') = 'RebateSettlementStatus'
    """
    for n in range(min(len(a), len(b)), 0, -1):
        if a.endswith(b[:n]):
            return a + b[n:]
    return a + b


def is_stringy(go_type: str) -> bool:
    return "string" in go_type.lower() or "sql.NullString" in go_type


def match_group_to_entity(
    group_name: str, entities: list[dict]
) -> list[tuple[dict, dict, int]]:
    """Match enum group_name to (entity, column, priority).

    Priority 1 (compound): dedupe_overlap(struct, col_camel) == group_name
    Priority 2 (bare): group_name lowercase == col_camel lowercase (enum-like cols only)
    Priority 3 (suffix + struct prefix): group_name endswith col_camel AND
      its prefix is a CamelCase prefix of struct (allows struct to be more
      specific than enum, e.g., enum 'OutboxStatus' on struct 'OutboxEvent').

    Returns the highest-priority match level only.
    """
    parts = split_camel(group_name)
    if len(parts) < 2:
        return []

    by_priority: dict[int, list[tuple[dict, dict, int]]] = {1: [], 2: [], 3: []}

    enum_field_hints = {
        "status", "type", "kind", "action", "source", "role", "mode", "state",
        "category", "class", "level", "destination", "method", "platform",
        "code", "entry", "reason", "calculation", "target",
    }

    for entity in entities:
        struct = entity["struct"]
        for col in entity["columns"]:
            if not is_stringy(col["go_type"]):
                continue

            col_camel = snake_to_camel(col["column"])

            if dedupe_overlap(struct, col_camel) == group_name:
                by_priority[1].append((entity, col, 1))
                continue

            if group_name.lower() == col_camel.lower():
                col_last = col["column"].rsplit("_", 1)[-1]
                if col_last.lower() in enum_field_hints:
                    by_priority[2].append((entity, col, 2))
                    continue

            if (
                col_camel
                and group_name.lower().endswith(col_camel.lower())
                and len(group_name) > len(col_camel)
            ):
                prefix = group_name[: -len(col_camel)]
                if prefix and struct.startswith(prefix):
                    by_priority[3].append((entity, col, 3))

    for p in (1, 2, 3):
        if by_priority[p]:
            return by_priority[p]
    return []


def find_dbs_for_table(table_name: str, dbs: list[str]) -> list[tuple[str, str]]:
    """Return [(db_name, schema), ...] for every DB containing the table."""
    out = []
    for db in dbs:
        tables_csv = OUT_ROOT / db / "_tables.csv"
        if not tables_csv.exists():
            continue
        with tables_csv.open() as f:
            for row in csv.DictReader(f):
                if row.get("table") == table_name:
                    out.append((db, row.get("schema") or "public"))
                    break
    return out


def main() -> int:
    print(f"Source: {GO_REPO}")
    print(f"Output: {OUT_ROOT}")
    print()

    print("Parsing enum files...")
    groups, all_consts = parse_enum_groups(ENUM_DIR)
    print(f"  Total constants: {len(all_consts)}")
    print(f"  Detected groups: {len(groups)}")
    for g in sorted(groups):
        print(f"    {g}: {len(groups[g])} values")

    print("\nParsing entity files...")
    entities = parse_entities(ENTITY_DIR)
    print(f"  Total entities: {len(entities)}")

    dbs = [d.name for d in OUT_ROOT.iterdir() if d.is_dir() and (d / "_tables.csv").exists()]
    print(f"  Databases: {dbs}")

    # Step 1: collect all (entity, col) → [(group_name, priority), ...]
    col_groups: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
    matched_groups = set()
    for group_name, members in groups.items():
        for entity, col, priority in match_group_to_entity(group_name, entities):
            col_groups[(entity["table"], col["column"])].append((group_name, priority))
            matched_groups.add(group_name)

    # Step 2: per (entity, col), keep only the BEST priority groups.
    # If multiple groups tie at the best priority, keep all of them
    # (e.g., outbox_events.event_type may aggregate multiple OutboxEvent* subgroups).
    table_rows: dict[str, list[dict]] = defaultdict(list)
    entity_by_table = {e["table"]: e for e in entities}
    col_by_table_col: dict[tuple[str, str], dict] = {}
    for e in entities:
        for c in e["columns"]:
            col_by_table_col[(e["table"], c["column"])] = c

    for (table, column), group_list in col_groups.items():
        best_priority = min(p for _, p in group_list)
        kept_groups = [g for g, p in group_list if p == best_priority]
        entity = entity_by_table[table]
        col = col_by_table_col[(table, column)]
        for g in kept_groups:
            for const_name, value in groups[g]:
                table_rows[table].append({
                    "column_name": col["column"],
                    "go_field": col["go_field"],
                    "enum_value": value,
                    "go_const": const_name,
                    "enum_group": g,
                    "source_struct": entity["struct"],
                })

    unmatched = sorted(set(groups) - matched_groups)
    if unmatched:
        print(f"\n{len(unmatched)} unmatched group(s) (no entity column found):")
        for g in unmatched:
            sample = groups[g][0]
            print(f"  - {g}: {len(groups[g])} values (e.g., {sample[0]}={sample[1]})")

    # Clean stale enum files first
    for db in dbs:
        enum_dir = OUT_ROOT / db / "enums"
        if enum_dir.exists():
            for f in enum_dir.glob("*.csv"):
                f.unlink()

    # Write per-table CSVs (one per DB that has the table)
    print(f"\nWriting per-table CSVs ({len(table_rows)} tables)...")
    written = 0
    skipped_no_db = []
    for table_name, rows in sorted(table_rows.items()):
        db_locations = find_dbs_for_table(table_name, dbs)
        if not db_locations:
            skipped_no_db.append(table_name)
            continue

        # Dedupe rows
        seen = set()
        unique_rows = []
        for r in rows:
            key = (r["column_name"], r["enum_value"], r["go_const"])
            if key in seen:
                continue
            seen.add(key)
            unique_rows.append(r)
        unique_rows.sort(key=lambda r: (r["column_name"], r["enum_value"]))

        fields = ["column_name", "go_field", "enum_value", "go_const", "enum_group", "source_struct"]

        for db, schema in db_locations:
            out_dir = OUT_ROOT / db / "enums"
            out_dir.mkdir(exist_ok=True)
            out_file = out_dir / f"{schema}.{table_name}.csv"
            with out_file.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
                w.writeheader()
                w.writerows(unique_rows)
            written += 1
            print(f"  {db}/enums/{schema}.{table_name}.csv  ({len(unique_rows)} rows)")

    if skipped_no_db:
        print(f"\nSkipped {len(skipped_no_db)} table(s) — not found in any extracted DB schema:")
        for t in skipped_no_db:
            print(f"  - {t}")

    print(f"\nDone: {written} CSV files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
