"""Tests for edit_links.py. Run: python3 -m pytest scripts/tests -q"""
import os
import sys
import textwrap

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import edit_links as el  # noqa: E402


def write(v, rel, front, body="Body text.\n"):
    p = v / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\n" + textwrap.dedent(front).strip() + "\n---\n\n" + body, encoding="utf-8")
    return p


def fm(path):
    return yaml.safe_load(path.read_text().split("---\n", 2)[1])


@pytest.fixture
def v(tmp_path):
    write(tmp_path, "S/Leasing.md", "nodeType: competency\nkind: practice\nrank: domain")
    write(tmp_path, "S/Excel.md", "nodeType: competency\nkind: tool\nrank: domain")
    write(tmp_path, "S/VTS.md", "nodeType: competency\nkind: tool\nrank: domain")
    write(tmp_path, "S/Sector_53.md", 'nodeType: sector\ncode: "53"')
    write(tmp_path, "Exp/Role.md", """
        title: Role – with dash
        organization: Org
        tenure: 2012-06-11 – 2021-07
        status: current
        related: ["[[Elsewhere]]"]
        nodeType: evidence
        evidenceType: role
        demonstrates: ["[[Leasing]]", "[[VTS]]"]   # keep this comment
        disclosure: on-request
        lastUpdated: 2026-01-01
    """, body="# Heading\n\nBody with demonstrates: [\"[[Fake]]\"] in prose.\n")
    write(tmp_path, "Exp/Block.md", """
        nodeType: evidence
        evidenceType: project
        period: 2020
        demonstrates:
          - "[[Leasing]]"
        disclosure: public
    """)
    write(tmp_path, "Exp/Bare.md", "nodeType: evidence\nevidenceType: project\nperiod: 2020\ndisclosure: public")
    write(tmp_path, "Exp/Child.md", "nodeType: evidence\nevidenceType: project\nperiod: 2020\ndisclosure: public")
    write(tmp_path, "Plain.md", "title: not a graph note")
    return tmp_path


def run(v, *args):
    return el.main(["--vault", str(v), *args])


def test_add_extends_never_replaces(v):
    """Regression: the 2026-11-08 one-off script replaced lists instead of extending them."""
    before = (v / "Exp/Role.md").read_text()
    assert run(v, "--apply", "add", "Role", "demonstrates", "Excel") == 0
    after = (v / "Exp/Role.md").read_text()
    assert fm(v / "Exp/Role.md")["demonstrates"] == ["[[Leasing]]", "[[VTS]]", "[[Excel]]"]
    assert "# keep this comment" in after
    assert after.split("---\n", 2)[2] == before.split("---\n", 2)[2]           # body untouched
    b, a = fm(v / "Exp/Role.md"), yaml.safe_load(before.split("---\n", 2)[1])
    assert {k: x for k, x in a.items() if k != "demonstrates"} == {k: x for k, x in b.items() if k != "demonstrates"}


def test_dry_run_writes_nothing(v):
    before = (v / "Exp/Role.md").read_text()
    assert run(v, "add", "Role", "demonstrates", "Excel") == 0
    assert (v / "Exp/Role.md").read_text() == before


def test_duplicates_skipped(v, capsys):
    assert run(v, "--apply", "add", "Role", "demonstrates", "[[VTS]]", "Excel", "excel") == 0
    assert fm(v / "Exp/Role.md")["demonstrates"] == ["[[Leasing]]", "[[VTS]]", "[[Excel]]"]
    assert "skipped" in capsys.readouterr().out


def test_block_list_and_absent_field(v):
    assert run(v, "--apply", "add", "Block", "demonstrates", "Excel") == 0
    assert fm(v / "Exp/Block.md")["demonstrates"] == ["[[Leasing]]", "[[Excel]]"]
    assert run(v, "--apply", "add", "Bare", "demonstrates", "Excel", "VTS") == 0
    assert fm(v / "Exp/Bare.md")["demonstrates"] == ["[[Excel]]", "[[VTS]]"]


def test_remove(v):
    assert run(v, "--apply", "remove", "Role", "demonstrates", "VTS") == 0
    assert fm(v / "Exp/Role.md")["demonstrates"] == ["[[Leasing]]"]
    assert run(v, "remove", "Role", "demonstrates", "Excel") == 1          # not present


@pytest.mark.parametrize("args", [
    ["add", "Role", "demonstrates", "Nope"],                  # broken target
    ["add", "Role", "demonstrates", "Sector_53"],             # wrong type for field
    ["add", "Role", "broader", "Leasing"],                    # not a link field for evidence
    ["add", "Plain", "demonstrates", "Leasing"],              # not a graph note
])
def test_refusals(v, args):
    before = (v / "Exp/Role.md").read_text()
    assert run(v, "--apply", *args) == 1
    assert (v / "Exp/Role.md").read_text() == before


