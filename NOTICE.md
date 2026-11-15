# Notice: what the licence covers, and third-party material

## What the MIT licence covers

The MIT licence in `LICENSE` covers Reggie Chan's own work in this repository: the method, the specification, the scripts and their tests, the dashboard page, the templates and guides, the evals, the level wording drafted for the graph, and the Chan frameworks (Chan AFSE, Chan AGEN, Chan CXMDS).

It does **not** cover material that belongs to third parties. That material is included for convenience, so that a person can measure their own record against a framework they already work to. It remains the property of its owners, and nothing here grants any right over it.

## Third-party material included in the framework library

The files are in `skills/competency-graph/assets/frameworks/`. `catalog.yaml` gives each framework's edition and the address of the guide it was taken from, and the `source` column of each descriptions file says where every part of a row came from.

| Framework | Owner | What is included | Files |
|---|---|---|---|
| RICS Assessment of Professional Competence (APC) | Royal Institution of Chartered Surveyors | Pathway and competency names, required levels and selection rules from the December 2025 *Requirements and competencies* guide and the September 2026 *Data analytics and intelligence* pilot guide. The descriptions and the wording of each level are the author's own, written for North American practice from the meaning of those guides and not copied from them | `rics-apc.csv`, `rics-apc-descriptions.csv` |
| CFA Program Candidate Body of Knowledge (CBOK) | CFA Institute | Topic area names and structure from the published CBOK and 2027 curriculum topic weights. The descriptions and level wording are drafted for the graph | `cfa-cbok.csv`, `cfa-cbok-descriptions.csv` |
| Six Sigma Green Belt Body of Knowledge (CSSGB) | ASQ | Section and topic names from the 2022 Body of Knowledge. The descriptions and level wording are drafted for the graph | `asq-cssgb.csv`, `asq-cssgb-descriptions.csv` |

These frameworks are restated on the graph's own L1 to L4 scale, which is the author's mapping and not the owners'. A body's current published guide is the authority: check a framework against it before relying on it.

RICS, APC, MRICS and FRICS are marks of the Royal Institution of Chartered Surveyors. CFA and CBOK are marks of CFA Institute. ASQ and CSSGB are marks of ASQ. This project is not affiliated with, endorsed by or sponsored by any of them.

A rights holder who wants material changed or removed can open an issue on this repository.

## Sources referred to, not copied

The method and the Chan frameworks draw on published ideas and cite them by name. Their wording is not reproduced.

- **Levels:** the Dreyfus model of skill acquisition, the US OPM and NIH proficiency scales, SFIA's levels of responsibility, and the RICS APC levels (`references/specification.md` §3.7).
- **Taxonomy:** ISCED-F 2013, ESCO, O\*NET, Lightcast Open Skills, SFIA, faceted classification (`references/domains-and-classifications.md` §2).
- **Industry classifications:** NAICS, NACE, UK SIC, ANZSIC and ISIC, used as codes on sector notes (`references/domains-and-classifications.md` §4).
- **The Chan frameworks:** each file lists the references it was checked against under its own sources and "Mapping to other references" sections, SFIA 9 among them (names and levels cited; the wording is not copied).

## Bundled software

| Software | Licence | Where |
|---|---|---|
| D3 v7.9.0, © 2010–2023 Mike Bostock | ISC | `skills/competency-graph/scripts/tests/vendor/d3.min.js`, with its licence in `d3.LICENSE`. Used only by the browser tests; the dashboard itself gets d3 from the claude.ai Dashboard runtime |
