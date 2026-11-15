# Experience update: a prompt for the machine where the work is

For an owner whose evidence of a job sits on an employer's machine or accounts. The competency graph lives somewhere else and must not reach in there. Paste everything **below the line** into Claude *on the work machine*. It installs a small skill, `experience-update`, that rebuilds the record of one role from the work that role left behind, checks it, strips anything confidential, and prints one complete file to carry back. The method is `references/recording-experience.md`; this is the same method, made to stand on its own.

Before the first run, check that the employer's rules allow an AI assistant to read the sources on that machine, and connect only the ones they allow.

---

I want you to create a reusable skill called `experience-update`. Don't run it yet. Just install it and confirm.

Where to put it:
- If you're Claude Code, save it as `~/.claude/skills/experience-update/SKILL.md`.
- If you can't write to a skills directory (for example in claude.ai), output the SKILL.md in a code block so I can upload it as a skill myself.

Write the SKILL.md exactly as below. Fix anything that doesn't work in this environment, such as a tool name, and tell me what you changed.

````markdown
---
name: experience-update
description: Rebuild the owner's record of one job, engagement or project (their experience file for that role) from evidence of delivered work found on this machine, written to the HAM-Z standard, then output a complete, sanitized replacement file. Use when the owner says "update my experience file", "experience update", "record my work at <organisation>", or pastes or attaches an experience record and asks to bring it up to date. Run with --newbuild to start a record for a role that has none.
---

# Experience update

## Purpose

The owner keeps one record for each role, on their own machine, where it is the evidence behind their CV and their competency graph. The evidence for this role's work is on this machine, so this skill gathers it here and writes the record here. The record then leaves for the owner's machine, so it must be clean before it does.

Every step follows two rules:
1. **Write only what was delivered.** Don't restate the job description, and don't estimate a number.
2. **Nothing confidential leaves these systems.** The record says what the owner did. It never includes the work product itself.

## Inputs

1. **The current record.** The owner attaches or pastes it. If it isn't there, ask for it and stop, unless the run is `--newbuild`. Never rebuild a record from memory or from this skill: the file is the base, and every part you aren't explicitly allowed to change (Step 4) comes through as it is.
2. **The period.** From the record's `lastUpdated` to today, by the system clock. Say so in one line and carry on unless the owner changes it. A new build covers the whole role.
3. **The handling notes.** The record's *Handling notes* section says what may be named: the employer, clients, the owner's manager, and what the owner's agreement with the employer says about work product. If the section is missing or silent on one of these, ask once, and write the answers into it.
4. **Evidence.** Whatever sources this environment can reach (Step 2).

### A new build (`--newbuild`)

There is no record yet. Create one with this shape, filling the front matter, *Role snapshot*, *Organisation context* and *Mandate as contracted* from the owner's offer or role description and their answers, then continue at Step 2 for the whole role. Keep any front-matter keys the owner asks for.

```markdown
---
title: "<role title>"
organization: "<employer, or for an engagement the client>"
tenure: <YYYY-MM-DD> – present
status: current
lastUpdated: <YYYY-MM-DD>
keywords: []
---

# <Organisation>: <role title>

> <N weeks or months> in. Bullets record delivered work only. Work that is scoped, drafted or scheduled but not delivered stays under "In progress (not yet delivered)" until it ships.

## Role snapshot
- **Title:** · **Reports to:** · **Scope:** · **Team:**

## Organisation context
<two or three sentences, from public information: what the organisation does and where this role sits>

## Mandate as contracted
<what the role was hired to do, from the role description: the contract, not a record of performance>

## Responsibilities & impact
### <a kind of work>
- <bullets, HAM-Z where the evidence allows> <!-- src: <kind of source>, <Mon YYYY>; verified|self-reported; hamz|supporting -->

### In progress (not yet delivered)

## Systems & tooling

## Recognition & thought leadership

## Evidence & artefacts
### Work-side evidence (held on the employer's systems, not copied)

## Handling notes
- Who may be named: <employer / clients / manager>
- What the agreement with the employer says about work product and confidentiality:
```

