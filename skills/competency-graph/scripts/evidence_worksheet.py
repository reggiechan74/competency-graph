#!/usr/bin/env python3
"""Generate a led-work and recognition worksheet for a competency graph (Specification v0.5).

`advanced` and `expert` are computed from led work (`demonstratesLed`) and outside recognition
(`recognition`) on evidence notes (spec §3.5). This worksheet lists every evidence note, grouped by
independent unit, with what it already `demonstrates`, so the owner can mark:

    demonstratesLed   the competencies they LED or were accountable for in that piece of evidence:
                      they made the call, gave the reasoned advice, or owned the result (RICS level 3,
                      SFIA level 5+), not just took part. Copy names from `demonstrates`.
    recognition       kinds of outside recognition the evidence itself shows:
                      credential   a senior or chartered credential in the discipline (FRICS, CFA)
                      assessing    assessed or judged others' work (exam assessor, peer reviewer, juror)
                      teaching     taught or trained others formally (course, workshop, counselling)
                      publication  published or presented outside the employer (paper, talk, keynote)
                      adoption     others adopted an original contribution (a method, tool, standard)
                      appointment  appointed as an authority (expert witness, advisory panel, critical role)
                      award        an award or prize from a third party

Each note gets two plan entries (`add: []` left empty = skipped), so the filled worksheet is an
`edit_links.py` plan. `suggested` is a hint from the note's type and title; it is never applied.

    evidence_worksheet.py [--vault . --profile P] [--out <worksheet.yaml>]
    edit_links.py plan <worksheet.yaml>          # dry run, then add --apply

Without --out the worksheet goes to the config's `working` folder as <date>_Led_Work_Worksheet.yaml.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_graph as cg  # noqa: E402

HINTS = [  # (pattern on title or name, recognition kind)
    (r"assessor|examiner|reviewer|judge|juror", "assessing"),
    (r"instructor|lecturer|teach|workshop|course creator|counsellor|counselor|mentor|trainer", "teaching"),
    (r"keynote|speaker|talk|paper|article|publication|book|podcast", "publication"),
    (r"expert witness|advisory|board|panel|council", "appointment"),
    (r"award|prize|winner", "award"),
]

HEADER = """# Led-work and recognition worksheet (Competency Graph Specification v0.5)
# Generated {today}. For each evidence note:
#   field: demonstratesLed -> under `add`, list the competencies from `demonstrates` that you LED there
#                             (you made the call, gave the reasoned advice, or owned the result).
#   field: recognition     -> under `add`, list kinds of outside recognition this evidence shows:
#                             credential | assessing | teaching | publication | adoption | appointment | award
# Leave `add: []` empty to skip. `suggested` is only a hint and is never applied.
# Competencies you list as led may stay in `demonstrates`; the checker counts them once.
# Apply with:  edit_links.py plan <this file>   (dry run), then add --apply
"""


def build(vault: str, profile: str | None, today: dt.date) -> list[dict]:
    an = cg.Analyzer(vault, cg.load_settings(profile), today)
    an.run()
    nodes = an.r.nodes
    title = lambda p: nodes[p].fm.get("title") or nodes[p].name  # noqa: E731
    order = sorted(an.evidence, key=lambda e: (-(an.period.get(an.root[e], (dt.date.min, dt.date.min))[1].toordinal()),
                                               title(an.root[e]), e != an.root[e], title(e)))
    rows = []
    for e in order:
        fm = nodes[e].fm
        demos = [nodes[s].name for s in an.links[e].get("demonstrates", [])]
        led = [nodes[s].name for s in an.links[e].get("demonstratesLed", [])]
        rec = fm.get("recognition") if isinstance(fm.get("recognition"), list) else []
        text = f"{title(e)} {nodes[e].name}".lower()
        hint = sorted({k for pat, k in HINTS if re.search(pat, text)}
                      | ({"credential"} if fm.get("evidenceType") == "credential" else set())
                      | ({"publication"} if fm.get("evidenceType") == "publication" else set()) - set(rec))
        context = {
            "title": title(e),
            "unit": title(an.root[e]) if an.root[e] != e else "(unit root)",
            "type": fm.get("evidenceType", ""),
            "organization": str(fm.get("organization") or ""),
            "period": cg.as_text(an.period_value(nodes[e])) if an.period_value(nodes[e]) is not None else "",
            "disclosure": fm.get("disclosure", ""),
        }
        if (demos or led) and fm.get("evidenceType") not in cg.KNOWLEDGE_ONLY:
            rows.append({"note": nodes[e].name, "field": "demonstratesLed", "add": [], **context,
                         "demonstrates": demos, "alreadyLed": led})
        rows.append({"note": nodes[e].name, "field": "recognition", "add": [], "title": context["title"],
                     "alreadyRecognised": rec, "suggested": hint})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    cg.kc.add_arguments(ap)
    ap.add_argument("--profile")
    ap.add_argument("--out", help="worksheet file (default: dated file in the config's `working` folder)")
    ap.add_argument("--today")
    args = ap.parse_args(argv)
    cfg = cg.kc.from_args(args)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    if not args.out:
        args.out = cfg.new_file("working", "Led_Work_Worksheet.yaml", today=today, mkdir=True)
    rows = build(args.vault, args.profile, today)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(HEADER.format(today=today.isoformat()))
        yaml.safe_dump(rows, fh, sort_keys=False, allow_unicode=True, width=200)
    notes = len({r["note"] for r in rows})
    hints = sum(bool(r.get("suggested")) for r in rows)
    print(f"{notes} evidence notes -> {args.out}  ({hints} with a recognition hint)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
