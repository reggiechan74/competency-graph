#!/usr/bin/env python3
"""Read the competency-graph config file and say where every kind of file belongs.

The config file is `competency-graph.yaml` at the vault root (the folder links resolve within). A vault
set up before the skill's rename may still have `knowledge-graph.yaml`; it is read the same way.
Every path in it is relative to that folder, or absolute. Only `graphRoot` and `profile` are
needed; each folder defaults to <graphRoot>/<Name>:

    kgConfigVersion: 1
    graphRoot: Competency_Graph
    profile: Competency_Graph/Profile_Priya_Nair.md
    folders:
      competencies:   Competency_Graph/Competencies      # competency notes (subfolders allowed)
      sectors:  Competency_Graph/Sectors     # sector notes
      evidence: Competency_Graph/Evidence    # new evidence notes (Projects/, Credentials/, ...)
      working:  Competency_Graph/Working     # placement proposals, pass tests, rating worksheets
      reports:  Competency_Graph/Working     # checker reports and JSON exports
      outputs:  Competency_Graph/Outputs     # things made for a reader: requirement tables, evidence packs
    datedFilenames: true                    # prefix files Claude names itself with YYYY-MM-DD_
    requirements: Competency_Graph/Competencies/Framework_Requirements.csv   # optional; levels L1-L4 (checked)
    descriptions: Competency_Graph/Competencies/Framework_Descriptions.csv   # optional; default beside requirements
    jobSpecs: Competency_Graph/Competencies/Job_Specs.yaml   # optional; this default when absent (job_specs.py)
    ownFrameworks: Competency_Graph/Frameworks   # optional; the owner's own frameworks, in the library's format
    dashboard:                              # optional; what dashboard_build.py writes into the page
      title: Priya's competency portfolio
      sectors: NAICS Canada                 # names the industry classification ("each NAICS Canada sector")
      disclosure: on-request                # public or on-request; never confidential
    assessors:                              # optional; the people who rate the owner's competencies (assessors.py)
      dana-okafor: {name: Dana Okafor, role: APC counsellor}   # id: {name, role?}; a rating records the name
    sources:                                # the owner's own records, where they keep them (optional)
      - path: Career/Resume                 # a folder or a file
        kind: resume-folder                 # cv, resume-folder, job-history, linkedin, github, credentials, ...
        use: collect                        # evidence (files become evidence notes in place), collect, or ignore
        note: master resume and tailored CVs

    kg_config.py where                                          where a NEW graph goes by default, from this folder
    kg_config.py [--config F | --vault V] show                  where everything goes
    kg_config.py [--config F | --vault V] path <kind> <name>    full path for a new file (kind = a folder key)
                                          [--no-date] [--mkdir]
    kg_config.py [--vault V] init [--graph-root R] --profile P [--<folder> DIR ...] [--requirements F]
                                [--descriptions F] [--job-specs F] [--own-frameworks DIR]
                                [--source PATH[=USE[:KIND]] ...] [--no-dated] [--force]

Where a new graph goes by default (`where`; `init` with no --vault and no --graph-root uses it):
  inside a git repository   the repository root is the vault, and the graph is <root>/Competency_Graph;
  anywhere else             the vault is Competency_Graph in the user's Documents folder, and the graph is that
                            folder itself (graphRoot "."), so one folder holds everything.
An owner may put either anywhere; these are only what is offered first.

Lookup order: --config, else <--vault>/competency-graph.yaml, else the nearest competency-graph.yaml
in the current folder or a parent (in each folder, the old name knowledge-graph.yaml counts too), else the one in
Documents/Competency_Graph, so a graph kept there is found from any folder. Command-line --vault/--profile override
the file.
Exit status: 0 = ok, 2 = no config / bad config / usage problem.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from dataclasses import dataclass, field

import yaml

CONFIG_NAME = "competency-graph.yaml"
LEGACY_CONFIG_NAMES = ("knowledge-graph.yaml",)   # the name before the skill was renamed (2026-11-13)
CONFIG_VERSION = 1
DEFAULT_GRAPH_ROOT = "Competency_Graph"            # a new graph's folder
LEGACY_GRAPH_ROOTS = ("Knowledge_Graph",)          # the default before 2026-11-15; still read where it is the one there
FOLDERS = {  # key -> (default subfolder of graphRoot, what goes there)
    "competencies": ("Competencies", "competency notes"),
    "sectors": ("Sectors", "sector notes"),
    "evidence": ("Evidence", "new evidence notes (Projects/, Credentials/, Publications/, Engagements/)"),
    "working": ("Working", "placement proposals, pass-test notes, rating worksheets"),
    "reports": ("Working", "checker reports and JSON exports"),
    "outputs": ("Outputs", "things made for a reader: requirement tables, evidence packs, CV material"),
}
GRAPH_FOLDERS = ("competencies", "sectors", "evidence")  # must sit inside the vault, or links can't resolve
KNOWN_KEYS = {"kgConfigVersion", "graphRoot", "profile", "folders", "datedFilenames", "requirements", "descriptions",
              "frameworks", "sources", "jobSpecs", "ownFrameworks", "dashboard", "assessors"}
ASSESSOR_KEYS = {"name", "role"}
ASSESSOR_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
ASSESSOR_TEXT = 80     # the longest name or role
DASHBOARD_KEYS = {"title", "sectors", "disclosure"}
DASHBOARD_DISCLOSURES = ("public", "on-request")   # a dashboard is read by others: never confidential (SKILL.md rule 7)
SOURCE_USES = ("evidence", "collect", "ignore")   # becomes evidence notes in place / read for competencies only / skipped
SOURCE_KEYS = {"path", "kind", "use", "note"}


class ConfigError(Exception):
    pass


@dataclass
class Config:
    vault: str                      # absolute vault root
    profile: str | None             # absolute path, or None
    graph_root: str | None          # absolute path, or None (no config file)
    folders: dict = field(default_factory=dict)   # key -> absolute path
    dated: bool = True
    path: str | None = None         # the config file, or None
    requirements: str | None = None  # framework requirements CSV (absolute), or None
    frameworks: dict = field(default_factory=dict)  # selected library frameworks: id -> {pathways?, notes?}
    descriptions: str | None = None  # framework descriptions CSV (absolute), or None (beside requirements)
    sources: list = field(default_factory=list)     # [{path (absolute), kind, use, note}] the owner's records
    job_specs: str | None = None    # job specs YAML (absolute), or None (the default beside the competencies)
    own_frameworks: str | None = None   # folder of the owner's own frameworks (absolute), or None
    dashboard: dict = field(default_factory=dict)   # {title?, sectors?, disclosure?} for dashboard_build.py
    assessors: dict = field(default_factory=dict)   # id -> {name, role}: who rates the owner's competencies

    @property
    def job_specs_file(self) -> str:
        """The job specs file: the config's `jobSpecs`, else Job_Specs.yaml in the competencies folder."""
        return self.job_specs or os.path.join(self.folders["competencies"], "Job_Specs.yaml")

    @property
    def descriptions_file(self) -> str | None:
        """The descriptions CSV: the config's `descriptions`, else beside the requirements file."""
        return self.descriptions or (default_descriptions(self.requirements) if self.requirements else None)

    def rel(self, p: str) -> str:
        r = os.path.relpath(p, self.vault)
        return p if r.startswith("..") else r.replace(os.sep, "/")

    def new_file(self, kind: str, name: str, dated: bool | None = None,
                 today: dt.date | None = None, mkdir: bool = False) -> str:
        """Full path for a new file of `kind` (a folder key). Adds the date prefix unless told not to."""
        if kind not in self.folders:
            raise ConfigError(f"unknown folder {kind!r}; one of: {', '.join(FOLDERS)}")
        folder = self.folders[kind]
        if (self.dated if dated is None else dated):
            stamp = (today or dt.date.today()).isoformat()
            if not name.startswith(stamp):
                name = f"{stamp}_{name}"
        path = os.path.join(folder, name)
        if mkdir:
            os.makedirs(os.path.dirname(path), exist_ok=True)   # includes any subfolder in `name`
        return path


