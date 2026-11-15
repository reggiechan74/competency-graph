"""Tests for assessors.py and the config's `assessors:` list. Run: python3 -m pytest scripts/tests -q"""
import json
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import assessors as asr  # noqa: E402
import check_graph as cg  # noqa: E402
import edit_links as el  # noqa: E402
import kg_config as kc  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)
from test_dashboard import configure  # noqa: E402

DANA = "assessors:\n  dana-okafor: {name: Dana Okafor, role: APC counsellor}\n  bo: {name: Bo Manager}\n"


def saved(tmp_path, people):
    """An ArtifactData export of the dashboard's `settings` collection holding this list."""
    d = tmp_path / "export" / "settings"
    d.mkdir(parents=True, exist_ok=True)
    (d / "assessors.json").write_text(json.dumps({"list": people, "savedAt": "2026-11-14T12:00:00Z"}))
    (d / "frameworks.json").write_text(json.dumps({"selected": ["RICS APC|Valuation"]}))     # another setting, left alone
    return str(tmp_path / "export")


def test_the_config_takes_assessors_by_id_and_refuses_a_list_it_cannot_tell_apart(vault):  # noqa: F811
    cfg = configure(vault, DANA)
    assert cfg.assessors == {"dana-okafor": {"name": "Dana Okafor", "role": "APC counsellor"}, "bo": {"name": "Bo Manager", "role": ""}}
    assert asr.rows(cfg.assessors) == [{"id": "dana-okafor", "name": "Dana Okafor", "role": "APC counsellor"},
                                       {"id": "bo", "name": "Bo Manager", "role": ""}]
    assert "Dana Okafor  (APC counsellor)" in kc.show(cfg) and configure(vault).assessors == {}
    for bad, why in (("assessors: [Dana]\n", "must map an id"), ("assessors:\n  Dana Okafor: {name: Dana}\n", "lowercase"),
                     ("assessors:\n  a: {role: Peer}\n", "needs a `name`"), ("assessors:\n  a: {name: X, phone: 1}\n", "only `name` and `role`"),
                     ("assessors:\n  a: {name: Jo Li}\n  b: {name: jo  li}\n", "same name"),
                     ("assessors:\n  a: {name: " + "x" * 81 + "}\n", "at most 80")):
        with pytest.raises(kc.ConfigError, match=why):
            configure(vault, bad)


