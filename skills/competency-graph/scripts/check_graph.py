#!/usr/bin/env python3
"""Read-only checker for the Competency Graph Specification (v0.5).

Scans a markdown vault for notes whose front matter has
`nodeType: competency | sector | evidence`, resolves their wikilinks vault-wide by
filename, and reports errors, warnings and insights (specification §3-4).
It never modifies a file.

Usage:
    check_graph.py [--config competency-graph.yaml | --vault <root>] [--profile <profile.md>]
                   [--today YYYY-MM-DD] [--report [out.md]] [--json [out.json]]

Vault and profile come from the nearest competency-graph.yaml (see kg_config.py) unless given.
--report / --json with no file name write a dated file to the config's `reports` folder.
With a config file, competency and sector notes outside their configured folders are warned about.

Settings come from flat keys in the profile's front matter (all optional):
    kgStaleYears: 5               # stale-claim threshold
    kgPractitionerMinMonths: 6    # months of delivered work for `practitioner`
    kgAdvancedMinYears: 5         # years of led work for `advanced`
    kgExpertMinYears: 10          # years of led work for `expert`
    kgExpertMinRecognition: 1     # kinds of outside recognition for `expert`
    kgPeriodAliases: [tenure]     # fields read as `period` on evidence notes
    kgExclude: [08_ARCHIVES]      # extra directories to skip

Exit status: 0 = no errors, 1 = errors found, 2 = usage problem.
Requires PyYAML.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kg_config as kc  # noqa: E402

AUTO = object()  # --report / --json given without a file name
SPEC_VERSION = "0.5"

LEVELS = {"aware", "practitioner", "advanced", "expert"}
LEVEL_RANK = {"none": 0, "aware": 1, "practitioner": 2, "advanced": 3, "expert": 4}
# display labels (spec §3.7); notes store the word, and `claimedLevel: L3` (or "L3 Advanced") is read as `advanced`
LEVEL_LABELS = {"aware": "L1 Aware", "practitioner": "L2 Practitioner", "advanced": "L3 Advanced", "expert": "L4 Expert"}
LEVEL_CODES = {"l1": "aware", "l2": "practitioner", "l3": "advanced", "l4": "expert"}
# the stored ratings (spec §2.1, §3.9): the owner's own, and the single assessor's rating of a graph made before a
# note could keep several (read still; new ratings go in ASSESSMENTS)
LEVEL_FIELDS = ("claimedLevel", "assessedLevel")
# each assessor's rating of a note, one string an assessor: "<assessor> | <level> | <YYYY-MM-DD>"
ASSESSMENTS = "assessments"
UNNAMED = "Unnamed assessor"       # a rating kept the old way with no `assessedBy`


def normalize_level(value):
    """Return the stored word for a level given as a word, an L-code (`L3`) or a label (`L3 Advanced`).
    Anything else is returned unchanged, so the value check still reports it."""
    if not isinstance(value, str) or not value.strip():
        return value
    v = value.strip()
    code = v.split()[0].lower()
    if code in LEVEL_CODES:
        word = LEVEL_CODES[code]
        rest = v.split(None, 1)[1].strip().lower() if len(v.split()) > 1 else word
        return word if rest == word else value          # "L3 Expert" is a contradiction: leave it to be reported
    return v.lower() if v.lower() in LEVEL_LABELS else value


def format_assessment(by: str, level: str, on: str) -> str:
    return f"{by} | {level} | {on}"


def parse_assessment(value):
    """{by, level, on} from "<assessor> | <level> | <date>" (the level as a word, L3 or L3 Advanced), or None."""
    if not isinstance(value, str):
        return None
    parts = [p.strip() for p in value.split("|")]
    if len(parts) != 3 or not parts[0]:
        return None
    return {"by": parts[0], "level": normalize_level(parts[1]), "on": parts[2]}


def assessments_of(fm: dict):
    """(ratings, problems): every assessor's rating a note records, as {by, level, on, raw}. `raw` is the string in
    `assessments`, or None for the one rating kept the old way (assessedLevel, assessedBy, assessedOn), which is read
    as one more unless `assessments` already has that assessor's. An assessor listed twice counts once, the later
    date winning. Problems are what the checker reports: an entry not in the form, a level off the scale, a date
    that is not a day."""
    ratings, problems = [], []
    value = fm.get(ASSESSMENTS)
    if value not in (None, "", []):
        if not isinstance(value, list):
            problems.append(f"`{ASSESSMENTS}` must be a list of \"<assessor> | <level> | <YYYY-MM-DD>\"")
            value = []
        for item in value:
            r = parse_assessment(item)
            if r is None:
                problems.append(f"`{ASSESSMENTS}`: {item!r} is not \"<assessor> | <level> | <YYYY-MM-DD>\"")
                continue
            if r["level"] not in LEVELS:
                problems.append(f"`{ASSESSMENTS}`: {r['by']}'s level {r['level']!r} is not one of {sorted(LEVELS)}")
                continue
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", r["on"]):
                problems.append(f"`{ASSESSMENTS}`: {r['by']}'s date {r['on']!r} is not a day (YYYY-MM-DD)")
            same = next((x for x in ratings if x["by"].casefold() == r["by"].casefold()), None)
            if same:
                problems.append(f"`{ASSESSMENTS}`: {r['by']} is listed twice; the later rating counts")
                if r["on"] >= same["on"]:
                    same.update(level=r["level"], on=r["on"], raw=str(item))
                continue
            ratings.append({**r, "raw": str(item)})
    old = fm.get("assessedLevel")
    if old in LEVELS:
        by = str(as_text(fm.get("assessedBy")) or "").strip() or UNNAMED
        if not any(x["by"].casefold() == by.casefold() for x in ratings):
            ratings.append({"by": by, "level": old, "on": str(as_text(fm.get("assessedOn")) or ""), "raw": None})
    return ratings, problems


def agreed_level(ratings) -> str:
    """The assessed level of a note with several assessors: the highest level every one of them supports, which is
    the lowest of their ratings ('' with none). One assessor's rating is that assessor's."""
    levels = [r["level"] for r in ratings if r["level"] in LEVELS]
    return min(levels, key=LEVEL_RANK.get) if levels else ""


def assessor_spread(ratings) -> int:
    """How many levels apart the assessors are: 0 when they agree, or when fewer than two have rated."""
    ranks = [LEVEL_RANK[r["level"]] for r in ratings if r["level"] in LEVELS]
    return max(ranks) - min(ranks) if len(ranks) > 1 else 0


def level_label(word) -> str:
    """'advanced' -> 'L3 Advanced'; 'none' and blanks pass through ('unrated' for a blank)."""
    if word in (None, ""):
        return "unrated"
    return LEVEL_LABELS.get(word, str(word))
# kinds of outside recognition (spec §3.5), adapted from FRICS characteristics and USCIS O-1 criteria
RECOGNITION = {"credential", "assessing", "teaching", "publication", "adoption", "appointment", "award"}
LED_UNIT_TYPES = {"role", "engagement", "activity"}   # other units count as led work only with recognition
KNOWLEDGE_ONLY = {"credential", "course"}            # not delivered work: alone, these support `aware`
# v0.3 and earlier called competency notes "skills" and the finest rank "skill"; both are still read (spec §10)
LEGACY_TYPES = {"skill": "competency"}
LEGACY_RANKS = {"skill": "element"}
CONTROLLED = {
    "competency": {
        "kind": {"practice", "method", "tool", "knowledge"},
        "rank": {"domain", "discipline", "specialty", "element", "branch"},
        "claimedLevel": LEVELS,
        "assessedLevel": LEVELS,
        "status": {"active", "dormant", "retired"},
    },
    "sector": {"claimedLevel": LEVELS, "assessedLevel": LEVELS},
    # layer 3 (spec §2.4, §2.5): an organisation the work was done for, and a person who can speak to it. Thin notes:
    # a name, other spellings, and a pointer to the owner's own contact record
    "organization": {},
    "person": {},
    "evidence": {
        "evidenceType": {"role", "engagement", "activity", "project", "credential", "publication", "course"},
        "disclosure": {"public", "on-request", "confidential"},
    },
}
# field -> required target nodeType (None = any resolvable note)
# `requires` and `appliedTo` are the named relations between competencies (spec §2.1); `referee` names the people who
# can vouch for a piece of evidence. `organization` is not here: on evidence and on a person it is text or a link
# (Analyzer.org_key)
LINK_FIELDS = {
    "competency": {"broader": "competency", "related": None, "sector": "sector", "requires": "competency",
                   "appliedTo": "competency"},
    "sector": {"broader": "sector", "related": None},
    "evidence": {"demonstrates": "competency", "demonstratesLed": "competency", "sector": "sector", "partOf": "evidence",
                 "referee": "person"},
    "organization": {"sector": "sector"},
    "person": {},
}
SINGLE_LINK_FIELDS = {"partOf"}
REQUIRED = {
    "organization": [],
    "person": [],
    "competency": ["kind"],
    "sector": ["code"],
    "evidence": ["evidenceType", "period", "disclosure"],
}
WORK_TYPES = {"role", "engagement"}
RECENCY_PRACTICE = {"role", "engagement", "activity"}
RECENCY_OTHER = {"role", "engagement", "activity", "project", "course"}
DEMONSTRATES_SPLIT_AT = 15
DEFAULT_EXCLUDE = {".git", ".obsidian", ".trash", ".claude", "node_modules"}  # .claude: skills, incl. this one's test fixtures

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", re.DOTALL)
WIKILINK = re.compile(r"^\s*\[\[([^\]]+)\]\]\s*$")
DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
PERIOD_SEP = " – "  # en dash with spaces


# --------------------------------------------------------------------------- model

@dataclass
class Node:
    path: str          # vault-relative, forward slashes
    name: str          # basename without .md
    type: str
    fm: dict


@dataclass
class Finding:
    code: str
    path: str
    message: str

    def line(self) -> str:
        return f"- `{self.code}` {self.path}: {self.message}"


@dataclass
class Result:
    nodes: dict = field(default_factory=dict)            # path -> Node
    edges: list = field(default_factory=list)            # (src, dst, field)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    insights: dict = field(default_factory=dict)         # title -> list[str]
    stats: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- loading

def read_front_matter(text: str):
    m = FRONT_MATTER.match(text)
    if not m:
        return None
    return yaml.safe_load(m.group(1))


def load_settings(profile_path: str | None) -> dict:
    settings = {"staleYears": 5, "periodAliases": [], "exclude": [], "practitionerMinMonths": 6.0,
                "advancedMinYears": 5.0, "expertMinYears": 10.0, "expertMinRecognition": 1}
    if not profile_path:
        return settings
    with open(profile_path, encoding="utf-8") as fh:
        fm = read_front_matter(fh.read()) or {}
    if "kgStaleYears" in fm:
        settings["staleYears"] = int(fm["kgStaleYears"])
    settings["periodAliases"] = list(fm.get("kgPeriodAliases") or [])
    settings["exclude"] = list(fm.get("kgExclude") or [])
    if fm.get("kgPractitionerMinMonths") is not None:
        settings["practitionerMinMonths"] = float(fm["kgPractitionerMinMonths"])
    if fm.get("kgExpertMinYears") is not None:
        settings["expertMinYears"] = float(fm["kgExpertMinYears"])
    if fm.get("kgAdvancedMinYears") is not None:
        settings["advancedMinYears"] = float(fm["kgAdvancedMinYears"])
    if fm.get("kgExpertMinRecognition") is not None:
        settings["expertMinRecognition"] = int(fm["kgExpertMinRecognition"])
    return settings


def scan_vault(vault: str, exclude: set):
    """Return (name index: lowercase basename -> [paths], nodes, parse errors)."""
    index: dict[str, list[str]] = defaultdict(list)
    nodes: dict[str, Node] = {}
    parse_errors: list[Finding] = []
    for root, dirs, files in os.walk(vault):
        rel_root = os.path.relpath(root, vault)
        dirs[:] = sorted(
            d for d in dirs
            if d not in exclude and os.path.normpath(os.path.join(rel_root, d)) not in exclude
        )
        for fname in sorted(files):
            if not fname.lower().endswith(".md"):
                continue
            rel = os.path.normpath(os.path.join(rel_root, fname)).replace(os.sep, "/")
            name = fname[:-3]
            index[name.lower()].append(rel)
            try:
                with open(os.path.join(root, fname), encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError):
                continue
            if not text.startswith("---"):
                continue
            try:
                fm = read_front_matter(text)
            except yaml.YAMLError as exc:
                if "nodeType:" in text[:4000]:
                    parse_errors.append(Finding("yaml", rel, f"front matter does not parse: {exc}".splitlines()[0]))
                continue
            if isinstance(fm, dict) and fm.get("nodeType") in LEGACY_TYPES:
                fm["nodeType"] = LEGACY_TYPES[fm["nodeType"]]      # v0.3 graphs: `nodeType: skill`
            if isinstance(fm, dict) and fm.get("nodeType") in CONTROLLED:
                if fm.get("rank") in LEGACY_RANKS:
                    fm["rank"] = LEGACY_RANKS[fm["rank"]]
                for key in LEVEL_FIELDS:
                    if key in fm:
                        fm[key] = normalize_level(fm[key])
                nodes[rel] = Node(rel, name, fm["nodeType"], fm)
    return index, nodes, parse_errors


# --------------------------------------------------------------------------- helpers

def as_text(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    if isinstance(value, int) and not isinstance(value, bool):   # unquoted year, e.g. `period: 2015`
        return str(value)
    return value


def parse_date(text: str, end: bool, today: dt.date):
    text = text.strip()
    if text.lower() == "present":
        return today
    m = DATE_RE.match(text)
    if not m:
        raise ValueError(text)
    y = int(m.group(1))
    if m.group(2) is None:                       # YYYY
        return dt.date(y, 12, 31) if end else dt.date(y, 1, 1)
    mo, d = int(m.group(2)), m.group(3)
    if d is not None:                            # YYYY-MM-DD
        return dt.date(y, mo, int(d))
    return dt.date(y, mo, calendar.monthrange(y, mo)[1] if end else 1)   # YYYY-MM


def parse_period(value, today: dt.date):
    """Return (start, end) or raise ValueError."""
    text = as_text(value)
    if not isinstance(text, str) or not text.strip():
        raise ValueError(repr(value))
    if PERIOD_SEP in text:
        start_s, end_s = text.split(PERIOD_SEP, 1)
    else:
        start_s = end_s = text
    start, end = parse_date(start_s, False, today), parse_date(end_s, True, today)
    if end < start:
        raise ValueError(f"end before start in {text!r}")
    return start, end


def years_before(day: dt.date, years: int) -> dt.date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 February
        return day.replace(year=day.year - years, day=28)


# --------------------------------------------------------------------------- analysis

class Analyzer:
    def __init__(self, vault: str, settings: dict, today: dt.date):
        self.vault = vault
        self.settings = settings
        self.today = today
        self.r = Result()

    # ---- findings
    def err(self, code, path, msg):
        self.r.errors.append(Finding(code, path, msg))

    def warn(self, code, path, msg):
        self.r.warnings.append(Finding(code, path, msg))

    # ---- link resolution
    def resolve(self, raw: str):
        """Return (path | None, problem | None)."""
        m = WIKILINK.match(raw)
        if not m:
            return None, f"not a wikilink: {raw!r} (use \"[[Note]]\")"
        target = m.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if target.lower().endswith(".md"):
            target = target[:-3]
        if "/" in target:
            suffix = (target + ".md").lower()
            hits = [p for paths in self.index.values() for p in paths
                    if p.lower() == suffix or p.lower().endswith("/" + suffix)]
        else:
            hits = self.index.get(target.lower(), [])
        if not hits:
            return None, f"broken link [[{target}]]"
        if len(hits) > 1:
            return None, f"ambiguous link [[{target}]] matches {len(hits)} files: {', '.join(hits[:4])}"
        return hits[0], None

    def link_values(self, node: Node, fname: str):
        value = node.fm.get(fname)
        if value is None or value == [] or value == "":
            return []
        if isinstance(value, dict) or (isinstance(value, list) and any(isinstance(v, (dict, list)) for v in value)):
            self.err("nested", node.path, f"`{fname}` contains a nested object; use a flat list of \"[[Note]]\"")
            return []
        values = value if isinstance(value, list) else [value]
        if fname in SINGLE_LINK_FIELDS and len(values) > 1:
            self.err("single", node.path, f"`{fname}` takes one link, found {len(values)}")
        out = []
        for v in values:
            if not isinstance(v, str):
                self.err("link-type", node.path, f"`{fname}` item {v!r} is not a quoted wikilink")
                continue
            out.append(v)
        return out

    # ---- main
    def run(self) -> Result:
        exclude = DEFAULT_EXCLUDE | set(self.settings["exclude"])
        self.index, nodes, parse_errors = scan_vault(self.vault, exclude)
        self.r.nodes = nodes
        self.r.errors.extend(parse_errors)
        self.links = defaultdict(lambda: defaultdict(list))   # path -> field -> [target paths]

        for node in nodes.values():
            self.check_fields(node)
            self.check_name(node)
            for fname, want in LINK_FIELDS[node.type].items():
                for raw in self.link_values(node, fname):
                    target, problem = self.resolve(raw)
                    if problem:
                        self.err("link", node.path, f"`{fname}`: {problem}")
                        continue
                    if want and (target not in nodes or nodes[target].type != want):
                        got = nodes[target].type if target in nodes else "a non-graph note"
                        self.err("target", node.path, f"`{fname}` → {target} is {got}, expected {want}")
                        continue
                    self.links[node.path][fname].append(target)
                    self.r.edges.append((node.path, target, fname))

        self.competencies = {p for p, n in nodes.items() if n.type == "competency"}
        self.sectors = {p for p, n in nodes.items() if n.type == "sector"}
        self.evidence = {p for p, n in nodes.items() if n.type == "evidence"}
        self.organizations = {p for p, n in nodes.items() if n.type == "organization"}
        self.people = {p for p, n in nodes.items() if n.type == "person"}
        self.index_organizations()

        self.check_competency_structure()
        self.check_sectors()
        self.check_evidence()
        self.compute_support()
        self.check_claims()
        self.compute_insights()
        self.r.stats = {
            "competencies": len(self.competencies), "sectors": len(self.sectors), "evidence": len(self.evidence),
            "edges": len(self.r.edges), "units": len(set(self.root.values())),
            "organizations": len(self.organizations), "people": len(self.people),
        }
        return self.r

    # ---- per-node field checks
    def check_fields(self, node: Node):
        for fname in REQUIRED[node.type]:
            if fname == "period" and self.period_value(node) is not None:
                continue
            if node.fm.get(fname) in (None, "", []):
                self.err("required", node.path, f"missing required field `{fname}`")
        for fname, allowed in CONTROLLED[node.type].items():
            value = node.fm.get(fname)
            if value is not None and value not in allowed:
                self.err("value", node.path, f"`{fname}: {value}` not in {sorted(allowed)}")
        if node.fm.get("assessedLevel") in LEVELS:          # a rating nobody can be asked about is not an assessment
            gaps = [k for k in ("assessedBy", "assessedOn") if node.fm.get(k) in (None, "", [])]
            when = as_text(node.fm.get("assessedOn"))
            if gaps:
                self.warn("assessment", node.path, f"`assessedLevel` without {' or '.join(f'`{k}`' for k in gaps)}: "
                                                   "say who gave the rating and when")
            elif not (isinstance(when, str) and DATE_RE.match(when)):
                self.warn("assessment", node.path, f"`assessedOn: {when}` is not a date (YYYY-MM-DD)")
        elif any(node.fm.get(k) not in (None, "", []) for k in ("assessedBy", "assessedOn")):
            self.warn("assessment", node.path, "`assessedBy` or `assessedOn` without an `assessedLevel`")
        if node.type in ("competency", "sector"):
            ratings, problems = assessments_of(node.fm)
            for p in problems:
                self.warn("assessment", node.path, p)
            if assessor_spread(ratings):                    # the assessors disagree: say so, and what counts meanwhile
                said = ", ".join(f"{r['by']} {level_label(r['level'])}" for r in
                                 sorted(ratings, key=lambda r: -LEVEL_RANK[r["level"]]))
                self.warn("assessors-differ", node.path, f"the assessors rate this {assessor_spread(ratings)} level(s) "
                          f"apart ({said}); the assessed level is the lowest, {level_label(agreed_level(ratings))}")
        if node.type == "evidence" and node.fm.get("recognition") not in (None, "", []):
            rec = node.fm["recognition"]
            bad = [v for v in (rec if isinstance(rec, list) else [rec]) if v not in RECOGNITION]
            if not isinstance(rec, list) or bad:
                self.err("value", node.path, f"`recognition` must be a list drawn from {sorted(RECOGNITION)}"
                                             + (f"; not allowed: {bad}" if bad else ""))

    def check_name(self, node: Node):
        hits = self.index.get(node.name.lower(), [])
        if len(hits) > 1:
            others = [h for h in hits if h != node.path]
            self.err("name", node.path, f"filename is not unique in the vault (also: {', '.join(others[:4])})")

    # ---- organisations (spec §2.4): one organisation however an evidence note spells it
    def index_organizations(self):
        """Every name an organisation note answers to (its filename, its title, its aliases) -> the note."""
        self.org_names = {}
        for p in sorted(self.organizations):
            n = self.r.nodes[p]
            aliases = n.fm.get("aliases") or []
            for name in [n.name, n.fm.get("title"), *(aliases if isinstance(aliases, list) else [aliases])]:
                key = " ".join(str(name or "").split()).casefold()
                if not key:
                    continue
                if self.org_names.get(key, p) != p:
                    self.warn("organization", p, f"the name {str(name)!r} is also {self.org_names[key]}'s: one "
                                                 "organisation, one note")
                    continue
                self.org_names[key] = p

    def org_key(self, value) -> str:
        """What an `organization` value counts as: the organisation note it links to or names (by filename, title or
        alias), else its own text in lower case. '' for none."""
        text = " ".join(str(as_text(value) or "").split())
        if not text:
            return ""
        m = WIKILINK.match(text)
        if m:
            target, _ = self.resolve(text)
            if target in self.organizations:
                return target
            text = m.group(1).split("|", 1)[0].strip()
        return self.org_names.get(text.casefold(), text.casefold())

    def org_name(self, value) -> str:
        """The organisation as a reader should see it: the note's title where there is one, else the text given."""
        key = self.org_key(value)
        if key in self.organizations:
            return str(self.r.nodes[key].fm.get("title") or self.r.nodes[key].name)
        text = " ".join(str(as_text(value) or "").split())
        m = WIKILINK.match(text)
        return m.group(1).split("|", 1)[0].strip() if m else text

    def anchored(self, evidence: set) -> bool:
        """Something a third party could check: an `anchor`, or a `referee` who can be asked."""
        return any(self.r.nodes[e].fm.get("anchor") or self.links[e].get("referee") for e in evidence)

    def period_value(self, node: Node):
        for fname in ["period", *self.settings["periodAliases"]]:
            if node.fm.get(fname) not in (None, ""):
                return node.fm[fname]
        return None

    # ---- graph structure
    def find_cycles(self, members: set, fname: str, label: str):
        state = {}
        reported = set()

        def visit(p, stack):
            state[p] = 1
            stack.append(p)
            for q in self.links[p].get(fname, []):
                if q not in members:
                    continue
                if state.get(q) == 1:
                    cycle = stack[stack.index(q):]
                    key = frozenset(cycle)
                    if key not in reported:
                        reported.add(key)
                        self.err("cycle", q, f"{label} cycle: " + " → ".join(cycle + [q]))
                elif q not in state:
                    visit(q, stack)
            stack.pop()
            state[p] = 2

        for p in sorted(members):
            if p not in state:
                visit(p, [])

    def ancestors(self, path: str, fname: str = "broader") -> set:
        seen, todo = set(), [path]
        while todo:
            p = todo.pop()
            for q in self.links[p].get(fname, []):
                if q not in seen:
                    seen.add(q)
                    todo.append(q)
        seen.discard(path)
        return seen

    def check_competency_structure(self):
        self.find_cycles(self.competencies, "broader", "broader")
        self.find_cycles(self.competencies, "requires", "requires")
        nodes = self.r.nodes
        for p in sorted(self.competencies):
            # `appliedTo` runs from a method, a tool or a piece of knowledge to the practice it serves (spec §2.1)
            for q in self.links[p].get("appliedTo", []):
                if nodes[p].fm.get("kind", "practice") == "practice":
                    self.warn("relation", p, f"`appliedTo` is for a method, tool or knowledge; between two practices "
                                             f"({nodes[q].name}) use `related`")
                elif nodes[q].fm.get("kind", "practice") != "practice":
                    self.warn("relation", p, f"`appliedTo` → {nodes[q].name} is a {nodes[q].fm.get('kind')}, "
                                             "expected a practice")
            for q in self.links[p].get("requires", []):
                if q in self.ancestors(p) or p in self.ancestors(q):
                    self.warn("relation", p, f"`requires` → {nodes[q].name} is already above or below this competency "
                                             "in the tree; a prerequisite is a different competency")
        self.domains = {p for p in self.competencies if nodes[p].fm.get("rank") == "domain"}
        for p in sorted(self.competencies):
            if p in self.domains:
                if self.links[p].get("broader"):
                    self.warn("domain-parent", p, "a domain should not have `broader`")
                continue
            if not nodes[p].fm.get("broader"):
                self.err("orphan", p, "non-domain competency with no `broader` (set `rank: domain` if it is a domain)")
        for p in sorted(self.competencies | self.sectors):
            for q in self.links[p].get("related", []):
                if p < q and p in self.links[q].get("related", []):
                    self.warn("related-twice", p, f"`related` is stored on both this note and {q}; keep it on one side")
        self.domain_of = {p: ({a for a in self.ancestors(p) | {p} if a in self.domains}) for p in self.competencies}
        self.primary_domain = {p: self.walk_primary(p) for p in self.competencies}

    def walk_primary(self, p):
        """Domain reached by following the first (main) `broader` link upward."""
        seen = set()
        while p not in self.domains:
            parents = self.links[p].get("broader", [])
            if not parents or p in seen:
                return None
            seen.add(p)
            p = parents[0]
        return p

    def check_sectors(self):
        self.find_cycles(self.sectors, "broader", "sector broader")
        seen = {}
        for p in sorted(self.sectors):
            code = self.r.nodes[p].fm.get("code")
            if code is None:
                continue
            if not isinstance(code, str):
                self.err("code", p, f"`code: {code}` must be a quoted string, e.g. code: \"{code}\"")
                code = str(code)
            if code in seen:
                self.err("code-dup", p, f"sector code {code!r} also used by {seen[code]}")
            else:
                seen[code] = p

        def top(p):
            chain = [p] + sorted(self.ancestors(p))
            roots = [q for q in chain if not self.links[q].get("broader")]
            return roots[0] if roots else p
        self.sector_top = {p: top(p) for p in self.sectors}

    def check_evidence(self):
        nodes = self.r.nodes
        self.find_cycles(self.evidence, "partOf", "partOf")
        self.period = {}
        for p in sorted(self.evidence):
            n = nodes[p]
            raw = self.period_value(n)
            if raw is not None:
                try:
                    self.period[p] = parse_period(raw, self.today)
                except ValueError as exc:
                    self.err("period", p, f"cannot parse period {as_text(raw)!r} ({exc}); "
                                          "use YYYY-MM-DD, YYYY-MM or YYYY, 'START – END', END may be 'present'")
        self.children = defaultdict(list)
        for p in self.evidence:
            for parent in self.links[p].get("partOf", []):
                self.children[parent].append(p)

        def root(p):
            seen = {p}
            while self.links[p].get("partOf"):
                q = self.links[p]["partOf"][0]
                if q in seen:
                    break
                seen.add(q)
                p = q
            return p
        self.root = {p: root(p) for p in self.evidence}

        for p in sorted(self.evidence):
            fm, etype = nodes[p].fm, nodes[p].fm.get("evidenceType")
            demos = self.links[p].get("demonstrates", [])
            if not (fm.get("demonstrates") or fm.get("demonstratesLed")) and not self.children[p]:
                self.warn("no-competencies", p, "demonstrates nothing and has no child projects")
            if len(demos) > DEMONSTRATES_SPLIT_AT and not self.children[p]:
                self.warn("split", p, f"`demonstrates` has {len(demos)} links; split specific work into "
                                      "project notes with `partOf`")
            if not self.anchored({p}) and not self.links[p].get("partOf"):
                # projects inside a role are vouched for through the role's anchor
                self.warn("anchor", p, "no `anchor` a third party could check, and no `referee`")
            if etype in WORK_TYPES:
                if not fm.get("sector") and not self.links[p].get("sector"):
                    self.warn("sector", p, f"{etype} has no `sector`")
            if etype in WORK_TYPES | {"activity"}:
                if not fm.get("organization"):
                    self.warn("organization", p, f"{etype} has no `organization`")

    # ---- support, claims, recency
    def compute_support(self):
        self.competency_support = defaultdict(set)    # competency -> evidence paths (rolled up)
        self.led_support = defaultdict(set)      # competency -> evidence that led it (rolled up)
        self.led_direct = defaultdict(set)       # competency -> evidence that led exactly this competency
        self.sector_support = defaultdict(set)
        self.ev_sectors = {}
        self._levels = {}
        for e in self.evidence:
            led = self.links[e].get("demonstratesLed", [])
            for s in self.links[e].get("demonstrates", []) + led:
                for target in {s} | self.ancestors(s):
                    self.competency_support[target].add(e)
            for s in led:
                self.led_direct[s].add(e)
                for target in {s} | self.ancestors(s):
                    self.led_support[target].add(e)
            secs = self.links[e].get("sector") or self.links[self.root[e]].get("sector", [])
            self.ev_sectors[e] = secs
            for s in secs:
                for target in {s} | self.ancestors(s):
                    self.sector_support[target].add(e)

    def unit_profile(self, support: set):
        units = {self.root[e] for e in support}
        orgs = {self.org_key(self.r.nodes[u].fm.get("organization")) for u in units} - {""}
        return units, orgs, self.anchored(support | units)

    def recency_of(self, p):
        """(latest end date, basis) for a competency or sector note. basis: 'work', 'project-only' or None.
        Practices use work evidence (roles, engagements, activities) when any exists; a practice evidenced
        only by projects/courses falls back to those, labelled 'project-only'."""
        nodes = self.r.nodes
        support = self.competency_support[p] if nodes[p].type == "competency" else self.sector_support[p]
        units = {self.root[e] for e in support}
        kind = nodes[p].fm.get("kind", "practice") if nodes[p].type == "competency" else "practice"
        def latest(types):
            ends = [self.period[u][1] for u in units if nodes[u].fm.get("evidenceType") in types and u in self.period]
            return max(ends) if ends else None
        if kind != "practice":
            d = latest(RECENCY_OTHER)
            return d, ("work" if d else None)
        d = latest(RECENCY_PRACTICE)
        if d:
            return d, "work"
        if any(nodes[u].fm.get("evidenceType") in RECENCY_PRACTICE for u in units):
            return None, None            # work evidence exists but is undated
        d = latest(RECENCY_OTHER)
        return d, ("project-only" if d else None)

    def years_of(self, p):
        """Years of dated evidence behind a competency or sector note (overlapping periods merged),
        using the same basis as recency: work evidence for practices when any exists, else projects."""
        nodes = self.r.nodes
        support = self.competency_support[p] if nodes[p].type == "competency" else self.sector_support[p]
        units = {self.root[e] for e in support}
        kind = nodes[p].fm.get("kind", "practice") if nodes[p].type == "competency" else "practice"
        if kind != "practice":
            types = RECENCY_OTHER
        elif any(nodes[u].fm.get("evidenceType") in RECENCY_PRACTICE for u in units):
            types = RECENCY_PRACTICE
        else:
            types = RECENCY_OTHER
        spans = sorted(self.period[u] for u in units if nodes[u].fm.get("evidenceType") in types and u in self.period)
        total, cur = 0, None
        for start, end in spans:
            if cur and start <= cur[1]:
                cur = (cur[0], max(cur[1], end))
            else:
                if cur:
                    total += (cur[1] - cur[0]).days + 1
                cur = (start, end)
        if cur:
            total += (cur[1] - cur[0]).days + 1
        return round(total / 365.25, 1)

    def recognition_of(self, evidence: set) -> set:
        """Kinds of outside recognition carried by these evidence notes or their unit roots."""
        kinds = set()
        for e in evidence:
            for q in (e, self.root[e]):
                rec = self.r.nodes[q].fm.get("recognition")
                if isinstance(rec, list):
                    kinds |= {k for k in rec if k in RECOGNITION}
        return kinds

    def span_years(self, units) -> float:
        """Years covered by these notes' own periods, overlaps merged."""
        spans = sorted(self.period[u] for u in units if u in self.period)
        total, cur = 0, None
        for start, end in spans:
            if cur and start <= cur[1]:
                cur = (cur[0], max(cur[1], end))
            else:
                if cur:
                    total += (cur[1] - cur[0]).days + 1
                cur = (start, end)
        if cur:
            total += (cur[1] - cur[0]).days + 1
        return round(total / 365.25, 1)

    def span_months(self, units) -> float:
        """Calendar months covered by these notes' own periods, overlaps merged. A period that runs from the
        first day of one month to the last day of the sixth is exactly six months, whatever the months' lengths."""
        spans = sorted(self.period[u] for u in units if u in self.period)
        merged = []
        for start, end in spans:
            if merged and start <= merged[-1][1] + dt.timedelta(days=1):
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        total = 0.0
        for start, end in merged:
            stop = end + dt.timedelta(days=1)                     # periods include their last day
            whole = (stop.year - start.year) * 12 + stop.month - start.month
            part = (stop.day - start.day) / calendar.monthrange(start.year, start.month)[1]
            total += whole + part
        return total

    def led_units(self, evidence: set) -> set:
        """Independent units of led work. Own projects, courses and the like count only with recognition."""
        nodes, units = self.r.nodes, set()
        for e in evidence:
            u = self.root[e]
            if nodes[u].fm.get("evidenceType") in LED_UNIT_TYPES or self.recognition_of({e}):
                units.add(u)
        return units

    def child_competencies(self, p):
        """Competencies directly under p, looking through branch roots (which aren't rated)."""
        out = []
        for q in self.competencies:
            if p in self.links[q].get("broader", []):
                out += self.child_competencies(q) if self.r.nodes[q].fm.get("rank") == "branch" else [q]
        return out

    def _meets(self, led_evidence: set, want: str, rec_evidence: set | None = None) -> dict:
        units = self.led_units(led_evidence)
        orgs = {self.org_key(self.r.nodes[u].fm.get("organization")) for u in units} - {""}
        anchored = self.anchored(led_evidence | units)
        # led years come from the led notes' own dates: a project led inside a long role counts the project's
        # period, not the whole role's (an undated project carries its role's period, an honest upper bound)
        counted = {e for e in led_evidence if self.root[e] in units}
        years = self.span_years({e if e in self.period else self.root[e] for e in counted})
        kinds = self.recognition_of(led_evidence if rec_evidence is None else rec_evidence)
        st = self.settings
        missing = []
        if len(units) < 2:
            missing.append(f"{len(units)} led unit(s), needs 2")
        if not (len(orgs) >= 2 or anchored):
            missing.append(f"{len(orgs)} organisation(s) and no anchor, needs 2 organisations or an anchor")
        min_years = st["advancedMinYears"] if want == "advanced" else st["expertMinYears"]
        if years < min_years:
            missing.append(f"{years:g} years of led work, needs {min_years:g}")
        if want == "expert" and len(kinds) < st["expertMinRecognition"]:
            missing.append(f"{len(kinds)} kind(s) of outside recognition, needs {st['expertMinRecognition']}")
        return {"units": len(units), "orgs": len(orgs), "anchored": anchored, "years": years,
                "recognition": sorted(kinds), "missing": missing}

    def level_detail(self, p) -> dict:
        """Highest level the evidence supports for a competency or sector note (spec §3.5), with the reasons.

        practitioner  delivered work (not just a course or credential) whose units' periods add up to
                      >= practitionerMinMonths; the work need not be led
        advanced     >=2 independent units of led work, >=2 organisations or an anchor, >= advancedMinYears
        expert        advanced, and >= expertMinYears of led work and >= expertMinRecognition kinds of
                      outside recognition
        A parent reaches advanced or expert from led work on exactly that note, or else through led work
        on narrower competencies only when one of its children reaches that level itself (no roll-up inflation).
        Sectors have no led work: their whole support is counted the same way."""
        if p in self._levels:
            return self._levels[p]
        self._levels[p] = {"level": "none"}          # cycle guard
        nodes = self.r.nodes
        is_comp = nodes[p].type == "competency"
        support = self.competency_support[p] if is_comp else self.sector_support[p]
        units = {self.root[e] for e in support}
        delivered = {u for u in units if nodes[u].fm.get("evidenceType") not in KNOWLEDGE_ONLY}
        # practitioner needs time doing the work, not one short piece of it: the delivered units' periods
        # (a project inside a role counts the role's, as Years of work does) must add up to practitionerMinMonths.
        # Delivering is enough here; leading the work is what advanced and expert ask for.
        months = self.span_months(delivered)
        need = self.settings["practitionerMinMonths"]
        too_short = []
        if delivered and months + 1e-9 < need:
            dated = any(u in self.period for u in delivered)
            too_short = [f"{round(months, 1):g} months of delivered work, needs {need:g}" if dated
                         else f"no dated delivered work, needs {need:g} months"]
        detail = {"level": "practitioner" if delivered and not too_short else ("aware" if units else "none"),
                  "via": "", "missing": [], "workMonths": round(months, 1)}
        kids = self.child_competencies(p) if is_comp else []
        for want in ("advanced", "expert"):
            if is_comp:
                # recognition counts from any evidence of this competency or a narrower one (a credential is never led)
                direct = self._meets(self.led_direct[p], want, support)
                rolled = self._meets(self.led_support[p], want, support)
                kid_ok = [q for q in kids if LEVEL_RANK[self.level_detail(q)["level"]] >= LEVEL_RANK[want]]
                if not direct["missing"]:
                    ok, info, via = True, direct, "led work on this competency"
                elif not rolled["missing"] and kid_ok:
                    ok, info, via = True, rolled, "led work on narrower competencies, with " + \
                        ", ".join(sorted(nodes[q].fm.get("title") or nodes[q].name for q in kid_ok)[:3]) + \
                        f" also {want}"
                else:
                    ok, info, via = False, rolled, ""
                    if not rolled["missing"] and kids:
                        info = dict(rolled, missing=[f"no narrower competency is {want} on its own"])
            else:
                info = self._meets(support, want)
                ok, via = not info["missing"], "sector evidence"
            detail.update({k: info[k] for k in ("units", "orgs", "anchored", "years", "recognition")})
            if not ok:
                detail["missing"] = info["missing"]
                detail["next"] = want
                break
            detail["level"], detail["via"], detail["missing"] = want, via, []
        if too_short and detail["level"] == "aware":             # the next level up is practitioner, not advanced
            detail["missing"], detail["next"] = too_short, "practitioner"
        self._levels[p] = detail
        return detail

    def supports_level(self, p):
        """Highest claimedLevel the evidence supports: 'expert' | 'advanced' | 'practitioner' | 'aware' | 'none'."""
        return self.level_detail(p)["level"]

    def check_claims(self):
        nodes = self.r.nodes
        stale_cut = years_before(self.today, self.settings["staleYears"])
        self.claim_rows = []
        for p in sorted(self.competencies | self.sectors):
            n = nodes[p]
            level = n.fm.get("claimedLevel")
            support = self.competency_support[p] if n.type == "competency" else self.sector_support[p]
            units, orgs, anchored = self.unit_profile(support)
            ok = True
            deemed = n.fm.get("deemed")                   # owner attestation without evidence (spec §2.1): not "unsupported"
            if level in LEVELS and level != "aware" and not deemed:   # an aware claim needs no evidence
                d = self.level_detail(p)
                if LEVEL_RANK[level] > LEVEL_RANK[d["level"]]:
                    ok = False
                    if d["level"] == "none":
                        why = "no evidence"
                    elif d["level"] == "aware" and d.get("next") == "practitioner":
                        why = "; ".join(d["missing"])
                    elif d["level"] == "aware":
                        why = "no delivered work; courses and credentials alone support aware"
                    else:
                        why = f"for {level_label(d['next'])}: " + "; ".join(d["missing"])
                    self.warn("unsupported", p, f"claims {level_label(level)}, evidence supports "
                                                f"{level_label(d['level'])} ({why})")
            # a claim rests on what it requires (spec §3.10): it should not stand above the claim made for a
            # prerequisite. Reported, like every check; neither level is changed
            for q in self.links[p].get("requires", []) if level in LEVELS else []:
                held = nodes[q].fm.get("claimedLevel") if nodes[q].fm.get("claimedLevel") in LEVELS else None
                if LEVEL_RANK[level] > LEVEL_RANK.get(held or "none", 0):
                    self.warn("prerequisite", p, f"claims {level_label(level)} but requires "
                              f"{nodes[q].fm.get('title') or nodes[q].name}, which is "
                              f"{'claimed at ' + level_label(held) if held else 'not rated'}")
            recency = None
            if level in LEVELS and units:
                recency, basis = self.recency_of(p)
                if n.fm.get("status", "active") == "active" and level != "aware":
                    if recency is None:
                        self.warn("stale", p, "no dated evidence that counts toward recency")
                    elif recency < stale_cut:
                        self.warn("stale", p, f"most recent eligible evidence ({basis}) ended {recency.isoformat()}, "
                                              f"more than {self.settings['staleYears']} years ago")
            if n.type == "competency":
                self.claim_rows.append((p, level, len(units), ok, recency))

    # ---- insights
    def compute_insights(self):
        nodes = self.r.nodes
        title = lambda p: nodes[p].fm.get("title") or nodes[p].name
        ins = {}
        ins["Deemed competencies (claimed on the owner's word, no evidence)"] = [
            f"{title(p)}: {level_label(nodes[p].fm.get('claimedLevel'))} ({nodes[p].fm.get('deemed')})"
            for p in sorted(self.competencies, key=title) if nodes[p].fm.get("deemed")]

        # A competency is cross-domain only where it declares parents whose main lines reach different domains;
        # its descendants inherit evidence roll-up but are not re-reported.
        multi = []
        for p in sorted(self.competencies - self.domains, key=title):
            reach = {self.primary_domain.get(q) for q in self.links[p].get("broader", [])} - {None}
            if len(reach) >= 2:
                multi.append(f"{title(p)}: {', '.join(sorted(title(d) for d in reach))}")
        ins["Competencies bridging two or more domains"] = multi

        unit_domains = defaultdict(set)
        for e in self.evidence:
            for s in self.links[e].get("demonstrates", []) + self.links[e].get("demonstratesLed", []):
                if self.primary_domain.get(s):
                    unit_domains[self.root[e]].add(self.primary_domain[s])
        ins["Evidence units spanning two or more domains"] = [
            f"{title(u)}: {', '.join(sorted(title(d) for d in ds))}"
            for u, ds in sorted(unit_domains.items(), key=lambda kv: title(kv[0])) if len(ds) >= 2]

        pairs = defaultdict(list)
        for u, ds in unit_domains.items():
            ds = sorted(ds, key=title)
            for i in range(len(ds)):
                for j in range(i + 1, len(ds)):
                    pairs[(ds[i], ds[j])].append(u)
        ins["Domain pairs (independent units evidencing both)"] = [
            f"{title(a)} × {title(b)}: {len(us)} — {', '.join(sorted(title(u).split(' – ')[0] for u in us))}"
            for (a, b), us in sorted(pairs.items(), key=lambda kv: (-len(kv[1]), title(kv[0][0]), title(kv[0][1])))]

        cross = []
        for p in sorted(self.competencies - self.domains, key=title):
            if nodes[p].fm.get("rank") == "branch" or nodes[p].fm.get("kind", "practice") != "practice":
                continue
            tops = {self.sector_top[s] for e in self.competency_support[p] for s in self.ev_sectors.get(e, [])}
            if len(tops) >= 2:
                cross.append(f"{title(p)}: {', '.join(sorted(title(t) for t in tops))}")
        ins["Practices evidenced in two or more top-level sectors"] = cross

        table = defaultdict(lambda: {"competencies": 0, "aware": 0, "practitioner": 0, "advanced": 0, "expert": 0,
                                     "unsupported": 0})
        for p, level, _units, ok, _rec in self.claim_rows:
            for d in {self.primary_domain.get(p)}:
                row = table[title(d) if d else "(no domain)"]
                row["competencies"] += 1
                if level in LEVELS:
                    row[level] += 1
                if not ok:
                    row["unsupported"] += 1
        ins["Claims by domain"] = [
            f"{d}: {v['competencies']} competencies; claimed L1 Aware {v['aware']}, L2 Practitioner {v['practitioner']}, "
            f"L3 Advanced {v['advanced']}, L4 Expert {v['expert']}; unsupported {v['unsupported']}"
            for d, v in sorted(table.items())]
        self.r.insights = ins