def test_ambiguous_target_refused(v):
    write(v, "Other/Excel.md", "title: another Excel")
    assert run(v, "--apply", "add", "Role", "demonstrates", "Excel") == 1


def test_single_link_field(v):
    assert run(v, "--apply", "add", "Child", "partOf", "Role") == 0
    assert fm(v / "Exp/Child.md")["partOf"] == "[[Role]]"
    assert run(v, "--apply", "add", "Child", "partOf", "Block") == 1        # already set


def test_plan_is_all_or_nothing(v, tmp_path_factory):
    plan = tmp_path_factory.mktemp("p") / "plan.yaml"
    plan.write_text(yaml.safe_dump([
        {"note": "Role", "field": "demonstrates", "add": ["Excel"]},
        {"note": "Role", "field": "sector", "add": ["Sector_53"]},
        {"note": "Block", "field": "demonstrates", "add": ["Nope"]},         # fails
    ]))
    before = {p: (v / p).read_text() for p in ("Exp/Role.md", "Exp/Block.md")}
    assert run(v, "--apply", "plan", str(plan)) == 1
    assert {p: (v / p).read_text() for p in before} == before
    plan.write_text(yaml.safe_dump([
        {"note": "Role", "field": "demonstrates", "add": ["Excel"]},
        {"note": "Role", "field": "sector", "add": ["Sector_53"]},           # chained on same file
    ]))
    assert run(v, "--apply", "--touch", "2026-11-08", "plan", str(plan)) == 0
    d = fm(v / "Exp/Role.md")
    assert d["demonstrates"][-1] == "[[Excel]]" and d["sector"] == ["[[Sector_53]]"]
    assert str(d["lastUpdated"]) == "2026-11-08"


def test_set_controlled_field(v):
    assert run(v, "--apply", "set", "Leasing", "claimedLevel", "expert") == 0
    assert fm(v / "S/Leasing.md")["claimedLevel"] == "expert"
    assert run(v, "--apply", "set", "Leasing", "claimedLevel", "practitioner") == 0     # replace existing
    assert fm(v / "S/Leasing.md")["claimedLevel"] == "practitioner"
    assert run(v, "--apply", "set", "Leasing", "claimedLevel", "guru") == 1             # not controlled value
    assert run(v, "--apply", "set", "Leasing", "kind", "tool") == 1                     # not settable
    assert run(v, "--apply", "set", "Role", "claimedLevel", "expert") == 1              # wrong nodeType


def test_worksheet_plan_skips_blank(v, tmp_path_factory):
    plan = tmp_path_factory.mktemp("w") / "w.yaml"
    plan.write_text(yaml.safe_dump([
        {"note": "Leasing", "field": "claimedLevel", "set": "expert", "title": "Leasing", "units": 3},
        {"note": "Excel", "field": "claimedLevel", "set": ""},
    ]))
    before = (v / "S/Excel.md").read_text()
    assert run(v, "--apply", "plan", str(plan)) == 0
    assert fm(v / "S/Leasing.md")["claimedLevel"] == "expert"
    assert (v / "S/Excel.md").read_text() == before


def test_set_anchor_free_text_is_quoted(v):
    val = 'CRM: NE-ALEEXA-001 (Alex Example, supervisor) # not a comment'
    assert run(v, "--apply", "set", "Role", "anchor", val) == 0
    assert fm(v / "Exp/Role.md")["anchor"] == val          # replaced existing anchor, colon and hash survive
    assert run(v, "--apply", "set", "Bare", "anchor", "https://example.org/x") == 0
    assert fm(v / "Exp/Bare.md")["anchor"] == "https://example.org/x"
    assert run(v, "--apply", "set", "Leasing", "anchor", "x") == 1     # competencies have no anchor field


def test_apply_and_touch_accepted_after_subcommand(v):
    # flags after the subcommand work the same as before it
    assert run(v, "add", "Bare", "demonstrates", "Excel", "--apply") == 0
    assert "[[Excel]]" in str(fm(v / "Exp/Bare.md")["demonstrates"])
    # without --apply anywhere it stays a dry run
    assert run(v, "add", "Child", "demonstrates", "Excel") == 0
    assert "demonstrates" not in fm(v / "Exp/Child.md")


def test_recognition_words_add_and_remove(tmp_path):
    v = tmp_path
    (v / "E").mkdir()
    (v / "E/Role.md").write_text("---\nnodeType: evidence\nevidenceType: role\nperiod: 2020\ndisclosure: public\n---\nBody\n")
    assert run(v, "--apply", "add", "Role", "recognition", "teaching", "assessing") == 0
    assert fm(v / "E/Role.md")["recognition"] == ["teaching", "assessing"]
    assert run(v, "--apply", "add", "Role", "recognition", "famous") == 1
    assert run(v, "--apply", "remove", "Role", "recognition", "teaching") == 0
    assert fm(v / "E/Role.md")["recognition"] == ["assessing"]
    assert (v / "E/Role.md").read_text().endswith("---\nBody\n")


