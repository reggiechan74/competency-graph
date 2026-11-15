"""Tests for job_specs.py: the file, the scoring, the merge of specs saved on the dashboard, and the page's scoring
(window.spJob in assets/dashboard/index.html) against this script's. Run: python3 -m pytest scripts/tests -q"""
import json
import os
import random
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_graph as cg  # noqa: E402
import job_specs as js  # noqa: E402
import kg_config as kc  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "dashboard", "index.html")

SPECS = """\
specs:
  manager:
    title: Manager, Acquisition
    next: senior
    mandatory:
      - {ref: "RICS APC: Client care", level: L2}
    core:
      - {ref: "RICS APC 2025: Valuation", level: L3}
      - {ref: "RICS APC: Leasing/letting", level: L2}
    optional:
      - {ref: "CFA CBOK: Alternative Investments", level: L1}
  senior:
    title: Senior Manager, Acquisition
    exceeds: 10
    mandatory:
      - {ref: "RICS APC: Client care", level: L3}
    core:
      - {ref: "RICS APC: Valuation", level: L4}
"""


def spec(rows, probation=80, exceeds=20, next_=""):
    return {"id": "s", "title": "S", "note": "", "next": next_, "probation": probation, "exceeds": exceeds,
            "rows": [{"section": s, "order": i, "framework": "F", "name": n, "required": r}
                     for i, (s, n, r) in enumerate(rows, 1)]}


def look(levels):
    return lambda f, n: levels.get(n, 0)


