#!/usr/bin/env python3
"""Job specs: roles the owner defines from framework competencies, scored on breadth and depth (Specification v0.5).

A job spec puts framework competencies (the skill's frameworks and the owner's own, `frameworks.py`) into three
sections, each with a required level on L1-L4: Mandatory, Core and Optional. The file is the record; the dashboard's
Job Specs tab shows it, scores the graph against it, and saves new or changed specs in its `jobspecs` collection
until Claude writes them back here with `merge`.

The file (config `jobSpecs`; default Job_Specs.yaml in the competencies folder):

    specs:
      manager-acquisition:                       # the spec's id: lowercase letters, digits and hyphens
        title: Manager, Property Acquisition
        note: Leads acquisitions for a transit agency   # optional
        next: senior-manager-acquisition         # optional: the next role up, for the promotion test
        probation: 80                            # optional: the Probation band's floor, % (default 80)
        exceeds: 20                              # optional: credit above the requirement, as % of the depth
                                                 # target, that makes Exceeds role (default 20)
        mandatory:
          - {ref: "RICS APC: Ethics, Rules of Conduct and professionalism", level: L3}
        core:
          - {ref: "RICS APC: Valuation", level: L2}
        optional:
          - {ref: "CFA CBOK: Private Markets", level: L1}

`ref` is written as in `externalRef`, without the edition year: "<framework>: <competency>".

Scoring, for each competency with required level r and level held a (0 when no competency in the graph maps to it
through `externalRef`; the highest when several do), weights W = 0, 1, 3, 9, 27 for L0-L4. The level held is read
on one of three bases: claimed (the owner's own rating), assessed (an assessor's rating, `assessedLevel`) or supported
(what the evidence backs):
    breadth   credited min(a, r) of target r
    depth     credited W[min(a, r)] of target W[r]
    above     W[a] - W[r] when a > r: credit above the requirement, kept apart so it never covers a gap
Optional competencies have no target: everything held there is credit above the requirement.
    gate      every Mandatory competency held at its level, or "Mandatory not met" whatever the totals say
    band      on Mandatory + Core, by the lower of breadth % and depth %: Below probation (< probation), Probation
              (< 100), Baseline (100: every requirement met), Exceeds role (Baseline, and Mandatory + Core credit
              above the requirement >= exceeds % of the depth target)
    promotion only with `next`: this spec at Baseline or better, and the next spec's gate met and its lower score at
              or above its own probation floor
    diagnosis depth % below breadth %: broad but shallow (the shortfalls are where higher levels are required);
              breadth % below depth %: deep but narrow (lower-level requirements are missing); else even
The dashboard's page scores the same way (window.spJob, its kg:jobscore block); the tests check that the two agree.

    job_specs.py [--config F | --vault V] list
    job_specs.py check                                 validate the file against the library
    job_specs.py build [--out FILE]                    write the dashboard's copy (Job_Specs.csv beside the file)
    job_specs.py score <id> [--basis claimed|assessed|supported] [--disclosure on-request|public]
    job_specs.py merge --from DIR [--apply]            write specs saved on the dashboard into the file

`merge` reads an ArtifactData export of the `jobspecs` collection: one document per saved spec, {id, title, note,
next, probation, exceeds, rows: [{section, framework, name, required}], deleted?}. A document with `deleted: true`
removes the spec. Dry run without --apply. Then `build`, refresh the dashboard's `jobspecs` dataset, and delete the
merged documents from the collection.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frameworks as fw  # noqa: E402
import kg_config as kc  # noqa: E402

SECTIONS = ("mandatory", "core", "optional")
SECTION_TITLES = {"mandatory": "Mandatory", "core": "Core", "optional": "Optional"}
LEVELS = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
WEIGHTS = [0, 1, 3, 9, 27]
RANK = {"": 0, "none": 0, "aware": 1, "practitioner": 2, "advanced": 3, "expert": 4}
SPEC_KEYS = {"title", "note", "next", "probation", "exceeds", *SECTIONS}
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
DEFAULT_PROBATION = 80
DEFAULT_EXCEEDS = 20
CSV_COLUMNS = ["spec", "title", "note", "next", "probation", "exceeds", "section", "order", "framework", "name",
               "required"]
HEADER = """\
# Job specs (competency-graph skill, job_specs.py). Each spec puts framework competencies in Mandatory, Core and
# Optional, each with a required level (L1-L4). `ref` is "<framework>: <competency>" as in externalRef, without the
# edition year. Optional per spec: note, next (the next role up), probation (%, default 80), exceeds (%, default 20).
# The dashboard's Job Specs tab shows these; specs saved there are written back here by `job_specs.py merge`.
"""


class SpecError(Exception):
    pass


def split_ref(ref: str) -> tuple[str, str]:
    """"RICS APC 2025: Valuation" -> ("RICS APC", "Valuation")."""
    head, sep, name = str(ref).partition(":")
    if not sep:
        return "", str(ref).strip()
    return re.sub(r"\s+\d{4}$", "", head.strip()), name.strip()


def library_names(lib: dict) -> dict:
    """{(framework, competency): framework id} for every competency the library names (requirements or descriptions)."""
    out = {}
    for fid, f in lib.items():
        for r in list(f["rows"]) + list(f["descriptions_rows"]):
            out[(f["framework"], r["name"])] = fid
    return out


def read_file(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise SpecError(f"{path}: not valid YAML ({exc})") from None
    if not isinstance(data, dict) or set(data) - {"specs"}:
        raise SpecError(f"{path}: expected one key, `specs`")
    specs = data.get("specs") or {}
    if not isinstance(specs, dict):
        raise SpecError(f"{path}: `specs` must map each spec's id to the spec")
    return specs


def normalise(sid: str, raw) -> dict:
    """A spec as the scripts use it: {id, title, note, next, probation, exceeds, rows: [{section, order, framework,
    name, required}]}. Raises SpecError on anything malformed (the library check is separate)."""
    if not ID.match(str(sid)):
        raise SpecError(f"spec id {sid!r}: use lowercase letters, digits and hyphens (up to 64)")
    if not isinstance(raw, dict):
        raise SpecError(f"{sid}: expected title, sections and settings")
    bad = set(raw) - SPEC_KEYS
    if bad:
        raise SpecError(f"{sid}: unknown key(s) {sorted(bad)}; allowed: {sorted(SPEC_KEYS)}")
    title = str(raw.get("title") or "").strip()
    if not title:
        raise SpecError(f"{sid}: needs a `title`")
    spec = {"id": str(sid), "title": title, "note": str(raw.get("note") or "").strip(),
            "next": str(raw.get("next") or "").strip(), "rows": []}
    for key, default in (("probation", DEFAULT_PROBATION), ("exceeds", DEFAULT_EXCEEDS)):
        v = raw.get(key, default)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 100:
            raise SpecError(f"{sid}: `{key}` must be a percentage from 0 to 100")
        spec[key] = int(v) if float(v).is_integer() else float(v)
    if spec["probation"] <= 0:
        raise SpecError(f"{sid}: `probation` must be above 0")
    seen = {}
    for section in SECTIONS:
        items = raw.get(section) or []
        if not isinstance(items, list):
            raise SpecError(f"{sid}.{section}: expected a list of {{ref, level}}")
        for i, item in enumerate(items, start=1):
            if not isinstance(item, dict) or set(item) - {"ref", "level"} or not item.get("ref"):
                raise SpecError(f"{sid}.{section}[{i}]: expected {{ref: \"Framework: Competency\", level: L1-L4}}")
            level = str(item.get("level") or "").strip().upper()
            if level not in LEVELS:
                raise SpecError(f"{sid}.{section}[{i}]: level {item.get('level')!r} is not one of L1-L4")
            framework, name = split_ref(item["ref"])
            if not framework:
                raise SpecError(f"{sid}.{section}[{i}]: ref {item['ref']!r} needs its framework (\"Framework: Name\")")
            if (framework, name) in seen:
                raise SpecError(f"{sid}: {framework}: {name} is in {seen[(framework, name)]} and {section}; "
                                "a competency goes in one section")
            seen[(framework, name)] = section
            spec["rows"].append({"section": section, "order": i, "framework": framework, "name": name,
                                 "required": level})
    if not spec["rows"]:
        raise SpecError(f"{sid}: lists no competencies")
    return spec


def load_specs(path: str) -> dict:
    """{id: spec} in file order."""
    return {sid: normalise(sid, raw) for sid, raw in read_file(path).items()}


def validate(specs: dict, lib: dict) -> list[str]:
    """Problems a spec has against the library and the other specs: unknown competencies, a `next` that names no
    spec or itself, a loop of `next`."""
    names = library_names(lib)
    problems = []
    for sid, s in specs.items():
        for r in s["rows"]:
            if (r["framework"], r["name"]) not in names:
                problems.append(f"{sid}: {r['framework']}: {r['name']} is not in the library "
                                f"(frameworks.py list --all; the owner's own frameworks count)")
        if s["next"]:
            if s["next"] == sid:
                problems.append(f"{sid}: `next` names the spec itself")
            elif s["next"] not in specs:
                problems.append(f"{sid}: `next` names {s['next']!r}, which is not a spec")
    for sid in specs:
        seen, cur = [], sid
        while cur in specs and specs[cur]["next"] and cur not in seen:
            seen.append(cur)
            cur = specs[cur]["next"]
        if cur == sid and seen:
            problems.append(f"{sid}: `next` goes round in a loop ({' -> '.join(seen + [sid])})")
    return problems


# ------------------------------------------------------------------ scoring (window.spJob in the page mirrors this)

def floor_pct(c: float, t: float):
    return None if not t else int(100 * c // t)


def score(spec: dict, level_of) -> dict:
    """level_of(framework, name) -> 0..4. Returns the rows' points, the totals, gate, band and diagnosis."""
    rows, tot = [], {s: {"bc": 0, "bt": 0, "dc": 0, "dt": 0, "above": 0, "n": 0, "met": 0} for s in SECTIONS}
    missing = short = 0
    gate_fail = 0
    for r in spec["rows"]:
        need, held = LEVELS[r["required"]], max(0, min(4, int(level_of(r["framework"], r["name"]) or 0)))
        opt = r["section"] == "optional"
        bc, bt = (0, 0) if opt else (min(held, need), need)
        dc, dt_ = (0, 0) if opt else (WEIGHTS[min(held, need)], WEIGHTS[need])
        above = WEIGHTS[held] if opt else max(0, WEIGHTS[held] - WEIGHTS[need])
        result = "above" if held > need else ("met" if held == need else ("short" if held else "missing"))
        if opt:
            result = "held" if held else "not-held"
        else:
            missing += result == "missing"
            short += result == "short"
            if r["section"] == "mandatory" and held < need:
                gate_fail += 1
        t = tot[r["section"]]
        t["bc"] += bc; t["bt"] += bt; t["dc"] += dc; t["dt"] += dt_; t["above"] += above; t["n"] += 1
        t["met"] += held >= need
        rows.append({**r, "held": held, "breadth": bc, "breadthTarget": bt, "depth": dc, "depthTarget": dt_,
                     "above": above, "result": result})
    bc = tot["mandatory"]["bc"] + tot["core"]["bc"]
    bt = tot["mandatory"]["bt"] + tot["core"]["bt"]
    dc = tot["mandatory"]["dc"] + tot["core"]["dc"]
    dt_ = tot["mandatory"]["dt"] + tot["core"]["dt"]
    above = tot["mandatory"]["above"] + tot["core"]["above"]
    bp, dp = floor_pct(bc, bt), floor_pct(dc, dt_)
    gate = "none" if not tot["mandatory"]["n"] else ("not-met" if gate_fail else "met")
    if not bt:
        band = "no-requirements"
    elif gate == "not-met":
        band = "mandatory-not-met"
    else:
        low = min(bp, dp)
        band = ("below" if low < spec["probation"] else "probation" if low < 100
                else "exceeds" if above * 100 >= spec["exceeds"] * dt_ else "baseline")
    if not bt or (not missing and not short):
        kind = "meets"
    elif dp < bp - 1:
        kind = "broad-shallow"
    elif bp < dp - 1:
        kind = "deep-narrow"
    else:
        kind = "even"
    return {"rows": rows, "sections": tot, "breadth": bc, "breadthTarget": bt, "depth": dc, "depthTarget": dt_,
            "breadthPct": bp, "depthPct": dp, "above": above, "optional": tot["optional"]["above"],
            "gate": gate, "gateShort": gate_fail, "missing": missing, "short": short, "band": band, "kind": kind}


