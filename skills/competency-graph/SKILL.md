---
name: competency-graph
argument-hint: "[--buildnew]"
description: Build and maintain a personal competency graph of what someone knows and the evidence that proves it, as markdown notes (Obsidian or any folder). It gives a discipline-first competency taxonomy, an industry-sector axis, evidence notes (jobs, projects, repos, credentials, courses, publications) linked to competencies, computed support for claimed levels (L1 Aware to L4 Expert), staleness checks and cross-domain insights. Use it whenever someone wants to map, organise or taxonomise their skills, competencies or expertise; turn a CV, resume folder, job history or GitHub repos into a competency graph; add a job, project or credential to an existing graph; check which claims are supported or stale; rate their levels; map them to a professional body's competencies (e.g. RICS APC); write up or update the record of a job as it is done (an experience file, HAM-Z bullets); or pull the evidence behind a competency for a CV or application. Also use it when notes have front matter nodeType competency, skill, sector or evidence, or a Profile_*.md has kgSpecVersion, even if the user doesn't say "competency graph" (or the old name, "knowledge graph"). Invoke it with `--buildnew` to onboard a completely new owner: they choose where every personal file is saved and point the graph at their own resume sources.
---

# Personal competency graph

You help one person (the **owner**) record what they know as a graph of markdown notes, built from their own records, with every claim traceable to evidence. The method is in `references/specification.md`; the scripts in `scripts/` do the checking, querying and safe editing. Paths below are relative to this skill's base directory, so call them as `python3 <skill-dir>/scripts/<script>.py`.

## The model in one minute

Explain this to the owner in their own terms (with one of their examples) the first time, because the whole build depends on it.

| Layer | What it holds |
|---|---|
| 1. Taxonomy | Personal competencies (`competency` notes) in a tree of "X is a specialization of Y" links (`broader`), plus `sector` notes for industries |
| 2. Evidence | `evidence` notes (a job, a project, a credential...) that `demonstrates` competencies, sits in a `sector`, and may be `partOf` a larger piece of evidence |
| 3. Ontology | Named relations between competencies (`requires`, a prerequisite; `appliedTo`, a method or tool to the practice it serves), `organization` and `person` notes, and a short list of rules that read them (spec §3.10). Optional: a graph with none of it works as before |

- **Two kinds of competency, with two names.** A **personal competency** is a note in the owner's graph: something they know or can do, with their claimed level and the evidence linked to it. A **framework competency** is a row in a framework (a professional body's, or the owner's own): a requirement with a level for each pathway and wording for L1–L4, the same for everyone who uses the framework. `externalRef` on the note joins the two, and one personal competency can answer to several frameworks. Use these two terms with the owner. In this skill's files, "competency" alone means a personal competency, and the stored names (`nodeType: competency`, file and script names) keep the plain word.
- **The tree is organised by discipline (what you do); sector (where you did it) is a separate axis.** "Leasing" is a discipline within real property practice; "commercial real estate" is the sector where it was practised. Mixing the two gives nearly every competency two parents and hides the competencies that transfer between industries. `references/domains-and-classifications.md` has the full argument.
- **Methods, tools and standards get their own branches** under each domain (`<Domain>_Methods`, `_Tools`, `_Standards_and_Law`), because "Excel is a kind of Financial Modelling" is false. Practices link to them with `related`.
- **Store claims, compute conclusions.** The owner's `claimedLevel` is stored. Support, recency and years are computed by the checker from the evidence. Evidence that backs a narrow competency also backs all its ancestors. Projects inside a job collapse into one *independent unit*, so a job with five projects doesn't count five times.
- **A second person can rate the same competencies.** An assessor (a supervisor, counsellor, manager or peer) gives a rating that is kept beside the owner's `claimedLevel`, in the note's `assessments` (one "<assessor> | <level> | <date>" for each assessor); it never replaces the claim or the computed support, and a job spec can be scored on any of the three. Several assessors can rate the same competency: the assessed level is the lowest of their ratings, and the checker and the dashboard say where they differ (spec §3.9).
- **Four levels: L2 comes from delivered work, the top two from led work.** L1 `aware` (knows it), L2 `practitioner` (delivers it), L3 `advanced` (leads complex work and is accountable for it), L4 `expert` (a recognised authority beyond their own team). Outputs show the labels (L1 Aware … L4 Expert, or "not rated"); notes store the word, and `L3` is accepted on input. Evidence marks the competencies the owner *led* with `demonstratesLed` and outside recognition (credential, assessing, teaching, publication, adoption, appointment, award) with `recognition`. *Led* means the owner took the lead on that competency in that work (made the call, gave the reasoned advice, owned the result), not that they managed people; work done under someone else's direction is delivered. `practitioner` needs delivered work adding up to ≥6 months, led or not; `advanced` needs ≥2 units of led work at ≥2 organisations (or an anchor) over ≥5 years; `expert` adds ≥10 led years and ≥1 kind of recognition. A parent isn't expert just because many children were each touched once. Spec §3.7 gives the rule and its sources (Dreyfus, OPM/NIH, SFIA, RICS APC, FRICS).
- **Professional frameworks map through `externalRef`, not the tree.** A competency that matches a professional body's (RICS, CPA, a nursing or engineering regulator) carries `externalRef: ["RICS APC 2025: Leasing/letting"]`, and every framework's own levels are restated on L1–L4 with the owner's approval. Preconfigured frameworks (RICS APC, CFA CBOK, Six Sigma Green Belt and others) ship in `assets/frameworks/`; the owner selects them under `frameworks:` in the config, and `frameworks.py build` writes the requirements and descriptions files. Competencies no body defines can go in the owner's **own frameworks** (`ownFrameworks:`, a folder in the same format in their vault). `references/domains-and-classifications.md` §6 has the placement rules, the level mappings and the library.
- **Job specs score the graph against a role.** The owner defines roles from framework competencies in Mandatory, Core and Optional, each with a required level, in a job specs file (`jobSpecs:`); breadth and depth scores, a mandatory gate, bands and a promotion test say how the graph measures up (`references/dashboard.md` §5).

