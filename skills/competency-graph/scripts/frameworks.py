#!/usr/bin/env python3
"""Preconfigured competency frameworks: list them, and build the owner's requirements file (Specification v0.5).

The library is `assets/frameworks/` in this skill: `catalog.yaml` names each framework (RICS APC pathways, CFA CBOK,
ASQ Six Sigma Green Belt, Chan AFSE, ...), its requirements file and, optionally, a `guide` with its level descriptors
and `status: draft` for a framework still under review, every level already on the L1-L4 scale. The owner selects
frameworks and pathways in competency-graph.yaml:

    frameworks:
      rics-apc:
        pathways: [Valuation, Commercial real estate]      # omit `pathways` to select every pathway
        notes: {Valuation: qualified 2019}                 # optional, shown beside the pathway's name
      cfa-cbok: {}

    frameworks.py list [--all]           the library, with the owner's selection marked (--all: every pathway)
    frameworks.py build [--out FILE] [--descriptions FILE]
                                         write the requirements file (default: the config's `requirements`) and the
                                         descriptions file beside it (default: `Requirements` in its name becomes
                                         `Descriptions`, else `_descriptions` is added)
    frameworks.py apply --from DIR [--apply]
                                         make a selection saved on the dashboard's Configuration tab the record: the
                                         exported `settings` document ({selected: ["RICS APC|Valuation", ...]}) is
                                         written into `frameworks:` in competency-graph.yaml (dry run without --apply).
                                         A framework with nothing selected keeps its notes under `pathways: []`

    frameworks.py new ID --name "Framework name" [--title T] [--body B] [--no-pathways]
    frameworks.py new ID --from LIBRARY_ID [--name "Another name"]
                                         start one of the owner's own frameworks in their own folder: an empty one to
                                         fill in, or a copy of one the plugin ships. A copy under the shipped id is the
                                         owner's own edition of it and takes its place for this owner

The library the plugin ships is read, never written: an update of the plugin replaces it. Everything an owner adds is
kept in their own files. Their own frameworks live in a folder in the library's format (its own `catalog.yaml`,
requirements and descriptions files): `ownFrameworks` in the config, else `Frameworks` under the graph root, read once
it holds a catalog. They join the plugin's library under their own ids and names. One may instead carry a shipped
framework's id with `replaces_plugin: true` in its catalog entry: the owner's own edition of that framework, which is
then the one this owner sees (`list` says so, and says when the plugin's edition has since changed). A framework may
have only a `descriptions` file and no `file`: a competency library with no pathways, offered to job specs
(job_specs.py) but not on the Competency frameworks tab.

`build` writes every framework and pathway in the library, with a `selected` column (yes/no) from the config and
the owner's `pathway_note`, so the dashboard's Configuration tab can offer all of them and show the selected ones,
and `framework_status` (`draft` or blank) with its note, so the dashboard marks a framework still under review.
Each selection rule is written without the page numbers and table text that came along from the guides' PDFs.
`subgroup` (optional in a library file) names a sub-group inside a group, e.g. a specialisation within Optional: the
dashboard prints it as a sub-heading over its rows, under the group's rule, which still applies to the whole group.
The descriptions file has one row per framework competency (each framework's `descriptions` file in the library): a
general description, what each of L1-L4 means, and where each part came from; the dashboard's Framework competency definitions
tab joins it to the requirements by framework and name.
The vault comes from the nearest competency-graph.yaml unless --config/--vault is given.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kg_config as kc  # noqa: E402

LIBRARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "frameworks")
STATUSES = ("released", "draft")
COLUMNS = ["framework", "pathway", "pathway_note", "selected", "group", "subgroup", "order", "name", "required", "rule",
           "framework_status", "framework_status_note"]


DESCRIPTION_COLUMNS = ["framework", "name", "description", "l1", "l2", "l3", "l4", "source"]


class FrameworkError(Exception):
    pass


def _load_catalog(folder: str, own: bool) -> dict:
    path = os.path.join(folder, "catalog.yaml")
    if not os.path.isfile(path):
        raise FrameworkError(f"no catalog.yaml in {folder}")
    with open(path, encoding="utf-8") as fh:
        cat = (yaml.safe_load(fh) or {}).get("frameworks") or {}
    out = {}
    for fid, meta in cat.items():
        meta = dict(meta or {})
        if meta.get("status", "released") not in STATUSES:
            raise FrameworkError(f"{fid}: status {meta['status']!r} is not one of {', '.join(STATUSES)}")
        if not meta.get("framework"):
            raise FrameworkError(f"{fid}: catalog entry has no `framework` name")
        if not meta.get("file") and not meta.get("descriptions"):
            raise FrameworkError(f"{fid}: catalog entry names neither a requirements `file` nor `descriptions`")
        rows = []
        if meta.get("file"):
            with open(os.path.join(folder, meta["file"]), encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
        descriptions = []
        if meta.get("descriptions"):
            with open(os.path.join(folder, meta["descriptions"]), encoding="utf-8", newline="") as fh:
                descriptions = list(csv.DictReader(fh))
        out[fid] = {**meta, "rows": rows, "descriptions_rows": descriptions, "own": own, "folder": folder,
                    "pathways": list(dict.fromkeys(r["pathway"] for r in rows))}
    return out


def load_library(library: str = LIBRARY, own: str | None = None) -> dict:
    """{id: {meta..., rows: [...], pathways: [names in file order], own: bool}}: the skill's library, then the
    owner's own frameworks (`ownFrameworks` in the config), which may not reuse an id or a framework name."""
    out = _load_catalog(library, False)
    if own:
        mine = _load_catalog(own, True)
        names = {f["framework"]: fid for fid, f in out.items()}
        for fid, f in mine.items():
            if fid in out and not f.get("replaces_plugin"):
                raise FrameworkError(f"own framework id {fid!r} is already in the plugin's library; choose another id, or "
                                     "add `replaces_plugin: true` to make it your own edition of that framework")
            if f["framework"] in names and names[f["framework"]] != fid:
                raise FrameworkError(f"own framework {fid}: name {f['framework']!r} is already used by {names[f['framework']]}")
            names[f["framework"]] = fid       # nor may two of the owner's own share a name
            if fid in out:        # the owner's own edition takes the shipped one's place, and remembers what it replaced
                f["shipped_edition"] = out[fid].get("edition")
        # an own edition keeps the shipped framework's place in the list
        out = {fid: mine.pop(fid) if fid in mine else fw for fid, fw in out.items()}
        out.update(mine)
    return out


