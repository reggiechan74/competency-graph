---
title: CX and Managed Data Services Framework
date: 2026-11-10
keywords: [customer-experience, managed-data-services, competency-framework, data-operations, customer-success, data-quality, knowledge-graph]
lastUpdated: 2026-11-14
author: Reggie Chan
documentType: framework
version: 2026.3
status: draft
---

# Customer Experience and Managed Data Services Framework (Chan CXMDS 2026.3)

*Reggie Chan, November 2026.* A competency framework for the people who run managed data services for enterprise clients. In such a service a data company collects the data that a client's third parties hold, maps it to a standard model, checks it and delivers it. It also keeps both the client and those third parties well served while it does. The work sits between customer success, professional services and data operations, and no single body covers it. CXPA's CCXP covers customer-experience strategy, customer success certifications cover the account relationship, ITIL 4 covers service management and DAMA-DMBOK covers data management. None joins them, and none covers the third-party data providers who make or break the service. Real estate is the worked sector. The competencies are written for any data-services company that serves enterprise clients, such as a data platform, a fund administrator's data team or a SaaS onboarding team. They have been tested against outside role postings (see Outside role check) but not yet reviewed by outside practitioners.

Three terms, as used here. **Managed data services (MDS):** the provider runs a data process for the client as an ongoing service, in addition to licensing software. It onboards the client's data providers, collects and maps their data, validates it, follows up what is late or wrong, and delivers it. Data comes in three ways, and many services use all three: providers submit to templates or a portal; systems send automated feeds (custodians, banks, accounting systems); or the service collects documents (statements, notices, valuations) and extracts the data from them. A new client usually also brings history, which is converted and loaded once. **Data providers:** the third parties who hold the data and release it to the service on the client's behalf (in real estate: property managers, operators and fund administrators; in wealth and fund services: custodians, banks and fund administrators). They are often not the provider's customers at all. **Customer experience (CX):** the experience of the client, the client's own users and the data providers with the service.

**Scope.** The framework covers two job families: customer success and account delivery (Tier A) and data operations (Tier B). The managed data services lead is the role that bridges them. CX in the sense of the CXPA's CCXP (customer insight, journey design, CX strategy and CX culture) is a small part: A7 and, in part, A6.3. Enterprise CX strategy and CX culture are out of scope. Most of the client-facing content is customer success and service management.

## Structure

- **Tier A, customer success and account delivery (8 domains, 27 competencies):** the client- and provider-facing work: relationships and governance, contracts, scope and retention, onboarding and implementation, provider management, support, service levels, customer experience, and team and service operations.
- **Tier B, managed data services and data operations (8 domains, 27 competencies):** the data work the service rests on: domain knowledge, modelling, onboarding and mapping, quality, operations and incidents, platform and delivery, governance, security and lineage, and automation and AI. Each Tier B domain backs a Tier A promise: validation and reconciliation make service levels credible, gap analysis and mapping make onboarding fast, and access governance and lineage satisfy the client's risk, finance and audit teams.
- **One pathway, Managed data services professional,** puts every competency in exactly one of three groups: **Mandatory** (7, required of everyone at a fixed level), **Core** (16, required of everyone at L2) and **Optional** (31, of which a person takes six: three to L3 and three to L2). The Optional competencies are listed in three sub-groups, one for each specialisation: Client delivery and customer experience, Data operations and quality, and Solutions and onboarding. See "The pathway".

Levels use the competency graph's scale: **L1 Aware** (knows it, has not delivered it), **L2 Practitioner** (delivers it independently), **L3 Advanced** (handles complex cases, is accountable for the result, guides others), **L4 Expert** (a recognised authority beyond their own team). Roughly SFIA 1–2, 3, 4–5 and 5–6. Every L3 needs evidence of guiding others (reviewing their work, coaching them, or setting a method they follow), whether or not the row names it. A delivered design that matches an L3 row without that evidence rates L2. Every L4 descriptor asks for recognition beyond one account: a standard that other teams or accounts adopt, published work, teaching beyond the person's own team, or an external credential. Where another function owns a policy (security, legal, pricing, product), the L4 descriptor says the person contributes to it.

Real-estate examples appear in brackets ("in real estate: …"). In another sector, read them as that sector's equivalents: policies and claims in insurance, loans and collateral in lending, funds and investors in fund administration, sites and assets in infrastructure.

### Where neighbouring competencies meet

Each pair below shares a boundary. Evidence belongs under one of them only.

