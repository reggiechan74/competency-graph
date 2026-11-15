#!/usr/bin/env python3
"""Safe link editor for Competency Graph notes (Specification v0.5).

Adds or removes wikilinks in one graph field (`broader`, `related`, `sector`,
`demonstrates`, `demonstratesLed`, `partOf`, and the layer-3 relations `requires`, `appliedTo`
and `referee`) without touching anything else in the file.
The same add/remove works on `recognition`, a list of controlled words on evidence notes
(credential, assessing, teaching, publication, adoption, appointment, award), and on the
free-text lists `externalRef` and `aliases` (e.g. externalRef "RICS APC 2025: Leasing/letting").
An assessor's rating has its own command, `assess`: a note keeps one rating an assessor in `assessments`.

    edit_links.py --vault . add    <note> <field> <link> [<link> ...] [--apply] [--touch YYYY-MM-DD]
    edit_links.py --vault . remove <note> <field> <link> [<link> ...] [--apply] [--touch YYYY-MM-DD]
    edit_links.py --vault . set    <note> <field> <value>              [--apply] [--touch YYYY-MM-DD]
    edit_links.py --vault . assess <note> <level|none> --by <assessor> [--on YYYY-MM-DD] [--apply] [--touch YYYY-MM-DD]
    edit_links.py --vault . plan   <plan.yaml>                         [--apply] [--touch YYYY-MM-DD]

<note> and <link> are note names (filename without .md, with or without [[ ]])
or vault-relative paths. A plan file is a YAML list of
    {note: <note>, field: <field>, add: [<link>, ...], remove: [<link>, ...]}
or, for a scalar field (`claimedLevel`, `status`, `title`, `rank`, `disclosure`, or free-text `anchor` on evidence),
    {note: <note>, field: <field>, set: <value>}      # empty `set` = skip the entry
    {note: <note>, field: <field>, unset: true}       # remove the field (claimedLevel -> not rated)
or, for an assessor's rating (what `assess` does),
    {note: <note>, field: assessedLevel, set: L3, assessedBy: <assessor>, assessedOn: YYYY-MM-DD}
                                                      # written to `assessments` as "<assessor> | advanced | <date>",
                                                      # in place of that assessor's last rating; the others' stay
    {note: <note>, field: assessedLevel, unset: true, assessedBy: <assessor>}
                                                      # that assessor's rating removed; with no assessedBy, every one
A note that keeps a single rating the old way (assessedLevel, assessedBy, assessedOn) has it moved into `assessments`
by the first of these edits.
Extra keys in plan entries are ignored, so a worksheet can double as a plan.
`claimedLevel` and `assessedLevel` also take the labels L1-L4 (`L3`, `L3 Advanced`) and store the word (`advanced`).

Safety rules:
  * Dry run unless --apply. Nothing is written if any edit in the run fails.
  * The note must be a graph note, and the field must be a link field for its nodeType.
  * Every added link must resolve to exactly one note of the type that field requires.
  * Existing links keep their order; additions go at the end; duplicates are skipped.
  * After editing, the front matter is re-parsed: the field must equal exactly the
    expected list, and every other key must be unchanged. The body is never touched.
  * A trailing YAML comment on the field line is preserved (list fields and `set` alike).
  * `set` quotes a value YAML would read as something else ("2021", "true"); `period` keeps a bare year or date.
  * --touch sets an existing `lastUpdated` to the given date (the only other change allowed).

The vault comes from the nearest competency-graph.yaml unless --config/--vault is given.

Exit status: 0 = ok (or dry run ok), 1 = an edit was refused, 2 = usage problem.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_graph as cg  # noqa: E402

FM_RE = re.compile(r"\A---[ \t]*\n(.*?\n)?---[ \t]*(\n|\Z)", re.DOTALL)


class EditError(Exception):
    pass


VALUE_LIST_FIELDS = {"evidence": {"recognition": cg.RECOGNITION}}
# free-text lists: any non-empty string, stored quoted (e.g. externalRef: ["RICS APC 2025: Leasing/letting"])
TEXT_LIST_FIELDS = {"competency": {"externalRef", "aliases", cg.ASSESSMENTS}, "sector": {"externalRef", "aliases", cg.ASSESSMENTS},
                    "evidence": {"aliases"}, "organization": {"aliases"}, "person": {"aliases"}}
ASSESSMENT = {"assessedLevel", "assessedBy", "assessedOn"}      # one assessor's rating kept the old way: still removable
SCALAR_FIELDS = {"competency": {"claimedLevel", "status", "title", "rank", "deemed"} | ASSESSMENT,
                 "sector": {"claimedLevel", "title"} | ASSESSMENT,
                 "evidence": {"disclosure", "anchor", "title", "organization", "evidenceType", "period"},
                 # an organisation or a person (spec §2.4, §2.5): a name, and where the owner's own record of them is
                 "organization": {"title", "crm"}, "person": {"title", "role", "organization", "crm"}}
SAFE_PLAIN = re.compile(r"^[A-Za-z0-9_.-]+$")
DATE_FIELDS = {"period", "assessedOn"}                          # written bare, read back through cg.as_text


def scalar_text(field: str, value: str) -> str:
    """The value as YAML: plain when it reads back as the same string, else double-quoted (a JSON string is valid
    YAML). "2021", "true" and "2021-03-04" need quotes to stay strings; `period` keeps the spec's unquoted year or
    date (`period: 2021`), which the checker reads as text, and so does `assessedOn`."""
    if SAFE_PLAIN.match(value):
        try:
            back = yaml.safe_load(value)
        except yaml.YAMLError:
            back = None
        if back == value or (field in DATE_FIELDS and cg.as_text(back) == value):
            return value
    return json.dumps(value, ensure_ascii=False)


def trailing_comment(value: str) -> str:
    """The YAML comment that ends a scalar's line: 'old   # keep me' -> '# keep me' ('' when there is none). A `#`
    inside a quoted value is not a comment."""
    v = value.strip()
    if v[:1] in ('"', "'"):
        quote, i = v[0], 1
        while i < len(v):
            if quote == '"' and v[i] == "\\":
                i += 2
                continue
            if v[i] == quote:
                if quote == "'" and v[i + 1:i + 2] == "'":
                    i += 2
                    continue
                break
            i += 1
        rest = v[i + 1:].strip()
        return rest if rest.startswith("#") else ""
    if v.startswith("#"):
        return v
    m = re.search(r"\s#", v)
    return v[m.start():].strip() if m else ""


def load_fm(path: str, fm: str, field: str) -> dict:
    """Front matter as a dict; a YAML error is a refusal, not a traceback (a value that runs over several lines
    leaves its other lines behind when its first is replaced)."""
    try:
        return yaml.safe_load(fm) or {}
    except yaml.YAMLError:
        raise EditError(f"{path}: `{field}` spans several lines, or the front matter does not parse; change it by hand") from None


def set_field(vault, note: str, field: str, value: str, touch: str | None = None, text: str | None = None):
    """Set a controlled scalar field. Returns (path, new_text, report) without writing."""
    path = vault.resolve(note)
    if path not in vault.nodes:
        raise EditError(f"{path} is not a graph note (no nodeType)")
    ntype = vault.nodes[path].type
    if field in ASSESSMENT:
        raise EditError(f"`{field}` is not set on its own: an assessor's rating is kept in `{cg.ASSESSMENTS}` "
                        "(`assess <note> <level> --by <assessor>`, or a plan entry with `assessedBy`)")
    if field not in SCALAR_FIELDS[ntype]:
        raise EditError(f"`{field}` is not a settable field for nodeType {ntype} (allowed: {', '.join(sorted(SCALAR_FIELDS[ntype] - ASSESSMENT))})")
    if field in cg.LEVEL_FIELDS:
        value = cg.normalize_level(value)              # `L3` / `L3 Advanced` -> advanced
    if field == "title" and not value.strip():
        raise EditError(f"{path}: `title` cannot be empty")
    allowed = cg.CONTROLLED[ntype].get(field)
    if allowed is not None and value not in allowed:
        raise EditError(f"{path}: `{field}: {value}` not in {sorted(allowed)}")
    if text is None:
        text = open(os.path.join(vault.root, path), encoding="utf-8").read()
    fm, tail = split_front_matter(text)
    before = load_fm(path, fm, field)
    m = re.search(rf"^{re.escape(field)}:[ \t]*(.*)$", fm, re.M)
    if m and re.match(r"\n[ \t]+\S", fm[m.end():]):
        raise EditError(f"{path}: `{field}` spans several lines; change it by hand")
    comment = trailing_comment(m.group(1)) if m else ""      # a comment on the field's line stays
    line = f"{field}: {scalar_text(field, value)}" + (f"   {comment}" if comment else "")
    new_fm = fm[:m.start()] + line + fm[m.end():] if m else fm + line + "\n"
    if touch and "lastUpdated" in before:
        new_fm = re.sub(r"^lastUpdated:.*$", f"lastUpdated: {touch}", new_fm, count=1, flags=re.M)
    after = load_fm(path, new_fm, field)
    got = cg.as_text(after.get(field)) if field in DATE_FIELDS else after.get(field)
    if got != value:
        raise EditError(f"{path}: verification failed for `{field}`")
    ignore = {field} | ({"lastUpdated"} if touch else set())
    if {k: v for k, v in before.items() if k not in ignore} != {k: v for k, v in after.items() if k not in ignore}:
        raise EditError(f"{path}: verification failed, other keys would change")
    return path, "---\n" + new_fm + tail, {"path": path, "field": field, "was": before.get(field), "now": value}


def unset_field(vault, note: str, field: str, touch: str | None = None, text: str | None = None):
    """Remove a settable scalar field (e.g. claimedLevel -> not rated). Returns (path, new_text, report)."""
    path = vault.resolve(note)
    if path not in vault.nodes:
        raise EditError(f"{path} is not a graph note (no nodeType)")
    ntype = vault.nodes[path].type
    if field not in SCALAR_FIELDS[ntype] or field == "title":
        raise EditError(f"`{field}` can't be unset on nodeType {ntype}")
    if text is None:
        text = open(os.path.join(vault.root, path), encoding="utf-8").read()
    fm, tail = split_front_matter(text)
    before = load_fm(path, fm, field)
    new_fm = re.sub(rf"^{re.escape(field)}:.*\n", "", fm, count=1, flags=re.M)
    if touch and "lastUpdated" in before:
        new_fm = re.sub(r"^lastUpdated:.*$", f"lastUpdated: {touch}", new_fm, count=1, flags=re.M)
    after = load_fm(path, new_fm, field)
    if field in after:
        raise EditError(f"{path}: `{field}` spans several lines; remove it by hand")
    ignore = {field} | ({"lastUpdated"} if touch else set())
    if {k: v for k, v in before.items() if k not in ignore} != {k: v for k, v in after.items() if k not in ignore}:
        raise EditError(f"{path}: verification failed, other keys would change")
    return path, "---\n" + new_fm + tail, {"path": path, "field": field, "was": before.get(field), "now": None}


def assess(vault, note: str, by, level, on, touch: str | None = None, text: str | None = None):
    """One assessor's rating of a note, written to `assessments` as "<assessor> | <level> | <date>" in place of the
    rating that assessor gave before; the other assessors' ratings stay. An empty level removes the assessor's rating,
    and an empty `by` with an empty level removes every rating. A single rating kept the old way (assessedLevel,
    assessedBy, assessedOn) is moved into the list by the same edit. Returns (path, new_text, reports) without writing."""
    path = vault.resolve(note)
    if path not in vault.nodes:
        raise EditError(f"{path} is not a graph note (no nodeType)")
    if cg.ASSESSMENTS not in TEXT_LIST_FIELDS.get(vault.nodes[path].type, set()):
        raise EditError(f"{path}: a {vault.nodes[path].type} note takes no assessor's rating")
    by = " ".join(str(by or "").split())
    level = cg.normalize_level(str(level)) if level not in (None, "") else ""
    on = str(cg.as_text(on) or "")
    if level:
        if level not in cg.LEVELS:
            raise EditError(f"{path}: an assessor's level {level!r} is not one of {sorted(cg.LEVELS)} (or L1-L4)")
        if not by:
            raise EditError(f"{path}: an assessor's rating needs the assessor's name (`assessedBy`)")
        if "|" in by:
            raise EditError(f"{path}: an assessor's name cannot contain `|` ({by!r})")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", on):
            raise EditError(f"{path}: `assessedOn: {on}` is not a date (YYYY-MM-DD)")
    if text is None:
        text = open(os.path.join(vault.root, path), encoding="utf-8").read()
    before = load_fm(path, split_front_matter(text)[0], cg.ASSESSMENTS)
    if "assessedLevel" in before:                      # the old field holds the word or an L-code, as the list does
        before["assessedLevel"] = cg.normalize_level(before["assessedLevel"])
    ratings, _ = cg.assessments_of(before)
    theirs = (lambda r: r["by"].casefold() == by.casefold()) if by else (lambda r: True)
    reports = []
    for old in ("assessedLevel", "assessedBy", "assessedOn"):      # the old way out: its rating goes into the list below
        if old in before:
            _, text, rep = unset_field(vault, note, old, touch, text=text)
            reports.append(rep)
    stored = [str(x) for x in before.get(cg.ASSESSMENTS) or []] if isinstance(before.get(cg.ASSESSMENTS), list) else []
    remove = [s for s in stored if (cg.parse_assessment(s) or {"by": ""})["by"].casefold() == by.casefold()] if by else stored
    add = [cg.format_assessment(r["by"], r["level"], r["on"]) for r in ratings if r["raw"] is None and not theirs(r)]
    if level:
        add.append(cg.format_assessment(by, level, on))
    if add or remove:
        _, text, rep = edit_note(vault, note, cg.ASSESSMENTS, add, remove, touch, text=text)
        rep["rating"] = (f"{by}: " if by else "every assessor: ") + (cg.level_label(level) if level else "rating removed")
        reports.append(rep)
    elif not reports and not level:
        raise EditError(f"{path}: no rating by {by or 'any assessor'} to remove")
    return path, text, reports


def norm_name(raw: str) -> str:
    raw = raw.strip()
    m = re.fullmatch(r"\[\[([^\]]+)\]\]", raw)
    if m:
        raw = m.group(1)
    raw = raw.split("|", 1)[0].split("#", 1)[0].strip()
    return raw[:-3] if raw.lower().endswith(".md") else raw


def link_target(raw: str) -> str:
    """Extract the target from a stored link value such as "[[A|alias]]"."""
    return norm_name(raw) if isinstance(raw, str) else str(raw)


class Vault:
    def __init__(self, root: str):
        self.root = root
        self.index, self.nodes, _ = cg.scan_vault(root, cg.DEFAULT_EXCLUDE)

    def resolve(self, name: str) -> str:
        name = norm_name(name)
        if "/" in name:
            want = (name + ".md").lower()
            hits = [p for ps in self.index.values() for p in ps if p.lower() == want or p.lower().endswith("/" + want)]
        else:
            hits = self.index.get(name.lower(), [])
        if not hits:
            raise EditError(f"no note named {name!r}")
        if len(hits) > 1:
            raise EditError(f"{name!r} is ambiguous: {', '.join(hits[:4])}")
        return hits[0]


def split_front_matter(text: str):
    m = FM_RE.match(text)
    if not m:
        raise EditError("file has no front matter")
    return m.group(1) or "", text[m.end(1) if m.group(1) else 4:]  # fm text, remainder starting at closing ---


def find_field(fm: str, field: str):
    """Return (start, end, style, comment) of the field's lines in fm, or None.
    style: 'flow' (single line), 'block' (indented '- ' items), 'scalar' (single value)."""
    m = re.search(rf"^{re.escape(field)}:[ \t]*(.*)$", fm, re.M)
    if not m:
        return None
    value = m.group(1)
    start, end = m.start(), m.end()
    if value.strip() == "" or value.strip().startswith("#"):
        # block list follows?
        rest = fm[end + 1:]
        items = re.match(r"((?:[ \t]+-[^\n]*\n|[ \t]*\n)*)", rest)
        block = items.group(1) if items else ""
        block = block.rstrip(" \t\n")
        if block.strip():
            return start, end + 1 + len(block), "block", value.strip()
        return start, end, "flow", value.strip()          # empty: treat as flow with optional comment
    if value.lstrip().startswith("["):
        close = value.rfind("]")
        comment = value[close + 1:].strip() if close >= 0 else ""
        if comment and not comment.startswith("#"):
            raise EditError(f"cannot safely edit `{field}`: unexpected text after list: {comment!r}")
        return start, end, "flow", comment
    hash_at = value.find("  #")
    return start, end, "scalar", value[hash_at:].strip() if hash_at >= 0 else ""


def render(field: str, links: list, single: bool, comment: str) -> str:
    quoted = [f'"[[{x}]]"' for x in links]
    if single:
        body = quoted[0] if quoted else '""'
    else:
        body = "[" + ", ".join(quoted) + "]"
    line = f"{field}: {body}"
    return f"{line}   {comment}" if comment else line


def render_words(field: str, words: list, comment: str) -> str:
    line = f"{field}: [{', '.join(words)}]"
    return f"{line}   {comment}" if comment else line


def render_text(field: str, items: list, comment: str) -> str:
    line = f"{field}: [{', '.join(json.dumps(x, ensure_ascii=False) for x in items)}]"   # JSON strings = valid YAML
    return f"{line}   {comment}" if comment else line


def current_links(fm_dict: dict, field: str) -> list:
    value = fm_dict.get(field)
    if value in (None, "", []):
        return []
    values = value if isinstance(value, list) else [value]
    if any(isinstance(v, (dict, list)) for v in values):
        raise EditError(f"`{field}` holds nested objects; fix by hand first")
    return [link_target(v) for v in values]


def current_text(fm_dict: dict, field: str) -> list:
    value = fm_dict.get(field)
    if value in (None, "", []):
        return []
    values = value if isinstance(value, list) else [value]
    if any(isinstance(v, (dict, list)) for v in values):
        raise EditError(f"`{field}` holds nested objects; fix by hand first")
    return [str(v) for v in values]


def edit_note(vault: Vault, note: str, field: str, add=(), remove=(), touch: str | None = None, text: str | None = None):
    """Return (path, new_text, report) without writing. `text` overrides the file's content (chained edits)."""
    path = vault.resolve(note)
    if path not in vault.nodes:
        raise EditError(f"{path} is not a graph note (no nodeType)")
    node = vault.nodes[path]
    allowed = cg.LINK_FIELDS[node.type]
    words = VALUE_LIST_FIELDS.get(node.type, {}).get(field)
    free = field in TEXT_LIST_FIELDS.get(node.type, set())
    if field not in allowed and words is None and not free:
        lists = list(allowed) + list(VALUE_LIST_FIELDS.get(node.type, {})) + sorted(TEXT_LIST_FIELDS.get(node.type, ()))
        raise EditError(f"`{field}` is not a list field for nodeType {node.type} (allowed: {', '.join(lists)})")
    want_type = allowed.get(field)
    single = field in cg.SINGLE_LINK_FIELDS

    add_names = []
    if words is not None:
        bad = [w for w in add if w not in words]
        if bad:
            raise EditError(f"{path}: `{field}` takes only {sorted(words)}; not allowed: {bad}")
        add, add_names = [], [str(w) for w in add]
    if free:
        bad = [x for x in add if not isinstance(x, str) or not x.strip()]
        if bad:
            raise EditError(f"{path}: `{field}` takes non-empty strings; not allowed: {bad}")
        add, add_names = [], [x.strip() for x in add]
    for raw in add:
        target = vault.resolve(raw)
        if want_type and (target not in vault.nodes or vault.nodes[target].type != want_type):
            got = vault.nodes[target].type if target in vault.nodes else "a non-graph note"
            raise EditError(f"{path}: `{field}` needs a {want_type}, but {target} is {got}")
        add_names.append(os.path.basename(target)[:-3])
    remove_names = [str(r).strip() for r in remove] if free else [norm_name(r) for r in remove]

    if text is None:
        text = open(os.path.join(vault.root, path), encoding="utf-8").read()
    fm, tail = split_front_matter(text)
    before = yaml.safe_load(fm) or {}
    old = current_text(before, field) if free else current_links(before, field)
    missing = [r for r in remove_names if r.lower() not in {o.lower() for o in old}]
    if missing:
        raise EditError(f"{path}: cannot remove {missing}, not present in `{field}`")
    kept = [o for o in old if o.lower() not in {r.lower() for r in remove_names}]
    added, seen = [], {k.lower() for k in kept}
    for a in add_names:                       # dedupe against existing links and within the request
        if a.lower() not in seen:
            added.append(a)
            seen.add(a.lower())
    skipped = [a for a in add_names if a not in added]
    new = kept + added
    if single and len(new) > 1:
        raise EditError(f"{path}: `{field}` takes one link; it would hold {new} (remove the old one first)")

    loc = find_field(fm, field)
    draw = (lambda f, xs, _s, c: render_words(f, xs, c)) if words is not None else render
    if free:
        draw = lambda f, xs, _s, c: render_text(f, xs, c)
    if loc is None:
        new_fm = fm + (draw(field, new, single, "") + "\n" if new else "")
    else:
        start, end, _style, comment = loc
        new_fm = fm[:start] + draw(field, new, single, comment) + fm[end:]
    if touch and "lastUpdated" in before:
        new_fm = re.sub(r"^lastUpdated:.*$", f"lastUpdated: {touch}", new_fm, count=1, flags=re.M)

    # verification: field exact, everything else unchanged
    after = yaml.safe_load(new_fm) or {}
    got = current_text(after, field) if free else current_links(after, field)
    if got != new:
        raise EditError(f"{path}: verification failed for `{field}` (got {got}, expected {new})")
    ignore = {field} | ({"lastUpdated"} if touch else set())
    if {k: v for k, v in before.items() if k not in ignore} != {k: v for k, v in after.items() if k not in ignore}:
        changed = sorted(k for k in set(before) | set(after) if k not in ignore and before.get(k) != after.get(k))
        raise EditError(f"{path}: verification failed, other keys would change: {changed}")

    report = {"path": path, "field": field, "had": len(old), "added": added, "removed": [o for o in old if o not in kept],
              "skipped": skipped, "now": len(new)}
    return path, "---\n" + new_fm + tail, report


