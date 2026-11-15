#!/usr/bin/env python3
"""Generate a self-rating worksheet for a competency graph (Specification v0.5).

For every competency (except branch roots) the worksheet shows what the evidence
supports, so the owner can set `claimedLevel` deliberately:

    units        independent evidence units (partOf collapsed, rolled up from children)
    orgs         distinct organisations behind those units
    anchored     whether any supporting evidence has an external anchor
    latest       most recent end date of recency-eligible evidence (spec §3.4)
    basis        'work' (roles/engagements/activities) or 'project-only' (practice evidenced only by projects)
    supports     highest level the evidence supports: L4 Expert | L3 Advanced | L2 Practitioner | L1 Aware | none
    led          independent units of led work, their years, and kinds of outside recognition
    toNext       what the evidence still lacks for the next level
    stale        latest is older than the profile's threshold

Each entry is also a valid `edit_links.py` plan entry
({note, field: claimedLevel, set: ...}); the context keys are ignored when applied.
Fill in `set` (aware | practitioner | advanced | expert, or L1-L4), leave it blank to skip, then:

    edit_links.py --vault . plan <worksheet.yaml>            # dry run
    edit_links.py --vault . --apply plan <worksheet.yaml>

With `--assessor "<name>"` it is an assessor's worksheet instead: `set` is the assessor's rating, each entry is
{note, field: assessedLevel, set: ..., assessedBy: <name>, assessedOn: <today>}, and `claimed` shows the owner's own rating beside
it (and `otherAssessors` any other assessor's). Applying it writes each rating to the note's `assessments` in place of
this assessor's last one; the other assessors' ratings and the owner's claimedLevel are not touched.

Usage:
    rating_worksheet.py [--vault . --profile <profile.md>] [--out <worksheet.yaml>] [--today YYYY-MM-DD]

Vault and profile come from the nearest competency-graph.yaml unless given. Without --out the
worksheet goes to the config's `working` folder as <date>_Self_Rating_Worksheet.yaml.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_graph as cg  # noqa: E402

RANK_ORDER = {"domain": 0, "discipline": 1, "specialty": 2, "element": 3, None: 4}


def build(vault: str, profile: str | None, today: dt.date, assessor: str | None = None) -> list[dict]:
    an = cg.Analyzer(vault, cg.load_settings(profile), today)
    an.run()
    nodes = an.r.nodes
    title = lambda p: nodes[p].fm.get("title") or nodes[p].name  # noqa: E731
    stale_cut = cg.years_before(today, an.settings["staleYears"])
    rows = []
    for p in an.competencies:
        fm = nodes[p].fm
        if fm.get("rank") == "branch":
            continue
        support = an.competency_support[p]
        units, orgs, anchored = an.unit_profile(support)
        kind = fm.get("kind", "practice")
        latest, basis = an.recency_of(p)
        years = an.years_of(p)
        detail = an.level_detail(p)
        supports = detail["level"]
        dom = an.primary_domain.get(p)
        if assessor:                                # this assessor's own last rating, with the others' beside it
            ratings = cg.assessments_of(fm)[0]
            mine = next((r for r in ratings if r["by"].casefold() == assessor.casefold()), None)
            others = [f"{r['by']}: {cg.level_label(r['level'])}" for r in ratings if r is not mine]
            rate = {"field": "assessedLevel", "set": mine["level"] if mine else "", "assessedBy": assessor,
                    "assessedOn": today.isoformat(), "claimed": fm.get("claimedLevel") or "",
                    **({"otherAssessors": others} if others else {})}
        else:
            rate = {"field": "claimedLevel", "set": fm.get("claimedLevel") or ""}
        rows.append({
            "note": nodes[p].name,
            **rate,
            "title": title(p),
            "domain": title(dom) if dom else "",
            "rank": fm.get("rank") or "",
            "kind": kind,
            "units": len(units),
            "orgs": len(orgs),
            "anchored": bool(anchored),
            "latest": latest.isoformat() if latest else "",
            "basis": basis or "",
            "years": years,
            "supports": cg.level_label(supports),
            "led": f"{detail.get('units', 0)} units, {detail.get('years', 0):g} yrs, recognition: "
                   f"{', '.join(detail.get('recognition', [])) or 'none'}",
            "toNext": (f"{cg.level_label(detail['next'])}: " + "; ".join(detail["missing"])) if detail.get("missing") else "",
            "stale": bool(latest and latest < stale_cut) or (bool(units) and latest is None),
            "sources": sorted(title(u).split(" – ")[0] for u in units)[:8],
        })
    rows.sort(key=lambda r: (r["domain"], RANK_ORDER.get(r["rank"] or None, 4), r["title"]))
    return rows


HEADER = """# Self-rating worksheet (Competency Graph Specification v0.5)
# Generated {today}. For each competency, set `set:` to aware | practitioner | advanced | expert
# (L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert; `L3` is also accepted), or leave it blank to skip.
#   aware        = understands it and can discuss it; has not delivered it
#   practitioner = delivers it independently in normal situations
#   advanced     = handles complex cases without guidance, is accountable for the result, guides others
#   expert       = a recognised authority beyond their own team: others rely on their judgement
# `supports` is the most the evidence supports today. practitioner needs delivered work adding up to {prac:g}+
# months (a course or credential alone supports aware). advanced needs >=2 independent units of LED work
# (demonstratesLed) at >=2 organisations or with an anchor, over {adv:g}+ years; expert also needs {exp:g}+ years
# of led work and {rec} kind(s) of outside recognition. `led` shows those counts; `toNext` says what is missing.
# `years` = all dated evidence, overlaps merged. Claiming above `supports` shows as an `unsupported` warning.
# `stale: true` means the latest eligible evidence is more than {years} years old. `basis: project-only` means a
# practice is evidenced only by your own projects/courses (no role, engagement or activity yet).
# Apply with:  edit_links.py plan <this file>   (dry run), then add --apply
"""


ASSESSOR_NOTE = """\
# ASSESSOR'S WORKSHEET ({name}). `set` is the assessor's rating, not the owner's: fill it in from the framework's
# wording for each level, with `claimed` (the owner's own rating) and the evidence counts beside it for reference.
# Each rating is written to the note's `assessments` as "{name} | <level> | <date>", in place of this assessor's last
# one; `otherAssessors` shows any other assessor's rating, which stays. Change `assessedOn` where a rating was given on
# another day. A blank `set` leaves the note as it is.
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    cg.kc.add_arguments(ap)
    ap.add_argument("--profile")
    ap.add_argument("--out", help="worksheet file (default: dated file in the config's `working` folder)")
    ap.add_argument("--today")
    ap.add_argument("--assessor", metavar="NAME", help="write an assessor's worksheet instead: `set` is the "
                    "assessor's rating (assessedLevel), recorded with this name and today's date")
    args = ap.parse_args(argv)
    cfg = cg.kc.from_args(args)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    if not args.out:
        args.out = cfg.new_file("working", "Assessor_Rating_Worksheet.yaml" if args.assessor
                                else "Self_Rating_Worksheet.yaml", today=today, mkdir=True)
    rows = build(args.vault, args.profile, today, args.assessor)
    years = cg.load_settings(args.profile)["staleYears"]
    with open(args.out, "w", encoding="utf-8") as fh:
        st = cg.load_settings(args.profile)
        fh.write(HEADER.format(today=today.isoformat(), years=years,
                               prac=st["practitionerMinMonths"], adv=st["advancedMinYears"], exp=st["expertMinYears"], rec=st["expertMinRecognition"]))
        if args.assessor:
            fh.write(ASSESSOR_NOTE.format(name=args.assessor))
        yaml.safe_dump(rows, fh, sort_keys=False, allow_unicode=True, width=200)
    counts = {k: sum(r["supports"] == k for r in rows) for k in ("expert", "advanced", "practitioner", "aware", "none")}
    print(f"{len(rows)} competencies -> {args.out}  (evidence supports: "
          + ", ".join(f"{v} {k}" for k, v in counts.items()) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