def own_entry(fid: str, meta: dict) -> str:
    """One framework's entry for the owner's catalog.yaml, as text to append."""
    lines = [f"  {fid}:"]
    for key in ("framework", "title", "body", "field", "edition", "status", "status_note", "replaces_plugin", "based_on",
                "file", "descriptions", "guide", "levels"):
        if meta.get(key) not in (None, ""):
            v = meta[key]
            lines.append(f"    {key}: {'true' if v is True else yq(v)}")
    if meta.get("sources"):
        lines.append("    sources:")
        lines += [f"      - {yq(x)}" for x in meta["sources"]]
    return "\n".join(lines) + "\n"


OWN_CATALOG_HEAD = """\
# Your own frameworks: the same format as the plugin's assets/frameworks/catalog.yaml. They are yours and stay here:
# a plugin update never touches this folder. frameworks.py reads them beside the plugin's library, so pathways and
# job specs can use them. An entry under a shipped framework's id with `replaces_plugin: true` is your own edition of it.
frameworks:
"""


def new_framework(home: str, fid: str, lib: dict, name: str | None = None, source: str | None = None, title: str | None = None,
                  body: str | None = None, pathways: bool = True, today: str = "") -> list[str]:
    """Start an own framework in `home` (the owner's own frameworks folder): empty files to fill in, or a copy of the
    library framework `source`. Returns the files written. Raises FrameworkError and writes nothing it does not undo."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fid):
        raise FrameworkError(f"id {fid!r} must be lowercase letters and digits joined by hyphens")
    if kc._inside(home, kc.SKILL_DIR):
        raise FrameworkError(f"{home} is inside the plugin's own folder, which an update replaces; keep your frameworks in your own files")
    cat = os.path.join(home, "catalog.yaml")
    existing = _load_catalog(home, True) if os.path.isfile(cat) else {}
    if fid in existing:
        raise FrameworkError(f"{fid} is already one of your own frameworks ({cat})")
    shipped = {k: v for k, v in _load_catalog(LIBRARY, False).items()} if lib is None else \
        {k: v for k, v in lib.items() if not v.get("own")}
    if fid in shipped and source != fid:
        raise FrameworkError(f"{fid} is the id of a framework the plugin ships; `new {fid} --from {fid}` makes your own "
                             "edition of it, or choose another id")
    written = []
    if source:
        if source not in shipped:
            raise FrameworkError(f"no framework {source!r} in the plugin's library; `frameworks.py list` shows them")
        src = shipped[source]
        same = fid == source
        if not same and not name:
            raise FrameworkError("a copy under a new id needs its own --name, since the framework's name is how notes refer to it")
        meta = {k: src.get(k) for k in ("title", "body", "field", "levels", "sources")}
        # the copy keeps the standing of what it copies: it is the owner's from here, and theirs to mark as a draft
        meta.update(framework=src["framework"] if same else name, edition=src.get("edition"),
                    status=src.get("status"), status_note=src.get("status_note"),
                    replaces_plugin=True if same else None, based_on=f"{source}, {src.get('edition', '?')}, copied {today}")
        for key in ("file", "descriptions", "guide"):
            if not src.get(key):
                continue
            target = src[key] if same else src[key].replace(source, fid, 1)
            meta[key] = target
            with open(os.path.join(src["folder"], src[key]), encoding="utf-8", newline="") as fh:
                text = fh.read()
            if not same and key in ("file", "descriptions"):     # the rows name their framework: the copy has its own
                rows = list(csv.DictReader(text.splitlines(keepends=True)))
                for r in rows:
                    r["framework"] = name
                cols = list(rows[0].keys()) if rows else (COLUMNS if key == "file" else DESCRIPTION_COLUMNS)
                written.append((target, rows, cols))
            else:
                written.append((target, text, None))
    else:
        if not name:
            raise FrameworkError("a new framework needs --name: the name notes will refer to it by")
        meta = {"framework": name, "title": title or name, "body": body or "The owner", "edition": f"draft ({today})",
                "status": "draft", "status_note": "New: its competencies and levels are still to be written and reviewed.",
                "levels": "Native L1-L4: L1 knows it, L2 delivers it, L3 leads complex work, L4 is recognised beyond their own team"}
        if pathways:
            meta["file"] = f"{fid}.csv"
            written.append((meta["file"], [], ["framework", "pathway", "group", "subgroup", "order", "name", "required", "rule"]))
        meta["descriptions"] = f"{fid}-descriptions.csv"
        written.append((meta["descriptions"], [], DESCRIPTION_COLUMNS))
    clash = [t for t, _, _ in written if os.path.exists(os.path.join(home, t))]
    if clash:
        raise FrameworkError(f"{', '.join(clash)} already in {home}; move or rename before starting {fid}")
    os.makedirs(home, exist_ok=True)
    before = open(cat, encoding="utf-8").read() if os.path.isfile(cat) else None
    made = []
    try:
        for target, content, cols in written:
            path = os.path.join(home, target)
            if cols is None:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(content)
            else:
                write(path, content, cols)
            made.append(path)
        text = before if before is not None else OWN_CATALOG_HEAD
        with open(cat, "w", encoding="utf-8") as fh:
            fh.write(text + ("" if text.endswith("\n") else "\n") + own_entry(fid, meta))
        load_library(own=home)            # it must read back beside the plugin's library
    except (FrameworkError, OSError, KeyError, yaml.YAMLError) as exc:
        for path in made:
            os.remove(path)
        if before is None:
            if os.path.isfile(cat):
                os.remove(cat)
        else:
            with open(cat, "w", encoding="utf-8") as fh:
                fh.write(before)
        raise FrameworkError(f"{fid} not created: {exc}") from None
    return made + [cat]


def library_for(cfg, library: str = LIBRARY) -> dict:
    """The library an owner sees: the skill's, plus their own frameworks when the config names a folder."""
    return load_library(library, getattr(cfg, "own_frameworks", None) if cfg else None)


