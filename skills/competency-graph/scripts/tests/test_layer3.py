"""Layer 3 of the specification (v0.5): prerequisites, named relations, organisation and person notes, and the rules
that read them. Run: python3 -m pytest scripts/tests -q"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_graph as cg  # noqa: E402
import edit_links as el  # noqa: E402
import query_graph as qg  # noqa: E402
import summary_graph as sg  # noqa: E402
from test_check_graph import TODAY, run, vault, write  # noqa: E402,F401  (fixture reuse)

COMP = 'nodeType: competency\nkind: {kind}\nbroader: ["[[Real_Property_Practice]]"]\n'


def said(vault, code):  # noqa: F811
    return [(os.path.basename(f.path)[:-3], f.message) for f in run(vault).warnings if f.code == code]


def test_a_claim_above_a_prerequisite_is_reported_and_no_level_is_changed(vault):  # noqa: F811
    write(vault, "KG/Competencies/Lease_Law.md", COMP.format(kind="knowledge") + "claimedLevel: aware")
    write(vault, "KG/Competencies/Negotiation.md", COMP.format(kind="practice"))
    write(vault, "KG/Competencies/Leasing.md", COMP.format(kind="practice") + 'claimedLevel: advanced\nrequires: ["[[Lease_Law]]", "[[Negotiation]]"]')
    r = run(vault)
    assert r.errors == []
    assert said(vault, "prerequisite") == [("Leasing", "claims L3 Advanced but requires Lease_Law, which is claimed at L1 Aware"),
                                           ("Leasing", "claims L3 Advanced but requires Negotiation, which is not rated")]
    before = {p: n.fm.get("claimedLevel") for p, n in r.nodes.items()}
    # the prerequisites raised to the claim: nothing to report. An unrated competency with prerequisites: nothing either
    write(vault, "KG/Competencies/Lease_Law.md", COMP.format(kind="knowledge") + "claimedLevel: expert")
    write(vault, "KG/Competencies/Negotiation.md", COMP.format(kind="practice") + "claimedLevel: advanced")
    assert said(vault, "prerequisite") == []
    write(vault, "KG/Competencies/Leasing.md", COMP.format(kind="practice") + 'requires: ["[[Lease_Law]]"]')
    assert said(vault, "prerequisite") == [] and before["KG/Competencies/Leasing.md"] == "advanced"
    # a loop of prerequisites is an error; a prerequisite in the competency's own line of the tree is questioned
    write(vault, "KG/Competencies/Lease_Law.md", COMP.format(kind="knowledge") + 'requires: ["[[Leasing]]"]')
    assert any(f.code == "cycle" and "requires cycle" in f.message for f in run(vault).errors)
    write(vault, "KG/Competencies/Lease_Law.md", COMP.format(kind="knowledge"))
    write(vault, "KG/Competencies/Leasing.md", COMP.format(kind="practice") + 'requires: ["[[Real_Property_Practice]]"]')
    assert "already above or below" in said(vault, "relation")[0][1]
    write(vault, "KG/Competencies/Leasing.md", COMP.format(kind="practice") + 'requires: ["[[Sector_53]]"]')
    assert any(f.code in ("target", "link") for f in run(vault).errors)          # a prerequisite is a competency


def test_applied_to_runs_from_a_method_or_tool_to_a_practice(vault):  # noqa: F811
    write(vault, "KG/Competencies/Leasing.md", COMP.format(kind="practice"))
    write(vault, "KG/Competencies/VTS.md", COMP.format(kind="tool") + 'appliedTo: ["[[Leasing]]"]')
    assert run(vault).errors == [] and said(vault, "relation") == []
    write(vault, "KG/Competencies/Negotiation.md", COMP.format(kind="practice") + 'appliedTo: ["[[Leasing]]"]')
    assert said(vault, "relation") == [("Negotiation", "`appliedTo` is for a method, tool or knowledge; between two practices (Leasing) use `related`")]
    write(vault, "KG/Competencies/Negotiation.md", COMP.format(kind="practice"))
    write(vault, "KG/Competencies/Excel.md", COMP.format(kind="tool") + 'appliedTo: ["[[VTS]]"]')
    assert said(vault, "relation") == [("Excel", "`appliedTo` → VTS is a tool, expected a practice")]


ROLE = ('nodeType: evidence\nevidenceType: role\nperiod: {period}\norganization: {org}\ndisclosure: on-request\n'
        'sector: ["[[Sector_53_Real_Estate]]"]\ndemonstrates: ["[[{comp}]]"]\ndemonstratesLed: ["[[{comp}]]"]\n')


def test_one_organisation_however_it_is_written_and_a_referee_as_an_anchor(vault):  # noqa: F811
    # a competency of its own, so that only these two roles are behind it
    write(vault, "KG/Competencies/Lease_Negotiation.md", COMP.format(kind="practice") + "claimedLevel: advanced")
    role = lambda period, org: ROLE.format(period=period, org=org, comp="Lease_Negotiation")  # noqa: E731
    write(vault, "Jobs/Role_A.md", role("2010-01 – 2014-12", "Artis REIT"))
    write(vault, "Jobs/Role_B.md", role("2015-01 – 2019-12", '"Artis Real Estate Investment Trust"'))
    an = cg.Analyzer(str(vault), cg.load_settings(str(vault / "KG/Profile.md")), TODAY)
    an.run()
    leasing = "KG/Competencies/Lease_Negotiation.md"
    # two spellings, no organisation note: two organisations, and that is enough for L3 with no anchor
    assert len(an.unit_profile({"Jobs/Role_A.md", "Jobs/Role_B.md"})[1]) == 2 and an.level_detail(leasing)["level"] == "advanced"
    write(vault, "KG/Organizations/Org_Artis.md", 'nodeType: organization\ntitle: Artis REIT\naliases: ["Artis Real Estate Investment Trust"]\n'
          'sector: ["[[Sector_53_Real_Estate]]"]\ncrm: "CRM/Clients/ARTIS"')
    an = cg.Analyzer(str(vault), cg.load_settings(str(vault / "KG/Profile.md")), TODAY)
    r = an.run()
    assert r.errors == [] and r.stats["organizations"] == 1
    assert an.org_key("artis  reit") == an.org_key("[[Org_Artis]]") == an.org_key("Artis Real Estate Investment Trust") == "KG/Organizations/Org_Artis.md"
    assert an.org_name("[[Org_Artis]]") == "Artis REIT" and an.org_key("Someone Else") == "someone else" and an.org_key(None) == ""
    # one organisation now: the same work no longer meets "two organisations or an anchor"
    d = an.level_detail(leasing)
    assert d["level"] == "practitioner" and any("1 organisation(s) and no anchor" in m for m in d["missing"])
    assert [m for _, m in said(vault, "unsupported") if "L3 Advanced" in m]
    # a referee who can be asked is an anchor: a person note, joined to the owner's own contact record by `crm`
    write(vault, "KG/People/Person_Dana_Okafor.md", 'nodeType: person\ntitle: Dana Okafor\nrole: Head of leasing\n'
          'organization: "[[Org_Artis]]"\ncrm: "CRM/Network/OKAFOR_Dana"')
    write(vault, "Jobs/Role_B.md", role("2015-01 – 2019-12", '"[[Org_Artis]]"') + 'referee: ["[[Person_Dana_Okafor]]"]')
    an = cg.Analyzer(str(vault), cg.load_settings(str(vault / "KG/Profile.md")), TODAY)
    r = an.run()
    assert r.errors == [] and r.stats["people"] == 1 and an.level_detail(leasing)["level"] == "advanced"
    assert not [f for f in r.warnings if f.code == "anchor" and f.path.endswith("Role_B.md")]
    assert [f for f in r.warnings if f.code == "anchor" and f.path.endswith("Role_A.md")]
    # a referee is a person; two organisation notes cannot answer to one name
    write(vault, "Jobs/Role_A.md", role("2010-01 – 2014-12", "Artis REIT") + 'referee: ["[[Org_Artis]]"]')
    assert any(f.code == "target" and "expected person" in f.message for f in run(vault).errors)
    write(vault, "Jobs/Role_A.md", role("2010-01 – 2014-12", "Artis REIT"))
    write(vault, "KG/Organizations/Org_Other.md", 'nodeType: organization\ntitle: Other\naliases: ["artis reit"]')
    assert "one organisation, one note" in said(vault, "organization")[0][1]


def test_the_link_editor_the_query_tool_and_the_summary_know_the_relations(vault, capsys):  # noqa: F811
    write(vault, "KG/Competencies/Leasing.md", COMP.format(kind="practice") + "claimedLevel: advanced")
    write(vault, "KG/Competencies/Lease_Law.md", COMP.format(kind="knowledge") + "claimedLevel: aware")
    write(vault, "KG/Competencies/VTS.md", COMP.format(kind="tool"))
    write(vault, "KG/Organizations/Org_Artis.md", "nodeType: organization\ntitle: Artis REIT")
    write(vault, "KG/People/Person_Dana_Okafor.md", "nodeType: person\ntitle: Dana Okafor")
    write(vault, "Jobs/Role_A.md", ROLE.format(period="2010-01 – 2014-12", org="artis reit", comp="Leasing"))
    write(vault, "Jobs/Cert.md", 'nodeType: evidence\nevidenceType: credential\nperiod: 2012\ndisclosure: public\ndemonstrates: ["[[Leasing]]"]')
    v = ["--vault", str(vault)]
    assert el.main(v + ["add", "Leasing", "requires", "Lease_Law", "--apply"]) == 0
    assert el.main(v + ["add", "VTS", "appliedTo", "Leasing", "--apply"]) == 0
    assert el.main(v + ["add", "Role_A", "referee", "Person_Dana_Okafor", "--apply"]) == 0
    assert el.main(v + ["add", "Org_Artis", "aliases", "Artis Real Estate Investment Trust", "--apply"]) == 0
    assert el.main(v + ["set", "Person_Dana_Okafor", "organization", "[[Org_Artis]]", "--apply"]) == 0
    assert el.main(v + ["add", "Leasing", "requires", "Org_Artis", "--apply"]) == 1          # not a competency: refused
    assert el.main(v + ["add", "Role_A", "referee", "Leasing", "--apply"]) == 1              # not a person: refused
    fm = cg.read_front_matter((vault / "KG/Competencies/Leasing.md").read_text())
    assert fm["requires"] == ["[[Lease_Law]]"] and run(vault).errors == []
    capsys.readouterr()
    assert qg.main(v + ["--today", TODAY.isoformat(), "relations", "Leasing"]) == 0
    out = capsys.readouterr().out
    assert "## Leasing (Leasing): claimed L3 Advanced" in out and "- requires: Lease_Law (L1 Aware)" in out
    assert "- served by: VTS" in out and "- certified by: Cert" in out and "- required by: none" in out
    assert qg.main(v + ["--today", TODAY.isoformat(), "relations", "Lease_Law"]) == 0
    assert "- required by: Leasing (L3 Advanced)" in capsys.readouterr().out
    assert qg.main(v + ["--today", TODAY.isoformat(), "organizations"]) == 0
    out = capsys.readouterr().out
    assert "| Artis REIT | Org_Artis | 1 | artis reit |" in out
    assert qg.main(v + ["--today", TODAY.isoformat(), "evidence", "Role_A"]) == 0
    out = capsys.readouterr().out
    assert "Artis REIT" in out and "- referee: Dana Okafor" in out
    s = sg.Summary(str(vault), str(vault / "KG/Profile.md"), TODAY, "on-request")
    rows = {r["note"]: r for r in s.competencies()}
    assert rows["Leasing"]["requires"] == ["Lease_Law"] and rows["VTS"]["requires"] == []
    assert "Artis REIT" in {t["organisation"] for t in s.timeline()}                    # the note's title, not "artis reit"