- **A1.2 Account governance and cadence** is the standing governance of the account (cadence, steering, decision rights, decision log). **A3.4 Implementation project management** is the plan of one implementation (tasks, dependencies, critical path, RAID log, effort budget).
- **A2.2 Scope and change control** is the one home of scope decisions. **A3.2 Discovery and requirements** and **B3.1 Source data profiling and gap analysis** supply the findings that scope decisions rest on.
- **A2.3 Renewal, expansion and commercial awareness** is the commercial conversation. **A2.4 Account health and retention** is spotting and acting on the risk of losing the client. **A8.4 Service economics and cost to serve** is what the service costs to run.
- **A3.1 Onboarding programme design** is the method used across onboardings. **A3.4 Implementation project management** is the plan and control of one of them.
- **A4.3 Submission compliance and follow-up** is the provider relationship (obligations, chasing, scorecards, remedies). **B5.1 Submission cycle operations** is the calendar and the running of the cycle.
- **A5.1 Request and issue handling** is questions and requests. **A5.2 Escalation management** is decisions on escalated issues of any kind. **B5.4 Data incident, correction and restatement management** is the handling of wrong data that has reached the client.
- **A5.3 Root cause and problem management** is recurring service problems (process, hand-offs, tooling, provider behaviour). **B4.2 Reconciliation and financial tie-outs** is numerical breaks between figures.
- **A6.1 Service level management** is the contractual service levels. **A6.2 Service performance reporting** is operational and data-quality measures.
- **A2.4 Account health and retention** owns the account's health score and retention risk. **A6.2 Service performance reporting** measures how the service performs (timeliness, data quality, open issues); its measures can feed the health score.
- **A3.4 Implementation project management** holds effort against the implementation plan. **A8.4 Service economics and cost to serve** holds effort against the running service.
- **A3.1 Onboarding programme design** covers training and adoption by the client's own users. **A4.2 Provider enablement and training** covers the data providers.
- **A4.2 Provider enablement and training** answers provider how-to questions that need training material or a guide. **A5.1 Request and issue handling** answers the rest.
- **A4.1 Provider engagement** obtains the authorisations and consents a provider needs before it releases data. **B7.3 Confidentiality, privacy and compliance** sets the legal and contractual limits on what is done with the data once it arrives.
- **A5.3 Root cause and problem management** reviews recurring service problems. The review of a data incident belongs to **B5.4 Data incident, correction and restatement management**.
- **B3.3 Data ingestion and transformation** is every intake channel (templates and portals, feeds, document extraction) and the one-off conversion of history. **B8.2 AI-assisted data processing** is the model-judgement steps inside it.
- **B4.2 Reconciliation and financial tie-outs** explains a break. **B7.4 Data lineage and traceability** builds the trace that makes it explainable.
- **B2.3 Business definitions and data dictionaries** is what a term means. **B7.4 Data lineage and traceability** is where a figure came from.
- **B4.1 Validation rules and data quality checks** checks data as it arrives. **B4.3 Exception triage and remediation** handles the exceptions the checks raise.
- **B8.1 Scripting and workflow automation** is automation without model judgement. **B8.2 AI-assisted data processing** applies AI to the data. **B8.3 AI-assisted service delivery** applies AI to client and provider service work.

## Tier A: customer success and account delivery

### A1. Client relationship and account governance

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A1.1 Stakeholder relationship management** (sponsors, stakeholder maps, RACI) | Knows who the client's sponsors, users and decision-makers are, and why their interests differ | Keeps working relationships with client contacts across functions; knows who decides what; keeps commitments | Keeps a stakeholder map across client, data providers and internal teams; resolves conflicting interests; holds sponsor-level relationships through changes of people or direction | Holds executive sponsor relationships on several enterprise accounts; other account teams adopt their stakeholder method, or they teach it beyond their own team |
| **A1.2 Account governance and cadence** (status meetings, steering committee, decision log, action log) | Knows the purpose of status meetings, steering committees and decision logs | Runs the account's meetings with agendas, minutes and actions; keeps the decision and action logs current | Sets the governance of a complex account: steering, escalation paths and decision rights; keeps decisions moving when priorities or people change | Designs a governance model that other managed-service accounts in the organisation adopt as their standard |
| **A1.3 Client communication and presentation** (status reports, pre-reads, executive briefings) | Knows what a status update, a pre-read and an executive briefing each contain, and who reads them | Writes pre-reads and status updates and presents work to client teams; adjusts the detail to the audience | Presents complex or contested matters to senior client stakeholders and gets decisions; delivers bad news with options | Sets client communication standards that other teams adopt, or presents the service's practice in published work or at industry events |
| **A1.4 Account planning and success plans** (success criteria, account plan, business reviews) | Knows what an account plan and a success plan contain | Keeps an account plan with the client's goals, success measures and milestones; runs periodic business reviews | Builds multi-year account plans tied to the client's business outcomes; aligns internal teams to them; revises them when the client's goals change | Their account-planning method is the standard other account managers use across a portfolio, or they teach it beyond their own team |

### A2. Contract, scope and commercial management

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A2.1 Contract and statement-of-work interpretation** (obligations, deliverables, acceptance criteria) | Knows the parts of a master agreement, an order form and a statement of work | Reads a statement of work and lists its deliverables, deadlines and acceptance criteria; traces work to clauses | Interprets contracts made of several instruments; advises on obligations, acceptance and risk; spots conflicts between documents | Contributes service terms to the organisation's contract templates, which legal owns; other account teams use their obligation and acceptance checklists |
| **A2.2 Scope and change control** (scope baseline, change requests, scope creep) | Knows what is in and out of scope and why change control exists | Raises change requests with effort and impact; keeps a change log | Turns discovery and gap-analysis findings into agreed scope; negotiates trade-offs with the client; protects margin and the relationship together | Their change-control method is adopted across a services portfolio; contributes to how change is priced, which the commercial team owns |
| **A2.3 Renewal, expansion and commercial awareness** (renewal, expansion, account economics) | Knows how the account earns revenue and when it renews | Spots expansion opportunities and builds the evidence for renewal with whoever owns the commercial relationship | Leads renewal and expansion conversations on delivered value; forecasts account revenue | Contributes to the commercial model of the managed-service line (packaging, outcome-based terms), which the commercial team owns; other account teams use their renewal approach |
| **A2.4 Account health and retention** (health scores, risk signals, churn analysis, save plans) | Knows the common signs that a client is at risk: falling use, unresolved issues, a change of sponsor, missed outcomes | Tracks the account's health signals; raises retention risks early with evidence and a proposed response | Designs the health measures for an account or segment and checks them against actual renewals and losses; runs save plans; feeds lessons from lost or shrinking accounts back to delivery and product | Their health and retention model is adopted across the organisation's accounts, or they publish or teach on retention in data services |

