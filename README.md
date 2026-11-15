# competency-graph

A Claude Code plugin that helps one person build and keep a **competency graph**: what they know, and the evidence that proves it.

The graph is a folder of plain markdown notes that the owner controls (an Obsidian vault or any folder, often a git repository). Claude proposes, the owner decides, and every claim can be traced back to a job, a project, a credential or another record the owner already has.

## What it does

- **Maps competencies** into a tree organised by discipline, with industry sectors kept as a separate axis.
- **Links evidence** (jobs, engagements, projects, repositories, credentials, courses, publications, activities) to the competencies it demonstrates.
- **Works out the level the evidence supports**, from L1 Aware to L4 Expert, and compares it with the level the owner claims.
- **Flags** claims above their evidence, stale evidence and claims that stand above a prerequisite.
- **Measures the graph against frameworks**: professional bodies' competency frameworks and the owner's own.
- **Scores the graph against a role** through job specs made of framework competencies.
- **Records another person's rating** (a supervisor, counsellor or manager) beside the owner's own.
- **Builds a dashboard** for claude.ai from the owner's files.
- **Pulls the evidence behind a competency** for a CV, an application or an interview, respecting what may be disclosed.

## Install

Add this repository as a marketplace, then install the plugin:

```
/plugin marketplace add reggiechan74/competency-graph
/plugin install competency-graph@competency-graph
```

To try a local copy, point the marketplace at the folder instead:

```
/plugin marketplace add /path/to/competency-graph
```

### Requirements

- Python 3 with PyYAML (`pip install pyyaml`). Claude asks before installing it.
- Nothing else is needed to build and check a graph.
- The dashboard needs a claude.ai account with the Dashboard artifact type.

## Use

Start a new graph:

```
/competency-graph:competency-graph --buildnew
```

Or just ask, for example:

- "Turn my resume folder into a competency graph."
- "Add my new contract to the graph."
- "What supports my claim for leasing?"
- "Which of my claims are stale or unsupported?"
- "How do I measure up against this job ad?"
- "Build my dashboard."

Claude asks where your records are, proposes domains and placements for you to approve, and creates no note until you have approved its place.

## Where your files go

Your graph lives in your own files, never in this plugin. A `competency-graph.yaml` file records where everything is saved.

| Where you start | Default location |
|---|---|
| Inside a git repository | `Competency_Graph/` at the repository's root |
| Anywhere else | `Competency_Graph/` in your Documents folder |

You can choose any other place. `kg_config.py where` prints the default for the folder you are in.

## What is in the plugin

Everything is under `skills/competency-graph/`:

| Folder | What it holds |
|---|---|
| `SKILL.md` | The method Claude follows, and the ground rules |
| `references/` | The specification, templates, onboarding, the dashboard guide, how to record a job |
| `scripts/` | The checker, queries, the safe link editor, worksheets, the summary and dashboard builders, and their tests |
| `assets/frameworks/` | The framework library |
| `assets/dashboard/` | The dashboard page and its design notes |
| `evals/` | Test cases for the skill itself |

## The framework library

| Framework | Source | Status |
|---|---|---|
| RICS APC | Royal Institution of Chartered Surveyors, December 2025 guides | Restated on L1 to L4 |
| CFA CBOK | CFA Institute, 2027 curriculum topic weights | Restated on L1 to L4 |
| ASQ CSSGB | ASQ, 2022 Six Sigma Green Belt Body of Knowledge | Restated on L1 to L4 |
| Chan AFSE, Chan AGEN, Chan CXMDS | The author's own role frameworks | Drafts, under review |

The first three are drawn from those bodies' published guides, which remain theirs (see `NOTICE.md`). Check a framework against its current guide before relying on it: bodies revise them every few years. `catalog.yaml` lists each framework's sources and how its levels were mapped.

## Versions

Three things carry a version, and they move separately:

| What | Version | Where it is recorded |
|---|---|---|
| This plugin | 0.1.0 | `.claude-plugin/plugin.json`, `CHANGELOG.md` |
| The specification (the graph's fields and rules) | 0.5 | `references/specification.md` |
| The dashboard page | 1.7.2 | `assets/dashboard/DESIGN.md` |

## Development

Run the tests from the skill's scripts folder:

```
cd skills/competency-graph/scripts
python3 -m pytest tests -q
```

The dashboard page's tests need Node with jsdom, and Playwright with Chromium; each is skipped when its tool is missing. Before publishing a change to the page, also render it under the Dashboard type's real stylesheet (`scripts/tests/render_page.py`, described in `assets/dashboard/DESIGN.md`).

## Status

The method and the dashboard were built and proven on the author's own graph. The plugin is at 0.1.0: the first release outside that repository.

## Licence

MIT, for the author's own work: see `LICENSE`.

The framework library also includes material from RICS, CFA Institute and ASQ, included for convenience. It remains theirs and the MIT licence does not cover it. `NOTICE.md` says exactly which material that is, lists the published ideas the method draws on, and gives the licence of the one bundled library (D3, used by the tests).
