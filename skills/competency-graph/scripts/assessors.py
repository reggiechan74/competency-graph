#!/usr/bin/env python3
"""The people who rate the owner's competencies: list them, and write the list saved on the dashboard into the config.

An assessor (a supervisor, counsellor, manager or peer) is kept in competency-graph.yaml, under an id that never
changes, with the name a rating is recorded under and an optional role:

    assessors:
      dana-okafor: {name: Dana Okafor, role: APC counsellor}

A rating itself stays in the competency's note, one an assessor (`assessments`, each "<name> | <level> | <date>";
Specification §3.9). This list only says who can be picked: on the dashboard, the Assessor dropdown on
each tab with an Assessed column.

    assessors.py list                                  the assessors in the config
    assessors.py apply --from <dir> [--apply]          the list saved on the dashboard's Configuration tab -> the config

`apply` reads an ArtifactData export of the dashboard's `settings` collection (`action: list`, `collection: settings`,
`out_dir: <dir>`) and finds the document `assessors`: {list: [{id, name, role}], savedAt}. It prints the new
`assessors:` block and what changes (added, removed, renamed, a role changed); `--apply` writes that block of
competency-graph.yaml and nothing else in it. Removing an assessor never touches a note: the ratings they gave stay,
under their name. Renaming one does: the notes that record a rating under the old name are listed, and with `--apply`
a plan for `edit_links.py plan` is written to the `working` folder (or `--plan`) that moves each such rating to the
new name. Then delete the applied document from `settings`, and rebuild and refresh the dashboard.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_graph as cg  # noqa: E402
import frameworks as fw  # noqa: E402
import kg_config as kc  # noqa: E402

COLUMNS = ["id", "name", "role"]


class AssessorError(Exception):
    pass


def rows(assessors: dict) -> list[dict]:
    """The dashboard's data file: one row an assessor, in the config's order."""
    return [{"id": aid, "name": a["name"], "role": a.get("role", "")} for aid, a in (assessors or {}).items()]


def render(assessors: dict) -> str:
    """The `assessors:` block of the config."""
    if not assessors:
        return "assessors: {}\n"
    lines = ["assessors:"]
    for aid, a in assessors.items():
        fields = [f"name: {fw.yq(a['name'])}"] + ([f"role: {fw.yq(a['role'])}"] if a.get("role") else [])
        lines.append(f"  {aid}: {{{', '.join(fields)}}}")
    return "\n".join(lines) + "\n"


def load_saved(src: str) -> dict:
    """{id: {name, role}} from an export of the dashboard's `settings` collection (or the one document)."""
    paths = [src] if os.path.isfile(src) else sorted(glob.glob(os.path.join(src, "**", "*.json"), recursive=True))
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        for d in data if isinstance(data, list) else [data]:
            if not isinstance(d, dict):
                continue
            doc = d.get("data") if isinstance(d.get("data"), dict) else d
            did = str(d.get("id") or os.path.basename(p)[:-5])
            if isinstance(doc.get("list"), list) and (did.endswith("assessors") or len(paths) == 1):
                raw = {}
                for a in doc["list"]:
                    if not isinstance(a, dict) or not a.get("id"):
                        raise AssessorError(f"{p}: an assessor with no id: {a!r}")
                    if a["id"] in raw:
                        raise AssessorError(f"{p}: two assessors share the id {a['id']!r}")
                    raw[a["id"]] = {"name": a.get("name"), **({"role": a["role"]} if a.get("role") else {})}
                try:
                    return kc.check_assessors(raw)
                except kc.ConfigError as exc:
                    raise AssessorError(f"{p}: {exc}") from None
    raise AssessorError(f"no saved list of assessors ({{list: [...]}}) found in {src}")


def changes(old: dict, new: dict) -> dict:
    """{added, removed, renamed: [(id, old name, new name)], roles: [(id, old role, new role)]}."""
    return {
        "added": [i for i in new if i not in old],
        "removed": [i for i in old if i not in new],
        "renamed": [(i, old[i]["name"], new[i]["name"]) for i in new if i in old and old[i]["name"] != new[i]["name"]],
        "roles": [(i, old[i].get("role", ""), new[i].get("role", "")) for i in new
                  if i in old and old[i].get("role", "") != new[i].get("role", "")],
    }


