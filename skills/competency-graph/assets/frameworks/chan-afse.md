---
title: Agentic Full-Stack Engineer Framework
date: 2026-11-09
keywords: [agentic-engineering, competency-framework, full-stack, forward-deployed, harness-engineering, evals, knowledge-graph]
lastUpdated: 2026-11-14
author: Reggie Chan
documentType: framework
version: 2026.6
status: draft
---

# Agentic Full-Stack Engineer Framework (Chan AFSE 2026.6)

*Reggie Chan, November 2026.* A competency framework for the engineer who designs, builds, evaluates, secures, deploys and operates LLM agent systems end to end, inside real applications. No professional body publishes one: SFIA 9 has no agent-engineering skill, and every vendor certification sits at about L2. The agentic tier rests on a November 2026 review of vendor, academic and practitioner sources, SFIA 9 and the agent-engineering certifications. Edition 2026.4 added the forward-deployed domain and seven foundation competencies after a check against three role descriptions and the job postings behind them (see "Changes in 2026.4").

## Structure

- **Tier A, full-stack software foundation (8 domains, 29 competencies):** what any full-stack developer needs; agents ship inside applications with front ends, APIs, databases and cloud infrastructure.
- **Tier B, agentic engineering (9 domains, 38 competencies):** the disciplines specific to agent systems, and the forward-deployed work of delivering them inside a customer's organisation (B9). Each Tier B domain builds on Tier A: agent UX on front-end engineering, retrieval on data stores, agent security on application security, agent operations on DevOps and system design.
- **One pathway, Agentic full-stack engineer,** puts every competency in exactly one of three groups: **Mandatory** (5, the list shared by every pathway in the agentic field, at fixed levels), **Core** (29, the baseline of this pathway, all at L2) and **Optional** (33, of which a person takes six: three to L3 and three to L2). Tier A, the full-stack foundation, is Core. Mandatory is five Tier B competencies. The Optional competencies are the rest of Tier B, listed in four sub-groups, one for each specialisation: Forward-deployed delivery, Agent application, Agent platform and harness, and Agent reliability and security. See "The pathway".
- **Three related roles are job specs,** not pathways: full-stack developer, forward-deployed engineer and agentic solutions architect. See "Roles as job specs".

Levels use the competency graph's scale: **L1 Aware** (knows it, has not delivered it), **L2 Practitioner** (delivers it independently), **L3 Advanced** (handles complex cases, is accountable for the result, guides others), **L4 Expert** (a recognised authority beyond their own team). Roughly SFIA 1–2, 3, 4–5 and 5–6. Every L3 needs evidence of guiding others (reviewing their work, coaching them, or setting a method they follow), whether or not the row names it; a delivered design that matches an L3 row without that evidence rates L2. Every L4 needs evidence of adoption or recognition beyond the person's own team.

Unstable discipline names are aliases, shown in brackets: harness engineering (B4.2), loop engineering (B4.3), graph engineering (B4.4), intent engineering (B1.1), prompt and context engineering (B2.1). Three new "X engineering" labels appeared between February and July 2026; the competencies underneath are older and steadier than the names.

## Tier A: full-stack software foundation

### A1. Front-end engineering

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A1.1 Web fundamentals and TypeScript** (HTML, CSS, JavaScript) | Knows the DOM, events and rendering, HTML semantics, CSS layout, JavaScript basics, browser storage and the same-origin policy | Builds typed, interactive pages in TypeScript with sound HTML and CSS; handles browser storage, caching and cross-origin requests correctly | Designs typed component and module structures; sets performance budgets and fixes Core Web Vitals regressions | Sets front-end language and tooling standards adopted across teams |
| **A1.2 Component frameworks and state** (React, Next.js, Vue, Svelte) | Knows components, props, state and routing | Builds an app with routing, forms, data fetching and client state in a mainstream framework | Designs state and data-fetching architecture (server components, streaming, caching, optimistic updates) | Chooses framework strategy for an organisation; maintains shared component libraries |
| **A1.3 Accessibility, responsive design and design systems** (WCAG, a11y) | Knows WCAG principles and responsive layout | Ships responsive UI that meets WCAG 2.2 AA, tested with a screen reader | Audits and remediates accessibility; builds accessible design-system components | Owns accessibility and design-system standards across products |

### A2. Back-end and APIs

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A2.1 Server-side programming** (Python, TypeScript/Node) | Knows how server code is organised and how a service is run locally | Builds services with typed code, packaging, configuration and error handling | Designs concurrency and async processing; profiles and fixes performance | Sets language, runtime and service-template standards |
| **A2.2 API design** (REST, GraphQL, OpenAPI, streaming) | Explains REST, GraphQL and HTTP semantics | Designs documented, versioned APIs (OpenAPI) with pagination and consistent errors | Designs streaming APIs (SSE, WebSocket), idempotency keys, rate limits and backward compatibility | Runs API governance and review across an organisation |
| **A2.3 Authentication and session management** (OAuth 2.1, OIDC, sessions, JWT) | Knows sessions, tokens and OAuth flows | Implements OAuth 2.1/OIDC sign-in and session handling with an identity provider | Designs token lifecycles, service-to-service auth and multi-tenant isolation | Designs identity architecture across products |
| **A2.4 Asynchronous and event-driven services** (queues, pub/sub, background jobs) | Knows queues, events and background jobs | Builds background jobs and consumers on a managed queue | Designs event-driven systems with retries, dead-letter queues and exactly-once effects | Sets platform patterns for eventing and workflows |

### A3. Data and databases

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A3.1 Relational modelling and SQL** (PostgreSQL, schema design, migrations) | Knows tables, keys and joins | Designs normalised schemas, writes SQL and manages migrations | Tunes queries and indexes; designs transactions, isolation and partitioning | Sets data-modelling standards and reviews schemas across teams |
| **A3.2 Document, key-value and vector stores** (NoSQL, Redis, pgvector, vector databases, caching) | Knows when document, key-value or vector stores fit | Uses a document or key-value store, a cache and a vector index in an application | Chooses the store per workload; designs hybrid search indexes, cache invalidation and consistency trade-offs | Sets data-store strategy for an organisation |
| **A3.3 Data pipelines and data quality** (ETL/ELT, data contracts) | Knows ETL and ELT | Profiles a source and builds a pipeline with validation and scheduling | Designs lineage, data contracts and quality monitoring; reconciles sources and handles schema change | Governs a data platform used by many teams |
| **A3.4 Data modelling and semantics** (entities, identifiers, ontology, system of record) | Knows entities, relationships, identifiers and cardinality, and that the same word can mean different things in different systems | Models a domain's entities and relationships; writes down what each field means, its unit and its grain, and which system owns it | Designs a canonical model across several source systems; settles conflicting definitions with the business owners; designs for meaning that changes over time | Sets a shared data model or ontology used beyond their own team |
| **A3.5 Data governance and privacy** (classification, provenance, retention, deletion) | Knows data classification, provenance, retention and deletion, and which privacy rules apply to the data handled | Applies classification, retention and deletion rules in an application; records where data came from and who owns it; fulfils an access or deletion request | Designs audit trails, lineage and retention across systems; checks data residency and movement; runs a privacy impact assessment | Sets data governance policy across an organisation |

