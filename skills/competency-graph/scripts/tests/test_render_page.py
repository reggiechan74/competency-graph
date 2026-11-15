"""render_page.py: the built page screenshotted view by view, and the list markers a host stylesheet takes away.
Skipped without Playwright and its Chromium. Run: python3 -m pytest scripts/tests -q"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import dashboard_build as db  # noqa: E402
import page_shim as ps  # noqa: E402
import render_page as rp  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)
from test_dashboard import configure  # noqa: E402
from test_page_browser import browser  # noqa: E402,F401  (fixture reuse; skips without Playwright)


@pytest.fixture
def bundle(vault, tmp_path):  # noqa: F811
    cfg = configure(vault, "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n")
    db.build(cfg, str(tmp_path / "bundle"), "on-request", TODAY)
    return str(tmp_path / "bundle")


def test_a_picture_for_each_view_and_each_card(browser, bundle, tmp_path):  # noqa: F811
    out = tmp_path / "shots"
    views, lost = rp.render(bundle, str(out), tabs=["howitworks"], widths=[400], schemes=["dark"], cards=True, browser=browser)
    assert lost == [] and [(v["tab"], v["scheme"], v["width"], v["errors"], v["slides"]) for v in views] == [
        ("howitworks", "dark", 400, [], False)]
    files = views[0]["files"]
    assert files[0] == "howitworks-dark-400.png" and len(files) == 1 + 10            # the tab, then its ten cards
    assert all((out / f).stat().st_size > 1000 for f in files)
    # a card that is out of view is passed over: Rating gaps hides the assessors' differences until someone has rated
    views, _ = rp.render(bundle, str(out), tabs=["gaps"], widths=[1280], schemes=["light"], cards=True, browser=browser)
    assert len(views[0]["files"]) == 1 + 1
    with pytest.raises(ValueError, match="no tab nosuch"):
        rp.render(bundle, str(out), tabs=["nosuch"], widths=[400], schemes=["light"], browser=browser)


def test_a_stylesheet_that_takes_list_markers_away_is_reported(browser, bundle, tmp_path):  # noqa: F811
    """The host resets every list. The page gives a list of prose its markers back, so that reset alone loses nothing;
    a list the page's style forgot (stood in for here by an !important rule) is named, with the card it is in. The row of
    topic buttons and the chain of steps have no markers by design, in both runs, and are not reported."""
    reset = ps.TOKENS + "\nol, ul, menu { list-style: none; }"
    _, lost = rp.render(bundle, str(tmp_path / "a"), reset, ["instructions", "howitworks", "definitions"], [1280], ["light"],
                        browser=browser)
    assert lost == []
    _, lost = rp.render(bundle, str(tmp_path / "b"), reset + "\n#howto-levels ol { list-style: none !important; }",
                        ["instructions", "howitworks"], [1280], ["light"], browser=browser)
    assert [(m["tab"], m["at"]) for m in lost] == [("instructions", "howto-levels")] and lost[0]["text"].startswith("Find the competency")