# --------------------------------------------------------------------------- output

def render_markdown(r: Result, today: dt.date) -> str:
    s = r.stats
    out = [f"# Competency graph check ({today.isoformat()})", "",
           f"Specification v{SPEC_VERSION}. {s.get('competencies', 0)} competencies, {s.get('sectors', 0)} sectors, "
           f"{s.get('evidence', 0)} evidence notes ({s.get('units', 0)} independent units), "
           f"{s.get('edges', 0)} links.", "",
           f"**{len(r.errors)} errors · {len(r.warnings)} warnings**", ""]
    for heading, items in (("Errors", r.errors), ("Warnings", r.warnings)):
        out.append(f"## {heading}")
        out.extend([f.line() for f in sorted(items, key=lambda f: (f.path, f.code))] or ["None."])
        out.append("")
    out.append("## Insights")
    for heading, lines in r.insights.items():
        out.append(f"### {heading}")
        out.extend([f"- {line}" for line in lines] or ["None."])
        out.append("")
    return "\n".join(out)


def to_json(r: Result) -> dict:
    def clean(v):
        if isinstance(v, (dt.date, dt.datetime)):
            return v.isoformat()
        if isinstance(v, list):
            return [clean(x) for x in v]
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        return v
    return {
        "specVersion": SPEC_VERSION,
        "nodes": [{"id": n.path, "name": n.name, "type": n.type, "fields": clean(n.fm)} for n in r.nodes.values()],
        "edges": [{"source": a, "target": b, "field": f} for a, b, f in r.edges],
        "errors": [f.__dict__ for f in r.errors],
        "warnings": [f.__dict__ for f in r.warnings],
    }


