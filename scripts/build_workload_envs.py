"""
Phase 3: Build per-workload structured env CSVs by parsing K8s YAML manifests.

For each PRD workload mapped to a backend cmd:
1. Parse its deployment yaml (multi-doc safe_load_all)
2. Extract container.env[*].name (inline envs) + container.envFrom[*] refs
3. Resolve refs by parsing sibling ConfigMap/Secret yamls in same directory
4. Write workload-envs/<workload>.csv with env_name + source

Schema:
    env_name,source
where source ∈ {inline, configmap:<name>, secret:<name>, externalsecret-unresolved:<name>}
"""
import csv
import yaml
from pathlib import Path
from collections import defaultdict

REPO = Path("/Users/kittiphong/Desktop/codes/claude/ontrust-mission-control")
INFRA = Path("/Users/kittiphong/Desktop/codes/terraform/aeternix-crm")
WORKLOADS_CSV = REPO / "artifacts-infra" / "k8s-workloads.csv"
OUT_DIR = REPO / "artifacts-infra" / "workload-envs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_yaml_docs(path):
    if not path.exists():
        return []
    with path.open() as f:
        try:
            return [d for d in yaml.safe_load_all(f) if d]
        except yaml.YAMLError:
            return []

def find_workload_doc(docs, kind_filter=None):
    """Return first doc matching Deployment/StatefulSet/Job."""
    targets = kind_filter or {"Deployment", "StatefulSet", "Job"}
    for d in docs:
        if d and d.get("kind") in targets:
            return d
    return None

def extract_container_envs(deploy_doc):
    """Return (inline_envs, envfrom_refs).

    inline_envs: list of (name, source_descriptor) from container.env
    envfrom_refs: list of (kind, name) from container.envFrom
    """
    inline = []
    envfrom = []
    if not deploy_doc:
        return inline, envfrom
    spec = deploy_doc.get("spec", {})
    template = spec.get("template", {}) if isinstance(spec, dict) else {}
    pod_spec = template.get("spec", {}) if isinstance(template, dict) else spec
    containers = pod_spec.get("containers", []) if isinstance(pod_spec, dict) else []
    for c in containers:
        for env in (c.get("env") or []):
            name = env.get("name")
            if not name:
                continue
            vf = env.get("valueFrom") or {}
            if "configMapKeyRef" in vf:
                src = f"inline-cm-ref:{vf['configMapKeyRef'].get('name','?')}"
            elif "secretKeyRef" in vf:
                src = f"inline-secret-ref:{vf['secretKeyRef'].get('name','?')}"
            else:
                src = "inline-literal"
            inline.append((name, src))
        for ef in (c.get("envFrom") or []):
            if "configMapRef" in ef:
                envfrom.append(("configmap", ef["configMapRef"].get("name","?")))
            elif "secretRef" in ef:
                envfrom.append(("secret", ef["secretRef"].get("name","?")))
    return inline, envfrom

def find_manifest_keys(search_dirs, kind, name):
    """Search yaml files in given dirs for a manifest matching kind+name.

    Returns (status, keys):
      status ∈ {found, not_found, externalsecret, unparseable}
      keys: list of env names (or empty)
    """
    for d in search_dirs:
        if not d.exists():
            continue
        for yml in d.glob("*.yaml"):
            for doc in load_yaml_docs(yml):
                if not doc:
                    continue
                meta_name = doc.get("metadata", {}).get("name")
                kind_d = doc.get("kind")
                if meta_name != name:
                    continue
                if kind == "configmap" and kind_d == "ConfigMap":
                    data = doc.get("data") or {}
                    return ("found", sorted(data.keys()))
                if kind == "secret":
                    if kind_d == "Secret":
                        # gather all data keys
                        keys = list((doc.get("data") or {}).keys())
                        keys += list((doc.get("stringData") or {}).keys())
                        return ("found", sorted(set(keys)))
                    if kind_d == "ExternalSecret":
                        # try to extract keys from spec.data[].secretKey or spec.target.template.data
                        spec = doc.get("spec", {})
                        keys = []
                        for d_item in (spec.get("data") or []):
                            sk = d_item.get("secretKey")
                            if sk:
                                keys.append(sk)
                        tgt_template = (spec.get("target") or {}).get("template", {})
                        for k in (tgt_template.get("data") or {}).keys():
                            keys.append(k)
                        if keys:
                            return ("externalsecret-templated", sorted(set(keys)))
                        # dataFrom + extract → keys are sourced from upstream, unknown
                        return ("externalsecret-opaque", [])
    return ("not_found", [])

# Read workloads
workloads = []
with WORKLOADS_CSV.open(newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        workloads.append(r)

# Process workloads that map to a backend cmd
deployed = [w for w in workloads
            if w.get("entrypoint_service") not in ("n/a", "", None)]

print(f"Processing {len(deployed)} workloads (mapped to backend cmds) ...")

written = 0
unresolved_summary = []
for w in deployed:
    workload = w["workload"]
    source_path = w["source_path"]
    yml = INFRA / source_path
    if not yml.exists():
        # source_path might be a directory
        if (INFRA / source_path).is_dir():
            # find a yaml that names this workload (e.g., archiver.yaml)
            yml = (INFRA / source_path) / f"{workload}.yaml"
        if not yml.exists():
            print(f"  ! {workload}: source yaml not found at {source_path}")
            unresolved_summary.append((workload, "yaml_not_found", source_path))
            continue

    docs = load_yaml_docs(yml)
    deploy_doc = find_workload_doc(docs)
    if not deploy_doc:
        print(f"  ! {workload}: no Deployment/StatefulSet/Job in {yml.name}")
        unresolved_summary.append((workload, "no_workload_kind", str(yml)))
        continue

    inline, envfrom = extract_container_envs(deploy_doc)

    # Resolve envFrom refs
    search_dirs = [yml.parent]
    # also check parent dir for shared configmaps
    if yml.parent.parent.exists():
        search_dirs.append(yml.parent.parent)

    rows = []
    for name, src in inline:
        rows.append((name, src))
    for kind, ref_name in envfrom:
        status, keys = find_manifest_keys(search_dirs, kind, ref_name)
        src_label = f"{kind}:{ref_name}"
        if status == "found":
            for k in keys:
                rows.append((k, src_label))
        elif status == "externalsecret-templated":
            for k in keys:
                rows.append((k, f"externalsecret:{ref_name}"))
        else:
            # unresolved — record placeholder row
            rows.append((f"({status})", src_label))
            unresolved_summary.append((workload, status, ref_name))

    # Sort + dedupe (env_name, source)
    rows = sorted(set(rows), key=lambda x: (x[0], x[1]))

    # Write CSV
    out = OUT_DIR / f"{workload}.csv"
    with out.open("w", newline="") as f:
        ww = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        ww.writerow(["env_name", "source"])
        ww.writerows(rows)
    written += 1

print(f"\nWrote {written} workload-envs CSVs at {OUT_DIR.relative_to(REPO)}")

if unresolved_summary:
    print(f"\nUnresolved refs ({len(unresolved_summary)}):")
    for w, status, info in unresolved_summary:
        print(f"  {w}: {status} ({info})")
