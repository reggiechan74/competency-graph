# Choosing domains and an industry classification

Read this for build step 3 (setting the domains) and when the profile interview reaches the industry classification. It explains *why* the tree is discipline-first and gives the reference standards to check a proposed domain list against.

## Contents
1. Why discipline first, sector separate
2. Reference standards for checking domains
3. Proposing domains
4. Industry classifications for sector notes
5. Sector coding rules
6. Professional Practice and professional-body frameworks

---

## 1. Why discipline first, sector separate

Existing standards disagree about what a top-level category *is*: some sort by academic discipline, some by industry, some by sector of practice. Most of the hard multi-parent cases in a person's competencies come from mixing two of those axes in one tree.

| Competency | Discipline (what) | Sector (where) |
|---|---|---|
| Corridor valuation | Valuation | Utilities, transportation |
| Property accounting | Accounting | Real estate |
| Clinical data engineering | Data engineering | Health care |
| Construction claims law | Contract law | Construction |

Put both axes in one tree and nearly every specialist competency gets two parents, the tree mostly records sector, and the competencies that *transfer* between sectors (the most valuable thing a career graph can show) disappear. Separate them and:

- the tree holds only "X is a specialization of Y" links, so most nodes have one parent;
- sector becomes a filter ("my valuation evidence in infrastructure") and a claim of its own (knowledge of how a sector works);
- the remaining multi-parent nodes are rare and meaningful: real overlaps between disciplines, which the checker reports as cross-domain insights.

People often arrive with a sector-first mental model ("leasing is a subset of real estate"). The precise version is: leasing is a discipline within real property *practice*; commercial real estate is the *sector* where it was practised. Explain this once, with one of the owner's own examples, before proposing domains.

## 2. Reference standards for checking domains

Use these as vocabulary and as a sanity check, not as the tree itself. None fits a single person's mix of work.

| Standard | Top level sorts by | Use it for |
|---|---|---|
| **ISCED-F 2013** (UNESCO fields of education) | Academic discipline: broad → narrow → detailed field (e.g. 04 Business, administration & law → 041 → 0411 Accounting & taxation) | Naming knowledge-heavy disciplines; the discipline-first backbone |
| **ESCO** (EU competencies, competences, occupations) | Knowledge / competencies / attitudes / language; knowledge concepts follow ISCED-F. Concepts may have several parents | An `esco` URI on a competency makes graphs comparable across people |
| **O\*NET** (US occupations) | Occupations, with knowledge, competencies, abilities, work activities | Vocabulary for practice notes; detailed work activities help phrase disciplines |
| **Lightcast Open Skills** | Industry / career area → subcategory → skill; each skill typed specialized, common or certification | Spelling of tool and method names. A warning too: an industry-first tree scatters cross-industry work |
| **SFIA** (digital competencies) | Categories that SFIA itself calls navigation aids only | Data, software and AI disciplines; codes go in `externalRef` |
| **Professional body frameworks** (e.g. RICS APC pathways, CFA topic areas, CPA competency maps, nursing or engineering competency standards) | Usually sector of practice or exam subject, often mixed | The owner's own profession's names for its disciplines; credentials' competency codes go in `externalRef` |
| **Faceted classification** (Ranganathan; Art & Architecture Thesaurus) | Several independent axes instead of one tree | The theory behind keeping sector as its own axis |

Look up the current version of any standard you cite; several revise every few years.

## 3. Proposing domains

- Aim for **3–8 domains**: about 3 for a focused career, 5–8 for a long or varied one. Too few hides real breadth; too many turns domains into disciplines. Don't pad a short career to reach a number.
- Derive them from the collected candidate competencies, not from a standard: cluster the candidates, name each cluster by discipline, then check the names against §2.
- **Law and regulation are usually not a domain.** Statutes and standards sit in each domain's *Standards & Law* branch; knowledge of how a sector is regulated sits on the sector note.
- **Personal and non-career knowledge is legitimate** (heritage, languages, music, sport coaching). Ask whether the owner wants it in; the graph is theirs.
- For each domain, record in the profile: name, example disciplines, likely branches (Methods, Tools, Standards & Law), and the reason it exists. The owner decides; record the decision with a date.

A good domain table in the profile looks like:

| Domain | Disciplines (provisional) | Branches (examples) |
|---|---|---|
| **Clinical Practice** | Emergency nursing · Triage · Patient education | Methods: SBAR handover · Standards & Law: provincial scope-of-practice rules |
| **Data & Software Engineering** | Data pipelines · Analytics · Software prototyping | Tools: Python, SQL, dbt |

## 4. Industry classifications for sector notes

Pick **one** classification, by the owner's country and what their recruiters or clients use. State it, with its version, once in the profile.

| Region | Classification | Notes |
|---|---|---|
| USA, Canada, Mexico | **NAICS** (US 2022; NAICS Canada 2022 v1.0) | 2-digit sectors 11–92. Three sectors are ranges: 31–33, 44–45, 48–49. Canada's next edition is NAICS Canada 2027 |
| EU | **NACE Rev. 2.1** | Letter sections A–V, then 2-digit divisions |
| UK | **UK SIC 2007** | Derived from NACE; check whether a newer UK SIC is in force |
| Australia, New Zealand | **ANZSIC 2006** | Divisions A–S; a revision is in progress |
| Anywhere / international | **ISIC Rev. 5** (UN) | The parent of NACE; a safe default when nothing local fits |

Prefer these over older or home-made lists. US SIC (1987) is obsolete outside SEC filings and has no codes for most modern data, software or platform businesses.

## 5. Sector coding rules

- Each sector note carries `code:` as a **quoted** string (`"22"`, `"J"`, `"62.01"`) so YAML doesn't turn it into a number. Filenames: `Sector_<code>_<Short_Label>.md`.
- Create sector notes **only when evidence needs them**, starting at the top level (2-digit NAICS, NACE section). Go deeper only when the owner needs the distinction (e.g. air transport vs. transit), and then link the deeper note to its parent with `broader`.
- Code the **business where the work was done**: the employer's operating unit, or for an engagement the client, not a corporate parent. A real-estate investment unit of an insurer is coded as real estate if that is what it did. Record the coding rule in the profile.
- Government bodies are coded by activity under NAICS (a transit agency is transportation), not automatically as public administration. Check the classification's own rule.
- Asset class, client size and geography are not industry codes. If the owner needs them, propose a separate field and add it to the profile first (principle 6).
- When the classification is revised, remap codes in one pass with `edit_links.py`.

## 6. Professional Practice and professional-body frameworks

Offer this when the owner holds, or is working toward, a professional body's membership, or simply wants their graph to show the conduct every professional is expected to have.

**A cross-cutting domain.** Most professional bodies list two kinds of competency: technical ones that belong to the profession's disciplines, and mandatory or behavioural ones expected of every member whatever their discipline (RICS APC mandatory competencies; ESCO transversal competencies; SFIA behavioural factors; CPA enabling competencies). The second kind cuts across every other domain, so it can sit in its own domain, **Professional Practice**. It is optional: a graph with only a few such competencies can keep them in a management domain.

Rules for placing framework competencies:

1. **A competency that is already a discipline stays in its domain** and gets an `externalRef` (accounting, business planning, data management, leadership, project management). Don't give a note a second parent just to sit in a framework's list. The framework's view comes from `externalRef`, never from the tree's shape.
2. **A competency that isn't anywhere yet** goes in Professional Practice (ethics, client care, communication and negotiation, health and safety, conflict avoidance and dispute resolution, diversity, inclusion and teamworking, inclusive environments, sustainability).
3. **Technical competencies map onto the existing disciplines** with `externalRef`. Create a new discipline only for a competency the owner's evidence shows and the tree lacks (e.g. *Landlord and tenant* gathering lease administration and lease economics). Leave out competencies with no evidence; mandatory ones may be created as L1 Aware claims, since every member is expected to know them.
4. **Titles.** Retitle a note in the framework's wording if the owner wants consistency with the framework; keep the filename (so no link breaks) and put the old name in `aliases`.
5. **Levels: always L1–L4.** Map the framework's own levels onto L1 Aware, L2 Practitioner, L3 Advanced, L4 Expert by meaning, never use them as they stand, and record the mapping with its reason in the decision log once the owner approves it. Frameworks with three levels (knowledge, application, reasoned advice) map to L1–L3 one to one; L4 Expert is beyond them. A credential's examined syllabus (e.g. the CFA charter) is L1 for every topic it covers. Belt or tier systems map by role (Six Sigma: Yellow L1, Green L2, Black L3, Master Black L4). An educational taxonomy such as Bloom's describes exam questions, not practice: use the role the certificate qualifies for instead. The requirements file holds only `L1`–`L4`, `L2 or L3` or `choice`, and the checker enforces it.