def promotion(spec: dict, specs: dict, level_of, this: dict | None = None) -> dict | None:
    """None without `next`; else {ready, next, nextScore}: this spec at Baseline or better, and the next spec's gate
    met and its lower score at or above its own probation floor."""
    if not spec.get("next") or spec["next"] not in specs:
        return None
    this = this or score(spec, level_of)
    nxt = specs[spec["next"]]
    ns = score(nxt, level_of)
    low = min(x for x in (ns["breadthPct"], ns["depthPct"]) if x is not None) if ns["breadthTarget"] else 100
    ready = this["band"] in ("baseline", "exceeds") and ns["gate"] != "not-met" and low >= nxt["probation"]
    return {"ready": ready, "next": nxt["id"], "nextTitle": nxt["title"], "nextScore": ns}


BAND_WORDS = {"mandatory-not-met": "Mandatory not met", "below": "Below probation", "probation": "Probation",
              "baseline": "Baseline", "exceeds": "Exceeds role", "no-requirements": "No Mandatory or Core requirements"}


def diagnosis(s: dict) -> str:
    """The one sentence the dashboard shows beside the scores (the same words as the page's)."""
    n = lambda k, w: f"{k} {w}{'' if k == 1 else 's'}"  # noqa: E731
    if s["kind"] == "meets":
        return ("Meets every requirement" + (f", with {s['above']} depth points above it" if s["above"] else "")
                if s["breadthTarget"] else "Nothing required yet")
    counts = f"{n(s['missing'], 'requirement')} not held, {s['short']} held below the level"
    if s["kind"] == "broad-shallow":
        return f"Broad but shallow: the shortfalls are where the higher levels are required ({counts})"
    if s["kind"] == "deep-narrow":
        return f"Deep but narrow: lower-level requirements are missing ({counts})"
    return f"Short evenly across the requirements ({counts})"