### A3. Client and provider onboarding

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A3.1 Onboarding programme design** (onboarding playbook, stages, entry and exit criteria, client-user training and adoption, time to value) | Knows the stages of onboarding a client, its users or a data provider, and what time to value and adoption mean | Runs an onboarding to a written playbook with stages, owners and exit criteria; trains the client's users and checks that they use the service | Designs the onboarding programme for an account with many providers or users: sequence, entry and exit criteria, user training, and time-to-value and adoption measures; acts when adoption lags; changes the programme from what earlier onboardings showed | Their onboarding method is adopted by other accounts in the organisation and measured across them |
| **A3.2 Discovery and requirements** (discovery sessions, current-state assessment, requirements) | Knows the purpose of discovery and the questions to ask | Runs discovery sessions and records requirements, sources and constraints clearly | Leads discovery across many parties; turns unclear needs into prioritised, testable requirements; challenges requirements whose cost exceeds their value | Their discovery method and templates are adopted across the organisation, or they teach it beyond their own team |
| **A3.3 Implementation and go-live** (cutover, parallel run, user acceptance, hypercare, hand-over to run state) | Knows cutover, parallel runs, acceptance testing and hypercare | Takes a provider or client to go-live with a test, a parallel run against the prior system or provider, a sign-off and a hypercare period | Leads go-lives with many parties and hard dates; decides go or no-go on evidence; manages rollback; hands the account over to the run-state service against agreed exit criteria | Their readiness gates and go-live standards are adopted across the organisation |
| **A3.4 Implementation project management** (project plan, dependencies, critical path, RAID log of risks, assumptions, issues and dependencies, effort budget) | Knows what a project plan, a dependency, a critical path and a RAID log are | Keeps an implementation plan with tasks, owners, dependencies and dates; keeps the RAID log current; reports progress against the plan | Plans and controls implementations with many parties and dependencies; manages the critical path and the effort budget; replans with the client when dates or scope move | Sets the implementation-planning standard that other teams use, or teaches implementation planning beyond their own team |

### A4. Data provider management

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A4.1 Provider engagement** (data providers and data vendors, data-feed authorisations and consents; in real estate: property managers, operators, fund administrators) | Knows who the data providers are, what the client asks of them, and what authorisation each needs before it releases data | Is the working contact for a group of providers; obtains the authorisations and consents they need to release data (for example, letters of authorisation); keeps them informed and responsive | Handles escalations from providers and keeps reluctant providers engaged; when the client and a provider read an obligation differently, brings them to an agreed reading; coaches colleagues on difficult providers | Shapes how a sector's data providers work with data services, through industry groups, provider councils or published guidance |
| **A4.2 Provider enablement and training** (submission guides, templates, training sessions, self-service help) | Knows the templates and guides providers use | Writes provider guides and runs training sessions; answers how-to questions | Designs the provider enablement programme (guides, training, office hours, self-service help) and measures its effect on submission quality | Their enablement materials or programme are adopted across accounts or by a sector body, or they teach provider enablement beyond their own team |
| **A4.3 Submission compliance and follow-up** (provider obligations, chasing, scorecards, remedies) | Knows what each provider must submit and the consequences of late or poor submissions | Follows up late and incomplete submissions with providers; records the reasons | Runs provider scorecards and escalation for repeated non-compliance; agrees remedies with the client | Their provider compliance regime is adopted across accounts in the organisation |

### A5. Support, escalation and problem management

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A5.1 Request and issue handling** (service desk, ticket triage, response targets) | Knows how requests are logged, prioritised and closed | Logs, triages and resolves client and provider requests within targets, in a ticketing or work-management tool | Runs the support queue for an account; sets priorities and response targets; finds patterns in requests and removes their cause | Their support model (tiers, channels, self-service) is adopted across the organisation |
| **A5.2 Escalation management** (escalation paths, delegated authority, escalation communication) | Knows the escalation path and when to use it | Escalates issues with facts, options and an owner; tracks them to closure | Decides escalations within delegated authority, with options and trade-offs; keeps the client informed on time; reviews escalations afterwards and fixes the path | Their escalation and major-issue process is adopted across the organisation |
| **A5.3 Root cause and problem management** (root cause analysis, post-incident review, recurring service problems) | Knows the difference between fixing an incident and removing its cause | Traces a recurring service problem to its cause in process, hand-offs, tooling or provider behaviour, and removes it | Runs problem management for an account: trends, root causes, post-incident reviews and preventive fixes | Their problem-management practice is adopted across the organisation |

### A6. Service levels and performance reporting

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A6.1 Service level management** (SLAs, OLAs, service credits) | Knows what SLAs, operational level agreements (OLAs) and service credits are | Measures delivery against the agreed service levels; reports breaches with their causes; applies service credits where due | Defines service levels with the client and internal teams; manages to them; negotiates changes | Their service-level framework is used across the organisation's managed-service offers |
| **A6.2 Service performance reporting** (operational scorecards, submission timeliness, data quality measures, trends) | Knows the service's key operational measures (on-time submission, data quality, open issues) | Produces regular performance reports from tracked data, with trends and commentary | Designs the scorecard for an account or service and uses it to drive action; makes sure each measure is defined, sourced and comparable over time | Their scorecard and benchmarks are adopted across accounts, or published |
| **A6.3 Value realisation and outcome measurement** (time to value, ROI, business outcomes) | Knows the client's reasons for buying the service | Records the outcomes the service delivered (time saved, coverage, accuracy) and shows them to the client | Measures value against the client's business case; links data quality to the client's decisions and reports | Their value-measurement method is used across the organisation's offers, or published |

### A7. Customer experience

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A7.1 Customer insight and feedback** (voice of the customer, CSAT, NPS, customer effort) | Knows the main feedback measures (CSAT, NPS, customer effort) and their limits | Collects and acts on client and provider feedback; closes the loop with the person who gave it | Runs a voice-of-the-customer programme for an account or service; combines survey, interview and operational data; turns findings into changes owned by named teams | Leads customer insight across the organisation; other teams adopt its methods, or they publish or teach on it |
| **A7.2 Journey mapping and experience design** (client and provider journeys, friction, effort) | Knows what a journey map shows | Maps a client or provider journey and fixes friction points in it | Redesigns journeys across touchpoints to cut provider effort and client waiting; measures the change | Sets the experience-design standards that other teams adopt for client and provider journeys; contributes to the organisation's customer-experience strategy |