def descriptions_path(requirements: str) -> str:
    """The descriptions file beside a requirements file: Framework_Requirements.csv -> Framework_Descriptions.csv."""
    return kc.default_descriptions(requirements)


def build_descriptions(lib: dict) -> list[dict]:
    """Every framework's description rows, one per competency the framework names, in library order."""
    rows = []
    for fw in lib.values():
        for r in fw.get("descriptions_rows") or []:
            rows.append({c: " ".join(str(r.get(c, "") or "").split()) for c in DESCRIPTION_COLUMNS})
    return rows


def subgroups(lib: dict) -> dict:
    """{(framework, competency): (sub-group, its place among the framework's sub-groups, from 1)} for every library
    competency that a pathway lists in a sub-group of a group (a specialisation within Optional)."""
    out = {}
    for fw in lib.values():
        place: dict = {}
        for r in fw["rows"]:
            s = " ".join(str(r.get("subgroup") or "").split())
            if s:
                place.setdefault(s, len(place) + 1)
                out.setdefault((fw["framework"], r["name"]), (s, place[s]))
    return out


def selection(config_frameworks: dict | None, lib: dict) -> dict:
    """{(framework id, pathway): note or ""} for the selected pathways; raises on unknown ids or pathways."""
    sel = {}
    for fid, spec in (config_frameworks or {}).items():
        if fid not in lib:
            raise FrameworkError(f"unknown framework {fid!r}; the library has: {', '.join(lib)}")
        spec = spec or {}
        # no `pathways`: every pathway; `pathways: []`: none (the framework stays listed, with its notes)
        names = lib[fid]["pathways"] if spec.get("pathways") is None else spec["pathways"]
        notes = spec.get("notes") or {}
        for n in list(names) + list(notes):
            if n not in lib[fid]["pathways"]:
                raise FrameworkError(f"{fid}: unknown pathway {n!r}; one of: {', '.join(lib[fid]['pathways'])}")
        for n in names:
            sel[(fid, n)] = str(notes.get(n, "") or "")
    return sel


