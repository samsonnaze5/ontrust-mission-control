"""
Phase 4: Cross-check engine + Markdown report.

Compares per deployed cmd:
- ENVS: code-required (entrypoint-envs/) vs infra-provided (workload-envs/)
- KAFKA: code direction/topic/CG (entrypoint-kafka/) vs infra workload mapping (kafka-consumers.csv) + topic existence (kafka-topics.csv)

Output: artifacts-infra/cross-check-report.md
"""
import csv
import yaml
from pathlib import Path
from collections import defaultdict

REPO = Path("/Users/kittiphong/Desktop/codes/claude/ontrust-mission-control")
INFRA_DIR = REPO / "artifacts-infra"
WORKLOADS_CSV = INFRA_DIR / "k8s-workloads.csv"
KAFKA_CONSUMERS_CSV = INFRA_DIR / "kafka-consumers.csv"
KAFKA_TOPICS_CSV = INFRA_DIR / "kafka-topics.csv"
EP_ENVS_DIR = INFRA_DIR / "entrypoint-envs"
EP_KAFKA_DIR = INFRA_DIR / "entrypoint-kafka"
WL_ENVS_DIR = INFRA_DIR / "workload-envs"
ENVS_CATALOG = REPO / "artifacts" / "envs.csv"
REPORT = INFRA_DIR / "cross-check-report.md"

# ─── Load all input data ────────────────────────────────────────────────

# workload → (entrypoint_service, entrypoint_cmd)
wl_to_cmd = {}
# (service, cmd) → workload (forward)
cmd_to_wl = {}
all_workloads = []
with WORKLOADS_CSV.open(newline="") as f:
    for r in csv.DictReader(f):
        wl = r["workload"]
        svc = r.get("entrypoint_service", "")
        cmd = r.get("entrypoint_cmd", "")
        all_workloads.append(wl)
        if svc and svc != "n/a" and cmd != "n/a":
            wl_to_cmd[wl] = (svc, cmd)
            # one cmd may have multiple workloads (legacy + new); keep mapping list
            cmd_to_wl.setdefault((svc, cmd), []).append(wl)

# kafka-consumers (infra view): workload → (consumer_group, topics_in, topics_out)
kc_by_wl = {}
with KAFKA_CONSUMERS_CSV.open(newline="") as f:
    for r in csv.DictReader(f):
        wl = r["workload"]
        kc_by_wl[wl] = {
            "consumer_group": r.get("consumer_group", ""),
            "topics_in":  [t.strip() for t in (r.get("topics_in") or "").split(";") if t.strip()],
            "topics_out": [t.strip() for t in (r.get("topics_out") or "").split(";") if t.strip()],
            "role": r.get("role", ""),
        }

# kafka-topics (infra view): set of topic names
infra_topics = set()
with KAFKA_TOPICS_CSV.open(newline="") as f:
    for r in csv.DictReader(f):
        infra_topics.add(r["topic"])

# envs.csv catalog (set of canonical env names)
catalog_envs = set()
with ENVS_CATALOG.open(newline="") as f:
    for r in csv.DictReader(f):
        catalog_envs.add(r["env_name"])

# Load entrypoint-envs (code-required) and entrypoint-kafka (code-kafka) per cmd
def load_envs_csv(p):
    if not p.exists(): return set()
    with p.open(newline="") as f:
        rd = csv.DictReader(f)
        return {row["env_name"] for row in rd if row.get("env_name")}

def load_kafka_csv(p):
    """Return dict: 'in' → set of (topic, cg), 'out' → set of topic"""
    out = {"in": set(), "out": set()}
    if not p.exists(): return out
    with p.open(newline="") as f:
        for r in csv.DictReader(f):
            d = r.get("direction")
            if d == "in":
                out["in"].add((r.get("topic",""), r.get("consumer_group","")))
            elif d == "out":
                out["out"].add(r.get("topic",""))
    return out

# Load workload-envs (infra-provided) per workload
def load_workload_envs(wl):
    p = WL_ENVS_DIR / f"{wl}.csv"
    if not p.exists(): return set()
    with p.open(newline="") as f:
        rd = csv.DictReader(f)
        return {row["env_name"] for row in rd if row.get("env_name")}