def check_folders(r: Result, cfg) -> None:
    """Warn about competency/sector notes outside the folders the config file names for them."""
    for p, n in r.nodes.items():
        key = {"competency": "competencies", "sector": "sectors"}.get(n.type)
        if not key:
            continue
        want = os.path.relpath(cfg.folders[key], cfg.vault).replace(os.sep, "/")
        here = os.path.dirname(p)
        if here != want and not here.startswith(want + "/"):      # subfolders (e.g. Competencies/RICS/) are fine
            r.warnings.append(Finding("folder", p, f"{n.type} note outside the configured `{key}` folder ({want}/)"))


def check_sources(r: Result, cfg) -> None:
    """Warn about the owner's records (config `sources`) that aren't where the config says: a moved resume folder
    means the next collection pass reads nothing."""
    for e in getattr(cfg, "sources", None) or []:
        if e["use"] != "ignore" and not os.path.exists(e["path"]):
            r.warnings.append(Finding("source", cfg.rel(e["path"]),
                                      f"source named in the config ({e['use']}{', ' + e['kind'] if e['kind'] else ''}) "
                                      "does not exist; fix its path in competency-graph.yaml"))


REQUIREMENT_COLUMNS = ["framework", "pathway", "group", "name", "required"]
REQUIRED_VALUES = {"L1", "L2", "L3", "L4", "L2 or L3", "choice"}


