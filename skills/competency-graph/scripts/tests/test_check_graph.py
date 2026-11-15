"""Tests for check_graph.py. Run: python3 -m pytest scripts/tests -q"""
import datetime as dt
import os
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_graph as cg  # noqa: E402

TODAY = dt.date(2026, 11, 8)


def write(vault, rel, front, body="Body.\n"):
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + textwrap.dedent(front).strip() + "\n---\n\n" + body, encoding="utf-8")
    return path


@pytest.fixture
def vault(tmp_path):
    """A small, valid graph: 2 domains, a two-parent competency, a role with a project, a credential."""
    v = tmp_path
    write(v, "KG/Competencies/Real_Property_Practice.md", "nodeType: competency\nkind: practice\nrank: domain")
    write(v, "KG/Competencies/Finance.md", "nodeType: competency\nkind: practice\nrank: domain")
    write(v, "KG/Competencies/Valuation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]')
    write(v, "KG/Competencies/Real_Property_Valuation.md", """
        nodeType: competency
        kind: practice
        rank: discipline
        broader: ["[[Real_Property_Practice]]", "[[Valuation]]"]
        claimedLevel: expert
    """)
    write(v, "KG/Competencies/Leasing.md", """
        nodeType: competency
        kind: practice
        broader: ["[[Real_Property_Practice]]"]
        claimedLevel: practitioner
    """)
    write(v, "KG/Sectors/Sector_53_Real_Estate.md", 'nodeType: sector\ncode: "53"')
    write(v, "KG/Sectors/Sector_22_Utilities.md", 'nodeType: sector\ncode: "22"')
    write(v, "Experience/Experience_Artis.md", """
        title: Artis REIT
        organization: Artis
        tenure: 2012-06-11 – 2021-07
        status: current
        related: ["[[Not_In_Vault]]"]
        nodeType: evidence
        evidenceType: role
        sector: ["[[Sector_53_Real_Estate]]"]
        demonstrates: ["[[Leasing]]"]
        demonstratesLed: ["[[Real_Property_Valuation]]"]
        recognition: [teaching]
        anchor: crm/referee
        disclosure: on-request
    """)
    write(v, "Experience/Experience_HydroOne.md", """
        organization: Hydro One
        tenure: 2025-02 – 2026-08
        nodeType: evidence
        evidenceType: engagement
        via: LandSolutions Inc.
        sector: ["[[Sector_22_Utilities]]"]
        demonstratesLed: ["[[Real_Property_Valuation]]"]
        anchor: crm/manager
        disclosure: on-request
    """)
    write(v, "KG/Evidence/Projects/Project_Artis_Paper.md", """
        nodeType: evidence
        evidenceType: publication
        period: 2019-03
        partOf: "[[Experience_Artis]]"
        demonstrates: ["[[Leasing]]"]
        anchor: https://example.org/paper
        disclosure: public
    """)
    write(v, "KG/Profile.md", "title: Profile\nkgStaleYears: 5\nkgPeriodAliases: [tenure]")
    return v


def run(v):
    return cg.check(str(v), str(v / "KG/Profile.md"), TODAY)


def codes(findings):
    return sorted({f.code for f in findings})


def find(findings, code):
    return [f for f in findings if f.code == code]


# --------------------------------------------------------------------------- baseline

def test_clean_fixture_has_no_errors(vault):
    r = run(vault)
    assert r.errors == [], [f.line() for f in r.errors]
    assert r.stats["competencies"] == 5 and r.stats["sectors"] == 2 and r.stats["evidence"] == 3


def test_reused_file_fields_are_ignored(vault):
    # Experience_Artis has `status: current` and a broken `related` link; neither is a graph field for evidence.
    r = run(vault)
    assert not [f for f in r.errors if "Not_In_Vault" in f.message or "status" in f.message]


def test_tenure_alias_is_read_as_period(vault):
    r = run(vault)
    assert not find(r.errors, "required")


# --------------------------------------------------------------------------- errors

def test_broken_link(vault):
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Estate]]"]')
    assert any("broken link [[Real_Estate]]" in f.message for f in run(vault).errors)


def test_ambiguous_filename(vault):
    write(vault, "Elsewhere/Leasing.md", "title: unrelated note")
    r = run(vault)
    assert find(r.errors, "name")
    assert any("ambiguous link [[Leasing]]" in f.message for f in r.errors)


