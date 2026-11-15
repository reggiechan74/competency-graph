"""Tests for frameworks.py and the shipped framework library. Run: python3 -m pytest scripts/tests -q"""
import csv
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_graph as cg  # noqa: E402
import frameworks as fw  # noqa: E402
import kg_config as kc  # noqa: E402


def test_library_is_on_the_l1_l4_scale():
    lib = fw.load_library()
    assert {"rics-apc", "cfa-cbok", "asq-cssgb", "chan-afse"} <= set(lib)
    for fid, f in lib.items():
        bad = {r["required"] for r in f["rows"]} - cg.REQUIRED_VALUES
        assert not bad, (fid, bad)
        assert all(r["framework"] == f["framework"] for r in f["rows"])
    assert len(lib["rics-apc"]["pathways"]) >= 23


def test_build_marks_selection_and_notes(tmp_path):
    (tmp_path / "KG").mkdir()
    (tmp_path / kc.CONFIG_NAME).write_text(
        "kgConfigVersion: 1\ngraphRoot: KG\nrequirements: KG/Req.csv\n"
        "frameworks:\n  rics-apc:\n    pathways: [Valuation]\n    notes: {Valuation: assessor}\n  cfa-cbok: {}\n")
    assert fw.main(["--vault", str(tmp_path), "build"]) == 0
    rows = list(csv.DictReader(open(tmp_path / "KG/Req.csv")))
    val = [r for r in rows if r["pathway"] == "Valuation"]
    assert val and all(r["selected"] == "yes" and r["pathway_note"] == "assessor" for r in val)
    assert all(r["selected"] == "no" for r in rows if r["framework"] == "RICS APC" and r["pathway"] != "Valuation")
    assert all(r["selected"] == "yes" for r in rows if r["framework"] == "CFA CBOK")
    assert all(r["selected"] == "no" for r in rows if r["framework"] == "ASQ CSSGB")
    cfg = kc.read_config(str(tmp_path / kc.CONFIG_NAME))
    r = cg.check(str(tmp_path), None, cg.dt.date(2026, 11, 9), cfg)
    assert not [e for e in r.errors if e.code == "requirements"]


def test_unknown_pathway_is_refused(tmp_path):
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nframeworks:\n  rics-apc:\n    pathways: [Astrology]\n")
    assert fw.main(["--vault", str(tmp_path), "list"]) == 2
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nframeworks:\n  rics-apc:\n    colour: red\n")
    with pytest.raises(kc.ConfigError):
        kc.read_config(str(tmp_path / kc.CONFIG_NAME))


def test_rules_lose_pdf_page_numbers_and_table_spillover():
    assert fw.clean_rule("Up to 30% of your experience can come from other property sectors, e.g. residential. 22") \
        == "Up to 30% of your experience can come from other property sectors, e.g. residential."
    assert fw.clean_rule("• Local taxation/assessment • Purchase and sale 40") == "• Local taxation/assessment • Purchase and sale"
    spill = ("One to Level 3 or two to Level 2. Plus, one to Level 2 from the full list. "
             "Client care Mandatory ✓ – Core Health and safety Business planning")
    assert fw.clean_rule(spill) == "One to Level 3 or two to Level 2. Plus, one to Level 2 from the full list."
    for kept in ("Two to Level 2", "Must be taken to L3", "to either Level 2 or 3", "One to Level 3 and two to Level 2"):
        assert fw.clean_rule(kept) == kept
    # the shipped library, as build writes it: no rule ends in a page number or carries a table cell
    rows = fw.build_rows(fw.load_library(), {})
    assert not [r["rule"] for r in rows if fw.PAGE_NUMBER.search(r["rule"]) or fw.TABLE_CELL in r["rule"]]
    cre = {r["rule"] for r in rows if r["framework"] == "RICS APC" and r["pathway"] == "Commercial real estate"
           and r["group"] == "Optional"}
    assert all(t.endswith("e.g. residential.") for t in cre)


def test_library_files_are_clean_and_guides_exist():
    """The library as shipped, not only as built: rules already clean, and every named level guide is there."""
    lib = fw.load_library()
    for fid, f in lib.items():
        assert not [r["rule"] for r in f["rows"] if fw.clean_rule(r["rule"]) != r["rule"]], fid
        if f.get("guide"):
            assert os.path.isfile(os.path.join(fw.LIBRARY, f["guide"])), (fid, f["guide"])
    # every competency a guided framework's requirements name has its descriptor row in the guide
    guided = [fid for fid, f in lib.items() if f.get("guide")]
    assert {"chan-afse", "chan-agen", "chan-cxmds"} <= set(guided)
    for fid in guided:
        guide = open(os.path.join(fw.LIBRARY, lib[fid]["guide"]), encoding="utf-8").read()
        assert not [r["name"] for r in lib[fid]["rows"] if r["name"] not in guide], fid


