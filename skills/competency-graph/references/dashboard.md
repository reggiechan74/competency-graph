# The competency dashboard

Read this when the owner wants their graph as a dashboard on claude.ai, wants to change claimed levels or job specs there, asks you to apply changes they saved on it, or needs it rebuilt. The page is `assets/dashboard/index.html`; it is built for the claude.ai **Dashboard** artifact type (the type called *Data*) and reads the files `dashboard_build.py` writes.

**The dashboard is a display, never a record.** Everything on it is rebuilt from the skill and the owner's files: the notes, `competency-graph.yaml`, the profile, the owner's own frameworks and the job specs file. A change made on the dashboard (a claimed level, a job spec, a framework selection) waits in its store until Claude writes it into those files (§4). If the dashboard disappeared, §7 rebuilds it with nothing lost but changes not yet applied.

## Contents
1. What the page shows
2. Building it
3. Refreshing it
4. Changes saved on the dashboard
5. Job specs
6. The framework requirements file
7. Recreating the dashboard
8. Pitfalls

---

## 1. What the page shows

| Tab | What it holds |
|---|---|
| **Overview** | Domains (claimed against supported level, units, organisations, years, recognition), evidence over time by domain, domains across industries, and how each domain's competencies are rated |
| **Competency frameworks** | Framework requirements by pathway: each requirement's mapped competency, **Evidence** (Meets, Short, None) and **Basis**, with group minimums on pathways grouped as Mandatory, Core and Optional (RICS APC, Chan AFSE, Chan AGEN, Chan CXMDS), and a sub-heading for each sub-group of a group (the specialisations within the Optional lists of the three Chan role frameworks) |
| **Job specs** | Roles the owner defines from framework competencies (Mandatory, Core, Optional, each with a required level): a verdict as claimed and as supported, a scorecard, an editor, and specs compared side by side (§5). A competency its framework lists in a sub-group (a specialisation) is shown under that sub-group in the scorecard and named with it in the editor and the comparison |
| **Rate personal competencies** | Every competency, with search, filters and a Claimed dropdown on each row |
| **Rating gaps** | Competencies rated above or below the evidence, with what is missing for the next level; where the graph has prerequisites, the claims that stand above one; and, once assessors have rated, the competencies they rate differently, with each one's rating |
| **General definitions** | Each rule and term, explained once |
| **Framework competency definitions** | The chosen pathway's competencies with a description and what L1–L4 mean for each |
| **Configuration** | The assessors who can rate the competencies (add, edit, delete), and which frameworks and pathways the framework tabs show |
| **Instructions** | How to use the page, for whoever opens it |
| **How this works** | What the page and the skill behind it are: the three parts, the graph's notes and links, how records are stored, where evidence comes from, how a supported level is worked out, frameworks and job specs, how the page is built, the dashboard's own database (where a saved change waits) and how that change reaches the notes. Static text and drawings, the same for every owner |

The two framework tabs (Competency frameworks, Framework competency definitions) and Configuration's frameworks card appear only for an owner with frameworks; `dashboard_build.py` cuts them otherwise. Every Claimed cell is a dropdown; changes stay on the page until **Save changes** writes them to the `claims` collection (§4). The page never edits the notes. Confidential evidence never reaches it (§2).

The full design (every card, the gap marker and colour roles, keyboard and screen-reader behaviour, empty and error states, narrow panes, the build markers) is in `assets/dashboard/DESIGN.md`. Read it only before changing the page itself.

## 2. Building it

