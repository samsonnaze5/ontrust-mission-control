#!/usr/bin/env python3
"""
Semantic schema diff for one DB: compares per-table CSVs in
`artifacts/schemas/<db>/tables/` between two states (git refs or working tree).

Reports tables added/removed/modified, and per modified table the columns
added/removed/type-changed. This is more readable than `git diff` on raw CSVs
when reviewing a schema migration.

Usage:
    python3 scripts/schema_diff.py <db>                  # HEAD vs working tree
    python3 scripts/schema_diff.py <db> --base <ref>     # <ref> vs working tree
    python3 scripts/schema_diff.py <db> --base <a> --target <b>
                                                         # <a> vs <b> (both refs)

Examples:
    python3 scripts/schema_diff.py crm_financial
    python3 scripts/schema_diff.py crm_financial --base HEAD~1
    python3 scripts/schema_diff.py crm_financial --base v1.0 --target main
"""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_ROOT = REPO_ROOT / "artifacts" / "schemas"


def _git_show(ref: str, rel_path: str) -> str | None:
    """Return file content at git ref, or None if missing/error."""
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{rel_path}"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode()
    except subprocess.CalledProcessError:
        return None


def _git_ls_csvs(ref: str, rel_dir: str) -> list[str]:
    """Return list of CSV paths under rel_dir at git ref."""
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", ref, rel_dir],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode()
    except subprocess.CalledProcessError:
        return []
    return [p for p in out.strip().split("\n") if p.endswith(".csv")]


def load_at(db: str, ref: str | None) -> dict[str, list[dict]]:
    """Return {table_basename: [column_rows]} at the given ref or working tree."""
    schema_dir = SCHEMAS_ROOT / db / "tables"
    rel_dir = str(schema_dir.relative_to(REPO_ROOT))
    out: dict[str, list[dict]] = {}

    if ref is None:
        if not schema_dir.is_dir():
            return out
        for csv_path in sorted(schema_dir.glob("*.csv")):
            with csv_path.open() as f:
                out[csv_path.name] = list(csv.DictReader(f))
        return out

    for full_path in _git_ls_csvs(ref, rel_dir):
        content = _git_show(ref, full_path)
        if content is None:
            continue
        out[Path(full_path).name] = list(csv.DictReader(io.StringIO(content)))
    return out


def diff_columns(old: list[dict], new: list[dict]) -> dict:
    """Return {added, removed, type_changed} between two column lists."""
    old_map = {r["column_name"]: r for r in old}
    new_map = {r["column_name"]: r for r in new}

    added = sorted(set(new_map) - set(old_map))
    removed = sorted(set(old_map) - set(new_map))
    type_changed: list[tuple[str, str, str]] = []
    for name in sorted(set(old_map) & set(new_map)):
        old_t = old_map[name].get("data_type", "")
        new_t = new_map[name].get("data_type", "")
        if old_t != new_t:
            type_changed.append((name, old_t, new_t))

    return {"added": added, "removed": removed, "type_changed": type_changed}


def format_diff(db: str, base_label: str, target_label: str,
                base: dict[str, list[dict]], target: dict[str, list[dict]]) -> str:
    base_t = set(base)
    target_t = set(target)

    added = sorted(target_t - base_t)
    removed = sorted(base_t - target_t)
    common = sorted(base_t & target_t)

    modified: list[tuple[str, dict]] = []
    unchanged: list[str] = []
    for tbl in common:
        cd = diff_columns(base[tbl], target[tbl])
        if cd["added"] or cd["removed"] or cd["type_changed"]:
            modified.append((tbl, cd))
        else:
            unchanged.append(tbl)

    lines = [f"=== {db} schema diff ({base_label} → {target_label}) ===", ""]

    lines.append(f"Tables added ({len(added)}):")
    lines.extend(f"  + {t}" for t in added) if added else lines.append("  (none)")
    lines.append("")

    lines.append(f"Tables removed ({len(removed)}):")
    lines.extend(f"  - {t}" for t in removed) if removed else lines.append("  (none)")
    lines.append("")

    lines.append(f"Tables modified ({len(modified)}):")
    if modified:
        for tbl, cd in modified:
            lines.append(f"  ~ {tbl}")
            for col in cd["added"]:
                lines.append(f"      + added column: {col}")
            for col in cd["removed"]:
                lines.append(f"      - removed column: {col}")
            for name, old_t, new_t in cd["type_changed"]:
                lines.append(f"      ~ {name}: {old_t} -> {new_t}")
    else:
        lines.append("  (none)")
    lines.append("")

    if unchanged:
        lines.append(f"Tables unchanged ({len(unchanged)}):")
        head = unchanged[:5]
        for t in head:
            lines.append(f"    {t}")
        if len(unchanged) > 5:
            lines.append(f"    ... and {len(unchanged) - 5} more")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("db", help="DB name (e.g. crm_financial)")
    ap.add_argument("--base", default="HEAD",
                    help="Base git ref to compare from (default: HEAD)")
    ap.add_argument("--target", default=None,
                    help="Target git ref to compare to (default: working tree)")
    args = ap.parse_args()

    base = load_at(args.db, args.base)
    target = load_at(args.db, args.target)

    if not base and not target:
        print(f"ERROR: no schema CSVs found for '{args.db}' at either ref.\n"
              f"  Check artifacts/schemas/{args.db}/tables/ exists, or run\n"
              f"  `task schemas:refresh:db -- {args.db}` first.", file=sys.stderr)
        return 1

    target_label = args.target if args.target else "working"
    print(format_diff(args.db, args.base, target_label, base, target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