def test_cycle(vault):
    write(vault, "KG/Competencies/Valuation.md",
          'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Valuation]]"]')
    assert find(run(vault).errors, "cycle")


def test_orphan(vault):
    write(vault, "KG/Competencies/Negotiation.md", "nodeType: competency\nkind: practice")
    assert [f for f in run(vault).errors if f.code == "orphan" and "Negotiation" in f.path]


def test_wrong_target_type(vault):
    write(vault, "KG/Competencies/Leasing.md",
          'nodeType: competency\nkind: practice\nbroader: ["[[Sector_53_Real_Estate]]"]')
    assert find(run(vault).errors, "target")


def test_unquoted_and_duplicate_sector_codes(vault):
    write(vault, "KG/Sectors/Sector_22_Utilities.md", "nodeType: sector\ncode: 22")
    write(vault, "KG/Sectors/Sector_53_Dup.md", 'nodeType: sector\ncode: "53"')
    assert set(codes(run(vault).errors)) >= {"code", "code-dup"}


def test_nested_object_rejected(vault):
    write(vault, "KG/Evidence/Projects/Repo_x.md", """
        nodeType: evidence
        evidenceType: project
        period: 2024-01 – present
        demonstrates:
          - competency: "[[Leasing]]"
            depth: led
        disclosure: public
    """)
    assert find(run(vault).errors, "nested")


def test_controlled_values_and_required(vault):
    write(vault, "KG/Competencies/Leasing.md",
          'nodeType: competency\nkind: hobby\nbroader: ["[[Real_Property_Practice]]"]')
    write(vault, "KG/Evidence/Projects/Repo_y.md", 'nodeType: evidence\nevidenceType: project\ndemonstrates: ["[[Leasing]]"]')
    r = run(vault)
    assert find(r.errors, "value")
    assert {f.message for f in find(r.errors, "required") if "Repo_y" in f.path} == {
        "missing required field `period`", "missing required field `disclosure`"}


@pytest.mark.parametrize("period", ["June 2012 – 2021", "2012-06 - 2021-07", "2021-07 – 2012-06", "Fall 2015", "15-06"])
def test_bad_periods(vault, period):
    write(vault, "KG/Evidence/Projects/Repo_z.md",
          f'nodeType: evidence\nevidenceType: project\nperiod: "{period}"\ndemonstrates: ["[[Leasing]]"]\n'
          "disclosure: public")
    assert find(run(vault).errors, "period")


@pytest.mark.parametrize("period", ["2026-08-31 – present", "2012-06-11 – 2021-07", "2018-10", "2026-08-31",
                                    "2015", "2018 – 2021-03", "2020 – 2021-06"])
def test_good_periods(vault, period):
    write(vault, "KG/Evidence/Projects/Repo_z.md",
          f"nodeType: evidence\nevidenceType: project\nperiod: {period}\ndemonstrates: [\"[[Leasing]]\"]\n"
          "disclosure: public\nanchor: x")
    assert not find(run(vault).errors, "period")


# --------------------------------------------------------------------------- counting

def test_partof_collapses_to_one_unit(vault):
    # Leasing: Artis role + paper inside Artis = 1 unit of led work. Claim expert -> unsupported.
    write(vault, "KG/Competencies/Leasing.md", """
        nodeType: competency
        kind: practice
        broader: ["[[Real_Property_Practice]]"]
        claimedLevel: expert
    """)
    for name in ("Experience/Experience_Artis.md", "KG/Evidence/Projects/Project_Artis_Paper.md"):
        p = vault / name
        p.write_text(p.read_text().replace('demonstrates: ["[[Leasing]]"]', 'demonstratesLed: ["[[Leasing]]"]', 1)
                     .replace('demonstratesLed: ["[[Real_Property_Valuation]]"]',
                              'demonstratesLed: ["[[Real_Property_Valuation]]", "[[Leasing]]"]'))
    r = run(vault)
    hits = [f for f in find(r.warnings, "unsupported") if "Leasing" in f.path]
    assert hits and "1 led unit(s)" in hits[0].message