### A4. Cloud, infrastructure and DevOps

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A4.1 Containers and runtime platforms** (Docker, Kubernetes, serverless) | Knows containers and managed platforms | Containerises an app and deploys it to a managed platform | Runs orchestrated or serverless workloads with autoscaling and zero-downtime deploys | Designs the internal platform other teams deploy to |
| **A4.2 CI/CD and release engineering** (pipelines, feature flags) | Knows build and deploy pipelines, package managers and lockfiles | Builds CI with tests and linting, and CD to staging and production; produces a reproducible build with pinned dependencies and configuration kept apart for each environment | Designs progressive delivery, feature flags and rollback; sequences schema migrations with releases | Sets release standards across an organisation |
| **A4.3 Infrastructure as code and cloud services** (Terraform, Pulumi, CDK, networking) | Knows infrastructure as code and core cloud services | Provisions environments with an IaC tool | Designs multi-environment, cost-aware cloud architecture and networking | Sets cloud strategy, landing zones and governance |
| **A4.4 Operating systems and networking** (processes, shells, DNS, HTTP, TLS) | Knows processes, filesystems, permissions and environment variables, and how DNS, HTTP, TLS, ports and proxies carry a request | Works in a shell on a server or container; configures DNS, TLS and a reverse proxy for a service; traces a failed connection to its cause | Diagnoses resource and network faults across hosts and environments; designs the network layout and access between services | Sets host and network standards across an organisation |
| **A4.5 Reliability operations and recovery** (incident response, backups, disaster recovery) | Knows health checks, alerting, backups and recovery objectives (RTO, RPO) | Adds health checks and alerts to a service; takes backups and proves a restore works; follows a runbook in an incident | Leads incident response with named roles, a live record of the incident and clear hand-offs; plans capacity; designs and tests disaster recovery against availability objectives | Sets reliability practice and availability objectives across an organisation |

### A5. Application security

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A5.1 Secure coding and the OWASP Top 10** (OWASP Top 10, threat modelling) | Knows the OWASP Top 10 | Prevents injection, XSS, CSRF and SSRF; validates and encodes input and output | Threat-models applications; runs SAST and DAST and fixes findings | Runs a secure development lifecycle across an organisation |
| **A5.2 Authorisation and data protection** (RBAC, ABAC, encryption, PII) | Knows RBAC, encryption at rest and in transit, and PII | Implements role-based access, encrypts sensitive data and minimises PII | Designs fine-grained authorisation (policy engines), tenant isolation and privacy by design | Sets data-protection architecture and policy |
| **A5.3 Secrets and supply-chain security** (secret managers, SBOM, SLSA) | Knows secret managers and dependency risk | Uses a secret manager, dependency scanning and lockfiles | Produces SBOMs and signed builds; leads security incident response | Sets supply-chain security policy across an organisation |

### A6. Software quality and testing

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A6.1 Automated testing** (unit, integration, end-to-end, TDD) | Knows the test pyramid | Writes unit, integration and end-to-end tests; uses test-first where it helps | Designs test strategy by risk; contract tests; controls flaky tests | Sets quality standards across teams |
| **A6.2 Version control and code review** (Git, pull requests) | Knows Git basics | Works in branches and pull requests; reviews others' code | Designs branching and review workflows; trunk-based development; monorepo practice | Sets engineering-practice standards across an organisation |
| **A6.3 Debugging and performance profiling** (post-mortems) | Knows how to use a debugger and read logs | Diagnoses production bugs from logs and traces | Profiles and root-causes issues across services; load-tests to find bottlenecks and capacity limits; writes blameless post-mortems | Builds an organisation's debugging and incident practice |

### A7. Architecture and system design

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A7.1 System design and distributed systems** (scalability, consistency, CAP) | Knows client-server design, latency and the CAP trade-off | Designs a service with a database, cache and queue | Designs for scale, failure and consistency across services | Reviews architecture across teams; sets reference architectures |
| **A7.2 Architecture decisions and documentation** (ADRs, C4, design docs) | Reads an ADR and an architecture diagram | Writes ADRs, design docs and C4 diagrams | Runs design reviews; weighs trade-offs with evidence | Sets architecture governance |
| **A7.3 Observability fundamentals** (logs, metrics, traces, SLOs, OpenTelemetry) | Knows logs, metrics and traces | Instruments services with structured logs, metrics and OpenTelemetry traces | Defines SLOs, alerts and dashboards; runs on-call | Sets observability standards across an organisation |
| **A7.4 Concurrency, consistency and idempotency** (race conditions, locking, isolation) | Knows what a race condition is, and why a retry or a duplicate request can repeat an effect | Uses transactions, locks or optimistic concurrency so that simultaneous changes stay correct; makes a retried request safe with an idempotency key | Chooses isolation levels and locking per workload; finds and fixes races in production; designs duplicate-safe processing across services | Sets concurrency and consistency patterns adopted across teams |

### A8. Programming and software design

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **A8.1 Programming fundamentals, data structures and algorithms** (types, control flow, async, complexity) | Knows types, control flow, functions, error handling and the common data structures (arrays, maps, sets, trees, queues) | Writes correct, readable code in one language with error handling and asynchronous execution; picks the data structure and algorithm for the job and states its time and memory cost | Diagnoses faults rooted in runtime behaviour (memory, the event loop, garbage collection) and in complexity as the workload grows; reviews others' code for both | Sets language and coding standards adopted across teams; is consulted on algorithmic and runtime problems beyond their own team |
| **A8.2 Software design and refactoring** (modularity, interfaces, dependencies) | Knows encapsulation, interfaces, coupling and cohesion, and the functional and object-oriented approaches | Breaks a feature into coherent modules behind clear interfaces; refactors working code under tests without changing its behaviour | Designs module boundaries and dependency direction for a codebase; weighs the main design options by their impact and risk; leads a large refactor in safe steps; reviews others' designs | Sets design standards and leads the modernisation of codebases across teams |

## Tier B: agentic engineering

### B1. Intent and specification

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B1.1 Outcome and acceptance specification** (intent engineering, objective functions) | Explains why goals, constraints and stop conditions steer agent behaviour; spots vague briefs | Writes goals with hard constraints, edge cases and testable acceptance criteria before building | Writes **machine-checkable** acceptance and escalation conditions that a loop or verifier acts on; reconciles conflicting objectives across stakeholders | Sets organisation-wide specification standards that trace business outcomes to eval criteria; other teams adopt them |
| **B1.2 Spec-driven development and living documentation** (SDD, PRD/ADR chains, constitutions) | Knows the specify → plan → tasks → implement flow and the role of PRDs and ADRs | Runs an SDD cycle on a feature with Spec Kit, Kiro or similar; keeps AGENTS.md/CLAUDE.md current | Maintains a constitution and living specs that agents verify against; prunes instruction bloat; judges when SDD is overkill | Designs instruction-file hierarchies and mechanically enforced doc freshness across many repos (CI checks, doc-gardening agents) |