def default_descriptions(requirements: str) -> str:
    """The descriptions file beside a requirements file: Framework_Requirements.csv -> Framework_Descriptions.csv."""
    d, base = os.path.split(requirements)
    stem, ext = os.path.splitext(base)
    if "Requirements" in stem:
        return os.path.join(d, stem.replace("Requirements", "Descriptions") + ext)
    if "requirements" in stem:
        return os.path.join(d, stem.replace("requirements", "descriptions") + ext)
    return os.path.join(d, stem + "_descriptions" + (ext or ".csv"))


def config_in(folder: str) -> str | None:
    """The config file in `folder`: competency-graph.yaml, else the legacy knowledge-graph.yaml."""
    for name in (CONFIG_NAME,) + LEGACY_CONFIG_NAMES:
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            return p
    return None


def find_config(start: str) -> str | None:
    """The nearest config in `start` or a parent; else the one in Documents/Competency_Graph, where a graph outside a
    repository is kept by default, so it is found from any folder."""
    d = os.path.abspath(start)
    while True:
        p = config_in(d)
        if p:
            return p
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    home = os.path.join(documents_dir(), DEFAULT_GRAPH_ROOT)
    return config_in(home) if os.path.isdir(home) else None


def git_root(start: str) -> str | None:
    """The root of the git repository `start` is in (the nearest folder holding `.git`: a repository's own folder or, in a
    worktree or submodule, a file), or None."""
    d = os.path.abspath(start)
    while True:
        g = os.path.join(d, ".git")
        # a repository's own folder holds HEAD; a stray empty `.git` folder is not one
        if os.path.isfile(g) or os.path.isfile(os.path.join(g, "HEAD")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def documents_dir() -> str:
    """The user's Documents folder ("My Documents"): XDG_DOCUMENTS_DIR where a Linux desktop sets it, else ~/Documents.
    It need not exist yet."""
    home = os.path.expanduser("~")
    xdg = os.environ.get("XDG_DOCUMENTS_DIR")
    if not xdg:
        try:
            with open(os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config"), "user-dirs.dirs"),
                      encoding="utf-8") as fh:
                m = re.search(r'^XDG_DOCUMENTS_DIR="?([^"\n]+)"?', fh.read(), re.M)
            xdg = m.group(1).replace("$HOME", home) if m else None
        except OSError:
            xdg = None
    # a desktop with no Documents folder points XDG_DOCUMENTS_DIR at the home folder itself: use ~/Documents then
    if xdg and os.path.isabs(xdg) and os.path.normpath(xdg) != os.path.normpath(home):
        return os.path.normpath(xdg)
    return os.path.join(home, "Documents")


def default_location(start: str | None = None) -> dict:
    """Where a new graph goes when the owner names no place: {vault, graph_root (relative to the vault), graph, in_repo}.
    In a git repository the vault is the repository root and the graph is Competency_Graph at that root; anywhere else
    the vault is Documents/Competency_Graph and the graph is that folder itself, so one folder holds everything."""
    repo = git_root(start or os.getcwd())
    # a home folder kept in git (dotfiles) is not a project: the graph goes in Documents, not loose in the home folder
    if repo and os.path.normpath(repo) != os.path.normpath(os.path.expanduser("~")):
        return {"vault": repo, "graph_root": DEFAULT_GRAPH_ROOT, "graph": os.path.join(repo, DEFAULT_GRAPH_ROOT), "in_repo": True}
    vault = os.path.join(documents_dir(), DEFAULT_GRAPH_ROOT)
    return {"vault": vault, "graph_root": ".", "graph": vault, "in_repo": False}


def default_graph_folder(vault: str) -> str:
    """The graph folder of a vault with no config file: <vault>/Competency_Graph, or an older graph's
    <vault>/Knowledge_Graph where that is the one there."""
    new = os.path.join(vault, DEFAULT_GRAPH_ROOT)
    if not os.path.isdir(new):
        for name in LEGACY_GRAPH_ROOTS:
            if os.path.isdir(os.path.join(vault, name)):
                return os.path.join(vault, name)
    return new


def _resolve(base: str, value, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key}: expected a path, got {value!r}")
    return os.path.normpath(os.path.join(base, os.path.expanduser(value.strip())))


def _inside(path: str, root: str) -> bool:
    return os.path.commonpath([os.path.abspath(path), os.path.abspath(root)]) == os.path.abspath(root)


def check_assessors(raw) -> dict:
    """{id: {name, role}} from the config's `assessors:` (or a list saved on the dashboard, once keyed by id): every id
    a lowercase slug, every name given and different from the others, a role optional."""
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise ConfigError("assessors must map an id to its assessor (e.g. `dana-okafor: {name: Dana Okafor}`)")
    out, seen = {}, {}
    for aid, a in raw.items():
        if not isinstance(aid, str) or not ASSESSOR_ID.match(aid):
            raise ConfigError(f"assessors: id {aid!r} must be lowercase letters and digits joined by hyphens")
        if not isinstance(a, dict) or set(a) - ASSESSOR_KEYS:
            raise ConfigError(f"assessors.{aid} takes only `name` and `role`")
        name, role = a.get("name"), a.get("role", "")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"assessors.{aid} needs a `name`")
        if role is None:
            role = ""
        if not isinstance(role, str):
            raise ConfigError(f"assessors.{aid}.role must be text")
        name, role = " ".join(name.split()), " ".join(role.split())
        if len(name) > ASSESSOR_TEXT or len(role) > ASSESSOR_TEXT:
            raise ConfigError(f"assessors.{aid}: a name or role is at most {ASSESSOR_TEXT} characters")
        if name.casefold() in seen:
            raise ConfigError(f"assessors.{aid} and assessors.{seen[name.casefold()]} have the same name ({name})")
        seen[name.casefold()] = aid
        out[aid] = {"name": name, "role": role}
    return out


