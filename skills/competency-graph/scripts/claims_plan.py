#!/usr/bin/env python3
"""Turn level changes saved on the dashboard into an edit_links.py plan (Specification v0.5).

The dashboard (assets/dashboard/index.html) keeps each saved change as one document in its store's
`claims` collection: {key, note, framework, requirement, title, from, to, savedAt}. A document with
`field: assessedLevel` is one assessor's rating and carries `by`, the assessor's name (several assessors may each
have one for the same competency); the others are the owner's own claimed levels. Export them with the
ArtifactData tool (`action: list`, `collection: claims`, `out_dir: <dir>`), then:

    claims_plan.py --from <dir> [--out plan.yaml]

<dir> is searched for *.json files, one per document (the file name is the document id). A file holding a
list of {id, data} objects also works.

Writes a plan for `edit_links.py plan`:
    - a change to a level  -> {note, field: claimedLevel, set: <level>}
    - a change to Not rated -> {note, field: claimedLevel, unset: true}
    - an assessor's rating  -> {note, field: assessedLevel, set: <level>, assessedBy: <the document's `by`>,
                                assessedOn: <the day it was saved>}
      (to Not rated: unset with assessedBy, which removes that assessor's rating and leaves the others')
Changes for a framework competency that is not in the graph yet (no `note`, with `framework` and
`requirement`) are NOT in the plan: they need a new competency note, and its placement needs the owner's
approval first (SKILL.md ground rule 1). They are listed under `newCompetencies` in a second file
(`<out>.new.yaml`) and printed.

After applying the plan, delete the applied documents from `claims` and refresh the dashboard.
Read-only except for the files it writes.
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

LEVELS = {"", "aware", "practitioner", "advanced", "expert"}


def load_claims(src: str) -> list[dict]:
    """Return [{id, ...fields}] from a folder of per-document JSON files or one JSON list."""
    docs = []
    if os.path.isdir(src):
        for path in sorted(glob.glob(os.path.join(src, "**", "*.json"), recursive=True)):
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and "id" in data:
                docs.append({"id": data["id"], **data["data"]})
            elif isinstance(data, dict):
                docs.append({"id": os.path.basename(path)[:-5], **data})
    else:
        with open(src, encoding="utf-8") as fh:
            data = json.load(fh)
        for d in data if isinstance(data, list) else [data]:
            docs.append({"id": d.get("id"), **(d.get("data") or {})} if "data" in d else dict(d))
    return docs


def build(docs: list[dict]):
    plan, new, problems = [], [], []
    for d in docs:
        to = cg.normalize_level(d.get("to", "")) if d.get("to") else ""
        if to not in LEVELS:
            problems.append(f"{d.get('id')}: level {d.get('to')!r} is not one of aware, practitioner, advanced, expert or blank")
            continue
        saved = f"saved on the dashboard {d.get('savedAt', '')}; was {cg.level_label(d.get('from')) if d.get('from') else 'not rated'}"
        field = d.get("field") or "claimedLevel"
        if field not in cg.LEVEL_FIELDS:
            problems.append(f"{d.get('id')}: `field: {field}` is not claimedLevel or assessedLevel")
            continue
        assessed = field == "assessedLevel"
        # the day it was given: the assessor's own date where the page recorded one (savedAt is UTC)
        by, on = str(d.get("by") or "").strip(), str(d.get("on") or d.get("savedAt") or "")[:10]
        if assessed and not by:                    # a note keeps a rating an assessor: whose this is must be known
            problems.append(f"{d.get('id')}: an assessor's rating with no assessor named (`by`)")
            continue
        if d.get("note"):
            entry = {"note": d["note"], "field": field}
            entry.update({"unset": True} if to == "" else {"set": to})
            if assessed:
                entry.update({"assessedBy": by, **({"assessedOn": on} if on and to else {})})
            entry.update({"claim": d.get("id"), "why": saved})
            plan.append(entry)
        elif d.get("framework") or d.get("requirement") or d.get("rics"):
            new.append({"claim": d.get("id"), "framework": d.get("framework") or ("RICS APC" if d.get("rics") else ""),
                        "requirement": d.get("requirement") or d.get("rics"), "level": to or "not rated",
                        **({"field": field, "assessedBy": by, "assessedOn": on} if assessed else {}), "why": saved})
        else:
            problems.append(f"{d.get('id')}: names neither a note nor a framework competency")
    return plan, new, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    cg.kc.add_arguments(ap)
    ap.add_argument("--from", dest="src", required=True, help="folder (or JSON file) of exported `claims` documents")
    ap.add_argument("--out", help="plan file (default: dated file in the `working` folder)")
    args = ap.parse_args(argv)
    if not args.out:
        cfg = cg.kc.load(args.config, args.vault, None, os.getcwd(), required=False)
        if cfg is None:
            print("give --out, or run inside a vault with a competency-graph.yaml", file=sys.stderr)
            return 2
        args.out = cfg.new_file("working", "Dashboard_Claims.yaml", mkdir=True)
    plan, new, problems = build(load_claims(args.src))
    for p in problems:
        print("SKIPPED:", p, file=sys.stderr)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# Level changes saved on the dashboard: the owner's claimed levels, and assessors' ratings (assessedLevel,\n")
        fh.write("# with assessedBy and assessedOn). Apply with: edit_links.py plan <this file> --apply\n")
        fh.write("# Then delete the applied documents (`claim` ids) from the dashboard's `claims` collection.\n")
        yaml.safe_dump(plan, fh, sort_keys=False, allow_unicode=True)
    print(f"{len(plan)} change(s) -> {args.out}")
    if new:
        new_path = args.out[:-5] + ".new.yaml" if args.out.endswith(".yaml") else args.out + ".new.yaml"
        with open(new_path, "w", encoding="utf-8") as fh:
            fh.write("# Levels saved for framework competencies not in the graph. Propose each one's placement to the\n")
            fh.write("# owner; once approved, create the note with this level and its externalRef.\n")
            yaml.safe_dump({"newCompetencies": new}, fh, sort_keys=False, allow_unicode=True)
        print(f"{len(new)} new competency request(s) -> {new_path}")
        for n in new:
            print(f"  - {n['framework']}: {n['requirement']} at {n['level']}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