# ------------------------------------------------------------------ the graph's levels

def graph_levels(cfg, disclosure: str = "on-request", today: dt.date | None = None) -> list[dict]:
    """The competency rows the dashboard reads (summary_graph.py), at this disclosure."""
    import summary_graph as sg
    s = sg.Summary(cfg.vault, cfg.profile, today or dt.date.today(), disclosure)
    return s.competencies()


def level_lookup(competencies: list[dict], basis: str):
    """(framework, name) -> the highest level among the graph's competencies whose externalRef names it."""
    best: dict = {}
    for c in competencies:
        lv = RANK.get(str(c.get(basis) or ""), 0)
        refs = c.get("externalRef") or []
        if isinstance(refs, str):
            refs = json.loads(refs) if refs.strip().startswith("[") else [refs]
        for ref in refs:
            k = split_ref(ref)
            best[k] = max(best.get(k, 0), lv)
    return lambda framework, name: best.get((framework, name), 0)


# ------------------------------------------------------------------ the file and the dashboard's copy

def csv_rows(specs: dict) -> list[dict]:
    out = []
    for s in specs.values():
        for r in s["rows"]:
            out.append({"spec": s["id"], "title": s["title"], "note": s["note"], "next": s["next"],
                        "probation": s["probation"], "exceeds": s["exceeds"], "section": r["section"],
                        "order": r["order"], "framework": r["framework"], "name": r["name"],
                        "required": r["required"]})
    return out


