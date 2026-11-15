# Templates

Copy and fill these in. Field rules are in `specification.md` §2; this file shows the shapes. Every example uses a fictional person. If the owner's vault has required front-matter fields of its own (e.g. `title`, `date`, `lastUpdated`), add them to every note, and get today's date from the shell (`date +%F`), never from memory.

## Contents
0. Config file
1. Profile
2. Placement proposal (working note)
3. Competency notes: domain, branch root, practice, method/tool, knowledge
4. Sector note
5. Evidence notes: role tagged in place, project inside a role, repo, credential, course, activity
6. Plan file for `edit_links.py`
7. Experience record: one role or engagement, written as the work is done
8. Layer 3: a prerequisite, an organisation note, a person note

---

## 0. Config file: `<vault root>/competency-graph.yaml`

Write it with `kg_config.py --vault <root> init --graph-root <dir> --profile <dir>/Profile_<Owner>.md`, which produces this shape. Every path is relative to the vault root. Delete a folder line to use its default (`<graphRoot>/<Name>`). Here the owner keeps finished material with their job applications, outside the graph:

```yaml
kgConfigVersion: 1
graphRoot: Competency_Graph
profile: Competency_Graph/Profile_Priya_Nair.md
folders:
  competencies: Competency_Graph/Competencies
  sectors: Competency_Graph/Sectors
  evidence: Competency_Graph/Evidence
  working: Competency_Graph/Working
  reports: Competency_Graph/Working
  outputs: Career/Applications       # requirement tables, evidence packs, CV material
datedFilenames: true                 # prefix files Claude names itself with YYYY-MM-DD_
# requirements: Competency_Graph/Competencies/Framework_Requirements.csv   # optional; checked: levels must be L1-L4
# descriptions: Competency_Graph/Competencies/Framework_Descriptions.csv   # optional; default: beside requirements
# jobSpecs: Competency_Graph/Competencies/Job_Specs.yaml   # optional; this is the default (dashboard.md §5)
# ownFrameworks: Competency_Graph/Frameworks   # optional; this is the default. The owner's own frameworks (frameworks.py new)
# dashboard:                         # optional; what dashboard_build.py writes into the page
#   title: Priya's competency portfolio
#   sectors: NAICS Canada            # the industry classification's name
#   disclosure: on-request           # or public; never confidential
# assessors:                         # optional; who rates the owner's competencies (assessors.py; spec §3.9)
#   dana-okafor: {name: Dana Okafor, role: APC counsellor}   # id: {name, role?}; the id never changes
sources:                             # the owner's own records (onboarding.md §3)
  - path: Career/Resume              # master resume and tailored CVs
    kind: resume-folder
    use: collect                     # read for candidate competencies, cited; not turned into notes
    note: master resume is Resume_Master.md
  - path: Career/Jobs                # one file per role
    kind: job-history
    use: evidence                    # files become evidence notes in place; must be inside the vault
  - path: Career/Private
    use: ignore                      # never read
```

`init` takes every location and source as flags: `--competencies`, `--sectors`, `--evidence`, `--working`, `--reports`, `--outputs`, `--requirements`, `--descriptions`, `--job-specs`, `--own-frameworks`, `--source PATH=USE:KIND` (repeat), `--no-dated`. The `dashboard:` and `assessors:` blocks are added by hand (or `assessors:` from the dashboard, by `assessors.py apply`). A source's `use` is `evidence`, `collect` (default) or `ignore`, and `kind` is free text (`cv`, `resume-folder`, `job-history`, `linkedin`, `github`, `credentials`, `publications`, ...).

---

## 1. Profile: `<graph root>/Profile_<Owner>.md`