def rename_plan(cfg, renamed: list) -> list[dict]:
    """edit_links plan entries: every note whose rating is recorded under a renamed assessor's old name."""
    if not renamed:
        return []
    to = {old: new for _, old, new in renamed}
    exclude = cg.DEFAULT_EXCLUDE | set(cg.load_settings(cfg.profile)["exclude"])
    _, nodes, _ = cg.scan_vault(cfg.vault, exclude)
    low = {old.casefold(): new for old, new in to.items()}
    plan = []
    for node in nodes.values():
        for r in cg.assessments_of(node.fm)[0]:
            new = low.get(r["by"].casefold())
            if new:                                    # the rating under the old name goes, and comes back under the new
                why = f"assessor renamed from {r['by']}"
                plan += [{"note": node.name, "field": "assessedLevel", "unset": True, "assessedBy": r["by"], "why": why},
                         {"note": node.name, "field": "assessedLevel", "set": r["level"], "assessedBy": new,
                          "assessedOn": r["on"], "why": why}]
    return plan


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    kc.add_arguments(ap)
    ap.add_argument("--profile")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="the assessors in the config")
    a = sub.add_parser("apply", help="write the list saved on the dashboard into the config")
    a.add_argument("--from", dest="src", required=True, help="ArtifactData export of the dashboard's `settings` collection")
    a.add_argument("--apply", action="store_true", help="write competency-graph.yaml (default: dry run)")
    a.add_argument("--plan", help="where to write the edit_links plan for renamed assessors (default: the `working` folder)")
    args = ap.parse_args(argv)
    try:
        cfg = kc.from_args(args)
    except kc.ConfigError as exc:
        print(f"assessors: {exc}", file=sys.stderr)
        return 2
    if args.cmd == "list":
        for aid, x in cfg.assessors.items():
            print(f"{aid:<20} {x['name']}" + (f"  ({x['role']})" if x["role"] else ""))
        if not cfg.assessors:
            print("no assessors in the config", file=sys.stderr)
        return 0
    if not cfg.path:
        print("apply: needs a competency-graph.yaml to write to", file=sys.stderr)
        return 2
    try:
        new = load_saved(args.src)
    except (AssessorError, OSError, ValueError) as exc:
        print(f"apply: {exc}", file=sys.stderr)
        return 2
    ch = changes(cfg.assessors, new)
    block = render(new)
    print(block, end="")
    for i in ch["added"]:
        print(f"added:   {new[i]['name']}", file=sys.stderr)
    for i in ch["removed"]:
        print(f"removed: {cfg.assessors[i]['name']} (the ratings they gave stay in the notes)", file=sys.stderr)
    for _, was, now in ch["renamed"]:
        print(f"renamed: {was} -> {now}", file=sys.stderr)
    for i, was, now in ch["roles"]:
        print(f"role:    {new[i]['name']}: {was or '(none)'} -> {now or '(none)'}", file=sys.stderr)
    plan = rename_plan(cfg, ch["renamed"])
    for e in plan:
        if "set" in e:
            print(f"  {e['note']}: the rating moves to {e['assessedBy']}", file=sys.stderr)
    if not any(ch.values()):
        print("nothing to change: the saved list is the config's", file=sys.stderr)
        return 0
    if not args.apply:
        print("(dry run: add --apply to write competency-graph.yaml)", file=sys.stderr)
        return 0
    with open(cfg.path, encoding="utf-8") as fh:
        old_text = fh.read()
    with open(cfg.path, "w", encoding="utf-8") as fh:
        fh.write(fw.replace_block(old_text, "assessors", block))
    try:                                   # it must read back as exactly the list saved
        if kc.read_config(cfg.path).assessors != new:
            raise AssessorError("the written config does not read back as the saved list")
    except (kc.ConfigError, AssessorError) as exc:
        with open(cfg.path, "w", encoding="utf-8") as fh:
            fh.write(old_text)
        print(f"apply: {exc}; competency-graph.yaml left as it was", file=sys.stderr)
        return 2
    print(f"wrote `assessors:` in {cfg.path}", file=sys.stderr)
    if plan:
        out = args.plan or cfg.new_file("working", "Assessor_Renames.yaml", mkdir=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("# Ratings recorded under an assessor's old name. Apply with: edit_links.py plan <this file> --apply\n")
            yaml.safe_dump(plan, fh, sort_keys=False, allow_unicode=True)
        print(f"{sum('set' in e for e in plan)} rating(s) recorded under an old name -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