# a page number left at the end ("... e.g. residential. 22"); never a level ("... to Level 2", "Level 2 or 3")
PAGE_NUMBER = re.compile(r"(?<!Level)(?<!\bL)\s+(?:[5-9]|\d{2,3})$")
TABLE_CELL = "\u2713"                                       # a check mark is a table cell, never rule text


def clean_rule(text: str) -> str:
    """A selection rule as the framework states it, without what came along when it was copied from the guide's PDF:
    a page number at the end, and a competency table that ran into the text after the rule's last sentence."""
    t = " ".join(str(text or "").split())
    if TABLE_CELL in t:
        head = t[: t.index(TABLE_CELL)]
        end = head.rfind(". ")
        t = head[: end + 1] if end >= 0 else head
    return PAGE_NUMBER.sub("", t).strip()


def build_rows(lib: dict, sel: dict, notes_for_unselected: dict | None = None) -> list[dict]:
    rows = []
    for fid, fw in lib.items():
        draft = fw.get("status") == "draft"
        status = {"framework_status": "draft" if draft else "",
                  "framework_status_note": str(fw.get("status_note") or "") if draft else ""}
        for r in fw["rows"]:
            key = (fid, r["pathway"])
            rows.append({**{c: r.get(c, "") for c in ("framework", "pathway", "group", "order", "name", "required")},
                         "subgroup": " ".join(str(r.get("subgroup") or "").split()),
                         "rule": clean_rule(r.get("rule", "")),
                         "pathway_note": sel.get(key, (notes_for_unselected or {}).get(key, "")),
                         "selected": "yes" if key in sel else "no", **status})
    return rows


def write(path: str, rows: list[dict], columns: list[str] = COLUMNS) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def selection_from_keys(keys, lib: dict) -> dict:
    """["RICS APC|Valuation", ...] (the dashboard's saved selection) -> {id: [pathways in library order]}."""
    by_name = {f["framework"]: fid for fid, f in lib.items()}
    chosen: dict = {}
    for k in keys:
        name, _, pathway = str(k).partition("|")
        fid = by_name.get(name)
        if not fid or pathway not in lib[fid]["pathways"]:
            raise FrameworkError(f"saved selection names {k!r}, which is not in the library")
        chosen.setdefault(fid, set()).add(pathway)
    return {fid: [p for p in lib[fid]["pathways"] if p in ps] for fid, ps in chosen.items()}


def merged_config(current: dict | None, chosen: dict, lib: dict) -> dict:
    """The new `frameworks:` mapping: every framework chosen, plus any the config lists with notes (kept with
    `pathways: []`, so a note like "qualified 2019" is never lost). A framework with every pathway chosen omits
    `pathways`. Notes are kept as they were."""
    current = current or {}
    out = {}
    for fid in [f for f in lib if f in chosen or f in current]:
        notes = dict(((current.get(fid) or {}).get("notes")) or {})
        pws = chosen.get(fid, [])
        if not pws and not notes:
            continue
        spec = {}
        if len(pws) != len(lib[fid]["pathways"]):
            spec["pathways"] = pws
        if notes:
            spec["notes"] = notes
        out[fid] = spec
    return out


PLAIN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._/()&'+-]*$")


