#!/usr/bin/env python3
"""Set the one version number the plugin and its dashboard page share, everywhere it is written.

The plugin and the dashboard page carry the same version. It is written in six places, and this keeps them equal:

    skills/competency-graph/assets/dashboard/index.html   the number the dashboard shows at its top right
    skills/competency-graph/assets/dashboard/DESIGN.md    "Page versions": what changed on the page, newest first
    .claude-plugin/plugin.json and marketplace.json       what Claude Code installs
    CHANGELOG.md                                           what changed in the plugin, newest first
    README.md                                              the Version and Tests badges and the Versions table

    python3 tools/bump_version.py 1.7.3 "What changed, in a sentence."
                                  [--page "What changed on the dashboard page, in a sentence."]
    python3 tools/bump_version.py --check      # exits 1 if the places disagree

Without --page the page's history gets "no change to the page", since the number still moves on it. A release is then:
finish the two entries if they need more than a sentence, run the tests, commit, `git tag vX.Y.Z`, push with the tag,
and `gh release create vX.Y.Z`.
Patch: a fix or a rewording. Minor: something new to see or use. Major: data files, store documents, settings or
notes in a new shape, so that owners must rebuild or migrate (assets/dashboard/DESIGN.md, "Page versions").
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "competency-graph")
PAGE = os.path.join(SKILL, "assets", "dashboard", "index.html")
DESIGN = os.path.join(SKILL, "assets", "dashboard", "DESIGN.md")
PLUGIN = os.path.join(ROOT, ".claude-plugin", "plugin.json")
MARKET = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
README = os.path.join(ROOT, "README.md")
SEMVER = r"\d+\.\d+\.\d+"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def versions() -> dict:
    """The version each place states, by a short name; None where it states none."""
    def find(pattern: str, text: str):
        m = re.search(pattern, text, re.M)
        return m.group(1) if m else None
    market = json.loads(read(MARKET))
    return {
        "dashboard page (index.html)": find(rf'id="page-version">Version ({SEMVER})</p>', read(PAGE)),
        "page history (DESIGN.md)": find(rf"^- \*\*({SEMVER})\*\* \(", read(DESIGN)),
        "plugin.json": json.loads(read(PLUGIN)).get("version"),
        "marketplace.json": next((p.get("version") for p in market.get("plugins", []) if p.get("name") == "competency-graph"), None),
        "CHANGELOG.md": find(rf"^## ({SEMVER}) \(", read(CHANGELOG)),
        "README badge": find(rf"badge/Version-({SEMVER})-", read(README)),
        "README table": find(rf"^\| The plugin and its dashboard page \| ({SEMVER}) \|", read(README)),
    }


def test_count() -> int | None:
    """How many tests the suite collects, for the README's badge; None when pytest can't say."""
    try:
        out = subprocess.run([sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"], cwd=os.path.join(SKILL, "scripts"),
                             capture_output=True, text=True, timeout=300).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"^(\d+) tests? collected", out, re.M)
    return int(m.group(1)) if m else None


def sub_once(pattern: str, repl: str, text: str, what: str) -> str:
    out, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f"bump: could not find {what}")
    return out


def bump(new: str, note: str, page_note: str | None, today: str) -> None:
    write(PAGE, sub_once(rf'(id="page-version">Version ){SEMVER}(</p>)', rf"\g<1>{new}\g<2>", read(PAGE), "the page's version"))
    design = read(DESIGN)
    if not re.search(rf"^- \*\*{re.escape(new)}\*\* \(", design, re.M):
        line = f"- **{new}** ({today}): {page_note or 'no change to the page; see the plugin’s `CHANGELOG.md`.'}\n"
        design = sub_once(rf"^(- \*\*{SEMVER}\*\* \()", line + r"\g<1>", design, "the page history's newest line")
    write(DESIGN, design)
    plugin = read(PLUGIN)
    write(PLUGIN, sub_once(rf'("version": "){SEMVER}(")', rf"\g<1>{new}\g<2>", plugin, "plugin.json's version"))
    write(MARKET, sub_once(rf'("version": "){SEMVER}(")', rf"\g<1>{new}\g<2>", read(MARKET), "marketplace.json's version"))
    log = read(CHANGELOG)
    if not re.search(rf"^## {re.escape(new)} \(", log, re.M):
        log = sub_once(rf"^(## {SEMVER} \()", f"## {new} ({today})\n\n- {note}\n\n" + r"\g<1>", log, "the changelog's newest entry")
    write(CHANGELOG, log)
    readme = sub_once(rf"(badge/Version-){SEMVER}(-)", rf"\g<1>{new}\g<2>", read(README), "the README's Version badge")
    readme = sub_once(rf"^(\| The plugin and its dashboard page \| ){SEMVER}( \|)", rf"\g<1>{new}\g<2>", readme, "the README's Versions table")
    n = test_count()
    if n:
        readme = sub_once(r"(badge/Tests-)\d+(-)", rf"\g<1>{n}\g<2>", readme, "the README's Tests badge")
    write(README, readme)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("version", nargs="?", help="the new version, X.Y.Z")
    ap.add_argument("note", nargs="?", help="what changed, in a sentence (the changelog entry's first line)")
    ap.add_argument("--page", help="what changed on the dashboard page, in a sentence (default: no change to the page)")
    ap.add_argument("--check", action="store_true", help="change nothing; exit 1 if the places disagree")
    ap.add_argument("--today", help="the release date, YYYY-MM-DD (default: today)")
    args = ap.parse_args(argv)
    if args.check:
        found = versions()
        for where, v in found.items():
            print(f"{v or 'none':<8} {where}")
        return 0 if len(set(found.values())) == 1 and None not in found.values() else 1
    if not args.version or not re.fullmatch(SEMVER, args.version):
        ap.error("give the new version as X.Y.Z")
    if not args.note:
        ap.error("say what changed, in a sentence")
    bump(args.version, args.note, args.page, args.today or dt.date.today().isoformat())
    found = versions()
    if set(found.values()) != {args.version}:
        print("bump: the places still disagree:", found, file=sys.stderr)
        return 1
    print(f"version {args.version} written in {len(found)} places; finish the entries in CHANGELOG.md and DESIGN.md if they need more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