If someone asks "is this a taxonomy, an ontology or a competency graph?": a taxonomy is the tree of categories; an ontology adds typed relationships and rules; a competency graph is the connected data (here, competencies plus the evidence linked to them). They are building a competency graph: layers 1 and 2, with as much of layer 3 as they have a use for.

## `--buildnew`: onboard a new owner

When the skill is invoked with `--buildnew`, the person is a **new owner** starting from nothing: read `references/onboarding.md` and follow it before anything else, even if a graph exists in this folder or a parent (it may belong to someone else). It has the owner choose where every personal file goes (config folders, profile, requirements and descriptions files, outputs) and record where their own resume material lives (the config's `sources:`), writes the config and profile, and then hands over to *Building a graph* at step 2. Never resume, read or copy another owner's graph, profile or outputs while onboarding.

## First, find out where they are

Look before asking. First run `python3 <skill-dir>/scripts/kg_config.py show` (add `--vault <folder>` when the graph lives in a subfolder of where you are). It finds the nearest `competency-graph.yaml` (in this folder or a parent; failing that, the one in the owner's `Documents/Competency_Graph`, where a graph outside a repository is kept by default) and prints the vault, the profile and every output folder. Check that the config it found belongs to the folder the owner means: the lookup walks up through parent folders, so it can find an unrelated one higher up. Then search for a `Profile_*.md` with `kgSpecVersion` or `kgStaleYears` in its front matter, and for notes with `nodeType: competency|sector|evidence` (graphs made before v0.4 say `skill` for `competency`; the scripts read both).

- **Nothing found** → a new graph. Follow *Building a graph* from step 1 (or `references/onboarding.md`, which `--buildnew` uses, for the full setup).
- **A profile but no config file** → an older graph. Offer to create the config from the locations the profile records (see *Where files go*); until then pass `--vault` and `--profile` to every script.
- **A profile exists** → read it fully. Its milestone and decision log say what's done and what's next. Run the checker to see the current state, then resume. Never re-litigate a decision recorded in the decision log.
- **The request is a specific task** on an existing graph (add a job, answer "what supports X?", rate competencies, fix warnings) → go to *Working with an existing graph*.

Check `python3 -c "import yaml"` works before running scripts. If PyYAML is missing, ask before installing it (`pip install pyyaml`).

## Ground rules (and why)

1. **The owner approves every placement before a note is created.** Claude proposes; the owner decides. A self-taxonomy that the owner didn't shape is useless to them, and wrong placements are expensive to unwind once evidence links to them. Batch the proposals (see templates) so approval is quick.
2. **Reuse existing files; never copy their content.** An existing job-history file becomes an evidence note by gaining front-matter keys. Its body is untouched. Copies drift.
3. **Change links and controlled fields in existing notes only with `edit_links.py`**, never with regex or ad-hoc text replacement. In the pilot build a one-off regex *replaced* ten link lists instead of extending them. The editor dry-runs, checks targets exist and are the right type, keeps order, refuses a batch if any edit fails, and re-parses the file to prove nothing else changed. Creating a brand-new note with the Write tool is fine.
4. **Check the owner's conventions before naming fields or files.** If a field name already means something in their vault (e.g. `shareable`, `status`), don't reuse it. Record it as reserved in the profile. Filenames must be unique across the whole vault, because links resolve by filename.
5. **Never invent dates.** Use `YYYY-MM-DD`, or `YYYY-MM` / `YYYY` when that's all the source records. An undated project inside a job takes the job's period as an honest bound, with a comment saying so. Get today's date from the shell.
6. **`demonstrates` is an index, not proof.** When writing a CV line or answering "can I claim X?", read and cite the evidence note's *body* and its source file, not the tag.
7. **Match `disclosure` to the audience.** The three levels map to three audiences, so choose the filter by where the output is going:
   - **Something sent to a named reader**, such as a job application, a cover letter, a CV sent to one employer, or a brief for a client: use `on-request` and `public` evidence (`--disclosure on-request`). This is the purpose of `on-request`: evidence that can be named and shown to a specific person who asks. Leaving it out of an application drops most of the owner's work history.
   - **Something published or posted openly**, such as a website, a LinkedIn profile or a public portfolio: use `public` evidence only (`--disclosure public`).
   - **`confidential` never leaves the vault.** Don't name it, describe it, or hint at it, even to explain a gap.
   If the owner states a rule in their own words ("leave out anything confidential"), follow it as stated, and don't tighten it. Tell them which `on-request` items you used, so they can drop any they'd rather not share.
8. **Checks report; they never fix.** Stale and unsupported warnings are information for the owner. Marking a competency `dormant`, lowering a claim, or accepting a warning is their call.
9. **Cite sources by file and section heading** in note bodies. Line numbers drift (tagging a file adds front-matter lines). Line numbers are fine in short-lived proposals.
10. **If the vault is a git repo, commit after each approved step** (ask once whether they want that). Each domain then becomes a reviewable, revertible unit.

## Where files go

`competency-graph.yaml` at the vault root decides where every file is saved (a vault set up before the skill was renamed may have `knowledge-graph.yaml`, which works the same). The scripts read it too, so with a config they need no `--vault` or `--profile`. Every path in it is relative to the vault root; only `graphRoot` and `profile` are required, and each folder defaults to `<graphRoot>/<Name>`, except `reports`, which defaults to `<graphRoot>/Working` (template: `references/templates.md` §0).

| Folder key | What goes there |
|---|---|
| `competencies`, `sectors` | New competency and sector notes (subfolders allowed for browsing, e.g. `Competencies/RICS/`) |
| `evidence` | New evidence notes (`Projects/`, `Credentials/`, `Publications/`, `Engagements/`). Existing record files that become evidence stay where they are (rule 2) |
| `working` | Placement proposals, pass-test notes, rating worksheets, plan files |
| `reports` | Checker reports and JSON exports |
| `outputs` | Anything made for a reader: requirement-evidence tables, evidence packs, CV or cover-letter material |

- **Get the path from the config; don't build it by hand:** `kg_config.py path <key> <Name.md> --mkdir`. It adds the `YYYY-MM-DD_` prefix when `datedFilenames` is on (the default).
- **The owner's words win for that one file.** A folder or full path in the request is used as given. A bare filename ("save it as matches.md") goes into the configured folder under exactly that name (`--no-date`).
- **Never put working files or outputs in the graph folders.** The checker warns (`folder`) about competency or sector notes outside their configured folders.
- **Changing a folder later:** move the files (with `git mv` in a git vault), then edit the config, then run the checker. Links resolve by filename, so moving notes doesn't break them.

## Building a graph

The order matters: a thin slice proves the method on real material before the owner invests in the whole tree.

### Step 1: Profile interview

Ask conversationally, a few questions at a time, offering a sensible default for each. Write the answers into `Profile_<Owner>.md` using `references/templates.md` §1.

- **Sources.** Where their records are (CV files, a resume folder, job write-ups, LinkedIn export, GitHub account, credential lists, publication lists, course certificates). For each source decide: becomes evidence notes in place, used only for collecting competencies, or ignored. Record each under `sources:` in the config (`--source PATH=USE:KIND` on `init`) and in the profile's *Sources* table; the checker warns when a configured source goes missing.
- **Locations.** Where the graph goes, whether the vault is Obsidian, and where finished outputs should go (default `<graphRoot>/Outputs`; some owners prefer their applications folder). Offer the default first (`kg_config.py where` prints it for the folder you are in): **inside a git repository**, the repository's root is the vault and the graph is `Competency_Graph/` at that root; **anywhere else**, the graph is `Competency_Graph` in the owner's Documents folder, which is then the vault too, so one folder holds everything. The owner may name any other place. Write the config first: `kg_config.py init --profile <graph folder>/Profile_<Owner>.md [--outputs <dir>]` takes the default place, and `--vault <root>` with `--graph-root <dir>` names another. Run `kg_config.py show` to confirm it with the owner.
- **Conventions:** required front matter, filename style, existing fields to treat as reserved, and existing date fields to map to `period` (`kgPeriodAliases`).
- **Industry classification** for sector notes. Suggest one by country (NAICS, NACE, UK SIC, ANZSIC, ISIC; see `references/domains-and-classifications.md` §4).
- **Thresholds:** stale after how many years (default 5). The level thresholds default to 6 months of delivered work for practitioner, 5 led years for advanced, 10 for expert and one kind of recognition (`kgPractitionerMinMonths`, `kgAdvancedMinYears`, `kgExpertMinYears`, `kgExpertMinRecognition`); change them only if the owner's profession sets its own bar.
- **Frameworks.** Which professional bodies, credentials or role frameworks the owner wants to be measured against. Show the library (`frameworks.py list --all`); for any marked DRAFT, say it is still under review and why (its `status_note`) before the owner picks it. Record the chosen frameworks and pathways, with a note each ("qualified 2019", "assessor"), under `frameworks:` in the config. A framework the library lacks is added to the library later (§6 of `references/domains-and-classifications.md`).
- **Disclosure defaults:** for example, roles `on-request`, public repos `public`, everything else `confidential`. Also ask about anything that must always stay confidential (litigation, health, family).
- **A real question the graph should answer** for the thin-slice pass test (e.g. "which of my evidence fits this job ad?").

### Step 2: Collect candidate competencies

Read the sources and list candidate competencies, each with a citation. Prefer the concrete competency inside achievement bullets ("built a nightly HL7 feed" → data pipelines, HL7) over keyword lists. Then **scan the full documents for named methods, models, frameworks and tools that never became a bullet**: the pilot's first pass test failed on exactly such a model. Merge duplicates and near-synonyms (keep the variants as `aliases`).

### Step 3: Propose domains

Cluster the candidates into **domains named by discipline**: usually 3–8, fewer for a focused career, more for a long or varied one. Don't pad. Check the names against the reference standards in `references/domains-and-classifications.md` §2–3, and present them as a table with example disciplines, likely branches and a one-line reason each. The owner decides. Record the decision and reasons in the profile.

**Stop here until the owner has decided on the domains**, even when they've said to go ahead or to pick defaults. Don't draft placements for any domain in the same turn. Every placement hangs from a domain's name and boundary, so drafting placements early means redoing them when a domain changes, and a finished-looking tree pulls the owner toward accepting Claude's structure instead of shaping their own (ground rule 1). Candidates and domains are enough for one review.

### Step 4: Place competencies, domain by domain

For one domain at a time, write a **placement proposal** in the `working` folder (`references/templates.md` §2). It has batches of disciplines, then specialties, then methods/tools/standards, each row with its parent, `kind`, any `related` link and a source citation. Add numbered **judgment calls**: anything a reasonable owner might decide differently. List the candidates you left out, and why. End with the evidence plan: new evidence notes, and links to add to existing ones.

For each placement, apply the test "X is a specialization of Y". If it fails, the link is `related`, not `broader`. Allow a second parent only for a genuine overlap between two disciplines, never for a sector. Store `related` on one side only: the method, tool or knowledge note, or else the more specific practice.

Stop and wait for approval. Then create the notes (templates §3–5), apply the link edits with `edit_links.py` (dry run, then `--apply`), and run the checker.

### Step 5: Thin slice first (milestone M1)

Build one domain, with 2–3 roles, 1–2 credentials, 2–3 projects and the sector notes they need. Run the checker to zero errors, then do the **pass test**: answer the owner's real question from the graph alone (use `query_graph.py find` and `support`) and compare it with what they'd have found by hand. Write the result to the `working` folder as `M1_Test.md` (dated). A gap here usually means a collection miss, so go back to step 2 for that source. Record the outcome in the profile.

### Step 6: Expand one domain at a time

Repeat step 4 for each remaining domain, running the checker after each. Tag every remaining job file. When a role's `demonstrates` list would pass ~15 links, split the specific work into `project` notes with `partOf` pointing at the role.

### Step 7: Self-rating, anchors and review

- **Led work and recognition first.** Run `evidence_worksheet.py` and go through it **one unit at a time**, with the note body open: for each piece of evidence, propose which of its `demonstrates` competencies the owner *led* (they made the call, gave the reasoned advice, or owned the result) and what outside recognition it shows, quoting the line in the body that justifies each. Be sparing: led means accountable, not involved, and an entry-level certificate isn't `credential`. The owner decides; apply with `edit_links.py plan`. Without this pass nothing can reach `advanced` or `expert`.
- **Ratings.** Run `rating_worksheet.py` and walk the owner through it **one domain at a time**. Show each competency's evidence-supported level, units, organisations, years and staleness, and suggest a level. The owner sets it. Apply the worksheet with `edit_links.py plan`; blank `set:` entries are skipped. Rating domains, disciplines and specialties is usually enough; methods and tools can stay unrated.
- **Anchors.** For each independent unit with no `anchor`, ask what a third party could check: a public URL, a register or member ID, a DOI, a referee (a contact record path counts). Leaving an anchor blank is a valid choice; record it.
- **Review** the checker's insights with the owner: domain pairs (their positioning), competencies bridging domains, practices evidenced in several sectors (transferable competency), and stale claims.

## Working with an existing graph

| Request | What to do |
|---|---|
| "Record my work at …" / "Update my experience file" / a role with no write-up worth tagging | `references/recording-experience.md`: one record for each role (templates §7), built from what the work left behind: gather read-only, an evidence ledger, one batch of questions, bullets to the HAM-Z standard (a named tool, an action, a number from a source, the process; no number, no HAM-Z bullet), a fact-check, the sanitisation gate, then the graph links as a proposal. When the evidence is on an employer's machine, give the owner `assets/prompts/experience-update.md` to paste into Claude there, and take up the file it prints |
| "Add my new job / project / cert" | Read the source. Propose the evidence note (type, period, sector, partOf, disclosure, demonstrates) and any **new** competencies it needs, as a small placement proposal. Create or tag it once approved, then run the checker |
| "What supports X?" / "Can I claim X?" | `query_graph.py support X`, then read the listed evidence notes' bodies before answering |
| Job ad or CV tailoring | Save the result in the `outputs` folder unless the owner says where. For each requirement, `find` the matching competencies, then `support --disclosure on-request` (or `public` if the output will be posted openly). Read the evidence note bodies *and* the source files they cite: the source file may evidence a requirement no competency note covers, such as presenting to a council. Cite the note bodies and source files, mark which items are `on-request`, and say which requirements have no evidence |
| "Which claims are stale or unsupported?" | Run the checker and summarise the warnings in plain language, grouped by what the owner could do about each |
| "Summarise my graph" / a report or dashboard | `summary_graph.py --markdown` writes four row tables (domains, competencies, timeline, domain × sector grid) and `summary.md` to a dated folder in `outputs`. Choose `--disclosure` by audience (rule 7): the default `on-request` suits a page shared with a named person, `public` anything posted openly. For a visual, draw an **evidence timeline** (one lane per domain, units as bars, credentials as points, a line at the stale cutoff), the **domain × sector grid** and **claim vs. support** per domain beside the domain table. Avoid a whole-graph node-and-link diagram, which becomes unreadable past a few dozen notes. When the owner wants it on claude.ai, run `dashboard_build.py` and publish what it writes on the Dashboard artifact type, following `references/dashboard.md` §2, never from `confidential` output. The dashboard is a display: it is rebuilt from the owner's files, never edited by hand (§7 there recreates a lost one) |
| "Apply my dashboard changes" / changes saved on the dashboard | `references/dashboard.md` §4: export the `claims`, `jobspecs` and `settings` collections; `claims_plan.py` and `edit_links.py plan` for levels (propose placements for new competencies), `job_specs.py merge` for job specs, `frameworks.py apply` for a framework selection, `assessors.py apply` for the list of assessors; then clear the applied changes, rebuild and refresh |
| "Make a job spec for …" / "How do I measure up against this role?" | Propose the spec as a table (section, framework competency, required level, a reason each) for the owner to approve, write it into the job specs file, `job_specs.py check`, then `job_specs.py score <id>` (both bases) and explain the verdict; or point them to the Job specs tab to build it themselves |
| "Show me my tree" | `query_graph.py tree [<domain>] --depth N` |
| "What does X depend on?" / "Is my claim for X consistent?" / "Count these two employers as one" / "Who can vouch for this job?" | Layer 3, each added only when the owner has a use for it and each link approved like a placement (ground rule 1). A **prerequisite** is `requires` on the dependent competency (`edit_links.py add X requires Y`): the checker then reports a claim for X above the claim for Y, and changes neither. A method, tool or standard names the practice it serves with `appliedTo`. One employer written two ways becomes one with an `organization` note listing the spellings under `aliases` (templates §8); warn the owner first that a level resting on "two organisations" may fall, and show which (`query_graph.py organizations`, then the checker). A referee is a `person` note pointing at the owner's own contact record (`crm`), named in the evidence note's `referee`; it counts as an anchor. `query_graph.py relations X` shows what X requires and what requires it, what serves it and what certifies it. Don't add any of these in bulk or by guesswork: a prerequisite nobody asked for is a warning the owner has to argue with |
| "My supervisor / counsellor / manager is rating me" / "Assess <person> against this role" | The graph is the person being assessed; the assessor's ratings go in `assessedLevel`. Who can rate is a list in the config (`assessors:`, an id with a name and an optional role; `assessors.py list`), which the owner keeps on the dashboard's Configuration tab or asks you to edit. Either the assessor enters the ratings on the dashboard (pick them under **Rate as assessor**, then *apply my dashboard changes*), or run `rating_worksheet.py --assessor "<name>"` with the name as the config has it, have the assessor fill in `set` from the wording of each level (`frameworks.py build` writes the descriptions), and apply it with `edit_links.py plan`. Each assessor fills in their own worksheet or picks their own name: a rating replaces only that assessor's last, and no assessor is shown another's while rating. Never copy a claim into an assessed level, never change a claim to match a rating, and never change one assessor's rating to match another's: the gaps between them are what the review is for. When the checker says the assessors differ, tell the owner which competencies and by how much, and leave the ratings as they are. Then `job_specs.py score <id> --basis assessed` |
| Re-rate after new evidence | Regenerate the worksheet; walk through only the competencies whose `supports` changed |

## Scripts

With a `competency-graph.yaml` in the current folder or a parent, the scripts take the vault and profile from it. Otherwise (or to override it) pass `--vault <root>` (the folder links resolve within; usually the vault root, not the graph root) and `--profile <Profile_*.md>`, or `--config <file>`. All are read only, except `edit_links.py --apply`, `kg_config.py init`, and the report and worksheet files they're asked to write.

```bash
S=<skill-dir>/scripts
python3 $S/kg_config.py      show | path <key> <Name> [--no-date] [--mkdir]
python3 $S/kg_config.py      init --graph-root R --profile P [--<folder> DIR] [--requirements F] [--descriptions F] [--source PATH=USE:KIND ...] [--no-dated]
python3 $S/check_graph.py    [--report [out.md]] [--json [graph.json]]      # no file name: dated file in `reports`
python3 $S/query_graph.py    support <competency> [...] [--disclosure public|on-request|confidential]
python3 $S/query_graph.py    find "<phrase>" ["<phrase>" ...]
python3 $S/query_graph.py    tree [<competency>] [--depth N]
python3 $S/query_graph.py    framework "RICS APC" [--links]                      # every competency mapped to a framework
python3 $S/claims_plan.py     --from <exported claims folder> [--out plan.yaml]   # dashboard changes -> edit_links plan
python3 $S/frameworks.py      list [--all] | build [--out FILE] | apply --from DIR [--apply]   # the library; requirements file; dashboard selection -> config
python3 $S/assessors.py       list | apply --from DIR [--apply]                    # who rates the owner; the list saved on the dashboard -> config
python3 $S/job_specs.py       list | check | build | score <id> [--basis claimed|assessed|supported] | merge --from DIR [--apply]
python3 $S/dashboard_build.py [--out DIR] [--disclosure on-request|public] [--one-file]   # the whole dashboard from the files: page (in parts), data, manifest
python3 $S/query_graph.py    evidence <note>
python3 $S/query_graph.py    relations <competency> | organizations             # layer 3: prerequisites, what serves and certifies; organisations and their spellings
python3 $S/edit_links.py     add|remove <note> <field> <link|word> [...] [--apply] [--touch YYYY-MM-DD]   # also demonstratesLed, recognition, externalRef, aliases
python3 $S/edit_links.py     set <note> <claimedLevel|status|title|rank|disclosure|anchor> <value> [--apply]   # levels take L1-L4 too
python3 $S/edit_links.py     assess <note> <level|none> --by "<assessor>" [--on YYYY-MM-DD] [--apply]   # one assessor's rating; the others' stay
python3 $S/edit_links.py     plan <plan.yaml> [--apply] [--touch YYYY-MM-DD]
python3 $S/evidence_worksheet.py [--out <file>]                                # led work and recognition; default: `working`
python3 $S/rating_worksheet.py [--assessor "<name>"] [--out <file>]            # default: dated file in `working`; --assessor: the assessor's worksheet
python3 $S/summary_graph.py  [--disclosure on-request] [--markdown] [--out-dir D] # default: dated folder in `outputs`
```

- The checker exits 1 when there are errors. Fix every error before moving on. Warnings are for the owner to judge.
- `--touch` bumps an existing `lastUpdated` field. Use it if the vault keeps one.
- Link fields hold flat lists of quoted wikilinks: `demonstrates: ["[[Data_Pipelines]]", "[[Python]]"]`. A nested object, or an unquoted `[[A]]` (which YAML reads as a nested list), is an error.
- The tests for the scripts are in `scripts/tests/` (`python3 -m pytest <skill-dir>/scripts/tests -q`). The dashboard page's tests run it in jsdom (needs Node and jsdom) and in Chromium (needs Playwright); each is skipped when its tool is missing. They use stand-in styles, so before publishing a change to the page itself, also run `scripts/tests/render_page.py --css <the Dashboard type's app.css>` and look at its pictures (`assets/dashboard/DESIGN.md`).

## Talking with the owner

Owners range from engineers to people who have never seen YAML. Lead with their competencies and their evidence, not with field names. Show proposals as tables they can approve line by line, and explain a term such as "independent unit" the first time it matters to a decision. When a warning appears, say what it means for them ("your leasing evidence ends in 2021, so a reader would see it as five years old"), not just the code.

## Reference files

- `references/onboarding.md`: onboarding a completely new owner (`--buildnew`): where every personal file goes, pointing to their own resume sources, the config and profile, then the build.
- `references/specification.md`: the full method. Fields and allowed values (§2, §5), counting rules (§3), every check (§4), layout and naming (§6), build method (§8), profile keys (§9). Read §2–3 before creating notes, and §4 when interpreting checker output.
- `references/templates.md`: the config file, the profile, placement proposal, every note type and the plan-file format. Copy from here.
- `references/domains-and-classifications.md`: why the tree is discipline-first, standards for checking domains, and industry classifications and sector-coding rules. Read it for steps 1 and 3, and §6 for professional frameworks.
- `references/recording-experience.md`: how an owner records a job as it is done, the HAM-Z standard for a bullet, the sanitisation gate, and how a record becomes graph links. `assets/prompts/experience-update.md` is the same method as a prompt for a work machine.
- `references/dashboard.md`: building, refreshing, recreating and applying changes from the claude.ai dashboard, job specs and their scoring, the framework requirements file and the owner's own frameworks. The page's own design is in `assets/dashboard/DESIGN.md`, needed only to change the page.
