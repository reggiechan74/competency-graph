#!/usr/bin/env python3
"""Build the whole claude.ai dashboard from the skill and the owner's files (Specification v0.5).

The dashboard is a display of the graph, never a record. Everything it shows can be rebuilt with this script from
the skill (the template, the framework library) and the owner's files (the notes, competency-graph.yaml, the
profile, their own frameworks and the job specs file). Changes made on the dashboard (claimed levels, job specs, a
framework selection) wait in its store until Claude writes them into those files (references/dashboard.md §4).

    dashboard_build.py [--config F | --vault V] [--profile P] [--out DIR] [--disclosure on-request|public] [--today D]
                       [--one-file]

Writes, by default to `<outputs>/Dashboard/`:

    index.html     the page: assets/dashboard/index.html with the owner's settings written in, its style and
    dashboard.css  scripts moved to files of their own (dashboard.css, dashboard-1.js ...), which index.html loads.
    dashboard-N.js The dashboard's store holds at most 256 KB a document, and the template in one piece is over
                   that; each part is well under it. --one-file keeps the page in one index.html, and stops if
                   that file would not fit the store (as the shipped template no longer does)
    data/          domains.json, competencies.json, timeline.json, sectors.json (summary_graph.py), descriptions.csv
                   (every framework competency, the owner's own frameworks included), jobspecs.csv (job_specs.py), assessors.csv (the config's `assessors:`) and,
                   when the owner has frameworks, requirements.csv (frameworks.py)
    manifest.json  the dashboard's title, the page's version (`pageVersion`), the page's files (`files`: what to
                   write as files/<name>), and each
                   dataset's id, file, title, description and format: what to upload

The owner's settings come from the config's `dashboard:` block (title; sectors, the industry classification's name;
disclosure) and the profile (kgStaleYears, kgPractitionerMinMonths, kgAdvancedMinYears, kgExpertMinYears,
kgExpertMinRecognition). The template marks each place with a comment, `<!-- kg:NAME -->default<!-- /kg:NAME -->` (in a script,
`/* kg:NAME */default/* /kg:NAME */`). With no frameworks, every `kg:fw` block is cut: the two framework tabs,
Configuration's frameworks card and what feeds them.

Disclosure: `on-request` (default) or `public`. Never confidential: everyone who can open the dashboard can read its
whole data files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_graph as cg  # noqa: E402
import frameworks as fw  # noqa: E402
import job_specs as js  # noqa: E402
import assessors as asr  # noqa: E402
import kg_config as kc  # noqa: E402
import summary_graph as sg  # noqa: E402

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "dashboard", "index.html")
VALUES = ("title", "sectors", "staleYears", "practitionerMonths", "advancedYears", "expertYears", "expertRecognition")
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
DATASETS = {   # id -> (title, description, fixed)
    "domains": ("Domains", "Each domain's claimed and supported level, units, organisations, years and recognition.", False),
    "competencies": ("Competencies", "Every competency with its claimed and supported level, evidence counts, fit and "
                     "framework references.", False),
    "timeline": ("Evidence timeline", "Each independent unit of evidence with its dates, kind, organisation and sector, "
                 "once per domain it evidences.", False),
    "sectors": ("Domains by sector", "Units of evidence for each domain in each top-level industry sector, with the sector's code.", False),
    "requirements": ("Framework requirements", "Every pathway of the framework library with its required levels on "
                     "L1-L4 and whether the owner selected it.", True),
    "descriptions": ("Competency descriptions", "Every framework competency with a description and what L1 to L4 mean "
                     "for it, the owner's own frameworks included, and the sub-group (specialisation) a pathway "
                     "lists it in.", True),
    "jobspecs": ("Job specs", "The owner's job specs: each competency with its section and required level.", False),
    "assessors": ("Assessors", "The people who rate the owner's competencies, from the config: an id, the name a "
                  "rating is recorded under, and a role.", False),
}


PART_LIMIT = 256 * 1024     # the dashboard's store holds at most 256 KB a document; each page file is one document
PART_WARN = 0.8             # say so when a file passes this share of the limit


class BuildError(Exception):
    pass


def words(n: float, unit: str = "") -> str:
    n = int(n) if float(n).is_integer() else n
    w = WORDS[n] if isinstance(n, int) and 0 <= n < len(WORDS) else str(n)
    if not unit:
        return w
    return f"{w} {unit}{'' if n == 1 else 's'}"


def page_values(cfg, settings: dict) -> dict:
    d = cfg.dashboard or {}
    return {
        "title": html.escape(d.get("title") or "Competency portfolio"),
        "sectors": html.escape(d.get("sectors") or "top-level industry"),
        "staleYears": str(int(settings["staleYears"])),
        "practitionerMonths": words(settings["practitionerMinMonths"], "month"),
        "advancedYears": words(settings["advancedMinYears"]),
        "expertYears": words(settings["expertMinYears"]),
        "expertRecognition": words(settings["expertMinRecognition"], "kind"),
    }


FW_LINE = re.compile(r"^[ \t]*<!-- kg:fw -->[ \t]*\n.*?^[ \t]*<!-- /kg:fw -->[ \t]*\n", re.S | re.M)
FW_INLINE = re.compile(r"<!-- kg:fw -->.*?<!-- /kg:fw -->", re.S)
FW_JS = re.compile(r"^[ \t]*/\* kg:fw \*/[ \t]*\n.*?^[ \t]*/\* /kg:fw \*/[ \t]*\n", re.S | re.M)


def render_page(template: str, values: dict, frameworks: bool) -> str:
    """The template with each kg:NAME value written in, and every kg:fw block cut when there are no frameworks."""
    out = template
    for name in VALUES:
        val = values[name]
        out, n1 = re.subn(rf"(<!-- kg:{name} -->).*?(<!-- /kg:{name} -->)", lambda m: m.group(1) + val + m.group(2), out, flags=re.S)
        out, n2 = re.subn(rf"(/\* kg:{name} \*/).*?(/\* /kg:{name} \*/)", lambda m: m.group(1) + val + m.group(2), out, flags=re.S)
        if not n1 + n2:
            raise BuildError(f"the template has no kg:{name} marker")
    opened = len(re.findall(r"<!-- kg:fw -->|/\* kg:fw \*/", out))
    closed = len(re.findall(r"<!-- /kg:fw -->|/\* /kg:fw \*/", out))
    if opened != closed:
        raise BuildError(f"the template's kg:fw markers don't pair up ({opened} open, {closed} closed)")
    if not frameworks:
        out = FW_JS.sub("", FW_LINE.sub("", out))
        out = FW_INLINE.sub("", out)
        if re.search(r"kg:fw", out):
            raise BuildError("a kg:fw block was left in the page")
    unknown = set(re.findall(r"(?:<!--|/\*) kg:([A-Za-z]+) (?:-->|\*/)", out)) - set(VALUES) - {"fw", "jobscore"}
    if unknown:
        raise BuildError(f"the template has unknown marker(s) {sorted(unknown)}")
    return out


STYLE = re.compile(r"<style>\n?(.*?)</style>", re.S)
VERSION = re.compile(r'<p class="sp-version" id="page-version">Version (\d+\.\d+\.\d+)</p>')
SCRIPT = re.compile(r"<script>\n?(.*?)</script>", re.S)


def page_version(page: str) -> str:
    """The page's own version, as the template shows it at the top right (DESIGN.md, *Page versions*)."""
    m = VERSION.search(page)
    if not m:
        raise BuildError("the template shows no page version (`<p class=\"sp-version\" id=\"page-version\">Version X.Y.Z</p>`)")
    return m.group(1)