def read_config(path: str) -> Config:
    with open(path, encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"{path}: not valid YAML ({exc})") from None
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: expected key: value pairs")
    unknown = set(data) - KNOWN_KEYS
    if unknown:
        raise ConfigError(f"{path}: unknown key(s) {sorted(unknown)}; allowed: {sorted(KNOWN_KEYS)}")
    version = data.get("kgConfigVersion", CONFIG_VERSION)
    if version != CONFIG_VERSION:
        raise ConfigError(f"{path}: kgConfigVersion {version!r} not supported (this script reads {CONFIG_VERSION})")
    vault = os.path.dirname(os.path.abspath(path))
    if "graphRoot" not in data:
        raise ConfigError(f"{path}: graphRoot is required")
    graph_root = _resolve(vault, data["graphRoot"], "graphRoot")
    profile = _resolve(vault, data["profile"], "profile") if data.get("profile") else None
    given = data.get("folders") or {}
    if not isinstance(given, dict):
        raise ConfigError(f"{path}: folders must be key: path pairs")
    if "skills" in given:                      # spec v0.3 name for the competencies folder
        if "competencies" in given:
            raise ConfigError(f"{path}: give `competencies` or the old `skills`, not both")
        given = {("competencies" if k == "skills" else k): v for k, v in given.items()}
    bad = set(given) - set(FOLDERS)
    if bad:
        raise ConfigError(f"{path}: unknown folder key(s) {sorted(bad)}; allowed: {list(FOLDERS)}")
    folders = {k: (_resolve(vault, given[k], f"folders.{k}") if k in given else os.path.join(graph_root, sub))
               for k, (sub, _) in FOLDERS.items()}
    for k in ("graphRoot",) + GRAPH_FOLDERS:
        p = graph_root if k == "graphRoot" else folders[k]
        if not _inside(p, vault):
            raise ConfigError(f"{path}: {k} ({p}) is outside the vault; links resolve only inside {vault}")
    if profile and not _inside(profile, vault):
        raise ConfigError(f"{path}: profile ({profile}) is outside the vault")
    dated = data.get("datedFilenames", True)
    if not isinstance(dated, bool):
        raise ConfigError(f"{path}: datedFilenames must be true or false")
    req = _resolve(vault, data["requirements"], "requirements") if data.get("requirements") else None
    if req and not _inside(req, vault):
        raise ConfigError(f"{path}: requirements ({req}) is outside the vault")
    fws = data.get("frameworks") or {}
    if not isinstance(fws, dict):
        raise ConfigError(f"{path}: frameworks must map a library id to its settings (e.g. `cfa-cbok: {{}}`)")
    for fid, spec in fws.items():
        spec = spec or {}
        if not isinstance(spec, dict) or set(spec) - {"pathways", "notes"}:
            raise ConfigError(f"{path}: frameworks.{fid} takes only `pathways` (a list) and `notes` (pathway: note)")
        if "pathways" in spec and not isinstance(spec["pathways"], list):
            raise ConfigError(f"{path}: frameworks.{fid}.pathways must be a list")
        if "notes" in spec and not isinstance(spec["notes"], dict):
            raise ConfigError(f"{path}: frameworks.{fid}.notes must map a pathway to a note")
    desc = _resolve(vault, data["descriptions"], "descriptions") if data.get("descriptions") else None
    if desc and not _inside(desc, vault):
        raise ConfigError(f"{path}: descriptions ({desc}) is outside the vault")
    srcs = []
    given_src = data.get("sources") or []
    if not isinstance(given_src, list):
        raise ConfigError(f"{path}: sources must be a list of {{path, kind, use, note}} entries")
    for i, e in enumerate(given_src):
        if isinstance(e, str):
            e = {"path": e}
        if not isinstance(e, dict) or set(e) - SOURCE_KEYS or not e.get("path"):
            raise ConfigError(f"{path}: sources[{i}] needs a `path` and may have only {sorted(SOURCE_KEYS)}")
        use = str(e.get("use") or "collect")
        if use not in SOURCE_USES:
            raise ConfigError(f"{path}: sources[{i}].use {use!r} is not one of {', '.join(SOURCE_USES)}")
        sp = _resolve(vault, e["path"], f"sources[{i}].path")
        # a file that becomes an evidence note must be inside the vault, or links to it can't resolve
        if use == "evidence" and not _inside(sp, vault):
            raise ConfigError(f"{path}: sources[{i}] ({sp}) is outside the vault; `use: evidence` files must be inside it")
        srcs.append({"path": sp, "kind": str(e.get("kind") or ""), "use": use, "note": str(e.get("note") or "")})
    js = _resolve(vault, data["jobSpecs"], "jobSpecs") if data.get("jobSpecs") else None
    if js and not _inside(js, vault):
        raise ConfigError(f"{path}: jobSpecs ({js}) is outside the vault")
    own = _resolve(vault, data["ownFrameworks"], "ownFrameworks") if data.get("ownFrameworks") else None
    if own and not _inside(own, vault):
        raise ConfigError(f"{path}: ownFrameworks ({own}) is outside the vault")
    dash = data.get("dashboard") or {}
    if not isinstance(dash, dict) or set(dash) - DASHBOARD_KEYS:
        raise ConfigError(f"{path}: dashboard takes only {sorted(DASHBOARD_KEYS)}")
    for k in ("title", "sectors"):
        if k in dash and not isinstance(dash[k], str):
            raise ConfigError(f"{path}: dashboard.{k} must be text")
    if "disclosure" in dash and dash["disclosure"] not in DASHBOARD_DISCLOSURES:
        raise ConfigError(f"{path}: dashboard.disclosure must be one of {', '.join(DASHBOARD_DISCLOSURES)}; "
                          "a dashboard is never built from confidential evidence")
    try:
        assessors = check_assessors(data.get("assessors"))
    except ConfigError as exc:
        raise ConfigError(f"{path}: {exc}") from None
    return Config(vault=vault, profile=profile, graph_root=graph_root, folders=folders, dated=dated, path=path,
                  requirements=req, frameworks=fws, descriptions=desc, sources=srcs, job_specs=js,
                  own_frameworks=own, dashboard=dict(dash), assessors=assessors)


