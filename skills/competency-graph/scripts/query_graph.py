#!/usr/bin/env python3
"""Answer questions from a competency graph (Specification v0.5). Read-only.

Vault and profile come from the nearest competency-graph.yaml unless --config/--vault/--profile are given.

    query_graph.py [--vault .] [--profile P] [--today D] support  <competency> [<competency> ...] [--disclosure LEVEL]
    query_graph.py [--vault .] [--profile P] [--today D] find     <words> [<words> ...]
    query_graph.py [--vault .] [--profile P] [--today D] tree     [<competency>] [--depth N]
    query_graph.py [--vault .] [--profile P] [--today D] framework <prefix> [--links]
    query_graph.py [--vault .] [--profile P] [--today D] evidence <note>
    query_graph.py [--vault .] [--profile P] [--today D] relations <competency>
    query_graph.py [--vault .] [--profile P] [--today D] organizations

support   What backs a competency (or sector) note: claim vs. support, independent units, organisations,
          anchors, recency and years, and which evidence notes, through which specific competency.
          --disclosure public | on-request | confidential (default) hides evidence above that level:
          on-request for anything sent to a named reader (an application), public for anything posted openly.
find      Map free text (e.g. a job requirement) to competency notes by title, filename and aliases.
          Each argument is one phrase; every word in it must match.
tree      Outline the competency tree by main parent, with claims and unit counts. A second parent is
          shown as "(also: ...)". Starts from all domains, or from <competency>.
framework Every competency mapped to an external framework (`externalRef` starting with <prefix>, e.g. "RICS APC"),
          with domain, claim and support. --links writes wikilinks, for an index note in the vault.
evidence  One evidence note: its unit root, children, period, links and disclosure.
relations What a competency requires and what requires it (each with its claimed level), what it is applied to and
          what serves it, and the credentials that certify it. The last is worked out from the evidence.
organizations  Each organisation the evidence names, with its units and every way it is written; an organisation
          note (its title or an alias) makes several spellings count as one.

<competency>/<note> may be a filename (with or without [[ ]]), a title, or an alias.
The note body, not the `demonstrates` tag, is the proof (Specification principle 11): read the
listed notes before citing them.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_graph as cg  # noqa: E402

DISCLOSURE_RANK = {"public": 0, "on-request": 1, "confidential": 2}


class Query:
    def __init__(self, vault, profile, today):
        self.an = cg.Analyzer(vault, cg.load_settings(profile), today)
        self.an.run()
        self.nodes = self.an.r.nodes
        self.today = today

    # ---- helpers
    def title(self, p):
        return self.nodes[p].fm.get("title") or self.nodes[p].name

    def labels(self, p):
        fm = self.nodes[p].fm
        out = [self.nodes[p].name, self.nodes[p].name.replace("_", " "), str(fm.get("title") or "")]
        aliases = fm.get("aliases") or []
        out += [str(a) for a in (aliases if isinstance(aliases, list) else [aliases])]
        return [x for x in out if x]

    def lookup(self, raw, types=None):
        raw = raw.strip()
        name = raw[2:-2] if raw.startswith("[[") and raw.endswith("]]") else raw
        path, _ = self.an.resolve(f"[[{name}]]")
        if path in self.nodes and (not types or self.nodes[path].type in types):
            return path
        want = name.lower()
        hits = [p for p in self.nodes if (not types or self.nodes[p].type in types)
                and want in {x.lower() for x in self.labels(p)}]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise SystemExit(f"'{raw}' matches {len(hits)} notes: " + ", ".join(self.nodes[h].name for h in hits))
        raise SystemExit(f"no graph note named '{raw}'. Try: query_graph.py ... find \"{raw}\"")

    def period_text(self, p):
        raw = self.an.period_value(self.nodes[p])
        return cg.as_text(raw) if raw is not None else "undated"

    def descendants(self, p):
        kids = {}
        for q in self.an.competencies:
            for parent in self.an.links[q].get("broader", []):
                kids.setdefault(parent, []).append(q)
        seen, todo = set(), [p]
        while todo:
            x = todo.pop()
            for c in kids.get(x, []):
                if c not in seen:
                    seen.add(c)
                    todo.append(c)
        return seen

    # ---- support
    def support(self, raw, max_disclosure="confidential"):
        an, nodes = self.an, self.nodes
        p = self.lookup(raw, {"competency", "sector"})
        fm = nodes[p].fm
        support = an.competency_support[p] if nodes[p].type == "competency" else an.sector_support[p]
        units, orgs, anchored = an.unit_profile(support)
        latest, basis = an.recency_of(p)
        years = an.years_of(p)
        stale_cut = cg.years_before(self.today, an.settings["staleYears"])
        stale = bool(latest and latest < stale_cut)
        kind = fm.get("kind", "practice") if nodes[p].type == "competency" else "sector"
        out = [f"## {self.title(p)} ({nodes[p].name})", ""]
        parents = [self.title(q) for q in an.links[p].get("broader", [])]
        dom = an.primary_domain.get(p) if nodes[p].type == "competency" else None
        bits = [f"type {nodes[p].type}/{kind}"]
        if fm.get("rank"):
            bits.append(f"rank {fm['rank']}")
        if dom and dom != p:
            bits.append(f"main domain {self.title(dom)}")
        if parents:
            bits.append("parents " + ", ".join(parents))
        out.append("- " + "; ".join(bits))
        d = an.level_detail(p)
        out.append(f"- claimed **{cg.level_label(fm.get('claimedLevel'))}**; evidence supports "
                   f"**{cg.level_label(d['level'])}** ({len(units)} independent units, {len(orgs)} organisations, "
                   f"{'anchored' if anchored else 'no external anchor'})")
        if "units" in d:
            out.append(f"- led work: {d['units']} unit(s), {d['orgs']} organisation(s), {d['years']:g} years; "
                       f"outside recognition: {', '.join(d['recognition']) or 'none'}"
                       + (f"; reached through {d['via']}" if d.get("via") else "")
                       + (f"; for {cg.level_label(d['next'])}: {'; '.join(d['missing'])}" if d.get("missing") else ""))
        refs = fm.get("externalRef") or []
        if refs:
            out.append("- external frameworks: " + "; ".join(str(r) for r in (refs if isinstance(refs, list) else [refs])))
        out.append(f"- latest eligible evidence {latest.isoformat() if latest else 'none'}"
                   f"{f' ({basis})' if basis else ''}; {years:g} years of dated evidence"
                   f"{'; STALE' if stale else ''}; status {fm.get('status', 'active')}")
        related = [self.title(q) for q in an.links[p].get("related", [])]
        related += [self.title(q) for q in an.competencies | an.sectors if p in an.links[q].get("related", [])]
        if related:
            out.append("- related: " + ", ".join(sorted(set(related))))
        out.append("")
        if not units:
            out.append("No evidence links to this note or any narrower competency.")
            return "\n".join(out)
        scope = {p} | (self.descendants(p) if nodes[p].type == "competency" else set())
        limit = DISCLOSURE_RANK[max_disclosure]
        rows, hidden = [], 0
        for u in sorted(units, key=lambda u: (an.period.get(u, (dt.date.min, dt.date.min))[1], self.title(u)), reverse=True):
            members = sorted(e for e in support if an.root[e] == u)
            shown = [e for e in members
                     if DISCLOSURE_RANK.get(nodes[e].fm.get("disclosure", "confidential"), 2) <= limit]
            if not shown:
                hidden += 1
                continue
            ufm = nodes[u].fm
            if nodes[p].type == "competency":
                via = sorted({self.title(s) for e in shown for s in an.links[e].get("demonstrates", []) if s in scope}
                             | {self.title(s) + " (led)" for e in shown
                                for s in an.links[e].get("demonstratesLed", []) if s in scope} or {"(via parent)"})
            else:
                via = sorted({self.title(s) for e in shown for s in an.links[e].get("sector", []) if s in scope}
                             or {"(via parent)"})
            notes = ", ".join(f"{nodes[e].name} [{nodes[e].fm.get('disclosure', 'confidential')}]" for e in shown)
            rows.append(f"| {self.title(u)} | {ufm.get('evidenceType', '')} | {an.org_name(ufm.get('organization'))} | "
                        f"{self.period_text(u)} | {'yes' if an.anchored({u}) else 'no'} | {', '.join(via)} | {notes} |")
        out += ["| Unit | Type | Organisation | Period | Anchor | Through competency | Evidence notes [disclosure] |",
                "|---|---|---|---|---|---|---|", *rows]
        if hidden:
            out += ["", f"{hidden} unit(s) hidden: all their evidence is above disclosure `{max_disclosure}`."]
        out += ["", "Paths: " + "; ".join(f"{nodes[e].name} = {e}" for e in sorted(support)
                                         if DISCLOSURE_RANK.get(nodes[e].fm.get("disclosure", "confidential"), 2) <= limit)]
        return "\n".join(out)

    # ---- find
    def find(self, phrases):
        out = []
        for phrase in phrases:
            words = [w for w in re.split(r"[\s_/,&-]+", phrase.lower()) if w]
            hits = []
            for p in self.an.competencies | self.an.sectors:
                tokens = re.split(r"[\s_/,&()'-]+", " ".join(self.labels(p)).lower())
                if words and all(any(t.startswith(w) for t in tokens) for w in words):
                    hits.append(p)
            out.append(f"## \"{phrase}\": {len(hits)} match(es)")
            for p in sorted(hits, key=self.title):
                units, _, _ = self.an.unit_profile(self.an.competency_support[p] if self.nodes[p].type == "competency"
                                                   else self.an.sector_support[p])
                out.append(f"- {self.title(p)} (`{self.nodes[p].name}`, {self.nodes[p].fm.get('kind', 'sector')}): "
                           f"claimed {cg.level_label(self.nodes[p].fm.get('claimedLevel'))}, {len(units)} units")
            if not hits:
                out.append("- none. Try fewer or broader words, or check whether the competency is missing from the graph.")
            out.append("")
        return "\n".join(out)

    # ---- tree
    def tree(self, raw=None, depth=None):
        an = self.an
        kids = {}
        for q in an.competencies:
            parents = an.links[q].get("broader", [])
            if parents:
                kids.setdefault(parents[0], []).append(q)
        roots = [self.lookup(raw, {"competency"})] if raw else sorted(an.domains, key=self.title)
        out = []

        def walk(p, level):
            fm = self.nodes[p].fm
            units, _, _ = an.unit_profile(an.competency_support[p])
            extra = [self.title(q) for q in an.links[p].get("broader", [])[1:]]
            tag = f" [{cg.level_label(fm.get('claimedLevel'))}]" if fm.get("claimedLevel") else ""
            dorm = f" ({fm['status']})" if fm.get("status") not in (None, "active") else ""
            also = f" (also: {', '.join(extra)})" if extra else ""
            out.append(f"{'  ' * level}- {self.title(p)}{tag} · {len(units)}u{also}{dorm}")
            if depth is None or level + 1 < depth:
                for c in sorted(kids.get(p, []), key=lambda c: (self.nodes[c].fm.get("rank") == "branch", self.title(c))):
                    walk(c, level + 1)

        for r in roots:
            walk(r, 0)
        out.append("")
        out.append("[level] = claimedLevel (L1 Aware, L2 Practitioner, L3 Advanced, L4 Expert); Nu = independent evidence units (rolled up from narrower competencies).")
        return "\n".join(out)

    # ---- framework
    def framework(self, prefix, links=False):
        """Every competency whose `externalRef` starts with `prefix` (e.g. "RICS APC"), one row per reference."""
        an, nodes = self.an, self.nodes
        rows = []
        for p in an.competencies:
            for ref in nodes[p].fm.get("externalRef") or []:
                ref = str(ref)
                if not ref.lower().startswith(prefix.lower()):
                    continue
                name = ref.split(":", 1)[1].strip() if ":" in ref else ref
                dom = an.primary_domain.get(p)
                comp = f"[[{nodes[p].name}\\|{self.title(p)}]]" if links else self.title(p)   # \\| : a pipe inside a table cell
                rows.append((name.lower(), name, comp, self.title(dom) if dom else "",
                             cg.level_label(nodes[p].fm.get("claimedLevel")), cg.level_label(an.level_detail(p)["level"])))
        rows.sort()
        out = [f"| {prefix} competency | Competency | Domain | Claimed | Supported |", "|---|---|---|---|---|"]
        out += [f"| {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |" for r in rows]
        out += ["", f"{len(rows)} reference(s) on {len({r[2] for r in rows})} competency note(s)."]
        return "\n".join(out)

    # ---- evidence
    def evidence(self, raw):
        an, nodes = self.an, self.nodes
        p = self.lookup(raw, {"evidence"})
        fm = nodes[p].fm
        out = [f"## {self.title(p)} ({nodes[p].name})", f"- path: {p}",
               "- " + "; ".join(x for x in (
                   str(fm.get("evidenceType") or ""),
                   an.org_name(fm.get("organization")) + (" via " + fm["via"] if fm.get("via") else ""),
                   f"period {self.period_text(p)}", f"disclosure {fm.get('disclosure')}",
                   f"anchor {fm.get('anchor') or 'none'}") if x)]
        if an.root[p] != p:
            out.append(f"- part of unit: {self.title(an.root[p])} ({nodes[an.root[p]].name})")
        kids = sorted(an.children.get(p, []), key=self.title)
        if kids:
            out.append("- contains: " + ", ".join(nodes[k].name for k in kids))
        if nodes[p].fm.get("recognition"):
            out.append("- recognition: " + ", ".join(map(str, nodes[p].fm["recognition"])))
        for f in ("demonstrates", "demonstratesLed", "sector", "referee"):
            vals = [self.title(q) for q in an.links[p].get(f, [])]
            if vals:
                out.append(f"- {f}: " + ", ".join(vals))
        return "\n".join(out)


    def relations(self, raw):
        """The named relations of one competency, both ways: what it requires and what requires it, what it is applied
        to and what serves it, and the credentials that certify it (worked out from the evidence, never stored)."""
        an, nodes = self.an, self.nodes
        p = self.lookup(raw, {"competency"})
        level = lambda q: cg.level_label(nodes[q].fm.get("claimedLevel")) if nodes[q].fm.get("claimedLevel") in cg.LEVELS else "not rated"  # noqa: E731
        named = lambda qs, lv=False: ", ".join(f"{self.title(q)}" + (f" ({level(q)})" if lv else "") for q in sorted(qs, key=self.title)) or "none"  # noqa: E731
        back = lambda f: {q for q in an.competencies if p in an.links[q].get(f, [])}  # noqa: E731
        certs = {e for e in an.competency_support[p] if nodes[e].fm.get("evidenceType") == "credential"}
        out = [f"## {self.title(p)} ({nodes[p].name}): claimed {level(p)}",
               f"- requires: {named(an.links[p].get('requires', []), True)}",
               f"- required by: {named(back('requires'), True)}",
               f"- applied to: {named(an.links[p].get('appliedTo', []))}",
               f"- served by: {named(back('appliedTo'))}",
               f"- certified by: {named(certs)}"]
        return "\n".join(out)

    def organizations(self):
        """Each organisation the evidence names, with its units: by organisation note where one answers to the name."""
        an, nodes = self.an, self.nodes
        units = {}
        for u in set(an.root.values()):
            key = an.org_key(nodes[u].fm.get("organization"))
            if key:
                units.setdefault(key, []).append(u)
        rows = []
        for key, us in units.items():
            noted = key in an.organizations
            spelt = sorted({" ".join(str(cg.as_text(nodes[u].fm.get("organization"))).split()) for u in us})
            name = self.title(key) if noted else spelt[0]
            rows.append((not noted, name.lower(), f"| {name} | {nodes[key].name if noted else '(no note)'} | {len(us)} | {'; '.join(spelt)} |"))
        return "\n".join(["| Organisation | Note | Units | Written as |", "|---|---|---|---|", *(r[2] for r in sorted(rows))])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    cg.kc.add_arguments(ap)
    ap.add_argument("--profile")
    ap.add_argument("--today")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("support")
    s.add_argument("competencies", nargs="+")
    s.add_argument("--disclosure", choices=list(DISCLOSURE_RANK), default="confidential")
    f = sub.add_parser("find")
    f.add_argument("phrases", nargs="+")
    t = sub.add_parser("tree")
    t.add_argument("competency", nargs="?")
    t.add_argument("--depth", type=int)
    w = sub.add_parser("framework")
    w.add_argument("prefix", help='start of the externalRef, e.g. "RICS APC"')
    w.add_argument("--links", action="store_true", help="competencies as wikilinks (for a note in the vault)")
    e = sub.add_parser("evidence")
    e.add_argument("note")
    r = sub.add_parser("relations", help="what a competency requires, is applied to and is certified by, both ways")
    r.add_argument("competency")
    sub.add_parser("organizations", help="each organisation the evidence names, with its units")
    args = ap.parse_args(argv)
    cg.kc.from_args(args)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    q = Query(args.vault, args.profile, today)
    if args.cmd == "support":
        print("\n\n".join(q.support(x, args.disclosure) for x in args.competencies))
    elif args.cmd == "find":
        print(q.find(args.phrases))
    elif args.cmd == "tree":
        print(q.tree(args.competency, args.depth))
    elif args.cmd == "framework":
        print(q.framework(args.prefix, args.links))
    elif args.cmd == "relations":
        print(q.relations(args.competency))
    elif args.cmd == "organizations":
        print(q.organizations())
    else:
        print(q.evidence(args.note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
