"""Screenshot the dashboard page as a reader sees it, and report what the tests can't see.

The tests run the page with stand-in tokens (page_shim.py), so they show that it works and fits, not how it looks on
claude.ai. This script runs the same page with the Dashboard type's real stylesheet, which also resets every element:
that is how the numbered steps on Instructions were found to have lost their numbers. Use it before publishing a change
to assets/dashboard/index.html, and look at the pictures.

    python3 render_page.py --css app.css [--tab howitworks ...] [--width 1280 --width 400] [--scheme light --scheme dark]
                           [--cards] [--out DIR] [--bundle DIR | --vault ... --config ...]

--css     the type's stylesheet, saved from a published dashboard: with the Artifact tool, `action: read`, the
          dashboard's url and `path: artifact-type/app.css`. It is the host's file and changes, so it is not kept in the
          skill. Without it the stand-in tokens are used, and the pictures show layout only.
--bundle  a folder dashboard_build.py wrote. Without it the dashboard is built from the config into <out>/bundle.
--tab     a tab's id, as in its link (overview, rating, instructions, howitworks...); every tab when left out.
--cards   also one picture a card, which is easier to read than a long tab.

For each view it reports a script error and a page that slides sideways, and, with --css, each list that has bullets
or numbers under the stand-in tokens and none under the real stylesheet. It exits 1 when it reports anything.
Needs Playwright and its Chromium (`pip install playwright && playwright install chromium`)."""
import argparse
import datetime as dt
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import dashboard_build as db  # noqa: E402
import kg_config as kc  # noqa: E402
from page_shim import shim  # noqa: E402

WIDTHS = (1280, 400)
SCHEMES = ("light", "dark")

# every list in the open tab: where it is, how it starts, and whether it has markers
LISTS = """(tab) => [...document.getElementById(tab).querySelectorAll('ul, ol')].map((l) => ({
  at: (l.closest('[id]') || l).id, text: l.textContent.trim().replace(/\\s+/g, ' ').slice(0, 48),
  markers: getComputedStyle(l).listStyleType !== 'none' }))"""
STATE = "({ errors: window.__errors.slice(), slides: document.scrollingElement.scrollWidth > innerWidth + 1 })"


def _open(browser, target, width, scheme="light", scale=1):
    page = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme,
                               device_scale_factor=scale).new_page()
    page.goto("file://" + os.path.abspath(target))
    page.wait_for_timeout(400)
    return page


def _tabs(page, wanted):
    have = page.eval_on_selector_all(".sp-tab", "ts => ts.map(t => t.dataset.tab)")
    unknown = [t for t in wanted or [] if t not in have]
    if unknown:
        raise ValueError(f"no tab {', '.join(unknown)}; the page has {', '.join(have)}")
    return list(wanted or have)


def _lists(browser, target, tabs):
    page = _open(browser, target, WIDTHS[0])
    out = {}
    for tab in _tabs(page, tabs):
        page.click(f"#tab-{tab}")
        page.wait_for_timeout(300)
        out[tab] = page.evaluate(LISTS, tab)
    page.context.close()
    return out


def lost_markers(browser, bundle, out, css, tabs=None):
    """[{tab, at, text}]: each list with markers under the stand-in tokens and none under `css`. The page's own style
    takes the markers off a list it lays out as a row or a grid, in both runs; only the host's reset differs."""
    plain = _lists(browser, shim(bundle, os.path.join(out, "page-standin.html")), tabs)
    real = _lists(browser, shim(bundle, os.path.join(out, "page.html"), css), tabs)
    return [{"tab": tab, "at": a["at"], "text": a["text"]} for tab in plain for a, b in zip(plain[tab], real[tab])
            if a["markers"] and not b["markers"]]