def test_empty_plan_entries_are_skipped(tmp_path):
    v = tmp_path
    (v / "E").mkdir()
    (v / "E/Role.md").write_text("---\nnodeType: evidence\nevidenceType: role\nperiod: 2020\ndisclosure: public\n---\nBody\n")
    plan = v / "plan.yaml"
    plan.write_text("- {note: Role, field: recognition, add: []}\n- {note: Role, field: demonstratesLed, add: []}\n")
    before = (v / "E/Role.md").read_text()
    assert run(v, "--apply", "plan", str(plan)) == 0
    assert (v / "E/Role.md").read_text() == before


def test_external_ref_and_aliases_are_free_text(v):
    p = v / "S/Leasing.md"
    assert run(v, "add", "Leasing", "externalRef", "RICS APC 2025: Leasing/letting", "--apply") == 0
    assert run(v, "add", "Leasing", "aliases", "Leasing", "Letting", "--apply") == 0
    assert fm(p)["externalRef"] == ["RICS APC 2025: Leasing/letting"]
    assert fm(p)["aliases"] == ["Leasing", "Letting"]
    assert run(v, "remove", "Leasing", "aliases", "Letting", "--apply") == 0
    assert fm(p)["aliases"] == ["Leasing"]
    assert run(v, "add", "Leasing", "externalRef", "  ", "--apply") == 1          # empty string refused
    assert run(v, "add", "Role", "externalRef", "x", "--apply") == 1              # not a field for evidence


def test_set_title_and_level_code(v):
    p = v / "S/Leasing.md"
    assert run(v, "set", "Leasing", "title", "Leasing/letting", "--apply") == 0
    assert fm(p)["title"] == "Leasing/letting"
    assert run(v, "set", "Leasing", "claimedLevel", "L3", "--apply") == 0
    assert fm(p)["claimedLevel"] == "advanced"
    assert run(v, "set", "Leasing", "claimedLevel", "L3 Expert", "--apply") == 1


def test_unset_claimed_level(v, tmp_path_factory):
    assert run(v, "set", "Leasing", "claimedLevel", "L3", "--apply") == 0
    plan = tmp_path_factory.mktemp("p") / "plan.yaml"
    plan.write_text("- {note: Leasing, field: claimedLevel, unset: true}\n")
    assert run(v, "plan", str(plan), "--apply") == 0
    assert "claimedLevel" not in fm(v / "S/Leasing.md")
    plan.write_text("- {note: Leasing, field: title, unset: true}\n")
    assert run(v, "plan", str(plan), "--apply") == 1


def test_set_keeps_the_comment_on_the_field_line(v):
    p = write(v, "Exp/Undated.md", "nodeType: evidence\nevidenceType: project\nperiod: 2020   # date not recorded; bounded by role\n"
              'anchor: "a # b"   # the register\ndisclosure: public')
    assert run(v, "set", "Undated", "period", "2021", "--apply") == 0
    assert run(v, "set", "Undated", "anchor", "ID-7", "--apply") == 0
    text = p.read_text()
    assert "period: 2021   # date not recorded; bounded by role\n" in text
    assert "anchor: ID-7   # the register\n" in text


@pytest.mark.parametrize("field,value,stored", [
    ("period", "2021", 2021),                       # the spec's bare year, read as text by the checker
    ("period", "2021-03", "2021-03"),
    ("period", "2019-01 – 2021-03-04", "2019-01 – 2021-03-04"),
    ("anchor", "12345", "12345"),                   # stays a string: quoted
    ("anchor", "true", "true"),
    ("anchor", "https://example.org/x#frag", "https://example.org/x#frag"),
])
def test_set_takes_values_yaml_reads_as_numbers_dates_or_booleans(v, field, value, stored):
    assert run(v, "set", "Bare", field, value, "--apply") == 0
    assert fm(v / "Exp/Bare.md")[field] == stored


def test_set_refuses_a_value_that_spans_lines_and_a_plan_entry_that_is_no_mapping(v, capsys):
    write(v, "S/Folded.md", "nodeType: competency\nkind: practice\ntitle: >\n  A folded\n  title")
    before = (v / "S/Folded.md").read_text()
    assert run(v, "set", "Folded", "title", "New", "--apply") == 1
    assert "spans several lines" in capsys.readouterr().err and (v / "S/Folded.md").read_text() == before
    plan = v / "plan.yaml"
    plan.write_text("- just a string\n")
    assert run(v, "plan", str(plan), "--apply") == 1
    assert "REFUSED" in capsys.readouterr().err


