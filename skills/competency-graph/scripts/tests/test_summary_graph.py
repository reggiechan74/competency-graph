"""Tests for summary_graph.py. Run: python3 -m pytest scripts/tests -q"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import summary_graph as sg  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)


def s(v, disclosure="confidential"):
    return sg.Summary(str(v), str(v / "KG/Profile.md"), TODAY, disclosure)


def test_domain_rows_count_units_and_levels(vault):
    rows = {r["domain"]: r for r in s(vault).domains()}
    rp = rows["Real_Property_Practice"]
    assert rp["units"] == 2 and rp["organisations"] == 2 and rp["supported"] == "expert"
    assert rp["competencies"] >= 2


def test_disclosure_filter_recounts_before_levels(vault):
    full = {r["competency"]: r for r in s(vault).competencies()}
    public = {r["competency"]: r for r in s(vault, "public").competencies()}
    assert full["Real_Property_Valuation"]["units"] == 2
    # both valuation units are on-request: at `public` nothing is left to count
    assert "Real_Property_Valuation" not in public or public["Real_Property_Valuation"]["units"] == 0
    assert all(r["unit"] != "Experience_Artis" for r in s(vault, "public").timeline())


def test_confidential_child_is_not_counted_at_on_request(vault):
    write(vault, "KG/Evidence/Projects/Project_Secret.md", """
        nodeType: evidence
        evidenceType: project
        period: 2015
        disclosure: confidential
        partOf: "[[Experience_Artis]]"
        demonstrates: ["[[Finance]]"]
    """)
    summ = s(vault, "on-request")
    assert all(e != "KG/Evidence/Projects/Project_Secret.md" for e in summ.visible)
    assert summ.hidden_units == 0          # the unit (Artis) is still shown, the child is not


def test_fit_flags_over_claim(vault):
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nclaimedLevel: expert\nbroader: ["[[Real_Property_Practice]]"]')
    fits = {r["competency"]: r["fit"] for r in s(vault).competencies()}
    assert fits["Leasing"] == "over-claimed"


def test_cli_writes_row_files_to_outputs(vault, monkeypatch):
    (vault / "competency-graph.yaml").write_text("graphRoot: KG\nprofile: KG/Profile.md\n", encoding="utf-8")
    monkeypatch.chdir(vault)
    assert sg.main(["--today", TODAY.isoformat(), "--markdown"]) == 0
    out = vault / "KG/Outputs/2026-11-08_Graph_Summary_on-request"
    for name in ("domains", "competencies", "timeline", "sectors"):
        assert isinstance(json.loads((out / f"{name}.json").read_text()), list)
    assert (out / "summary.md").read_text().startswith("# Competency graph summary")


def test_timeline_uses_main_domain_only(vault):
    # Real_Property_Valuation's second parent is Finance's Valuation: its evidence stays in Real Property Practice's lane
    sm = s(vault)
    an = sm.an
    rpv = next(p for p in an.competencies if an.r.nodes[p].name == "Real_Property_Valuation")
    finance = next(p for p in an.domains if an.r.nodes[p].name == "Finance")
    units = {an.root[e] for e in an.competency_support[rpv]}
    only_rpv = [u for u in units if all(an.primary_domain.get(c) != finance
                                         for e in an.competency_support[rpv] if an.root[e] == u
                                         for c in an.links.get(e, {}).get("demonstrates", []))]
    doms = sm.unit_domains()
    assert only_rpv and all(finance not in doms[u] for u in only_rpv)


def test_competency_rows_list_every_competency_with_its_parent(vault):
    rows = {r["note"]: r for r in s(vault, "public").competencies()}
    # no evidence at `public`, no claim: still listed (the dashboard's Rate tab shows it), with 0 units
    assert "Real_Property_Valuation" in rows and rows["Real_Property_Valuation"]["units"] == 0
    assert rows["Real_Property_Valuation"]["fit"] == "no-evidence"
    assert rows["Real_Property_Valuation"]["parent"] == "Real_Property_Practice"   # the first (main) `broader`
    assert all(r["rank"] not in ("branch", "domain") for r in rows.values())


# ---- disclosure: confidential evidence must not raise a level or add led years (SKILL.md rule 7)

def rows_by(summ, kind):
    return {r["note"] if kind == "competencies" else r["domain"]: r for r in getattr(summ, kind)()}


def test_confidential_led_unit_does_not_raise_a_cached_level(vault):
    # Real_Property_Valuation is claimed, so check_graph's run() caches its level from ALL evidence; with Hydro One
    # confidential, only Artis's led work is shareable: one led unit, so practitioner, not expert
    text = (vault / "Experience/Experience_HydroOne.md").read_text()
    (vault / "Experience/Experience_HydroOne.md").write_text(text.replace("disclosure: on-request", "disclosure: confidential"))
    full = rows_by(s(vault, "confidential"), "competencies")["Real_Property_Valuation"]
    assert full["supported"] == "expert" and full["ledUnits"] == 2          # the fixture really does raise it
    row = rows_by(s(vault, "on-request"), "competencies")["Real_Property_Valuation"]
    assert row["supported"] == "practitioner"
    assert row["ledUnits"] == 1 and row["ledYears"] == 9.1               # Artis 2012-06 to 2021-07 only
    assert "advanced" == row["nextLevel"] and "1 led unit(s)" in row["missing"]
    dom = rows_by(s(vault, "on-request"), "domains")["Real_Property_Practice"]
    assert dom["supported"] == "practitioner" and dom["ledYears"] == 9.1


def test_confidential_only_led_work_adds_no_led_years(vault):
    write(vault, "KG/Competencies/Negotiation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]')
    write(vault, "KG/Evidence/Projects/Project_Artis_Deal.md", """
        nodeType: evidence
        evidenceType: project
        period: 2016
        partOf: "[[Experience_Artis]]"
        demonstrates: ["[[Negotiation]]"]
        disclosure: on-request
    """)
    write(vault, "Experience/Experience_Hidden.md", """
        organization: Hidden Co
        tenure: 2000-01 – 2009-12
        nodeType: evidence
        evidenceType: role
        demonstratesLed: ["[[Negotiation]]"]
        anchor: crm/someone
        disclosure: confidential
    """)
    full = rows_by(s(vault, "confidential"), "competencies")["Negotiation"]
    assert full["ledUnits"] == 1 and full["ledYears"] == 10.0             # counted for the owner's own eyes
    summ = s(vault, "on-request")
    row = rows_by(summ, "competencies")["Negotiation"]
    assert row["supported"] == "practitioner" and row["units"] == 1
    assert row["ledUnits"] == 0 and row["ledYears"] == 0 and row["first"] == "2012-06-11"
    dom = rows_by(summ, "domains")["Real_Property_Practice"]
    assert dom["ledYears"] <= dom["years"] and dom["first"] == "2012-06-11"


def test_on_request_rows_equal_a_vault_without_the_confidential_notes(vault):
    # the strongest form of the rule: at `on-request`, every row is what it would be if the confidential notes
    # didn't exist (only the hidden-unit count differs)
    write(vault, "Experience/Experience_Hidden.md", """
        organization: Hidden Co
        tenure: 2000-01 – 2011-12
        nodeType: evidence
        evidenceType: role
        sector: ["[[Sector_22_Utilities]]"]
        demonstratesLed: ["[[Real_Property_Valuation]]", "[[Leasing]]", "[[Valuation]]"]
        recognition: [award]
        anchor: crm/someone
        disclosure: confidential
    """)
    write(vault, "KG/Evidence/Projects/Project_Artis_Secret.md", """
        nodeType: evidence
        evidenceType: project
        period: 2020
        partOf: "[[Experience_Artis]]"
        demonstratesLed: ["[[Leasing]]"]
        recognition: [publication]
        disclosure: confidential
    """)
    def snapshot():
        summ = s(vault, "on-request")
        return summ.domains(), summ.competencies(), summ.timeline(), summ.sectors()
    with_hidden = snapshot()
    (vault / "Experience/Experience_Hidden.md").unlink()
    (vault / "KG/Evidence/Projects/Project_Artis_Secret.md").unlink()
    assert with_hidden == snapshot()


def test_rows_carry_the_assessors_rating_beside_the_claim(vault):
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nclaimedLevel: expert\n'
          'assessedLevel: L2\nassessedBy: A. Counsellor\nassessedOn: 2026-11-13\nbroader: ["[[Real_Property_Practice]]"]')
    rows = {r["competency"]: r for r in s(vault).competencies()}
    got = rows["Leasing"]
    assert (got["claimed"], got["assessed"], got["assessedBy"], got["assessedOn"]) == (
        "expert", "practitioner", "A. Counsellor", "2026-11-13")
    assert got["assessments"] == ["A. Counsellor | practitioner | 2026-11-13"] and got["assessedSpread"] == 0
    assert rows["Valuation"]["assessed"] == "" and rows["Valuation"]["assessedBy"] == ""
    assert rows["Valuation"]["assessments"] == [] and rows["Valuation"]["assessedSpread"] == 0
    # several assessors: each rating is carried, the assessed level is the lowest, and the spread says they differ
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nclaimedLevel: expert\n'
          'assessments: ["A. Counsellor | L2 | 2026-11-13", "Bo Manager | expert | 2026-11-14"]\nbroader: ["[[Real_Property_Practice]]"]')
    got = {r["competency"]: r for r in s(vault).competencies()}["Leasing"]
    assert (got["assessed"], got["assessedSpread"], got["assessedBy"], got["assessedOn"]) == (
        "practitioner", 2, "A. Counsellor, Bo Manager", "2026-11-14")
    assert got["assessments"] == ["A. Counsellor | practitioner | 2026-11-13", "Bo Manager | expert | 2026-11-14"]


def test_sector_rows_carry_the_sectors_code_and_no_sector_has_none(vault):
    rows = s(vault).sectors()
    by_sector = {r["sector"]: r["code"] for r in rows}
    assert by_sector and all(isinstance(c, str) for c in by_sector.values())
    assert by_sector.get("No sector", "") == ""
    coded = {name: c for name, c in by_sector.items() if name != "No sector"}
    assert coded and all(c for c in coded.values())            # every sector note in the sample vault has a code
    assert set(coded.values()) <= {"22", "53"}