# ─── Build cross-check ───────────────────────────────────────────────────
# Walk all cmds (44) — for each, do the comparison if deployed
# Also identify orphan workloads (in K8s but no cmd mapped)

cmds = []
for svc_dir in sorted(EP_ENVS_DIR.iterdir()):
    if not svc_dir.is_dir(): continue
    svc = svc_dir.name
    for f in sorted(svc_dir.iterdir()):
        if f.suffix != ".csv": continue
        cmds.append((svc, f.stem))

# Counts for summary
n_cmds = len(cmds)
n_deployed = 0
n_env_clean = 0
n_env_missing = 0
n_kafka_clean = 0
n_kafka_issues = 0

cmd_findings = []  # list of dicts with all comparison data

for svc, cmd in cmds:
    code_envs = load_envs_csv(EP_ENVS_DIR / svc / f"{cmd}.csv")
    code_kafka = load_kafka_csv(EP_KAFKA_DIR / svc / f"{cmd}.csv")
    workloads = cmd_to_wl.get((svc, cmd), [])
    if not workloads:
        cmd_findings.append({
            "svc": svc, "cmd": cmd, "deployed": False,
            "code_envs": code_envs, "code_kafka": code_kafka,
            "workloads": [],
        })
        continue
    n_deployed += 1
    for wl in workloads:
        infra_envs = load_workload_envs(wl)
        infra_kc   = kc_by_wl.get(wl, {})
        # Env diff
        missing_in_infra = sorted(code_envs - infra_envs)
        unused_in_code   = sorted(infra_envs - code_envs)
        # Kafka diff
        kafka_issues = []
        # in: code expects (topic, cg) → infra workload has (consumer_group, topics_in)
        infra_in_topics = set(infra_kc.get("topics_in", []))
        infra_in_cg     = infra_kc.get("consumer_group", "")
        for (t, cg) in code_kafka["in"]:
            topic_match = t in infra_in_topics
            cg_match = (infra_in_cg == cg) if infra_in_cg and cg else False
            issue = {
                "direction": "in",
                "code_topic": t, "code_cg": cg,
                "infra_topic_match": topic_match,
                "infra_cg": infra_in_cg, "cg_match": cg_match,
                "topic_in_infra_catalog": t in infra_topics,
            }
            kafka_issues.append(issue)
        # out
        infra_out_topics = set(infra_kc.get("topics_out", []))
        for t in code_kafka["out"]:
            topic_match_workload = t in infra_out_topics
            topic_in_catalog     = t in infra_topics
            kafka_issues.append({
                "direction": "out",
                "code_topic": t, "code_cg": "",
                "infra_topic_match": topic_match_workload,
                "infra_cg": "", "cg_match": True,
                "topic_in_infra_catalog": topic_in_catalog,
            })

        if not missing_in_infra:
            n_env_clean += 1
        else:
            n_env_missing += 1
        # rough kafka cleanliness
        if kafka_issues and all(i["topic_in_infra_catalog"] and i["infra_topic_match"] and (i["cg_match"] or i["direction"]=="out")
                                for i in kafka_issues):
            n_kafka_clean += 1
        elif kafka_issues:
            n_kafka_issues += 1

        cmd_findings.append({
            "svc": svc, "cmd": cmd, "workload": wl, "deployed": True,
            "code_envs": code_envs, "infra_envs": infra_envs,
            "missing_in_infra": missing_in_infra,
            "unused_in_code": unused_in_code,
            "code_kafka": code_kafka,
            "infra_kc": infra_kc,
            "kafka_issues": kafka_issues,
        })

# Orphan workloads (not in cmd_to_wl)
orphan_wl = [wl for wl in all_workloads
             if wl not in wl_to_cmd]

# ─── Render report ───────────────────────────────────────────────────────

lines = []
def w(s=""): lines.append(s)