### B2. Context, retrieval and memory

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B2.1 Context engineering** (prompt engineering, context assembly) | Explains the context window as finite; knows system prompts, few-shot examples and instruction files | Writes effective system prompts, instruction files and schemas; chooses what to retrieve for a task | Manages context across long runs (compaction, context editing, sub-agent isolation, just-in-time retrieval); diagnoses context rot; measures the effect | Sets context-architecture patterns for an organisation; benchmarks context strategies on cost and accuracy |
| **B2.2 Retrieval and agentic search** (RAG engineering) | Distinguishes vector, keyword, agentic search and GraphRAG | Builds a RAG pipeline with managed embeddings, or gives an agent search tools | Implements hybrid retrieval with reranking and contextual chunking; builds retrieval evals (recall@k); exposes retrieval as tools | Sets retrieval strategy (agentic, hybrid or GraphRAG per corpus) from measured evidence that other teams adopt; designs knowledge-graph schemas used beyond their team |
| **B2.3 Memory and state** (memory engineering) | Distinguishes working, session and long-term memory | Uses SDK sessions, checkpointers and a memory tool with defaults | Designs memory schemas, progress artefacts and expiry; treats stored memory as a poisonable attack surface | Sets memory-hygiene policy (what is written, trusted and forgotten) and measures its effect across systems |

### B3. Tools and protocols

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B3.1 Tool and interface design** (tool engineering) | Explains how tool names, descriptions and schemas steer the model | Writes tools with clear names, typed parameters and actionable errors | Consolidates and namespaces tools; adds pagination and response-format controls; refines tool design from eval transcripts | Designs tool surfaces that many agents depend on; sets tool-design standards from measured results |
| **B3.2 Protocol integration** (MCP, A2A, Agent Skills, AGENTS.md) | Explains what MCP, A2A and Skills each connect | Builds an MCP server with an official SDK and wires it to a client; packages a skill | Implements OAuth 2.1 resource-server auth; migrates to the stateless 2026-07-28 spec; designs skill libraries | Designs cross-organisation A2A topologies with signed Agent Cards; contributes to specifications (SEPs) |
| **B3.3 Computer-use and browser agents** | Knows the API → DOM → pixel hierarchy and why OSWorld tracks are not comparable | Builds a sandboxed browser agent for a bounded task | Picks the lowest-autonomy channel that works; evaluates on real tasks; isolates sessions | Sets policy on when GUI agents are allowed; designs hybrid connector-plus-GUI architectures |

### B4. Architecture, harness and orchestration

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B4.1 Architecture pattern selection** (workflows vs agents) | Names the workflow patterns (chaining, routing, parallelisation, orchestrator-workers, evaluator-optimiser) | Builds one tool-using agent loop, or a chain or router, with one SDK | Chooses workflow, single agent or multi-agent with cost and quality evidence; justifies the token cost | Sets architecture standards and reviews other teams' agent designs; ports designs across handoff, subagent and graph SDKs |
| **B4.2 Harness engineering** (agent scaffolding, environment design) | Explains "Agent = Model + Harness" and names the harness components | Configures an off-the-shelf harness: instruction files, MCP servers, permissions, a few skills | Builds hooks, sub-agents and deterministic lint and test gates into the agent's feedback loop; designs long-running harnesses (initializer, progress file, one feature per session, separate generator and evaluator) | Builds harnesses used across an organisation; measures harness changes against evals; **removes components as models improve**; discloses the harness when comparing agents |
| **B4.3 Autonomous loop design** (loop engineering, Ralph loops) | Explains loops versus turn-by-turn prompting; knows "done is a claim and not a proof" | Runs a sandboxed agent loop with a single completion signal | Adds machine-checkable stop conditions checked by a separate model, committed state files, worktrees, token and iteration budgets, a verifier sub-agent and human hand-off points | Runs scheduled or event-triggered loop fleets that feed triage inboxes; measures loop outcomes; sets policy for unattended runs |
| **B4.4 Workflow and multi-agent orchestration** (graph engineering) | Knows nodes, edges and shared state, and which frameworks implement them | Builds a branching graph with typed state | Builds cyclic graphs with retries, checkpointed human interrupts, dynamic fan-out and durable resumption | Designs portable orchestration that teams across the organisation adopt, and is consulted on when not to use a graph (graph versus loop versus harness) |
| **B4.5 Model selection, control and adaptation** | Knows model tiers, structured outputs, effort settings and fine-tuning options | Picks a tier per task; uses schema-enforced outputs; sets effort | Routes across tiers (large orchestrator, small workers); tunes effort per call site | Runs the cost and quality frontier analyses other teams rely on for model choice; decides when fine-tuning or RL beats context engineering; designs graders and rewards reused beyond their team |

### B5. Evaluation and verification

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B5.1 Error analysis and failure taxonomy** | Knows the vocabulary (task, trial, grader, transcript, outcome) and why public benchmarks do not certify a product | Reviews 30–100 real traces, builds a failure taxonomy, and annotates the first failure in each trace | Uses transition failure matrices for multi-step agents; evaluates retrieval separately from generation; keeps a named domain-expert owner of quality | Defines eval methodology that other teams adopt; audits published benchmark claims for contamination and grader bugs |
| **B5.2 Graders and LLM-as-judge** (reward design) | Knows code, model and human graders and their trade-offs | Builds binary code-based and LLM graders for failure modes already observed | Validates judges on held-out human labels (TPR/TNR); re-aligns them as criteria drift; grades the outcome in the environment's state, not the agent's claim | Designs hack-resistant graders and rewards reused across evals and fine-tuning; publishes calibration methods |
| **B5.3 Verification gates and regression** (CI evals, pass^k) | Knows capability versus regression suites and pass@k versus pass^k | Runs a curated regression suite in CI with deterministic assertions | Runs isolated containerised trials; sets pass^k release gates; feeds production failures back into CI; uses independent verifier agents | Sets risk-tiered release gates across an organisation and audits other teams' suites for saturated or broken tasks |
| **B5.4 Verification of agent output** | Knows that an agent saying work is done or correct is a claim, not proof, and that models produce fluent errors | Checks agent output against the source, a test or an independent check before relying on it; records what was checked | Builds verification into the work (independent reviewers or tests, checking rates set by risk); measures the error that gets through; guides others | Sets verification standards adopted beyond their own team or project |

