"""Tests for dashboard_build.py: the whole dashboard rebuilt from the skill and the owner's files, and the page run in
jsdom (page_harness.js) when Node and jsdom are installed. Run: python3 -m pytest scripts/tests -q"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import dashboard_build as db  # noqa: E402
import kg_config as kc  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = """\
specs:
  manager:
    title: Manager, Acquisition
    mandatory:
      - {ref: "RICS APC: Client care", level: L2}
    core:
      - {ref: "RICS APC: Valuation", level: L3}
      - {ref: "RICS APC: Leasing/letting", level: L2}
"""


def configure(v, extra=""):
    (v / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nprofile: KG/Profile.md\n" + extra)
    (v / "KG/Competencies/Job_Specs.yaml").write_text(SPECS)
    write(v, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\n'
          'claimedLevel: practitioner\nexternalRef: ["RICS APC 2025: Leasing/letting"]')
    write(v, "KG/Profile.md", "title: Profile\nkgStaleYears: 7\nkgPeriodAliases: [tenure]\nkgExpertMinYears: 12\n"
          "kgExpertMinRecognition: 2")
    return kc.read_config(str(v / kc.CONFIG_NAME))


def whole(out, manifest):
    """The built page in one piece: index.html with the stylesheet and scripts it loads back in their places."""
    return db.join_page({f["name"]: (out / f["name"]).read_text(encoding="utf-8") for f in manifest["files"]})


def test_bundle_with_frameworks(vault, tmp_path):  # noqa: F811
    cfg = configure(vault, "dashboard:\n  title: Priya's <portfolio>\n  sectors: NAICS Canada\nframeworks:\n  rics-apc:\n"
                           "    pathways: [Valuation]\n")
    out = tmp_path / "out"
    m = db.build(cfg, str(out), "on-request", TODAY)
    assert [d["id"] for d in m["datasets"]] == ["domains", "competencies", "timeline", "sectors", "requirements",
                                               "descriptions", "jobspecs", "assessors"]
    assert all((out / d["file"]).is_file() for d in m["datasets"]) and m["frameworks"] is True
    page = whole(out, m)
    assert "<!-- kg:title -->Priya&#x27;s &lt;portfolio&gt;<!-- /kg:title -->" in page
    assert "each <!-- kg:sectors -->NAICS Canada<!-- /kg:sectors --> sector" in page
    # the heatmap names a sector with its code, and the card's note says what the number is, in the classification's name
    assert "after a sector’s name is its <!-- kg:sectors -->NAICS Canada<!-- /kg:sectors --> code." in page
    sectors = json.loads((out / "data" / "sectors.json").read_text())
    assert sectors and all(set(r) == {"domain", "sector", "code", "units"} for r in sectors)
    assert "/* kg:staleYears */7/* /kg:staleYears */" in page
    assert "<!-- kg:expertYears -->twelve<!-- /kg:expertYears -->" in page
    assert "<!-- kg:practitionerMonths -->six months<!-- /kg:practitionerMonths -->" in page   # the default
    assert "<!-- kg:expertRecognition -->two kinds<!-- /kg:expertRecognition -->" in page
    assert 'id="tab-frameworks"' in page and 'id="tab-jobspecs"' in page
    comp = json.loads((out / "data/competencies.json").read_text())
    assert any(r["externalRef"] == ["RICS APC 2025: Leasing/letting"] for r in comp)
    jobs = (out / "data/jobspecs.csv").read_text()
    assert jobs.startswith("spec,title,") and "Leasing/letting" in jobs


def test_bundle_without_frameworks_cuts_the_framework_tabs(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    out = tmp_path / "out"
    m = db.build(cfg, str(out), "public", TODAY)
    assert m["frameworks"] is False and "requirements" not in [d["id"] for d in m["datasets"]]
    page = whole(out, m)
    for gone in ('id="tab-frameworks"', 'id="tab-competencydefs"', 'id="framework-config"', 'id="frameworks"',
                 "dash.calc('framework_pathway'", "dash.calc('competency_definitions'", "Group minimums: Mandatory, Core and Optional",
                 'id="def-pathways"', 'data-jump="def-pathways"', "kg:fw"):
        assert gone not in page, gone
    assert "how both measure against the roles defined on Job specs." in page
    assert "left out of every count. Instructions says how to use the page, and How this works says what is behind it.</p>" in page
    assert 'id="tab-jobspecs"' in page and "job_spec_scores" in page
    # Configuration stays for the assessors, which every owner can have
    assert 'id="tab-configuration"' in page and 'id="assessor-config"' in page and (out / "data/assessors.csv").read_text() == "id,name,role\n"
    assert "<dd>The assessors who can rate these competencies.</dd>" in page
    # General definitions keeps its other topics, and every topic button still has a card to go to
    assert all(f'id="{i}"' in page for i in re.findall(r'data-jump="([^"]+)"', page)) and 'data-jump="def-jobspecs"' in page
    # every script still parses
    if shutil.which("node"):
        for i, s in enumerate(re.findall(r"<script>(.*?)</script>", page, re.S)):
            f = tmp_path / f"s{i}.js"
            f.write_text(s)
            assert subprocess.run(["node", "--check", str(f)], capture_output=True).returncode == 0, i


@pytest.mark.parametrize("frameworks", [True, False])
def test_how_this_works_explains_the_system_without_a_script(vault, tmp_path, frameworks):  # noqa: F811
    """The explainer tab is all in the HTML: a card for each topic button, each drawing an inline SVG with a name and a
    caption and nothing a host could strip (no ids to point at, no script, no style), and the framework-selection row
    going with the framework tabs."""
    cfg = configure(vault, "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n" if frameworks else "")
    out = tmp_path / "out"
    page = whole(out, db.build(cfg, str(out), "on-request", TODAY))
    assert 'id="tab-howitworks"' in page and 'aria-controls="howitworks"' in page
    panel = re.search(r'<section class="sp-panel" id="howitworks".*?\n  </section>\n', page, re.S).group(0)
    jumps = re.findall(r'data-jump="([^"]+)"', panel)
    assert len(jumps) == 9 and all(f'<section class="sp-card sp-ref" id="{j}">' in panel for j in jumps)
    figures = re.findall(r'<figure class="sp-fig">.*?</figure>', panel, re.S)
    assert len(figures) == 6
    for f in figures:
        assert re.search(r'<svg viewBox="0 0 720 \d+" role="img" aria-label="[^"]{60,}">', f) and "<figcaption>" in f
        assert not re.search(r"<script|<style|<foreignObject|url\(#|\bid=|href=", f)
    assert panel.count('<ol class="sp-flow" role="list">') == 3 and "data-draw" not in panel and "data-source" not in panel
    # the record behind a job: one bullet with its four HAM-Z parts marked, on both tabs
    assert page.count('<p class="sp-hamz">') == 2 and sorted(set(re.findall(r'<span data-p="([A-Z])">', panel))) == ["A", "H", "M", "Z"]
    assert 'id="howto-record"' in page
    # the dashboard's own database is named as one, with its collections; the framework selection goes with the framework tabs
    assert "The dashboard’s database</h3>" in panel and "<code>files</code>" in panel and "<code>datasets</code>" in panel
    assert "<code>settings</code>" in panel and "settings: the list of assessors" in panel
    assert ("and the choice of frameworks" in panel) is frameworks and ("pathways ticked" in panel) is frameworks
    assert "<code>claims</code>" in panel and "<code>jobspecs</code>" in panel
    # the owner's own threshold reaches the drawing's caption, as it reaches General definitions
    assert "for under <!-- kg:advancedYears -->five<!-- /kg:advancedYears --> years" in panel


def test_the_page_shows_its_own_version_beside_the_title(vault, tmp_path):  # noqa: F811
    """The version is the template's, the same on every owner's dashboard: in the header beside the title, in the
    manifest, and the newest entry of DESIGN.md's list of page versions, so a bump comes with a line saying what changed."""
    out = tmp_path / "out"
    m = db.build(configure(vault), str(out), "on-request", TODAY)
    page = whole(out, m)
    assert re.fullmatch(r"\d+\.\d+\.\d+", m["pageVersion"])
    row = re.search(r'<div class="sp-titlerow">\s*<h1>.*?</h1>\s*<p class="sp-version" id="page-version">Version ([\d.]+)</p>\s*</div>',
                    page, re.S)
    assert row and row.group(1) == m["pageVersion"]
    design = open(os.path.join(os.path.dirname(db.TEMPLATE), "DESIGN.md"), encoding="utf-8").read()
    listed = re.findall(r"^- \*\*(\d+\.\d+\.\d+)\*\* \(\d{4}-\d{2}-\d{2}\)", design[design.index("## Page versions"):], re.M)
    assert listed and listed[0] == m["pageVersion"]
    assert listed == sorted(listed, key=lambda v: tuple(map(int, v.split("."))), reverse=True)
    with pytest.raises(db.BuildError, match="page version"):
        db.page_version(page.replace('id="page-version"', ""))