**Preconfigured frameworks.** Before mapping a framework by hand, look in `assets/frameworks/catalog.yaml` (`frameworks.py list --all`): all 23 RICS APC pathways, the CFA Candidate Body of Knowledge, the ASQ Six Sigma Green Belt and three role frameworks (Chan AFSE, agentic full-stack engineering; Chan AGEN, agentic genealogy; Chan CXMDS, customer experience and managed data services), each with one pathway in Mandatory, Core and Optional, its options listed by specialisation, are there, already on L1–L4. Select them under `frameworks:` in the config. A framework whose catalog entry names a `guide` (e.g. `chan-agen.md`) has its level descriptors there: read the competency's row before suggesting a level against it. A framework with `status: draft` in the catalog has not passed review (Chan AGEN and Chan CXMDS, November 2026): offer it only as a draft, with its `status_note`.

**Mandatory, Core and Optional: what each group means.** When a framework is written (the library's or the owner's own), each competency goes in one group by this rule:

- **Mandatory** competencies apply to every pathway in the same field. All the pathways in a field carry the same Mandatory list, at the same levels and with the same level wording. RICS APC is the model: its 23 pathways share the same eleven mandatory competencies. Mandatory is what anyone working in the field must hold, whatever their pathway.
- **Core** competencies are the baseline of one pathway only: the work that pathway consists of.
- **Optional** competencies are where a person on that pathway chooses to go deeper. Specialisations are sub-groups of Optional.

So settle the field before the groups. Two frameworks in the same field are two pathways of it and list the same Mandatory competencies (Chan AFSE and Chan AGEN are both agentic). A competency that only one of them requires is Core there, however important it is to that pathway. A framework alone in its field still writes its Mandatory list as what a later pathway in that field would share. In the catalog, frameworks in one field carry the same `field:` value. "Field" here is the area of practice a framework belongs to, not an industry: the graph keeps `sector` for industries (§4).

**The owner's own frameworks.** A competency the owner's evidence shows and no body defines (a firm's method, a tool, a niche practice) can still be measured and put in a job spec: put it in the owner's own framework, a folder named by `ownFrameworks` in the config with the library's format (a `catalog.yaml` entry, and a descriptions file with a description and L1–L4 wording per competency; a requirements `file` only if it has pathways). Mark it `status: draft` until the owner has approved each description, give the notes their `externalRef` (`"<Own framework> <year>: <name>"`), and keep it in their vault, not the skill's library, since another owner wouldn't use it. Leave out the tree's grouping notes (domains and their `_Methods`, `_Tools`, `_Standards_and_Law` branches): a job asks for a competency, not a branch.

`externalRef` format: `"<framework> <edition>: <competency name or code>"`, e.g. `"RICS APC 2025: Leasing/letting"`, `"SFIA 9: DATM"`. Use the competency name exactly as the current edition spells it; look the edition up, since bodies revise their lists every few years (RICS reissued its APC guides in December 2025).

**Worked example (pilot graph, RICS APC, December 2025 guides).**

| RICS competency | Placement |
|---|---|
| Ethics, Rules of Conduct and professionalism; Client care; Communication and negotiation; Health and safety; Conflict avoidance, management and dispute resolution procedures; Diversity, inclusion and teamworking; Inclusive environments; Sustainability | New competencies under Professional Practice. Negotiation, with its lease and settlement specialties, moved under Communication and negotiation |
| Accounting principles and procedures; Business planning; Data management; Leadership; Managing people; Managing resources | Existing disciplines in Finance & Accounting, Management & Strategy and Data Management & Analytics, with `externalRef` |
| Leasing/letting; Asset management; Purchase and sale; Compulsory purchase and compensation; Development appraisals | Existing disciplines retitled in RICS wording, old names in `aliases` |
| Landlord and tenant; Access and rights over land; Strategic real estate consultancy | New disciplines in Real Property Practice, gathering existing specialties where they fit |
| Investment management (including fund and portfolio management); Financial modelling; Valuation; Property management; Due diligence; Planning and development management | Existing competencies with `externalRef`; portfolio optimisation moved under Investment Analysis, as RICS folds portfolio management into investment management |