def test_one_pathway_frameworks_list_each_competency_once_and_sub_groups_reach_the_build(tmp_path):
    """Chan AFSE, AGEN and CXMDS: one pathway, every competency in exactly one of Mandatory, Core and Optional. Each
    lists its Optional competencies in sub-groups (its specialisations) under one selection rule, and `build` writes
    the `subgroup` column for every framework (blank where a framework has none)."""
    lib = fw.load_library()
    for fid in ("chan-afse", "chan-agen", "chan-cxmds"):
        rows = lib[fid]["rows"]
        assert len(lib[fid]["pathways"]) == 1, fid
        assert list(dict.fromkeys(r["group"] for r in rows)) == ["Mandatory", "Core", "Optional"], fid
        assert len({r["name"] for r in rows}) == len(rows), (fid, "a competency is listed twice")
        assert all(r["required"] in ("L1", "L2") for r in rows if r["group"] != "Optional"), fid
        optional = [r for r in rows if r["group"] == "Optional"]
        assert {r["required"] for r in optional} == {"choice"} and len({r["rule"] for r in optional}) == 1, fid
    cx = lib["chan-cxmds"]["rows"]
    assert len(cx) == 54 and [sum(r["group"] == g for r in cx) for g in ("Mandatory", "Core", "Optional")] == [7, 16, 31]
    assert not [r for r in cx if r["group"] != "Optional" and r["subgroup"]]
    subs = [r["subgroup"] for r in cx if r["group"] == "Optional"]
    assert list(dict.fromkeys(subs)) == ["Client delivery and customer experience", "Data operations and quality",
                                         "Solutions and onboarding"]
    ag = lib["chan-agen"]["rows"]
    assert len(ag) == 55 and not [r for r in ag if r["group"] != "Optional" and r["subgroup"]]
    agen_subs = [r["subgroup"] for r in ag if r["group"] == "Optional"]
    assert [(s, agen_subs.count(s)) for s in dict.fromkeys(agen_subs)] == [
        ("Research and specialised evidence", 5), ("Chinese clan genealogy (zupu)", 9),
        ("Agentic pipeline engineering", 9), ("Publication and family history writing", 4)]
    af = lib["chan-afse"]["rows"]
    assert len(af) == 67 and [sum(r["group"] == g for r in af) for g in ("Mandatory", "Core", "Optional")] == [5, 29, 33]
    afse_subs = [r["subgroup"] for r in af if r["group"] == "Optional"]
    assert [(s, afse_subs.count(s)) for s in dict.fromkeys(afse_subs)] == [
        ("Forward-deployed delivery", 9), ("Agent application", 7), ("Agent platform and harness", 8),
        ("Agent reliability and security", 9)]
    # a sub-group's rows are together in the file, so the page prints each heading once
    for group in (subs, agen_subs, afse_subs):
        assert all(group.index(s) + group.count(s) - 1 == len(group) - 1 - group[::-1].index(s) for s in set(group))
    out = tmp_path / "req.csv"
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\n")
    assert fw.main(["--vault", str(tmp_path), "build", "--out", str(out)]) == 0
    built = list(csv.DictReader(open(out)))
    assert list(built[0]) == fw.COLUMNS and "subgroup" in fw.COLUMNS
    assert [r["subgroup"] for r in built if r["framework"] == "Chan CXMDS"] == [r["subgroup"] for r in cx]
    assert not [r for r in built if r["framework"] == "RICS APC" and r["subgroup"]]


