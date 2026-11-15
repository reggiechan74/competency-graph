"""Tests for kg_config.py and the scripts' use of it. Run: python3 -m pytest scripts/tests -q"""
import datetime as dt
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import check_graph as cg  # noqa: E402
import kg_config as kc  # noqa: E402
import rating_worksheet as rw  # noqa: E402
from test_check_graph import TODAY, vault, write  # noqa: E402,F401  (fixture reuse)


@pytest.fixture(autouse=True)
def own_home(tmp_path_factory, monkeypatch):
    """Each test gets an empty home folder, so the lookup's last resort (Documents/Competency_Graph) finds nothing of
    the machine's own."""
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    return home


def make_config(v, text=None):
    (v / kc.CONFIG_NAME).write_text(text or "kgConfigVersion: 1\ngraphRoot: KG\nprofile: KG/Profile.md\n",
                                    encoding="utf-8")
    return v / kc.CONFIG_NAME


def test_defaults_derive_from_graph_root(vault):
    cfg = kc.read_config(str(make_config(vault)))
    assert cfg.vault == str(vault)
    assert cfg.profile == str(vault / "KG/Profile.md")
    assert cfg.folders["competencies"] == str(vault / "KG/Competencies")
    assert cfg.folders["reports"] == str(vault / "KG/Working")
    assert cfg.folders["outputs"] == str(vault / "KG/Outputs")
    assert cfg.dated is True


def test_folder_overrides_and_outputs_outside_vault(vault, tmp_path_factory):
    elsewhere = tmp_path_factory.mktemp("deliverables")
    make_config(vault, f"graphRoot: KG\nprofile: KG/Profile.md\nfolders:\n  outputs: {elsewhere}\n"
                       "  working: Drafts/KG\ndatedFilenames: false\n")
    cfg = kc.read_config(str(vault / kc.CONFIG_NAME))
    assert cfg.folders["outputs"] == str(elsewhere)
    assert cfg.folders["working"] == str(vault / "Drafts/KG")
    assert cfg.new_file("outputs", "Match.md") == os.path.join(str(elsewhere), "Match.md")


@pytest.mark.parametrize("text, problem", [
    ("profile: KG/Profile.md\n", "graphRoot is required"),
    ("graphRoot: KG\nfolder: {}\n", "unknown key"),
    ("graphRoot: KG\nfolders:\n  notes: X\n", "unknown folder key"),
    ("graphRoot: KG\nfolders:\n  competencies: ../Elsewhere\n", "outside the vault"),
    ("graphRoot: KG\nkgConfigVersion: 2\n", "not supported"),
    ("graphRoot: KG\ndatedFilenames: maybe\n", "true or false"),
])
def test_bad_configs_are_refused(vault, text, problem):
    make_config(vault, text)
    with pytest.raises(kc.ConfigError, match=problem):
        kc.read_config(str(vault / kc.CONFIG_NAME))


def test_new_file_dates_once_and_respects_no_date(vault):
    cfg = kc.read_config(str(make_config(vault)))
    d = dt.date(2026, 11, 8)
    assert cfg.new_file("working", "M1_Test.md", today=d).endswith("KG/Working/2026-11-08_M1_Test.md")
    assert cfg.new_file("working", "2026-11-08_M1_Test.md", today=d).endswith("/2026-11-08_M1_Test.md")
    assert cfg.new_file("outputs", "requirements.md", dated=False).endswith("KG/Outputs/requirements.md")
    with pytest.raises(kc.ConfigError):
        cfg.new_file("nowhere", "x.md")


def test_found_from_a_subfolder_and_vault_flag_wins_over_walk(vault, tmp_path_factory):
    make_config(vault)
    sub = vault / "CV" / "Deep"
    sub.mkdir(parents=True)
    assert kc.load(start=str(sub)).path == str(vault / kc.CONFIG_NAME)
    other = tmp_path_factory.mktemp("other_vault")
    cfg = kc.load(vault=str(other))          # explicit vault: no walking up, defaults used
    assert cfg.path is None and cfg.vault == str(other)