def load(config: str | None = None, vault: str | None = None, profile: str | None = None,
         start: str | None = None, required: bool = False) -> Config:
    """Resolve settings. Explicit vault/profile win over the file.

    With no config file, folders default to <vault>/Competency_Graph/<Name> (an older graph's
    <vault>/Knowledge_Graph where that is the folder there) only when `vault` is given;
    if neither a file nor a vault is found, raise ConfigError when `required`, else use the current folder.
    """
    path = config
    if path and not os.path.isfile(path):
        raise ConfigError(f"config file not found: {path}")
    if not path and vault:
        path = config_in(vault)
    if not path and not vault:
        path = find_config(start or os.getcwd())
    if path:
        cfg = read_config(path)
        if vault and os.path.abspath(vault) != cfg.vault:
            raise ConfigError(f"--vault {vault} does not match the config's folder {cfg.vault}")
    else:
        if required and not vault:
            raise ConfigError(f"no {CONFIG_NAME} found in {start or os.getcwd()} or its parents; "
                              f"pass --vault (and --profile), or create one with kg_config.py init")
        root = os.path.abspath(vault or ".")
        gr = default_graph_folder(root)
        cfg = Config(vault=root, profile=None, graph_root=None,
                     folders={k: os.path.join(gr, sub) for k, (sub, _) in FOLDERS.items()})
    if profile:
        cfg.profile = os.path.abspath(profile)
    return cfg