def run(vault_root: str, edits: list, apply: bool, touch: str | None):
    """edits: list of dicts {note, field, add, remove}. All-or-nothing."""
    vault = Vault(vault_root)
    staged, reports = {}, []
    for e in edits:
        if not isinstance(e, dict):
            raise EditError(f"plan entry is not a {{note, field, ...}} mapping: {e!r}")
        for key in ("note", "field"):
            if not e.get(key):
                raise EditError(f"plan entry missing `{key}`: {e}")
        path = vault.resolve(e["note"])
        if e["field"] == "assessedLevel":                  # an assessor's rating: one of several the note may keep
            if not e.get("unset") and e.get("set") in (None, ""):
                continue                                   # an empty worksheet entry: skipped
            p, text, reps = assess(vault, e["note"], e.get("assessedBy"), "" if e.get("unset") else e["set"],
                                   e.get("assessedOn"), touch, text=staged.get(path))
            staged[p] = text
            reports.extend(reps)
            continue
        if e.get("unset"):
            p, text, rep = unset_field(vault, e["note"], e["field"], touch, text=staged.get(path))
            staged[p] = text
            reports.append(rep)
            continue
        if "set" in e:
            if e["set"] in (None, ""):
                continue
            p, text, rep = set_field(vault, e["note"], e["field"], str(e["set"]), touch, text=staged.get(path))
            staged[p] = text
            reports.append(rep)
            continue
        if not (e.get("add") or e.get("remove")):
            continue                                   # an empty worksheet entry: skipped
        p, text, rep = edit_note(vault, e["note"], e["field"], e.get("add") or [], e.get("remove") or [], touch,
                                 text=staged.get(path))   # chain edits to the same file in memory
        staged[p] = text
        reports.append(rep)
    if apply:
        for p, text in staged.items():
            with open(os.path.join(vault_root, p), "w", encoding="utf-8") as fh:
                fh.write(text)
    return reports


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    cg.kc.add_arguments(ap)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--touch", metavar="YYYY-MM-DD", help="set lastUpdated on edited notes")
    # --apply / --touch are also accepted after the subcommand (e.g. `plan p.yaml --apply`);
    # SUPPRESS keeps the subparser from overwriting a value given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--apply", action="store_true", default=argparse.SUPPRESS)
    common.add_argument("--touch", metavar="YYYY-MM-DD", default=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("add", "remove"):
        sp = sub.add_parser(name, parents=[common])
        sp.add_argument("note")
        sp.add_argument("field")
        sp.add_argument("links", nargs="+")
    sp = sub.add_parser("set", parents=[common])
    sp.add_argument("note")
    sp.add_argument("field")
    sp.add_argument("value")
    sp = sub.add_parser("assess", parents=[common], help="one assessor's rating of a note")
    sp.add_argument("note")
    sp.add_argument("level", help="aware, practitioner, advanced, expert (or L1-L4); `none` removes this assessor's rating")
    sp.add_argument("--by", required=True, metavar="ASSESSOR", help="the assessor's name, as the config lists it")
    sp.add_argument("--on", metavar="YYYY-MM-DD", help="the day the rating was given (default: today)")
    sp = sub.add_parser("plan", parents=[common])
    sp.add_argument("plan_file")
    args = ap.parse_args(argv)
    cg.kc.from_args(args)

    if args.cmd == "plan":
        with open(args.plan_file, encoding="utf-8") as fh:
            edits = yaml.safe_load(fh) or []
        if not isinstance(edits, list):
            print("plan file must be a YAML list", file=sys.stderr)
            return 2
    elif args.cmd == "assess":
        gone = args.level.strip().lower() in ("none", "")
        edits = [{"note": args.note, "field": "assessedLevel", "assessedBy": args.by,
                  **({"unset": True} if gone else {"set": args.level, "assessedOn": args.on or dt.date.today().isoformat()})}]
    elif args.cmd == "set":
        edits = [{"note": args.note, "field": args.field, "set": args.value}]
    else:
        edits = [{"note": args.note, "field": args.field, args.cmd: args.links}]
    try:
        reports = run(args.vault, edits, args.apply, args.touch)
    except EditError as exc:
        print(f"REFUSED: {exc}\nNothing was written.", file=sys.stderr)
        return 1
    for r in reports:
        if "now" in r and "had" not in r:
            print(f"{r['path']} `{r['field']}`: {r['was']!r} -> {r['now']!r}")
            continue
        bits = ([r["rating"]] if r.get("rating") else []) + [f"had {r['had']}"]
        if r["added"]:
            bits.append(f"+{len(r['added'])} ({', '.join(r['added'])})")
        if r["removed"]:
            bits.append(f"-{len(r['removed'])} ({', '.join(r['removed'])})")
        if r["skipped"]:
            bits.append(f"skipped {len(r['skipped'])} already present")
        bits.append(f"now {r['now']}")
        print(f"{r['path']} `{r['field']}`: " + ", ".join(bits))
    print("Applied." if args.apply else "Dry run: nothing written (use --apply).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