def split_page(page: str) -> dict:
    """{file name: text}, index.html first: the page with its <style> moved to dashboard.css and each <script> to
    dashboard-N.js, loaded from index.html in the same order (the Dashboard type loads a `<link>` or `<script src>`
    that names one of the dashboard's own files). Each script stays a file of its own, as it was a scope of its own."""
    files: dict = {}

    def style(m):
        first = "dashboard.css" not in files
        files["dashboard.css"] = files.get("dashboard.css", "") + m.group(1)
        return '<link rel="stylesheet" href="dashboard.css">' if first else ""

    def script(m):
        name = f"dashboard-{sum(k.endswith('.js') for k in files) + 1}.js"
        files[name] = m.group(1)
        return f'<script src="{name}"></script>'

    html_text = SCRIPT.sub(script, STYLE.sub(style, page))
    return {"index.html": html_text, **files}


def join_page(files: dict) -> str:
    """The page in one piece again, each linked file back in its place (for a test or a tool that reads it whole)."""
    out = files["index.html"]
    for name, text in files.items():
        if name.endswith(".css"):
            out = out.replace(f'<link rel="stylesheet" href="{name}">', f"<style>\n{text}</style>")
        elif name.endswith(".js"):
            out = out.replace(f'<script src="{name}"></script>', f"<script>\n{text}</script>")
    return out