def test_expert_supported_by_two_orgs(vault):
    # Real_Property_Valuation: Artis + Hydro One = 2 units, 2 organisations.
    r = run(vault)
    assert not [f for f in find(r.warnings, "unsupported") if "Real_Property_Valuation" in f.path]


def test_expert_same_org_needs_anchor(vault):
    for name in ("Experience_Artis", "Experience_HydroOne"):
        p = vault / "Experience" / f"{name}.md"
        text = p.read_text().replace("organization: Hydro One", "organization: Artis")
        p.write_text("\n".join(line for line in text.splitlines() if not line.startswith("anchor:")) + "\n")
    hits = [f for f in find(run(vault).warnings, "unsupported") if "Real_Property_Valuation" in f.path]
    assert hits and "1 organisation(s) and no anchor" in hits[0].message


def test_rollup_to_ancestors(vault):
    write(vault, "KG/Competencies/Finance.md", "nodeType: competency\nkind: practice\nrank: domain\nclaimedLevel: practitioner")
    # Finance has no direct evidence but Real_Property_Valuation -> Valuation -> Finance does.
    assert not [f for f in find(run(vault).warnings, "unsupported") if "Finance" in f.path]


# --------------------------------------------------------------------------- recency

def test_stale_practice_not_rescued_by_project(vault):
    # Leasing evidence: Artis (ended 2021-07) + a recent repo NOT partOf anything.
    write(vault, "KG/Evidence/Projects/Repo_lease.md", """
        nodeType: evidence
        evidenceType: project
        period: 2026-01 – present
        demonstrates: ["[[Leasing]]"]
        anchor: https://github.com/x/y
        disclosure: public
    """)
    r = cg.check(str(vault), str(vault / "KG/Profile.md"), dt.date(2026, 11, 8))
    stale = [f for f in find(r.warnings, "stale") if "Leasing" in f.path]
    assert stale and "2021-07-31" in stale[0].message


def test_stale_threshold_from_profile(vault):
    write(vault, "KG/Profile.md", "title: Profile\nkgStaleYears: 10\nkgPeriodAliases: [tenure]")
    assert not [f for f in find(run(vault).warnings, "stale") if "Leasing" in f.path]


def test_tool_recency_counts_projects(vault):
    write(vault, "KG/Competencies/Real_Property_Tools.md", """
        nodeType: competency
        kind: tool
        rank: branch
        broader: ["[[Real_Property_Practice]]"]
    """)
    write(vault, "KG/Competencies/VTS.md", """
        nodeType: competency
        kind: tool
        broader: ["[[Real_Property_Tools]]"]
        claimedLevel: practitioner
    """)
    write(vault, "KG/Evidence/Projects/Repo_vts.md", """
        nodeType: evidence
        evidenceType: project
        period: 2026-01 – present
        demonstrates: ["[[VTS]]"]
        anchor: https://github.com/x/vts
        disclosure: public
    """)
    assert not [f for f in run(vault).warnings if "VTS" in f.path]


def test_credential_never_counts_for_recency(vault):
    write(vault, "KG/Evidence/Credentials/Credential_FRICS.md", """
        nodeType: evidence
        evidenceType: credential
        period: 2018-10 – present
        organization: RICS
        demonstrates: ["[[Leasing]]"]
        anchor: member-id
        disclosure: public
    """)
    stale = [f for f in find(run(vault).warnings, "stale") if "Leasing" in f.path]
    assert stale  # still stale: credential "present" does not reset practice recency


# --------------------------------------------------------------------------- warnings

def test_work_evidence_warnings(vault):
    write(vault, "Experience/Experience_NewCo.md", """
        tenure: 2009-09 – 2010-09
        nodeType: evidence
        evidenceType: role
        demonstrates: ["[[Leasing]]"]
        disclosure: on-request
    """)
    w = [f.code for f in run(vault).warnings if "NewCo" in f.path]
    assert set(w) >= {"sector", "organization", "anchor"}


# --------------------------------------------------------------------------- insights

def test_insights(vault):
    r = run(vault)
    bridging = r.insights["Competencies bridging two or more domains"]
    assert any("Real_Property_Valuation" in s for s in bridging)
    # a child of a two-parent competency is not re-reported
    write(vault, "KG/Competencies/Corridor_Valuation.md",
          'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Valuation]]"]')
    assert not any("Corridor" in s for s in run(vault).insights["Competencies bridging two or more domains"])
    cross = r.insights["Practices evidenced in two or more top-level sectors"]
    assert any("Real_Property_Valuation" in s and "Sector_22_Utilities" in s and "Sector_53_Real_Estate" in s
               for s in cross)


