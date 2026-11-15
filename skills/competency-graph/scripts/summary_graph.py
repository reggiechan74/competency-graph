#!/usr/bin/env python3
"""Summarise a competency graph (Specification v0.5) as tables for a report or dashboard. Read-only
except for the files it writes.

    summary_graph.py [--config F | --vault V] [--profile P] [--today D]
                     [--disclosure public|on-request|confidential] [--out-dir DIR] [--markdown]

Writes four JSON row files (a bare list of row objects each) to --out-dir, by default a dated
folder `<date>_Graph_Summary_<disclosure>/` in the config's `outputs` folder:

    domains.json   one row per domain: claimed vs supported level, units, organisations, years,
                   first and latest evidence, stale flag, competencies rated
    competencies.json    one row per competency (domains and branch roots left out), rated or not, with
                   or without evidence at this disclosure: note (filename), domain, parent (main
                   `broader` note), rank, kind, claimed, supported, units, organisations, years,
                   latest, stale, fit (fit = over-claimed | under-claimed | matches | unrated |
                   no-evidence: no evidence at this disclosure, rated or not)
    timeline.json  one row per (independent unit, domain): unit, type, organisation, start, end,
                   sector, asOf (the day the graph was read, the same on every row); draw these as
                   bars on a time axis, one lane per domain, the stale line measured back from asOf
    sectors.json   one row per (domain, top-level sector), with the sector's code: independent units evidencing both;
                   units with no sector count under "No sector"

With --markdown it also writes summary.md (the domain table, the fit counts and the grid).

Disclosure: evidence above --disclosure is left out *before* anything is counted, so the levels,
units and dates are what a reader at that level could be shown. The default is `on-request`
(an application or a page you share with a named person); use `public` for anything posted openly.
`confidential` is for the owner's own eyes and must never leave the vault (SKILL.md rule 7).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_graph as cg  # noqa: E402

DISCLOSURE_RANK = {"public": 0, "on-request": 1, "confidential": 2}
LEVEL_RANK = cg.LEVEL_RANK


class Summary:
    def __init__(self, vault, profile, today, disclosure="on-request"):
        self.today = today
        self.disclosure = disclosure
        an = self.an = cg.Analyzer(vault, cg.load_settings(profile), today)
        an.run()
        self.nodes = an.r.nodes
        limit = DISCLOSURE_RANK[disclosure]

        def visible(e):
            rank = lambda p: DISCLOSURE_RANK.get(self.nodes[p].fm.get("disclosure", "confidential"), 2)  # noqa: E731
            return rank(e) <= limit and rank(an.root[e]) <= limit
        self.visible = {e for e in an.evidence if visible(e)}
        self.hidden_units = len({an.root[e] for e in an.evidence} - {an.root[e] for e in self.visible})
        # recount on visible evidence only. Every count the rows read (units, years, recency, led units and led
        # years, recognition, supported level, "missing for next level") comes from these tables, so all of them
        # are filtered; run() already computed and cached levels from ALL evidence, so that cache is dropped
        # and levels are recomputed from the filtered tables on first use.
        for table in (an.competency_support, an.led_support, an.led_direct, an.sector_support):
            for k in list(table):
                table[k] = {e for e in table[k] if e in self.visible}
        an.ev_sectors = {e: s for e, s in an.ev_sectors.items() if e in self.visible}
        an._levels = {}
        self.stale_cut = cg.years_before(today, an.settings["staleYears"])

    def title(self, p):
        return self.nodes[p].fm.get("title") or self.nodes[p].name

    def unit_label(self, u):
        return self.title(u)

    def competency_row(self, p):
        an, fm = self.an, self.nodes[p].fm
        units, orgs, _ = an.unit_profile(an.competency_support[p])
        latest, basis = an.recency_of(p)
        claimed = fm.get("claimedLevel") or ""
        detail = an.level_detail(p)
        supports = detail["level"]
        if not units:
            fit = "no-evidence"
        elif claimed not in LEVEL_RANK:
            fit = "unrated"
        elif LEVEL_RANK[claimed] > LEVEL_RANK[supports]:
            fit = "over-claimed"
        elif LEVEL_RANK[claimed] < LEVEL_RANK[supports]:
            fit = "under-claimed"
        else:
            fit = "matches"
        starts = [an.period[u][0] for u in units if u in an.period]
        dom = an.primary_domain.get(p)
        up = an.links[p].get("broader") or []
        ratings, _ = cg.assessments_of(fm)
        return {
            "competency": self.title(p),
            "note": self.nodes[p].name,
            "domain": self.title(dom) if dom else "",
            "parent": self.nodes[up[0]].name if up else "",   # the main `broader` note (a branch root or domain too)
            "rank": fm.get("rank") or "",
            "kind": fm.get("kind", "practice"),
            "claimed": claimed,
            # the assessors' ratings of the same competency (spec §3.9): each one, the level they agree on (the
            # lowest), how many levels apart they are, and who gave them and when
            "assessed": cg.agreed_level(ratings),
            "assessedBy": ", ".join(r["by"] for r in ratings),
            "assessedOn": max((r["on"] for r in ratings), default=""),
            "assessments": [cg.format_assessment(r["by"], r["level"], r["on"]) for r in ratings],
            "assessedSpread": cg.assessor_spread(ratings),
            # the competencies this one requires (spec §2.1, §3.10), by note: a claim should not stand above theirs
            "requires": [self.nodes[q].name for q in an.links[p].get("requires", [])],
            "supported": supports,
            "fit": fit,
            "deemed": str(fm.get("deemed") or ""),
            "externalRef": [str(x) for x in (fm.get("externalRef") or []) ] if isinstance(fm.get("externalRef"), list)
            else ([str(fm["externalRef"])] if fm.get("externalRef") else []),
            "units": len(units),
            "organisations": len(orgs),
            "years": an.years_of(p),
            "first": min(starts).isoformat() if starts else "",
            "latest": latest.isoformat() if latest else "",
            "basis": basis or "",
            "stale": bool(latest and latest < self.stale_cut) or (bool(units) and latest is None),
            "ledUnits": detail.get("units", 0),
            "ledYears": detail.get("years", 0),
            "recognition": ", ".join(detail.get("recognition", [])),
            "nextLevel": detail.get("next", ""),
            "missing": "; ".join(detail.get("missing", [])),
        }

    def domains(self):
        rows = []
        for d in sorted(self.an.domains, key=self.title):
            r = self.competency_row(d)
            members = [p for p in self.an.competencies if self.an.primary_domain.get(p) == d
                       and self.nodes[p].fm.get("rank") != "branch"]
            r = {"domain": r["competency"], **{k: v for k, v in r.items() if k not in ("competency", "domain", "rank", "kind")}}
            r["competenciesAdvancedPlus"] = sum(LEVEL_RANK[self.an.supports_level(q)] >= LEVEL_RANK["advanced"]
                                          for q in members)
            r["competencies"] = len(members)
            r["competenciesRated"] = sum(bool(self.nodes[p].fm.get("claimedLevel")) for p in members)
            rows.append(r)
        return rows

    def competencies(self):
        rows = [self.competency_row(p) for p in self.an.competencies if self.nodes[p].fm.get("rank") != "branch"
                and p not in self.an.domains]
        order = {"discipline": 0, "specialty": 1, "element": 2}
        return sorted(rows, key=lambda r: (r["domain"], order.get(r["rank"], 3), r["competency"]))

    def unit_domains(self):
        """independent unit -> set of domain paths it evidences (visible evidence only): the MAIN domain of each
        competency it demonstrates. A second parent in another domain (e.g. Real Property Valuation under Finance's
        Valuation) doesn't put the unit in that domain's lane; the domain support counts still roll up through it."""
        an, out = self.an, defaultdict(set)
        visible = set().union(*an.competency_support.values()) if an.competency_support else set()
        for e in visible:
            for field in ("demonstrates", "demonstratesLed"):
                for c in an.links.get(e, {}).get(field, []):
                    d = an.primary_domain.get(c)
                    if d:
                        out[an.root[e]].add(d)
        return out

    def unit_sector(self, u):
        secs = self.an.ev_sectors.get(u) or []
        tops = sorted({self.title(self.an.sector_top.get(s, s)) for s in secs})
        return tops

    def timeline(self):
        an, rows = self.an, []
        for u, doms in sorted(self.unit_domains().items(), key=lambda kv: (an.period.get(kv[0], (dt.date.min,))[0], kv[0])):
            if u not in an.period:
                continue
            start, end = an.period[u]
            fm = self.nodes[u].fm
            point = fm.get("evidenceType") == "credential"   # a credential is earned once: draw a point
            if point:
                end = start
            for d in sorted(doms, key=self.title):
                rows.append({
                    "unit": self.unit_label(u),
                    "domain": self.title(d),
                    "type": fm.get("evidenceType", ""),
                    "organisation": an.org_name(fm.get("organization")),
                    "sector": ", ".join(self.unit_sector(u)) or "No sector",
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "ongoing": not point and end >= self.today,
                    "point": point,
                    "asOf": self.today.isoformat(),   # the day the graph was read: the stale line is measured from it
                })
        return rows

    def sectors(self):
        grid = defaultdict(set)
        for u, doms in self.unit_domains().items():
            for s in self.unit_sector(u) or ["No sector"]:
                for d in doms:
                    grid[(self.title(d), s)].add(u)
        # each top-level sector's code in its classification ("51", "48-49"), for the page to show after its name;
        # "No sector" has none, and nor does a sector note still without one
        codes = {self.title(p): str(self.nodes[p].fm.get("code") or "") for p in set(self.an.sector_top.values())}
        return [{"domain": d, "sector": s, "code": codes.get(s, ""), "units": len(us)} for (d, s), us in sorted(grid.items())]

    def markdown(self, domains, competencies, sectors):
        out = [f"# Competency graph summary ({self.today.isoformat()})", "",
               f"Disclosure: `{self.disclosure}` and below. {self.hidden_units} independent unit(s) above that "
               f"level are left out of every count. Stale = latest evidence before {self.stale_cut.isoformat()}.", "",
               "Levels: L1 Aware, L2 Practitioner, L3 Advanced, L4 Expert (JSON files store the words).", "",
               "| Domain | Claimed | Supported | Units | Orgs | Years | First | Latest | Stale | Competencies rated |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for r in domains:
            out.append(f"| {r['domain']} | {cg.level_label(r['claimed']) if r['claimed'] else '-'} | "
                       f"{cg.level_label(r['supported'])} | {r['units']} | "
                       f"{r['organisations']} | {r['years']:g} | {r['first'][:7]} | {r['latest'][:7]} | "
                       f"{'yes' if r['stale'] else ''} | {r['competenciesRated']}/{r['competencies']} |")
        fits = defaultdict(int)
        for r in competencies:
            fits[r["fit"]] += 1
        out += ["", "**Claim vs. evidence (competencies):** " + ", ".join(f"{k} {v}" for k, v in sorted(fits.items())), ""]
        over = [r for r in competencies if r["fit"] == "over-claimed"]
        if over:
            out += ["Over-claimed: " + ", ".join(f"{r['competency']} ({cg.level_label(r['claimed'])} vs {cg.level_label(r['supported'])})" for r in over), ""]
        secs = sorted({r["sector"] for r in sectors})
        out += ["| Domain | " + " | ".join(secs) + " |", "|---|" + "---|" * len(secs)]
        cell = {(r["domain"], r["sector"]): r["units"] for r in sectors}
        for d in [r["domain"] for r in domains]:
            out.append(f"| {d} | " + " | ".join(str(cell.get((d, s), "")) for s in secs) + " |")
        return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    cg.kc.add_arguments(ap)
    ap.add_argument("--profile")
    ap.add_argument("--today")
    ap.add_argument("--disclosure", choices=list(DISCLOSURE_RANK), default="on-request")
    ap.add_argument("--out-dir", help="folder for the JSON files (default: dated folder in `outputs`)")
    ap.add_argument("--markdown", action="store_true", help="also write summary.md")
    args = ap.parse_args(argv)
    cfg = cg.kc.from_args(args)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    s = Summary(args.vault, args.profile, today, args.disclosure)
    out = args.out_dir or cfg.new_file("outputs", f"Graph_Summary_{args.disclosure}", today=today)
    os.makedirs(out, exist_ok=True)
    domains, competencies, timeline, sectors = s.domains(), s.competencies(), s.timeline(), s.sectors()
    for name, rows in (("domains", domains), ("competencies", competencies), ("timeline", timeline), ("sectors", sectors)):
        with open(os.path.join(out, f"{name}.json"), "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1, ensure_ascii=False)
    if args.markdown:
        with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as fh:
            fh.write(s.markdown(domains, competencies, sectors))
    print(f"{len(domains)} domains, {len(competencies)} competencies, {len(timeline)} timeline rows, {len(sectors)} grid cells "
          f"-> {out}  (disclosure {args.disclosure}; {s.hidden_units} unit(s) left out)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