def write_page(out: str, page: str, one_file: bool) -> list[dict]:
    """Write the page's files; return [{name, bytes}] in loading order. Refuses a file over the store's limit."""
    files = {"index.html": page} if one_file else split_page(page)
    sizes = {name: len(text.encode("utf-8")) for name, text in files.items()}
    over = [f"{n} ({b // 1024} KB)" for n, b in sizes.items() if b > PART_LIMIT]
    if over:
        raise BuildError(f"page file over the dashboard's {PART_LIMIT // 1024} KB limit: {', '.join(over)}"
                         + ("; build without --one-file" if one_file else "; split the script in the template"))
    for name in os.listdir(out):                     # a part left over from a build with more of them
        if re.fullmatch(r"dashboard(-\d+)?\.(js|css)", name) and name not in files:
            os.remove(os.path.join(out, name))
    for name, text in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    return [{"name": n, "bytes": b} for n, b in sizes.items()]


def write_json(path: str, rows) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)


def write_csv(path: str, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def build(cfg, out: str, disclosure: str = "on-request", today: dt.date | None = None,
          template: str = TEMPLATE, one_file: bool = False) -> dict:
    """Write the page, the data files and the manifest to `out`; return the manifest."""
    if disclosure not in kc.DASHBOARD_DISCLOSURES:
        raise BuildError(f"disclosure {disclosure!r}: a dashboard is built from public or on-request evidence only")
    today = today or dt.date.today()
    settings = cg.load_settings(cfg.profile)
    lib = fw.library_for(cfg)
    sel = fw.selection(cfg.frameworks, lib)
    specs = js.load_specs(cfg.job_specs_file)
    problems = js.validate(specs, lib)
    if problems:
        raise BuildError("job specs: " + "; ".join(problems))
    s = sg.Summary(cfg.vault, cfg.profile, today, disclosure)
    data = os.path.join(out, "data")
    os.makedirs(data, exist_ok=True)
    files = {}
    for name, rows in (("domains", s.domains()), ("competencies", s.competencies()), ("timeline", s.timeline()),
                       ("sectors", s.sectors())):
        write_json(os.path.join(data, f"{name}.json"), rows)
        files[name] = (f"data/{name}.json", "json")
    has_fw = bool(cfg.frameworks)
    req_rows = None
    if has_fw:
        req_rows = fw.build_rows(lib, sel)
    elif cfg.requirements and os.path.isfile(cfg.requirements):     # a hand-made requirements file, kept as it is
        has_fw = True
        with open(cfg.requirements, encoding="utf-8", newline="") as fh:
            req_rows = list(csv.DictReader(fh))
    if req_rows is not None:
        cols = fw.COLUMNS if cfg.frameworks else list(req_rows[0].keys()) if req_rows else fw.COLUMNS
        write_csv(os.path.join(data, "requirements.csv"), req_rows, cols)
        files["requirements"] = ("data/requirements.csv", "csv")
    elif os.path.exists(os.path.join(data, "requirements.csv")):
        os.remove(os.path.join(data, "requirements.csv"))
    # each framework competency with the sub-group a pathway lists it in (a specialisation), for the Job specs tab
    subs = fw.subgroups(lib)
    desc_rows = []
    for r in fw.build_descriptions(lib):
        sub, place = subs.get((r["framework"], r["name"]), ("", ""))
        desc_rows.append({**r, "subgroup": sub, "subgroup_order": place})
    write_csv(os.path.join(data, "descriptions.csv"), desc_rows, fw.DESCRIPTION_COLUMNS + ["subgroup", "subgroup_order"])
    files["descriptions"] = ("data/descriptions.csv", "csv")
    js.write_csv(os.path.join(data, "jobspecs.csv"), specs)
    files["jobspecs"] = ("data/jobspecs.csv", "csv")
    write_csv(os.path.join(data, "assessors.csv"), asr.rows(cfg.assessors), asr.COLUMNS)
    files["assessors"] = ("data/assessors.csv", "csv")
    with open(template, encoding="utf-8") as fh:
        page = render_page(fh.read(), page_values(cfg, settings), has_fw)
    page_files = write_page(out, page, one_file)
    title = (cfg.dashboard or {}).get("title") or "Competency portfolio"
    manifest = {
        "title": title, "disclosure": disclosure, "builtOn": today.isoformat(), "frameworks": has_fw,
        "page": "index.html", "pageVersion": page_version(page), "files": page_files,
        "datasets": [{"id": k, "file": f, "format": fmt, "title": DATASETS[k][0], "description": DATASETS[k][1],
                      "fixed": DATASETS[k][2]} for k, (f, fmt) in files.items()],
        "unitsLeftOut": s.hidden_units,
    }
    write_json(os.path.join(out, "manifest.json"), manifest)
    return manifest


def stale_requirements(cfg, lib, sel) -> bool:
    """True when the vault's requirements file differs from what `frameworks.py build` would write now."""
    if not cfg.requirements or not cfg.frameworks or not os.path.isfile(cfg.requirements):
        return False
    with open(cfg.requirements, encoding="utf-8", newline="") as fh:
        have = list(csv.DictReader(fh))
    want = [{k: str(v) for k, v in r.items()} for r in fw.build_rows(lib, sel)]
    return have != want


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    kc.add_arguments(ap)
    ap.add_argument("--profile")
    ap.add_argument("--out", help="folder to write (default: Dashboard/ in the config's `outputs`)")
    ap.add_argument("--disclosure", choices=list(kc.DASHBOARD_DISCLOSURES),
                    help="evidence to count (default: the config's dashboard.disclosure, else on-request)")
    ap.add_argument("--today")
    ap.add_argument("--one-file", action="store_true",
                    help="keep the page in one index.html; stops if it is over the store's 256 KB a document, as the "
                         "shipped template now is")
    args = ap.parse_args(argv)
    cfg = kc.from_args(args)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    out = args.out or os.path.join(cfg.folders["outputs"], "Dashboard")
    disclosure = args.disclosure or (cfg.dashboard or {}).get("disclosure") or "on-request"
    try:
        m = build(cfg, out, disclosure, today, one_file=args.one_file)
        lib = fw.library_for(cfg)
        if stale_requirements(cfg, lib, fw.selection(cfg.frameworks, lib)):
            print(f"note: {cfg.rel(cfg.requirements)} is older than the config and library; run `frameworks.py build`",
                  file=sys.stderr)
    except (BuildError, js.SpecError, fw.FrameworkError) as exc:
        print(f"dashboard: {exc}", file=sys.stderr)
        return 1
    print(f"{m['title']}: {len(m['datasets'])} data files ({disclosure}; {m['unitsLeftOut']} unit(s) left out), "
          f"frameworks {'on' if m['frameworks'] else 'off'} -> {out}")
    for d in m["datasets"]:
        print(f"  {d['id']:<13} {d['file']}")
    print(f"page v{m['pageVersion']}: " + ", ".join(f"{f['name']} {max(1, f['bytes'] // 1024)} KB" for f in m["files"]))
    for f in m["files"]:
        if f["bytes"] > PART_WARN * PART_LIMIT:
            print(f"note: {f['name']} is {f['bytes'] // 1024} KB of the {PART_LIMIT // 1024} KB a store document may hold",
                  file=sys.stderr)
    print("Upload each data file and write each page file as references/dashboard.md §2 says.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