def write_csv(path: str, specs: dict) -> int:
    rows = csv_rows(specs)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def default_csv(path: str) -> str:
    return os.path.splitext(path)[0] + ".csv"


def render_yaml(specs: dict) -> str:
    """The file, written the same way every time: settings first, then the sections, one {ref, level} per line."""
    q = fw.yq
    lines = [HEADER.rstrip("\n"), "specs:" + ("" if specs else " {}")]
    for s in specs.values():
        lines.append(f"  {s['id']}:")
        lines.append(f"    title: {q(s['title'])}")
        for k in ("note", "next"):
            if s.get(k):
                lines.append(f"    {k}: {q(s[k])}")
        for k, d in (("probation", DEFAULT_PROBATION), ("exceeds", DEFAULT_EXCEEDS)):
            if s.get(k, d) != d:
                lines.append(f"    {k}: {s[k]}")
        for section in SECTIONS:
            rows = [r for r in s["rows"] if r["section"] == section]
            if not rows:
                continue
            lines.append(f"    {section}:")
            for r in sorted(rows, key=lambda r: r["order"]):
                lines.append(f"      - {{ref: {json.dumps(r['framework'] + ': ' + r['name'], ensure_ascii=False)}, "
                             f"level: {r['required']}}}")
    return "\n".join(lines) + "\n"


