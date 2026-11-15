# Competency Graph Specification (v0.5)

A general method for recording one person's knowledge as a graph of plain markdown notes. It works without plugins in any folder of markdown files, and especially well in Obsidian.

**This file has no person-specific values.** The owner's choices (domains, industry classification, source files, file conventions, thresholds) live in a **profile** (§9) inside the owner's graph. The scripts named here ship with the `competency-graph` skill (for Claude Code) in its `scripts/` folder.

| Layer | Contents | In scope |
|---|---|---|
| 1. Taxonomy | `competency` notes (the owner's **personal competencies**) linked by `broader`; `sector` notes | Yes |
| 2. Evidence | `evidence` notes linked by `demonstrates`, `demonstratesLed`, `sector`, `partOf`, with `recognition` | Yes |
| 3. Ontology | Named relations between competencies (`requires`, `appliedTo`), `organization` and `person` notes, and the rules that read them (§3.10) | Yes, as far as §3.10 goes; what is left is in §11 |

**Two terms.** A *personal competency* is a `competency` note in the owner's graph: something the owner knows or can do, with a claimed level and evidence. A *framework competency* is a row in a framework's requirements and descriptions files (§3.8): a requirement with a level for each pathway and L1–L4 wording, the same for every owner. `externalRef` joins a personal competency to each framework competency it answers to. Where this file says "competency" alone, it means a personal competency.

---

## 1. Principles

1. **Each link is recorded once, on the more specific side.** A child records `broader`. An evidence note records `demonstrates`, `sector` and `partOf`. Inverse links (children, supporting evidence) are always worked out, never stored.
2. **The tree is organised by discipline; sector is a separate axis.** The competency tree holds what the person *does* (valuation, leasing, accounting). Where they did it is recorded as a link from evidence to a `sector` note. Combining the two in one tree gives nearly every specialist competency two parents and hides competencies that transfer between sectors.
3. **Several parents are allowed but should be rare.** `broader` is a list. Its **first** entry is the main parent, used for outlines. A second parent should be a genuine overlap between disciplines (e.g. appraisal automation = valuation + agentic engineering), not a sector.
4. **One test for every `broader` link: "X is a specialization of Y."** If a link fails, use `related`. Methods, tools and laws or standards fail this test against practices (VTS is not a kind of Leasing), so they get their own branches (§2.1).
5. **Reuse existing files.** Existing records (job histories, credential lists) become evidence notes by gaining fields. Their content is never copied.
6. **Never repurpose an existing field.** Check the owner's metadata conventions first. If a field name already means something, choose another name.
7. **Fields only mean something for their note type.** The check script reads only the fields defined here for that `nodeType`. Same-named fields left over in reused files (`status`, `related`, ...) are ignored.
8. **Folders don't hold the hierarchy; metadata does.** A tree where notes can have several parents can't be represented as folders. An owner may group notes in subfolders for browsing (e.g. `Competencies/RICS/` for the competencies mapped to a professional body); the scripts ignore subfolders, and a note keeps its place in the tree wherever its file sits.
9. **Links in metadata are flat lists of quoted wikilinks** (`["[[A]]", "[[B]]"]`). Obsidian shows these in backlinks and the graph view, but it does not support nested properties and does not label link types. The check script is what tells `broader` apart from `demonstrates`.
10. **Store claims, compute conclusions.** Notes store the owner's claims (`claimedLevel`). Evidence counts, recency and strength are always worked out. **Checks only report. They never edit notes.**
11. **`demonstrates` is an index, not proof.** Any tool that writes CVs or checks claims must cite the evidence note's *content*, never just the tag.

---

## 2. Note types

### 2.1 `competency`: one note per node in the discipline tree

| Field | Required | Values | Notes |
|---|---|---|---|
| `nodeType` | yes | `competency` | |
| `kind` | yes | `practice` \| `method` \| `tool` \| `knowledge` | `knowledge` = laws, regulations, standards (IFRS 16, a national appraisal standard) |
| `rank` | no | `domain` \| `discipline` \| `specialty` \| `element` \| `branch` | Display label only; depth is worked out. `branch` marks the root of a branch (below) |
| `broader` | yes, except domains | quoted wikilinks; first = main parent | |
| `related` | no | quoted wikilinks | Links that fail the specialization test. Symmetric, so stored on **one** side: the method, tool or knowledge note keeps it (it points at the practice it serves); between two practices, the more specific one |
| `sector` | no | quoted wikilinks to `sector` notes | Only for competencies tied to one sector (e.g. corridor valuation) |
| `requires` | no | quoted wikilinks to `competency` notes | **A prerequisite:** this competency cannot be held above the level of the one it names. A different competency, not one above or below it in the tree. The checker reports a claim that stands above a prerequisite's (§3.10) |
| `appliedTo` | no | quoted wikilinks to `competency` notes of kind `practice` | From a method, a tool or a piece of knowledge to **the practice it serves**: the named form of the `related` link that such a note keeps. `related` stays for a link between two practices |
| `claimedLevel` | no, allowed on any node | `aware` \| `practitioner` \| `advanced` \| `expert` | The owner's claim, tested in §3. Shown as L1 Aware … L4 Expert; leave it unset for "not rated"; `L3` or `L3 Advanced` is read as `advanced` |
| `assessments` | no, allowed on any node | list of quoted strings, `"<assessor> | <level> | <YYYY-MM-DD>"` | **Each assessor's rating** of the same competency (a supervisor, counsellor, manager or peer), one string an assessor, kept beside the owner's claim and never in its place (§3.9): who gave it (a name; where the config lists assessors, §9.1, the name as listed there), the level (the word, or `L3`), and the day. A name cannot contain `|`. Several assessors' ratings stand side by side; a new rating replaces only that assessor's last |
| `assessedLevel`, `assessedBy`, `assessedOn` | no | as `claimedLevel`; free text; `YYYY-MM-DD` | One assessor's rating as it was kept before a note could hold several. Still read, as one more assessor's rating; `edit_links.py` moves it into `assessments` when it next writes a rating to the note. New ratings are not written this way |
| `esco` | no | ESCO concept URI | Lets different people's graphs be compared |
| `externalRef` | no | list of quoted strings, `"<framework> <edition>: <name or code>"` | Other standards: professional body competencies (`"RICS APC 2025: Leasing/letting"`), SFIA codes (`"SFIA 9: DATM"`). Several allowed. A framework's view of the graph comes from these, never from the tree's shape (§3.8) |
| `status` | no | `active` \| `dormant` \| `retired` | |
| `deemed` | no | text, e.g. `"Deemed to have it (Owner, 2026-11-10)"` | The owner attests the claimed level without evidence (e.g. a professional body's mandatory competency they hold but have not documented). The checker does not report the claim as unsupported but lists it under *Deemed competencies*; outputs label it **deemed**, never as evidence |
| `aliases` | no | list of strings | **Search and autocomplete only. Aliases do not resolve links**, and the check script ignores them |

**Branches.** Each domain may have up to three branch roots, `<Domain> Methods`, `<Domain> Tools` and `<Domain> Standards & Law`, with `rank: branch` and `kind` set to method, tool or knowledge. The specialization test applies *within* a branch: VTS is a kind of real property tool. A branch root's own link to its domain means "belongs to". It is the one documented exception to principle 4. Practices link to methods, tools and standards through `related`.

The note body holds an optional definition: what the term means to this person and where its scope ends.

### 2.2 `sector`: one note per industry used

| Field | Required | Values | Notes |
|---|---|---|---|
| `nodeType` | yes | `sector` | |
| `code` | yes | quoted string, e.g. `"22"` | From the classification named in the profile. The code identifies the note |
| `broader` | no | quoted wikilink to the parent sector note | Only when notes exist at more than one level |
| `claimedLevel` | no | as for competency | **Knowledge of the sector itself** (regulation, market structure, major players) |
| `assessments` | no | as for competency | Each assessor's rating of the same knowledge (the three older fields are read here too) |
| `related` | no | quoted wikilinks | |

The classification and its version are stated **once, in the profile**, not on each note. When the classification is revised, codes are remapped in one pass.

### 2.3 `evidence`: anything that proves a competency

| Field | Required | Values | Notes |
|---|---|---|---|
| `nodeType` | yes | `evidence` | |
| `evidenceType` | yes | `role` \| `engagement` \| `activity` \| `project` \| `credential` \| `publication` \| `course` | **credential** = an academic or professional qualification awarded to the owner: degree, diploma, designation, licence or certificate (dated by the award; a certificate earned by completing a course is a credential). A job title is never a credential: it belongs on the role. **role** = employment. **engagement** = contracted work for a client, including placements through an agency or consultancy. **activity** = ongoing professional or volunteer service (assessor, board seat, mentor programme). **project** = a build, initiative or deliverable |
| `period` | yes | `START – END` (en dash with spaces) or a single date. Each date is `YYYY-MM-DD`, or `YYYY-MM` / `YYYY` when the day or month isn't recorded (ISO 8601 reduced precision; never invent a day or month). `END` may be `present` | A credential that is still held uses `start – present`. The profile may name an existing field to use instead (e.g. `tenure`) |
| `demonstrates` | yes, except roles whose competencies sit on their sub-projects | quoted wikilinks to `competency` notes | Link the most specific competency. Parents are implied |
| `demonstratesLed` | no | quoted wikilinks to `competency` notes | Competencies the owner **led** here: made the call, gave the reasoned advice, or owned the result (RICS APC level 3, SFIA level 5 and up), not just took part. Only led work counts toward `advanced` and `expert` (§3.5). A competency may also stay in `demonstrates`; it is counted once |
| `recognition` | no | a list drawn from `credential` \| `assessing` \| `teaching` \| `publication` \| `adoption` \| `appointment` \| `award` | Outside recognition this evidence shows (§5). Counts toward `expert` for every competency the note demonstrates |
| `sector` | yes for roles and engagements | quoted wikilinks to `sector` notes | The business **where the work was done**: for an engagement, the client's sector |
| `partOf` | no | one quoted wikilink to another evidence note | A project inside a role, or a repo built during an engagement. Prevents double counting (§3) |
| `organization` | yes for roles, engagements and activities | text, or a quoted wikilink to an `organization` note | The employer, or for engagements the client. Text that an organisation note answers to (its filename, title or an alias) counts as that organisation, so no evidence note has to change when one is added (§2.4) |
| `via` | no | string | The agency or consultancy for a placement |
| `anchor` | no | URL, member ID, DOI, file path or CRM dossier path | Something a third party could check. A CRM dossier for a referee or counterparty counts |
| `referee` | no | quoted wikilinks to `person` notes | The people who can speak to this work. A referee counts as an anchor (§3.10) |
| `disclosure` | yes | `public` \| `on-request` \| `confidential` | Who may see it in outputs. Default `confidential` |

### 2.4 `organization`: one note per organisation the owner wants counted as one

| Field | Required | Values | Notes |
|---|---|---|---|
| `nodeType` | yes | `organization` | |
| `title` | no | string | The name a reader should see. The filename serves when there is none |
| `aliases` | no | list of strings | **Every other way the evidence writes it.** Unlike a competency's aliases, these are read: an evidence note whose `organization` is the filename, the title or an alias counts as this organisation |
| `sector` | no | quoted wikilinks to `sector` notes | The organisation's own industry |
| `crm` | no | path or id | Where the owner's own record of the organisation is. The note points at it; it copies nothing from it |

An organisation note is optional and is worth adding only where it changes something: an employer written two ways, or one the owner wants to hang people on. Two notes may not answer to the same name.

### 2.5 `person`: one note per person who can speak to the owner's work

| Field | Required | Values | Notes |
|---|---|---|---|
| `nodeType` | yes | `person` | |
| `title` | no | string | The person's name |
| `role` | no | string | What they were to the owner: manager, client, counsellor |
| `organization` | no | text, or a quoted wikilink to an `organization` note | Where they were when they saw the work |
| `aliases` | no | list of strings | Other forms of the name |
| `crm` | no | path or id | The owner's contact record for them. People are joined to an existing contact system this way, never duplicated in the graph |

A person enters the graph as an evidence note's `referee`. An assessor (§3.9) may have a person note too; a rating still records the assessor's name.

**Citing sources in note bodies.** Cite the source file and its **section heading**; add a line number only with an "as of" date. Line numbers drift whenever a file above the cited passage changes, and tagging a file in place adds front-matter lines (in the pilot build, citations went 6 lines off after the files were tagged). Line numbers are fine in short-lived working proposals.

**Undated sub-projects.** When a project inside a role has no recorded date, use the parent's period as an honest bound and say so in a comment (`# date not recorded; bounded by role`). Never guess a narrower window.

**Size rule.** If a role's `demonstrates` list would pass ~15 links, split the specific work into `project` notes with `partOf` pointing at the role. The role keeps only the competencies used across the whole role.

---

## 3. Counting rules (computed)

1. **Rollup.** Evidence that supports a competency also supports every ancestor of that competency, through all `broader` links.
2. **Independent units.** Evidence linked by `partOf` collapses to the root of its chain. Each root is **one unit**. A role and three projects inside it are one unit; a credential is its own unit. **Organisations** are counted from the units' `organization`: by organisation note where one answers to the name (§2.4), otherwise by the text itself, so an employer written two ways is two organisations until a note says they are one.
3. **Support by level** (summary; the full rule is item 7):

   | `claimedLevel` | Needed |
   |---|---|
   | `aware` | Nothing. A course or credential alone supports `aware` |
   | `practitioner` | ≥1 unit of delivered work (anything but a course or credential), with ≥6 months of delivered work in all |
   | `advanced` | ≥2 units of **led** work, from ≥2 organisations or with an external `anchor`, over ≥5 years of led work |
   | `expert` | `advanced`, plus ≥10 years of led work and ≥1 kind of outside `recognition` |

4. **Recency** = the latest end date (`present` = today) among supporting units that count toward recency:
   - for `practice` competencies: roles, engagements and activities. A side project doesn't reset the clock on a practice that has work evidence. **A practice evidenced only by projects or courses falls back to those, labelled `project-only`** (e.g. a competency built entirely through personal repos);
   - for `method`, `tool` and `knowledge` competencies: roles, engagements, activities, projects and courses.

   Credentials support a claim but never count toward recency. A unit's date is its root's `period` end. A reduced-precision end date counts as the last day of its month or year, and a reduced-precision start as the first. The profile may change these rules.
5. **Years** ("years of work") = total length of the dated evidence behind a competency, led or not (unit periods, overlaps merged; same basis as recency). It is context: no level is tested on it. **Months of delivered work**, the `practitioner` test, are counted the same way over every kind of delivered unit. **Led years**, the `advanced` and `expert` test, count only the led work and use the periods of the led evidence notes themselves: a project led inside a long role counts the project's dates, not the role's (an undated project carries its role's period as an upper bound). Tag led work on the specific project where one exists, rather than on the whole role. Role-level periods count in full for every competency a role demonstrates, so years are an upper bound.
6. **Stale** = recency older than the profile's threshold while `status: active`. This is reported only. Whether to mark the competency `dormant` is the owner's call. **Staleness never lowers a level**: someone who was an expert and stopped practising is an expert whose evidence is stale.
7. **Levels.** The four levels follow the shape shared by the Dreyfus model, the US OPM and NIH proficiency scales, SFIA's levels of responsibility and the RICS APC levels: knowing about a competency, applying it, applying it to complex cases with accountability, and being relied on as an authority by people outside one's own team.

   | Level (label) | Meaning | Comparable to |
   |---|---|---|
   | `aware` (L1) | Understands it and can discuss it; has not delivered it | Dreyfus novice/advanced beginner; OPM 1–2; RICS level 1 |
   | `practitioner` (L2) | Delivers it independently in normal situations | Dreyfus competent; OPM 3; RICS level 2 |
   | `advanced` (L3) | Handles complex cases without guidance, is accountable for the result, guides others | Dreyfus proficient; OPM 4; SFIA 5; RICS level 3 |
   | `expert` (L4) | A recognised authority beyond their own team: others rely on their judgement | Dreyfus expert; OPM/NIH 5 ("recognized authority"); SFIA 6–7; the FRICS "expert" characteristic |

   **Labels.** Every output shows the levels as **L1 Aware, L2 Practitioner, L3 Advanced, L4 Expert**; a competency with no `claimedLevel` shows as **not rated**. Notes store the word (readable in YAML, stable across graphs); `claimedLevel: L3` or `L3 Advanced` is read as `advanced`, and the link editor stores the word. L1–L3 line up one to one with the RICS APC levels (knowledge, application, reasoned advice), so a profession's level-3 competency is evidenced the same way as an L3 competency: led work. L4 sits beyond the APC (the FRICS "expert" characteristic).

   The computed rule:
   - **Delivered work** is any unit except a course or credential: the owner did the work, or part of it, to a result. It need not have been led.
   - **practitioner**: ≥1 unit of delivered work, and the delivered units' periods add up to ≥ `kgPractitionerMinMonths` (default 6) months, overlaps merged. The months are the units' own: a project inside a role counts the role's period (as Years does, item 5), and a project standing alone counts its own. Delivered work that is shorter, or undated, supports `aware`: two months in a job, or one short piece of work, shows exposure and not yet independent delivery. Set the key to `0` to switch the time test off.
   - **Led work** is a unit whose evidence lists the competency in `demonstratesLed`. Led means the owner took the lead on that competency in that work: made the call, gave the reasoned advice or owned the result. It is about the work, not about managing people, and work done well under someone else's direction is delivered, not led. Led work is also delivered work. Units that are roles, engagements or activities count. A project, publication or course counts as led work only if it carries `recognition` (e.g. others adopted it); the owner's own projects otherwise show practice, not standing.
   - **advanced**: ≥2 units of led work; ≥2 organisations among them or an `anchor`; ≥ `kgAdvancedMinYears` (default 5) led years.
   - **expert**: advanced, plus ≥ `kgExpertMinYears` (default 10) led years, plus ≥ `kgExpertMinRecognition` (default 1) kinds of `recognition` on any evidence of the competency or a narrower one.
   - **No roll-up inflation.** Led work rolls up to ancestors, but a parent reaches `advanced` or `expert` either from led work tagged on the parent itself, or through narrower competencies only when at least one of its children reaches that level on its own. Many children each led once don't make a parent an expert.
   - **Sectors** have no led work: a sector note's whole support is counted against the same thresholds.

   Why years and recognition, not just counts: years of experience alone predict performance poorly (Ericsson's expert-performance research; Benner: experience is not the mere passage of time), so the ten-year guideline applies only to led work, and expertise is defined by what others rely on (NIH "recognized authority"; the FRICS and USCIS O-1 tests of outside recognition).
8. **External frameworks.** A professional body's competency list (RICS APC, CPA competency map, SFIA, a nursing standard) is mapped with `externalRef`, not by reshaping the tree. Retitle a competency in the framework's wording only when the owner wants it, and keep the old name in `aliases`. Cross-cutting competencies that every professional is expected to hold (ethics, client care, communication and negotiation, health and safety, conflict avoidance, inclusion and teamworking, sustainability) may form their own domain, *Professional Practice*; a framework competency that is already a discipline elsewhere (accounting, data management, leadership) stays there with an `externalRef`. See `domains-and-classifications.md` §6.

   **Every framework uses this graph's L1–L4 scale.** A framework's own levels (RICS levels 1–3, CFA exam levels, Bloom's taxonomy, Six Sigma belts, SFIA levels) are never used as they stand: map them onto L1 Aware, L2 Practitioner, L3 Advanced, L4 Expert by what each means here (knows it, delivers it, leads it and is accountable, recognised authority), propose the mapping with a one-line reason to the owner like any placement (ground rule 1), and record it in the profile's decision log. Examples: RICS levels 1–3 = L1–L3; the CFA charter = L1 for every topic it examines; Six Sigma Yellow, Green, Black and Master Black Belt = L1, L2, L3, L4. The requirements file's `required` column then takes only `L1`–`L4`, `L2 or L3` or `choice`, and the checker reports any other value as an error (`requirements`).

9. **Three readings of a level, kept apart.** A competency can carry up to three levels, and none of them overwrites another:

   | Reading | Where it comes from | What it answers |
   |---|---|---|
   | Claimed | `claimedLevel`, set by the owner | What do I say I can do? |
   | Assessed | `assessments`, one rating an assessor, each with their name and the day | What does someone who has seen my work say? |
   | Supported | Computed from the evidence (item 7) | What can a stranger verify from the record? |

   The assessor rates against the wording of each level (the framework's descriptions, or the table in item 7), not against the evidence counts: a level-3 rating says the assessor has seen reasoned advice given, whether or not five years of led work are on file. So an assessed level can sit above the supported one, and that difference is information (the work is real but not yet documented), not an error. The checker reports nothing when the three differ, except the usual unsupported-claim warning for the claim. A rating is the assessor's word as the owner recorded it; the name and the day are there so a reader can ask.

   **Several assessors.** A competency keeps one rating for each assessor who has rated it. A new rating by the same assessor replaces their last, and the vault's history (git, or the dated worksheets in `working`) keeps the earlier ones; another assessor's rating is added beside it. The **assessed level** is then the highest level every assessor supports, which is the lowest of their ratings: a supervisor's L3 and a counsellor's L2 make an assessed level of L2, as two signatures on one level would. That is the level outputs show and a job spec is scored on. When the ratings are not all the same the assessors **differ**, by the number of levels between the highest and the lowest; the checker reports it (`assessors-differ`), the summary rows carry it (`assessedSpread`, with every rating in `assessments`), and the dashboard marks it beside the assessed level and lists each assessor's rating. A difference is information, not an error: it shows where the people who have seen the work do not yet agree, and which rating to talk about. An assessor rates without being shown the others' ratings. The config may list the people who rate (`assessors:`, §9.1), each under an id that never changes, so that a tool can offer them by name and a later change of name can be carried into the notes; the list says who can be picked, and a note still records only the name.

10. **Rules that read the relations.** Layer 3 adds no stored conclusion: each rule below is worked out on every run, and reports or counts. None of them writes to a note (principle 10).

    | Rule | Reads | What follows |
    |---|---|---|
    | **Prerequisite** | `requires` and the two competencies' `claimedLevel` | A claim that stands above the claim made for a competency it requires is reported (`prerequisite`), and so is a claim that requires a competency not rated at all. Neither claim is changed, and the supported level is not touched: the evidence rule (item 7) stands alone |
    | **One organisation** | `organization` on evidence, and the organisation notes' names | Spellings that one organisation note answers to are one organisation in every count: the two-organisation test for `advanced` and the organisations shown beside a competency |
    | **Referee as anchor** | `referee` | A unit with a referee is anchored, as if it carried an `anchor` |
    | **Served by** | `appliedTo`, read backwards | The methods, tools and knowledge that serve a practice. A view (`query_graph.py relations`); nothing is counted from it |
    | **Certified by** | `demonstrates` on evidence of type `credential`, read backwards | The credentials behind a competency. A view; never stored, since the link already exists on the credential (principle 1) |

---

## 4. Checks (the check script)

All checks are read-only. Links are resolved vault-wide **by filename**; a filename that matches more than one file is an error.

| Severity | Check |
|---|---|
| Error | Broken link: a `broader`, `related`, `sector`, `demonstrates` or `partOf` target is missing |
| Error | Ambiguous link: target filename matches more than one file |
| Error | Cycle in `broader`, `partOf` or `requires` |
| Error | Orphan: a non-domain competency with no `broader` |
| Error | Unknown value in a controlled field (§5), or a nested object in a graph field |
| Error | Two sector notes with the same `code` |
| Warning | Unsupported claim: `claimedLevel` exceeds the support (§3.3, §3.7); the message says what is missing for the next level |
| Warning | Stale claim (§3.5) |
| Warning | Prerequisite: a `claimedLevel` above the claim made for a competency this one `requires`, or requiring one that is not rated (§3.10) |
| Warning | Relation: `appliedTo` from a practice, or to something that is not a practice; `requires` naming a competency above or below this one in the tree |
| Warning | Organisation: two organisation notes answering to the same name |
| Warning | Assessment: an `assessments` entry that is not `"<assessor> | <level> | <YYYY-MM-DD>"`, has a level off the scale or a date that is not a day, or repeats an assessor (the later rating counts); an `assessedLevel` with no `assessedBy` or `assessedOn`, or either of those without a level (§3.9) |
| Warning | Assessors differ: two or more assessors rate a note at different levels; the message gives each rating and the assessed level (the lowest) (§3.9) |
| Warning | `related` stored on both notes (it is symmetric; keep it on one side, principle 1) |
| Warning | Role or engagement with no `sector` |
| Warning | Evidence with no `anchor` and no `referee`, for unit roots only (a project with `partOf` is vouched for through its parent) |
| Warning | `demonstrates` longer than ~15 with no child projects |
| Warning | Config only: a competency or sector note outside its configured folder (`folder`); a configured source that doesn't exist (`source`) |
| Insight | **Cross-domain:** competencies that *declare* parents whose main lines reach different domains (their descendants are not re-reported), and evidence units whose linked competencies' main domains differ. A competency's **main domain** is the one its first-`broader` chain reaches. Second parents still feed evidence roll-up (§3.1) |
| Insight | **Domain pairs:** for each pair of domains, the independent units whose linked competencies' main domains include both, ranked by count (the positioning view, e.g. Real Property × Data & AI) |
| Insight | **Cross-sector:** the same discipline evidenced in ≥2 top-level sectors (shows transferable competency) |
| Insight | Claims compared with support: a table per main domain |

Output: a markdown report (errors, warnings, insights) plus an optional JSON export of the graph.

**Scripts** (Python 3.9+ with PyYAML; all take `--vault <root>` and `--profile <profile.md>`):

| Script | Does |
|---|---|
| `check_graph.py` | The checks above. Read-only. Exit 1 on errors |
| `query_graph.py` | `support` (what backs a competency, with a `--disclosure` filter), `find` (free text → competency notes), `tree`, `framework` (every competency mapped to an external framework, e.g. for an index note), `evidence`, `relations` (what a competency requires, is applied to and is certified by, both ways) and `organizations` (each organisation with its units and spellings). Read-only |
| `edit_links.py` | `add` / `remove` links or `externalRef` / `aliases` strings, `set` a controlled field or `title` / `rank`, `assess` (one assessor's rating, written to `assessments` in place of their last), or apply a `plan` YAML. Dry run unless `--apply` |
| `rating_worksheet.py` | Writes a YAML worksheet of every competency with its support, for the owner to set `claimedLevel`, or with `--assessor "<name>"` for that assessor to give their own ratings (the other assessors' are shown beside, and kept); the worksheet is also an `edit_links.py` plan |
| `evidence_worksheet.py` | Writes a YAML worksheet of every evidence note, for the owner to mark `demonstratesLed` and `recognition`; also an `edit_links.py` plan |
| `summary_graph.py` | Writes summary tables (domains, competencies, an evidence timeline, a domain × sector grid) at a chosen disclosure level, for a report or dashboard |
| `frameworks.py` | Lists the framework library (`assets/frameworks/` and the owner's own frameworks) with the owner's selection, builds the requirements and descriptions files from it (`build`), and writes a selection saved on the dashboard into the config (`apply`) |
| `assessors.py` | Lists the config's assessors, and writes the list saved on the dashboard into the config (`apply`), with an `edit_links.py` plan for the notes that record a rating under a name that changed |
| `job_specs.py` | Checks, lists and scores the owner's job specs (breadth, depth, mandatory gate, band, promotion), writes the dashboard's copy (`build`) and writes specs saved on the dashboard into the file (`merge`) |
| `dashboard_build.py` | Writes the whole dashboard from the skill and the owner's files: the page with the owner's settings, every data file, and a manifest of what to upload |
| `claims_plan.py` | Turns claimed-level changes saved on the dashboard into an `edit_links.py` plan, and lists requests for competencies not yet in the graph (`dashboard.md` §4) |
| `kg_config.py` | Reads `competency-graph.yaml` (§9.1): shows where files go and the owner's sources, gives the path for a new file, writes a new config with every location and source |

**Link editing.** Links and controlled fields in existing notes are changed only through the link editor (`edit_links.py`), never with ad-hoc text replacement. It dry-runs by default, checks each target's existence and type, keeps existing links in order, refuses a whole batch if any edit fails, and re-parses the front matter to prove nothing else changed. (Added after a one-off regex replaced ten link lists instead of extending them.)

---

## 5. Controlled values

| Field | Value | Meaning |
|---|---|---|
| `claimedLevel` | `aware` (L1) | Understands it and can discuss it; has not delivered it |
| | `practitioner` (L2) | Delivers it independently in normal situations |
| | `advanced` (L3) | Handles complex cases without guidance, is accountable for the result, guides others |
| | `expert` (L4) | A recognised authority beyond their own team: others rely on their judgement (§3.7) |
| `recognition` | `credential` | A senior or chartered credential in the discipline (e.g. FRICS, CFA charter); not an entry-level certificate |
| | `assessing` | Assessed or judged others' work: exam assessor, peer reviewer, award juror |
| | `teaching` | Taught or trained others formally: a course, workshop or structured mentoring programme |
| | `publication` | Published or presented outside the employer: paper, book, talk, keynote |
| | `adoption` | Others adopted an original contribution: a method, tool, model or standard in use beyond the owner |
| | `appointment` | Appointed as an authority: expert witness, advisory panel, a critical role at a distinguished organisation |
| | `award` | An award or prize from a third party |
| `kind` | `practice` / `method` / `tool` / `knowledge` | Professional activity / technique / named software or platform / law, regulation or standard |
| `status` | `active` / `dormant` / `retired` | Still offered / recoverable / no longer claimed |
| `disclosure` | `public` / `on-request` / `confidential` | Can appear anywhere / can be named and shown when asked / never leaves the vault. An application or brief sent to a named reader counts as "asked", so it may use `on-request`; anything posted openly uses `public` only |
| `evidenceType` | see §2.3 | |

New values are added here (or as an extension in the profile) before they are used.

---

## 6. Layout and naming

```
<vault root>/
├── competency-graph.yaml     # where every kind of file goes (§9.1)
└── <graph root>/
    ├── Profile_<Owner>.md   # records which specification version the graph follows
    ├── Working/             # dated placement proposals, test notes, rating worksheets, checker reports
    ├── Outputs/             # material made for a reader (requirement tables, evidence packs)
    ├── Competencies/              # every competency note including branch roots; optional subfolders for browsing (§1.8)
    ├── Sectors/             # Sector_<code>_<Short_Label>.md
    ├── Organizations/       # Org_<name>.md, only where one is needed (§2.4)
    ├── People/              # Person_<name>.md, the referees (§2.5)
    └── Evidence/
        ├── Projects/        # Repo_<name>.md, Project_<name>.md
        ├── Credentials/     # Credential_<abbrev>.md
        ├── Publications/
        └── Engagements/     # only when no existing record file exists
```

- These are the default folders. `competency-graph.yaml` at the vault root can move any of them (§9.1). Graph-note folders must stay inside the vault, because links resolve only there; working, reports and outputs folders may be anywhere.
- Existing record files stay where they are and are referenced in place.
- **Filenames must be unique across the vault.** Before creating a competency note, check for a file of the same name. If one exists, use a more specific name (`Business_Strategy.md`, not `Strategy.md`).
- The prefixes (`Sector_`, `Repo_`, `Credential_`, `Org_`, `Person_`) keep evidence, sector, organisation and person names separate from competency names.
- The `title` field carries the human-readable label.

---

## 7. Views inside the vault

Obsidian's backlinks and graph view work with no setup. Obsidian **Bases** (a core plugin) can show computed tables inside a note, such as a competency's children or the evidence pointing at it, by filtering on these properties. Bases only display; the check script remains the authority for rollup, recency and support.

---

## 8. Build method

1. **Profile.** Interview the owner: sources, existing metadata conventions and reserved field names, where the graph goes, industry classification, threshold, domains (step 3).
2. **Collect candidate competencies** from the sources, each with a citation. Prefer the concrete competency inside achievement bullets over keyword lists. Then **scan the full source documents for named methods, models and frameworks that never became a bullet**: bullet-only collection misses them (the pilot's first pass test failed on exactly such a model). Merge duplicates.
3. **Set the domains.** Claude proposes them (usually 3–8, by the breadth of the career) based on the candidates, checks them against reference standards (ESCO/ISCED-F; the owner's professional bodies) and records the reasons. The owner decides.
4. **Place the competencies.** Claude proposes a parent, `kind` and branch for each candidate, in batches. The owner approves or edits. Claude never makes a placement the owner hasn't approved.
5. **Build a thin slice first:** one domain, 2–3 roles, 1–2 credentials, 2–3 projects, the sector notes they need, and the check script. Prove it answers one real question before going further.
6. **Expand one domain at a time,** running checks after each.
7. **Review:** go through claims against support, act on stale warnings, and note the cross-domain and cross-sector insights.

---

## 9. The profile

Everything that varies by person lives in `Profile_<Owner>.md`. The scripts read these flat keys from its front matter (all optional):

| Key | Default | Meaning |
|---|---|---|
| `kgSpecVersion` | | The specification version the graph follows |
| `kgStaleYears` | `5` | Stale threshold (§3.6) |
| `kgPractitionerMinMonths` | `6` | Minimum months of delivered work for `practitioner` (§3.7) |
| `kgAdvancedMinYears` | `5` | Minimum years of led work for `advanced` (§3.7) |
| `kgExpertMinYears` | `10` | Minimum years of led work for `expert` (§3.7) |
| `kgExpertMinRecognition` | `1` | Kinds of outside `recognition` needed for `expert` (§3.7) |
| `kgPeriodAliases` | `[]` | Existing fields read as `period` on evidence notes (e.g. `[tenure]`) |
| `kgExclude` | `[]` | Extra directories the scripts skip |

### 9.1 The config file

`competency-graph.yaml`, at the vault root, says where files go. The scripts find it by looking in the current folder, then its parents, then `Competency_Graph` in the owner's Documents folder (a vault set up before the skill was renamed may have `knowledge-graph.yaml`; it is found the same way, and a `competency-graph.yaml` in the same folder wins); `--config`, `--vault` and `--profile` override it. Paths are relative to the vault root, or absolute.

| Key | Default | Meaning |
|---|---|---|
| `kgConfigVersion` | `1` | Config format version |
| `graphRoot` | required | The graph root folder. Offered first for a new graph (`kg_config.py where`): `Competency_Graph` at the root of the git repository the owner is working in; outside a repository, `.` in a vault that is `Competency_Graph` in their Documents folder |
| `profile` | none | The profile note |
| `folders.competencies`, `.sectors`, `.evidence` | `<graphRoot>/Competencies`, `/Sectors`, `/Evidence` | New graph notes; must be inside the vault |
| `folders.working` | `<graphRoot>/Working` | Placement proposals, pass tests, rating worksheets |
| `folders.reports` | `<graphRoot>/Working` | Checker reports and JSON exports |
| `folders.outputs` | `<graphRoot>/Outputs` | Material made for a reader |
| `datedFilenames` | `true` | Prefix files the assistant names with `YYYY-MM-DD_` |
| `requirements` | none | Optional framework requirements CSV (`dashboard.md` §5). The checker validates it: every `required` is on the L1–L4 scale |
| `descriptions` | beside `requirements` (`…Requirements…` becomes `…Descriptions…`) | Optional framework descriptions CSV for the dashboard's Framework competency definitions tab; `frameworks.py build` writes it |
| `sources` | none | The owner's own records: a list of `{path, kind, use, note}`. `use` is `evidence` (files become evidence notes in place; must be inside the vault), `collect` (read for candidate competencies only; may be outside the vault) or `ignore`. The checker warns (`source`) when one is missing |
| `frameworks` | none | Selected library frameworks: `<id>: {pathways: [...], notes: {pathway: note}}`; omit `pathways` for all, `[]` for none (the notes are kept). `frameworks.py build` writes `requirements` from it |
| `ownFrameworks` | `<graphRoot>/Frameworks`, read once it holds a `catalog.yaml` | A folder of the owner's own frameworks in the library's format (`catalog.yaml` and its files), inside the vault and never inside the plugin's own folder. `frameworks.py new` starts one. They join the library; an entry under a shipped framework's id with `replaces_plugin: true` is the owner's own edition and takes its place; one may have descriptions only, for job specs |
| `jobSpecs` | `<competencies>/Job_Specs.yaml` | The owner's job specs (`dashboard.md` §5). The checker validates it when it exists |
| `dashboard` | none | `{title, sectors, disclosure}` for `dashboard_build.py`: the page's title, the industry classification's name, and `on-request` or `public` |
| `assessors` | none | The people who rate the owner's competencies (§3.9): `<id>: {name, role}`. The id is lowercase letters and digits joined by hyphens and never changes; the name is what a rating records in `assessedBy` and must differ from the others'; the role is optional. `assessors.py apply` writes it from the dashboard |

Unknown keys are an error, so a misspelt folder isn't silently ignored. Where files go is kept out of the profile, which holds how the graph is judged; moving a folder then never touches a decision record.

### 9.2 The profile body

The body records:

- owner, graph location (matching the config file), check script location;
- metadata conventions to follow and **reserved field names** the graph must not reuse;
- source files and how each is treated (becomes a note, used for collection, ignored);
- field mappings (e.g. `tenure` → `period`);
- industry classification and version;
- domains, their branches and the reasons;
- stale threshold and any recency-rule overrides;
- default `disclosure` rules;
- current milestone, decision log, known source-data issues, related systems.

---

## 10. Changes

**v0.5** (2026-11-14; nothing renamed, existing graphs stay valid). Layer 3 is in scope as far as four things go. Two named relations between competencies: `requires`, a prerequisite, and `appliedTo`, from a method, tool or piece of knowledge to the practice it serves (§2.1). Two note types, `organization` and `person` (§2.4, §2.5), each a thin note that points at the owner's own record, with `referee` on evidence. And the rules that read them (§3.10): a claim above a prerequisite's is reported; spellings one organisation note answers to count as one organisation; a referee is an anchor; what serves a practice and what certifies a competency are views. A graph with none of these fields behaves exactly as before. One count can change in a graph that adds an organisation note: two units that were two organisations by spelling become one, and a level that rested on "two organisations" then needs an anchor or a referee.

**v0.4, 2026-11-14 addition** (existing graphs stay valid). A note keeps each assessor's rating, in `assessments` (§2.1, §3.9), where it kept one in `assessedLevel`, `assessedBy` and `assessedOn`; those are still read and are moved into the list by the next rating written. The assessed level is the lowest of the assessors' ratings, and a difference between them is reported.

**v0.4, 2026-11-14 addition** (no field renamed; existing graphs stay valid). The config may list the assessors (`assessors:`, §9.1), and `assessors.py` applies the list kept on the dashboard. A note records a rating as before.

**v0.4, 2026-11-14 addition** (no field renamed; existing graphs stay valid, but some supported levels fall). `practitioner` needs six months of delivered work as well as a unit of it (§3.7; profile key `kgPractitionerMinMonths`, `0` restores the old rule). Before this, a single day's work or the first weeks of a new job supported L2. In the pilot graph 40 of 256 notes supported at L2 or above fell to L1, most of them evidenced only by a role begun ten weeks earlier.

**v0.4, 2026-11-13 addition** (no field renamed; existing graphs stay valid). An assessor's rating: `assessedLevel` with `assessedBy` and `assessedOn` on competency and sector notes (§2, §3.9), a third reading beside the claimed and supported levels. `rating_worksheet.py --assessor` writes the assessor's worksheet, `job_specs.py score --basis assessed` scores a job spec on the ratings, and the dashboard shows an Assessed column where one exists or is being entered.

**v0.4** (2026-11-09). Every external framework is stated on the L1–L4 scale; the optional `requirements` file named in the config is checked for it. One term: the taxonomy's notes are **competencies** (`nodeType: competency`, folder `Competencies/`, config key `competencies`), because owners mapping to a professional body's competency framework found "skills" and "competencies" side by side confusing. The finest rank is `element` (was `skill`), the word competency frameworks use for the parts of a competency. Nothing else is renamed. **Older graphs keep working:** the scripts read `nodeType: skill` as `competency`, `rank: skill` as `element`, and the config key `skills` as `competencies`. To migrate, move the folder (filenames unchanged, so links hold), then change those two front-matter values in each note and the config key.

**v0.3, 2026-11-09 addition** (no field renamed; existing graphs stay valid). Levels are labelled L1 Aware to L4 Expert in every output, and `claimedLevel` accepts the L-codes on input. `externalRef` has a fixed format, and external frameworks are mapped through it (§3.8); `domains-and-classifications.md` §6 adds an optional Professional Practice domain and the RICS APC mapping as a worked example. The link editor also edits `externalRef`, `aliases`, `title` and `rank`.

**v0.3.** Four levels: `advanced` added between `practitioner` and `expert`, with definitions mapped to Dreyfus, OPM/NIH, SFIA and RICS. New evidence fields `demonstratesLed` (moved forward from layer 3) and `recognition`. `advanced` and `expert` are computed from led work only, `expert` needs ten years of led work and outside recognition, a parent can't become expert by roll-up alone, and a course or credential alone supports only `aware`. `kgExpertMinYears` now defaults to 10; the `expert-years` warning is folded into `unsupported`. In the pilot graph, the v0.2 rule found 53 of 175 competencies expert-supported, including tools such as Excel.

**v0.2** (from v0.1).

Disciplines and sectors are now separate axes. Added sector notes, `partOf`, `via`, `disclosure` (in place of reusing `shareable`), `kind: knowledge`, branches, and claims on any node. Added counting by independent units and the rule requiring more than one organisation or an external anchor for `expert`. Recency now depends on the kind of competency. Added a thin-slice milestone and the check script. Aliases are no longer described as resolving links. Owner-specific values moved to the profile.

---

## 11. What is left of layer 3

Built in v0.5: `requires`, `appliedTo`, organisation and person notes, `referee`, and the rules of §3.10. Left out, and why:

- **`certifiedBy` as a stored field.** It would repeat the `demonstrates` link a credential already carries (principle 1), so it is a view (§3.10).
- **More depth per link** as further lists (e.g. `demonstratesApplied`). `demonstratesLed` arrived in v0.3 and is the one distinction a level is computed from; another would need a rule that uses it.
- **A level worked out from a prerequisite.** The prerequisite rule reports; it does not cap a supported level, because that would let an unrated tool pull down a level the evidence supports.
- **A general rule language.** The rules are a short fixed list in the checker. A new rule is added there, with its line in §3.10, when a real question needs it.

None of these, and nothing in v0.5, renames a layer-1 or layer-2 field.