### A8. Team leadership and service operations

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A8.1 Team leadership and coaching** (onboarding staff, coaching, performance) | Knows the team's roles and how work is assigned | Onboards and coaches a team member; reviews their work and gives feedback | Leads a delivery team; sets goals, develops people and manages performance | Develops leaders: builds career paths or a development programme adopted beyond their own team |
| **A8.2 Workload planning and prioritisation** (capacity, task registers, resourcing) | Knows how the team's work is tracked and prioritised | Plans the team's work in a shared register; sets priorities against deadlines | Plans capacity across accounts and cycles; makes trade-offs visible to management | Their capacity-planning model is used across the service line |
| **A8.3 Continuous improvement and standardisation** (process mapping, lean, reuse across accounts) | Knows basic process mapping and improvement methods | Improves a process in their own area and records the new way of working | Leads improvement across an account; turns one-off solutions into standard ones that other accounts use | Runs an improvement programme whose methods other service lines adopt, or holds a Master Black Belt, or a Black Belt and teaches improvement beyond their own team |
| **A8.4 Service economics and cost to serve** (effort tracking, utilisation, cost to serve, service margin) | Knows that the service has a cost to serve and what drives it: effort per provider, rework, exceptions | Records effort against the account and its activities; spots work that costs more than planned | Models the cost to serve an account; finds and cuts its main cost drivers; compares delivery options (in-house, offshore, automated) on cost and quality; reports service margin to management | Their cost-to-serve model is used across the service line to price and plan, with finance owning the figures |

## Tier B: managed data services and data operations

### B1. Data domain knowledge

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B1.1 Financial and accounting data** (general ledger, trial balance, financial statements; in real estate: NOI) | Knows the general ledger, the trial balance and the main financial statements | Reads and checks financial submissions; knows how accounts roll up to statements and to the sector's key measures (in real estate: NOI) | Works across the ledgers and statements of many entities; resolves classification and sign issues; advises client finance teams | A recognised authority on financial data in the sector, shown by published work, teaching or standards work; a CPA or CFA supports but does not by itself show L4 |
| **B1.2 Sector data and terminology** (in real estate: property, unit, lease, rent roll, operating statement) | Knows the main data objects and terms of the client's sector (in real estate: property, unit, lease, tenant, rent roll, operating statement) | Uses sector terms correctly in mapping, validation and client conversations | Works across several sub-sectors (in real estate: office, residential, hospitality, industrial, funds and debt); resolves sector-specific definitions and edge cases | Recognised in the sector for its data: contributes to sector standards, publishes or teaches |
| **B1.3 Industry data standards** (in real estate: OSCRE, RESO, NCREIF PREA; across sectors: AICPA Audit Data Standards, XBRL) | Knows which data standards exist for the sector and what each covers | Applies a standard in a mapping, model or template | Chooses and adapts standards for a client's model; explains the trade-offs of following or departing from them | Contributes to the development of a published standard |

### B2. Data modelling and standardisation

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B2.1 Target data models** (canonical model, target tables, grain, keys) | Knows entities, attributes, keys and grain | Reads the service's target model and places client data in it correctly | Designs target tables and extensions for a client's needs; sets grain, keys and constraints | Owns a canonical data model that other teams build on across clients |
| **B2.2 Reference data and chart-of-accounts design** (taxonomies, code lists, charts of accounts) | Knows what reference data, code lists and a chart of accounts are | Maintains reference lists and a chart of accounts; adds codes under change control | Designs a reference taxonomy or chart of accounts that many sources map to; tests its coverage against real source data; runs a versioned change process that the client and other teams follow | Their reference-data standards are used across clients or adopted by a sector body |
| **B2.3 Business definitions and data dictionaries** (business glossary, operational definitions, metadata) | Knows why shared definitions matter | Writes clear field and term definitions in a data dictionary | Resolves conflicting definitions across client, providers and internal teams; owns the glossary and gets definitions adopted | Their glossary and metadata practice is adopted across the organisation |

### B3. Data onboarding, mapping and integration

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B3.1 Source data profiling and gap analysis** (field inventory, completeness, required-field lists) | Knows how to profile a source (fields, completeness, formats, values) | Profiles a provider's data and lists the gaps against the target | Runs gap analyses across many providers or source systems; classifies each gap by how it will be closed, with the effort; presents the findings for the scope decision; reviews others' profiles | Their profiling and gap-analysis method is adopted across the organisation |
| **B3.2 Source-to-target mapping** (field mapping, account mapping, transformation rules) | Knows what a mapping specification contains | Writes and tests field and account mappings from a provider's source to the target | Maps complex sources at scale; handles many-to-many, sign and period issues; reviews others' mappings | Their mapping standards and reusable mapping libraries are used across clients |
| **B3.3 Data ingestion and transformation** (ETL/ELT, file formats, APIs and automated feeds, submission templates and portals, document collection and extraction, historical conversion and backfill) | Knows ETL and ELT, common file formats, API and system feeds, and extraction from documents | Configures or builds an ingestion with transformations and load checks; loads a new client's history and checks it against the prior system or provider | Designs ingestion for many providers on different systems, formats and intake channels, including documents; plans historical conversion and backfill; handles late, partial and resubmitted data | Their ingestion patterns are the standard that other teams build on |
| **B3.4 Entity resolution and master data** (matching, entity hierarchies, identifier crosswalks) | Knows why the same property, entity or party appears under different names and IDs | Matches records to master entities and maintains identifier crosswalks | Designs entity hierarchies and matching rules; resolves conflicts between sources; reviews others' matches | Owns a master-data approach used across clients |