### B6. Security, safety and governance

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B6.1 Agent threat modelling and injection-resistant design** | Explains direct and indirect prompt injection, the lethal trifecta, and the OWASP LLM and Agentic lists | Spots trifecta exposure in a design; treats retrieved content and tool output as untrusted | Threat-models each agent against the trifecta and ASI01–ASI10; red-teams; applies plan-then-execute or dual-LLM patterns | Designs capability and provenance architectures (CaMeL-style) so injected input cannot trigger consequential actions; assumes injection will succeed and limits the blast radius |
| **B6.2 Identity, permissions and sandboxing** (least agency) | Knows least privilege, sandboxing and secrets hygiene | Scopes tool permissions; keeps secrets out of context; sandboxes code execution | Gives each agent its own identity with short-lived, audience-bound tokens; puts MCP behind a gateway with allowlists and definition pinning; applies default-deny egress | Designs defences against confused-deputy and credential-aggregation attacks across fleets; builds kill-switches on governable agent identities, adopted across the organisation's agents |
| **B6.3 Guardrails and human oversight** | Knows which agent actions need a person's approval, and how an automatic check differs from a person's review | Sets up agent work so that consequential actions (changes to the record, publication, payments, messages sent) wait for a person's approval; reviews what the agent did before accepting it | Sets approval levels by the risk of each action; puts cheap automatic checks before human review; measures how often checks wrongly pass or block | Designs oversight that resists approval fatigue and manipulation of the people approving; sets policy adopted beyond their own team |
| **B6.4 Responsible AI and regulatory compliance** | Knows the EU AI Act tiers and current dates, NIST AI RMF and ISO/IEC 42001 | Implements Article 50 disclosure, trace-based audit logs and PII minimisation | Classifies use cases (e.g. Annex III) and maps controls to Articles 12 and 14 and to AI RMF functions; runs DPIAs on agent data flows | Runs an ISO 42001-style management system across an agent portfolio; tracks moving regulation such as the Omnibus and CAISI outputs |
| **B6.5 AI disclosure and use boundaries** | Knows the principles of responsible AI use in their field: accuracy, disclosure, privacy, education and compliance | Discloses where AI materially shaped the work and records which AI tools were used; cites an AI response where its words are kept; never presents AI-generated or AI-altered material as evidence | Writes an AI-use statement for a project or product saying what agents did and what people verified; checks the AI rules of clients, credentialing bodies, publishers and platforms before delivering | Contributes to AI guidelines or position statements that a professional body, society or coalition publishes |
| **B6.6 Privacy and data protection in AI use** | Knows that data sent to a model provider can leave their control, and what a provider's data terms cover | Keeps personal and confidential data out of prompts unless it is permitted; checks a provider's data terms before sending records | Builds redaction and release checks into the workflow and enforces the policy automatically | Designs privacy arrangements for AI use that projects or organisations the person does not run adopt |

### B7. Production operations

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B7.1 Observability and trajectory debugging** | Knows traces and spans, and that tokens drive cost | Instruments an agent with an OTel-compatible tracer; walks a trajectory to the failing tool call | Standardises on `gen_ai.*` attributes; controls content capture for privacy; runs online judges on sampled traces | Sets vendor-portable telemetry conventions that other teams adopt; links traces to eval datasets and incident response |
| **B7.2 Reliability and durable execution** | Knows APIs rate-limit and fail transiently | Implements retries with backoff and jitter, timeouts, fallbacks, and step and spend caps | Makes side-effecting tools idempotent; checkpoints long runs on a durable-execution engine | Sets durable-execution patterns other teams adopt (replay-safe workflows with LLM decisions recorded as events; key-TTL hazards) and SLOs on pass^k and p95 latency |
| **B7.3 Cost and latency engineering** | Knows caching, batching and model tiers affect cost | Enables prompt caching and uses batch for offline work (50% discount) | Designs cache-friendly prompt layouts; budgets per tenant; treats runaway spend (OWASP LLM10) as a security risk | Runs portfolio-level cost and quality trade-offs; decides how much harness complexity a measured reliability gain justifies |
| **B7.4 Deployment, versioning and runtimes** (agent ops, LLMOps) | Knows prompts, tools and model IDs are deployable artefacts | Versions prompts, tools and model IDs in Git; runs evals in CI; deploys to one runtime | Gates releases on regression evals; runs canary or shadow traffic; pins model snapshots and handles deprecations | Sets the organisation's runtime and eval-gated delivery standards (lock-in, identity, residency, isolation, drift detection) |

### B8. Agentic software delivery and the human surface

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B8.1 Agent-assisted software development** (agentic engineering; vibe coding as the anti-pattern) | Knows how coding agents are used and can tell vibe coding from agentic engineering | Ships features with a coding agent under review and can explain every committed line; maintains instruction files | Runs spec → plan → tasks → implement with agent-written tests first; runs parallel agents in worktrees; writes team skills, hooks and integrations | Designs organisation-wide agent workflows (shared skill libraries, CI-integrated agent review); measures productivity and defect rates |
| **B8.2 Agent UX and human-in-the-loop interfaces** | Knows streaming, generative UI patterns and approval surfaces | Streams tokens and tool events to a UI and shows progress | Implements AG-UI-style state sync, interrupts and approvals; ships MCP Apps with a secure sandbox | Sets human-in-the-loop policy (which actions need approval; how plans, diffs, undo and rollback are shown); chooses the generative-UI pattern for the trust context; ensures text fallback and accessibility |

### B9. Forward-deployed delivery