def test_confidential_is_refused_and_a_bad_spec_stops_the_build(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    with pytest.raises(db.BuildError):
        db.build(cfg, str(tmp_path / "out"), "confidential", TODAY)
    (vault / "KG/Competencies/Job_Specs.yaml").write_text(SPECS.replace("Valuation", "Astrology"))
    with pytest.raises(db.BuildError, match="Astrology"):
        db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)


def test_template_markers_are_known_and_paired():
    page = open(db.TEMPLATE, encoding="utf-8").read()
    names = set(re.findall(r"(?:<!--|/\*) /?kg:([A-Za-z]+) (?:-->|\*/)", page))
    assert names == set(db.VALUES) | {"fw", "jobscore"}
    for n in names:
        assert len(re.findall(rf"(?:<!--|/\*) kg:{n} (?:-->|\*/)", page)) == len(re.findall(rf"(?:<!--|/\*) /kg:{n} (?:-->|\*/)", page)), n


def harness(bundle, scenario, tmp_path):
    f = tmp_path / "scenario.js"
    f.write_text(scenario)
    r = subprocess.run(["node", os.path.join(HERE, "page_harness.js"), str(bundle), str(f)], capture_output=True,
                       text=True, timeout=120)
    out = json.loads(r.stdout[r.stdout.index("{"):])
    if "skip" in out:
        pytest.skip(out["skip"])
    return out


