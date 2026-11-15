"""Tests for query_graph.py. Run: python3 -m pytest scripts/tests -q"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import query_graph as qg  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)


def q(v):
    return qg.Query(str(v), str(v / "KG/Profile.md"), TODAY)


def test_support_rolls_up_and_lists_units(vault):
    out = q(vault).support("Real_Property_Practice")
    # Artis role (with its paper) and Hydro One engagement: 2 independent units
    assert "2 independent units" in out and "2 organisations" in out
    assert "Artis REIT" in out and "Hydro One" in out
    assert "Project_Artis_Paper [public]" in out


def test_support_through_skill_names_the_specific_skill(vault):
    out = q(vault).support("Real_Property_Practice")
    artis_row = next(line for line in out.splitlines() if line.startswith("| Artis REIT"))
    assert "Leasing" in artis_row and "Real_Property_Valuation (led)" in artis_row   # no title: filename shown


def test_support_disclosure_filter_hides_units(vault):
    out = q(vault).support("Real_Property_Valuation", "public")
    # both units are on-request only for this skill (the public paper demonstrates Leasing, not valuation)
    assert "2 unit(s) hidden" in out
    out = q(vault).support("Leasing", "public")
    assert "Project_Artis_Paper [public]" in out and "Experience_Artis [" not in out


def test_support_reports_claim_and_supported_level(vault):
    out = q(vault).support("Real_Property_Valuation")
    assert "claimed **L4 Expert**" in out and "supports **L4 Expert**" in out


def test_lookup_by_title_and_alias(vault):
    write(vault, "KG/Competencies/Lease_Administration.md",
          'nodeType: competency\nkind: practice\ntitle: Lease Admin\naliases: [abstracting]\nbroader: ["[[Leasing]]"]')
    query = q(vault)
    assert "Lease_Administration" in query.support("Lease Admin")
    assert "Lease_Administration" in query.support("abstracting")
    with pytest.raises(SystemExit):
        query.support("No_Such_Skill")


def test_find_matches_word_starts_not_substrings(vault):
    write(vault, "KG/Competencies/Model_Evaluation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]')
    out = q(vault).find(["valuation"])
    assert "Real Property Valuation" in out or "Real_Property_Valuation" in out
    assert "Model_Evaluation" not in out


def test_find_reports_no_match(vault):
    assert "0 match(es)" in q(vault).find(["underwater basket weaving"])


def test_tree_marks_second_parent(vault):
    out = q(vault).tree()
    assert "(also: Valuation)" in out
    # main parent placement: valuation sits under Real Property Practice
    lines = out.splitlines()
    rp = lines.index(next(line for line in lines if line.startswith("- Real_Property_Practice") or line.startswith("- Real Property Practice")))
    assert "Real_Property_Valuation" in lines[rp + 1] or "Real_Property_Valuation" in lines[rp + 2]


def test_evidence_shows_unit_root(vault):
    out = q(vault).evidence("Project_Artis_Paper")
    assert "part of unit: Artis REIT" in out and "demonstrates: Leasing" in out


def test_framework_lists_external_refs(vault):
    p = vault / "KG/Competencies/Real_Property_Valuation.md"
    p.write_text(p.read_text().replace("nodeType: competency", 'nodeType: competency\nexternalRef: ["RICS APC 2025: Valuation", "SFIA 9: X"]'))
    out = q(vault).framework("RICS APC", links=True)
    assert "| Valuation | [[Real_Property_Valuation\\|" in out and "SFIA" not in out and "1 reference(s)" in out