def test_required_without_config_or_vault(tmp_path):
    with pytest.raises(kc.ConfigError, match="no competency-graph.yaml"):
        kc.load(start=str(tmp_path), required=True)


def test_vault_mismatch_with_config(vault, tmp_path_factory):
    cfg_path = make_config(vault)
    with pytest.raises(kc.ConfigError, match="does not match"):
        kc.load(config=str(cfg_path), vault=str(tmp_path_factory.mktemp("x")))


def test_init_writes_a_config_that_reads_back(tmp_path, capsys):
    assert kc.main(["--vault", str(tmp_path), "init", "--graph-root", "Graph",
                    "--profile", "Graph/Profile_A.md", "--outputs", "Applications"]) == 0
    cfg = kc.read_config(str(tmp_path / kc.CONFIG_NAME))
    assert cfg.folders["outputs"] == str(tmp_path / "Applications")
    assert cfg.folders["competencies"] == str(tmp_path / "Graph/Competencies")
    assert kc.main(["--vault", str(tmp_path), "init", "--graph-root", "G", "--profile", "G/P.md"]) == 2


def test_checker_runs_from_config_alone(vault, monkeypatch, capsys):
    make_config(vault)
    monkeypatch.chdir(vault / "KG")
    assert cg.main(["--today", TODAY.isoformat()]) == 0
    assert "0 errors" in capsys.readouterr().out


def test_checker_auto_report_goes_to_reports_folder(vault, monkeypatch):
    make_config(vault)
    monkeypatch.chdir(vault)
    cg.main(["--today", TODAY.isoformat(), "--report", "--json"])
    assert (vault / "KG/Working/2026-11-08_Graph_Check.md").exists()
    assert (vault / "KG/Working/2026-11-08_Graph.json").exists()