def test_apply_writes_only_the_assessors_block_and_plans_a_rename_through_the_link_editor(vault, tmp_path, capsys):  # noqa: F811
    cfg = configure(vault, "# who rates me\n" + DANA + "dashboard:\n  title: Mine   # kept\n")
    write(vault, "KG/Competencies/Leasing.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\n'
          'claimedLevel: practitioner\nassessments: ["Bo Manager | aware | 2026-10-30", "dana okafor | advanced | 2026-11-01"]')
    write(vault, "KG/Competencies/Valuation.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Real_Property_Practice]]"]\n'
          'assessedLevel: L2\nassessedBy: Dana Okafor\nassessedOn: 2026-10-01')                  # a rating kept the old way
    people = [{"id": "dana-okafor", "name": "Dana Okafor-Reyes", "role": "Supervisor"},
              {"id": "li-wei", "name": "Li: Wei", "role": ""}]                         # Bo is gone; Dana renamed; Li added
    src = saved(tmp_path, people)
    before = (vault / kc.CONFIG_NAME).read_text()
    args = ["--config", str(vault / kc.CONFIG_NAME), "apply", "--from", src]
    assert asr.main(args) == 0                                                         # a dry run writes nothing
    out = capsys.readouterr()
    assert out.out == 'assessors:\n  dana-okafor: {name: Dana Okafor-Reyes, role: Supervisor}\n  li-wei: {name: "Li: Wei"}\n'
    for line in ("added:   Li: Wei", "removed: Bo Manager (the ratings they gave stay in the notes)",
                 "renamed: Dana Okafor -> Dana Okafor-Reyes", "role:    Dana Okafor-Reyes: APC counsellor -> Supervisor",
                 "Leasing: the rating moves to Dana Okafor-Reyes",
                 "Valuation: the rating moves to Dana Okafor-Reyes", "(dry run"):
        assert line in out.err
    assert (vault / kc.CONFIG_NAME).read_text() == before and not list((vault / "KG/Working").glob("*Assessor_Renames*"))

    plan_file = tmp_path / "renames.yaml"
    assert asr.main(args + ["--apply", "--plan", str(plan_file)]) == 0
    text = (vault / kc.CONFIG_NAME).read_text()
    assert "# who rates me\nassessors:\n  dana-okafor: {name: Dana Okafor-Reyes, role: Supervisor}\n  li-wei:" in text
    assert text.startswith("kgConfigVersion: 1\ngraphRoot: KG\n")
    assert "dashboard:\n  title: Mine   # kept\n" in text and "Bo Manager" not in text
    back = kc.read_config(str(vault / kc.CONFIG_NAME))
    assert list(back.assessors) == ["dana-okafor", "li-wei"] and back.dashboard == {"title": "Mine"}
    plan = yaml.safe_load(plan_file.read_text())
    assert [(e["note"], e.get("unset"), e.get("set"), e["assessedBy"]) for e in plan] == [
        ("Leasing", True, None, "dana okafor"), ("Leasing", None, "advanced", "Dana Okafor-Reyes"),
        ("Valuation", True, None, "Dana Okafor"), ("Valuation", None, "practitioner", "Dana Okafor-Reyes")]
    el.run(str(vault), plan, apply=True, touch=None)                                   # the rename reaches the notes
    fm = cg.read_front_matter((vault / "KG/Competencies/Leasing.md").read_text())      # Bo's rating stays, though Bo left the list
    assert fm["assessments"] == ["Bo Manager | aware | 2026-10-30", "Dana Okafor-Reyes | advanced | 2026-11-01"]
    fm = cg.read_front_matter((vault / "KG/Competencies/Valuation.md").read_text())
    assert fm["assessments"] == ["Dana Okafor-Reyes | practitioner | 2026-10-01"] and "assessedBy" not in fm
    capsys.readouterr()
    assert asr.main(args) == 0 and "nothing to change" in capsys.readouterr().err     # applied: the lists agree


def test_apply_refuses_a_list_it_cannot_write(vault, tmp_path, capsys):  # noqa: F811
    configure(vault, DANA)
    before = (vault / kc.CONFIG_NAME).read_text()
    base = ["--config", str(vault / kc.CONFIG_NAME), "apply", "--apply", "--from"]
    for people, why in (([{"id": "a", "name": "Jo"}, {"id": "a", "name": "Flo"}], "share the id"),
                        ([{"id": "a", "name": "Jo"}, {"id": "b", "name": "JO"}], "same name"),
                        ([{"name": "Jo"}], "no id"), ([{"id": "Not A Slug", "name": "Jo"}], "lowercase")):
        assert asr.main(base + [saved(tmp_path, people)]) == 2 and why in capsys.readouterr().err
    empty = tmp_path / "none"
    empty.mkdir()
    assert asr.main(base + [str(empty)]) == 2 and "no saved list" in capsys.readouterr().err
    assert (vault / kc.CONFIG_NAME).read_text() == before
    # every assessor deleted on the dashboard: the block is kept, empty
    assert asr.main(base + [saved(tmp_path, [])]) == 0
    assert "assessors: {}\n" in (vault / kc.CONFIG_NAME).read_text() and kc.read_config(str(vault / kc.CONFIG_NAME)).assessors == {}
    assert asr.main(["--config", str(vault / kc.CONFIG_NAME), "list"]) == 0 and "no assessors" in capsys.readouterr().err