## Step 1: Inventory the current record

Parse the file and note:
- `lastUpdated`, `keywords` and any other list the front matter keeps
- the status line at the top
- every subsection and bullet under "Responsibilities & impact", so you don't add a duplicate
- the handling notes

## Step 2: Gather evidence (read-only)

Check which tools and connectors are available. Search every available one for the period. Afterwards, tell the owner which sources you checked and which aren't connected. Typical sources:

- **Calendar:** client cadences, steering meetings, calls the owner ran, presentations they gave
- **Email and chat:** what the owner *sent*: deliverables, resolved escalations, rollout announcements; and thanks or recognition they received
- **Documents and wikis:** what the owner wrote or owns: runbooks, specifications, reports, guides, training material
- **Tickets:** issues closed, exceptions decided, cycle times
- **Platforms and dashboards:** **aggregates only**: counts, rates, volumes, coverage. Prefer an existing dashboard to a new query, and never run a heavy query against production
- **Repositories, if any:** tools or automations the owner built

Strictly read-only: don't send, post, edit or comment on anything.

Build an **evidence ledger** in the conversation. It never goes in the output file.

| # | Candidate achievement | Source (kind and month, no links) | Metric | Baseline | Period | Confidence |
|---|---|---|---|---|---|---|

Confidence is one of: `verified` (seen in a source), `self-reported` (the owner stated it), or `missing`.

## Step 3: Interview the owner

Show the ledger. Then ask in **one batch** (eight questions at most), aimed at the gaps:
- a metric or baseline that is missing ("What was the on-time rate before you took over the cycle?")
- the owner's own part in shared work: what they led, what they co-designed, what they supported
- anything delivered that left no trace in the sources
- recognition: thanks from a client, a talk given, something others took up
- what is in flight and not yet delivered

Don't ask for what a source already answered. A number the owner gives from memory is `self-reported`.

## Step 4: Write the updated record

### What you may change
- **`lastUpdated`:** today's date from the system clock, `YYYY-MM-DD`.
- **`keywords` and similar lists:** you may only add.
- **The status line:** the time in role ("one week in" becomes "seven weeks in"). Keep its rule against promoting undelivered work.
- **Role snapshot:** only where a fact has changed (title, manager, scope, team). Pay only if the owner says it changed.
- **Responsibilities & impact:** add subsections and bullets, or update existing ones. Head each subsection with the kind of work.
- **Systems & tooling:** tools the owner actually used.
- **Recognition & thought leadership:** only what happened: talks, presentations, written pieces, thanks received. Something planned is labelled a candidate.
- **Evidence & artefacts:** a sub-list headed `Work-side evidence (held on the employer's systems, not copied)` that describes each item generically, for example "Q4 service-health deck to the client's finance team (Oct 2026)". No links, file paths or document ids.
- **Handling notes:** only to record the owner's answers from Inputs, item 3.

### What you must not touch
`title`, `organization`, `tenure` and any front-matter key not named above; "Organisation context"; "Mandate as contracted" (it is the contract, not a record of performance); and any path or link the record already holds. Those point to the owner's own machine and won't exist here. That is expected: leave them.

### The bullet standard: HAM-Z

A bullet meets HAM-Z when it has all four parts:

| Part | What it is | Test |
|---|---|---|
| **H** Hard skill or tool | A named tool, system, framework, standard, statute or technical method | Could a reader look it up? |
| **A** Action | A concrete verb for what the owner did: built, cut, led, mapped, negotiated, onboarded | Does it say how much of it was theirs? |
| **M** Metric | A number from a source, with its baseline and period where they exist | "Improved on-time delivery" fails. "From 62% to 91% on time across two quarters" passes |
| **Z** Process | The mechanism: how the result came about | Would the line still be true of someone who did it another way? Then it is too vague |