| Competency | L1 Aware | L2 Practitioner | L3 Advanced | L4 Expert |
|---|---|---|---|---|
| **B9.1 Business and problem discovery** (customer discovery, domain analysis) | Explains how a customer's business earns revenue, incurs cost and carries risk; can tell a requested feature from the problem behind it | Interviews users, observes the work and examines the evidence; states the underlying problem, and what a correct answer looks like in the customer's terms; records where each requirement came from | Leads discovery in an unfamiliar organisation; traces a problem to its root cause and gets the stakeholders' agreement to the conclusions; catches a solution that is technically valid but commercially wrong; coaches others in discovery | Sets a discovery method that other teams adopt; is consulted on a domain's problems beyond their own engagements |
| **B9.2 Process analysis and task allocation** (workflow mapping, automation suitability) | Knows the parts of a workflow (activities, hand-offs, approvals, exceptions), and that fixed rules, a model, an agent and a person each suit different tasks | Maps a workflow as it is actually done, in a process model others can read, with its exceptions and bottlenecks; assigns each task to code, a model, an agent or a person, with approval points | Decomposes a process that crosses teams; sets out alternative designs and whether each is feasible; justifies the degree of autonomy at each step with evidence of cost and error; reviews others' allocations | Sets the organisation's method for deciding what is automated and what stays with people |
| **B9.3 Customer systems and enterprise integration** (legacy systems, files and feeds, identity) | Knows the common enterprise systems (ERP, CRM, data warehouse, identity provider) and the ways they exchange data (API, file, SFTP, database, queue) | Maps a customer's systems, their owners and their data flows; builds and tests an integration on the customer's own infrastructure, alongside their engineers, that handles authentication, rate limits, retries and duplicates | Decides where a new solution fits in the existing estate; designs integration across legacy and modern systems with reconciliation; assesses the integration risks; works inside the customer's network limits and security review | Sets reference integration architectures reused across customers |
| **B9.4 Platform fit, configuration and reuse** (configure or build, field feedback) | Knows the deployed platform's capabilities, limits, extension points and security model | Meets a requirement by configuration where that is enough and by custom code where it is not; knows what each costs to run | Separates a general product gap from a local requirement; turns a working pattern into a tool, playbook or building block that others use; takes field evidence, including where the model succeeds and fails, back to the product team | Shapes the product roadmap from field evidence; builds components adopted across customers |
| **B9.5 Prototyping and assumption testing** (rapid experimentation, proof of concept) | Knows what a prototype is for, and how a demonstration differs from a production system | Builds a narrow prototype that tests one named assumption (feasibility, data availability or usefulness) and reports what it showed | Orders experiments by risk; states what a successful demonstration leaves unproven; checks that architectural assumptions survive implementation | Sets how an organisation takes work from prototype to production, adopted beyond their own team |
| **B9.6 Delivery and scope management** (scopes of work, project plans) | Knows scope, estimates, dependencies and blockers | Scopes, sequences and estimates their own work; tracks dependencies; reports progress, risks and issues; raises and removes blockers early | Owns the delivery of an engagement from first prototype to stable production: writes the scope of work and the plan, delivers in increments, manages risks and dependencies, controls scope, and gets the trade-offs between scope, speed and quality stated and agreed | Sets the delivery method used across engagements |
| **B9.7 Stakeholder communication and decision ownership** | Knows the audiences on an engagement (executives, operators, developers, security) and what each needs to hear | Explains a technical decision to a non-technical audience; records who owns each decision | Brings executives, operators and security teams through a disagreement to a decision; coaches others | Advises customer executives across several engagements; sets the communication practice other teams follow |
| **B9.8 Adoption, handover and operational ownership** (change management, runbooks, training) | Knows that a deployed system is not yet an adopted one; knows runbooks and operational ownership | Trains users, writes the runbook, agrees with the customer's operators what must be true before they accept the system, and hands it to a named owner who can operate it | Designs adoption into daily work, including the incentives and habits that block it; works out how the change affects operational work and adjusts the change plan from feedback; leaves the customer able to diagnose and fix production failures without the engagement team | Sets adoption and handover practice across engagements, including the move from engagement delivery to the customer's own operation |
| **B9.9 Outcome measurement and delivery economics** (baselines, ROI, total cost of ownership) | Knows baselines, outcome measures (cycle time, accuracy, manual effort, cost, risk) and total cost of ownership | Sets a baseline before delivery, agrees the measures and how they will be tracked, and measures the change after it (adoption in production and the effect on the workflow); counts maintenance and human review in the cost | Builds the return case for an engagement (cost, benefit, impact and risk of each option; cost for each successfully completed task; support burden; the long-term cost of customer-specific work); compares the result with what the case predicted; decides build, buy or extend | Sets how the organisation measures and prices delivered outcomes |

## The pathway

The framework has one pathway, **Agentic full-stack engineer**. Every competency sits in exactly one of three groups. Within a group, and within each specialisation, the competencies are listed in alphabetical order; the code shows each one's tier and domain.

| Group | Competencies | What it holds | What is required |
|---|---|---|---|
| **Mandatory** | 5 | What anyone working with agents must hold, whatever their pathway: human oversight, verifying agent output, disclosing AI use, protecting data in AI use, and the rules on responsible AI. Shared with every pathway in the agentic field | All five, at the level shown (four at L2, one at L1) |
| **Core** | 29 | The full stack: Tier A, which every agentic full-stack engineer delivers, from programming fundamentals and the front end to security, testing, the cloud and its operation | All twenty-nine at L2 |
| **Optional** | 33 | The agentic tier, where a person goes deeper, listed by specialisation: Forward-deployed delivery (9), Agent application (7), Agent platform and harness (8) and Agent reliability and security (9) | Six of the person's choice: three to L3 and three to L2 |

### Mandatory

The same five competencies, at the same levels and with the same level wording, in every pathway of the agentic field.

| Competency | Code | Required |
|---|---|---|
| AI disclosure and use boundaries | B6.5 | L2 |
| Guardrails and human oversight | B6.3 | L2 |
| Privacy and data protection in AI use | B6.6 | L2 |
| Responsible AI and regulatory compliance | B6.4 | L1 |
| Verification of agent output | B5.4 | L2 |

**In this pathway** the shared wording shows up as: schema validation, filters for personal data and approval for writes, payments and outbound messages; policy written as code outside the model; evaluation suites and tests in CI before an agent's change is accepted; secrets and personal data kept out of context; disclosure under Article 50 of the EU AI Act. The engineering depth behind these is in the Optional list (B5, B6 and B7).

### Core (all at L2)

| Competency | Code | Domain |
|---|---|---|
| Accessibility, responsive design and design systems | A1.3 | A1. Front-end engineering |
| API design | A2.2 | A2. Back-end and APIs |
| Architecture decisions and documentation | A7.2 | A7. Architecture and system design |
| Asynchronous and event-driven services | A2.4 | A2. Back-end and APIs |
| Authentication and session management | A2.3 | A2. Back-end and APIs |
| Authorisation and data protection | A5.2 | A5. Application security |
| Automated testing | A6.1 | A6. Software quality and testing |
| CI/CD and release engineering | A4.2 | A4. Cloud, infrastructure and DevOps |
| Component frameworks and state | A1.2 | A1. Front-end engineering |
| Concurrency, consistency and idempotency | A7.4 | A7. Architecture and system design |
| Containers and runtime platforms | A4.1 | A4. Cloud, infrastructure and DevOps |
| Data governance and privacy | A3.5 | A3. Data and databases |
| Data modelling and semantics | A3.4 | A3. Data and databases |
| Data pipelines and data quality | A3.3 | A3. Data and databases |
| Debugging and performance profiling | A6.3 | A6. Software quality and testing |
| Document, key-value and vector stores | A3.2 | A3. Data and databases |
| Infrastructure as code and cloud services | A4.3 | A4. Cloud, infrastructure and DevOps |
| Observability fundamentals | A7.3 | A7. Architecture and system design |
| Operating systems and networking | A4.4 | A4. Cloud, infrastructure and DevOps |
| Programming fundamentals, data structures and algorithms | A8.1 | A8. Programming and software design |
| Relational modelling and SQL | A3.1 | A3. Data and databases |
| Reliability operations and recovery | A4.5 | A4. Cloud, infrastructure and DevOps |
| Secrets and supply-chain security | A5.3 | A5. Application security |
| Secure coding and the OWASP Top 10 | A5.1 | A5. Application security |
| Server-side programming | A2.1 | A2. Back-end and APIs |
| Software design and refactoring | A8.2 | A8. Programming and software design |
| System design and distributed systems | A7.1 | A7. Architecture and system design |
| Version control and code review | A6.2 | A6. Software quality and testing |
| Web fundamentals and TypeScript | A1.1 | A1. Front-end engineering |

### Optional (six: three to L3 and three to L2)

The options are the Tier B competencies, in four sub-groups, one for each specialisation. Each agentic domain belongs to one specialisation, and so does every competency in it.

**Forward-deployed delivery** (9: domain B9). Carries a customer's problem through to a system the customer operates (the forward-deployed engineer postings at OpenAI and Palantir): discovery, process analysis, integration with the customer's systems, prototyping, delivery, communication, adoption and measured outcomes.

