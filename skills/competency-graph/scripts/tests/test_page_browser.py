"""The dashboard page in a real browser: the three d3 charts, the layout at full and phone width, and the controls that
only a browser can show (page_harness.js runs the page in jsdom, which has no layout and no d3).

Skipped without Playwright and its Chromium (`pip install playwright && playwright install chromium`). The page is
run by page_shim.py with its stand-in for the claude.ai Dashboard type's tokens, so this checks that the page works
and fits, not how it looks there (render_page.py shows that, given the type's real stylesheet).
Run: python3 -m pytest scripts/tests -q"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import dashboard_build as db  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)
from test_dashboard import configure  # noqa: E402
from page_shim import shim  # noqa: E402

sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as exc:  # noqa: BLE001  (no browser installed: nothing to run the page in)
            pytest.skip(f"Chromium not available to Playwright: {str(exc).splitlines()[0]}")
        yield b
        b.close()


@pytest.fixture
def built(vault, tmp_path):  # noqa: F811
    cfg = configure(vault, "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n")
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    return "file://" + shim(str(tmp_path / "out"), str(tmp_path / "page.html"))


def open_page(browser, url, width):
    page = browser.new_context(viewport={"width": width, "height": 900}).new_page()
    page.goto(url)
    page.wait_for_timeout(300)
    return page


@pytest.mark.parametrize("width", [1280, 400])
def test_every_tab_draws_and_fits_the_pane(browser, built, width):
    page = open_page(browser, built, width)
    tabs = page.eval_on_selector_all(".sp-tab", "ts => ts.map(t => t.dataset.tab)")
    assert len(tabs) == 10
    for t in tabs:
        page.click(f"#tab-{t}")
        page.wait_for_timeout(150)
        m = page.evaluate("({sw: document.scrollingElement.scrollWidth, iw: innerWidth, errs: window.__errors})")
        assert m["errs"] == [], t
        assert m["sw"] <= m["iw"] + 1, f"{t} slides sideways at {width}px"
    page.context.close()


@pytest.mark.parametrize("width", [1280, 400])
def test_how_this_works_keeps_its_drawings_readable(browser, built, width):
    """A drawing never shrinks below a readable size: in a narrow pane it scrolls sideways inside its own wrapper,
    which the keyboard can reach. The chain of steps is a row in a wide pane and a column in a narrow one."""
    page = open_page(browser, built, width)
    page.click("#tab-howitworks")
    page.wait_for_timeout(200)
    m = page.evaluate("""({
      figs: [...document.querySelectorAll('#howitworks .sp-fig')].map((f) => { const b = f.querySelector('.sp-scroll'), s = f.querySelector('svg');
        return { svg: s.getBoundingClientRect().width, box: b.clientWidth, scrolls: b.scrollWidth > b.clientWidth + 1, tab: b.getAttribute('tabindex') }; }),
      text: Math.min(...[...document.querySelectorAll('#howitworks .sp-fig text.m')].map((t) => parseFloat(getComputedStyle(t).fontSize) * t.getScreenCTM().a)),
      flow: [...document.querySelectorAll('#howitworks .sp-flow')].map((o) => new Set([...o.children].map((li) => Math.round(li.getBoundingClientRect().left))).size),
      errs: window.__errors })""")
    assert m["errs"] == [] and len(m["figs"]) == 6 and m["text"] >= 9
    for f in m["figs"]:
        assert f["svg"] >= 570
        assert (f["scrolls"], f["tab"]) == ((True, "0") if width == 400 else (False, None))
    assert m["flow"] == ([6, 6, 6] if width == 1280 else [1, 1, 1])
    page.context.close()


@pytest.mark.parametrize("width", [1280, 400])
def test_the_version_sits_at_the_top_right_on_the_titles_first_line(browser, built, width):
    page = open_page(browser, built, width)
    m = page.evaluate("""(() => { const r = (s) => document.querySelector(s).getBoundingClientRect();
      const v = r('#page-version'), h = r('.sp-head h1'), head = r('.sp-head');
      return { text: document.querySelector('#page-version').textContent, right: head.right - v.right, top: v.top - h.top,
        after: v.left - h.right, line: parseFloat(getComputedStyle(document.querySelector('.sp-head h1')).lineHeight) || h.height }; })()""")
    assert re.fullmatch(r"Version \d+\.\d+\.\d+", m["text"])
    assert abs(m["right"]) <= 1 and m["after"] >= 0 and 0 <= m["top"] <= m["line"]
    page.context.close()


@pytest.mark.parametrize("width", [1280, 400])
def test_an_assessor_is_added_from_the_keyboard_and_offered_on_each_rating_tab(browser, built, width):
    """Add an assessor opens Configuration at the Assessors card; focus goes to the Name field, Enter saves, and focus
    returns to Add an assessor. The dropdown then shows above each table with an Assessed column, and nothing slides."""
    page = open_page(browser, built, width)
    page.click("#tab-rating")
    page.wait_for_timeout(150)
    page.click("#rating .sp-asrnone")
    page.wait_for_timeout(150)
    at = lambda: page.evaluate("document.activeElement.id || document.activeElement.dataset.k")  # noqa: E731
    assert page.evaluate("document.querySelector('.sp-tab[aria-selected=true]').dataset.tab") == "configuration" and at() == "h-assessors"
    page.click('#assessor-config [data-k="add"]')
    assert at() == "asr-name"
    page.keyboard.type("Dana Okafor")
    page.keyboard.press("Tab")
    page.keyboard.type("APC counsellor")
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    assert at() == "add" and page.inner_text("#assessor-config .sp-asrlist .who b") == "Dana Okafor"
    page.click('#assessor-config [data-k="delete:dana-okafor"]')
    assert at() == "keep"
    page.keyboard.press("Enter")                              # Keep: back on the row's Delete
    assert at() == "delete:dana-okafor"
    for tab in ("rating", "frameworks", "jobspecs"):
        page.click(f"#tab-{tab}")
        page.wait_for_timeout(200)
        sel = f'#{tab} select[data-draw="assessorsel"]'
        assert page.is_visible(sel) and not page.is_visible(f"#{tab} .sp-asrnone")
        page.select_option(sel, "dana-okafor")
        page.wait_for_timeout(200)
        m = page.evaluate("({sw: document.scrollingElement.scrollWidth, iw: innerWidth, errs: window.__errors, "
                          "cells: document.querySelectorAll('#%s td.sp-as select').length})" % tab)
        assert m["errs"] == [] and m["sw"] <= m["iw"] + 1 and m["cells"] > 0, tab
        page.select_option(sel, "")
    page.context.close()


def test_the_three_charts_draw(browser, built):
    page = open_page(browser, built, 1280)
    c = page.evaluate("""({
      bars: document.querySelectorAll('[data-draw=timelinechart] svg rect[rx="2"]').length,
      tlLabel: document.querySelector('[data-draw=timelinechart] svg').getAttribute('aria-label'),
      heat: !!document.querySelector('[data-draw=heat] table'),
      heatHeads: [...document.querySelectorAll('[data-draw=heat] thead th')].map((t) => t.textContent),
      fitSegs: document.querySelectorAll('[data-draw=fitchart] svg rect[rx="2"]').length,
      fitLabel: getComputedStyle(document.querySelector('[data-draw=fitchart] svg text.lane')).fill,
      lane: getComputedStyle(document.querySelector('[data-draw=timelinechart] svg text.lane')).fill,
      fg: getComputedStyle(document.querySelector('.sp')).color,
      asOf: document.querySelector('[data-draw=asof]').textContent, errs: window.__errors })""")
    assert c["errs"] == [] and c["bars"] > 0 and c["heat"] and c["fitSegs"] > 0
    # each sector is named with its code after it; units with no sector are headed for what they are, with no code
    assert "No sector" not in c["heatHeads"]
    named = [h for h in c["heatHeads"] if h != "Own work & credentials"]
    assert named and all(re.fullmatch(r".+ \([\w-]+\)", h) for h in named), c["heatHeads"]
    assert c["fitLabel"] == c["lane"] == c["fg"]                 # domain names in the text colour on both charts
    assert c["tlLabel"].startswith("Timeline of ")
    assert c["asOf"] == TODAY.strftime("%b ") + str(TODAY.day) + TODAY.strftime(", %Y")   # the day the graph was read
    page.context.close()


def test_the_timeline_shows_all_years_or_only_the_recent_ones(browser, built):
    page = open_page(browser, built, 1280)
    read = """() => ({
      years: [...document.querySelectorAll('[data-draw=timelinechart] svg text')].map(t => t.textContent).filter(t => /^\\d{4}$/.test(t)),
      staleShown: [...document.querySelectorAll('#timeline .sp-legend li[data-stale]')].filter(li => !li.hidden).length,
      pressed: [...document.querySelectorAll('.sp-tlrange')].map(b => b.dataset.range + '=' + b.getAttribute('aria-pressed')),
      label: document.querySelector('[data-draw=timelinechart] svg').getAttribute('aria-label'), errs: window.__errors })"""
    every = page.evaluate(read)
    page.click(".sp-tlrange[data-range=recent]")
    page.wait_for_timeout(150)
    recent = page.evaluate(read)
    assert every["errs"] == recent["errs"] == []
    assert every["pressed"] == ["all=true", "recent=false"] and recent["pressed"] == ["all=false", "recent=true"]
    assert every["staleShown"] == 2 and recent["staleShown"] == 0          # the stale line belongs to All years
    stale = db.cg.load_settings(None)["staleYears"]                         # the test profile sets 7; the page says which
    n = int(re.search(r"the last (\d+) years only", recent["label"]).group(1))
    assert n >= stale and int(recent["years"][0]) >= TODAY.year - n         # the axis starts at the cutoff
    assert len(set(recent["years"])) == len(recent["years"])                # one tick a year: no label twice
    assert int(every["years"][0]) <= int(recent["years"][0])
    page.context.close()


@pytest.mark.parametrize("width", [1280, 400])
def test_general_definitions_reads_as_cards_and_tables(browser, built, width):
    """Each topic is a card that is open to read (nothing to expand), with its values in tables that never slide the
    page sideways: side by side in a wide pane, one block a row in a narrow one, still tables to a screen reader."""
    page = open_page(browser, built, width)
    page.click("#tab-definitions")
    page.wait_for_timeout(200)
    got = page.evaluate("""() => { const p = document.getElementById('definitions');
      const card = (t) => t.closest('.sp-card').getBoundingClientRect();
      return { cards: p.querySelectorAll('.sp-card').length, closed: p.querySelectorAll('details').length,
        tables: p.querySelectorAll('table.sp-rt').length,
        wide: [...p.querySelectorAll('table.sp-rt')].filter(t => t.getBoundingClientRect().right > card(t).right + 1).length,
        rowDisplay: getComputedStyle(p.querySelector('table.sp-rt tbody tr')).display,
        roles: [...new Set([...p.querySelectorAll('table.sp-rt, .sp-rt tr, .sp-rt td')].map(e => e.getAttribute('role')))].sort(),
        unlabelled: [...p.querySelectorAll('table.sp-rt')].filter(t => t.querySelectorAll('thead th').length > 2
          && [...t.querySelectorAll('td')].some(c => !c.dataset.l)).length,
        stale: p.querySelector('[data-draw=staleyears]').textContent,
        jumps: [...p.querySelectorAll('[data-jump]')].map(b => !!document.getElementById(b.dataset.jump)),
        slide: document.documentElement.scrollWidth - innerWidth, errs: window.__errors }; }""")
    assert got["errs"] == [] and got["slide"] <= 0 and got["wide"] == 0
    assert got["cards"] >= 6 and got["closed"] == 0 and got["tables"] >= 15
    assert got["rowDisplay"] == ("table-row" if width == 1280 else "block")
    assert got["roles"] == ["cell", "row", "table"]                       # said outright, so the blocks are still a table
    assert got["unlabelled"] == 0                                          # a stacked cell names its column
    assert got["stale"] == str(db.cg.load_settings(None)["staleYears"]) or got["stale"].isdigit()
    assert got["jumps"] and all(got["jumps"])
    page.click("[data-jump=def-jobspecs]")                                 # a topic button goes to its card's heading
    page.wait_for_timeout(150)
    assert page.evaluate("document.activeElement.id") == "h-def-jobspecs"
    top = page.evaluate("document.getElementById('def-jobspecs').getBoundingClientRect().top")
    assert 0 <= top < 200
    page.context.close()


def test_what_is_missing_opens_in_place_and_many_saved_changes_close_under_their_count(browser, built):
    page = open_page(browser, built, 400)
    page.click("#tab-rating")
    page.wait_for_timeout(200)
    miss = page.locator("tbody[data-draw=alltable] button.sp-miss").first
    if miss.count():
        brief = miss.inner_text()
        miss.click()
        assert miss.get_attribute("aria-expanded") == "true" and miss.inner_text().startswith("For ")
        miss.click()
        assert miss.inner_text() == brief
    # six saved changes: the list closes under its count
    page.evaluate("""async () => { const db = await window.claude.use('db');
      for (let i = 0; i < 6; i += 1) await db.doc('claims/x' + i).set({ key: 'x' + i, note: 'x' + i, title: 'Competency ' + i, from: '', to: 'aware' }); }""")
    page.wait_for_timeout(200)
    box = page.evaluate("""({ summary: (document.querySelector('[data-draw=pendinglist] details summary') || {}).textContent,
      open: !!document.querySelector('[data-draw=pendinglist] details[open]'),
      status: document.querySelector('[data-draw=savestatus]').textContent, errs: window.__errors })""")
    assert box["errs"] == [] and box["open"] is False
    assert box["summary"] == "6 saved changes waiting for Claude to apply to the notes"
    assert box["status"] == "6 saved changes waiting for Claude to apply to the notes."
    page.context.close()