def test_checker_warns_about_notes_outside_configured_folders(vault):
    cfg = kc.read_config(str(make_config(vault)))
    write(vault, "Misc/Stray_Skill.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]')
    r = cg.check(str(vault), str(vault / "KG/Profile.md"), TODAY, cfg)
    stray = [w for w in r.warnings if w.code == "folder"]
    assert [w.path for w in stray] == ["Misc/Stray_Skill.md"]
    write(vault, "KG/Competencies/RICS/Grouped.md", 'nodeType: competency\nkind: practice\nbroader: ["[[Finance]]"]')
    r = cg.check(str(vault), str(vault / "KG/Profile.md"), TODAY, cfg)
    assert [w.path for w in r.warnings if w.code == "folder"] == ["Misc/Stray_Skill.md"]   # subfolder is fine
    # without a config file there is no folder rule
    r = cg.check(str(vault), str(vault / "KG/Profile.md"), TODAY)
    assert not [w for w in r.warnings if w.code == "folder"]


def test_worksheet_defaults_to_working_folder(vault, monkeypatch):
    make_config(vault)
    monkeypatch.chdir(vault)
    assert rw.main(["--today", TODAY.isoformat()]) == 0
    assert (vault / "KG/Working/2026-11-08_Self_Rating_Worksheet.yaml").exists()


def test_legacy_skills_folder_key(vault):
    (vault / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nfolders:\n  skills: KG/Skills\n")
    cfg = kc.read_config(str(vault / kc.CONFIG_NAME))
    assert cfg.folders["competencies"] == str(vault / "KG/Skills")
    (vault / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nfolders:\n  skills: KG/Skills\n  competencies: KG/C\n")
    with pytest.raises(kc.ConfigError):
        kc.read_config(str(vault / kc.CONFIG_NAME))


def test_new_file_mkdir_creates_subfolder(vault):
    cfg = kc.read_config(str(make_config(vault)))
    p = cfg.new_file("outputs", "Dashboard/index.html", dated=False, mkdir=True)
    assert p == str(vault / "KG/Outputs/Dashboard/index.html") and (vault / "KG/Outputs/Dashboard").is_dir()


def test_requirements_file_must_use_l1_l4(vault):
    req = vault / "KG/Framework_Requirements.csv"
    req.write_text("framework,pathway,group,order,name,required,rule\n"
                   "Example,Path,Core,1,Valuation,L3,\n"
                   "Example,Path,Optional,1,Tax,choice,\n"
                   "Bloomish,Path,Core,1,Stats,Apply,\n")
    (vault / kc.CONFIG_NAME).write_text("kgConfigVersion: 1\ngraphRoot: KG\nprofile: KG/Profile.md\n"
                                        "requirements: KG/Framework_Requirements.csv\n")
    cfg = kc.read_config(str(vault / kc.CONFIG_NAME))
    assert cfg.requirements == str(req)
    r = cg.check(str(vault), str(vault / "KG/Profile.md"), TODAY, cfg)
    errs = [e for e in r.errors if e.code == "requirements"]
    assert len(errs) == 1 and "Bloomish" in errs[0].message and "'Apply'" in errs[0].message
    req.write_text("framework,pathway,group,order,name,required,rule\nExample,Path,Core,1,Valuation,L3,\n")
    assert not [e for e in cg.check(str(vault), str(vault / "KG/Profile.md"), TODAY, cfg).errors if e.code == "requirements"]


def test_sources_and_descriptions_read_back(vault, tmp_path_factory):
    outside = tmp_path_factory.mktemp("cloud")
    (vault / "Career/Resume").mkdir(parents=True)
    make_config(vault, "graphRoot: KG\nprofile: KG/Profile.md\nrequirements: KG/Req.csv\ndescriptions: Data/Desc.csv\n"
                       f"sources:\n  - path: Career/Resume\n    kind: resume-folder\n    note: master CV\n"
                       f"  - {{path: {outside}, use: collect}}\n  - Jobs\n")
    cfg = kc.read_config(str(vault / kc.CONFIG_NAME))
    assert cfg.descriptions_file == str(vault / "Data/Desc.csv")
    assert [(e["use"], e["kind"]) for e in cfg.sources] == [("collect", "resume-folder"), ("collect", ""), ("collect", "")]
    assert cfg.sources[0]["path"] == str(vault / "Career/Resume")
    text = kc.show(cfg)
    assert "Career/Resume  [resume-folder]  master CV" in text and "Jobs  (MISSING)" in text
    make_config(vault, "graphRoot: KG\nrequirements: KG/Framework_Requirements.csv\n")
    assert kc.read_config(str(vault / kc.CONFIG_NAME)).descriptions_file == str(vault / "KG/Framework_Descriptions.csv")


@pytest.mark.parametrize("text, problem", [
    ("graphRoot: KG\nsources: Career\n", "must be a list"),
    ("graphRoot: KG\nsources:\n  - {path: CV, use: maybe}\n", "not one of"),
    ("graphRoot: KG\nsources:\n  - {kind: cv}\n", "needs a `path`"),
    ("graphRoot: KG\nsources:\n  - {path: CV, colour: red}\n", "needs a `path`"),
    ("graphRoot: KG\nsources:\n  - {path: /elsewhere/Jobs, use: evidence}\n", "must be inside it"),
    ("graphRoot: KG\ndescriptions: ../Desc.csv\n", "outside the vault"),
])
def test_bad_sources_are_refused(vault, text, problem):
    make_config(vault, text)
    with pytest.raises(kc.ConfigError, match=problem):
        kc.read_config(str(vault / kc.CONFIG_NAME))


def test_init_takes_every_location_and_source(tmp_path):
    assert kc.main(["--vault", str(tmp_path), "init", "--graph-root", "Me/Graph", "--profile", "Me/Graph/Profile_A.md",
                    "--competencies", "Me/Graph/Skills", "--working", "Me/Drafts", "--outputs", "Applications",
                    "--requirements", "Me/Graph/Framework_Requirements.csv", "--descriptions", "Me/Graph/Desc.csv",
                    "--source", "Career/Resume=collect:resume-folder", "--source", "Career/Jobs=evidence:job-history",
                    "--source", "Old", "--no-dated"]) == 0
    cfg = kc.read_config(str(tmp_path / kc.CONFIG_NAME))
    assert cfg.folders["competencies"] == str(tmp_path / "Me/Graph/Skills")
    assert cfg.folders["working"] == str(tmp_path / "Me/Drafts")
    assert cfg.requirements == str(tmp_path / "Me/Graph/Framework_Requirements.csv")
    assert cfg.descriptions_file == str(tmp_path / "Me/Graph/Desc.csv")
    assert [(e["use"], e["kind"]) for e in cfg.sources] == [("collect", "resume-folder"), ("evidence", "job-history"),
                                                            ("collect", "")]
    assert cfg.dated is False
    # a bad source is refused and leaves no file behind
    (tmp_path / "x").mkdir()
    assert kc.main(["--vault", str(tmp_path / "x"), "init", "--graph-root", "G", "--profile", "G/P.md",
                    "--source", "J=maybe"]) == 2
    assert not (tmp_path / "x" / kc.CONFIG_NAME).exists()


def test_checker_warns_about_missing_sources(vault):
    (vault / "Career").mkdir()
    make_config(vault, "graphRoot: KG\nprofile: KG/Profile.md\nsources:\n  - Career\n  - {path: Gone, kind: cv}\n"
                       "  - {path: Skipped, use: ignore}\n")
    cfg = kc.read_config(str(vault / kc.CONFIG_NAME))
    r = cg.check(str(vault), None, TODAY, cfg)
    src = [f for f in r.warnings if f.code == "source"]
    assert [f.path for f in src] == ["Gone"]


def test_job_specs_own_frameworks_and_dashboard_keys(tmp_path):
    p = tmp_path / kc.CONFIG_NAME
    p.write_text("kgConfigVersion: 1\ngraphRoot: KG\n")
    cfg = kc.read_config(str(p))
    assert cfg.job_specs_file == str(tmp_path / "KG/Competencies/Job_Specs.yaml") and cfg.own_frameworks is None
    p.write_text("kgConfigVersion: 1\ngraphRoot: KG\njobSpecs: Roles/Specs.yaml\nownFrameworks: KG/Mine\n"
                 "dashboard:\n  title: My portfolio\n  sectors: NAICS Canada\n  disclosure: public\n")
    cfg = kc.read_config(str(p))
    assert cfg.job_specs_file == str(tmp_path / "Roles/Specs.yaml") and cfg.own_frameworks == str(tmp_path / "KG/Mine")
    assert cfg.dashboard == {"title": "My portfolio", "sectors": "NAICS Canada", "disclosure": "public"}
    for bad in ("dashboard:\n  disclosure: confidential\n", "dashboard:\n  colour: red\n", "jobSpecs: /elsewhere/x.yaml\n"):
        p.write_text("kgConfigVersion: 1\ngraphRoot: KG\n" + bad)
        with pytest.raises(kc.ConfigError):
            kc.read_config(str(p))


def test_legacy_config_name_still_found(vault, tmp_path_factory, capsys):
    legacy = vault / "knowledge-graph.yaml"
    legacy.write_text("kgConfigVersion: 1\ngraphRoot: KG\nprofile: KG/Profile.md\n", encoding="utf-8")
    sub = vault / "KG" / "Deep"
    sub.mkdir(parents=True, exist_ok=True)
    assert kc.find_config(str(sub)) == str(legacy)
    assert kc.load(vault=str(vault)).profile == str(vault / "KG/Profile.md")
    # init refuses to add a second config beside the old one
    assert kc.main(["--vault", str(vault), "init", "--graph-root", "KG", "--profile", "KG/Profile.md"]) == 2
    assert "knowledge-graph.yaml already configures" in capsys.readouterr().err
    # the new name wins when both are present
    new = make_config(vault, "kgConfigVersion: 1\ngraphRoot: KG2\nprofile: KG2/Profile.md\n")
    assert kc.find_config(str(sub)) == str(new)


def repo(tmp_path):
    r = tmp_path / "repo"
    (r / ".git").mkdir(parents=True)
    (r / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (r / "notes" / "deep").mkdir(parents=True)
    return r


def test_a_new_graph_goes_at_the_root_of_the_repository_it_is_started_in(tmp_path, monkeypatch, capsys):
    r = repo(tmp_path)
    where = kc.default_location(str(r / "notes" / "deep"))
    assert where == {"vault": str(r), "graph_root": "Competency_Graph", "graph": str(r / "Competency_Graph"), "in_repo": True}
    # init with no --vault and no --graph-root, from a subfolder: the config and the graph land at the repository's root
    monkeypatch.chdir(r / "notes" / "deep")
    assert kc.main(["init", "--profile", "Competency_Graph/Profile_A.md"]) == 0
    cfg = kc.read_config(str(r / kc.CONFIG_NAME))
    assert cfg.vault == str(r) and cfg.graph_root == str(r / "Competency_Graph")
    assert cfg.folders["competencies"] == str(r / "Competency_Graph" / "Competencies")
    assert kc.main(["where"]) == 0
    said = capsys.readouterr().out
    assert f"vault:  {r}" in said and "already configures this vault" in said


def test_outside_a_repository_the_graph_is_one_folder_in_documents_found_from_anywhere(tmp_path, own_home, monkeypatch):
    plain = tmp_path / "plain"
    plain.mkdir()
    docs = own_home / "Documents"
    where = kc.default_location(str(plain))
    assert where == {"vault": str(docs / "Competency_Graph"), "graph_root": ".", "graph": str(docs / "Competency_Graph"),
                     "in_repo": False}
    monkeypatch.chdir(plain)
    assert kc.main(["init", "--profile", "Profile_A.md"]) == 0
    cfg = kc.read_config(str(docs / "Competency_Graph" / kc.CONFIG_NAME))
    assert cfg.vault == cfg.graph_root == str(docs / "Competency_Graph")       # the vault is the graph folder itself
    assert cfg.folders["competencies"] == str(docs / "Competency_Graph" / "Competencies")
    assert cfg.folders["outputs"] == str(docs / "Competency_Graph" / "Outputs")
    # no config in this folder or above it: the one in Documents is the one found
    assert kc.load(start=str(plain), required=True).path == str(docs / "Competency_Graph" / kc.CONFIG_NAME)
    # a nearer config still wins over it
    make_config(plain)
    assert kc.load(start=str(plain)).path == str(plain / kc.CONFIG_NAME)


def test_documents_follows_the_desktops_own_setting_and_a_home_repository_is_not_a_project(own_home, monkeypatch):
    (own_home / ".config").mkdir()
    (own_home / ".config" / "user-dirs.dirs").write_text('XDG_DESKTOP_DIR="$HOME/Desktop"\nXDG_DOCUMENTS_DIR="$HOME/Papers"\n')
    assert kc.documents_dir() == str(own_home / "Papers")
    (own_home / ".config" / "user-dirs.dirs").write_text('XDG_DOCUMENTS_DIR="$HOME/"\n')     # a desktop with no Documents
    assert kc.documents_dir() == str(own_home / "Documents")
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(own_home / "Docs"))
    assert kc.documents_dir() == str(own_home / "Docs")
    # dotfiles kept in git at the home folder: not a repository to put a graph at the root of
    (own_home / ".git").mkdir()
    (own_home / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (own_home / "work").mkdir()
    assert kc.default_location(str(own_home / "work"))["in_repo"] is False
    # and an empty `.git` folder is no repository at all
    (own_home / "work" / ".git").mkdir()
    assert kc.git_root(str(own_home / "work")) == str(own_home)


def test_a_vault_with_no_config_uses_its_older_graph_folder_where_that_is_the_one_there(tmp_path):
    new = tmp_path / "new"
    new.mkdir()
    assert kc.load(vault=str(new)).folders["competencies"] == str(new / "Competency_Graph" / "Competencies")
    old = tmp_path / "old"
    (old / "Knowledge_Graph").mkdir(parents=True)
    assert kc.load(vault=str(old)).folders["competencies"] == str(old / "Knowledge_Graph" / "Competencies")
    (old / "Competency_Graph").mkdir()
    assert kc.load(vault=str(old)).folders["competencies"] == str(old / "Competency_Graph" / "Competencies")