w("# Cross-Check Report — Backend Code vs PRD Infrastructure")
w()
w(f"_Generated: {Path(__file__).name} • Source: 5 backend repos × infra repo `aeternix-crm` (kubeflow/prd)_")
w()
w("This report compares **what the backend code requires** (entrypoints, envs, kafka topics + consumer groups) against **what's actually deployed in PRD K8s + Kafka**. Use it to spot drift, missing envs, name mismatches, and orphans.")
w()

w("## Summary")
w()
w(f"- **Backend cmds total:** {n_cmds}")
w(f"- **Cmds deployed in PRD:** {n_deployed} (linked via `k8s-workloads.csv.entrypoint_*`)")
w(f"- **Workload-cmd pairs analyzed:** {sum(1 for f_ in cmd_findings if f_.get('deployed'))}")
w(f"- **Env: all required satisfied (no missing):** {n_env_clean}")
w(f"- **Env: missing some envs in infra:** {n_env_missing}")
w(f"- **Kafka: clean (topic + CG match):** {n_kafka_clean}")
w(f"- **Kafka: at least 1 issue (topic missing / CG mismatch):** {n_kafka_issues}")
w(f"- **PRD workloads NOT mapped to a backend cmd:** {len(orphan_wl)} (Debezium / Python / Jobs / seeders)")
w()

# Action Items section — high-priority issues to fix
w("## Top Action Items for DevOps")
w()
action_envs = []
action_kafka = []
for f_ in cmd_findings:
    if not f_.get("deployed"): continue
    wl = f_["workload"]; svc = f_["svc"]; cmd = f_["cmd"]
    if f_["missing_in_infra"]:
        action_envs.append((wl, svc, cmd, f_["missing_in_infra"]))
    for issue in f_["kafka_issues"]:
        if not issue["topic_in_infra_catalog"]:
            action_kafka.append(("topic_missing_in_kafka_topics", wl, svc, cmd, issue["direction"], issue["code_topic"]))
        if issue["direction"] == "in" and not issue["infra_topic_match"]:
            action_kafka.append(("topic_missing_in_workload", wl, svc, cmd, issue["direction"], issue["code_topic"]))
        if issue["direction"] == "in" and not issue["cg_match"]:
            action_kafka.append(("cg_mismatch", wl, svc, cmd, issue["direction"], f"code={issue['code_cg']} infra={issue['infra_cg']}"))

if action_envs:
    w("### 🔴 ENV — Required envs missing in PRD ConfigMap/Secret")
    w()
    w("| Workload | Service | Cmd | Missing envs |")
    w("|---|---|---|---|")
    for wl, svc, cmd, missing in action_envs:
        w(f"| {wl} | {svc} | {cmd} | {', '.join(f'`{e}`' for e in missing)} |")
    w()
else:
    w("### ✅ ENV — All deployed cmds have their required envs in infra")
    w()

if action_kafka:
    w("### 🔴 KAFKA — Topic / Consumer-Group mismatches")
    w()
    w("| Type | Workload | Service / Cmd | Direction | Detail |")
    w("|---|---|---|---|---|")
    for typ, wl, svc, cmd, direction, detail in action_kafka:
        w(f"| {typ} | {wl} | {svc} / {cmd} | {direction} | {detail} |")
    w()
else:
    w("### ✅ KAFKA — All deployed cmds have matching topics + consumer groups")
    w()

# Per-cmd detail section
w("## Per-cmd Detail")
w()
w("Click through to inspect each deployed cmd's env + kafka comparison. Cmds NOT deployed in PRD are listed at the bottom.")
w()

# Group by service
by_svc = defaultdict(list)
for f_ in cmd_findings:
    by_svc[f_["svc"]].append(f_)

