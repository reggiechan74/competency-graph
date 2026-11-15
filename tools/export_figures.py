#!/usr/bin/env python3
"""Write the drawings of the dashboard's "How this works" tab as standalone SVG files for the README.

The drawings live once, in skills/competency-graph/assets/dashboard/index.html, where they take their look from the
page's stylesheet by class. This copies each one out with that look written into the file, in a light and a dark
version, each on its own background so it reads on any page. Run it after changing a drawing in the template:

    python3 tools/export_figures.py            # writes docs/images/<name>.svg and <name>-dark.svg
    python3 tools/export_figures.py --check    # exits 1 if the files are out of date (for a test or a hook)
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "skills", "competency-graph", "assets", "dashboard", "index.html")
OUT = os.path.join(ROOT, "docs", "images")
# the card each drawing sits in -> its file name
NAMES = {"hw-parts": "three-parts", "hw-graph": "graph", "hw-counting": "supported-level", "hw-readings": "three-readings",
         "hw-frameworks": "frameworks-and-job-specs", "hw-page": "dashboard-database"}
PAD = 16
# the page's roles for a drawing (assets/dashboard/DESIGN.md, "Drawings"), as plain colours
THEMES = {
    "": {"bg": "#ffffff", "edge": "#d1d9e0", "fg": "#1f2328", "muted": "#59636e", "zone": "#d1d9e0", "box": "#f3f4f6"},
    "-dark": {"bg": "#0d1117", "edge": "#3d444d", "fg": "#f0f6fc", "muted": "#9198a1", "zone": "#3d444d", "box": "#161b22"},
}
STYLE = """
  text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 13px; fill: {fg}; }}
  text.m {{ fill: {muted}; font-size: 11.5px; }}
  text.k {{ fill: {muted}; font-size: 9.5px; letter-spacing: .06em; }}
  .b {{ fill: {fg}; font-weight: 600; }}
  .n {{ fill: {box}; stroke: {fg}; stroke-width: 1; }}
  .n.i {{ fill: {bg}; stroke: {muted}; }}
  .n.q {{ fill: none; stroke: {muted}; stroke-dasharray: 4 3; }}
  .z {{ fill: none; stroke: {zone}; stroke-width: 1.5; }}
  .e {{ fill: none; stroke: {fg}; stroke-width: 1.25; }}
  .e.q {{ stroke-dasharray: 4 3; }}
  .h {{ fill: {fg}; }}
"""


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def figures(html: str) -> dict:
    """{card id: (viewBox width, height, aria-label, inner SVG markup)} for each drawing on the How this works tab."""
    tab = html[html.index('id="howitworks"'):]
    out = {}
    for card in re.split(r'<section class="sp-card sp-ref" id="', tab)[1:]:
        cid = card[:card.index('"')]
        m = re.search(r'<figure class="sp-fig">.*?<svg viewBox="0 0 (\d+) (\d+)" role="img" aria-label="([^"]*)">(.*?)</svg>', card, re.S)
        if m:
            out[cid] = (int(m.group(1)), int(m.group(2)), m.group(3), m.group(4))
    return out


def render(w: int, h: int, label: str, inner: str, theme: dict) -> str:
    body = "\n".join("  " + line.strip() for line in inner.strip().splitlines())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-PAD} {-PAD} {w + 2 * PAD} {h + 2 * PAD}" '
            f'width="{w + 2 * PAD}" height="{h + 2 * PAD}" role="img" aria-label="{label}">\n'
            f"  <title>{esc(label)}</title>\n"
            f"  <style>{STYLE.format(**theme)}  </style>\n"
            f'  <rect x="{-PAD + .5}" y="{-PAD + .5}" width="{w + 2 * PAD - 1}" height="{h + 2 * PAD - 1}" rx="8" '
            f'fill="{theme["bg"]}" stroke="{theme["edge"]}"/>\n'
            f"{body}\n</svg>\n")


def build() -> dict:
    figs = figures(open(TEMPLATE, encoding="utf-8").read())
    missing = set(NAMES) - set(figs)
    if missing:
        raise SystemExit(f"no drawing found in: {', '.join(sorted(missing))}")
    return {f"{NAMES[cid]}{suffix}.svg": render(*figs[cid], theme) for cid in NAMES for suffix, theme in THEMES.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a file is missing or out of date")
    args = ap.parse_args(argv)
    files = build()
    stale = [n for n, text in files.items()
             if not os.path.isfile(os.path.join(OUT, n)) or open(os.path.join(OUT, n), encoding="utf-8").read() != text]
    if args.check:
        for n in stale:
            print(f"out of date: docs/images/{n}")
        return 1 if stale else 0
    os.makedirs(OUT, exist_ok=True)
    for n, text in files.items():
        with open(os.path.join(OUT, n), "w", encoding="utf-8") as fh:
            fh.write(text)
    print(f"wrote {len(files)} files to docs/images ({len(stale)} changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