### B4. Data quality and validation

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B4.1 Validation rules and data quality checks** (completeness, accuracy, timeliness, consistency) | Knows the data quality dimensions and what a validation rule is | Writes and runs validation rules on submissions; documents what each rule checks | Designs the validation rule set for an account; sets thresholds by risk; tunes rules to cut false alarms | Their data quality framework is adopted across clients, or they publish or teach on data quality |
| **B4.2 Reconciliation and financial tie-outs** (control totals, roll-forwards, cross-checks) | Knows what a reconciliation proves | Reconciles submitted data to source totals and statements; explains the breaks | Designs the reconciliation controls for an account's data; traces breaks to their cause across sources and periods; reviews others' reconciliations | Their reconciliation standards are adopted across the service line |
| **B4.3 Exception triage and remediation** (exception queues, issue logs, triage criteria) | Knows how exceptions are raised and logged | Triages exceptions, fixes what is internal, and sends providers clear, documented issues | Runs an exception review with documented triage criteria and escalation thresholds; decides what goes to providers or the client; reviews others' triage | Their exception-management model is adopted across accounts |

### B5. Data operations

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B5.1 Submission cycle operations** (cycle calendars, cut-offs, close-out, cycle time) | Knows the submission calendar and the steps in a cycle | Runs a reporting cycle to the calendar and closes it out | Runs cycles across many providers; keeps them on time when inputs are late; shortens cycle time | Their cycle operating model is adopted across clients |
| **B5.2 Pipeline monitoring and data observability** (DataOps, freshness, volume, schema, alerts, data contracts) | Knows the signs of a failed or stale feed (freshness, volume, schema) | Monitors feeds and loads; acts on alerts and failed jobs | Sets monitoring and alert thresholds; agrees data contracts with providers; cuts the time to detect and fix | Their observability standards are adopted across the platform |
| **B5.3 Standard operating procedures and runbooks** (SOPs, playbooks, work instructions) | Knows where the procedures are and what a good one contains | Writes clear step-by-step procedures and runbooks that others can follow | Owns the procedure set for an account or service; keeps it current and makes it the basis for training and audit | Their procedure standards are adopted across the service line |
| **B5.4 Data incident, correction and restatement management** (wrong data delivered, corrections, prior-period restatements, notice to data users) | Knows what a data incident is and why corrections to delivered data must be traced and notified | Corrects wrong data delivered to a client; records what changed and why; tells the people who use it | Runs data incidents for an account: assesses the impact on delivered reports, decides between correction and restatement, coordinates providers and client, and closes with a review | Their data-incident and restatement process is adopted across the organisation |

### B6. Platform, solutions and data delivery

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B6.1 Platform configuration and product knowledge** (templates, rules, users, workflows) | Knows what the service's platform does and its main modules | Configures the platform for a client or provider (templates, rules, users) to a runbook | Knows the platform's limits; configures complex cases and workarounds; trains others | Recognised as the platform expert across the organisation: trains other teams and clients, or contributes to the product's design; the vendor's highest certification supports but does not by itself show L4 |
| **B6.2 Data delivery, reporting and analytics** (SQL, BI dashboards, data feeds to client systems) | Knows how clients receive and use the data (files, feeds, dashboards) | Queries the data with SQL and builds reports or feeds for client use | Designs the delivery layer for an account (feeds, dashboards, downstream analytics) around the client's decisions | Their data products and delivery patterns are offered across clients |
| **B6.3 Solution design and product feedback** (solution options, product requirements) | Knows what the product does out of the box and where services fill the gaps | Proposes solution options for a client need; writes clear feature requests | Designs solutions across product, configuration and service; turns field needs into product requirements that ship | Contributes to the product roadmap, which product management owns, with requirements drawn from patterns across clients |

### B7. Data governance, security and lineage

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B7.1 Data governance and stewardship** (data owners, stewards, policies, decision rights) | Knows what data owners and stewards do | Acts as steward for an account's data and applies its policies | Sets up data governance for an account: data owners, stewards, decision rights over the data and data policies, agreed with the client | Leads data governance across the organisation with policies other teams adopt, or holds a data-management credential (such as CDMP, Certified Data Management Professional) and teaches it |
| **B7.2 User access and data security** (provisioning, least privilege, access reviews) | Knows least privilege, segregation of duties and multi-factor authentication | Provisions and removes users to a documented process; keeps access records | Designs the access-control process for an account (roles, approvals, periodic access reviews) and agrees it with the client | Contributes to the organisation's access and security policy, which security owns; their access-control design is adopted across accounts |
| **B7.3 Confidentiality, privacy and compliance** (confidentiality terms, privacy law, data residency) | Knows the confidentiality and privacy duties that apply to client data | Handles client and provider data within its contractual and legal limits; records what was shared and with whom | Assesses new data flows for confidentiality, privacy and residency risk; supports client compliance audits | Contributes to the service's compliance policy, which legal or compliance owns; other teams use their data-flow assessments, or they hold a privacy credential (such as CIPP, Certified Information Privacy Professional) and advise beyond their team |
| **B7.4 Data lineage and traceability** (lineage, transformation history, figure-to-source tracing) | Knows what lineage is and why finance and audit teams ask where a figure came from | Traces a delivered figure back to the submitted source through each mapping and transformation, and documents the path | Designs lineage capture for an account so that any delivered figure can be traced to its source and version; answers finance and audit queries from it | Their lineage standard is adopted across the platform or service line |

### B8. Automation and AI in data services

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B8.1 Scripting and workflow automation** (Python, SQL, spreadsheet automation, low-code) | Knows which repeated tasks can be automated | Writes scripts that automate parts of profiling, mapping or checking | Builds tested, version-controlled automation that others on the team run | Their automation and its standards are adopted across the service line |
| **B8.2 AI-assisted data processing** (LLM classification, extraction, mapping suggestions, human review) | Knows where models help with data work (classification, extraction, mapping suggestions) and how they fail | Uses AI tools to suggest mappings or classify fields, and reviews every output before use | Builds AI-assisted steps with confidence routing, human approval, logged decisions and measured accuracy | Contributes to the organisation's policy on where model judgement is allowed in data work; other teams adopt their method, or they publish it |
| **B8.3 AI-assisted service delivery** (AI drafting and summaries, assistants for client and provider questions, automated follow-up, human review) | Knows how AI assistants can draft summaries, replies and reports, and how they fail (missing context, invented facts, confidentiality) | Uses AI assistants for summaries, drafts and replies; checks every output against its sources before it reaches a client or provider | Sets up AI-assisted delivery workflows with the organisation's AI tools that others on the team use, with source citations, review steps and a rule for what may reach a client without a human check; measures their error rate | Their AI delivery workflows or policy are adopted by other teams in the organisation, or they publish or teach the method |