# ------------------------------------------------------------------ helpers for the other scripts

def add_arguments(ap: argparse.ArgumentParser, vault_help: str = "vault root (default: from the config file)"):
    ap.add_argument("--config", help=f"config file (default: nearest {CONFIG_NAME})")
    ap.add_argument("--vault", help=vault_help)


def from_args(args) -> Config:
    """Resolve --config/--vault/--profile for a script; exits 2 with a message on a config problem."""
    try:
        cfg = load(getattr(args, "config", None), getattr(args, "vault", None),
                   getattr(args, "profile", None), required=True)
    except ConfigError as exc:
        print(f"config: {exc}", file=sys.stderr)
        sys.exit(2)
    if cfg.profile and not os.path.isfile(cfg.profile):
        print(f"config: profile not found: {cfg.profile}", file=sys.stderr)
        sys.exit(2)
    args.vault, args.profile = cfg.vault, cfg.profile
    return cfg


# ------------------------------------------------------------------ CLI

TEMPLATE = """\
# Where the competency-graph skill reads and writes files.
# Every path is relative to this file's folder (the vault root), or absolute.
# Graph notes (competencies, sectors, evidence) must stay inside the vault; working,
# reports and outputs may point anywhere. Delete a folder line to use its default.
kgConfigVersion: 1
graphRoot: {graph_root}
profile: {profile}
folders:
{folders}
datedFilenames: {dated}    # prefix files Claude names itself with YYYY-MM-DD_
{extra}"""


