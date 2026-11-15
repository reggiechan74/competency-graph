# Changelog

Changes to the plugin, newest first. The plugin and its dashboard page share one version number; what changed on the page itself is also listed in `skills/competency-graph/assets/dashboard/DESIGN.md`. The specification keeps its own history in `references/specification.md`.

## 1.8.0 (2026-11-15)

- **Everything an owner adds is saved in their own files, never in the plugin.** The plugin's folder is replaced on every update, so the scripts now refuse a setting or an output that points inside it, and the docs no longer tell anyone to add a framework to the shipped library.
- **A home for your own frameworks:** `Frameworks/` under the graph folder, read once it holds a catalog, with no setting needed (`ownFrameworks` still names another place).
- **`frameworks.py new`** starts one there: an empty framework to fill in (`--name`), a list of competencies only (`--no-pathways`), or a copy of a shipped framework (`--from`).
- **Your own edition of a shipped framework:** a copy under the shipped id takes its place for you, keeping its name so your notes still match. `frameworks.py list` marks it and says when the plugin's has changed since you copied it.
- Two own frameworks may no longer share a name.
- The dashboard page is unchanged.

## 1.7.2 (2026-11-15)

- **One version number.** The plugin takes the dashboard page's number, so the version a dashboard shows is the release of the plugin that built it. `tools/bump_version.py` writes the number everywhere it appears, a test fails if any two places disagree, and each release is tagged `vX.Y.Z` on GitHub. The page itself is unchanged from 1.7.2.
- **README:** a *How it works* section with the dashboard's own six drawings (exported by `tools/export_figures.py`, in light and dark), and badges.
- Everything listed under 0.1.1 and 0.1.0 below, which were the plugin's numbers before it shared the page's.

## 0.1.1 (2026-11-15)

- RICS APC level wording: the 213 L1 to L3 cells that repeated RICS's guides in whole or in part are reworded for North American practice, from the guides' meaning and the pathway guides' examples. No level cell now shares more than a fifth of its six-word runs with the guides. Competency names, required levels and selection rules are unchanged.
- `NOTICE.md` says so.

## 0.1.0 (2026-11-15)

The first release as a plugin. The skill was moved here from the author's own repository, where it was built and tested on a pilot graph.

- The `competency-graph` skill: specification v0.5, dashboard page 1.7.2.
- A new graph's default folder is `Competency_Graph`: at a git repository's root, or in the Documents folder outside one.
- The framework library: RICS APC, CFA CBOK, ASQ CSSGB, and the drafts Chan AFSE, Chan AGEN and Chan CXMDS.
- MIT licence for the author's own work; `NOTICE.md` sets out the third-party material it does not cover.
