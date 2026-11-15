# Recording work experience

Read this when the owner wants to write down what they did in a job, an engagement or a project, or bring such a record up to date ("record my work at …", "update my experience file", "I've been in this role three months"), and when a build finds a role whose record is too thin to tag. The graph is only as good as the records it points at: an evidence note is a record with a few fields added, and its body is what a CV line or a claim is checked against (ground rule 6).

## Contents
1. What a good record is
2. Where the work is
3. The steps
4. HAM-Z: the standard for a bullet
5. The sanitisation gate
6. How often
7. From a record to CV bullets

---

## 1. What a good record is

One file for each role or engagement, kept with the owner's other career files (a `sources` entry with `use: evidence`, so the file becomes the evidence note in place). The template is `templates.md` §7.

A record written from memory the week a CV is due is thin and unprovable. A good one is written while the work is still within reach, from what the work left behind:

| Rule | Why |
|---|---|
| **Only what was delivered.** The job description goes under *Mandate as contracted*, never among the achievements | A bullet that could have been written on the first day proves nothing |
| **No number that isn't in a source.** A missing metric is left out, or asked for; it is never estimated | One invented figure makes every other figure doubtful |
| **Who did the work is said plainly:** led, co-designed with the team, contributed to | It decides whether the work counts as led (spec §3.7) |
| **Work in flight is kept apart**, under *In progress (not yet delivered)*, until it ships | The record is read later as a list of results |
| **Each bullet says where it came from** and whether it was seen or only said | So a later check, or a referee, can follow it |
| **Nothing confidential leaves the employer's systems.** The record says what the owner did, never the work product itself | The owner's agreement with the employer, and the people in the work, come first |

## 2. Where the work is