def test_frameworks_in_one_field_share_their_mandatory_list():
    """Mandatory is the list every pathway in a field shares, and Core the baseline of one pathway only
    (domains-and-classifications.md §6). So the pathways of one framework list the same Mandatory competencies at the
    same levels (RICS APC's 23 do), and frameworks with the same `field` in the catalog list the same ones too, with the
    same description and the same L1-L4 wording (Chan AFSE and Chan AGEN are both agentic)."""
    lib = fw.load_library()
    for fid, f in lib.items():
        per = {}
        for r in f.get("rows", []):
            if r["group"] == "Mandatory":
                per.setdefault(r["pathway"], {})[r["name"]] = r["required"]
        assert len({tuple(sorted(m.items())) for m in per.values()}) <= 1, (fid, "pathways differ in Mandatory")
    fields = {}
    for fid, f in lib.items():
        if f.get("field"):
            fields.setdefault(f["field"], []).append(fid)
    assert {"chan-afse", "chan-agen"} <= set(fields.get("agentic", []))
    for field, fids in fields.items():
        lists, words = [], []
        for fid in fids:
            f = lib[fid]
            mandatory = {r["name"]: r["required"] for r in f["rows"] if r["group"] == "Mandatory"}
            with open(os.path.join(fw.LIBRARY, f["descriptions"]), encoding="utf-8", newline="") as fh:
                wording = {r["name"]: (r["description"], r["l1"], r["l2"], r["l3"], r["l4"])
                           for r in csv.DictReader(fh) if r["name"] in mandatory}
            assert mandatory and set(wording) == set(mandatory), (field, fid)
            lists.append(mandatory)
            words.append(wording)
        assert all(m == lists[0] for m in lists), (field, fids, "Mandatory lists differ")
        assert all(w == words[0] for w in words), (field, fids, "Mandatory wording differs")
    agentic = {r["name"]: r["required"] for r in lib["chan-afse"]["rows"] if r["group"] == "Mandatory"}
    assert agentic == {"AI disclosure and use boundaries": "L2", "Guardrails and human oversight": "L2",
                       "Privacy and data protection in AI use": "L2", "Responsible AI and regulatory compliance": "L1",
                       "Verification of agent output": "L2"}


def test_draft_frameworks_are_marked_in_the_list(capsys, tmp_path):
    lib = fw.load_library()
    assert {fid for fid, f in lib.items() if f.get("status") == "draft"} >= {"chan-afse", "chan-agen", "chan-cxmds"}
    assert all(f.get("status_note") for f in lib.values() if f.get("status") == "draft")
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\n")
    assert fw.main(["--vault", str(tmp_path), "list"]) == 0
    out = capsys.readouterr().out
    agen = next(line for line in out.splitlines() if line.startswith("chan-agen:"))
    assert agen.endswith("selected") and ". DRAFT. " in agen
    rics = next(line for line in out.splitlines() if line.startswith("rics-apc:"))
    assert "DRAFT" not in rics


def test_build_carries_draft_status_to_the_dashboard(tmp_path):
    out = tmp_path / "req.csv"
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\n")
    assert fw.main(["--vault", str(tmp_path), "build", "--out", str(out)]) == 0
    rows = list(csv.DictReader(open(out)))
    assert rows and list(rows[0])[-2:] == ["framework_status", "framework_status_note"]
    lib = fw.load_library()
    drafts = {f["framework"] for f in lib.values() if f.get("status") == "draft"}
    for r in rows:
        if r["framework"] in drafts:
            assert r["framework_status"] == "draft" and r["framework_status_note"]
        else:
            assert r["framework_status"] == "" and r["framework_status_note"] == ""
    # the checker still accepts the file
    (tmp_path / "KG").mkdir()
    (tmp_path / kc.CONFIG_NAME).write_text(f"kgConfigVersion: 1\ngraphRoot: KG\nrequirements: {out}\n")
    cfg = kc.read_config(str(tmp_path / kc.CONFIG_NAME))
    r = cg.check(str(tmp_path), None, cg.dt.date(2026, 11, 10), cfg)
    assert not [e for e in r.errors if e.code == "requirements"]


def test_descriptions_cover_every_framework_competency():
    """Each framework's descriptions file has one complete row per competency its requirements name, and no others."""
    lib = fw.load_library()
    for fid, f in lib.items():
        assert f.get("descriptions"), fid
        rows = f["descriptions_rows"]
        names = [r["name"] for r in rows]
        assert len(names) == len(set(names)), (fid, "duplicate names")
        assert set(names) == {r["name"] for r in f["rows"]}, (fid, set(names) ^ {r["name"] for r in f["rows"]})
        assert {r["framework"] for r in rows} == {r["framework"] for r in f["rows"]}, fid
        for r in rows:
            assert all(r[c].strip() for c in fw.DESCRIPTION_COLUMNS), (fid, r["name"])
            assert not any(ch < " " for c in fw.DESCRIPTION_COLUMNS for ch in r[c]), (fid, r["name"], "control character")