| Competency | Code | Domain |
|---|---|---|
| Adoption, handover and operational ownership | B9.8 | B9. Forward-deployed delivery |
| Business and problem discovery | B9.1 | B9. Forward-deployed delivery |
| Customer systems and enterprise integration | B9.3 | B9. Forward-deployed delivery |
| Delivery and scope management | B9.6 | B9. Forward-deployed delivery |
| Outcome measurement and delivery economics | B9.9 | B9. Forward-deployed delivery |
| Platform fit, configuration and reuse | B9.4 | B9. Forward-deployed delivery |
| Process analysis and task allocation | B9.2 | B9. Forward-deployed delivery |
| Prototyping and assumption testing | B9.5 | B9. Forward-deployed delivery |
| Stakeholder communication and decision ownership | B9.7 | B9. Forward-deployed delivery |

**Agent application** (7: domains B1, B2 and B8). Builds the agent a person works with: intent and specification, context, retrieval and memory, agent-assisted delivery and the human surface.

| Competency | Code | Domain |
|---|---|---|
| Agent UX and human-in-the-loop interfaces | B8.2 | B8. Agentic software delivery and the human surface |
| Agent-assisted software development | B8.1 | B8. Agentic software delivery and the human surface |
| Context engineering | B2.1 | B2. Context, retrieval and memory |
| Memory and state | B2.3 | B2. Context, retrieval and memory |
| Outcome and acceptance specification | B1.1 | B1. Intent and specification |
| Retrieval and agentic search | B2.2 | B2. Context, retrieval and memory |
| Spec-driven development and living documentation | B1.2 | B1. Intent and specification |

**Agent platform and harness** (8: domains B3 and B4). Builds the harnesses, loops, orchestration and the tool and protocol layer that others build on.

| Competency | Code | Domain |
|---|---|---|
| Architecture pattern selection | B4.1 | B4. Architecture, harness and orchestration |
| Autonomous loop design | B4.3 | B4. Architecture, harness and orchestration |
| Computer-use and browser agents | B3.3 | B3. Tools and protocols |
| Harness engineering | B4.2 | B4. Architecture, harness and orchestration |
| Model selection, control and adaptation | B4.5 | B4. Architecture, harness and orchestration |
| Protocol integration | B3.2 | B3. Tools and protocols |
| Tool and interface design | B3.1 | B3. Tools and protocols |
| Workflow and multi-agent orchestration | B4.4 | B4. Architecture, harness and orchestration |

**Agent reliability and security** (9: domains B5, B6 and B7). Evals and verification gates, injection-resistant design, permissions and sandboxing, and running agents in production: observability, reliability, cost and deployment.

| Competency | Code | Domain |
|---|---|---|
| Agent threat modelling and injection-resistant design | B6.1 | B6. Security, safety and governance |
| Cost and latency engineering | B7.3 | B7. Production operations |
| Deployment, versioning and runtimes | B7.4 | B7. Production operations |
| Error analysis and failure taxonomy | B5.1 | B5. Evaluation and verification |
| Graders and LLM-as-judge | B5.2 | B5. Evaluation and verification |
| Identity, permissions and sandboxing | B6.2 | B6. Security, safety and governance |
| Observability and trajectory debugging | B7.1 | B7. Production operations |
| Reliability and durable execution | B7.2 | B7. Production operations |
| Verification gates and regression | B5.3 | B5. Evaluation and verification |

**Choosing options.** The selection rule covers the whole Optional list; the sub-groups say where each option belongs, and a person may choose within one or across them.

- **A specialist** takes all six from one specialisation.
- **A generalist** takes options from all four, so that nothing in the agentic tier is missing end to end.

**Roles that need more.** The pathway is the minimum for the title. A role that needs more is written as a job spec from the same competencies, each with its own required level: a full-stack generalist with every agentic competency at L2; a specialist with Tier A depth as well (front end for agent applications; back end, containers and CI/CD for platform work; security and testing for reliability work); a senior post. Every L3 still needs evidence of guiding others. The pathway sets nothing at L4. Three such roles are written out under "Roles as job specs".

## Roles as job specs

The pathway describes one title. Three related roles are written as job specs, because each draws on competencies from several groups and sub-groups, and a sub-group cannot hold that: every competency sits in exactly one. The roles are not rungs of seniority, and one person can hold all three.

A job spec puts competencies in three sections, each at its own level: **Mandatory** (one below its level fails the role, whatever the totals), **Core** (counted for breadth and depth) and **Optional** (extra credit only). To score a graph against a role, copy the spec into the job specs file with each competency written as `Chan AFSE: <competency>`; `references/dashboard.md` §5 has the format and the scoring.

### Full-stack developer

Builds and ships an application across every layer, and knows enough of operations and security to see a risk and trace a failure. It sits below the pathway on eight operations and architecture competencies (L1) and asks nothing of the agentic tier. (31 competencies; spec id `full-stack-developer`.)

| Section | Level | Competencies |
|---|---|---|
| Mandatory | L2 | Programming fundamentals, data structures and algorithms; Web fundamentals and TypeScript; Server-side programming; API design; Relational modelling and SQL; Automated testing; Version control and code review; Secure coding and the OWASP Top 10; CI/CD and release engineering |
| Core | L2 | Component frameworks and state; Accessibility, responsive design and design systems; Software design and refactoring; Data modelling and semantics; Document, key-value and vector stores; Authentication and session management; Authorisation and data protection; Secrets and supply-chain security; Asynchronous and event-driven services; Concurrency, consistency and idempotency; Debugging and performance profiling; Containers and runtime platforms |
| Core | L1 | Operating systems and networking; Infrastructure as code and cloud services; System design and distributed systems; Architecture decisions and documentation; Observability fundamentals; Reliability operations and recovery; Data pipelines and data quality; Data governance and privacy |
| Optional | L1 | Business and problem discovery; Outcome and acceptance specification |

### Forward-deployed engineer (senior, AI deployments)

Carries a customer's problem through to a working system the customer operates. It follows the two OpenAI postings, which are senior roles: owning discovery and delivery is Mandatory at L3, and two AI competencies are Core (the posting asks for experience of how model behaviour affects the product, and for eval-driven feedback). The rest of the AI layer is Optional because it depends on the product deployed. A forward-deployed role on a product with no AI in it would drop the two AI rows. (39 competencies; spec id `forward-deployed-engineer`.)

| Section | Level | Competencies |
|---|---|---|
| Mandatory | L3 | Business and problem discovery; Delivery and scope management |
| Mandatory | L2 | Customer systems and enterprise integration; Prototyping and assumption testing; Stakeholder communication and decision ownership; Adoption, handover and operational ownership; Server-side programming; Data pipelines and data quality; Automated testing; Authorisation and data protection |
| Core | L2 | Process analysis and task allocation; Platform fit, configuration and reuse; Outcome measurement and delivery economics; Model selection, control and adaptation; Error analysis and failure taxonomy; Component frameworks and state; Context engineering; Outcome and acceptance specification; Data modelling and semantics; Data governance and privacy; Programming fundamentals, data structures and algorithms; API design; Relational modelling and SQL; Authentication and session management; Secure coding and the OWASP Top 10; Version control and code review; CI/CD and release engineering; Debugging and performance profiling; Web fundamentals and TypeScript |
| Core | L1 | Reliability operations and recovery; Operating systems and networking; System design and distributed systems |
| Optional | L2 | Retrieval and agentic search; Tool and interface design; Workflow and multi-agent orchestration; Graders and LLM-as-judge; Agent threat modelling and injection-resistant design; Guardrails and human oversight; Protocol integration |

