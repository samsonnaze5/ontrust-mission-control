#!/usr/bin/env python3
"""
Extract `cmd/*` entry points from each backend service listed in
`artifacts/services.csv` and produce `artifacts/entrypoints.csv`.

Output schema:
    service, cmd_name, cmd_path, dockerfile_path, kind, deployable, port, description

Scope: only **deployable** cmds are written. Rows classified as `kind=tool`
(dev/CLI utilities like migrate, kafka-topic-init, *-generator, mock, seed-*)
are detected but **excluded** from the output — they don't get built into
container images.

Heuristics:
  * `kind` — inspect cmd name + main.go patterns
      - migrate / kafka-topic-* / *-generator / *gen / mock / seed-* → tool
      - grpc.NewServer       → server (gRPC)
      - fiber.New / app.Listen → server
      - outbox.NewOutboxPublisher → worker
      - tickInterval const / *-scheduler / *-watcher → scheduler
      - pkgkafka.NewConsumer → consumer  (default for everything else)
  * `deployable` — `tool` → no, otherwise yes (always yes after filter)
  * `port` — regex-match `app.Listen(":NNNN")` / `port := NNNN` / `config.<X>.Port`
  * `description` — PRESERVED from existing CSV; new cmds get the Go top
    comment block as a placeholder prefixed with `[TODO review]`.

Side effect: writes/updates `artifacts/entrypoints.meta.csv` with one row
per service (last_extracted_at, source_commit_sha, extracted_by, …).

Usage:
    python3 scripts/extract_entrypoints.py            # write
    python3 scripts/extract_entrypoints.py --check    # dry-run, exit 1 on diff
    python3 scripts/extract_entrypoints.py --by user  # set extracted_by (default: claude)
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_CSV = REPO_ROOT / "artifacts" / "services.csv"
OUT_CSV = REPO_ROOT / "artifacts" / "entrypoints.csv"
META_CSV = REPO_ROOT / "artifacts" / "entrypoints.meta.csv"

OUT_FIELDS = [
    "service", "cmd_name", "cmd_path", "dockerfile_path",
    "kind", "deployable", "port", "description",
]
META_FIELDS = [
    "service", "last_extracted_at", "extracted_by",
    "source_commit_sha", "source_branch", "notes",
]

TOOL_NAME_PATTERNS = [
    re.compile(r".*-generator$"),
    re.compile(r".*gen$"),
    re.compile(r"^mock$"),
    re.compile(r"^mock-.*"),
    re.compile(r"^seed-.*"),
]


def load_services() -> list[dict]:
    with SERVICES_CSV.open() as f:
        return [r for r in csv.DictReader(f) if (Path(r["path"]) / "cmd").is_dir()]


def load_existing_descriptions() -> dict[tuple[str, str], str]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open() as f:
        return {(r["service"], r["cmd_name"]): r["description"] for r in csv.DictReader(f)}


def find_dockerfile(service_root: Path) -> str:
    for candidate in [
        service_root / "deployments" / "Dockerfile",
        service_root / "Dockerfile",
    ]:
        if candidate.is_file():
            return str(candidate.relative_to(service_root))
    return ""


def read_main_go(cmd_dir: Path) -> str:
    main_go = cmd_dir / "main.go"
    return main_go.read_text() if main_go.is_file() else ""


def extract_top_comment(src: str) -> str:
    """Return concatenated `//` lines above `package main`, stripped."""
    lines = []
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("package "):
            break
        if stripped.startswith("//"):
            lines.append(stripped[2:].strip())
        elif stripped == "" and lines:
            # blank inside comment block — keep as separator
            lines.append("")
        elif stripped == "":
            continue
        else:
            break
    # Collapse to single line, trim trailing blanks
    text = " ".join(l for l in lines if l).strip()
    return text


def detect_kind(cmd_name: str, src: str) -> str:
    if (any(p.match(cmd_name) for p in TOOL_NAME_PATTERNS)
            or cmd_name == "migrate"
            or cmd_name.startswith("kafka-topic")):
        return "tool"

    # Code-pattern checks
    if "grpc.NewServer" in src:
        return "server"
    if "outbox.NewOutboxPublisher" in src or "outbox publisher" in src.lower():
        return "worker"
    if re.search(r"\btickInterval\b\s*=", src) or "scheduler" in cmd_name.lower():
        return "scheduler"
    if "interval worker" in src.lower() or "sleep" in src.lower() and "rebate-settlement" in cmd_name:
        return "scheduler"
    if "watcher" in cmd_name.lower():
        return "scheduler"
    if "fiber.New(" in src or "app.Listen(" in src:
        return "server"
    if "pkgkafka.NewConsumer" in src or "kafkaadapter.New" in src:
        return "consumer"

    # Default fallback — treat as consumer (most common)
    return "consumer"


PORT_HARDCODED_RE = re.compile(r'app\.Listen\(":(\d+)"\)')
PORT_LISTEN_FN_RE = re.compile(r'app\.Listen\(":?\$?\{?(\w+)\}?"\)')
PORT_CONFIG_RE = re.compile(r'config\.(\w+)\.Port')
PORT_SIMPLE_CONFIG_RE = re.compile(r'config\.Port\b')
PORT_SERVERADDR_RE = re.compile(r'port\s*:?=\s*(\d+)')


def detect_port(src: str, kind: str) -> str:
    if kind != "server":
        return ""
    m = PORT_HARDCODED_RE.search(src)
    if m:
        return m.group(1)
    m = PORT_SERVERADDR_RE.search(src)
    if m:
        return m.group(1)
    m = PORT_CONFIG_RE.search(src)
    if m:
        return "${" + re.sub(r"([a-z])([A-Z])", r"\1_\2", m.group(1)).upper() + "_PORT}"
    if PORT_SIMPLE_CONFIG_RE.search(src):
        return "${PORT}"
    return ""


def deployable_from_kind(kind: str) -> str:
    return "no" if kind == "tool" else "yes"


def git_head_sha(repo_path: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except subprocess.CalledProcessError:
        return ""


def git_branch(repo_path: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except subprocess.CalledProcessError:
        return ""


def build_rows(services: list[dict], existing: dict[tuple[str, str], str]) -> list[dict]:
    rows = []
    for svc in services:
        svc_name = svc["service"]
        svc_root = Path(svc["path"])
        cmd_root = svc_root / "cmd"
        dockerfile = find_dockerfile(svc_root)

        for cmd_dir in sorted(cmd_root.iterdir()):
            if not cmd_dir.is_dir():
                continue
            cmd_name = cmd_dir.name
            src = read_main_go(cmd_dir)
            kind = detect_kind(cmd_name, src)
            port = detect_port(src, kind)

            existing_desc = existing.get((svc_name, cmd_name))
            if existing_desc:
                description = existing_desc
            else:
                top = extract_top_comment(src)
                description = f"[TODO review] {top}" if top else f"[TODO review] {cmd_name}"

            rows.append({
                "service": svc_name,
                "cmd_name": cmd_name,
                "cmd_path": f"./cmd/{cmd_name}",
                "dockerfile_path": dockerfile,
                "kind": kind,
                "deployable": deployable_from_kind(kind),
                "port": port,
                "description": description,
            })
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_meta(services: list[dict], extracted_by: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    rows = []
    for svc in services:
        svc_root = Path(svc["path"])
        rows.append({
            "service": svc["service"],
            "last_extracted_at": now,
            "extracted_by": extracted_by,
            "source_commit_sha": git_head_sha(svc_root) or "UNKNOWN",
            "source_branch": git_branch(svc_root) or "UNKNOWN",
            "notes": "",
        })
    write_csv(META_CSV, rows, META_FIELDS)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="dry-run; exit 1 if the regenerated CSV would differ")
    ap.add_argument("--by", default="claude", choices=["user", "claude", "ci"],
                    help="value for `extracted_by` in entrypoints.meta.csv")
    args = ap.parse_args()

    services = load_services()
    existing = load_existing_descriptions()
    all_rows = build_rows(services, existing)
    # Exclude tool-kind rows — entrypoints.csv lists only deployable workloads
    rows = [r for r in all_rows if r["kind"] != "tool"]

    if args.check:
        # Compare against on-disk CSV
        on_disk = []
        if OUT_CSV.exists():
            with OUT_CSV.open() as f:
                on_disk = list(csv.DictReader(f))
        new_keys = {(r["service"], r["cmd_name"]) for r in rows}
        old_keys = {(r["service"], r["cmd_name"]) for r in on_disk}
        added = new_keys - old_keys
        removed = old_keys - new_keys
        if added or removed:
            for k in sorted(added):
                print(f"+ {k[0]} / {k[1]}")
            for k in sorted(removed):
                print(f"- {k[0]} / {k[1]}")
            return 1
        # Field-level diff
        on_disk_map = {(r["service"], r["cmd_name"]): r for r in on_disk}
        changed = []
        for r in rows:
            old = on_disk_map.get((r["service"], r["cmd_name"]))
            if old:
                for f in OUT_FIELDS:
                    if old.get(f, "") != r[f]:
                        changed.append((r["service"], r["cmd_name"], f, old.get(f, ""), r[f]))
        if changed:
            for svc, cmd, field, old_v, new_v in changed:
                print(f"~ {svc} / {cmd} / {field}: {old_v!r} → {new_v!r}")
            return 1
        print("entrypoints.csv is up to date")
        return 0

    write_csv(OUT_CSV, rows, OUT_FIELDS)
    write_meta(services, args.by)

    print(f"wrote {OUT_CSV.relative_to(REPO_ROOT)} ({len(rows)} rows)")
    print(f"wrote {META_CSV.relative_to(REPO_ROOT)} ({len(services)} services)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