def test_each_assessors_rating_is_kept_and_one_assessors_new_rating_replaces_only_their_own(v, tmp_path_factory):
    p = v / "S/Leasing.md"
    assert run(v, "set", "Leasing", "claimedLevel", "L2", "--apply") == 0
    plan = tmp_path_factory.mktemp("p") / "plan.yaml"
    plan.write_text('- {note: Leasing, field: assessedLevel, set: L3, assessedBy: "A. Counsellor", assessedOn: 2026-11-13}\n'
                    '- {note: Leasing, field: assessedLevel, set: L2, assessedBy: Bo Manager, assessedOn: 2026-11-10}\n'
                    '- {note: Leasing, field: assessedLevel, set: "", assessedBy: Nobody}\n')        # a blank worksheet row
    assert run(v, "plan", str(plan), "--apply") == 0
    got = fm(p)
    assert got["assessments"] == ["A. Counsellor | advanced | 2026-11-13", "Bo Manager | practitioner | 2026-11-10"]
    assert got["claimedLevel"] == "practitioner" and "assessedLevel" not in got                # the claim is not touched
    assert 'assessments: ["A. Counsellor | advanced | 2026-11-13", "Bo Manager | practitioner | 2026-11-10"]\n' in p.read_text()
    # the same assessor again: their rating is replaced, the other's stays
    assert run(v, "assess", "Leasing", "L4", "--by", "a. counsellor", "--on", "2026-11-14", "--apply") == 0
    assert fm(p)["assessments"] == ["Bo Manager | practitioner | 2026-11-10", "a. counsellor | expert | 2026-11-14"]
    assert run(v, "assess", "Sector_53", "L1", "--by", "Bo Manager", "--apply") == 0          # sectors are rated too; today
    rated = fm(v / "S/Sector_53.md")["assessments"]
    assert len(rated) == 1 and rated[0].startswith("Bo Manager | aware | 20") and len(rated[0].split(" | ")[2]) == 10
    # what is refused: a rating with no assessor, a level off the scale, a date that is not a day, a name with a bar,
    # the old fields set on their own
    before = p.read_text()
    for bad in ('{note: Leasing, field: assessedLevel, set: L3}', '{note: Leasing, field: assessedLevel, set: master, assessedBy: X, assessedOn: 2026-11-13}',
                '{note: Leasing, field: assessedLevel, set: L3, assessedBy: X, assessedOn: last week}',
                '{note: Leasing, field: assessedLevel, set: L3, assessedBy: "X | Y", assessedOn: 2026-11-13}',
                '{note: Leasing, field: assessedLevel, unset: true, assessedBy: Nobody}'):
        plan.write_text(f"- {bad}\n")
        assert run(v, "plan", str(plan), "--apply") == 1, bad
    assert run(v, "set", "Leasing", "assessedBy", "Someone", "--apply") == 1 and run(v, "set", "Leasing", "assessedLevel", "L1", "--apply") == 1
    assert p.read_text() == before
    # one assessor's rating withdrawn, then every one
    assert run(v, "assess", "Leasing", "none", "--by", "Bo Manager", "--apply") == 0
    assert fm(p)["assessments"] == ["a. counsellor | expert | 2026-11-14"]
    plan.write_text("- {note: Leasing, field: assessedLevel, unset: true}\n")
    assert run(v, "plan", str(plan), "--apply") == 0
    assert fm(p)["assessments"] == [] and fm(p)["claimedLevel"] == "practitioner"


def test_a_rating_kept_the_old_way_moves_into_the_list_with_the_first_new_one(v):
    p = v / "S/Leasing.md"
    old = p.read_text()
    p.write_text(old.replace("---\n", "---\nassessedLevel: L2   # the counsellor\nassessedBy: A. Counsellor\nassessedOn: 2026-11-01\n", 1))
    assert run(v, "assess", "Leasing", "advanced", "--by", "Bo Manager", "--on", "2026-11-14", "--apply") == 0
    got = fm(p)
    assert got["assessments"] == ["A. Counsellor | practitioner | 2026-11-01", "Bo Manager | advanced | 2026-11-14"]
    assert not {"assessedLevel", "assessedBy", "assessedOn"} & set(got)
    assert {k: w for k, w in got.items() if k != "assessments"} == yaml.safe_load(old.split("---\n", 2)[1])   # nothing else changed
    # the old rating's own assessor rating again: the old one is replaced, not kept beside the new
    p.write_text(old.replace("---\n", "---\nassessedLevel: aware\nassessedBy: A. Counsellor\nassessedOn: 2026-11-01\n", 1))
    assert run(v, "assess", "Leasing", "L3", "--by", "A. Counsellor", "--on", "2026-11-14", "--apply") == 0
    assert fm(p)["assessments"] == ["A. Counsellor | advanced | 2026-11-14"]