def test_build_writes_descriptions_beside_the_requirements(tmp_path):
    out = tmp_path / "Framework_Requirements.csv"
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\n")
    assert fw.main(["--vault", str(tmp_path), "build", "--out", str(out)]) == 0
    rows = list(csv.DictReader(open(tmp_path / "Framework_Descriptions.csv", encoding="utf-8")))
    assert list(rows[0]) == fw.DESCRIPTION_COLUMNS
    req = {(r["framework"], r["name"]) for r in csv.DictReader(open(out, encoding="utf-8"))}
    assert req == {(r["framework"], r["name"]) for r in rows}
    assert fw.descriptions_path("/v/req.csv") == "/v/req_descriptions.csv"


def test_dashboard_examples_agree():
    """The example descriptions file covers exactly the example requirements, in the columns build writes."""
    d = os.path.join(os.path.dirname(fw.LIBRARY), "dashboard")
    req = {(r["framework"], r["name"]) for r in csv.DictReader(open(os.path.join(d, "requirements_example.csv"), encoding="utf-8"))}
    rows = list(csv.DictReader(open(os.path.join(d, "descriptions_example.csv"), encoding="utf-8")))
    assert list(rows[0]) == fw.DESCRIPTION_COLUMNS
    assert {(r["framework"], r["name"]) for r in rows} == req
    assert all(r[c].strip() for r in rows for c in fw.DESCRIPTION_COLUMNS)


def test_build_honours_the_configs_descriptions_path(tmp_path):
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nrequirements: KG/Req.csv\n"
                                           "descriptions: Data/Levels.csv\n")
    assert fw.main(["--vault", str(tmp_path), "build"]) == 0
    assert (tmp_path / "KG/Req.csv").is_file() and (tmp_path / "Data/Levels.csv").is_file()


def own_library(tmp_path):
    own = tmp_path / "KG/Frameworks"
    own.mkdir(parents=True)
    (own / "catalog.yaml").write_text(
        "frameworks:\n  own-practice:\n    framework: Own Practice\n    title: Own practice competencies\n"
        "    body: The owner\n    edition: \"2026.1\"\n    status: draft\n    status_note: drafted for review\n"
        "    descriptions: own-practice-descriptions.csv\n")
    with open(own / "own-practice-descriptions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fw.DESCRIPTION_COLUMNS)
        w.writeheader()
        w.writerow({"framework": "Own Practice", "name": "Discounted cash flow", "description": "d", "l1": "a",
                    "l2": "b", "l3": "c", "l4": "e", "source": "drafted"})
    return own


def test_own_frameworks_join_the_library_and_may_have_no_pathways(tmp_path):
    own_library(tmp_path)
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nownFrameworks: KG/Frameworks\n"
                                           "requirements: KG/Req.csv\nframeworks:\n  cfa-cbok: {}\n")
    cfg = kc.read_config(str(tmp_path / kc.CONFIG_NAME))
    lib = fw.library_for(cfg)
    assert lib["own-practice"]["own"] and lib["own-practice"]["pathways"] == [] and not lib["rics-apc"]["own"]
    assert fw.main(["--vault", str(tmp_path), "build"]) == 0
    desc = list(csv.DictReader(open(tmp_path / "KG/Req_descriptions.csv")))
    assert {"Own Practice", "RICS APC"} <= {r["framework"] for r in desc}
    req = list(csv.DictReader(open(tmp_path / "KG/Req.csv")))
    assert "Own Practice" not in {r["framework"] for r in req}          # no pathways, so no requirement rows


def test_own_framework_may_not_reuse_a_library_id_or_name(tmp_path):
    own = own_library(tmp_path)
    (own / "catalog.yaml").write_text("frameworks:\n  rics-apc:\n    framework: X\n    descriptions: own-practice-descriptions.csv\n")
    with pytest.raises(fw.FrameworkError, match="already in the plugin's library"):
        fw.load_library(own=str(own))
    (own / "catalog.yaml").write_text("frameworks:\n  mine:\n    framework: RICS APC\n    descriptions: own-practice-descriptions.csv\n")
    with pytest.raises(fw.FrameworkError, match="already used"):
        fw.load_library(own=str(own))