def render(bundle, out, css=None, tabs=None, widths=WIDTHS, schemes=SCHEMES, cards=False, scale=1, browser=None):
    """Write <out>/<tab>-<scheme>-<width>.png for each view (and -cardN.png with `cards`); return (views, lost), where
    a view is {tab, scheme, width, files, errors, slides} and lost is lost_markers() (empty without `css`)."""
    from playwright.sync_api import sync_playwright
    os.makedirs(out, exist_ok=True)
    own = None if browser else sync_playwright().start()
    browser = browser or own.chromium.launch()
    try:
        lost = lost_markers(browser, bundle, out, css, tabs) if css else []
        target = shim(bundle, os.path.join(out, "page.html"), css)
        views = []
        for scheme in schemes:
            for width in widths:
                page = _open(browser, target, width, scheme, scale)
                if cards:           # a card's picture is taken wherever it has scrolled to: keep the tab bar off it
                    page.add_style_tag(content=".sp-sticky { position: static !important; }")
                seen = 0
                for tab in _tabs(page, tabs):
                    page.click(f"#tab-{tab}")
                    page.wait_for_timeout(300)
                    state = page.evaluate(STATE)
                    files = [f"{tab}-{scheme}-{width}.png"]
                    page.screenshot(path=os.path.join(out, files[0]), full_page=True)
                    if cards:
                        # a card out of view (the assessors' differences before anyone has rated) has no picture
                        shown = [c for c in page.query_selector_all(f"#{tab} > .sp-card") if c.is_visible()]
                        for i, card in enumerate(shown):
                            files.append(f"{tab}-{scheme}-{width}-card{i + 1}.png")
                            card.screenshot(path=os.path.join(out, files[-1]))
                    views.append({"tab": tab, "scheme": scheme, "width": width, "files": files,
                                  "errors": state["errors"][seen:], "slides": state["slides"]})
                    seen = len(state["errors"])
                page.context.close()
        return views, lost
    finally:
        if own:
            browser.close()
            own.stop()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    kc.add_arguments(ap)
    ap.add_argument("--profile")
    ap.add_argument("--bundle", help="a folder dashboard_build.py wrote (default: build one from the config)")
    ap.add_argument("--css", help="the Dashboard type's stylesheet (artifact-type/app.css of a published dashboard)")
    ap.add_argument("--tab", action="append", help="a tab's id; may be given more than once (default: every tab)")
    ap.add_argument("--width", action="append", type=int, help=f"pane width in px (default: {WIDTHS[0]} and {WIDTHS[1]})")
    ap.add_argument("--scheme", action="append", choices=SCHEMES, help="default: light and dark")
    ap.add_argument("--cards", action="store_true", help="also one picture a card")
    ap.add_argument("--scale", type=float, default=1, help="device pixel ratio of the pictures (default 1)")
    ap.add_argument("--out", help="folder for the pictures (default: a new temporary folder)")
    args = ap.parse_args(argv)
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        print("render: needs Playwright (`pip install playwright && playwright install chromium`)", file=sys.stderr)
        return 1
    out = args.out or tempfile.mkdtemp(prefix="dashboard-render-")
    bundle = args.bundle
    try:
        if not bundle:
            cfg = kc.from_args(args)
            bundle = os.path.join(out, "bundle")
            db.build(cfg, bundle, (cfg.dashboard or {}).get("disclosure") or "on-request", dt.date.today())
        css = open(args.css, encoding="utf-8").read() if args.css else None
        views, lost = render(bundle, out, css, args.tab, args.width or WIDTHS, args.scheme or SCHEMES, args.cards, args.scale)
    except (db.BuildError, OSError, ValueError) as exc:
        print(f"render: {exc}", file=sys.stderr)
        return 1
    bad = len(lost)
    for v in views:
        said = [f"script error: {e}" for e in v["errors"]] + (["the page slides sideways"] if v["slides"] else [])
        bad += len(said)
        print(f"{v['tab']:<15} {v['scheme']:<5} {v['width']:>5}px  {'; '.join(said) or 'ok'}  {v['files'][0]}"
              + (f" (+{len(v['files']) - 1} cards)" if len(v["files"]) > 1 else ""))
    for m in lost:
        print(f"{m['tab']}: a list in #{m['at']} loses its bullets or numbers under the stylesheet: “{m['text']}…”")
    if not css:
        print("note: no --css, so these show the stand-in tokens: layout only, not the look on claude.ai", file=sys.stderr)
    print(f"{len(views)} view(s), {bad} problem(s) -> {out}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
