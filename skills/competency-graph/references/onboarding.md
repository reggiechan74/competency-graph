# Onboarding a new owner (`--buildnew`)

Read this when the skill is invoked with `--buildnew`, or when someone with no graph wants to start one from scratch. It takes a completely new owner from nothing to a working config, a profile and a list of their own records, then hands over to *Building a graph* in `SKILL.md` (steps 2–7). Its job is the decisions that come before the first competency: **where every personal file goes** and **where the owner's own resume material lives**. The owner makes each of these decisions; Claude proposes defaults and checks them.

## Contents

1. Start clean
2. Choose where everything goes
3. Point to the owner's own records
4. Write the config and check it
5. Write the profile
6. Choose frameworks
7. Hand over to the build
8. Done when

---

## 1. Start clean

`--buildnew` means **a new owner**, even when the current folder already holds someone's graph. Don't resume, read or copy anything that belongs to another owner.

- **Find out whose vault this is.** Run `kg_config.py show` from where the owner wants their graph. The lookup walks up through parent folders, and failing that reads the one in `Documents/Competency_Graph`, so it can find **another owner's** `competency-graph.yaml` higher up (for example, the skill's author's own repository) or a graph already kept in this machine's Documents folder. If it finds one, say so and don't use it: the new owner's config goes in their own vault root, and every script call passes `--vault <their root>` until that config exists.
- **Don't nest one owner's vault inside another's.** Links resolve by filename across the whole vault, and the checker scans all of it, so two owners' notes in one vault collide (two `Valuation.md` files make every link to either ambiguous). Use a separate repository or folder. If the owner insists on a subfolder of someone else's vault, the other owner must add it to their profile's `kgExclude`, and the new owner's vault root is that subfolder.
- **Carry over nothing personal.** Never copy another owner's profile, notes, requirements file (its `pathway_note` and `selected` columns are theirs), dashboard page, claims or outputs. The skill's library (`assets/`) is generic and is the only thing to start from. Where a library file carries one author's own wording, say so when offering it (§6).
- **Check the tools.** `python3 -c "import yaml"` must work; if PyYAML is missing, ask before installing it. Ask whether the vault is a git repository and whether the owner wants a commit after each approved step (rule 10).
- **Get today's date from the shell** for every date written (rule 5).

## 2. Choose where everything goes

Run `kg_config.py where` from the folder the owner is working in: it prints the default vault root, graph folder and config path for that folder. Show this table with the defaults filled in, and let them change any line. Ask about the lines that matter most to them (usually the vault root, the graph root and outputs) and accept the defaults for the rest unless they object. Every path is relative to the vault root, or absolute.

| What | Config key | Default | Constraint |
|---|---|---|---|
| Vault root: the folder links resolve within | (where `competency-graph.yaml` lives) | **In a git repository:** the repository's root. **Anywhere else:** `Competency_Graph` in the owner's Documents folder | One owner per vault (§1) |
| Graph root | `graphRoot` | **In a repository:** `Competency_Graph` at its root. **Anywhere else:** `.`, the vault itself, so that one folder in Documents holds everything | Inside the vault |
| Profile: settings and the decision log | `profile` | `<graphRoot>/Profile_<Owner>.md` | Inside the vault |
| Competency notes | `folders.competencies` | `<graphRoot>/Competencies` | Inside the vault; subfolders allowed |
| Sector notes | `folders.sectors` | `<graphRoot>/Sectors` | Inside the vault |
| New evidence notes | `folders.evidence` | `<graphRoot>/Evidence` | Inside the vault. Existing record files stay where they are (rule 2) |
| Proposals, pass tests, worksheets | `folders.working` | `<graphRoot>/Working` | Anywhere |
| Checker reports and JSON exports | `folders.reports` | `<graphRoot>/Working` | Anywhere |
| Material made for a reader: requirement tables, evidence packs, CV material, summaries, the dashboard copy | `folders.outputs` | `<graphRoot>/Outputs` | Anywhere; some owners use their applications folder |
| Framework requirements file | `requirements` | `<graphRoot>/Competencies/Framework_Requirements.csv` | Inside the vault; only if the owner picks frameworks (§6) |
| Framework descriptions file | `descriptions` | beside the requirements file (`Framework_Descriptions.csv`) | Inside the vault |
| The owner's own frameworks | `ownFrameworks` | `<graphRoot>/Frameworks` | Inside the vault. Read once it holds a `catalog.yaml`, which `frameworks.py new` writes (§6) |
| Job specs | `jobSpecs` | `<graphRoot>/Competencies/Job_Specs.yaml` | Inside the vault |
| Dashboard title, classification name, disclosure | `dashboard` | "Competency portfolio", "top-level industry", `on-request` | Only if they want a dashboard |
| Date prefix on files Claude names | `datedFilenames` | `true` | |