def parse_source(text: str) -> dict:
    """--source PATH[=USE[:KIND]]: e.g. Career/Resume=collect:resume-folder, Jobs=evidence:job-history."""
    path, _, rest = str(text).partition("=")
    use, _, kind = rest.partition(":")
    out = {"path": path.strip()}
    if use.strip():
        out["use"] = use.strip()
    if kind.strip():
        out["kind"] = kind.strip()
    return out


def render(graph_root: str, profile: str, overrides: dict, requirements: str | None = None,
           descriptions: str | None = None, sources: list | None = None, dated: bool = True,
           job_specs: str | None = None, own_frameworks: str | None = None) -> str:
    gr = graph_root.rstrip("/") or "."
    here = gr in (".", "./")          # the graph is the vault itself (a graph kept in Documents/Competency_Graph)
    lines = []
    for k, (sub, what) in FOLDERS.items():
        val = overrides.get(k) or (sub if here else f"{gr}/{sub}")
        lines.append(f"  # {what}\n  {k}: {val}")
    extra = []
    if requirements:
        extra.append(f"requirements: {requirements}    # framework requirements CSV (frameworks.py build writes it)")
    if descriptions:
        extra.append(f"descriptions: {descriptions}    # framework descriptions CSV (default: beside requirements)")
    if job_specs:
        extra.append(f"jobSpecs: {job_specs}    # job specs (job_specs.py build writes the dashboard's copy)")
    if own_frameworks:
        extra.append(f"ownFrameworks: {own_frameworks}    # the owner's own frameworks, in the library's format")
    if sources:
        extra.append("# the owner's own records: use = evidence (files become evidence notes in place, inside the vault),\n"
                     "# collect (read for candidate competencies only) or ignore\nsources:")
        for e in sources:
            extra.append(f"  - path: {e['path']}\n    use: {e.get('use', 'collect')}"
                         + (f"\n    kind: {e['kind']}" if e.get("kind") else ""))
    return TEMPLATE.format(graph_root="." if here else gr, profile=profile, folders="\n".join(lines),
                           dated="true" if dated else "false", extra="".join(x + "\n" for x in extra))