```markdown
---
title: Competency Graph Profile - Priya Nair
kgSpecVersion: "0.4"
kgStaleYears: 5
kgPractitionerMinMonths: 6   # months of delivered work for practitioner (default 6)
kgAdvancedMinYears: 5        # years of led work for advanced (default 5)
kgExpertMinYears: 10         # years of led work for expert (default 10)
kgExpertMinRecognition: 1    # kinds of outside recognition for expert (default 1)
kgPeriodAliases: []          # e.g. [tenure] if existing job files already carry dates
kgExclude: [Archive]         # folders the scripts should skip
---

# Competency Graph Profile: Priya Nair

Settings under the competency-graph specification v0.3. Anything not set here follows the specification.

## 1. Setup
| Setting | Value |
|---|---|
| Owner | Priya Nair |
| Graph root | `Competency_Graph/` |
| File locations | `competency-graph.yaml` at the vault root (outputs go to `Career/Applications/`) |
| Scripts | the `competency-graph` skill's `scripts/` folder |
| Industry classification | NAICS 2022 (US) |
| Stale threshold | 5 years |
| Expert definition | Specification rule, plus 5+ years of dated evidence |
| Default `disclosure` | `confidential`; roles and engagements `on-request`; public repos and publications `public` |

## 2. Metadata conventions
- Existing required front matter: ... (or "none")
- Filename style: `PascalCase_With_Underscores`
- **Reserved field names** (already mean something else here; the graph must not reuse them): ...
- Field mappings: ... (e.g. job files' `tenure` is read as `period`)

## 3. Sources
| Source | Treatment |
|---|---|
| `CV/Jobs/*.md` | Become `role` evidence notes in place (front matter added; content untouched) |
| `CV/Resume_2026.md` | Collection only (candidate competencies, with citations) |
| GitHub `priyanair` | One `Repo_<name>` note per repo that proves a competency |

## 4. Evidence classification
| File | evidenceType | via | sector |
|---|---|---|---|

## 5. Domains
| Domain | Disciplines (provisional) | Branches (examples) |
|---|---|---|
Reasons and placement rules: ...

## 6. Milestone
Thin slice M1: scope, pass test (a real question the graph must answer), status.

## 7. Known source-data issues
Fix in the source files, not in the graph.

## 8. Decision log
| Date | Decision |
|---|---|
```

## 2. Placement proposal: `<working folder>/<date>_<Domain>_Placement_Proposal.md`

Claude writes this; the owner approves or edits it before any note is created.

```markdown
# Data & Software Engineering Placement Proposal

Status: **awaiting approval**. Collected from: `CV/Jobs/Acme.md`, `CV/Resume_2026.md`, repos `etl-kit`, `ward-dash`.

Source keys: `AC` Acme job file, `RS` resume, `GH/<repo>` README.

## Batch 1: Disciplines (kind `practice`, broader `Data_and_Software_Engineering`)
| # | Note | Source |
|---|---|---|
| 1 | Data_Pipelines | AC "Achievements" (nightly HL7 feed into the warehouse), GH/etl-kit |

## Batch 2: Specialties
| # | Note | broader | related | Source |
|---|---|---|---|---|

## Batch 3: Methods and tools (new `<Domain>_Methods` / `_Tools` branches)
| # | Note | kind | broader | related | Source |
|---|---|---|---|---|---|

## Judgment calls to confirm
1. **<the call>**, because <reason>. (Anything a reasonable owner might decide differently: two parents, a sector-vs-discipline call, a borderline competency left out.)

## Not created
- <candidate>: <why not> (too minor, no evidence, a strategy document rather than delivered work, ...)

## Evidence plan after approval
New evidence notes:
| Note | Type | Period | partOf | disclosure | demonstrates |
|---|---|---|---|---|---|

Links on existing notes (applied with `edit_links.py`, dry run first):
- `Experience_Acme`: + Data_Pipelines
```

Line numbers are fine in a proposal (it's short-lived); notes cite section headings.

## 3. Competency notes: `<competencies folder>/<Name>.md`

Give every note a short body: one-line definition, then **Scope** and **Boundary**. The boundary is what keeps later placements consistent.

**Domain**
```yaml
---
title: Clinical Practice
nodeType: competency
kind: practice
rank: domain
status: active
---
```
```markdown
# Clinical Practice
Direct care of patients and the practices around it, in any care setting.

**Scope.** Emergency nursing, triage, patient education. **Boundary.** Excludes health data work (Data & Software Engineering) and knowledge of how the health sector is funded (sector note).
```

**Branch root** (one of up to three per domain; its link to the domain means "belongs to")
```yaml
nodeType: competency
kind: method          # tool for <Domain>_Tools, knowledge for <Domain>_Standards_and_Law
rank: branch
broader: ["[[Clinical_Practice]]"]
```

**Practice with two discipline parents** (rare: a genuine overlap, never a sector)
```yaml
nodeType: competency
kind: practice
rank: specialty
broader: ["[[Data_Pipelines]]", "[[Health_Informatics]]"]   # first = main parent
claimedLevel: practitioner
```

**Discipline mapped to a professional body's competency** (spec §3.8; title in the body's wording, old name kept for search)
```yaml
title: Purchase and Sale
nodeType: competency
kind: practice
rank: discipline
broader: ["[[Real_Property_Practice]]"]
aliases: ["Acquisitions & Dispositions"]
externalRef: ["RICS APC 2025: Purchase and sale"]
claimedLevel: L2          # stored as practitioner by edit_links; the checker reads either
```

**Competency with assessors' ratings** (spec §3.9; written by `edit_links.py` from an assessor's worksheet or the dashboard, one string an assessor)
```yaml
nodeType: competency
kind: practice
broader: ["[[Real_Property_Practice]]"]
claimedLevel: advanced          # the owner's own rating: unchanged by an assessment
assessments: ["Dana Okafor | practitioner | 2026-11-13", "Bo Manager | advanced | 2026-11-14"]
# the assessed level is the lowest, practitioner; the checker says the two differ by one level
```

**Practice tied to one sector**
```yaml
nodeType: competency
kind: practice
broader: ["[[Real_Property_Valuation]]"]
sector: ["[[Sector_22_Utilities]]"]
```

**Method or tool** (inside its branch; `related` points at the practice it serves)
```yaml
nodeType: competency
kind: tool
broader: ["[[Data_and_Software_Engineering_Tools]]"]
related: ["[[Data_Pipelines]]"]
aliases: [dbt Core, dbt Cloud]       # search only; aliases never resolve links
```

**Knowledge** (law, regulation, standard)
```yaml
nodeType: competency
kind: knowledge
broader: ["[[Clinical_Practice_Standards_and_Law]]"]
related: ["[[Emergency_Nursing]]"]
```

## 4. Sector note: `<sectors folder>/Sector_<code>_<Label>.md`

```yaml
---
title: Health Care and Social Assistance
nodeType: sector
code: "62"
claimedLevel: practitioner      # optional: knowledge of the sector itself
---
```
Body: what the owner knows about the sector (regulation, funding, major players).

## 5. Evidence notes

**Role tagged in place** (an existing job file: add these keys, change nothing else)
```yaml
# existing fields unchanged
nodeType: evidence
evidenceType: role
period: 2019-03 – present           # or read from an existing field via kgPeriodAliases
organization: St. Brendan's Hospital
sector: ["[[Sector_62_Health_Care]]"]
demonstrates: ["[[Emergency_Nursing]]", "[[Triage]]"]   # competencies used across the whole role
demonstratesLed: ["[[Triage]]"]     # competencies she led here: ran triage for the unit and owned the result
recognition: [teaching]             # trained the unit's new triage nurses (a structured programme)
anchor: "Referee: charge nurse (CRM/People/OKAFOR_Ada)"
disclosure: on-request
```

**Engagement through an agency**: `evidenceType: engagement`, `organization:` the client, `via:` the agency, `sector:` the client's sector.

**Project inside a role** (`Evidence/Projects/Project_<Org>_<Name>.md`)
```yaml
nodeType: evidence
evidenceType: project
period: 2019-03 – present    # date not recorded; bounded by role
partOf: "[[Experience_StBrendans]]"
demonstrates: ["[[Data_Pipelines]]", "[[Python]]"]
disclosure: confidential
```
Body: two or three sentences of what was delivered, with numbers, and the source file and section heading it came from.

**Repo** (`Evidence/Projects/Repo_<name>.md`)
```yaml
nodeType: evidence
evidenceType: project
period: 2024-02-11 – 2025-06-30     # created → last push
anchor: https://github.com/priyanair/ward-dash
demonstrates: ["[[Software_Prototyping]]", "[[Python]]"]
disclosure: public
```
Add `partOf` only if it was built for a specific role or engagement; confirm with the owner. An own repo counts as led work only if others adopted it (`recognition: [adoption]`, with the evidence in the body, such as downstream users or citations).

**Credential** (`Evidence/Credentials/Credential_<abbrev>.md`)
```yaml
nodeType: evidence
evidenceType: credential
period: 2016-06 – present            # still held
organization: Nursing board
anchor: "Registration number (public register)"
demonstrates: ["[[Emergency_Nursing]]"]
recognition: [credential]            # only for a senior or chartered credential, not an entry-level certificate
disclosure: public
```
A credential or course alone supports `aware`; it adds `recognition` to a competency that has led work, but it is never led work itself.

**Course**: `evidenceType: course`, a dated `period`, the certificate as `anchor` if there is one. **Activity** (ongoing volunteer or professional service, a talk, an assessor seat): `evidenceType: activity`, `organization` required.

## 6. Plan file for `edit_links.py`

```yaml
- note: Experience_StBrendans
  field: demonstrates
  add: ["Data_Pipelines", "Triage"]
- note: Emergency_Nursing
  field: related
  remove: ["Triage"]
- note: Repo_ward-dash
  field: anchor
  set: https://github.com/priyanair/ward-dash
```
Run `edit_links.py --vault . plan plan.yaml` (dry run), show the owner the diff summary, then add `--apply`.

---

## 7. Experience record: `<the owner's career folder>/Experience_<year>_<Organisation>.md`

The owner's own write-up of one role or engagement, kept up to date as `recording-experience.md` describes; the evidence note for the role is this file with the graph fields in its front matter (§5, *role tagged in place*). Keep the owner's own keys, and use the vault's date field for `period` if it has one (`kgPeriodAliases`).

```markdown
---
title: "Asset Systems Analyst"
organization: "Harbour Water Board"
tenure: 2024-03-04 – present
status: current
lastUpdated: 2026-06-30
keywords: [asset management, hydraulic modelling, capital planning]
# competency graph
nodeType: evidence
evidenceType: role
sector: ["[[Sector_22_Utilities]]"]
demonstrates: ["[[Hydraulic_Modelling]]", "[[EPANET]]", "[[Capital_Planning]]"]
demonstratesLed: ["[[Hydraulic_Modelling]]"]
disclosure: on-request
anchor: "a referee, a register entry or a public link"
---

# Harbour Water Board: Asset Systems Analyst

> Two years in. Bullets record delivered work only. Work that is scoped, drafted or scheduled but not delivered stays under "In progress (not yet delivered)" until it ships.

## Role snapshot
- **Title:** Asset Systems Analyst · **Reports to:** Head of Asset Planning · **Scope:** the northern network · **Team:** two analysts

## Organisation context
Two or three sentences from public information: what the organisation does, and where this role sits in it.

## Mandate as contracted
What the role was hired to do, from the role description. The contract, not a record of performance.

## Responsibilities & impact

### Hydraulic modelling
- Cut the model's calibration error from 14% to 4% across 212 pressure zones by rebuilding the demand allocation in EPANET from two years of logger data. <!-- src: report, Nov 2025; verified; hamz -->
- Chairs the monthly model review with operations. <!-- src: calendar, Jun 2026; verified; supporting -->

### In progress (not yet delivered)
- A pump-scheduling study for the eastern zone, due in the autumn.

## Systems & tooling
EPANET, the asset register, the board's GIS.

## Recognition & thought leadership
- Presented the calibration method to the regional modelling group (Feb 2026).

## Evidence & artefacts
### Work-side evidence (held on the employer's systems, not copied)
- Calibration report to the asset planning committee (Nov 2025).

## Handling notes
- Who may be named: the board, yes; contractors and sites, no.
- The agreement with the employer: work product stays with the board; this file describes the work and holds none of it.
```

A bullet's tag says where it came from (a kind of source and a month, never a link), whether it was seen (`verified`) or said (`self-reported`), and whether it meets HAM-Z (`hamz`: a named tool or method, an action, a number from a source, and the process) or is a `supporting` point with no number yet.

---

## 8. Layer 3: a prerequisite, an organisation note, a person note

All optional (spec §2.1, §2.4, §2.5, §3.10). Add one where the owner has a use for it, never in bulk.

**A prerequisite, and a tool applied to a practice** (two competency notes)
```yaml
# Hydraulic_Modelling.md
nodeType: competency
kind: practice
broader: ["[[Water_Network_Engineering]]"]
claimedLevel: advanced
requires: ["[[Fluid_Mechanics]]"]      # cannot be held above the level claimed for Fluid_Mechanics
```
```yaml
# EPANET.md
nodeType: competency
kind: tool
broader: ["[[Infrastructure_Engineering_Tools]]"]
appliedTo: ["[[Hydraulic_Modelling]]"]  # the practice this tool serves
```

**Organisation**: `<graph root>/Organizations/Org_Harbour_Water_Board.md`
```yaml
nodeType: organization
title: Harbour Water Board
aliases: ["HWB", "Harbour Water"]       # every other way the evidence writes it: all count as this one
sector: ["[[Sector_22_Utilities]]"]
crm: "Contacts/Organisations/Harbour_Water_Board"   # the owner's own record; nothing is copied from it
```
An evidence note whose `organization` is `Harbour Water Board`, `HWB` or `[[Org_Harbour_Water_Board]]` now counts as this organisation. No evidence note has to change.

**Person**: `<graph root>/People/Person_Meera_Shah.md`
```yaml
nodeType: person
title: Meera Shah
role: Head of Asset Planning; line manager 2024 to 2026
organization: "[[Org_Harbour_Water_Board]]"
crm: "Contacts/People/SHAH_Meera"
```
Named on the evidence she can speak to: `referee: ["[[Person_Meera_Shah]]"]`. The body can say what she saw and how to reach her, at the note's own level of discretion; a person note has no `disclosure`, so keep out of it anything that must not travel with the graph.