- **Within reach of this session** (the owner's own repositories, their own mail and calendar, client folders they hold): follow §3 here.
- **On an employer's machine or accounts**, which this session cannot and should not reach: give the owner `assets/prompts/experience-update.md`. They paste it into Claude *there*. It installs a small skill, `experience-update`, that follows the same steps on that side, passes the sanitisation gate, and prints one complete file for the owner to carry back. Then continue here at step 7.

Never ask the owner to copy work product across so that it can be read here.

## 3. The steps

1. **Inventory.** Read the record as it stands: its dates, its sections, every bullet already there (so nothing is added twice), and its *Handling notes*, which say what may be named. No record yet: start one from the template, filling only the role snapshot, the organisation context and the mandate as contracted.
2. **Gather the evidence, read-only.** Search what can be reached for the period since the record was last updated: calendar (cadences run, presentations given), mail and chat (what the owner *sent*: deliverables, resolved escalations, thanks received), documents (what the owner wrote or owns), tickets (issues closed, cycle times), dashboards (aggregates only), repositories (tools built). Send, post, edit and comment on nothing. Say which sources were searched and which could not be reached.
3. **Build an evidence ledger** in the conversation. It never goes into the record.

   | # | Candidate achievement | Source (kind and month, no links) | Metric | Baseline | Period | Confidence |
   |---|---|---|---|---|---|---|

   Confidence is `verified` (seen in a source), `self-reported` (the owner said so) or `missing`.
4. **Interview the owner once.** Show the ledger, then ask one batch of at most eight questions aimed at its gaps: a missing metric or baseline, what the owner's own part was in shared work, what was led and what was supported, anything delivered that left no trace, recognition received. Don't ask for what a source already answered.
5. **Write the bullets** to the HAM-Z standard (§4), under headings that name the kind of work. Past tense for finished work, present tense for a standing duty. A newer number replaces the older one in the same bullet. Plain words, in the voice the record already has.
6. **Check before anything is saved.** First the facts: read each new or changed bullet against its source as a sceptic would, and mark it supported, unverifiable (not found in a source: flag it) or contradicted (conflicts with one: fix or drop it). Look for an invented number, a scope made larger, a projection stated as a result, a team's result claimed alone, and a tool no source names. Then the sanitisation gate (§5) when the record leaves an employer's systems.
7. **Take it into the graph**, as a proposal the owner approves (ground rule 1):

   | In the record | Becomes |
   |---|---|
   | Dates, organisation, the client's industry, who may see it | `period`, `organization`, `sector`, `disclosure` on the evidence note |
   | **H**, each named tool, method, standard or statute | `demonstrates` a tool, method or knowledge competency (propose a new one where the graph has none) |
   | **Z**, the process: what kind of work it was | `demonstrates` a practice competency |
   | **A**, where the verb is one of ownership (led, decided, owned, advised and was relied on) | `demonstratesLed` for that competency, quoting the bullet. Involved is not led |
   | Thanks from outside the team, a talk given, a method others took up, an appointment | `recognition`, sparingly |
   | A referee, a public link, a register entry | `anchor` |
   | More than about fifteen competencies on one role | The specific work split into `project` notes with `partOf` |

   Apply the approved links with `edit_links.py`, run the checker, and rebuild the dashboard if the owner has one. The record's body is not rewritten by this step.

## 4. HAM-Z: the standard for a bullet

HAM-Z joins two older habits: the XYZ sentence ("accomplished X, as measured by Y, by doing Z") and a checklist of what a strong line contains. A bullet meets it when it has all four parts:

| Part | What it is | Test |
|---|---|---|
| **H** Hard skill or tool | A named tool, system, framework, standard, statute or technical method | Could a reader look it up? "A leasing platform" fails; its name passes |
| **A** Action | A concrete verb for what the owner did: built, cut, led, mapped, negotiated, onboarded | Does it say who did it and how much of it was theirs? |
| **M** Metric | A number from a source, with its baseline and its period where they exist: a percentage, an amount, a count, an area, hours, a rank | Can the number be found in a source? "Improved on-time submissions" fails; "from 62% to 91% on time across two quarters" passes |
| **Z** Process | The mechanism: how the result came about | Would the sentence still be true of someone who did it another way? Then it is too vague |

> **[Result: action and metric] by [process], using [hard skill or tool].**
>
> *Cut average lease cycle time by 50% by leading the company-wide roll-out of the VTS leasing platform, moving the whole deal pipeline online from offer to signing.*

**The metric is the gate.** A bullet with no number from a source is not a HAM-Z bullet, and no number is made up to make it one. Such a bullet is still worth keeping when a reader would care: it is a *supporting point*. So every achievement bullet is one of two kinds, and says which in its source tag:

```
- Cut average lease cycle time by 50% ... <!-- src: dashboard, Mar 2026; verified; hamz -->
- Chaired the weekly client cadence for the account ... <!-- src: calendar, Feb 2026; verified; supporting -->
```

`src:` gives the kind of source and the month, never a link; then `verified` or `self-reported`; then `hamz` or `supporting`. A supporting point becomes a HAM-Z bullet the day its number turns up.

**Accuracy, which outranks polish:**

1. Never invent or estimate a metric.
2. A projection is written as a projection ("projected a 30% saving"), never as a result.
3. A team's or an organisation's result is written as a contribution to it, not as the owner's alone.
4. Scope is kept exact: the part of the programme the owner had, not the whole programme.
5. No tool or framework that no source names.
6. An edit for style only recombines facts already in the record. A pass that brings in new facts is checked again (step 6).

**Style:** lead with the number, then "by" and the mechanism, in one dense sentence. Fold a supporting fact into the bullet it strengthens. Merge two bullets about the same thing, keeping every distinct number. State a portfolio's size or a project's scope once. Ask of every line whether a hiring manager would care; cut what any peer would have done.

## 5. The sanitisation gate

Run it on every new or changed line before a record leaves an employer's systems. The record's *Handling notes* hold the owner's own answers (which names are already cleared, what the agreement with the employer says), so read them first, and ask once when they are silent.

- [ ] **Clients and counterparties:** named only where the handling notes clear the name; otherwise described by kind and scale ("a sovereign-wealth client").
- [ ] **Third parties:** no names of suppliers, partners, funds, properties, sites or addresses.
- [ ] **Client and company financials:** no balances, valuations, prices, rents, loan amounts or internal results. Figures the organisation has published are fine.
- [ ] **Operational metrics:** aggregates only (counts, percentages, durations), and nothing that picks out one customer, supplier or asset.
- [ ] **Internal identifiers:** no links, file paths, ticket keys, channel names or document ids.
- [ ] **Work product:** no code, queries, schema or table names, rule text, mapping tables, prompts or screenshots. Describe it instead: "wrote 40 validation rules covering trial balance and rent roll tie-outs".
- [ ] **People:** no colleague's name unless the handling notes clear it, and nothing personal about anyone.
- [ ] **Company confidential:** nothing on unreleased products, plans, pricing, contract terms, headcount or deals.
- [ ] **Credentials:** no tokens, keys or passwords.

A point that fails is made general. One that cannot be is dropped, and listed for the owner as withheld, with the reason.

## 6. How often

- **On the first day or week:** the role snapshot, the organisation context and the mandate as contracted. They are easiest to get then, and the mandate is what later bullets are read against.
- **Every month or quarter,** and whenever something ships: steps 1 to 7 for the period since the last update.
- **Before leaving a role:** a last full pass while the sources can still be reached. After the last day most of them cannot.

The checker's stale warning (spec §3.6) is the late signal that a record has not been touched.

## 7. From a record to CV bullets

A record is long and grouped by kind of work. A CV needs its best lines. Where the owner wants them ready, derive a bullets file beside the record, in two sections that are both always kept:

```markdown
## HAM-Z bullets
- <every bullet tagged hamz, tightened: number first, one sentence>

## Supporting points
- <bullets tagged supporting that a recruiter would still want>
```

Nothing enters it that is not in the record, and it is checked against the record the way step 6 checks the record against its sources. For a job advert, match these bullets through the graph (`query_graph.py support`) at the right disclosure, as *Working with an existing graph* says.