def yq(v) -> str:
    """A YAML scalar: plain when that reads back the same, else double-quoted."""
    s = str(v)
    if PLAIN.match(s) and s.strip() == s and s.lower() not in {"yes", "no", "true", "false", "null", "on", "off"}:
        return s
    return json.dumps(s, ensure_ascii=False)


def render_frameworks(spec: dict) -> str:
    lines = ["frameworks:"]
    if not spec:
        return "frameworks: {}\n"
    for fid, f in spec.items():
        if not f:
            lines.append(f"  {fid}: {{}}")
            continue
        lines.append(f"  {fid}:")
        if "pathways" in f:
            lines.append(f"    pathways: [{', '.join(yq(p) for p in f['pathways'])}]")
        if f.get("notes"):
            lines.append("    notes:")
            lines += [f"      {yq(k)}: {yq(v)}" for k, v in f["notes"].items()]
    return "\n".join(lines) + "\n"


def replace_block(text: str, key: str, block: str) -> str:
    """Replace a top-level `key:` block of a YAML file (its line and every indented or blank line after it), keeping
    the rest, comments included. The block is added at the end when the key isn't there."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if re.match(rf"^{re.escape(key)}\s*:", l)), None)
    if start is None:
        return text + ("" if text.endswith("\n") or not text else "\n") + block
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end][:1] in (" ", "\t")):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():     # leave the blank lines before the next key
        end -= 1
    return "".join(lines[:start]) + block + "".join(lines[end:])


def load_selection_doc(src: str) -> list[str]:
    """The saved selection from an ArtifactData export of the `settings` collection (or the one document)."""
    import glob
    paths = [src] if os.path.isfile(src) else sorted(glob.glob(os.path.join(src, "**", "*.json"), recursive=True))
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        for d in data if isinstance(data, list) else [data]:
            if not isinstance(d, dict):
                continue
            doc = d.get("data") if isinstance(d.get("data"), dict) else d
            did = str(d.get("id") or os.path.basename(p)[:-5])
            if isinstance(doc.get("selected"), list) and (did.endswith("frameworks") or len(paths) == 1):
                return [str(x) for x in doc["selected"]]
    raise FrameworkError(f"no saved selection ({{selected: [...]}}) found in {src}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    kc.add_arguments(ap)
    ap.add_argument("--library", default=LIBRARY, help="framework library folder (default: the plugin's assets/frameworks)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--all", action="store_true", help="list every pathway, not only counts")
    b = sub.add_parser("build")
    b.add_argument("--out", help="requirements file (default: the config's `requirements`)")
    b.add_argument("--descriptions", help="descriptions file (default: the config's `descriptions`, else beside the "
                   "requirements file)")
    n = sub.add_parser("new", help="start one of your own frameworks in your own folder")
    n.add_argument("id", help="its id: lowercase letters and digits joined by hyphens")
    n.add_argument("--name", help="the framework's name, as notes will refer to it (externalRef)")
    n.add_argument("--from", dest="source", help="copy this framework from the plugin's library to edit as your own")
    n.add_argument("--title", help="a longer title (default: the name)")
    n.add_argument("--body", help="who publishes it (default: the owner)")
    n.add_argument("--no-pathways", action="store_true", help="a competency library only: no requirements file")
    a = sub.add_parser("apply")
    a.add_argument("--from", dest="src", required=True, help="ArtifactData export of the dashboard's `settings` collection")
    a.add_argument("--apply", action="store_true", help="write competency-graph.yaml (default: show the new block)")
    args = ap.parse_args(argv)
    try:
        cfg = kc.load(args.config, args.vault, None, os.getcwd(), required=False)
    except kc.ConfigError as exc:
        print(f"config: {exc}", file=sys.stderr)
        return 2
    try:
        lib = load_library(args.library, getattr(cfg, "own_frameworks", None) if cfg else None)
        sel = selection(getattr(cfg, "frameworks", None) if cfg else None, lib)
    except FrameworkError as exc:
        print(f"config: {exc}", file=sys.stderr)
        return 2
    if args.cmd == "new":
        home = getattr(cfg, "own_frameworks_home", None) if cfg else None
        if not home:
            print("new needs a competency-graph.yaml, which says where your own frameworks are kept", file=sys.stderr)
            return 2
        import datetime as dt
        try:
            made = new_framework(home, args.id, lib, name=args.name, source=args.source, title=args.title, body=args.body,
                                 pathways=not args.no_pathways, today=dt.date.today().isoformat())
        except FrameworkError as exc:
            print(f"new: {exc}", file=sys.stderr)
            return 2
        print(f"{args.id}: started in {cfg.rel(home)}, in your own files (a plugin update never touches them)")
        for path in made:
            print(f"  {cfg.rel(path)}")
        print("next: fill in the files, select it under `frameworks:` in competency-graph.yaml if it has pathways, "
              "then `frameworks.py build`")
        return 0
    if args.cmd == "apply":
        if not cfg or not cfg.path:
            print("apply needs a competency-graph.yaml to write", file=sys.stderr)
            return 2
        try:
            chosen = selection_from_keys(load_selection_doc(args.src), lib)
        except FrameworkError as exc:
            print(f"apply: {exc}", file=sys.stderr)
            return 2
        new = merged_config(cfg.frameworks, chosen, lib)
        block = render_frameworks(new)
        with open(cfg.path, encoding="utf-8") as fh:
            old_text = fh.read()
        text = replace_block(old_text, "frameworks", block)
        print(block, end="")
        if not args.apply:
            print("(dry run: add --apply to write competency-graph.yaml)", file=sys.stderr)
            return 0
        with open(cfg.path, "w", encoding="utf-8") as fh:
            fh.write(text)
        try:                                   # it must read back as exactly the selection saved
            back = kc.read_config(cfg.path)
            want = {(f, p): str(((back.frameworks.get(f) or {}).get("notes") or {}).get(p, "") or "")
                    for f, ps in chosen.items() for p in ps}
            if selection(back.frameworks, lib) != want:
                raise FrameworkError("the written config does not read back as the saved selection")
        except (kc.ConfigError, FrameworkError) as exc:
            with open(cfg.path, "w", encoding="utf-8") as fh:
                fh.write(old_text)
            print(f"apply: {exc}; competency-graph.yaml left as it was", file=sys.stderr)
            return 2
        print(f"wrote `frameworks:` in {cfg.path}; now run `frameworks.py build` and refresh the dashboard",
              file=sys.stderr)
        return 0
    if args.cmd == "list":
        for fid, fw in lib.items():
            chosen = [p for p in fw["pathways"] if (fid, p) in sel]
            draft = " DRAFT." if fw.get("status") == "draft" else ""
            size = (f"{len(fw['pathways'])} pathway(s), {len(chosen)} selected" if fw["pathways"]
                    else f"{len(fw['descriptions_rows'])} competencies, no pathways (job specs only)")
            own = " OWN." if fw.get("own") else ""
            if fw.get("replaces_plugin"):
                own = " OWN EDITION: yours takes the place of the plugin's."
                if fw.get("shipped_edition") and fw.get("based_on") and str(fw["shipped_edition"]) not in str(fw["based_on"]):
                    own += f" The plugin's has changed since (yours is based on {fw['based_on']}; the plugin's is now {fw['shipped_edition']})." 
            print(f"{fid}: {fw.get('title', fw['framework'])} ({fw.get('body', '?')}, {fw.get('edition', '?')})."
                  f"{own}{draft} {size}")
            if draft and fw.get("status_note"):
                print(f"    draft: {fw['status_note']}")
            if fw.get("levels"):
                print(f"    levels: {fw['levels']}")
            if fw.get("guide"):
                print(f"    level guide: {os.path.normpath(os.path.join(fw['folder'], fw['guide']))}")
            for p in fw["pathways"] if args.all else chosen:
                note = sel.get((fid, p), "")
                print(f"    [{'x' if (fid, p) in sel else ' '}] {p}{' (' + note + ')' if note else ''}")
        return 0
    out = args.out or (cfg.requirements if cfg else None)
    if not out:
        print("give --out, or set `requirements` in competency-graph.yaml", file=sys.stderr)
        return 2
    if kc._inside(out, kc.SKILL_DIR):
        print(f"build: {out} is inside the plugin's own folder, which an update replaces; write it in your own files", file=sys.stderr)
        return 2
    rows = build_rows(lib, sel)
    write(out, rows)
    print(f"{len(rows)} rows, {len(sel)} selected pathway(s) of "
          f"{sum(len(f['pathways']) for f in lib.values())} -> {out}")
    desc = build_descriptions(lib)
    if desc:
        dpath = args.descriptions or (cfg.descriptions if cfg and cfg.descriptions and not args.out else None) \
            or descriptions_path(out)
        write(dpath, desc, DESCRIPTION_COLUMNS)
        print(f"{len(desc)} competency descriptions -> {dpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