### Agentic solutions architect

Decides what the system may decide and do, what evidence it needs, and how its behaviour is controlled and verified. L3 sits on the design decisions; the rest is the depth needed to defend and validate a design. (35 competencies; spec id `agentic-solutions-architect`.)

| Section | Level | Competencies |
|---|---|---|
| Mandatory | L3 | Process analysis and task allocation; Architecture pattern selection; Outcome and acceptance specification; Tool and interface design; Identity, permissions and sandboxing; Guardrails and human oversight; Verification gates and regression |
| Core | L3 | System design and distributed systems; Data modelling and semantics |
| Core | L2 | Agent threat modelling and injection-resistant design; Business and problem discovery; Customer systems and enterprise integration; Prototyping and assumption testing; Adoption, handover and operational ownership; Outcome measurement and delivery economics; Architecture decisions and documentation; Retrieval and agentic search; Model selection, control and adaptation; Context engineering; Memory and state; Workflow and multi-agent orchestration; Reliability and durable execution; Error analysis and failure taxonomy; Graders and LLM-as-judge; Agent UX and human-in-the-loop interfaces; Observability and trajectory debugging; Deployment, versioning and runtimes; Cost and latency engineering; Responsible AI and regulatory compliance; Data governance and privacy |
| Optional | L2 | Harness engineering; Autonomous loop design; Protocol integration; Stakeholder communication and decision ownership; Platform fit, configuration and reuse |

## Mapping to other references

- **SFIA 9:** Tier A maps to PROG, SWDN, HCEV, DBDS, DENG, ITOP, RELM, SCTY, SCAD, TEST and ARCH; Tier B to MLNG, AIDE, ARCH, TEST, SCTY and RELM (SFIA has no agent skill).
- **SFIA 9 skills behind the 2026.4 competencies** (read November 2026; names and levels are cited, the wording is not copied): B9.1 Business situation analysis, Requirements definition and management, Consultancy; B9.2 Business process improvement, Business modelling; B9.3 Systems integration and build; B9.4 Product management; B9.5 Feasibility assessment; B9.6 Delivery management; B9.7 Stakeholder relationship management; B9.8 Organisational change management, Service acceptance; B9.9 Benefits management; A8.1 Programming/software development; A8.2 Software design; A3.4 Data modelling and design; A3.5 Data management; A4.4 Network support; A4.5 Incident management, Availability management, Continuity management. SFIA defines Stakeholder relationship management and Consultancy from level 4 and Solution architecture at levels 4 to 6, so the L1 and L2 rows of B9.7 have no SFIA counterpart. SFIA has no skill for A7.4; Computer Science Curricula 2023 (ACM, IEEE-CS and AAAI) covers its topics in the operating systems, parallel and distributed computing and data management areas (race conditions, thread safety, deadlock, isolation levels, ordering, consistency and idempotency), without level wording. https://csed.acm.org/ https://sfia-online.org/en/sfia-9/skills
- **Certifications (all about L2):** Claude Certified Architect – Foundations, AWS Generative AI Developer – Professional (AIP-C01), Microsoft AI-103, NVIDIA NCP-AAI, Linux Foundation MCPA, Databricks Generative AI Engineer. Evaluation is the least tested domain in every exam.
- **Role references for B9 and the job specs (read November 2026):** OpenAI, Forward Deployed Engineer (FDE) and Forward Deployed Software Engineer postings; Anthropic, Forward Deployed Engineer posting; Palantir, Forward Deployed Software Engineer posting; Microsoft, Exam AB-100 study guide, Agentic AI Business Solutions Architect (skills as of 16 November 2026); Anthropic, Building effective agents (December 2024); Google, Site Reliability Engineering, "Managing incidents" (for A4.5); a16z, "Trading Margin for Moat" (why thin integrations to legacy systems of record fail, for B9.3).
- **Front-end and full-stack references for Tier A:** roadmap.sh full-stack and front-end roadmaps, the OWASP Top 10 (2021) and ASVS, WCAG 2.2.

## Changes in 2026.6

- **One Mandatory list for the agentic field.** A rule set on 2026-11-14 makes Mandatory the list shared by every pathway in a field, as all RICS APC pathways share their mandatory competencies, and Core the baseline of one pathway only. Chan AFSE and Chan AGEN are both pathways of the agentic field (`field: agentic` in the catalog) and now list the same five Mandatory competencies, with the same levels and level wording: AI disclosure and use boundaries (L2), Guardrails and human oversight (L2), Privacy and data protection in AI use (L2), Responsible AI and regulatory compliance (L1) and Verification of agent output (L2). A test holds the two lists together.
- **What moved.** Five competencies went from Mandatory to Core, where they are still required of every agentic full-stack engineer at L2: A5.1 Secure coding and the OWASP Top 10, A5.2 Authorisation and data protection, A5.3 Secrets and supply-chain security, A6.1 Automated testing and A6.2 Version control and code review. B6.4 Responsible AI and regulatory compliance stays Mandatory, unchanged.
- **Three new rows, all Mandatory:** B5.4 Verification of agent output, B6.5 AI disclosure and use boundaries and B6.6 Privacy and data protection in AI use. B6.3 Guardrails and human oversight is reworded for any field; its engineering detail (schema validation, policy as code) is now this pathway's examples.
- **Counts.** 67 competencies (64 in 2026.5): Mandatory 5 (was 7), Core 29 (was 24), Optional 33.
- **Overlaps left in place.** B5.4 is the baseline habit under B5.1 to B5.3; B6.6 sits beside A5.2 (personal data in the application) and B6.2 (secrets kept out of context).
- **Sources.** A7.4 now cites Computer Science Curricula 2023 for its topics, and B9.3 cites a16z.
- **Not yet reviewed.** The shared list and its wording have had no outside review.

## Changes in 2026.5