## The pathway

The framework has one pathway, **Managed data services professional**. Every competency sits in exactly one of three groups. Within a group, and within each specialisation, the competencies are listed in alphabetical order; the code shows each one's tier and domain.

| Group | Competencies | What it holds | What is required |
|---|---|---|---|
| **Mandatory** | 7 | The commitments and conduct that bind every piece of work, whoever does it: what the contract and the service levels promise, how client data is protected, how the client is told, when to escalate and the written procedure | All seven, at the level shown (five at L2, two at L1) |
| **Core** | 16 | The shared foundation: the work everyone in a managed data service delivers, on the client side and on the data side | All sixteen at L2 |
| **Optional** | 31 | Where a person goes deeper, listed by specialisation: Client delivery and customer experience (9), Data operations and quality (11) and Solutions and onboarding (11) | Six of the person's choice: three to L3 and three to L2 |

### Mandatory

| Competency | Code | Required |
|---|---|---|
| Client communication and presentation | A1.3 | L2 |
| Confidentiality, privacy and compliance | B7.3 | L2 |
| Contract and statement-of-work interpretation | A2.1 | L1 |
| Escalation management | A5.2 | L2 |
| Service level management | A6.1 | L1 |
| Standard operating procedures and runbooks | B5.3 | L2 |
| User access and data security | B7.2 | L2 |

### Core (all at L2)

| Competency | Code | Domain |
|---|---|---|
| Business definitions and data dictionaries | B2.3 | B2. Data modelling and standardisation |
| Continuous improvement and standardisation | A8.3 | A8. Team leadership and service operations |
| Data delivery, reporting and analytics | B6.2 | B6. Platform, solutions and data delivery |
| Discovery and requirements | A3.2 | A3. Client and provider onboarding |
| Financial and accounting data | B1.1 | B1. Data domain knowledge |
| Implementation and go-live | A3.3 | A3. Client and provider onboarding |
| Platform configuration and product knowledge | B6.1 | B6. Platform, solutions and data delivery |
| Provider enablement and training | A4.2 | A4. Data provider management |
| Provider engagement | A4.1 | A4. Data provider management |
| Root cause and problem management | A5.3 | A5. Support, escalation and problem management |
| Sector data and terminology | B1.2 | B1. Data domain knowledge |
| Service economics and cost to serve | A8.4 | A8. Team leadership and service operations |
| Stakeholder relationship management | A1.1 | A1. Client relationship and account governance |
| Team leadership and coaching | A8.1 | A8. Team leadership and service operations |
| Validation rules and data quality checks | B4.1 | B4. Data quality and validation |
| Workload planning and prioritisation | A8.2 | A8. Team leadership and service operations |

### Optional (six: three to L3 and three to L2)

The options are listed in three sub-groups, one for each specialisation. A competency belongs to the specialisation that goes deepest in it, and to no other.

**Client delivery and customer experience.** The customer success or engagement manager for one or a few high-touch enterprise accounts: account governance and planning, renewal and retention, requests, value, customer experience and AI-assisted service delivery. A manager covering a large pool of smaller accounts needs more of A8.2 (segmentation, capacity) and B8.3, and less depth per account.

| Competency | Code | Domain |
|---|---|---|
| Account governance and cadence | A1.2 | A1. Client relationship and account governance |
| Account health and retention | A2.4 | A2. Contract, scope and commercial management |
| Account planning and success plans | A1.4 | A1. Client relationship and account governance |
| AI-assisted service delivery | B8.3 | B8. Automation and AI in data services |
| Customer insight and feedback | A7.1 | A7. Customer experience |
| Journey mapping and experience design | A7.2 | A7. Customer experience |
| Renewal, expansion and commercial awareness | A2.3 | A2. Contract, scope and commercial management |
| Request and issue handling | A5.1 | A5. Support, escalation and problem management |
| Value realisation and outcome measurement | A6.3 | A6. Service levels and performance reporting |

**Data operations and quality.** Runs the data cycle: provider compliance, the submission cycle, entity resolution, reconciliation, exceptions, monitoring, data incidents, performance reporting, governance, lineage and AI-assisted processing.

| Competency | Code | Domain |
|---|---|---|
| AI-assisted data processing | B8.2 | B8. Automation and AI in data services |
| Data governance and stewardship | B7.1 | B7. Data governance, security and lineage |
| Data incident, correction and restatement management | B5.4 | B5. Data operations |
| Data lineage and traceability | B7.4 | B7. Data governance, security and lineage |
| Entity resolution and master data | B3.4 | B3. Data onboarding, mapping and integration |
| Exception triage and remediation | B4.3 | B4. Data quality and validation |
| Pipeline monitoring and data observability | B5.2 | B5. Data operations |
| Reconciliation and financial tie-outs | B4.2 | B4. Data quality and validation |
| Service performance reporting | A6.2 | A6. Service levels and performance reporting |
| Submission compliance and follow-up | A4.3 | A4. Data provider management |
| Submission cycle operations | B5.1 | B5. Data operations |

**Solutions and onboarding.** The implementation consultant or data onboarding engineer: scope, onboarding design and the implementation plan, industry standards, modelling and reference data, gap analysis, mapping, ingestion, solution design and automation.