def to_raw(spec: dict) -> dict:
    """A normalised spec back to the file's shape (for normalise to read again)."""
    raw = {"title": spec["title"], "note": spec.get("note", ""), "next": spec.get("next", ""),
           "probation": spec.get("probation", DEFAULT_PROBATION), "exceeds": spec.get("exceeds", DEFAULT_EXCEEDS)}
    for section in SECTIONS:
        raw[section] = [{"ref": f"{r['framework']}: {r['name']}", "level": r["required"]}
                        for r in spec["rows"] if r["section"] == section]
    return raw


def load_docs(src: str) -> list[dict]:
    """The `jobspecs` documents from an ArtifactData export (a folder of per-document JSON files, or one JSON list)."""
    docs = []
    paths = [src] if os.path.isfile(src) else sorted(glob.glob(os.path.join(src, "**", "*.json"), recursive=True))
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        for d in data if isinstance(data, list) else [data]:
            if not isinstance(d, dict):
                continue
            doc = dict(d["data"]) if isinstance(d.get("data"), dict) else dict(d)
            doc["id"] = str(doc.get("id") or d.get("id") or os.path.basename(p)[:-5])
            docs.append(doc)
    return docs


def doc_to_spec(doc: dict) -> dict:
    """A saved document -> a normalised spec (raises SpecError)."""
    raw = {"title": doc.get("title"), "note": doc.get("note") or "", "next": doc.get("next") or "",
           "probation": doc.get("probation", DEFAULT_PROBATION), "exceeds": doc.get("exceeds", DEFAULT_EXCEEDS)}
    rows = doc.get("rows") or []
    if not isinstance(rows, list):
        raise SpecError(f"{doc['id']}: `rows` must be a list")
    order = sorted(rows, key=lambda r: (SECTIONS.index(r.get("section")) if r.get("section") in SECTIONS else 9,
                                        float(r.get("order") or 0)))
    for r in order:
        if r.get("section") not in SECTIONS:
            raise SpecError(f"{doc['id']}: row {r.get('name')!r} has no section (mandatory, core or optional)")
        raw.setdefault(r["section"], []).append({"ref": f"{r.get('framework')}: {r.get('name')}",
                                                 "level": r.get("required")})
    for k in ("probation", "exceeds"):
        if isinstance(raw[k], str) and raw[k].strip():
            try:
                raw[k] = float(raw[k])
            except ValueError:
                pass
    return normalise(doc["id"], raw)


def merge(specs: dict, docs: list[dict]) -> tuple[dict, list[str]]:
    """Specs with the saved documents applied (in file order, new ones at the end), and a line per change."""
    out = dict(specs)
    log = []
    for d in docs:
        sid = d["id"]
        if d.get("deleted"):
            if sid in out:
                del out[sid]
                log.append(f"delete  {sid}")
            else:
                log.append(f"skip    {sid} (deleted on the dashboard, not in the file)")
            continue
        new = doc_to_spec(d)
        log.append(f"{'change' if sid in out else 'add':<7} {sid}: {new['title']} ({len(new['rows'])} competencies)")
        out[sid] = new
    return out, log