- **Wording only.** No competency is added, removed or regrouped; the counts are those of 2026.4.
- **Sixteen cells reworded** after reading SFIA 9, Google's SRE book and Anthropic's forward-deployed engineer posting against the 2026.4 rows: B9.1 (L2, L3), B9.2 (L2, L3), B9.3 (L2, L3), B9.6 (L2, L3), B9.8 (L2, L3, L4), B9.9 (L2, L3), A3.5 (L2), A4.5 (L3) and A8.2 (L3). Each adds what a published source expects at that level: requirement traceability and root-cause analysis in discovery, a process model in B9.2, integration testing in B9.3, acceptance criteria agreed with the customer's operators in B9.8, and results compared with the business case in B9.9.
- **Sources for B9.** Two of the three parts that 2026.4 listed as unsourced now have a primary source: workflow mapping in B9.2 (SFIA Business process improvement and Business modelling) and handover in B9.8 (SFIA Service acceptance and Organisational change management). The integration detail in B9.3 is partly supported (SFIA Systems integration and build; the Anthropic posting). A7.4 still has no published level wording behind it.
- **Job specs.** Forward-deployed engineer gains Context engineering (Core, L2) and Protocol integration (Optional, L2), both from Anthropic's posting. Agentic solutions architect gains Platform fit, configuration and reuse (Optional, L2), from NVIDIA's posting for the role.
- **Mandatory list not yet aligned.** A rule set on 2026-11-14 makes Mandatory the list shared by every pathway in a field, and Core the baseline of one pathway only. Chan AFSE and Chan AGEN are both in the agentic field and do not yet share a Mandatory list; that regrouping is proposed separately.
- **Not yet reviewed.** As for 2026.4.

## Changes in 2026.4

- **Why.** The framework was checked against descriptions of three roles: full-stack developer, forward-deployed engineer and agentic solutions architect. Nine of the 26 full-stack domains had no competency of their own; fourteen forward-deployed domains rested on B1.3 alone; the architect's gaps were the same ones.
- **Seven new Tier A competencies, all Core at L2:** A3.4 Data modelling and semantics, A3.5 Data governance and privacy, A4.4 Operating systems and networking, A4.5 Reliability operations and recovery, A7.4 Concurrency, consistency and idempotency, and a new domain, A8 Programming and software design (A8.1 Programming fundamentals, data structures and algorithms; A8.2 Software design and refactoring).
- **Wider wording in four rows;** names and codes unchanged. A1.1 (L1, L2: browser behaviour), A3.3 (L2, L3: source profiling, reconciliation, schema change), A4.2 (L1 to L3: build systems, pinned dependencies, migration sequencing) and A6.3 (L3: load testing).
- **New domain B9, Forward-deployed delivery:** nine competencies, all Optional (B9.1 to B9.9).
- **B1.3 Problem translation and deployment delivery is retired.** B9 unpacks it. Its code is not reused, and B1 is renamed Intent and specification. A graph competency mapped to B1.3 needs a new mapping to whichever B9 competency its evidence shows.
- **Four Optional sub-groups replace three.** Forward-deployed delivery (9) is new, and Agent application and forward-deployed becomes Agent application (7). Agent platform and harness (8) and Agent reliability and security (9) are unchanged, and so is the rule: six options, three to L3 and three to L2.
- **Counts.** 64 competencies (49 in 2026.3): Mandatory 7, Core 24 (was 17), Optional 33 (was 25).
- **Three roles as job specs:** full-stack developer, forward-deployed engineer (senior, AI deployments) and agentic solutions architect. The architect role draws on every agentic domain, which a sub-group cannot hold.
- **Sources.** The three role descriptions were AI-written syntheses; they were used as a coverage checklist and are not cited. The new rows were checked against the postings and guides listed under "Mapping to other references". No primary source supports workflow mapping in B9.2, the integration detail in B9.3 or handover in B9.8: they rest on the syntheses and on the author's own delivery practice.
- **Overlaps left in place.** Idempotency and isolation still appear in the L3 cells of A2.2, A2.4, A3.1 and B7.2; A7.4 names the skill once. A7.3 is about seeing a system and A4.5 about recovering it, though A7.3's L3 mentions on-call. A3.5 holds what data may be kept and for how long; A5.2 stays on access and encryption, and B6.4 on the rules specific to AI. B9.2 allocates a business process between code, a model, an agent and a person; B4.1 chooses the technical pattern for the AI part.
- **Business and industry knowledge is not a competency here.** B9.1 is the skill of learning a customer's business. The knowledge itself belongs to a domain framework, which a job spec can name beside this one.
- **Not yet reviewed.** The additions, the grouping and the job specs have had no outside review, and the catalog marks the framework as a draft.

## Changes in 2026.3

- **One pathway replaces four.** Full-stack generalist, Agent application and forward-deployed, Agent platform and harness and Agent reliability and security each restated all 49 competencies at a different level, grouped by depth (Specialism, Shared foundation, Awareness). The single pathway, Agentic full-stack engineer, lists each competency once, as Mandatory, Core or Optional. The three specialisms are now the sub-groups of Optional, and the senior-role rule is replaced by job specs.
- **Competencies and descriptors:** unchanged. All 49 keep their names and their L1–L4 wording.
- **How the groups were drawn.** By tier. Tier A, the full-stack software foundation, is required of everyone: five of its competencies as Mandatory (A5.1, A5.2, A5.3, A6.1, A6.2) and the other seventeen as Core. Tier B, agentic engineering, is where a person specialises: B6.3 Guardrails and human oversight and B6.4 Responsible AI and regulatory compliance are Mandatory, and the other 25 are Optional, each in the specialisation that owns its domain (B1, B2 and B8: Agent application and forward-deployed; B3 and B4: Agent platform and harness; B5, B6 and B7: Agent reliability and security). The rule used for Chan CXMDS (Optional is what some pathway held only at L1) does not carry over: every 2026.2 pathway held 36 of the 49 at L2 or above, which would leave eleven options.
- **Levels, against the 2026.2 generalist.** Mandatory and Core keep the generalist's level: L2, and L1 for B6.4 Responsible AI and regulatory compliance. Moved from required to Optional: 25 Tier B competencies (24 the generalist held at L2, and B3.3 Computer-use and browser agents at L1). L3 is now reached through three chosen options; the generalist had none.
- **Levels, against the 2026.2 specialisms.** Raised from L1 to L2, now Core: A1.1, A1.2, A1.3 (front end) for Agent reliability and security, and A4.1, A4.2, A4.3 (cloud and DevOps) for Agent application and forward-deployed. Each specialism's L3 competencies that are now Mandatory or Core are held at L2 (B6.4 at L1) and are not options (Agent application and forward-deployed: A1.1, A1.2, A1.3; Agent platform and harness: A2.1, A2.2, A2.4, A4.1, A4.2, A7.1; Agent reliability and security: A5.1, A5.2, A5.3, A6.1, A6.2, A6.3, B6.3, B6.4); a role that needs one at L3 says so in a job spec. B7.1 Observability and trajectory debugging, B7.2 Reliability and durable execution and B7.4 Deployment, versioning and runtimes were L3 for both Agent platform and harness and Agent reliability and security and sit with Agent reliability and security, which owns domain B7.
- **Not yet reviewed.** The grouping has not been reviewed.

## Use in the competency graph

This is the level guide for the library framework `chan-afse`; its requirements are in `chan-afse.csv` beside this file, on the L1–L4 scale. Competencies that match carry `externalRef: "Chan AFSE 2026: <competency>"`. Select it under `frameworks:` in `competency-graph.yaml` (`frameworks.py list --all` shows the pathway), and the dashboard's Competency frameworks tab lists it. When rating a competency against it, read that competency's row in the tables above: each column says what the evidence must show at that level.