for svc in sorted(by_svc):
    w(f"### `{svc}`")
    w()
    for f_ in sorted(by_svc[svc], key=lambda x: x["cmd"]):
        cmd = f_["cmd"]
        if not f_.get("deployed"):
            w(f"#### `{cmd}` — _NOT deployed in PRD_")
            w()
            w(f"- Code-required envs: {len(f_['code_envs'])}")
            in_topics = sorted(t for (t,cg) in f_['code_kafka']['in'])
            out_topics = sorted(f_['code_kafka']['out'])
            if in_topics or out_topics:
                w(f"- Code Kafka: in=[{', '.join(in_topics) or '—'}] out=[{', '.join(out_topics) or '—'}]")
            w()
            continue
        wl = f_["workload"]
        w(f"#### `{cmd}` → workload `{wl}`")
        w()

        # ENV
        n_req = len(f_["code_envs"])
        n_have = len(f_["infra_envs"])
        miss = f_["missing_in_infra"]
        unused = f_["unused_in_code"]
        env_status = "✅ all satisfied" if not miss else f"🔴 {len(miss)} missing"
        w(f"**Env** — code requires {n_req} • infra provides {n_have} • {env_status}")
        if miss:
            w()
            w(f"- 🔴 Missing in infra: {', '.join(f'`{e}`' for e in miss)}")
        if unused:
            w()
            cat = [e for e in unused if e in catalog_envs]
            offcat = [e for e in unused if e not in catalog_envs]
            if cat:
                w(f"- 🟡 Set in infra but unused by code (still in `envs.csv`): {', '.join(f'`{e}`' for e in cat)}")
            if offcat:
                w(f"- 🟡 Set in infra but NOT in `envs.csv` catalog: {', '.join(f'`{e}`' for e in offcat)}")
        w()

        # KAFKA
        if f_["kafka_issues"]:
            ki = f_["kafka_issues"]
            in_issues  = [i for i in ki if i["direction"] == "in"]
            out_issues = [i for i in ki if i["direction"] == "out"]
            w(f"**Kafka**")
            if in_issues:
                w()
                w(f"- Inbound (consumer):")
                for i in in_issues:
                    flags = []
                    if not i["topic_in_infra_catalog"]:
                        flags.append("🔴 topic NOT in `kafka-topics.csv`")
                    elif i["infra_topic_match"]:
                        flags.append("✅ topic ok")
                    else:
                        flags.append("🔴 topic NOT linked to this workload in `kafka-consumers.csv`")
                    if i["cg_match"]:
                        flags.append("✅ CG match")
                    elif i["infra_cg"]:
                        flags.append(f"🔴 CG mismatch (code=`{i['code_cg']}` vs infra=`{i['infra_cg']}`)")
                    else:
                        flags.append(f"🔴 workload not in `kafka-consumers.csv` (no CG recorded)")
                    w(f"  - `{i['code_topic']}` → CG `{i['code_cg']}` — {' • '.join(flags)}")
            if out_issues:
                w()
                w(f"- Outbound (producer):")
                for i in out_issues:
                    flags = []
                    if i["topic_in_infra_catalog"]:
                        flags.append("✅ topic in `kafka-topics.csv`")
                    else:
                        flags.append("🔴 topic NOT in `kafka-topics.csv`")
                    if i["infra_topic_match"]:
                        flags.append("✅ workload registered as producer")
                    else:
                        flags.append("🟡 not listed under workload's `topics_out`")
                    w(f"  - `{i['code_topic']}` — {' • '.join(flags)}")
        else:
            w(f"**Kafka** — no kafka usage in this cmd")
        w()

# Orphan workloads
w("## Orphan PRD Workloads (no backend-cmd mapping)")
w()
w(f"These {len(orphan_wl)} workloads run in PRD but don't link to any of our 5 backend cmds (Python/Debezium/Jobs/seeders). For reference only — no action needed unless one should be migrated to a Go cmd.")
w()
w("```")
for wl in orphan_wl:
    w(f"- {wl}")
w("```")
w()

REPORT.write_text("\n".join(lines))
print(f"Wrote {REPORT.relative_to(REPO)} ({len(lines)} lines)")
print()
print("=== Summary stats ===")
print(f"  Cmds total: {n_cmds}")
print(f"  Cmds deployed: {n_deployed}")
print(f"  Env clean: {n_env_clean}")
print(f"  Env missing: {n_env_missing}")
print(f"  Kafka clean: {n_kafka_clean}")
print(f"  Kafka issues: {n_kafka_issues}")
print(f"  Orphan workloads: {len(orphan_wl)}")
print(f"  Action items — env: {len(action_envs)}; kafka: {len(action_kafka)}")