def show(cfg: Config) -> str:
    out = [f"config:  {cfg.path or '(none; defaults)'}", f"vault:   {cfg.vault}",
           f"graph:   {cfg.rel(cfg.graph_root) if cfg.graph_root else '-'}",
           f"profile: {cfg.rel(cfg.profile) if cfg.profile else '-'}"
           + ("" if not cfg.profile or os.path.isfile(cfg.profile) else "  (missing)"),
           f"dated filenames: {'yes' if cfg.dated else 'no'}", ""]
    for k, (_, what) in FOLDERS.items():
        p = cfg.folders[k]
        out.append(f"{k:<12} {cfg.rel(p):<40} {'' if os.path.isdir(p) else '(not created yet) '}{what}")
    if cfg.requirements:
        out.append(f"{'requirements':<12} {cfg.rel(cfg.requirements)}{'' if os.path.isfile(cfg.requirements) else '  (not built yet)'}")
        d = cfg.descriptions_file
        out.append(f"{'descriptions':<12} {cfg.rel(d)}{'' if os.path.isfile(d) else '  (not built yet)'}")
    j = cfg.job_specs_file
    out.append(f"{'job specs':<12} {cfg.rel(j)}{'' if os.path.isfile(j) else '  (none yet)'}")
    if cfg.own_frameworks:
        o = cfg.own_frameworks
        out.append(f"{'own frameworks':<12} {cfg.rel(o)}{'' if os.path.isfile(os.path.join(o, 'catalog.yaml')) else '  (MISSING catalog.yaml)'}")
    if cfg.assessors:
        out += ["", "assessors (who rates the owner's competencies):"]
        out += [f"  {aid:<20} {a['name']}" + (f"  ({a['role']})" if a["role"] else "") for aid, a in cfg.assessors.items()]
    if cfg.sources:
        out += ["", "sources (the owner's own records):"]
        for e in cfg.sources:
            here = os.path.exists(e["path"])
            out.append(f"  {e['use']:<8} {cfg.rel(e['path'])}{'' if here else '  (MISSING)'}"
                       + (f"  [{e['kind']}]" if e["kind"] else "") + (f"  {e['note']}" if e["note"] else ""))
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    add_arguments(ap)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    sub.add_parser("where", help="where a new graph goes by default, from this folder")
    p = sub.add_parser("path")
    p.add_argument("kind", choices=list(FOLDERS))
    p.add_argument("name")
    p.add_argument("--no-date", action="store_true", help="keep the name exactly (e.g. one the owner gave)")
    p.add_argument("--mkdir", action="store_true", help="create the folder if missing")
    p.add_argument("--today")
    i = sub.add_parser("init")
    i.add_argument("--graph-root", help=f"the graph's folder, relative to the vault (default: {DEFAULT_GRAPH_ROOT} at a "
                                        "repository's root; with no --vault outside a repository, the vault itself)")
    i.add_argument("--profile", required=True)
    for k in FOLDERS:
        i.add_argument(f"--{k}", help=f"override folders.{k}")
    i.add_argument("--requirements", help="framework requirements CSV (inside the vault)")
    i.add_argument("--descriptions", help="framework descriptions CSV (default: beside the requirements file)")
    i.add_argument("--job-specs", help="job specs YAML (default: Job_Specs.yaml in the competencies folder)")
    i.add_argument("--own-frameworks", help="folder of the owner's own frameworks (catalog.yaml and its files)")
    i.add_argument("--source", action="append", default=[], metavar="PATH[=USE[:KIND]]",
                   help="one of the owner's records (repeat): USE is evidence, collect (default) or ignore")
    i.add_argument("--no-dated", action="store_true", help="don't prefix Claude-named files with the date")
    i.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "where":
        d = default_location()
        print(f"vault:  {d['vault']}  ({'the git repository this folder is in' if d['in_repo'] else 'not in a git repository: Documents'})")
        print(f"graph:  {d['graph']}" + ("" if d["in_repo"] else "  (the vault itself)"))
        print(f"config: {os.path.join(d['vault'], CONFIG_NAME)}")
        found = config_in(d["vault"])
        if found:
            print(f"note:   {found} already configures this vault")
        print(f"init:   kg_config.py init --profile {'' if not d['in_repo'] else DEFAULT_GRAPH_ROOT + '/'}Profile_<Owner>.md")
        return 0
    if args.cmd == "init":
        # no --vault: the default place for a new graph (a repository's root, else Documents/Competency_Graph)
        d = default_location() if not (args.vault or args.config) else None
        root = os.path.abspath(args.vault) if args.vault else (d["vault"] if d else os.path.abspath("."))
        if not args.graph_root:
            args.graph_root = d["graph_root"] if d else DEFAULT_GRAPH_ROOT
        os.makedirs(root, exist_ok=True)
        target = args.config or os.path.join(root, CONFIG_NAME)
        if os.path.exists(target) and not args.force:
            print(f"{target} already exists (use --force to overwrite)", file=sys.stderr)
            return 2
        legacy = None if args.config else config_in(root)
        if legacy and legacy != target:
            print(f"{legacy} already configures this vault; rename it to {CONFIG_NAME} or edit it", file=sys.stderr)
            return 2
        text = render(args.graph_root, args.profile, {k: getattr(args, k) for k in FOLDERS},
                      requirements=args.requirements, descriptions=args.descriptions,
                      sources=[parse_source(x) for x in args.source], dated=not args.no_dated,
                      job_specs=args.job_specs, own_frameworks=args.own_frameworks)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(text)
        try:
            read_config(target)
        except ConfigError as exc:
            os.remove(target)
            print(f"config: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {target}")
        return 0
    try:
        cfg = load(args.config, args.vault, required=True)
        if args.cmd == "show":
            print(show(cfg))
        else:
            today = dt.date.fromisoformat(args.today) if args.today else None
            print(cfg.new_file(args.kind, args.name, dated=False if args.no_date else None,
                               today=today, mkdir=args.mkdir))
    except ConfigError as exc:
        print(f"config: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