# ------------------------------------------------------------------ CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    kc.add_arguments(ap)
    ap.add_argument("--file", help="job specs file (default: the config's `jobSpecs`)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("check")
    b = sub.add_parser("build")
    b.add_argument("--out", help="the dashboard's copy (default: Job_Specs.csv beside the file)")
    sc = sub.add_parser("score")
    sc.add_argument("spec")
    sc.add_argument("--basis", choices=["claimed", "assessed", "supported"], default="claimed",
                    help="claimed: the owner's own rating; assessed: the assessor's; supported: the evidence")
    sc.add_argument("--disclosure", choices=["public", "on-request"], default="on-request")
    sc.add_argument("--profile")
    sc.add_argument("--today")
    m = sub.add_parser("merge")
    m.add_argument("--from", dest="src", required=True, help="ArtifactData export of the `jobspecs` collection")
    m.add_argument("--apply", action="store_true", help="write the file (default: dry run)")
    args = ap.parse_args(argv)
    try:
        cfg = kc.load(args.config, args.vault, getattr(args, "profile", None), os.getcwd(), required=True)
        lib = fw.library_for(cfg)
        path = os.path.abspath(args.file) if args.file else cfg.job_specs_file
        specs = load_specs(path)
    except (kc.ConfigError, fw.FrameworkError, SpecError) as exc:
        print(f"job specs: {exc}", file=sys.stderr)
        return 2
    problems = validate(specs, lib)
    if args.cmd == "merge":
        try:
            new, log = merge(specs, load_docs(args.src))
        except SpecError as exc:
            print(f"merge: {exc}", file=sys.stderr)
            return 2
        bad = validate(new, lib)
        print("\n".join(log) or "nothing saved on the dashboard")
        if bad:
            print("\n".join(f"problem: {p}" for p in bad), file=sys.stderr)
            return 1
        if not args.apply:
            print("(dry run: add --apply to write the file)", file=sys.stderr)
            return 0
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_yaml(new))
        if load_specs(path) != new:                      # it must read back as written
            print(f"merge: {path} does not read back as the merged specs", file=sys.stderr)
            return 2
        print(f"wrote {path}; now `job_specs.py build`, refresh the dashboard, and delete the merged documents",
              file=sys.stderr)
        return 0
    if problems:
        print("\n".join(f"problem: {p}" for p in problems), file=sys.stderr)
        if args.cmd in ("check", "build"):
            return 1
    if args.cmd == "check":
        print(f"{len(specs)} spec(s) in {cfg.rel(path)}: no problems")
        return 0
    if args.cmd == "list":
        if not specs:
            print(f"no job specs yet ({cfg.rel(path)})")
        for s in specs.values():
            counts = ", ".join(f"{sum(r['section'] == k for r in s['rows'])} {k}" for k in SECTIONS)
            print(f"{s['id']}: {s['title']} ({counts}){' -> ' + s['next'] if s['next'] else ''}")
        return 0
    if args.cmd == "build":
        out = args.out or default_csv(path)
        n = write_csv(out, specs)
        print(f"{n} rows, {len(specs)} spec(s) -> {out}")
        return 0
    # score
    if args.spec not in specs:
        print(f"no spec {args.spec!r}; one of: {', '.join(specs) or '(none)'}", file=sys.stderr)
        return 2
    today = dt.date.fromisoformat(args.today) if args.today else None
    look = level_lookup(graph_levels(cfg, args.disclosure, today), args.basis)
    s = score(specs[args.spec], look)
    spec = specs[args.spec]
    print(f"{spec['title']} — scored on {args.basis} levels ({args.disclosure} evidence)")
    for section in SECTIONS:
        rows = [r for r in s["rows"] if r["section"] == section]
        if not rows:
            continue
        print(f"\n{SECTION_TITLES[section]}")
        for r in rows:
            print(f"  {r['framework'] + ': ' + r['name']:<72} need {r['required']}  hold L{r['held']}  {r['result']}")
    gate = {"met": "met", "none": "no Mandatory section", "not-met": f"NOT MET ({s['gateShort']} short)"}[s["gate"]]
    print(f"\nMandatory gate: {gate}")
    print(f"Breadth {s['breadth']}/{s['breadthTarget']} ({s['breadthPct']}%), depth {s['depth']}/{s['depthTarget']} "
          f"({s['depthPct']}%), credit above the requirement {s['above']} (+{s['optional']} optional)")
    print(f"Band: {BAND_WORDS[s['band']]}. {diagnosis(s)}.")
    p = promotion(spec, specs, look, s)
    if p:
        print(f"Promotion to {p['nextTitle']}: {'ready' if p['ready'] else 'not yet'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