@pytest.fixture
def cfgvault(vault):  # noqa: F811
    (vault / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nprofile: KG/Profile.md\n")
    (vault / "KG/Competencies/Job_Specs.yaml").write_text(SPECS)
    return vault


def test_file_reads_and_validates_against_the_library(cfgvault):
    cfg = kc.read_config(str(cfgvault / kc.CONFIG_NAME))
    specs = js.load_specs(cfg.job_specs_file)
    assert list(specs) == ["manager", "senior"]
    m = specs["manager"]
    assert m["probation"] == 80 and m["exceeds"] == 20 and specs["senior"]["exceeds"] == 10
    assert [(r["section"], r["framework"], r["name"], r["required"]) for r in m["rows"]][:2] == [
        ("mandatory", "RICS APC", "Client care", "L2"), ("core", "RICS APC", "Valuation", "L3")]   # the year is dropped
    assert js.validate(specs, js.fw.library_for(cfg)) == []


@pytest.mark.parametrize("raw, words", [
    ({"title": "X", "core": [{"ref": "RICS APC: Valuation", "level": "L5"}]}, "not one of L1-L4"),
    ({"title": "X", "core": [{"ref": "Valuation", "level": "L2"}]}, "needs its framework"),
    ({"title": "X", "core": [{"ref": "A: B", "level": "L2"}], "optional": [{"ref": "A: B", "level": "L1"}]}, "one section"),
    ({"core": [{"ref": "A: B", "level": "L2"}]}, "needs a `title`"),
    ({"title": "X"}, "lists no competencies"),
    ({"title": "X", "probation": 0, "core": [{"ref": "A: B", "level": "L2"}]}, "above 0"),
    ({"title": "X", "colour": "red", "core": [{"ref": "A: B", "level": "L2"}]}, "unknown key"),
])
def test_malformed_specs_are_refused(raw, words):
    with pytest.raises(js.SpecError, match=words):
        js.normalise("x", raw)
    with pytest.raises(js.SpecError, match="lowercase"):
        js.normalise("Bad Id", {"title": "X", "core": [{"ref": "A: B", "level": "L2"}]})


def test_validate_finds_unknown_competencies_and_bad_next(cfgvault):
    cfg = kc.read_config(str(cfgvault / kc.CONFIG_NAME))
    lib = js.fw.library_for(cfg)
    specs = {"a": js.normalise("a", {"title": "A", "next": "b", "core": [{"ref": "RICS APC: Astrology", "level": "L2"}]}),
             "b": js.normalise("b", {"title": "B", "next": "a", "core": [{"ref": "RICS APC: Valuation", "level": "L2"}]}),
             "c": js.normalise("c", {"title": "C", "next": "zz", "core": [{"ref": "RICS APC: Valuation", "level": "L2"}]})}
    p = js.validate(specs, lib)
    assert any("Astrology is not in the library" in x for x in p)
    assert any("loop" in x for x in p) and any("'zz', which is not a spec" in x for x in p)


def test_score_worked_example():
    # Core asks Valuation L3, Leasing L2, GIS L1, PM L1; the graph holds Valuation L4 and Leasing L2
    s = js.score(spec([("core", "Valuation", "L3"), ("core", "Leasing", "L2"), ("core", "GIS", "L1"),
                       ("core", "PM", "L1")]), look({"Valuation": 4, "Leasing": 2}))
    assert (s["breadth"], s["breadthTarget"], s["breadthPct"]) == (5, 7, 71)
    assert (s["depth"], s["depthTarget"], s["depthPct"]) == (12, 14, 85)      # rounded down
    assert s["above"] == 18 and s["band"] == "below" and s["kind"] == "deep-narrow" and s["missing"] == 2
    assert js.diagnosis(s).startswith("Deep but narrow")


def test_a_level_above_never_fills_a_gap_and_the_gate_wins():
    s = js.score(spec([("mandatory", "Ethics", "L3"), ("core", "Valuation", "L1")]), look({"Ethics": 2, "Valuation": 4}))
    assert s["gate"] == "not-met" and s["band"] == "mandatory-not-met" and s["gateShort"] == 1
    assert s["depth"] == 3 + 1 and s["above"] == 26        # Valuation L4 against L1: 27 - 1, kept apart


def test_bands_and_exceeds():
    rows = [("mandatory", "A", "L2"), ("core", "B", "L2"), ("core", "C", "L1")]
    assert js.score(spec(rows), look({"A": 2, "B": 2, "C": 1}))["band"] == "baseline"
    assert js.score(spec(rows), look({"A": 2, "B": 1, "C": 1}))["band"] == "below"        # depth 5/7 = 71%
    assert js.score(spec(rows, probation=70), look({"A": 2, "B": 1, "C": 1}))["band"] == "probation"
    # depth target 7; 20% of it is 1.4: one level above on C (3 - 1 = 2) makes Exceeds role
    assert js.score(spec(rows), look({"A": 2, "B": 2, "C": 2}))["band"] == "exceeds"
    # optional credit doesn't count toward Exceeds
    assert js.score(spec(rows + [("optional", "D", "L1")]), look({"A": 2, "B": 2, "C": 1, "D": 4}))["band"] == "baseline"
    assert js.score(spec([("optional", "D", "L1")]), look({}))["band"] == "no-requirements"


def test_broad_shallow_and_even():
    rows = [("core", "A", "L3"), ("core", "B", "L3"), ("core", "C", "L1"), ("core", "D", "L1")]
    s = js.score(spec(rows), look({"A": 2, "B": 2, "C": 1, "D": 1}))       # breadth 6/8, depth 8/20
    assert s["kind"] == "broad-shallow" and js.diagnosis(s).startswith("Broad but shallow")
    s = js.score(spec([("core", "A", "L2"), ("core", "B", "L2")]), look({"A": 2}))
    assert s["kind"] == "even"


def test_promotion_needs_baseline_and_the_next_roles_gate_and_floor():
    specs = {"m": {**spec([("mandatory", "A", "L2"), ("core", "B", "L2")], next_="s"), "id": "m", "title": "M"},
             "s": {**spec([("mandatory", "A", "L3"), ("core", "B", "L3")]), "id": "s", "title": "S"}}
    p = js.promotion(specs["m"], specs, look({"A": 3, "B": 2}))
    assert p["ready"] is False                                       # next: B depth 3/9 is under its floor
    assert js.promotion(specs["m"], specs, look({"A": 3, "B": 3}))["ready"] is True
    assert js.promotion(specs["m"], specs, look({"A": 2, "B": 3}))["ready"] is False   # next role's gate not met
    assert js.promotion(specs["s"], specs, look({})) is None


def test_merge_adds_changes_and_deletes_then_reads_back(cfgvault, tmp_path):
    cfg = kc.read_config(str(cfgvault / kc.CONFIG_NAME))
    exp = tmp_path / "export"
    exp.mkdir()
    (exp / "manager.json").write_text(json.dumps({"id": "manager", "title": "Manager, Acquisition (2027)", "probation": 75,
        "rows": [{"section": "core", "order": 2, "framework": "RICS APC", "name": "Valuation", "required": "L2"},
                 {"section": "mandatory", "order": 1, "framework": "RICS APC", "name": "Client care", "required": "L3"}]}))
    (exp / "senior.json").write_text(json.dumps({"id": "senior", "title": "Senior Manager", "deleted": True}))
    (exp / "director.json").write_text(json.dumps({"id": "director", "data": {"title": "Director", "rows": [
        {"section": "core", "order": 1, "framework": "CFA CBOK", "name": "Alternative Investments", "required": "L2"}]}}))
    assert js.main(["--vault", str(cfgvault), "merge", "--from", str(exp)]) == 0          # dry run
    assert "Senior Manager" in (cfgvault / "KG/Competencies/Job_Specs.yaml").read_text()
    assert js.main(["--vault", str(cfgvault), "merge", "--from", str(exp), "--apply"]) == 0
    specs = js.load_specs(cfg.job_specs_file)
    assert list(specs) == ["manager", "director"]
    m = specs["manager"]
    assert m["title"] == "Manager, Acquisition (2027)" and m["probation"] == 75 and m["next"] == ""
    assert [(r["section"], r["name"], r["required"]) for r in m["rows"]] == [("mandatory", "Client care", "L3"),
                                                                            ("core", "Valuation", "L2")]
    assert js.render_yaml(specs) == (cfgvault / "KG/Competencies/Job_Specs.yaml").read_text()
    assert js.load_specs(cfg.job_specs_file) == specs


def test_merge_refuses_a_spec_that_leaves_the_file_invalid(cfgvault, tmp_path):
    exp = tmp_path / "export"
    exp.mkdir()
    (exp / "x.json").write_text(json.dumps({"id": "x", "title": "X", "rows": [
        {"section": "core", "framework": "RICS APC", "name": "Astrology", "required": "L2"}]}))
    before = (cfgvault / "KG/Competencies/Job_Specs.yaml").read_text()
    assert js.main(["--vault", str(cfgvault), "merge", "--from", str(exp), "--apply"]) == 1
    assert (cfgvault / "KG/Competencies/Job_Specs.yaml").read_text() == before


def test_build_writes_the_dashboards_copy(cfgvault):
    assert js.main(["--vault", str(cfgvault), "build"]) == 0
    import csv
    rows = list(csv.DictReader(open(cfgvault / "KG/Competencies/Job_Specs.csv")))
    assert rows[0]["spec"] == "manager" and rows[0]["section"] == "mandatory" and rows[0]["next"] == "senior"
    assert len(rows) == 6 and set(rows[0]) == set(js.CSV_COLUMNS)


def test_score_cli_reads_the_graphs_levels(cfgvault, capsys):
    write(cfgvault, "KG/Competencies/Valuation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]\n'
          'claimedLevel: advanced\nexternalRef: ["RICS APC 2025: Valuation"]')
    assert js.main(["--vault", str(cfgvault), "score", "manager", "--today", TODAY.isoformat()]) == 0
    out = capsys.readouterr().out
    assert "RICS APC: Valuation" in out and "hold L3" in out and "Mandatory gate: NOT MET (1 short)" in out


def test_checker_reports_a_broken_specs_file(cfgvault):
    (cfgvault / "KG/Competencies/Job_Specs.yaml").write_text(SPECS.replace("Leasing/letting", "Astrology"))
    cfg = kc.read_config(str(cfgvault / kc.CONFIG_NAME))
    r = cg.check(str(cfgvault), str(cfgvault / "KG/Profile.md"), TODAY, cfg)
    assert [e for e in r.errors if e.code == "jobspecs" and "Astrology" in e.message]
    (cfgvault / "KG/Competencies/Job_Specs.yaml").write_text(SPECS)
    r = cg.check(str(cfgvault), str(cfgvault / "KG/Profile.md"), TODAY, cfg)
    assert not [e for e in r.errors if e.code == "jobspecs"]


# ------------------------------------------------------------------ the page scores the same way

def page_scoring_block() -> str:
    text = open(TEMPLATE, encoding="utf-8").read()
    m = re.search(r"/\* kg:jobscore \*/(.*?)/\* /kg:jobscore \*/", text, re.S)
    assert m, "the template has no kg:jobscore block"
    return m.group(1)


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_page_and_script_score_alike(tmp_path):
    rnd = random.Random(7)
    cases = []
    for _ in range(300):
        n = rnd.randint(1, 9)
        rows = [(rnd.choice(js.SECTIONS), f"C{i}", rnd.choice(list(js.LEVELS))) for i in range(n)]
        levels = {f"C{i}": rnd.randint(0, 4) for i in range(n) if rnd.random() < 0.8}
        cases.append({"spec": spec(rows, probation=rnd.choice([60, 80, 95]), exceeds=rnd.choice([0, 10, 20, 50])),
                      "levels": levels})
    (tmp_path / "cases.json").write_text(json.dumps(cases))
    (tmp_path / "run.js").write_text("global.window = {};\n" + page_scoring_block() + """
const cases = require(process.argv[2]);
const out = cases.map((c) => { const s = window.spJob.score(c.spec, (f, n) => c.levels[n] || 0);
  delete s.rows; s.diagnosis = window.spJob.diagnosis(s); return s; });
console.log(JSON.stringify(out));
""")
    got = json.loads(subprocess.run(["node", str(tmp_path / "run.js"), str(tmp_path / "cases.json")],
                                    capture_output=True, text=True, check=True).stdout)
    for c, page in zip(cases, got):
        mine = js.score(c["spec"], look(c["levels"]))
        mine["diagnosis"] = js.diagnosis(mine)
        mine.pop("rows")
        assert page == json.loads(json.dumps(mine)), c


def test_score_on_the_assessors_ratings(cfgvault, capsys):
    write(cfgvault, "KG/Competencies/Valuation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]\n'
          'claimedLevel: advanced\nassessedLevel: practitioner\nassessedBy: A. Counsellor\nassessedOn: 2026-11-13\n'
          'externalRef: ["RICS APC 2025: Valuation"]')
    args = ["--vault", str(cfgvault), "score", "manager", "--today", TODAY.isoformat()]
    assert js.main(args + ["--basis", "assessed"]) == 0
    out = capsys.readouterr().out
    assert "scored on assessed levels" in out and "hold L2" in out and "hold L3" not in out
    assert js.main(args) == 0 and "hold L3" in capsys.readouterr().out          # the claim still scores as claimed
    # two assessors who differ: the score takes the level both support, the lower
    write(cfgvault, "KG/Competencies/Valuation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]\n'
          'claimedLevel: advanced\nassessments: ["A. Counsellor | L4 | 2026-11-13", "Bo Manager | L1 | 2026-11-14"]\n'
          'externalRef: ["RICS APC 2025: Valuation"]')
    assert js.main(args + ["--basis", "assessed"]) == 0
    out = capsys.readouterr().out
    assert "hold L1" in out and "hold L4" not in out