| Competency | Code | Domain |
|---|---|---|
| Data ingestion and transformation | B3.3 | B3. Data onboarding, mapping and integration |
| Implementation project management | A3.4 | A3. Client and provider onboarding |
| Industry data standards | B1.3 | B1. Data domain knowledge |
| Onboarding programme design | A3.1 | A3. Client and provider onboarding |
| Reference data and chart-of-accounts design | B2.2 | B2. Data modelling and standardisation |
| Scope and change control | A2.2 | A2. Contract, scope and commercial management |
| Scripting and workflow automation | B8.1 | B8. Automation and AI in data services |
| Solution design and product feedback | B6.3 | B6. Platform, solutions and data delivery |
| Source data profiling and gap analysis | B3.1 | B3. Data onboarding, mapping and integration |
| Source-to-target mapping | B3.2 | B3. Data onboarding, mapping and integration |
| Target data models | B2.1 | B2. Data modelling and standardisation |

**Choosing options.** The selection rule covers the whole Optional list; the sub-groups say where each option belongs, and a person may choose within one or across them.

- **A specialist** takes all six from one specialisation.
- **A lead**, who is accountable for an account across both halves of the service, takes options from all three. The lead's usual choices are the ones that join the halves: A1.2 Account governance and cadence, A2.4 Account health and retention; B5.4 Data incident, correction and restatement management, B4.3 Exception triage and remediation, B5.1 Submission cycle operations; A3.4 Implementation project management, A2.2 Scope and change control.

**Roles that need more.** The pathway is the minimum for the title. A role that needs more depth (the lead of an account, a senior specialist, the head of a service) is written as a job spec from the same competencies, each with its own required level. A managed data services lead, for example, usually needs A1.1 Stakeholder relationship management, A2.1 Contract and statement-of-work interpretation, A5.2 Escalation management, A6.1 Service level management and A8.1 Team leadership and coaching at L3, which the pathway holds at L1 or L2. Every L3 still needs evidence of guiding others. The pathway sets nothing at L4. The pathway's name follows industry use: several data companies call a whole service line "managed data services".

## Outside role check

In November 2026 an independent review tested the competency list against seven public role postings at other companies and one managed-data-services product page. The roles were a client data onboarding specialist and an onboarding lead at a wealth-data platform; an implementation specialist and a managed-services business analyst at an index and analytics provider; a mid-market customer success manager at a fund-software company; and a senior project manager and a director of data operations at a private-markets data company.

- **Supported well:** A3.3, A3.4, A4.1, A5.1, A5.2, A6.1, A6.2, A8.1 to A8.4, B3.3, B3.4, B4.2, B4.3, B5.3, B6.1, B7.4, B8.2 and B8.3. Every role mapped mostly onto existing competencies.
- **Gaps found and closed in 2026.2:** historical data conversion and backfill (B3.3, A3.3); collecting data from documents (B3.3 and the definition of MDS); data-feed authorisation and consent (A4.1); training and adoption by the client's own users (A3.1); the mix of in-house, offshore and automated delivery (A8.4).
- **Left to a job spec:** a customer success manager covering many smaller accounts (see Client delivery and customer experience under "The pathway"); hands-on scripting for leads (B8.1 is an option, or a job spec sets its level).

## Mapping to other references