def test_cli_exit_codes_and_outputs(vault, tmp_path_factory):
    out = tmp_path_factory.mktemp("out")
    rc = cg.main(["--vault", str(vault), "--profile", str(vault / "KG/Profile.md"), "--today", "2026-11-08",
                  "--report", str(out / "r.md"), "--json", str(out / "g.json")])
    assert rc == 0
    assert "# Competency graph check (2026-11-08)" in (out / "r.md").read_text()
    assert '"specVersion": "0.5"' in (out / "g.json").read_text()
    write(vault, "KG/Competencies/Orphan.md", "nodeType: competency\nkind: practice")
    assert cg.main(["--vault", str(vault), "--report", str(out / "r2.md")]) == 1


def test_year_precision_bounds():
    assert cg.parse_period("2018 – 2021-03", TODAY) == (dt.date(2018, 1, 1), dt.date(2021, 3, 31))
    assert cg.parse_period("2015", TODAY) == (dt.date(2015, 1, 1), dt.date(2015, 12, 31))


def test_activity_counts_for_practice_recency(vault):
    write(vault, "KG/Evidence/Activity_Assessor.md", """
        nodeType: evidence
        evidenceType: activity
        period: 2012-08 – present
        organization: RICS
        demonstrates: ["[[Leasing]]"]
        anchor: assessor-record
        disclosure: public
    """)
    r = run(vault)
    assert not [f for f in find(r.warnings, "stale") if "Leasing" in f.path]
    assert not [f for f in r.warnings if "Activity_Assessor" in f.path]


def test_activity_needs_organization_not_sector(vault):
    write(vault, "KG/Evidence/Activity_X.md", """
        nodeType: evidence
        evidenceType: activity
        period: 2019-05 – present
        demonstrates: ["[[Leasing]]"]
        anchor: x
        disclosure: public
    """)
    codes_x = {f.code for f in run(vault).warnings if "Activity_X" in f.path}
    assert codes_x == {"organization"}


def test_anchor_warning_only_on_unit_roots(vault):
    write(vault, "KG/Evidence/Projects/Project_Internal.md", """
        nodeType: evidence
        evidenceType: project
        period: 2015
        partOf: "[[Experience_Artis]]"
        demonstrates: ["[[Leasing]]"]
        disclosure: confidential
    """)
    assert not [f for f in run(vault).warnings if f.code == "anchor" and "Project_Internal" in f.path]


def test_domain_pairs(vault):
    write(vault, "KG/Evidence/Projects/Repo_pair.md", """
        nodeType: evidence
        evidenceType: project
        period: 2026-01 – present
        demonstrates: ["[[Valuation]]", "[[Leasing]]"]
        anchor: https://github.com/x/pair
        disclosure: public
    """)
    pairs = run(vault).insights["Domain pairs (independent units evidencing both)"]
    assert pairs == ["Finance × Real_Property_Practice: 1 — Repo_pair"]


