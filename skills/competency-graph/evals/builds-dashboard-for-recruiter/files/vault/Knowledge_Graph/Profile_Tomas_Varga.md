---
title: Competency Graph Profile - Tomás Varga
kgSpecVersion: "0.3"
kgStaleYears: 5
kgExpertMinYears: 5
kgPeriodAliases: [dates]
---

# Competency Graph Profile: Tomás Varga

Settings under the competency-graph specification v0.2.

## 1. Setup
| Setting | Value |
|---|---|
| Owner | Tomás Varga |
| Graph root | `Knowledge_Graph/` |
| Industry classification | NAICS Canada 2022 v1.0 |
| Stale threshold | 5 years |
| Expert definition | Specification rule plus 5+ years of dated evidence |
| Default `disclosure` | `confidential`; roles and engagements `on-request`; public repos, credentials and courses `public` |

## 2. Metadata conventions
- No required front matter beyond `title`.
- **Reserved field names:** `status` in `CV/Jobs/*.md` means current/completed job; the graph ignores it on evidence notes.
- Field mappings: job files' `dates` is read as `period`.

## 3. Sources
| Source | Treatment |
|---|---|
| `CV/Jobs/*.md` | Become `role`/`engagement` evidence notes in place |
| `CV/Resume_2026.md` | Collection only |
| `CV/Certifications.md` | Source for credential and course notes |
| GitHub `tvarga` | `Repo_<name>` notes |

## 5. Domains (decided 2026-10-02)
| Domain | Disciplines |
|---|---|
| **Infrastructure Engineering** | Water Network Engineering · Infrastructure Asset Management (→ Capital Planning) · Hydraulic Modelling |
| **Data & GIS** | Data Analysis (→ Leak Detection Analytics, 2nd parent Water Network Engineering) · Geospatial Analysis · Data Engineering |
| **Education & Communication** | Teaching & Training · Technical Writing |

## 6. Milestone
All three domains built 2026-10-20. Ratings set 2026-10-21.

## 8. Decision log
| Date | Decision |
|---|---|
| 2026-10-02 | Three domains, discipline-first; NAICS Canada 2022 |
| 2026-10-20 | Aquifer's Great Lakes pressure-zone work is `confidential` (NDA) |