- **SFIA 9:** A1 RLMT; A2 ITCM; A3 REQM, PRMG (A3.4); A4 SUPP (an analogy only: the providers supply the client, and the service manages them on the client's behalf); A5 CSMG, USUP, PBMG; A6 SLMO, MEAS; A7 CEXP; A8 PEMT, BPRE, FMIT (A8.4); B1–B2 DTAN, DATM; B3 DENG; B4 DATM, QUAS; B5 DENG, KNOW, USUP (B5.4); B6 BINT, DAAN, REQM, PROD; B7 GOVN, IRMG, SCTY, DATM (B7.4); B8 MLNG, AIDE. CEXP and DAAN are new in SFIA 9. CSMG was already in SFIA 8; SFIA 9 revised its level descriptions. DATM gained levels 2 and 3.
- **CXPA CCXP** (five exam domains): Customer insights and understanding → A7.1; Design, implementation and innovation → A7.2; Metrics, measurements and ROI → A6.3, A7.1; Customer experience strategy → A7.2 in part (journey-level strategy only); Culture and accountability → not covered. The CCXP tests CX at about L2 in A7 and A6.3. It does not cover account management, provider management or data work.
- **Customer success (SuccessCOACHING CCSM):** Level 1 (onboarding, account success plans, business reviews, escalations, customer success metrics) sits at about L1–L2 in A1.4, A3.1, A5.2 and A6.2. Level 2 (customer health, risk, churn, retention and renewals, expansion, feedback) sits at about L2 in A2.3, A2.4 and A7.1. Level 3 (segmentation, engagement models, capacity modelling) sits at about L2 in A8.2. A TSIA article on structuring a managed services organisation informs A8; TSIA's customer success capabilities framework is gated and was not read.
- **Service management (ITIL 4 practices):** relationship management → A1.1; project management → A3.4; service desk and service request management → A5.1; incident management → B5.4; problem management → A5.3; service level management → A6.1; measurement and reporting → A6.2; service financial management → A8.4; continual improvement → A8.3; supplier management → A4 (an analogy, as with SFIA SUPP); knowledge management → B5.3.
- **Data management (DAMA-DMBOK 2, 2024 revision):** data governance → B7.1; data quality → B4 (currency is now a quality dimension); reference and master data → B2.2, B3.4; data integration and interoperability → B3; metadata → B2.3, B7.4; data modelling and design → B2.1; data security → B7.2. **DataOps:** freshness, volume and schema checks and data contracts → B5.2; lineage → B7.4.
- **Real-estate data standards (B1.3):** OSCRE Industry Data Model (asset life cycle, 130+ use cases); RESO Data Dictionary 2.1, the current version for RESO certification (residential listings, so of limited use for institutional operating data); NCREIF PREA Reporting Standards (asset-level reporting elements, 2025 expansion); AICPA Audit Data Standards, General Ledger Standard (2015) for ledger and trial-balance design.
- **AI in data services (B8):** 2026 practice has agents propose mappings and schema fixes and a person approve them before go-live, with each decision logged; one published case reports schema-change fixes falling from days to hours. B8.2's L3 descriptor follows that pattern.

Sources:

- CXPA, CCXP exam blueprint and preparation resources: https://cxpaglobal.org/get-certified/prep-resources
- SFIA 9 skills A–Z: https://sfia-online.org/en/sfia-9/all-skills-a-z
- SFIA 9 data and analytics skills (release notes): https://sfia-online.org/en/sfia-9/sfia-9-release-notes/data-and-analytics-skills
- SFIA 9 Customer experience (CEXP), "a new skill introduced in SFIA 9": https://sfia-online.org/en/sfia-9/skills/customer-experience
- SFIA 8 Customer service support (CSMG): https://sfia-online.org/en/sfia-8/skills/customer-service-support
- SFIA 9 Customer service support (CSMG), revision notes: https://sfia-online.org/en/sfia-9/skills/customer-service-support
- ITIL 4 management practices (summary): https://itsm.tools/34-itil-4-management-practices/
- DAMA-DMBOK 2 revision notes: https://dama.org/dama-dmbok-revision/
- SuccessCOACHING CCSM Level 1: https://learn.successcoaching.co/bundles/ccsm-level-1
- SuccessCOACHING CCSM Level 2: https://learn.successcoaching.co/bundles/ccsm-level-2-refresh
- SuccessCOACHING CCSM Level 3: https://learn.successcoaching.co/bundles/ccsm-level-3-courses
- TSIA customer success capabilities framework (gated): https://www.tsia.com/ebooks/customer-success-capabilities-framework
- TSIA, structuring a managed services organisation: https://www.tsia.com/blog/how-to-structure-your-managed-services-organization
- Monte Carlo, what is DataOps (observability signals): https://montecarlodata.com/blog-what-is-dataops
- Teradata, what is DataOps (data contracts): https://www.teradata.com/insights/data-platform/what-is-dataops
- OSCRE Industry Data Model: https://www.oscre.org/Industry-Data-Model/Introducing-the-Data-Model
- RESO Data Dictionary (versions): https://dd.reso.org/
- NCREIF PREA Reporting Standards: https://ncreif.org/about/standards
- RSM, NCREIF PREA Reporting Standards update: https://rsmus.com/insights/industries/real-estate/ncreif-prea-reporting-standards.html
- XBRL International, what is XBRL: https://www.xbrl.org/the-standard/what/what-is-xbrl/
- AICPA Audit Data Standards, General Ledger Standard: https://www.aicpa-cima.com/resources/download/general-ledger-standard-audit-data-standards
- Agentic data-pipeline onboarding with human approval (F1 and AWS case): https://www.zenml.io/llmops-database/agentic-ai-for-automated-data-pipeline-onboarding-and-schema-evolution-in-sports-marketing
- Agentic data pipelines in production: https://blueorange.digital/blog/agentic-data-pipelines-what-actually-runs-in-production/

## Changes in 2026.3

- **One pathway replaces four.** Managed data services lead, Client delivery and customer experience, Data operations and quality and Solutions and onboarding each restated all 54 competencies at a different level, grouped by depth (Specialism, Shared foundation, Awareness). The single pathway, Managed data services professional, lists each competency once, as Mandatory, Core or Optional. The three specialisms are now the sub-groups of Optional. The lead is no longer a pathway: a lead takes options across the specialisations, and a lead's full requirement is a job spec. The senior-role rule is replaced by job specs.
- **Competencies and descriptors:** unchanged. All 54 keep their names and their L1–L4 wording.
- **How the groups were drawn.** A competency is Optional when one of the three specialisms took it to L3 and at least one 2026.2 pathway asked only for awareness (L1): 31 competencies, each in the specialism that took it to L3. No competency was L3 in two specialisms. The other 23 are required of everyone at the lowest level any 2026.2 pathway asked: L2 for 21, and L1 for A2.1 Contract and statement-of-work interpretation and A6.1 Service level management, which only the lead took to L3. Of those 23, the seven that bind every piece of work are Mandatory and the rest are Core.
- **Levels, against the 2026.2 lead pathway.** Lowered from L3 to L2: A1.1 Stakeholder relationship management (Core), A5.2 Escalation management (Mandatory), A8.1 Team leadership and coaching (Core). Lowered from L3 to L1, now Mandatory: A2.1 Contract and statement-of-work interpretation, A6.1 Service level management. Moved from a required level to Optional: 31 competencies (7 the lead held at L3, 16 at L2, 8 at L1). None raised. L3 is now reached through three chosen options; the lead pathway had twelve at L3.
- **Levels, against the 2026.2 specialisms.** Each specialism's L3 competencies that every pathway already held at L2 or above are now Mandatory or Core at L2, and are not options: Client delivery and customer experience: A1.1, A1.3, A4.1, A4.2; Data operations and quality: A5.3, B1.1, B2.3, B4.1, B5.3, B7.2; Solutions and onboarding: A3.2, A3.3, B1.2, B6.1, B6.2. A role that needs one of them at L3 says so in a job spec.
- **Not yet reviewed.** The grouping has not had the adversarial review that edition 2026.2 had.

## Use in the competency graph

This is the level guide for the library framework `chan-cxmds`; its requirements are in `chan-cxmds.csv` beside this file, on the L1–L4 scale. Competencies that match carry `externalRef: "Chan CXMDS 2026: <competency>"`. Select it under `frameworks:` in `competency-graph.yaml` (`frameworks.py list --all` shows the pathway), and the dashboard's Competency frameworks tab lists it. When rating a competency against it, read that competency's row in the tables above: each column says what the evidence must show at that level.