def test_related_stored_twice_warns(vault):
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\nrelated: ["[[Valuation]]"]')
    write(vault, "KG/Competencies/Valuation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]\nrelated: ["[[Leasing]]"]')
    assert len(find(run(vault).warnings, "related-twice")) == 1


def test_project_only_practice_falls_back_to_projects(vault):
    write(vault, "KG/Competencies/Machine_Learning.md", """
        nodeType: competency
        kind: practice
        broader: ["[[Finance]]"]
        claimedLevel: practitioner
    """)
    write(vault, "KG/Evidence/Projects/Repo_ml.md", """
        nodeType: evidence
        evidenceType: project
        period: 2025-10 – 2025-11
        demonstrates: ["[[Machine_Learning]]"]
        anchor: https://github.com/x/ml
        disclosure: public
    """)
    an = cg.Analyzer(str(vault), cg.load_settings(str(vault / "KG/Profile.md")), TODAY); an.run()
    p = next(q for q in an.r.nodes if an.r.nodes[q].name == "Machine_Learning")
    assert an.recency_of(p) == (dt.date(2025, 11, 30), "project-only")
    assert not [f for f in find(an.r.warnings, "stale") if "Machine_Learning" in f.path]


def test_expert_min_years(vault):
    # Real_Property_Valuation: Artis 2012-06-11..2021-07 + Hydro One 2025-02..2026-08 -> ~10.7 years
    write(vault, "KG/Profile.md", "title: Profile\nkgStaleYears: 5\nkgPeriodAliases: [tenure]\nkgExpertMinYears: 12")
    hits = [f for f in find(run(vault).warnings, "unsupported") if "Real_Property_Valuation" in f.path]
    assert hits and "supports L3 Advanced" in hits[0].message and "needs 12" in hits[0].message
    write(vault, "KG/Profile.md", "title: Profile\nkgStaleYears: 5\nkgPeriodAliases: [tenure]")   # default 10
    assert not [f for f in find(run(vault).warnings, "unsupported") if "Real_Property_Valuation" in f.path]
    an = cg.Analyzer(str(vault), cg.load_settings(str(vault / "KG/Profile.md")), TODAY); an.run()
    p = next(q for q in an.r.nodes if an.r.nodes[q].name == "Real_Property_Valuation")
    assert 10.5 < an.years_of(p) < 11


# --------------------------------------------------------------------------- levels (spec §3.5)

def level(v, name):
    an = cg.Analyzer(str(v), cg.load_settings(str(v / "KG/Profile.md")), TODAY)
    an.run()
    return an.supports_level(next(p for p in an.r.nodes if an.r.nodes[p].name == name))


def test_four_levels(vault):
    assert level(vault, "Real_Property_Valuation") == "expert"     # 2 led units, 2 orgs, 10.7 yrs, teaching
    assert level(vault, "Leasing") == "practitioner"               # delivered, never led
    p = vault / "Experience/Experience_Artis.md"
    p.write_text(p.read_text().replace("recognition: [teaching]\n", ""))
    assert level(vault, "Real_Property_Valuation") == "advanced"   # no outside recognition


def test_course_or_credential_alone_is_aware(vault):
    write(vault, "KG/Competencies/Tax.md", 'nodeType: competency\nkind: knowledge\nbroader: ["[[Finance]]"]\nclaimedLevel: practitioner')
    write(vault, "KG/Evidence/Credentials/Credential_Tax.md", """
        nodeType: evidence
        evidenceType: credential
        period: 2015-06
        demonstrates: ["[[Tax]]"]
        disclosure: public
    """)
    assert level(vault, "Tax") == "aware"
    hits = [f for f in find(run(vault).warnings, "unsupported") if "Tax" in f.path]
    assert hits and "courses and credentials alone" in hits[0].message


def _short_job(vault, name, period, org="Acme", comp="Data_Entry"):
    write(vault, f"Experience/{name}.md", f"""
        organization: {org}
        tenure: {period}
        nodeType: evidence
        evidenceType: role
        sector: ["[[Sector_53_Real_Estate]]"]
        demonstrates: ["[[{comp}]]"]
        anchor: crm/referee
        disclosure: on-request
    """)


def test_practitioner_needs_six_months_of_delivered_work(vault):
    write(vault, "KG/Competencies/Data_Entry.md",
          'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]\nclaimedLevel: practitioner')
    _short_job(vault, "Experience_Temp", "2026-08-31 – 2026-11-08")            # just over two months
    assert level(vault, "Data_Entry") == "aware"
    hits = [f for f in find(run(vault).warnings, "unsupported") if "Data_Entry" in f.path]
    assert hits and "supports L1 Aware" in hits[0].message
    assert "2.3 months of delivered work, needs 6" in hits[0].message
    an = cg.Analyzer(str(vault), cg.load_settings(str(vault / "KG/Profile.md")), TODAY); an.run()
    d = an.level_detail(next(p for p in an.r.nodes if an.r.nodes[p].name == "Data_Entry"))
    assert d["next"] == "practitioner" and d["workMonths"] == 2.3              # the next level is L2, not L3
    _short_job(vault, "Experience_Temp", "2026-01 – 2026-06")                   # six calendar months exactly
    assert level(vault, "Data_Entry") == "practitioner"
    assert not [f for f in find(run(vault).warnings, "unsupported") if "Data_Entry" in f.path]
    _short_job(vault, "Experience_Temp", "2026-01-02 – 2026-06")                # a day short
    assert level(vault, "Data_Entry") == "aware"


def test_practitioner_months_add_up_across_units_and_merge_overlaps(vault):
    write(vault, "KG/Competencies/Data_Entry.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]')
    _short_job(vault, "Experience_Temp_A", "2024-01 – 2024-03", org="A")
    assert level(vault, "Data_Entry") == "aware"
    _short_job(vault, "Experience_Temp_B", "2024-02 – 2024-04", org="B")       # overlaps: Jan-Apr is four months
    assert level(vault, "Data_Entry") == "aware"
    _short_job(vault, "Experience_Temp_C", "2025-07 – 2025-08", org="C")       # four and two, apart
    assert level(vault, "Data_Entry") == "practitioner"


def test_a_project_inside_a_role_counts_the_roles_months(vault):
    # the fixture's paper is dated one month, inside the nine-year Artis role: the unit is the role
    write(vault, "KG/Competencies/Technical_Writing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]')
    p = vault / "KG/Evidence/Projects/Project_Artis_Paper.md"
    p.write_text(p.read_text().replace('["[[Leasing]]"]', '["[[Leasing]]", "[[Technical_Writing]]"]'))
    assert level(vault, "Technical_Writing") == "practitioner"
    # the same one-month project standing alone is its own unit, and too short
    p.write_text(p.read_text().replace('partOf: "[[Experience_Artis]]"\n', ""))
    assert level(vault, "Technical_Writing") == "aware"


def test_practitioner_months_come_from_the_profile(vault):
    write(vault, "KG/Competencies/Data_Entry.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]')
    _short_job(vault, "Experience_Temp", "2026-01 – 2026-08")                   # eight months
    assert level(vault, "Data_Entry") == "practitioner"
    base = "title: Profile\nkgStaleYears: 5\nkgPeriodAliases: [tenure]\n"
    write(vault, "KG/Profile.md", base + "kgPractitionerMinMonths: 12")
    assert level(vault, "Data_Entry") == "aware"
    _short_job(vault, "Experience_Temp", "2026-11-01 – 2026-11-08")
    write(vault, "KG/Profile.md", base + "kgPractitionerMinMonths: 0")         # 0 switches the rule off
    assert level(vault, "Data_Entry") == "practitioner"


def test_six_months_does_not_change_the_led_levels(vault):
    assert level(vault, "Real_Property_Valuation") == "expert"
    write(vault, "KG/Profile.md", "title: Profile\nkgStaleYears: 5\nkgPeriodAliases: [tenure]\nkgPractitionerMinMonths: 6")
    assert level(vault, "Real_Property_Valuation") == "expert" and level(vault, "Leasing") == "practitioner"


def test_own_projects_are_not_led_work_without_recognition(vault):
    for i, (org, per) in enumerate((("A", "2010 – 2016"), ("B", "2016 – 2022"))):
        write(vault, f"KG/Evidence/Projects/Repo_{i}.md", f"""
            nodeType: evidence
            evidenceType: project
            organization: {org}
            period: {per}
            demonstratesLed: ["[[Leasing]]"]
            disclosure: public
        """)
    assert level(vault, "Leasing") == "practitioner"
    p = vault / "KG/Evidence/Projects/Repo_0.md"
    p.write_text(p.read_text().replace("disclosure: public", "disclosure: public\nrecognition: [adoption]"))
    p = vault / "KG/Evidence/Projects/Repo_1.md"
    p.write_text(p.read_text().replace("disclosure: public", "disclosure: public\nrecognition: [publication]"))
    assert level(vault, "Leasing") == "expert"


def test_parent_needs_a_child_at_the_level(vault):
    # Real_Property_Practice gets RPV's led work by roll-up; RPV is expert itself, so the parent may be too
    assert level(vault, "Real_Property_Practice") == "expert"
    # Make the led work land on two different children: neither child is expert on its own
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]')
    p = vault / "Experience/Experience_HydroOne.md"
    p.write_text(p.read_text().replace('demonstratesLed: ["[[Real_Property_Valuation]]"]', 'demonstratesLed: ["[[Leasing]]"]'))
    assert level(vault, "Real_Property_Practice") == "practitioner"


def test_recognition_values_checked(vault):
    p = vault / "Experience/Experience_Artis.md"
    p.write_text(p.read_text().replace("recognition: [teaching]", "recognition: [famous]"))
    assert [f for f in find(run(vault).errors, "value") if "recognition" in f.message]


def test_evidence_worksheet_is_a_valid_plan(vault, tmp_path_factory):
    import evidence_worksheet as ew
    import edit_links as el
    import yaml
    rows = ew.build(str(vault), str(vault / "KG/Profile.md"), TODAY)
    notes = {r["note"] for r in rows}
    assert {"Experience_Artis", "Experience_HydroOne", "Project_Artis_Paper"} <= notes
    paper = next(r for r in rows if r["note"] == "Project_Artis_Paper" and r["field"] == "recognition")
    assert "publication" in paper["suggested"]
    for r in rows:                      # fill one entry, leave the rest empty
        if r["note"] == "Experience_Artis" and r["field"] == "demonstratesLed":
            r["add"] = ["Leasing"]
    out = tmp_path_factory.mktemp("ws") / "ws.yaml"
    out.write_text(yaml.safe_dump(rows))
    assert el.main(["--vault", str(vault), "--apply", "plan", str(out)]) == 0
    assert level(vault, "Leasing") == "practitioner"   # one led unit is not enough for advanced
    assert "Leasing" in (vault / "Experience/Experience_Artis.md").read_text().split("demonstratesLed:")[1].split("\n")[0]


def test_recognition_on_a_credential_counts_for_its_skill(vault):
    p = vault / "Experience/Experience_Artis.md"
    p.write_text(p.read_text().replace("recognition: [teaching]\n", ""))
    assert level(vault, "Real_Property_Valuation") == "advanced"
    write(vault, "KG/Evidence/Credentials/Credential_FRICS.md", """
        nodeType: evidence
        evidenceType: credential
        period: 2018-05
        demonstrates: ["[[Real_Property_Valuation]]"]
        recognition: [credential]
        disclosure: public
    """)
    assert level(vault, "Real_Property_Valuation") == "expert"


def test_led_years_use_the_led_project_dates(vault):
    # led work on a 2019 project inside the 2012-2021 Artis role counts 2019 only
    write(vault, "KG/Evidence/Projects/Project_Artis_Paper.md", """
        nodeType: evidence
        evidenceType: publication
        period: 2019-03
        partOf: "[[Experience_Artis]]"
        demonstratesLed: ["[[Leasing]]"]
        anchor: https://example.org/paper
        disclosure: public
    """)
    an = cg.Analyzer(str(vault), cg.load_settings(str(vault / "KG/Profile.md")), TODAY)
    an.run()
    p = next(q for q in an.r.nodes if an.r.nodes[q].name == "Leasing")
    d = an.level_detail(p)
    assert d["units"] == 1 and d["years"] < 0.2


def test_level_codes_and_labels():
    assert cg.normalize_level("L3") == "advanced"
    assert cg.normalize_level("l1") == "aware"
    assert cg.normalize_level("L4 Expert") == "expert"
    assert cg.normalize_level("Practitioner") == "practitioner"
    assert cg.normalize_level("L3 Expert") == "L3 Expert"        # contradiction: left for the value check
    assert cg.normalize_level("guru") == "guru"
    assert cg.level_label("advanced") == "L3 Advanced"
    assert cg.level_label("none") == "none" and cg.level_label("") == "unrated"


def test_claimed_level_code_is_read_as_word(vault):
    text = (vault / "KG/Competencies/Real_Property_Valuation.md").read_text()
    (vault / "KG/Competencies/Real_Property_Valuation.md").write_text(text.replace("claimedLevel: expert", "claimedLevel: L4"))
    r = run(vault)
    assert not [f for f in r.errors if "Real_Property_Valuation" in f.path]
    p = next(q for q in r.nodes if r.nodes[q].name == "Real_Property_Valuation")
    assert r.nodes[p].fm["claimedLevel"] == "expert"


def test_legacy_skill_type_and_rank_still_read(vault):
    p = vault / "KG/Competencies/Real_Property_Valuation.md"
    p.write_text(p.read_text().replace("nodeType: competency", "nodeType: skill").replace("rank: discipline", "rank: skill"))
    r = run(vault)
    assert not r.errors
    node = next(n for n in r.nodes.values() if n.name == "Real_Property_Valuation")
    assert node.type == "competency" and node.fm["rank"] == "element"



def test_deemed_claim_is_not_unsupported(vault):
    write(vault, "KG/Competencies/Health_and_Safety.md", 'nodeType: competency\nkind: knowledge\nbroader: ["[[Finance]]"]\nclaimedLevel: practitioner\ndeemed: "Deemed to have it (Owner, 2026-11-10)"')
    r = run(vault)
    assert not [f for f in r.warnings if "Health_and_Safety" in f.path and f.code == "unsupported"]


def test_several_assessors_ratings_are_read_and_a_difference_between_them_is_reported(vault):
    base = 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\nclaimedLevel: practitioner\n'
    said = lambda code: [f.message for f in run(vault).warnings if f.code == code]  # noqa: E731
    write(vault, "KG/Competencies/Leasing.md", base + 'assessments: ["A. Counsellor | L3 | 2026-11-13", "Bo Manager | advanced | 2026-11-14"]')
    assert run(vault).errors == [] and said("assessment") == [] and said("assessors-differ") == []    # they agree
    write(vault, "KG/Competencies/Leasing.md", base + 'assessments: ["A. Counsellor | L4 | 2026-11-13", "Bo Manager | L2 | 2026-11-14"]')
    assert said("assessors-differ") == ["the assessors rate this 2 level(s) apart (A. Counsellor L4 Expert, Bo Manager L2 Practitioner); "
                                        "the assessed level is the lowest, L2 Practitioner"]
    # a rating kept the old way is one more assessor's, unless the list already has theirs
    fm = {"assessments": ["A. Counsellor | expert | 2026-11-13"], "assessedLevel": "aware", "assessedBy": "Bo Manager", "assessedOn": "2026-11-01"}
    ratings, problems = cg.assessments_of(fm)
    assert [(r["by"], r["level"], r["raw"] is None) for r in ratings] == [("A. Counsellor", "expert", False), ("Bo Manager", "aware", True)]
    assert problems == [] and cg.agreed_level(ratings) == "aware" and cg.assessor_spread(ratings) == 3
    assert [r["by"] for r in cg.assessments_of({**fm, "assessedBy": "a. counsellor"})[0]] == ["A. Counsellor"]
    assert cg.assessments_of({})[0] == [] and cg.agreed_level([]) == "" and cg.assessor_spread(ratings[:1]) == 0
    # what the checker says of a list it cannot read
    for bad, why in (('assessments: "A. Counsellor | L3 | 2026-11-13"', "must be a list"), ('assessments: ["A. Counsellor: L3"]', "is not \"<assessor>"),
                     ('assessments: ["A. Counsellor | master | 2026-11-13"]', "level 'master'"), ('assessments: ["A. Counsellor | L3 | last week"]', "is not a day"),
                     ('assessments: ["Jo | L3 | 2026-11-13", "jo | L1 | 2026-11-14"]', "listed twice")):
        write(vault, "KG/Competencies/Leasing.md", base + bad)
        assert why in said("assessment")[0], bad


def test_an_assessors_rating_needs_its_author_and_date(vault):
    base = 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\nclaimedLevel: practitioner\n'
    write(vault, "KG/Competencies/Leasing.md", base + "assessedLevel: L3\nassessedBy: A. Counsellor\nassessedOn: 2026-11-13")
    r = run(vault)
    assert r.errors == [] and not [f for f in r.warnings if f.code == "assessment"]
    assert r.nodes["KG/Competencies/Leasing.md"].fm["assessedLevel"] == "advanced"          # L3 is read as the word
    write(vault, "KG/Competencies/Leasing.md", base + "assessedLevel: advanced\nassessedBy: A. Counsellor")
    assert [f.message for f in run(vault).warnings if f.code == "assessment"][0].startswith("`assessedLevel` without `assessedOn`")
    write(vault, "KG/Competencies/Leasing.md", base + "assessedBy: A. Counsellor")
    assert "without an `assessedLevel`" in [f.message for f in run(vault).warnings if f.code == "assessment"][0]
    write(vault, "KG/Competencies/Leasing.md", base + "assessedLevel: master")
    assert any(f.code == "value" and "assessedLevel" in f.message for f in run(vault).errors)