> **[Result: action and metric] by [process], using [hard skill or tool].**
> *Cut average lease cycle time by 50% by leading the company-wide roll-out of the VTS leasing platform, moving the whole deal pipeline online from offer to signing.*

**The metric is the gate.** With no number from a source, a bullet is not HAM-Z, and you never make a number up to get it through. If a reader would still care, keep it as a *supporting point*. End every new or changed bullet with a tag that says where it came from, how sure it is, and which kind it is:

`<!-- src: <kind of source>, <Mon YYYY>; verified|self-reported; hamz|supporting -->`

Rules:
- Lead with the number, then "by" and the mechanism, in one dense sentence.
- Past tense for finished work, present tense for a standing duty.
- If you can't fill a part honestly, leave it out. Never pad.
- If a bullet could have been written before the owner started, delete it.
- Say who did the work: "Led…", "Co-designed with the team…", "Owned…", "Contributed to…". A team's or an organisation's result is a contribution, not the owner's alone.
- A projection is written as a projection, never as a result.
- Keep scope exact: the part of the programme the owner had, not the whole.
- Name no tool or framework that no source names.
- Work in flight goes under `### In progress (not yet delivered)`, never among the achievements.
- On a re-run, a newer number **replaces** the older one in the same bullet. A supporting point whose number has turned up becomes a HAM-Z bullet.
- Plain words. No "spearheaded", "leveraged", "drove transformation", "synergies" or "robust". Match the voice and spelling the record already has.

## Step 5: Fact-check

Before the gate, read every new or changed bullet against the ledger as a sceptic who did not write it, and mark each:
- **Supported:** every number, tool, scope and claim traces to a source or to the owner's own answer.
- **Unverifiable:** not found. Ask the owner, or drop it.
- **Contradicted:** conflicts with a source. Fix it or drop it.

Look for: an invented number, a scope made larger, a projection stated as a result, a team result claimed alone, a tool no source names.

## Step 6: Sanitization gate (required before output)

This file moves from the employer's systems to a personal machine. Read the handling notes, then check every new or changed line:

- [ ] **Clients and counterparties:** named only where the handling notes clear the name. Otherwise by kind and scale ("a sovereign-wealth client").
- [ ] **Third parties:** no names of suppliers, partners, funds, properties, sites or addresses.
- [ ] **Client and company financials:** no balances, valuations, prices, rents, loan amounts or internal results. Figures the organisation has published are fine.
- [ ] **Operational metrics:** aggregates only (counts, percentages, durations). Nothing that picks out one customer, supplier or asset.
- [ ] **Internal identifiers:** no links, file paths, ticket keys, channel names or document ids.
- [ ] **Work product:** no code, queries, schema or table names, rule text, mapping tables, prompts or screenshots. Describe them instead, e.g. "wrote 40 validation rules covering trial balance and rent roll tie-outs".
- [ ] **People:** no colleague's name unless the handling notes clear it. Nothing personal about anyone.
- [ ] **Company confidential:** nothing on unreleased products, plans, pricing, contract terms, internal financials, headcount or deals.
- [ ] **Credentials:** no tokens, keys or passwords of any kind.

If a useful point fails the gate, make it general. If it can't be made general, drop it and list it under "Withheld" in the change summary.

## Step 7: Output

1. If you can write files, save the result under the record's own file name in a folder the owner chooses (default: the current directory) and give them the path.
2. Always also print the **entire file** in the chat inside one fenced block opened with four backticks and `markdown`, so code fences inside the file survive. Print the full file, never a diff or an excerpt: the owner replaces their copy whole.
3. After the block, add a short **change summary** that is not part of the file:
   - sections changed, and bullets added or updated (counts), HAM-Z and supporting
   - bullets that rest on a `self-reported` metric
   - anything withheld at the gate, and why
   - sources checked and sources not available
   - **for the competency graph:** the named tools, methods and standards that are new to the record (the H parts), and the bullets where the owner led the work, so the owner's own session can propose the links
   - open questions, or metrics to collect before the next run
````