def test_apply_makes_the_dashboard_selection_the_record(tmp_path):
    cfgtext = ("# my settings\nkgConfigVersion: 1\ngraphRoot: KG\n# the frameworks I want\nframeworks:\n"
               "  rics-apc:\n    pathways: [Valuation]\n    notes: {Valuation: assessor}\n  asq-cssgb:\n"
               "    notes: {Six Sigma Green Belt: held 2009}\n\n# where my sources are\nsources:\n  - path: Career\n")
    (tmp_path / "Career").mkdir()
    (tmp_path / kc.CONFIG_NAME).write_text(cfgtext)
    exp = tmp_path / "export"
    exp.mkdir()
    (exp / "frameworks.json").write_text(json.dumps({"id": "frameworks", "data": {
        "selected": ["RICS APC|Commercial real estate", "CFA CBOK|Private Markets"]}}))
    assert fw.main(["--vault", str(tmp_path), "apply", "--from", str(exp)]) == 0
    assert (tmp_path / kc.CONFIG_NAME).read_text() == cfgtext                  # a dry run writes nothing
    assert fw.main(["--vault", str(tmp_path), "apply", "--from", str(exp), "--apply"]) == 0
    text = (tmp_path / kc.CONFIG_NAME).read_text()
    assert text.startswith("# my settings\n") and "# where my sources are\nsources:\n  - path: Career\n" in text
    cfg = kc.read_config(str(tmp_path / kc.CONFIG_NAME))
    lib = fw.load_library()
    assert set(fw.selection(cfg.frameworks, lib)) == {("rics-apc", "Commercial real estate"), ("cfa-cbok", "Private Markets")}
    # notes are kept: Valuation's on RICS APC, and the Green Belt's under `pathways: []` (listed, nothing selected)
    assert cfg.frameworks["rics-apc"]["notes"] == {"Valuation": "assessor"}
    assert cfg.frameworks["asq-cssgb"] == {"pathways": [], "notes": {"Six Sigma Green Belt": "held 2009"}}


def test_apply_refuses_a_selection_the_library_lacks(tmp_path):
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\n")
    (tmp_path / "s.json").write_text(json.dumps({"selected": ["RICS APC|Astrology"]}))
    assert fw.main(["--vault", str(tmp_path), "apply", "--from", str(tmp_path / "s.json"), "--apply"]) == 2