SCENARIO = r"""
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
module.exports = async (h) => {
  const q = (s) => h.doc.querySelector(s);
  await h.openTab('jobspecs');
  h.log({ options: h.text('select[data-draw="jsselect"] option'), verdict: h.text('tbody[data-draw="jsverdict"] tr'),
    rows: h.text('tbody[data-draw="jstable"] tr').length });
  await h.click('#js-dup');
  await h.type('#js-title', 'Senior Manager');
  await h.select(q('#js-show'), 'all');
  await h.type('#js-search', 'health safety'); await wait(300);
  const tr = [...h.doc.querySelectorAll('tbody[data-draw="jspick"] tr')].find((t) => t.querySelector('th').textContent === 'Health and safety');
  await h.select(tr.querySelectorAll('select')[0], 'mandatory');
  await h.click('#js-save');
  h.log({ store: [...h.store.keys()], saved: h.store.get('jobspecs/senior-manager'), status: h.text('[data-draw="jsstatus"]') });
  for (const t of ['overview', 'rating', 'gaps', 'definitions', 'instructions', 'howitworks']) await h.openTab(t);
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
@pytest.mark.parametrize("frameworks", [True, False])
def test_page_runs_and_keeps_the_one_writer_rule(vault, tmp_path, frameworks):  # noqa: F811
    cfg = configure(vault, "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n" if frameworks else "")
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    out = harness(tmp_path / "out", SCENARIO, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    first, saved = out["log"]
    assert first["options"] == ["Manager, Acquisition"] and first["rows"] == 5     # 2 section rows, 3 competencies
    assert any(v.startswith("As claimed") for v in first["verdict"])
    assert saved["store"] == ["jobspecs/senior-manager"]
    rows = saved["saved"]["rows"]
    assert {(r["section"], r["name"]) for r in rows} >= {("mandatory", "Health and safety"), ("core", "Valuation")}
    assert saved["saved"]["title"] == "Senior Manager" and saved["status"][0].startswith("Saved on this dashboard")


CLAIMS = r"""
module.exports = async (h) => {
  const q = (s) => h.doc.querySelector(s);
  await h.openTab('rating');
  const sel = () => [...h.doc.querySelectorAll('tbody[data-draw="alltable"] tr[data-key]')].find((t) => t.dataset.key === 'Leasing').querySelector('select');
  const status = () => h.text('[data-draw="savestatus"]')[0];
  const was = sel().value;
  await h.select(sel(), 'expert');
  await h.click('#savebtn');
  h.log({ was, store: [...h.store.keys()], to: (h.store.get('claims/Leasing') || {}).to, status: status() });
  h.window.spMsg = ''; h.window.spRedraw();
  h.log({ waiting: status() });
  h.window.spMsg = 'Saved 1 change. Ask Claude to apply them to the notes.';
  await h.select(sel(), 'advanced');                 // a new change: the last save's message goes
  h.log({ staged: status() });
  await h.select(sel(), was);                        // back at the note's own level
  await h.click('#savebtn');
  // the bar has closed by now (nothing unsaved, nothing waiting), so the message is the one read out
  h.log({ store: [...h.store.keys()], said: h.text('[data-draw="announce"]')[0], barHidden: q('#toolbar').hidden });
  await h.openTab('jobspecs');
  h.log({ one: q('.sp-empty[data-empty="jscompareone"]').hidden, tick: q('.sp-empty[data-empty="jscompare"]').hidden });
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_a_saved_change_put_back_is_withdrawn_and_the_status_line_stays_true(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    out = harness(tmp_path / "out", CLAIMS, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    saved, waiting, staged, back, compare = out["log"]
    assert saved["was"] == "practitioner" and saved["store"] == ["claims/Leasing"] and saved["to"] == "expert"
    assert saved["status"].startswith("Saved 1 change.")
    assert waiting["waiting"] == "1 saved change waiting for Claude to apply to the notes."
    assert staged["staged"] == "1 unsaved change."               # not "... Saved 1 change."
    assert back["store"] == [] and back["barHidden"] is True     # no "L2 to L2" document left behind
    assert back["said"].startswith("Withdrew 1 change")
    assert compare == {"one": False, "tick": True}               # one spec: nothing to tick, so say how to add one


def test_the_page_is_written_in_parts_each_well_under_the_store_limit(vault, tmp_path, monkeypatch):  # noqa: F811
    cfg = configure(vault, "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n")
    out = tmp_path / "out"
    m = db.build(cfg, str(out), "on-request", TODAY)
    names = [f["name"] for f in m["files"]]
    assert names[:2] == ["index.html", "dashboard.css"] and len(names) >= 4 and all((out / n).is_file() for n in names)
    index = (out / "index.html").read_text()
    assert index.startswith('<meta name="dash-one-writer">') and "<style>" not in index and "<script>" not in index
    assert [n for n in re.findall(r'<script src="([^"]+)"></script>', index)] == [n for n in names if n.endswith(".js")]
    assert '<link rel="stylesheet" href="dashboard.css">' in index
    # no part comes near the 256 KB a store document may hold, which the template in one piece does: each script and
    # the stylesheet keep under 60% of it. index.html holds every tab's own words and cannot be split (the Dashboard
    # type takes one HTML file), so it is held to the build's own warning line instead
    for f in m["files"]:
        assert f["bytes"] == (out / f["name"]).stat().st_size
        assert f["bytes"] < (db.PART_WARN if f["name"] == "index.html" else 0.6) * db.PART_LIMIT, f["name"]
    # split and joined, the page is the template with the owner's settings: nothing is lost or reordered
    with open(db.TEMPLATE, encoding="utf-8") as fh:
        rendered = db.render_page(fh.read(), db.page_values(cfg, db.cg.load_settings(cfg.profile)), True)
    assert whole(out, m) == rendered
    # in one piece the page is over the store's limit, and the build says so instead of writing it
    with pytest.raises(db.BuildError, match="build without --one-file"):
        db.build(cfg, str(out), "on-request", TODAY, one_file=True)
    # one file on request, where it fits, and a part left over from the split build is cleared away
    monkeypatch.setattr(db, "PART_LIMIT", 2 * db.PART_LIMIT)
    m1 = db.build(cfg, str(out), "on-request", TODAY, one_file=True)
    assert [f["name"] for f in m1["files"]] == ["index.html"] and (out / "index.html").read_text() == rendered
    assert not (out / "dashboard.css").exists() and not (out / "dashboard-1.js").exists()


def test_a_page_file_over_the_limit_stops_the_build(vault, tmp_path, monkeypatch):  # noqa: F811
    cfg = configure(vault)
    monkeypatch.setattr(db, "PART_LIMIT", 50 * 1024)
    with pytest.raises(db.BuildError, match="KB limit"):
        db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)


def test_timeline_rows_carry_the_day_the_graph_was_read(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    rows = json.loads((tmp_path / "out/data/timeline.json").read_text())
    assert rows and {r["asOf"] for r in rows} == {TODAY.isoformat()}


JOBS = r"""
module.exports = async (h) => {
  const q = (s) => h.doc.querySelector(s);
  await h.openTab('jobspecs');
  const heads = h.text('#jobscore thead th');
  const rows = () => h.text('tbody[data-draw="jstable"] tr[data-key]');
  // the points columns: headed with the basis being scored, and the credit above the requirement in a column of its own
  const shown = () => [...h.doc.querySelectorAll('#jobscore thead [data-basisword]')].filter((w) => !w.hidden).map((w) => w.textContent);
  const cells = () => [...h.doc.querySelectorAll('tbody[data-draw="jstable"] tr[data-key]')].map((tr) => [...tr.children].slice(-3).map((c) => c.textContent));
  const claimedHeads = shown(); const claimedCells = cells();
  await h.click('.sp-seg[data-basis="supported"]');
  const supportedHeads = shown(); const groupSpan = q('tbody[data-draw="jstable"] th.sp-group').colSpan;
  const width = q('tbody[data-draw="jstable"] tr[data-key]').children.length;
  await h.click('.sp-seg[data-basis="claimed"]');
  h.log({ heads: heads.slice(0, 3), verdictHeads: h.text('.sp-verdict thead th').slice(0, 3), all: rows().length,
    group: h.text('tbody[data-draw="jstable"] th.sp-group')[0], claimedHeads, supportedHeads, claimedCells, groupSpan, width });
  await h.click('#js-shortonly');
  h.log({ pressed: q('#js-shortonly').getAttribute('aria-pressed'), short: rows() });
  await h.click('#js-shortonly');
  // Delete asks first
  await h.click('#js-delete');
  h.log({ asked: !q('#js-delconfirm').hidden, store: [...h.store.keys()] });
  await h.click('#js-delno');
  h.log({ kept: q('#js-delconfirm').hidden, store: [...h.store.keys()] });
  await h.click('#js-delete');
  await h.click('#js-delyes');
  h.log({ store: [...h.store.keys()], doc: h.store.get('jobspecs/manager'), hidden: q('#js-delconfirm').hidden });
  // the editor's status line carries the verdict
  await h.click('[data-draw="jsstatus"] button');           // Use the file's version
  await h.click('#js-edit');
  h.log({ edit: h.text('[data-draw="jseditstatus"]')[0] });
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_scorecard_result_first_shortfalls_only_and_delete_asks_first(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    out = harness(tmp_path / "out", JOBS, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    first, short, asked, kept, deleted, edit = out["log"]
    assert first["heads"] == ["Framework competency", "Result", "Required"]   # the result beside the name
    assert first["verdictHeads"] == ["Scored on", "Band", "Promotion"]     # the answer before what it rests on
    assert first["all"] == 3 and re.match(r"Mandatory\s*\d of 1 met", first["group"])
    assert first["claimedHeads"] == ["Claimed breadth", "Claimed depth", "Claimed credit above"]
    assert first["supportedHeads"] == ["Supported breadth", "Supported depth", "Supported credit above"]
    # ten cells a row with the new column; the group heading spans the nine in view (Assessed is out of view here)
    assert first["width"] == 10 and first["groupSpan"] == 9
    for breadth, depth, above in first["claimedCells"]:                    # points credited of required; credit apart
        assert re.fullmatch(r"\d+ / \d+|—", breadth) and re.fullmatch(r"\d+ / \d+|—", depth)
        assert re.fullmatch(r"\+\d+|—", above)
    assert short["pressed"] == "true" and 0 < len(short["short"]) < 3
    assert all(re.search(r"Short|Not held", r) for r in short["short"])
    assert asked == {"asked": True, "store": []}                           # nothing is removed on the first press
    assert kept == {"kept": True, "store": []}
    assert deleted["store"] == ["jobspecs/manager"] and deleted["doc"]["deleted"] is True and deleted["hidden"] is True
    assert "As claimed:" in edit["edit"] and "As supported:" in edit["edit"]


GROUPS = r"""
module.exports = async (h) => {
  // spGroupStatus reads a rule up to its footnote. Six chosen competencies, the first n at L3 and the rest at L2, plus
  // (when extra) one more RICS competency at L2 outside the list, for "Plus, one to Level 2 from the full list".
  const run = (rule, l3, total, extra) => {
    const rows = Array.from({ length: total }, (_, i) => ({ framework: 'RICS APC', pathway: 'P', group: 'Optional', name: 'C' + i,
      note: 'N' + i, key: 'k' + i, required: 'choice', rule, lvl: i < l3 ? 3 : 2 }));
    const comps = extra ? [{ note: 'Extra', externalRef: JSON.stringify(['RICS APC 2025: Elsewhere']), lvl: 2 }] : [];
    return h.window.spGroupStatus(rows, [], comps, (r) => r.lvl).get('P|Optional');
  };
  const ownRule = 'Six from this list: three to L3 and three to L2. *Choose the options that fit; one to L4 is never asked.';
  const own = (l3, total, group) => {
    const rows = Array.from({ length: total }, (_, i) => ({ framework: 'Chan AGEN', pathway: 'P', group, name: 'C' + i,
      note: 'N' + i, key: 'k' + i, required: 'choice', rule: ownRule, lvl: i < l3 ? 3 : 2 }));
    return h.window.spGroupStatus(rows, [], [], (r) => r.lvl).get('P|' + group);
  };
  const marker = 'Three to Level 3 or two to Level 3 and two to Level 2*. Plus, one to Level 2 from the full list of technical competencies. *Candidates planning to specialise must choose two to Level 3 from the following list.';
  const spaced = 'Three to Level 3 and one to Level 2. Plus, one to Level 2 from the full list of technical competencies. * If Valuation is taken to Level 3 the optional requirements are: Two to Level 3 and one to Level 2 plus two to Level 2 from the full list.';
  const plain = 'Two to Level 2 * Candidates working in a contracting environment will likely choose Commercial management to Level 3.';
  h.log({
    markerNoPlus: run(marker, 2, 4, false),     // the list is met, the "Plus" is not: short
    markerPlus: run(marker, 2, 4, true),
    spacedPlus: run(spaced, 3, 4, true),        // the footnote's own "two to Level 3 ... plus two" is not the rule
    spacedShort: run(spaced, 2, 4, true),
    plain: run(plain, 0, 2, false),
    ownMeets: own(3, 6, 'Optional'),            // another framework grouped the same way: "three to L3 and three to L2"
    ownShort: own(2, 6, 'Optional'),
    ownFew: own(3, 5, 'Optional'),
    otherGroup: own(3, 6, 'Specialism: required at L3') || '',   // other group names carry no group minimum
    // display order: alphabetical within a group; under a printed rule or condition, within that rule
    alpha: h.window.spAlpha([{ name: 'Ethics' }, { name: 'client care' }, { name: 'AI use' }, { name: 'Accounting' }], false).map((r) => r.name),
    alphaByRule: h.window.spAlpha([
      { name: 'Zeta', rule: 'B. Second domain' }, { name: 'Sustainability', rule: 'Only one of: Sustainability, Data management. Two to Level 3.' },
      { name: 'Data management', rule: 'Only one of: Sustainability, Data management. Two to Level 3.' }, { name: 'Valuation', rule: 'Two to Level 3.' },
      { name: 'Auctioneering', rule: 'Two to Level 3.' }, { name: 'Alpha', rule: 'B. Second domain' },
      { name: 'Inspection', rule: 'Must be taken to L3. Two to Level 3.' }], true).map((r) => r.name),
    // sub-groups of a group (specialisations within Optional) stay together under the group's one rule, in file order
    alphaBySub: h.window.spAlpha([
      { name: 'Zeta', rule: 'Two to L3.', subgroup: 'Second' }, { name: 'Mapping', rule: 'Two to L3.', subgroup: 'First' },
      { name: 'Alpha', rule: 'Two to L3.', subgroup: 'Second' }, { name: 'Cadence', rule: 'Two to L3.', subgroup: 'First' }], true).map((r) => r.name),
    alphaBySubNoRule: h.window.spAlpha([
      { name: 'Zeta', subgroup: 'Second' }, { name: 'Mapping', subgroup: 'First' }, { name: 'Alpha', subgroup: 'Second' }], false).map((r) => r.name),
    // a condition on some rows says what the one counts toward; semicolons where a name has a comma of its own
    onlyOptional: h.window.spOnlyText('Only one of: B, A, and more.', 'Optional', ['A', 'B, and more']),
    onlyCore: h.window.spOnlyText('Only one of: A, B.', 'Core', ['A', 'B'], true),
    onlyAlone: h.window.spOnlyText('Only one of: A, B.', 'Optional', ['A']),
  });
  // the minimum applies each condition a guide puts on some rows of a group
  const row = (name, group, required, rule, lvl) => ({ framework: 'RICS APC', pathway: 'P', group, name, note: name, key: name, required, rule, lvl });
  const st = (rows, g) => h.window.spGroupStatus(rows, [], [], (r) => r.lvl).get('P|' + g);
  const core = (a, b) => [row('A', 'Core', 'L3', 'Only one of: A, B.', a), row('B', 'Core', 'L3', 'Only one of: A, B.', b)];
  const two = 'Only one of: A, B. Two to Level 2.';
  const must = (hl, xl) => [row('H', 'Optional', 'L3', 'Only one of: H, S. Must be taken to L3. One to Level 2.', hl),
    row('S', 'Optional', 'choice', 'Only one of: H, S. One to Level 2.', 0), row('X', 'Optional', 'choice', 'One to Level 2.', xl)];
  // "whichever is not selected as core": Core takes the lower of the two that meets it, the other is the choice
  const both = (a, b) => [...core(a, b), row('A', 'Optional', 'choice', 'Only one of: A, B. One to Level 3.', a),
    row('B', 'Optional', 'choice', 'Only one of: A, B. Whichever is not selected as core competency. One to Level 3.', b)];
  h.log({
    eitherOne: st(core(3, 0), 'Core'), eitherNone: st(core(2, 2), 'Core'),             // "A or B" at L3: one is enough
    onlyOneCounts: st([row('A', 'Optional', 'choice', two, 2), row('B', 'Optional', 'choice', two, 2)], 'Optional'),
    onlyOnePlusOther: st([row('A', 'Optional', 'choice', two, 2), row('B', 'Optional', 'choice', two, 2), row('C', 'Optional', 'choice', 'Two to Level 2.', 2)], 'Optional'),
    mustNotChosen: st(must(0, 2), 'Optional'),      // a choice that must be taken to L3, not taken: asks nothing
    mustBelow: st(must(2, 0), 'Optional'),          // below its level it does not count
    mustAt: st(must(3, 0), 'Optional'),
    notCoreTwice: st(both(3, 0), 'Optional'), coreAndChoice: st(both(3, 3), 'Optional'), higherIsTheChoice: st(both(4, 3), 'Optional'),
    isEither: [h.window.spEitherOr(core(0, 0)), h.window.spEitherOr(must(0, 0).slice(0, 2))],
  });
  // drawn: the Valuation pathway's four, each named whole, with every row listed and with the unrated ones hidden
  const drawn = async (hide) => {
    h.window.spPath = 'RICS APC|Valuation';
    h.window.spPathHideUnrated = hide;
    await h.openTab('frameworks');
    h.window.dash.draw('pathwaytable');
    return [...h.doc.querySelectorAll('tbody[data-draw="pathwaytable"] td.sp-rule.sp-sub .sp-ruletext')].map((x) => x.firstChild.textContent);
  };
  h.log({ shown: await drawn(false), hidden: (await drawn(true)).filter((t) => !t.startsWith('At most one of these four')) });
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_group_minimums_read_a_rule_up_to_its_footnote(vault, tmp_path):  # noqa: F811
    cfg = configure(vault, "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n")
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    out = harness(tmp_path / "out", GROUPS, tmp_path)
    assert out["errors"] == []
    assert out["log"] == [{"markerNoPlus": "short", "markerPlus": "meets", "spacedPlus": "meets", "spacedShort": "short",
                           "plain": "meets", "ownMeets": "meets", "ownShort": "short", "ownFew": "short",
                           "otherGroup": "", "alpha": ["Accounting", "AI use", "client care", "Ethics"],
                           "alphaByRule": ["Alpha", "Zeta", "Data management", "Sustainability", "Auctioneering",
                                           "Inspection", "Valuation"],
                           "alphaBySub": ["Alpha", "Zeta", "Cadence", "Mapping"],
                           "alphaBySubNoRule": ["Alpha", "Zeta", "Mapping"],
                           "onlyOptional": "At most one of these two counts toward the Optional choices: A; B, and more.",
                           "onlyCore": "One of these two is needed for Core: A, B.",
                           "onlyAlone": "Only one of: A, B."},
                          {"eitherOne": "meets", "eitherNone": "short", "onlyOneCounts": "short",
                           "onlyOnePlusOther": "meets", "mustNotChosen": "meets", "mustBelow": "short", "mustAt": "meets",
                           "notCoreTwice": "short", "coreAndChoice": "meets", "higherIsTheChoice": "meets",
                           "isEither": [True, False]},
                          {"shown": ["At most one of these four counts toward the Optional choices: Accounting principles "
                                     "and procedures; Conflict avoidance, management and dispute resolution procedures; "
                                     "Data management; Sustainability."],
                           "hidden": []}]


SUBGROUPS = r"""
module.exports = async (h) => {
  h.window.spPath = 'Chan CXMDS|Managed data services professional';
  h.window.spPathHideUnrated = false;
  await h.openTab('frameworks');
  const kinds = (draw) => [...h.doc.querySelectorAll(`tbody[data-draw="${draw}"] tr`)].map((tr) => {
    const t = tr.textContent.replace(/\s+/g, ' ').trim();
    if (tr.querySelector('th.sp-group')) return 'G:' + tr.querySelector('.sp-glabel').firstChild.textContent;
    if (tr.querySelector('th.sp-subgroup')) return 'S:' + t;
    if (tr.querySelector('td.sp-rule')) return 'R:' + t.slice(0, 16);
    return 'c:' + tr.querySelector('th[scope="row"]').textContent;
  });
  const path = kinds('pathwaytable');
  const optional = path.slice(path.indexOf('G:Optional'));
  // a competency under a sub-group names its group and its sub-group among its headers
  const row = [...h.doc.querySelectorAll('tbody[data-draw="pathwaytable"] tr')].find((tr) => tr.dataset.key && tr.dataset.key.includes('Target data models'));
  const heads = row.cells[1].getAttribute('headers').split(' ').map((id) => h.doc.getElementById(id).textContent.replace(/\s+/g, ' ').trim());
  await h.openTab('competencydefs');
  const defs = kinds('deftable');
  h.log({ shape: optional.filter((k) => !k.startsWith('c:')), first: optional.slice(0, 5), last: optional[optional.length - 1],
    counts: [path.filter((k) => k.startsWith('c:')).length, optional.filter((k) => k.startsWith('c:')).length],
    heads, defs: defs.slice(defs.indexOf('G:Optional')).filter((k) => !k.startsWith('c:')), defRows: defs.filter((k) => k.startsWith('c:')).length,
    flag: h.text('tbody[data-draw="pathwaytable"] th.sp-group').pop() });
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_sub_groups_of_a_group_are_headed_under_its_one_rule(vault, tmp_path):  # noqa: F811
    """Chan CXMDS: Optional lists three specialisations as sub-groups. Each is headed once, under the group's rule,
    with its competencies alphabetical beneath it, on Competency frameworks and on Framework competency definitions; the group
    minimum is still judged on the whole group."""
    cfg = configure(vault, "frameworks:\n  chan-cxmds: {}\n")
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    out = harness(tmp_path / "out", SUBGROUPS, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    got = out["log"][0]
    subs = ["S:Client delivery and customer experience", "S:Data operations and quality", "S:Solutions and onboarding"]
    assert got["shape"] == ["G:Optional", "R:Six from this li"] + subs
    assert got["first"] == ["G:Optional", "R:Six from this li", subs[0], "c:Account governance and cadence",
                            "c:Account health and retention"]
    assert got["last"] == "c:Target data models" and got["counts"] == [54, 31]
    assert got["heads"][-2:] == ["Solutions and onboarding", "Target data models"] and got["heads"][-3].startswith("Optional")
    assert got["defs"] == ["G:Optional"] + subs and got["defRows"] == 54
    assert "As claimed: short" in got["flag"]


JOBSUBS = r"""
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
module.exports = async (h) => {
  await h.openTab('jobspecs');
  const kinds = () => [...h.doc.querySelectorAll('tbody[data-draw="jstable"] tr')].map((tr) => {
    if (tr.querySelector('th.sp-group')) return 'G:' + tr.querySelector('.sp-glabel').firstChild.textContent;
    if (tr.querySelector('th.sp-subgroup')) return 'S:' + tr.textContent.replace(/\s+/g, ' ').trim();
    return 'c:' + tr.querySelector('th[scope="row"]').firstChild.firstChild.textContent;
  });
  const score = kinds();
  await h.click('#js-edit');
  const pick = () => [...h.doc.querySelectorAll('tbody[data-draw="jspick"] tr')].map((tr) => [tr.cells[0].textContent, tr.cells[1].textContent.replace(/\s+/g, ' ').trim()]);
  const inSpec = pick();
  await h.select(h.doc.querySelector('#js-show'), 'all');
  await h.type('#js-search', 'solutions onboarding'); await wait(300);
  const found = pick();
  h.log({ score, inSpec, found: found.length, foundAll: found.every((x) => x[1].includes('Solutions and onboarding')),
    compare: h.text('[data-draw="jscompare"] tbody th') });
};
"""

JOBSUB_SPECS = """specs:
  lead:
    title: Lead
    next: head
    mandatory:
      - {ref: "Chan CXMDS: Submission cycle operations", level: L3}
      - {ref: "Chan CXMDS: Escalation management", level: L3}
    core:
      - {ref: "Chan CXMDS: Scope and change control", level: L2}
      - {ref: "RICS APC: Valuation", level: L2}
      - {ref: "Chan CXMDS: Exception triage and remediation", level: L2}
  head:
    title: Head
    mandatory:
      - {ref: "Chan CXMDS: Submission cycle operations", level: L3}
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_job_specs_show_each_competencys_specialisation(vault, tmp_path):  # noqa: F811
    """Job specs: a competency that sits in a sub-group of its framework (a specialisation) is listed under that
    sub-group's heading in the scorecard, after the section's other competencies; the spec editor and the comparison
    name the specialisation, and Search finds it. The sub-groups reach the page on the descriptions data."""
    cfg = configure(vault, "frameworks:\n  chan-cxmds: {}\n")
    (vault / "KG/Competencies/Job_Specs.yaml").write_text(JOBSUB_SPECS)
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    rows = list(csv.DictReader(open(tmp_path / "out/data/descriptions.csv", encoding="utf-8", newline="")))
    assert list(rows[0]) == db.fw.DESCRIPTION_COLUMNS + ["subgroup", "subgroup_order"]
    sub = {(r["framework"], r["name"]): (r["subgroup"], r["subgroup_order"]) for r in rows}
    assert sub[("Chan CXMDS", "Submission cycle operations")] == ("Data operations and quality", "2")
    assert sub[("Chan CXMDS", "Escalation management")] == ("", "") and sub[("RICS APC", "Valuation")] == ("", "")
    out = harness(tmp_path / "out", JOBSUBS, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    got = out["log"][0]
    assert got["score"] == [
        "G:Mandatory", "c:Escalation management", "S:Chan CXMDS: Data operations and quality 0 of 1 met",
        "c:Submission cycle operations",
        "G:Core", "c:Valuation", "S:Chan CXMDS: Data operations and quality 0 of 1 met", "c:Exception triage and remediation",
        "S:Chan CXMDS: Solutions and onboarding 0 of 1 met", "c:Scope and change control"]
    assert ["Submission cycle operations", "Chan CXMDS Data operations and quality"] in got["inSpec"]
    assert ["Escalation management", "Chan CXMDS"] in got["inSpec"]
    assert got["found"] == 11 and got["foundAll"]
    assert "Submission cycle operations (Chan CXMDS: Data operations and quality)" in got["compare"]
    assert "Escalation management (Chan CXMDS)" in got["compare"]


def test_library_rules_keep_their_sentences_apart():
    """The guides' layout puts "Plus, ..." and each footnote on a line of its own; the copy keeps that as punctuation."""
    lib = db.fw.load_library()
    rules = {r["rule"] for r in lib["rics-apc"]["rows"] if r.get("rule")}
    assert rules
    for rule in rules:
        assert not re.search(r"[a-z0-9] Plus, ", rule), rule[:120]          # "... to Level 3. Plus, one ..."
        assert not re.search(r" \* [A-Z]", rule), rule[:120]                 # a footnote starts " *If", not " * If"
        assert not re.search(r"Level \d (To achieve|Although) ", rule), rule[:120]


ASSESS = r"""
module.exports = async (h) => {
  const q = (s) => h.doc.querySelector(s);
  const shown = () => q('.sp').classList.contains('sp-assess');
  const row = () => [...h.doc.querySelectorAll('tbody[data-draw="alltable"] tr[data-key]')].find((t) => t.dataset.key === 'Leasing');
  const pick = () => q('#rating select[data-draw="assessorsel"]');
  const cfg = (k) => `#assessor-config [data-k="${k}"]`;
  const people = () => h.text('#assessor-config .sp-asrlist li .who');
  const saved = () => (h.store.get('settings/assessors') || {}).list;
  await h.openTab('rating');
  // no assessors yet: no dropdown, and the button opens Configuration at the assessors
  h.log({ shown: shown(), cell: row().querySelector('td.sp-as').textContent, pick: q('#rating .sp-asrpick').hidden, none: q('#rating .sp-asrnone').hidden });
  await h.click('#rating .sp-asrnone'); h.drawAll();
  h.log({ tab: q('.sp-tab[aria-selected="true"]').dataset.tab, panel: q('#configuration').hidden, empty: h.text('#assessor-config .sp-asrempty') });
  await h.click(cfg('add'));
  await h.click(cfg('save'));                                    // no name: nothing is saved
  h.log({ error: h.text('#assessor-config .sp-asrerr'), store: [...h.store.keys()] });
  await h.type('#asr-name', '  A.  Counsellor '); await h.type('#asr-role', 'APC counsellor');
  await h.click(cfg('save'));
  await h.click(cfg('add')); await h.type('#asr-name', 'a. counsellor'); await h.click(cfg('save'));   // the same name again
  h.log({ people: people(), saved: saved(), error: h.text('#assessor-config .sp-asrerr'), status: h.text('#assessor-config .sp-save span') });
  await h.type('#asr-name', 'Bo Manager'); await h.click(cfg('save'));
  await h.openTab('rating');
  h.log({ pick: q('#rating .sp-asrpick').hidden, none: q('#rating .sp-asrnone').hidden, options: [...pick().options].map((o) => o.text), shown: shown() });
  await h.select(pick(), 'a-counsellor');
  await h.select(row().querySelector('td.sp-as select'), 'advanced');
  await h.openTab('jobspecs');                                   // the same choice on every tab; a second assessor rates another competency
  h.log({ onJobspecs: q('#jobspecs select[data-draw="assessorsel"]').value });
  await h.select(q('#jobspecs select[data-draw="assessorsel"]'), 'bo-manager');
  await h.openTab('rating');
  // the second assessor's dropdown is their own rating: what the first gave is not shown while they rate
  h.log({ onRating: pick().value, bosOwn: row().querySelector('td.sp-as select').value });
  await h.select(row().querySelector('td.sp-as select'), 'aware');
  await h.click('#savebtn');
  const docs = [...h.store.keys()].filter((k) => k.startsWith('claims/')).sort().map((k) => [k, h.store.get(k)]);
  h.log({ docs: docs.map(([k, d]) => [k, d.to, d.by, d.byId, d.ckey]), first: h.store.get('claims/assessed--a-counsellor--Leasing'),
    claimed: row().querySelector('td:not(.sp-as) select').value, status: h.text('[data-draw="savestatus"]')[0] });
  await h.select(pick(), '');                                    // done: the level both support, and a mark that they differ
  const mark = row().querySelector('td.sp-as .sp-differ');
  h.log({ shown: shown(), cell: row().querySelector('td.sp-as .sp-pill').textContent.trim(), selects: row().querySelectorAll('select').length,
    mark: mark.textContent + (mark.querySelector('svg path') ? ' drawn' : ''), said: mark.getAttribute('aria-label'), who: row().querySelector('td.sp-as .sp-pill').title });
  await h.openTab('gaps');
  h.log({ differ: h.text('tbody[data-draw="assessordiff"] tr'), agree: q('.sp-empty[data-empty="assessordiff"]').hidden, one: q('.sp-empty[data-empty="assessorone"]').hidden });
  await h.openTab('jobspecs');
  await h.click('.sp-seg[data-basis="assessed"]');
  const held = [...h.doc.querySelectorAll('tbody[data-draw="jstable"] tr[data-key]')].map((t) => t.textContent.replace(/\s+/g, ' ').trim());
  h.log({ verdict: h.text('tbody[data-draw="jsverdict"] tr th'), leasing: held.find((t) => t.startsWith('Leasing/letting')) });
  // the first assessor comes round to the second's level: the difference goes
  await h.openTab('rating');
  await h.select(pick(), 'a-counsellor');
  h.log({ anns: row().querySelector('td.sp-as select').value });
  await h.select(row().querySelector('td.sp-as select'), 'aware');
  await h.select(pick(), '');
  h.log({ cell: row().querySelector('td.sp-as').textContent.trim() });
  await h.click('#discardbtn');
  // edit keeps the id; delete asks first, and a list put back to the settings file's own is withdrawn
  await h.openTab('configuration');
  await h.click(cfg('edit:a-counsellor')); await h.type('#asr-name', 'Ann Counsellor'); await h.click(cfg('save'));
  await h.click(cfg('delete:bo-manager'));
  h.log({ saved: saved(), ask: h.text('#assessor-config .ask') });
  await h.click(cfg('keep'));
  h.log({ people: people() });
  await h.click(cfg('delete:bo-manager')); await h.click(cfg('yes:bo-manager'));
  await h.click(cfg('delete:a-counsellor')); await h.click(cfg('yes:a-counsellor'));
  await h.openTab('rating');
  h.log({ settings: h.store.has('settings/assessors'), none: q('#rating .sp-asrnone').hidden, pick: q('#rating .sp-asrpick').hidden });
};
"""

FROMFILE = r"""
module.exports = async (h) => {
  const q = (s) => h.doc.querySelector(s);
  const cfg = (k) => `#assessor-config [data-k="${k}"]`;
  await h.openTab('configuration');
  h.log({ people: h.text('#assessor-config .sp-asrlist li .who'), status: h.text('#assessor-config .sp-save span'), reset: q(cfg('reset')).disabled });
  await h.click(cfg('add')); await h.type('#asr-name', 'Élodie Brûlé-Smith'); await h.click(cfg('save'));
  h.log({ saved: h.store.get('settings/assessors').list, status: h.text('#assessor-config .sp-save span'), reset: q(cfg('reset')).disabled });
  await h.openTab('rating');
  h.log({ options: [...q('#rating select[data-draw="assessorsel"]').options].map((o) => [o.value, o.text]) });
  await h.openTab('configuration');
  await h.click(cfg('reset'));
  h.log({ settings: h.store.has('settings/assessors'), people: h.text('#assessor-config .sp-asrlist li .who') });
};
"""

RATED = r"""
module.exports = async (h) => {
  await h.openTab('rating');
  const row = [...h.doc.querySelectorAll('tbody[data-draw="alltable"] tr[data-key]')].find((t) => t.dataset.key === 'Leasing');
  const pill = row.querySelector('td.sp-as .sp-pill');
  await h.openTab('jobspecs');
  h.log({ shown: h.doc.querySelector('.sp').classList.contains('sp-assess'), cell: pill.textContent, who: pill.title,
    selects: row.querySelectorAll('select').length, verdict: h.text('tbody[data-draw="jsverdict"] tr th'),
    bases: [...new Set(h.window.dash.data('job_spec_scores').data.map((r) => r.basis))] });
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_assessors_are_kept_on_configuration_and_picked_where_ratings_are_given(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    out = harness(tmp_path / "out", ASSESS, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    first, opened, unnamed, added, offered, other, own, saved, closed, gaps, scored, mine, agreed, edited, kept, emptied = out["log"]
    assert first == {"shown": False, "cell": "—", "pick": True, "none": False}     # no rating, no assessor: only the button
    assert opened == {"tab": "configuration", "panel": False, "empty": ["No assessors yet."]}
    assert unnamed == {"error": ["Give the assessor a name."], "store": []}
    one = {"id": "a-counsellor", "name": "A. Counsellor", "role": "APC counsellor"}
    assert added["people"] == ["A. CounsellorAPC counsellor"] and added["saved"] == [one]
    assert added["error"] == ["Another assessor is already called a. counsellor."]
    assert offered == {"pick": False, "none": True, "options": ["No one", "A. Counsellor (APC counsellor)", "Bo Manager"], "shown": False}
    assert other == {"onJobspecs": "a-counsellor"}
    assert own == {"onRating": "bo-manager", "bosOwn": ""}
    # each assessor's rating is its own saved change, under the assessor picked as it was made; the owner's claim stays
    assert [d[:4] for d in saved["docs"] if d[4] == "Leasing"] == [
        ["claims/assessed--a-counsellor--Leasing", "advanced", "A. Counsellor", "a-counsellor"],
        ["claims/assessed--bo-manager--Leasing", "aware", "Bo Manager", "bo-manager"]]
    assert len(saved["docs"]) == 2
    doc = saved["first"]
    assert (doc["field"], doc["note"], doc["from"], doc["title"]) == ("assessedLevel", "Leasing", "", "Rating by A. Counsellor: Leasing")
    assert saved["claimed"] == "practitioner" and saved["status"].startswith("Saved 2 changes.")
    # the assessed level is the lowest of the two, and the cell says they differ
    assert (closed["shown"], closed["cell"], closed["selects"], closed["mark"]) == (True, "L1 Aware", 1, "2 drawn")
    assert closed["said"].startswith("The assessors differ by 2 levels: A. Counsellor L3 Advanced (")
    assert closed["who"].split("\n")[1].startswith("Bo Manager L1 Aware (") and closed["who"].endswith(", saved")
    assert len(gaps["differ"]) == 1 and gaps["differ"][0].startswith("Leasing") and gaps["agree"] is True and gaps["one"] is True
    assert "L2 Practitioner" in gaps["differ"][0] and "A. Counsellor L3 Advanced" in gaps["differ"][0]      # the claim, then each rating
    assert [v.split(" (")[0] for v in scored["verdict"]] == ["As claimed", "As assessed", "As supported"]
    assert "Short" in scored["leasing"]                                  # L1 agreed against L2 required
    assert mine == {"anns": "advanced"} and agreed == {"cell": "L1 Aware"}       # once they agree the mark goes
    assert edited["saved"] == [{**one, "name": "Ann Counsellor"}, {"id": "bo-manager", "name": "Bo Manager", "role": ""}]
    assert edited["ask"] == ["Delete Bo Manager? The ratings Bo Manager gave stay, under this name."]
    assert kept == {"people": ["Ann CounsellorAPC counsellor", "Bo Manager"]}
    assert emptied == {"settings": False, "none": False, "pick": True}


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_the_settings_files_assessors_show_until_a_list_is_saved_on_the_dashboard(vault, tmp_path):  # noqa: F811
    cfg = configure(vault, "assessors:\n  dana-okafor: {name: Dana Okafor, role: APC counsellor}\n")
    out = tmp_path / "out"
    db.build(cfg, str(out), "on-request", TODAY)
    assert (out / "data/assessors.csv").read_text() == "id,name,role\ndana-okafor,Dana Okafor,APC counsellor\n"
    res = harness(out, FROMFILE, tmp_path)
    assert res["errors"] == [] and res["violations"] == []
    file, added, offered, back = res["log"]
    assert file == {"people": ["Dana OkaforAPC counsellor"], "status": ["Showing the assessors in your settings file."], "reset": True}
    dana = {"id": "dana-okafor", "name": "Dana Okafor", "role": "APC counsellor"}
    assert added["saved"] == [dana, {"id": "elodie-brule-smith", "name": "Élodie Brûlé-Smith", "role": ""}]
    assert added["status"] == ["Added Élodie Brûlé-Smith."] and added["reset"] is False
    assert offered["options"] == [["", "No one"], ["dana-okafor", "Dana Okafor (APC counsellor)"], ["elodie-brule-smith", "Élodie Brûlé-Smith"]]
    assert back == {"settings": False, "people": ["Dana OkaforAPC counsellor"]}


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_a_rating_already_in_the_notes_shows_who_gave_it_and_the_third_basis(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    # a rating already in the notes: the column, who gave it, and the third basis are there from the start
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\n'
          'claimedLevel: practitioner\nassessedLevel: aware\nassessedBy: A. Counsellor\nassessedOn: 2026-11-13\n'
          'externalRef: ["RICS APC 2025: Leasing/letting"]')
    db.build(cfg, str(tmp_path / "rated"), "on-request", TODAY)
    out = harness(tmp_path / "rated", RATED, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    (rated,) = out["log"]
    assert rated["shown"] is True and rated["cell"] == "L1 Aware" and rated["selects"] == 1
    assert rated["who"] == "Assessed by A. Counsellor on 2026-11-13"
    assert rated["bases"] == ["claimed", "assessed", "supported"] and len(rated["verdict"]) == 3


def test_the_record_guide_and_the_work_machine_prompt_are_whole_and_name_no_one():
    """The method for recording a job ships with the skill for any owner: the guide, the template and the prompt for a
    work machine each carry the HAM-Z parts, the metric as the gate, the fact-check and the sanitisation gate, and none
    of them names a real owner, employer or client."""
    skill = os.path.join(os.path.dirname(db.TEMPLATE), "..", "..")
    read = lambda *p: open(os.path.join(skill, *p), encoding="utf-8").read()  # noqa: E731
    guide, prompt, templates = read("references", "recording-experience.md"), read("assets", "prompts", "experience-update.md"), read("references", "templates.md")
    for text in (guide, prompt):
        for part in ("**H** Hard skill or tool", "**A** Action", "**M** Metric", "**Z** Process", "The metric is the gate", "hamz", "supporting"):
            assert part in text, part
        for gate in ("Work product:", "Internal identifiers:", "Credentials:", "Clients and counterparties:"):
            assert gate in text, gate
        assert "read-only" in text.lower() and "ledger" in text and "Contradicted" in text or "contradicted" in text
    assert "name: experience-update" in prompt and prompt.count("````") == 2 and "--newbuild" in prompt
    assert "## 7. Experience record" in templates and "<!-- src: report, Nov 2025; verified; hamz -->" in templates
    assert "references/recording-experience.md" in read("SKILL.md") and "assets/prompts/experience-update.md" in read("SKILL.md")
    for text in (guide, prompt, templates[templates.index("## 7. Experience record"):]):
        for name in ("Reggie", "Cherre", "RealPage", "GIC"):
            assert name not in text, name


PREREQ = r"""
module.exports = async (h) => {
  const q = (s) => h.doc.querySelector(s);
  const rows = () => h.text('tbody[data-draw="prereqtable"] tr');
  await h.openTab('gaps');
  h.log({ shown: q('.sp').classList.contains('sp-prereq'), rows: rows(), empty: q('.sp-empty[data-empty="prereqtable"]').hidden });
  // the prerequisite raised to the claim: the row leaves, and nothing was written for the reader
  const sels = h.doc.querySelectorAll('tbody[data-draw="prereqtable"] tr select');
  h.log({ selects: [...sels].map((s) => [s.value, s.getAttribute('aria-label')]) });
  await h.select(sels[1], 'practitioner');
  h.log({ rows: rows(), empty: q('.sp-empty[data-empty="prereqtable"]').hidden, staged: [...h.window.spStaged.keys()], store: [...h.store.keys()] });
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_a_claim_above_a_prerequisite_is_listed_on_rating_gaps_only_where_the_graph_has_prerequisites(vault, tmp_path):  # noqa: F811
    cfg = configure(vault)
    out = tmp_path / "plain"
    db.build(cfg, str(out), "on-request", TODAY)
    assert all(r["requires"] == [] for r in json.loads((out / "data/competencies.json").read_text()))
    res = harness(out, "module.exports = async (h) => { await h.openTab('gaps'); h.log({ shown: h.doc.querySelector('.sp').classList.contains('sp-prereq') }); };", tmp_path)
    assert res["errors"] == [] and res["log"] == [{"shown": False}]              # no prerequisites: the card stays out of view
    write(vault, "KG/Competencies/Lease_Law.md", 'nodeType: competency\nkind: knowledge\nbroader: ["[[Real_Property_Practice]]"]\nclaimedLevel: aware')
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\n'
          'claimedLevel: practitioner\nrequires: ["[[Lease_Law]]"]\nexternalRef: ["RICS APC 2025: Leasing/letting"]')
    out = tmp_path / "prereq"
    db.build(cfg, str(out), "on-request", TODAY)
    assert {r["note"]: r["requires"] for r in json.loads((out / "data/competencies.json").read_text())}["Leasing"] == ["Lease_Law"]
    res = harness(out, PREREQ, tmp_path)
    assert res["errors"] == [] and res["violations"] == []
    first, sels, fixed = res["log"]
    assert first["shown"] is True and first["empty"] is True and len(first["rows"]) == 1
    assert first["rows"][0].startswith("Leasing") and "Lease_Law" in first["rows"][0] and first["rows"][0].endswith("1")
    assert sels["selects"] == [["practitioner", "Claimed level for Leasing"], ["aware", "Claimed level for Lease_Law, which Leasing requires"]]
    assert fixed == {"rows": [], "empty": False, "staged": ["Lease_Law"], "store": []}


RELOAD = r"""
module.exports = async (h) => {
  const q = (s) => h.doc.querySelector(s);
  const bar = () => ({ hidden: q('#loadbar').hidden, off: q('#reloadbtn').disabled,
    says: ['load-failed', 'load-busy', 'load-again'].filter((id) => !q('#' + id).hidden) });
  const settle = async () => { h.drawAll(); await h.tick(); await h.tick(); };
  h.log({ files: h.window.spFiles, start: bar() });
  h.force('domains', 'error'); h.force('sectors', 'error'); await settle();
  h.log({ failed: bar(), mark: h.text('#domains .sp-fail') });
  await h.click('#reloadbtn');
  h.log({ asked: h.refreshed.slice(), busy: bar() });
  h.force('domains', 'loading'); h.force('sectors', 'loading'); await settle();
  h.log({ waiting: bar() });
  h.force('sectors', null); h.force('domains', 'error'); await settle();     // one came back, one failed again
  h.log({ again: bar(), said: h.text('[data-draw="announce"]')[0] });
  await h.click('#reloadbtn');
  h.force('domains', 'loading'); await settle();
  h.force('domains', null); await settle();
  h.log({ asked: h.refreshed.slice(), done: bar(), said: h.text('[data-draw="announce"]')[0],
    mark: h.text('#domains .sp-fail') });
  h.force('timeline', 'error'); await settle();                              // a later failure starts from the first sentence
  h.log({ later: bar() });
};
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_reload_data_asks_again_for_the_files_that_failed_and_only_those(vault, tmp_path):  # noqa: F811
    cfg = configure(vault, "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n")
    db.build(cfg, str(tmp_path / "out"), "on-request", TODAY)
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text())
    out = harness(tmp_path / "out", RELOAD, tmp_path)
    assert out["errors"] == [] and out["violations"] == []
    start, failed, pressed, waiting, again, done, later = out["log"]
    # the page's list of data files is the build's, so no file can fail without the bar
    assert sorted(start["files"]) == sorted(d["id"] for d in manifest["datasets"])
    assert start["start"] == {"hidden": True, "off": False, "says": ["load-failed"]}
    assert failed["failed"] == {"hidden": False, "off": False, "says": ["load-failed"]} and failed["mark"] == ["Failed to load"]
    assert pressed["asked"] == ["domains", "sectors"]                 # the two that failed, not the six that loaded
    assert pressed["busy"] == {"hidden": False, "off": True, "says": ["load-busy"]} == waiting["waiting"]
    assert again["again"] == {"hidden": False, "off": False, "says": ["load-again"]}
    assert again["said"] == "The data failed to load again."
    assert done["asked"] == ["domains", "sectors", "domains"]
    assert done["done"]["hidden"] is True and done["said"] == "Data reloaded." and done["mark"] == []
    assert later["later"] == {"hidden": False, "off": False, "says": ["load-failed"]}