**What the two defaults mean for the owner.** In a repository the owner's existing files (job write-ups, a resume folder) are inside the vault, so they can become evidence notes in place (§3). A graph in `Documents/Competency_Graph` is a vault of its own: records kept elsewhere in Documents are outside it, so they are read as `collect` sources and new evidence notes are written in the graph's `Evidence` folder. An owner who wants their existing files tagged in place names a wider vault root (the folder that holds both). The home folder of someone who keeps their dotfiles in git does not count as a repository, and the scripts find a graph in Documents from any folder.

Two further locations follow from these and need no key. Say them anyway, so the owner knows where everything lands:

- **The dashboard:** `<outputs>/Dashboard/` (the page, its data files and a manifest, written by `dashboard_build.py`; only if they want a dashboard, `dashboard.md`). It is rebuilt from the files above at any time, so nothing on it is lost with it except changes not yet applied.
- **Summary data files:** a dated folder per run under `<outputs>` (`summary_graph.py`).

Before writing anything, check the owner's conventions: required front matter, filename style, and field names that already mean something in their vault (rule 4). A folder name the vault already uses for something else is a reason to pick another.

## 3. Point to the owner's own records

The graph is built from the owner's own material, and the config records where it is, so later sessions and the checker can find it. Ask where they keep each kind of record **in their own repository**, then look at what is there before deciding anything.

**Ask for**, offering the owner's likely folder names as examples:

- a master resume or CV, and tailored versions;
- a resume source folder (job write-ups, achievement banks, one file per role);
- job history files, project write-ups, engagement or client files;
- a LinkedIn export, a GitHub account or organisation, a portfolio site;
- credentials, course certificates, publication and talk lists, awards;
- anything that must stay out (litigation, health, family, an employer's confidential material).

**Then, for each one:**

1. **List it; don't read it yet.** Show the files in the folder (names, types, dates) so the owner can confirm it's the right place and point out what is current, old or private. Read a file's contents only once the owner has said it is in scope.
2. **Decide its use with the owner:**
   - `evidence`: its files become evidence notes **in place**, by gaining front-matter keys, with the body untouched (rule 2). They must be inside the vault, since links resolve only there.
   - `collect`: read for candidate competencies, cited by file and heading, but not turned into notes. It may be outside the vault, for example a separate resume repository.
   - `ignore`: recorded so nobody reads it by accident.
3. **Note its disclosure default** (`public`, `on-request` or `confidential`) for the profile, and anything in it that must always stay confidential.
4. **Record it** in the config's `sources:` list (path, `kind`, `use`, an optional `note`) and in the profile's *Sources* table (`templates.md` §1, its section 3), with the same paths.

Rules for sources:

- **Never copy a source's content into the graph.** Evidence notes are the source files themselves (rule 2); collected competencies cite the file.
- **A source in another repository** is pointed to by its path. Don't clone a repository the owner hasn't asked to clone; ask for the local path, or read individual files with the platform's API if they ask.
- **Nothing from the sources leaves the owner's machine** except what they publish on purpose. Don't put a name, employer or file content into a web search, an external service or a shared artifact without asking.
- **If a source moves later**, fix its path in the config; the checker warns (`source`) about a configured source that no longer exists.

## 4. Write the config and check it

Write the config in one command with every location and source the owner chose. Leave out a flag to take its default.

```bash
S=<skill-dir>/scripts
python3 $S/kg_config.py where                      # the default vault root and graph folder from here
python3 $S/kg_config.py [--vault <vault root>] init \
  [--graph-root Competency_Graph] --profile Competency_Graph/Profile_<Owner>.md \
  [--competencies DIR] [--sectors DIR] [--evidence DIR] [--working DIR] [--reports DIR] [--outputs DIR] \
  [--requirements Competency_Graph/Competencies/Framework_Requirements.csv] [--descriptions FILE] \
  --source "Career/Resume=collect:resume-folder" \
  --source "Career/Jobs=evidence:job-history" \
  --source "Career/Private=ignore" \
  [--no-dated]
python3 $S/kg_config.py --vault <vault root> show
```

With no `--vault`, `init` takes the default place `where` printed: a repository's root with `--graph-root` defaulting to `Competency_Graph`, or `Documents/Competency_Graph` with the graph as the vault itself (there the profile is `Profile_<Owner>.md` and the other paths have no `Competency_Graph/` in front). `--source PATH[=USE[:KIND]]` repeats; `USE` defaults to `collect`. `init` refuses to overwrite an existing config (`--force` only if the owner says to replace it, after showing them the old one). It also refuses an invalid config and leaves no file behind: a graph folder outside the vault, or an `evidence` source outside it. Add a `note:` to a source by editing the file afterwards (`templates.md` §0 shows the shape).

Read `show` back to the owner: every folder, the requirements and descriptions files, and each source with **(MISSING)** beside any path that doesn't exist. Fix any line they question before going on. From here on, run the scripts from inside the vault (or with `--vault`), and they read everything from this config.

## 5. Write the profile

Run the rest of the *Step 1: Profile interview* in `SKILL.md`: conventions, industry classification, thresholds, disclosure defaults, and a real question for the pass test. Write `Profile_<Owner>.md` at the configured path from `templates.md` §1, with:

- *Setup*: the owner, the graph root, "`competency-graph.yaml` at the vault root", and any outputs location outside the graph;
- *Sources*: the same paths and uses as the config's `sources:`, each with its disclosure default;
- *Decision log*: one dated row for each choice made in §2 to §6, in the owner's words where they gave reasons.

Where files go stays in the config, and how the graph is judged stays in the profile (spec §9.1). Don't repeat folder paths in the profile beyond the *Setup* line.

## 6. Choose frameworks

Only if the owner wants to be measured against a professional body, a credential or a role framework. Show the library with `frameworks.py list --all`. For each framework, say what it is and where its text comes from:

- **Drafts:** say so before the owner picks one (its `status_note`).
- **One author's own frameworks** (the `Chan` frameworks) are drafts built from that author's practice; say so.
- **RICS APC descriptions:** the L1–L3 wording is one author's North American adaptation of RICS's definitions, and the L4 is the graph's own. Another owner, especially outside North America, may want RICS's official wording; offer to note that in their profile.

Record the chosen frameworks and pathways, with the owner's note for each ("qualified 2019", "assessor"), under `frameworks:` in the config. Then build the requirements and descriptions files at the locations from §2:

```bash
python3 $S/frameworks.py build      # writes `requirements`, and `descriptions` (or the file beside it)
python3 $S/check_graph.py           # the requirements file is checked: every level on L1-L4
```

**Everything the owner adds is saved in their own files, never in the plugin.** The plugin's library (`assets/frameworks/`) is read only: a plugin update replaces that folder, so anything written there would be lost. A framework the library lacks, a firm's own framework, the owner's own methods, tools and practice, and an owner's own wording for a shipped framework all go in their own frameworks folder (`ownFrameworks`, by default `<graphRoot>/Frameworks`):

```bash
python3 $S/frameworks.py new firm-method --name "Firm Method"     # an empty framework to fill in, with L1–L4 wording they approve
python3 $S/frameworks.py new firm-tools --name "Firm Tools" --no-pathways   # a competency library only, for job specs
python3 $S/frameworks.py new rics-apc --from rics-apc             # their own edition of a shipped framework, to reword
```

An own edition takes the shipped framework's place for this owner, under the same id and name, so their notes' `externalRef` still match. A framework other owners could use can be offered to the plugin's library through its repository; until a release ships it, it works from the owner's folder (`domains-and-classifications.md` §6).

## 7. Hand over to the build

Commit if the owner wants commits (one commit for the config and profile). Then continue with *Building a graph* in `SKILL.md` from **step 2**:

- read the configured `sources` with `use: collect` or `evidence` for candidate competencies;
- tag the `use: evidence` files in place when their placements are approved.

Summarise for the owner, in a few lines:
- where everything will be saved;
- which of their records the graph will read, and how;
- what comes next (candidate competencies from their sources, then domains).

## 8. Done when

- [ ] The owner's vault has its own `competency-graph.yaml`, and `kg_config.py show` lists the locations they chose, with no source marked (MISSING).
- [ ] No file from another owner was read into, copied into or linked from the new vault.
- [ ] Every record the owner named is in `sources:` with a use, and in the profile's *Sources* table with its disclosure default.
- [ ] `Profile_<Owner>.md` exists at the configured path, with the setup, sources and a decision-log row for each choice.
- [ ] If frameworks were chosen: `frameworks.py build` wrote both files where the config says, and `check_graph.py` reports no `requirements` errors.
- [ ] `check_graph.py` runs from the config alone (no `--vault` needed when run inside the vault) with 0 errors.