def own_vault(tmp_path, extra=""):
    (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\n" + extra)
    (tmp_path / "KG").mkdir(exist_ok=True)
    return tmp_path


def test_a_new_own_framework_is_started_in_the_owners_files_and_read_without_a_setting(tmp_path, capsys):
    v = own_vault(tmp_path)
    cfg = kc.read_config(str(v / kc.CONFIG_NAME))
    assert cfg.own_frameworks is None and cfg.own_frameworks_home == str(v / "KG" / "Frameworks")   # a home, nothing in it yet
    assert fw.main(["--vault", str(v), "new", "firm-method", "--name", "Firm Method", "--body", "Example LLP"]) == 0
    home = v / "KG" / "Frameworks"
    assert sorted(p.name for p in home.iterdir()) == ["catalog.yaml", "firm-method-descriptions.csv", "firm-method.csv"]
    assert (home / "firm-method-descriptions.csv").read_text().strip() == ",".join(fw.DESCRIPTION_COLUMNS)
    # no `ownFrameworks:` in the config: the default folder is read once it holds a catalog
    cfg = kc.read_config(str(v / kc.CONFIG_NAME))
    assert cfg.own_frameworks == str(home)
    lib = fw.library_for(cfg)
    assert lib["firm-method"]["own"] and lib["firm-method"]["framework"] == "Firm Method" and lib["firm-method"]["status"] == "draft"
    assert not lib["rics-apc"]["own"]                              # the plugin's library is still there beside it
    # a competency library only, a second id, and the refusals; a refusal writes nothing
    assert fw.main(["--vault", str(v), "new", "firm-tools", "--name", "Firm Tools", "--no-pathways"]) == 0
    assert not (home / "firm-tools.csv").exists() and (home / "firm-tools-descriptions.csv").exists()
    before = sorted(p.name for p in home.iterdir()), (home / "catalog.yaml").read_text()
    for bad in (["new", "firm-method", "--name", "Again"], ["new", "Bad Id", "--name", "X"], ["new", "another"],
                ["new", "rics-apc", "--name", "X"], ["new", "copy2", "--from", "cfa-cbok"], ["new", "x", "--from", "nope"],
                ["new", "third", "--name", "Firm Method"]):
        assert fw.main(["--vault", str(v)] + bad) == 2, bad
    assert (sorted(p.name for p in home.iterdir()), (home / "catalog.yaml").read_text()) == before
    assert "is the id of a framework the plugin ships" in capsys.readouterr().err


def test_an_own_edition_of_a_shipped_framework_takes_its_place_for_this_owner(tmp_path, capsys):
    v = own_vault(tmp_path)
    shipped = fw.load_library()["asq-cssgb"]
    assert fw.main(["--vault", str(v), "new", "asq-cssgb", "--from", "asq-cssgb"]) == 0
    home = v / "KG" / "Frameworks"
    # the files are copies, byte for byte, in the owner's folder; the plugin's are untouched
    for key in ("file", "descriptions"):
        assert (home / shipped[key]).read_bytes() == open(os.path.join(fw.LIBRARY, shipped[key]), "rb").read()
    # the owner edits their copy: that wording is what they now see, under the same id and name, in the same place
    text = (home / shipped["descriptions"]).read_text()
    first = shipped["descriptions_rows"][0]["description"]
    (home / shipped["descriptions"]).write_text(text.replace(first, "My own wording.", 1))
    lib = fw.library_for(kc.read_config(str(v / kc.CONFIG_NAME)))
    mine = lib["asq-cssgb"]
    assert mine["own"] and mine["replaces_plugin"] is True and mine["framework"] == shipped["framework"]
    assert mine["descriptions_rows"][0]["description"] == "My own wording."
    assert list(lib)[:3] == ["rics-apc", "cfa-cbok", "asq-cssgb"] and len(lib) == len(fw.load_library())
    assert fw.load_library()["asq-cssgb"]["descriptions_rows"][0]["description"] == first
    capsys.readouterr()
    assert fw.main(["--vault", str(v), "list"]) == 0
    said = capsys.readouterr().out
    assert "OWN EDITION: yours takes the place of the plugin's." in said and "has changed since" not in said
    # when the plugin's edition moves on, list says so
    cat = home / "catalog.yaml"
    cat.write_text(cat.read_text().replace("based_on: ", "based_on: \"asq-cssgb, an older edition\" # "))
    assert fw.main(["--vault", str(v), "list"]) == 0
    assert "The plugin's has changed since" in capsys.readouterr().out


def test_a_copy_under_a_new_id_is_a_framework_of_its_own(tmp_path):
    v = own_vault(tmp_path)
    assert fw.main(["--vault", str(v), "new", "my-cfa", "--from", "cfa-cbok", "--name", "My CFA"]) == 0
    lib = fw.library_for(kc.read_config(str(v / kc.CONFIG_NAME)))
    assert lib["my-cfa"]["own"] and not lib["my-cfa"].get("replaces_plugin") and not lib["cfa-cbok"]["own"]
    assert {r["framework"] for r in lib["my-cfa"]["rows"]} == {"My CFA"}
    assert {r["framework"] for r in lib["my-cfa"]["descriptions_rows"]} == {"My CFA"}
    assert lib["my-cfa"]["pathways"] == lib["cfa-cbok"]["pathways"]


def test_nothing_of_the_owners_is_kept_in_the_plugins_own_folder(tmp_path, capsys, monkeypatch):
    inside = os.path.join(kc.SKILL_DIR, "assets", "frameworks")
    v = own_vault(tmp_path)
    # a requirements file is never built into the plugin, nor an own framework started there
    assert fw.main(["--vault", str(v), "build", "--out", os.path.join(inside, "x.csv")]) == 2
    assert "plugin's own folder" in capsys.readouterr().err and not os.path.exists(os.path.join(inside, "x.csv"))
    with pytest.raises(fw.FrameworkError, match="plugin's own folder"):
        fw.new_framework(os.path.join(inside, "own"), "x", None, name="X", today="2026-11-15")
    assert not os.path.exists(os.path.join(inside, "own"))
    # and no setting may point into it, even in a vault that holds the plugin (the plugin's own repository, say)
    monkeypatch.setattr(kc, "SKILL_DIR", str(tmp_path / "plugin" / "skills" / "competency-graph"))
    for text in ("graphRoot: plugin/skills/competency-graph/assets\n",
                 "graphRoot: KG\nownFrameworks: plugin/skills/competency-graph/assets/frameworks\n",
                 "graphRoot: KG\nrequirements: plugin/skills/competency-graph/assets/frameworks/mine.csv\n",
                 "graphRoot: KG\njobSpecs: plugin/skills/competency-graph/Job_Specs.yaml\n",
                 "graphRoot: KG\nfolders:\n  outputs: plugin/skills/competency-graph/out\n"):
        (tmp_path / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\n" + text)
        with pytest.raises(kc.ConfigError, match="plugin's own folder"):
            kc.read_config(str(tmp_path / kc.CONFIG_NAME))