def check_requirements(r: Result, cfg) -> None:
    """Every framework is stated on this graph's L1-L4 scale (spec §3.8): the requirements file's `required` must be
    L1-L4, "L2 or L3", or "choice" (the candidate picks it; minimum L2). A framework's own levels (Bloom, belts, exam
    levels) are mapped onto L1-L4 first, with the reason recorded in the profile's decision log."""
    import csv
    rel = cfg.rel(cfg.requirements)
    if not os.path.isfile(cfg.requirements):
        r.errors.append(Finding("requirements", rel, "requirements file named in the config does not exist"))
        return
    with open(cfg.requirements, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    cols = set(rows[0].keys()) if rows else set()
    missing = [c for c in REQUIREMENT_COLUMNS if c not in cols]
    if missing:
        r.errors.append(Finding("requirements", rel, f"missing column(s) {missing}"))
        return
    bad = {}
    for i, row in enumerate(rows, start=2):
        v = (row.get("required") or "").strip()
        if v not in REQUIRED_VALUES:
            bad.setdefault((row.get("framework") or "?", v), []).append(i)
    for (fw, v), lines in sorted(bad.items()):
        r.errors.append(Finding("requirements", rel,
                                f"{fw}: `required` {v!r} is not on the L1-L4 scale (lines {', '.join(map(str, lines[:6]))}"
                                f"{'…' if len(lines) > 6 else ''}); use L1-L4, \"L2 or L3\" or \"choice\""))


def check_library_and_specs(r: Result, cfg) -> None:
    """The owner's own frameworks (`ownFrameworks`) must load beside the skill's library, and the job specs file
    (`jobSpecs`, when it exists) must name only framework competencies, on L1-L4, each in one section."""
    import frameworks as fw
    import job_specs as js
    try:
        lib = fw.library_for(cfg)
    except (fw.FrameworkError, OSError, KeyError) as exc:
        r.errors.append(Finding("frameworks", cfg.rel(cfg.own_frameworks or fw.LIBRARY), str(exc)))
        return
    path = cfg.job_specs_file
    if not os.path.isfile(path):
        if getattr(cfg, "job_specs", None):
            r.errors.append(Finding("jobspecs", cfg.rel(path), "job specs file named in the config does not exist"))
        return
    try:
        specs = js.load_specs(path)
    except js.SpecError as exc:
        r.errors.append(Finding("jobspecs", cfg.rel(path), str(exc)))
        return
    for p in js.validate(specs, lib):
        r.errors.append(Finding("jobspecs", cfg.rel(path), p))


def check(vault: str, profile: str | None = None, today: dt.date | None = None, cfg=None) -> Result:
    settings = load_settings(profile)
    result = Analyzer(vault, settings, today or dt.date.today()).run()
    if cfg is not None and cfg.path:
        check_folders(result, cfg)
        check_sources(result, cfg)
        if getattr(cfg, "requirements", None):
            check_requirements(result, cfg)
        check_library_and_specs(result, cfg)
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    kc.add_arguments(ap, "vault root to scan (default: from the config file)")
    ap.add_argument("--profile", help="profile note with kg* settings in its front matter")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    ap.add_argument("--report", nargs="?", const=AUTO,
                    help="write the markdown report here instead of stdout (no name: dated file in `reports`)")
    ap.add_argument("--json", nargs="?", const=AUTO,
                    help="also write a JSON export of the graph (no name: dated file in `reports`)")
    args = ap.parse_args(argv)
    if args.vault and not os.path.isdir(args.vault):
        print(f"not a directory: {args.vault}", file=sys.stderr)
        return 2
    cfg = kc.from_args(args)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    if args.report is AUTO:
        args.report = cfg.new_file("reports", "Graph_Check.md", today=today, mkdir=True)
    if args.json is AUTO:
        args.json = cfg.new_file("reports", "Graph.json", today=today, mkdir=True)
    result = check(args.vault, args.profile, today, cfg)
    report = render_markdown(result, today)
    if args.report:
        print(f"report -> {args.report}", file=sys.stderr)
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
    else:
        print(report)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(to_json(result), fh, indent=2, ensure_ascii=False)
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