1. Run `dashboard_build.py`. It writes, to `<outputs>/Dashboard/` (or `--out`):
   - the page: `index.html`, `dashboard.css` and `dashboard-1.js` … (the template with the owner's settings written in, below, its style and scripts in files of their own, which `index.html` loads; the dashboard's store holds at most 256 KB a document, and the page in one piece is over that). `--one-file` keeps it in one `index.html` and stops if that file would not fit the store, as the shipped template no longer does;
   - `data/`: `domains.json`, `competencies.json`, `timeline.json` and `sectors.json` (the graph summary at the chosen disclosure; a competency row carries its prerequisites in `requires`, a sector row its sector's `code`, and an organisation is named by its organisation note where it has one), `descriptions.csv` (every framework competency, the owner's own frameworks included, with the sub-group a pathway lists it in, `subgroup` and `subgroup_order`, which only this data file carries), `jobspecs.csv` (the job specs file), `assessors.csv` (the config's `assessors:`, a header alone when there are none) and, with frameworks, `requirements.csv`;
   - `manifest.json`: the dashboard's title, the page's version (`pageVersion`, the number the page shows at its top right; it is the template's, the same for every owner, and `DESIGN.md` says when to change it), the page's files (`files`), and each data file's dataset id, title, description and format.

   Disclosure is the config's `dashboard.disclosure`, else `on-request` (`--disclosure public` for a page shared openly). It refuses `confidential`: everyone who can open the dashboard can read the whole data files. Job specs that don't validate stop the build.
2. Create the artifact from the Dashboard type (the Artifact tool's quickstart names it), titled with the manifest's `title`.
3. Upload each file in `data/` as an asset of that artifact (one call per file).
4. Write, in one batch:
   - `dash/meta`: `{title}`.
   - `datasets/<id>` for each manifest entry: `title`, `description`, `source: {kind: "file", url: <the asset url>, name, format}`, `updated: {at, by}`, `edit: {via: "claude", at}`, and `fixed: true` where the manifest says so.
   - `files/<name>`: `{text}` = the built file, for every file in the manifest's `files` (`index.html`, `dashboard.css`, each `dashboard-N.js`), each with `edit: {via: "claude", at}`.
5. Confirm that the page loaded what was published. Open the artifact (the Artifact tool's `open`), then read the type's own `check` and `runs` documents (in `data/users/me`) and fix what they report. The page writes them in a viewer's browser, so they say nothing until someone has the page open, and `runs` is removed again once everything loads. The publish is not finished until no dataset in `runs` has `status: "failed"`: each one just uploaded reads `ok` with its row count, or `runs` is gone. A file dataset that failed with "Couldn’t load the file (404)" just after its upload is seldom a bad file. The copy of the page that asked was refused it, and a page does not ask again for a file that failed, so the failure stays in `runs` until the page is reloaded. Read the asset back (the Artifact tool's `read`, with the asset's id as `path`) to confirm it is in the store, ask the owner to press **Reload data** in the bar the page shows under its tabs while a file has failed (it asks for the failed files again, with no page reload; reloading the page does the same and drops unsaved changes) and keep the page in view, then read `runs` again: the same address loads. Upload the file again as a new asset, and point its dataset at the new address, only when Reload data and a freshly loaded page both still fail. A calculation that failed because a dataset had not loaded runs again when the page is reloaded.

**The owner's settings in the page** come from the config's `dashboard:` block and the profile, never from hand edits, so the page can be rebuilt from the template at any time:

| In the page | From |
|---|---|
| The `<h1>` title | `dashboard.title` (default "Competency portfolio") |
| The sector sentences ("each NAICS Canada sector", "its NAICS Canada code") | `dashboard.sectors`, the classification's name (default "top-level industry") |
| The stale line and the Stale evidence item | the profile's `kgStaleYears` |
| The level thresholds in the Supported level item | `kgPractitionerMinMonths`, `kgAdvancedMinYears`, `kgExpertMinYears`, `kgExpertMinRecognition` |
| The two framework tabs, Configuration's frameworks card, their calcs, their definitions items, their Instructions lines, the How this works row on a saved framework selection and the header's framework words | cut when the owner has no frameworks (neither `frameworks:` nor a `requirements` file) |

The template marks each place with a comment (`<!-- kg:NAME -->…<!-- /kg:NAME -->`, in a script `/* kg:NAME */…/* /kg:NAME */`); `DESIGN.md` lists them. To change any of these, change the config or the profile and rebuild.

## 3. Refreshing it

After the graph, the config, the job specs or the library changes: run `dashboard_build.py` again, upload the changed data files as new assets, and `set` each changed dataset with its new `source.url`, `updated` and `edit`, pinning `if_version` to the version you read. Write the page's files (every one in the manifest's `files`) only when the template or the owner's settings changed, and read `files/index.html` first: the page may have been edited since. A dashboard made before the page was written in parts has one large `files/index.html`; writing the parts replaces it, and no other document needs removing. Finish every refresh with §2 step 5: a data file the page could not load leaves most tabs empty, and only the page's own `runs` document says so.

## 4. Changes saved on the dashboard

The owner's files stay the record. When the owner asks to *apply my dashboard changes*, export and apply all three collections, then clear what was applied and refresh (§3).

**Claimed levels (`claims`).** Each saved change is one document:

```
{key, note, framework, requirement, title, from, to, savedAt}
```

`note` is the competency's filename; `to` is `aware` … `expert`, or empty for Not rated. A level saved for a framework competency that is **not in the graph** has no `note`, and has `framework` and `requirement` instead.

**An assessor's rating** is saved in the same collection, one document for each assessor's rating of a competency (id `assessed--<assessor id>--<key>`, with `ckey`, the competency's key), with `field: assessedLevel`, `by` (the name of the assessor picked under Rate as assessor when the rating was made), `byId` (that assessor's id) and `on` (the day it was given, by the assessor's own clock; `savedAt` is UTC); `from` and `to` are the assessed level before and after. `claims_plan.py` turns it into an `assessedLevel` entry with `assessedBy` and `assessedOn` (the document's `on`, else the day of `savedAt`), so step 3 writes it into the note's `assessments` in place of that assessor's last rating, and leaves the other assessors' ratings and the owner's claim alone. A rating put back to Not rated removes only that assessor's. A rating saved with no name is skipped and reported: ask who gave it. Apply the assessors (below) in the same pass, so the name a rating is recorded under is one the config lists.

1. Export: ArtifactData `list`, `collection: claims`, `out_dir: <scratch folder>`.
2. `claims_plan.py --from <that folder>` writes an `edit_links.py` plan (`set` for a level, `unset` for Not rated) to the working folder, and lists new-competency requests separately.
3. `edit_links.py plan <file>` (dry run), then `--apply --touch <today>`; run the checker.
4. For each new-competency request, propose its placement (ground rule 1). Once the owner approves, create the note with the level and its `externalRef`, then link evidence as usual.

**Job specs (`jobspecs`).** One document per spec saved on the Job specs tab: `{id, title, note, next, probation, exceeds, rows: [{section, order, framework, name, required}], savedAt}`, or `{id, title, deleted: true}` for a spec in the file that was deleted there.

1. Export the `jobspecs` collection as above.
2. `job_specs.py merge --from <folder>` (dry run: it lists what it adds, changes and deletes), then `--apply`. It refuses specs that would leave the file invalid.
3. Show the owner what changed, in a line per spec.

**Framework selection (`settings/frameworks`).** `{selected: ["RICS APC|Valuation", …]}`, saved on the Configuration tab; the page shows it instead of the config's selection until it is applied.

1. Export the `settings` collection.
2. `frameworks.py apply --from <folder>` (dry run: it prints the new `frameworks:` block), then `--apply`. It rewrites only that block of `competency-graph.yaml`, keeps every note, and keeps a framework with nothing selected under `pathways: []` so its notes survive.
3. `frameworks.py build`.

**Assessors (`settings/assessors`).** `{list: [{id, name, role}], savedAt}`, the whole list as it stands after the last add, edit or delete on the Configuration tab; the page shows it instead of the config's `assessors:` until it is applied.

1. Export the `settings` collection (the same export serves the framework selection).
2. `assessors.py apply --from <folder>` (dry run: it prints the new `assessors:` block and what was added, removed, renamed or given a new role), then `--apply`. It rewrites only that block of `competency-graph.yaml`. Removing an assessor touches no note: the ratings they gave stay under their name.
3. A renamed assessor: `--apply` also writes a plan (`Assessor_Renames.yaml` in `working`) for the notes that record a rating under the old name. Show it to the owner, then `edit_links.py plan <file>` (dry run) and `--apply`.

**Then:** delete the applied documents (one batch, each pinned to its version), rebuild and refresh (§3), and record the change in the profile's decision log. A dashboard made before the page had an assessors list has no `assessors` dataset: upload `assessors.csv` and write `datasets/assessors` as §2 does for a new dashboard.

## 5. Job specs

A job spec is a role the owner defines from **framework competencies**: the skill's frameworks and the owner's own (§6). The record is the job specs file (`jobSpecs` in the config; default `Job_Specs.yaml` in the competencies folder); the format is in `job_specs.py`'s docstring:

```yaml
specs:
  manager-acquisition:
    title: Manager, Property Acquisition
    next: senior-manager-acquisition      # optional: the next role up, for the promotion test
    probation: 80                         # optional (%); exceeds: 20 likewise
    mandatory:
      - {ref: "RICS APC: Ethics, Rules of Conduct and professionalism", level: L3}
    core:
      - {ref: "RICS APC: Valuation", level: L2}
    optional:
      - {ref: "CFA CBOK: Alternative Investments", level: L1}
```

A competency goes in one section of a spec. The checker validates the file (`jobspecs`): every `ref` in the library, every level L1–L4, every `next` a spec.

**Scoring** (the page and `job_specs.py score` agree; the tests check it). For each Mandatory and Core competency, with required level r and level held a (the highest among the graph's competencies whose `externalRef` names it, as claimed, as assessed or as supported; the assessed basis appears on the page once the graph holds an assessor's rating or one is being entered):

- **Breadth** credits min(a, r) of r; **depth** credits the weight of min(a, r) of the weight of r, the weights being 1, 3, 9, 27 for L1–L4.
- **Credit above the requirement**: the weight of a minus the weight of r, when a > r, kept apart so it never fills a gap. Everything held in Optional counts there too.
- **Mandatory gate**: any Mandatory competency below its level gives *Mandatory not met*, whatever the totals.
- **Band**, by the lower of breadth % and depth %: *Below probation* (under the spec's `probation`, default 80), *Probation*, *Baseline* (every requirement met), *Exceeds role* (Baseline, plus Mandatory and Core credit above the requirement worth at least `exceeds`% of the depth target, default 20).
- **Promotion**, only with `next`: this spec at Baseline or better, and the next spec's gate met with its lower score at or above its own probation floor.
- **Diagnosis**: depth % below breadth % is *broad but shallow* (the shortfalls are where higher levels are required); breadth % below depth % is *deep but narrow* (lower-level requirements are missing).

`job_specs.py score <id> [--basis supported]` prints the same verdict in the terminal, for a CV or application conversation.

## 6. The framework requirements file

**Build it from the library.** The skill ships preconfigured frameworks in `assets/frameworks/` (`catalog.yaml` plus one file each, already on L1–L4). The owner selects them in `competency-graph.yaml`:

```yaml
requirements: Competency_Graph/Competencies/Framework_Requirements.csv
frameworks:
  rics-apc:
    pathways: [Valuation, Commercial real estate]   # omit for every pathway; [] for none (the notes are kept)
    notes: {Valuation: qualified 2019}
  cfa-cbok: {}
```

`frameworks.py build` writes the requirements file with **every** library pathway (each rule without the page numbers and table text copied in from the guides' PDFs), a `selected` column (yes/no) from that config and the owner's `pathway_note`, so the dashboard's Configuration tab can offer them all. A selection saved on the Configuration tab waits in the store (`settings/frameworks`) until `frameworks.py apply` writes it into the config (§4).

**The owner's own frameworks.** `ownFrameworks: <folder>` in the config names a folder in the library's format (its own `catalog.yaml` and files), kept in the owner's vault. They join the library under their own ids and names, which must not repeat the skill's. An own framework may have only a `descriptions` file and no requirements `file`: a competency library with no pathways, offered to job specs but not on the framework tabs. This is where an owner's practice competencies go when no professional body has them (`domains-and-classifications.md` §6). A framework that other owners could use goes in the skill's library instead.

The file's columns:

A CSV the owner keeps in their vault (e.g. beside the mapped competencies), one row per competency per pathway:

| Column | Meaning |
|---|---|
| `selected` | `yes` or `no`: shown on the Competency frameworks tab (written by `frameworks.py build`) |
| `framework` | The framework, written exactly as in `externalRef` before the edition year: `RICS APC` matches `"RICS APC 2025: Valuation"` |
| `pathway` | The pathway, route or specialism |
| `pathway_note` | Optional, shown in the pathway dropdown (e.g. "qualified 2019") |
| `group` | Mandatory, Core, Optional, or the framework's own words; groups show in file order. Mandatory is shared by every pathway in the same field, Core is the baseline of that pathway only, and Optional is the person's choice (`domains-and-classifications.md` §6) |
| `subgroup` | Optional: a sub-group inside the group, such as a specialisation within Optional. The page heads each sub-group once, the sub-groups in file order (keep a sub-group's rows together in the file). A `rule` shared by the group's rows still covers the whole group, so the sub-groups say where a competency belongs, not how many to choose from each |
| `order` | The file's own order within the group (the framework's guide order). The page lists a group's competencies alphabetically, keeping rows under one printed rule or in one sub-group together |
| `name` | The competency, exactly as after the colon in `externalRef` |
| `required` | Only `L1`–`L4`; `L2 or L3` (where the framework lets the candidate choose which reach L3); or `choice` (the candidate picks it; the minimum is L2). Map the framework's own levels onto L1–L4 first (spec §3.8); name the file as `requirements` in `competency-graph.yaml` and the checker enforces this |
| `rule` | Optional selection rule, shown above the rows it applies to ("One to L3 and one to L2 from this list") |
| `framework_status` | Optional: `draft` for a framework still under review (the catalog's `status`, written by `frameworks.py build`); blank when released. The dashboard tags a draft framework on the Configuration tab, in the pathway dropdown and above its pathway table |
| `framework_status_note` | Optional: why the framework is a draft (the catalog's `status_note`), shown beside the tag |

`assets/dashboard/requirements_example.csv` shows the shape, and `assets/dashboard/descriptions_example.csv` the descriptions file for the same competencies. Take requirements from the framework's current published guides and say which edition; bodies revise them every few years.

**The descriptions file.** `frameworks.py build` also writes, beside the requirements file, the descriptions file (`Framework_Requirements.csv` gives `Framework_Descriptions.csv`; `--descriptions` names another): one row per framework competency, own frameworks included, from each framework's `descriptions` file (`<id>-descriptions.csv`), with columns `framework`, `name` (as in the requirements file), `description`, `l1`, `l2`, `l3`, `l4` and `source`. The Framework competency definitions tab and the Job specs editor read it. Every column is filled; the tests check that each shipped framework's file has exactly one row per competency its requirements name. `source` says where each part came from, and text drafted for the graph says so: a body's own scale often stops short of L4 (RICS APC stops at Level 3, so its L4 is the graph's "recognised authority beyond their own team" written for each competency), and some frameworks publish no level descriptors at all (CFA CBOK, ASQ CSSGB), so all four are drafted from the body of knowledge. The RICS APC rows take L1–L3 from the owner's North American wording (Reggie Chan's RICS-APC-prep repository, `skills/<competency>/SKILL.md`) and fill the levels it leaves blank from RICS's December 2025 Requirements and competencies guide, and the Data analytics and intelligence pilot competencies from its September 2026 guide.

## 7. Recreating the dashboard

When the dashboard is lost, or the owner wants a fresh one:

1. If the old dashboard can still be opened, apply its saved changes first (§4); they exist nowhere else.
2. Run the checker (0 errors), `frameworks.py build` if the owner has frameworks, and `dashboard_build.py`.
3. Follow §2 from step 2, with the manifest's title. Record the new link in the profile's *Setup* table.

Nothing else is needed: the page, every data file and the scoring come from the skill and the owner's files. `test_dashboard.py` builds a dashboard from a sample vault this way and runs the page.

## 8. Pitfalls

- A list column (`externalRef`) reaches the page as JSON text, not an array. Parse it (`window.spRefs`).
- A wikilink inside a Markdown table needs `\|` (`[[Note\|Title]]`); a bare `|` splits the row. `query_graph.py framework --links` writes it that way.
- Page code may write to the store only when someone presses a control that says so. Dropdown changes and a spec being edited are held on the page until **Save changes** or **Save spec**.
- A drawing that sets `hidden` on itself never runs again. Empty it instead.
- A class that sets `display` (the tab panels are grid, the save bar is flex) beats the `hidden` attribute. Keep `.sp [hidden] { display: none !important; }` at the top of the style, or every tab shows at once.
- Outside a drawing, a script may only set `class`, `style`, `hidden` and the other attributes the one-writer rule allows. The Rate count line is its own drawing (`ratecount`), redrawn with `alltable` whenever a filter changes, the `domaintable` drawing shows or hides the Show/Hide unrated domains pair, and the `pathwaytable` drawing the Show/Hide unrated competencies pair (`hidden` only). The draft-framework note above each pathway table works the same way: the table's drawing sets only its `hidden`, and its words are their own drawings (`pathdraftnote`, `defdraftnote`); a table drawing that set the note's text would be a stray write. On Job specs, the buttons' `disabled`, the editor card's `hidden`, the Score on pair's `aria-pressed` and the form fields' `value` are set outside drawings; everything else is drawn. `page_harness.js` checks this rule when the tests run.
- The column headings of the tables with Claimed dropdowns carry static ids (`r-claimed`, `p-name`, `j-claimed`, …) that the drawings' `headers` attributes point to. Keep the ids when you change a table's columns, and give a new column one.
- Text hidden for sight but kept for screen readers (`position: absolute`, clipped) inside a sideways-scrolling table needs a positioned ancestor inside the scroller (the pill is `position: relative`), or it is placed against the page and widens it.
- The Dashboard type's stylesheet resets every element: a `ul` or `ol` has no markers unless the page's own style gives them back (`.sp-ref`, `.sp-howto` and `.sp-dtext` lists do). The tests run the page with stand-in tokens and no reset, so they can't show a missing marker. Before publishing a change to the page, run `scripts/tests/render_page.py --css app.css` (`DESIGN.md`, *Build markers*): it pictures every tab under the type's real stylesheet and names a list that lost its markers.
- The How this works tab describes the skill itself. A change to a note type, a link, a counting step, where a file is kept, a store collection or a script's job changes that tab too (`DESIGN.md`).
- Everyone who can open the dashboard can read the assessors' names and roles: they are in `assessors.csv`, in `settings/assessors` once edited, and beside each rating. Say so before an owner adds someone, as the Assessors card does.
- A mark whose data file has no rows gets `data-dash-source-state="empty"`, and the page turns such a mark's text transparent (a headline number with nothing to say). The assessors' file is empty for most owners while its marks still have a button and a status line to show, so their rule gives the colour back; a new mark on a file that can be empty needs the same.
- A store document holds at most 256 KB. `dashboard_build.py` refuses to write a page file over that and says so above 80%; when a script nears it, split that `<script>` in the template.
- The stale line and the header's "As of" date come from `asOf` on the timeline rows, the day the graph was read. A timeline file built before that field falls back to the latest date in it.
- An asset upload can time out. One retry is safe.
- After any rebuild, upload the changed files again and point their datasets at the new assets: the page reads the uploaded copies, not the vault's.
- Everyone who can open the dashboard can read every attached file, however little the page shows.
