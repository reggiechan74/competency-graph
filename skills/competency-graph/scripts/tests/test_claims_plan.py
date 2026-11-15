"""Tests for claims_plan.py. Run: python3 -m pytest scripts/tests -q"""
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import claims_plan as cp  # noqa: E402


def write_docs(d, docs):
    (d / "claims").mkdir(parents=True)
    for doc_id, data in docs.items():
        (d / "claims" / f"{doc_id}.json").write_text(json.dumps(data))


def test_plan_sets_unsets_and_lists_new(tmp_path):
    write_docs(tmp_path / "x", {
        "Leasing": {"key": "Leasing", "note": "Leasing", "from": "expert", "to": "advanced", "savedAt": "2026-11-09T13:40:00Z"},
        "Excel": {"key": "Excel", "note": "Excel", "from": "practitioner", "to": "", "savedAt": "2026-11-09T13:41:00Z"},
        "RICS_APC_Measurement": {"key": "RICS_APC_Measurement", "note": "", "framework": "RICS APC",
                                 "requirement": "Measurement", "from": "", "to": "practitioner"},
    })
    out = tmp_path / "plan.yaml"
    assert cp.main(["--from", str(tmp_path / "x"), "--out", str(out)]) == 0
    plan = yaml.safe_load(out.read_text())
    by = {e["note"]: e for e in plan}
    assert by["Leasing"]["set"] == "advanced" and by["Excel"]["unset"] is True and "set" not in by["Excel"]
    new = yaml.safe_load((tmp_path / "plan.new.yaml").read_text())["newCompetencies"]
    assert new == [{"claim": "RICS_APC_Measurement", "framework": "RICS APC", "requirement": "Measurement",
                    "level": "practitioner", "why": new[0]["why"]}]


def test_bad_level_is_skipped(tmp_path):
    write_docs(tmp_path / "x", {"A": {"note": "A", "to": "guru"}})
    assert cp.main(["--from", str(tmp_path / "x"), "--out", str(tmp_path / "p.yaml")]) == 1
    assert yaml.safe_load((tmp_path / "p.yaml").read_text().split("\n", 2)[2]) in (None, [])


def test_list_file_and_level_codes(tmp_path):
    f = tmp_path / "claims.json"
    f.write_text(json.dumps([{"id": "Leasing", "data": {"note": "Leasing", "to": "L3"}}]))
    out = tmp_path / "p.yaml"
    assert cp.main(["--from", str(f), "--out", str(out)]) == 0
    assert yaml.safe_load(out.read_text())[0]["set"] == "advanced"


def test_an_assessors_rating_becomes_an_assessed_level_entry_with_its_author_and_date(tmp_path):
    write_docs(tmp_path / "x", {
        "Leasing": {"key": "Leasing", "note": "Leasing", "from": "", "to": "advanced", "savedAt": "2026-11-13T09:00:00Z"},
        "assessed--Leasing": {"key": "assessed--Leasing", "field": "assessedLevel", "note": "Leasing", "from": "",
                              "to": "practitioner", "by": "A. Counsellor", "savedAt": "2026-11-13T09:05:00Z"},
        "assessed--Excel": {"key": "assessed--Excel", "field": "assessedLevel", "note": "Excel", "from": "aware",
                            "to": "", "by": "A. Counsellor", "savedAt": "2026-11-13T09:06:00Z"},
        "assessed--VTS": {"key": "assessed--VTS", "field": "assessedLevel", "note": "VTS", "from": "", "to": "aware"},
        # a second assessor's rating of the same competency: its own document, its own entry
        "assessed--bo-manager--Leasing": {"key": "assessed--bo-manager--Leasing", "field": "assessedLevel", "note": "Leasing",
                                          "from": "", "to": "advanced", "by": "Bo Manager", "byId": "bo-manager",
                                          "savedAt": "2026-11-15T01:30:00Z", "on": "2026-11-14"},   # an evening west of UTC
        "assessed--x--Word": {"key": "assessed--x--Word", "field": "assessedLevel", "note": "Word", "from": "aware", "to": ""},
    })
    out = tmp_path / "plan.yaml"
    assert cp.main(["--from", str(tmp_path / "x"), "--out", str(out)]) == 1          # the unnamed ratings are skipped
    plan = yaml.safe_load(out.read_text())
    assert sorted((e["set"], e["assessedBy"], str(e["assessedOn"])) for e in plan if e["note"] == "Leasing" and e["field"] == "assessedLevel") == [
        ("advanced", "Bo Manager", "2026-11-14"), ("practitioner", "A. Counsellor", "2026-11-13")]
    assert not [e for e in plan if e["note"] == "Word"]                              # whose rating to remove is not known
    by = {(e["note"], e["field"]): e for e in plan if e.get("assessedBy") != "Bo Manager"}
    assert by[("Leasing", "claimedLevel")]["set"] == "advanced" and "by" not in by[("Leasing", "claimedLevel")]
    rated = by[("Leasing", "assessedLevel")]
    assert (rated["set"], rated["assessedBy"], str(rated["assessedOn"])) == ("practitioner", "A. Counsellor", "2026-11-13")
    gone = by[("Excel", "assessedLevel")]                                           # only that assessor's rating goes
    assert gone["unset"] is True and gone["assessedBy"] == "A. Counsellor" and "assessedOn" not in gone
    assert ("VTS", "assessedLevel") not in by
