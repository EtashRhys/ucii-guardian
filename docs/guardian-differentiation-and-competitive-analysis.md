# UCII Guardian — Differentiation and Competitive Analysis

## Purpose

This document defines why UCII Guardian is architecturally different, why those differences matter, and which claims are appropriate for the hackathon demo, README, Devpost submission, architecture material, judge Q&A, and later product positioning.

It separates three kinds of statements:

1. **Demonstrated Guardian facts** — behavior already proven by the running Guardian + UCII system.
2. **Best-practice architectural arguments** — why the design is safer or cleaner than common alternatives.
3. **External competitive comparisons** — claims about other systems grounded in current public sources and explicitly bounded where evidence is incomplete.

Do not collapse these categories. Guardian does not need an unsupported "first ever" claim to be differentiated.

## Core differentiation thesis

> **UCII Guardian does not ask the model to be its own authority.**

The model interprets human intent and proposes actions. Independent cryptographic infrastructure determines whether that exact consequential action is currently authorized. The protected executor requires that independent result before execution can occur.

Guardian therefore separates:

```text
identity
!= authentication
!= delegated action authority
!= one-off human approval
!= economic/payment permission
!= execution
!= provenance
```

This separation is the foundation of the product.

## Why this is better practice

### 1. External enforcement is stronger than prompt-enforced permission

A prompt such as "never spend more than $80" is useful behavioral guidance, but it leaves the probabilistic model responsible for interpreting and obeying its own security boundary.

Guardian instead permits the model to propose an action and then evaluates consequential permission outside the model's reasoning loop.

**Why this is better:** prompt injection or reasoning error cannot itself manufacture authority; model output is a proposal rather than a permission grant; enforcement remains deterministic at the protected execution boundary; changing models does not require moving the authority boundary into the new model; and policy failure and model failure become separable operational events.

### 2. Identity should not imply authority

Knowing which principal is acting does not answer what that principal may do. Guardian deliberately supports:

```text
UCII_VERIFIED
+ REVOKED
+ DENY
```

The agent remains cryptographically identifiable while its delegated action authority is gone. This permits least-privilege permission lifecycle changes without destroying identity or attribution.

### 3. Revoking authority is cleaner than killing the agent

Guardian/UCII revokes the specific delegated authority record while preserving identity and historical evidence. Continued permission requires a fresh legitimate authority grant rather than silently restoring a revoked record.

### 4. One-time human judgment should not silently broaden standing authority

Guardian's `APPROVE_ONCE` is bound to the exact pending exceptional request and does not mutate standing delegated authority. Exceptions therefore do not become permanent privileges, and replay cannot create repeated execution.

### 5. Fresh authority evaluation is stronger than cached trust

The relevant question is:

> **Is this exact principal currently authorized for this exact consequential action?**

Guardian re-evaluates authority after revocation rather than reusing stale `ALLOW` state.

### 6. Authorization should be structurally required by the executor

Guardian's protected executor requires action-bound authorization evidence before a side effect can occur. Authorization is therefore an enforcement prerequisite, not advice the agent may ignore.

### 7. Payment capability should not imply action authority

UCII keeps economic policy/x402 separate from delegated action authority. Ability to pay or successful settlement cannot silently become permission to perform the underlying action.

### 8. Provenance should reconstruct causality, not merely log a final result

Guardian records request, identity verification, authority decision, escalation/human judgment, execution/refusal, and revocation-related outcomes so a human can determine what happened and why.

## Guardian's most important demonstrated separations

### Identity / Authority / Execution

```text
Guardian Decision | Authority | Execution
```

Before revocation:

```text
ALLOW | ACTIVE | Completed
```

After revocation:

```text
DENY | REVOKED | No execution
```

Meanwhile provenance can still show `IDENTITY_VERIFIED`.

> **Who the agent is, what it may do, and whether an action actually happened are separate facts.**

### Standing authority / human exception

```text
ACTIVE -> ALLOW -> EXECUTE
```

versus:

```text
NOT_GRANTED -> ESCALATION_REQUIRED -> APPROVE_ONCE -> EXECUTE ONCE
```

After the exceptional action, standing authority remains `NOT_GRANTED`.

### Identity / revocation

```text
same Guardian identity
+ same valid identity credential
+ same class of requested action
+ changed delegated-authority state
= different execution outcome
```

This isolates authority as the controlling variable.

## Broader UCII differentiation beneath Guardian

### Universal actor model

UCII is designed as common identity infrastructure for humans, AI agents, robots, devices, services, and organizations. Guardian is one AI-agent application on top of that broader substrate.

### Post-quantum-capable cryptographic substrate

Guardian uses real UCII cryptographic identity infrastructure rather than a mock trust flag. PQC is an important property, but the hackathon story should emphasize the complete working authority lifecycle rather than reducing UCII to "uses PQC."

### Economic dimension as an independent plane

UCII can express economic interaction separately from identity and action authority. Guardian's first-party entitlement demonstrates that economic infrastructure access does not create controller, action, approval, or execution authority.

## Common alternative patterns and Guardian's response

| Common pattern | Limitation | Guardian/UCII approach | Practical benefit |
|---|---|---|---|
| Prompt tells agent what it may do | Probabilistic self-policing | External deterministic authority check | Model error cannot grant permission |
| Valid identity token implies access | Identity and authorization become conflated | Separate identity and delegated action authority | Revoke permission without destroying identity |
| Revoke credential or shut down process | Excessive blast radius | Revoke exact delegated authority | Least-privilege lifecycle control |
| Human exception expands role/scope | Exception may become reusable privilege | Exact `APPROVE_ONCE` | Human exception stays one-time |
| Cache previous authorization | Revocation may not take effect | Fresh authoritative check | Revocation changes next execution decision |
| Policy engine gives advice | Agent may bypass policy | Protected executor requires evidence | Enforcement is structural |
| Wallet/payment proves legitimacy | Payment confused with permission | Economic state separate from action authority | Paying does not authorize action |
| Current status only | Weak forensic context | Lifecycle provenance | Reconstruct cause and responsibility |
| Agent-specific identity silo | Different principals require separate trust stacks | Universal UCII actor model | Common infrastructure across actor classes |

# Researched competitive landscape — September 2026

## Research rules

This section records what current public sources actually establish. Absence of a feature from public documentation is recorded as **not established from reviewed sources**, not as proof the feature does not exist.

Competitors are not all equivalent categories. AstraCipher is primarily an agent identity/trust protocol and product stack; AITH is a research protocol for human-to-AI continuous delegation; KXCO is a sponsored machine-identity/on-chain action stack; MAGIQ is a research framework for PQ-secure multi-agent communication governance; HBHC is a specialized hierarchical credential-revocation protocol. OAuth and SPIFFE are important adjacent baselines rather than direct Guardian competitors.

## AstraCipher

**Reviewed public sources (September 2026):** SSRN paper *AstraCipher: A Post-Quantum Cryptographic Identity Protocol for Autonomous AI Agents*; official AstraCipher site/documentation.

**Problem:** verifiable identity, capability bounding, delegated trust, auditability, and cross-protocol interoperability for autonomous AI agents.

**Identity model:** W3C Decentralized Identifiers. Each agent receives a DID and hybrid verification methods.

**Cryptography:** ML-DSA-65 + ECDSA P-256 hybrid signatures and ML-KEM-768 key encapsulation.

**Authorization/delegation:** W3C Verifiable Credentials encode capabilities, resource/action permissions, trust levels and rate limits. Trust chains support Creator -> Authorizer -> Agent -> Sub-agent, delegation-depth limits, and capability intersection/monotonic attenuation.

**Verification:** credentials can be verified offline. Public documentation exposes `hasPermission`-style checks and verification checks including structure, expiration, signature and revocation.

**Revocation:** revocation checking is clearly part of credential verification in official material. The reviewed public material does not establish the same Guardian-specific distinction between revoking an independent delegated-action authority record and preserving a separately valid agent identity credential; do not claim AstraCipher lacks such semantics without deeper source-code verification.

**Audit:** official material describes cryptographically signed append-only audit logs, DID attribution, and tamper-evident chain hashing.

**Integrations:** MCP server, Google A2A adapter, Python SDK and CLI. The paper reports 92 unit tests and 67 end-to-end tests and sub-100ms identity operations.

**Actor scope:** official positioning is purpose-built around AI-agent identity. Its trust model includes creators/authorizers/sub-agents, but the reviewed public identity product is not presented as a universal identity substrate for humans, organizations, services, devices and agents in the same UCII taxonomy.

**Major overlap with UCII/Guardian:** PQ agent identity, capability-bounded authorization, delegated trust, revocation checking, auditability, MCP/A2A interoperability and developer SDKs.

**Meaningful Guardian/UCII distinctions supported by current evidence:** UCII's broader actor taxonomy; Guardian's demonstrated independent identity/delegated-action-authority/execution states; exact `APPROVE_ONCE` exceptional-action semantics that leave standing authority unchanged; protected consequential executor as part of the demonstrated application lifecycle; and UCII's independent economic/x402 plane. AstraCipher's public material is stronger than Guardian today in DID/VC standards alignment, MCP/A2A packaged integrations, compliance modules, and developer-facing quick-start polish. These are lessons, not weaknesses to dismiss.

**Claims Guardian must not make:** first PQ identity for AI agents; first PQ capability-bounded agent credentials; first delegated agent trust chain; first agent revocation/audit system; first MCP/A2A cryptographic identity layer.

**Lesson for UCII:** AstraCipher makes adoption look extremely easy. UCII should compete aggressively on time-to-first-authorized-action, SDK ergonomics, adapters, and documentation while preserving Guardian's stricter domain separation.

## AITH — AI Trust Handshake

**Reviewed public source:** 2026 paper *AITH: A Post-Quantum Continuous Delegation Protocol for Human-AI Trust Establishment*.

AITH is the **closest conceptual neighbor** to Guardian in this review.

**Problem:** bounded, revocable and auditable human-to-AI authority for continuously operating probabilistic agents.

**Identity model:** notably different from UCII. The AITH paper models the AI agent by a SHA-256 hash of model weights and explicitly states that the AI agent does **not** possess a private key. A provider issues attestation certificates binding runtime configuration to that model hash. The human principal owns the ML-DSA key.

**Cryptography:** a human signs a Continuous Delegation Certificate once using ML-DSA-87. Routine operations then use deterministic boundary checks rather than per-operation PQ signatures.

**Delegation:** the certificate encodes delegation level, multidimensional constraints, escalation triggers, temporal validity and registered target systems.

**Boundary engine:** six ordered checks cover certificate validity/agent identity, delegation level, boundary constraints, rate limits, anomaly detection and escalation. The paper reports roughly 0.21 microsecond boundary comparison and 4.7 million operations/second on one core after certificate issuance.

**Human escalation:** AITH explicitly supports human escalation. Trigger classes include threshold, novelty and composition. Human responses are `APPROVE`, `DENY`, or `MODIFY`; timeout auto-denies.

**Revocation:** push-based revocation sends signed invalidation to registered target systems with immediate, graceful and partial/tightening modes. The paper targets propagation under one second.

**Audit:** a three-tier SHA-256 Responsibility Chain records AI decision logs, human confirmation logs for escalations, and system execution logs.

**Formal assurance:** five core properties are reported as machine-verified in Tamarin under the Dolev-Yao model. The authors also report multi-model adversarial auditing and a 100,000-operation simulation with 79.5% autonomous, 6.1% escalated and 14.4% blocked outcomes.

**Major overlap with Guardian:** external deterministic boundary enforcement, high autonomous throughput inside human-defined bounds, human escalation, revocation, audit/responsibility attribution, PQC, and explicit rejection of the idea that probabilistic AI should enforce its own authority boundary.

**Important differences:**

- AITH binds the agent to a model-weight hash and gives the AI no private key; Guardian is a cryptographically credentialed UCII principal that proves possession of its own ML-DSA credential.
- AITH's authority is a human-signed Continuous Delegation Certificate; Guardian separates UCII identity credential from a separately lifecycle-managed delegated action-authority record.
- AITH allows human `APPROVE`, `DENY`, or `MODIFY`. The reviewed paper does not establish Guardian's exact semantic guarantee that `APPROVE_ONCE` executes one exact exceptional request while standing delegated authority remains `NOT_GRANTED` afterward. Do not claim AITH cannot implement one-shot approval; say that exact invariant is not established in the reviewed paper.
- AITH revocation includes partial tightening and graceful modes; Guardian intentionally makes revocation of a particular delegated-authority record permanent and requires fresh authority for renewed permission.
- AITH is a protocol/research system centered on human-AI delegation. Guardian is a working Strands application exercising UCII identity, delegated authority, protected execution, human one-off approval, revocation and provenance against live infrastructure.
- UCII extends beyond the human-AI relationship to multiple actor classes and has a separate economic/x402 dimension.

**Claims Guardian must not make:** first external deterministic boundary for probabilistic agents; first human-to-AI cryptographic delegation; first autonomous-within-bounds architecture; first human escalation; first PQ revocation; first responsibility/audit chain for bounded agents.

**Lessons for UCII:** AITH is stronger today on formal verification, quantified boundary-engine performance, explicit multidimensional constraints/rate limits/anomaly checks, and sub-second push revocation. Those are legitimate future UCII research/hardening directions. Guardian's strongest counter-position is not "AITH lacks boundaries"; it is the different principal model and the clean separation of persistent identity, independent action authority, exact one-off human judgment, execution, economics and provenance.

## kxco-pq-agent / KXCO machine identity

**Reviewed public sources:** official npm package documentation and KXCO developer documentation.

**Problem:** give LLMs, robots, IoT devices and automated processes institution-sponsored identity and constrained authority for regulated/on-chain operations.

**Identity model:** a KYC-verified institution sponsors a machine identity by signing the agent's ML-DSA-65 public key plus a locked capability scope. The agent then signs its own operations.

**Cryptography:** ML-DSA-65 machine identity; KXCO's broader PQ stack also exposes post-quantum primitives.

**Authorization:** sponsor-signed scope can include payment maximums, rolling daily caps, allowed recipients, attestation purposes, audit-log permission and credential-management permission. The relay validates sponsor credential and agent-signed intent and enforces scope server-side.

**Revocation:** package exposes on-chain agent credential revocation. To change scope, documentation says revoke and re-issue.

**Execution/economics:** unusually concrete. `AgentChainClient` exposes constrained on-chain actions such as transfers, attestations and audit-root anchoring. This is not merely identity metadata; the relay enforces scope on operations.

**Actor scope:** `llm`, `robot`, `iot`, and `process`; broader KXCO SDK includes human/institution identities.

**Major overlap with UCII/Guardian:** PQ machine identity, external sponsor, locked capabilities, signed operations, server-side scope enforcement, revocation, auditability, robots/IoT/process actors and economic operations.

**Meaningful distinctions:** KXCO is explicitly institution/KYC-sponsored and oriented toward regulated/on-chain activity. UCII's actor taxonomy and Guardian demo are not dependent on an institution-sponsored blockchain relay. Guardian also demonstrates human escalation and exact one-off approval as a separate authority domain, independent delegated-action revocation while identity remains valid, and general protected execution outside an on-chain-only framing. UCII's x402 plane is conceptually separate from action authority, whereas KXCO's published scope model directly includes payment capabilities within the sponsor credential.

**Claims Guardian must not make:** first PQ identity for robots/IoT/LLMs; first sponsor-bounded machine capability; first PQ signed agent operations; first revocable machine credential; first cryptographically bounded agent payment mechanism.

**Lessons for UCII:** KXCO demonstrates the value of highly concrete capability schemas, server-side enforcement and legal/institutional sponsorship. UCII should preserve the ability to support organizations/controllers without requiring every autonomous principal to fit one KYC-sponsored blockchain model.

## MAGIQ

**Reviewed public source:** 2026 paper *MAGIQ: A Post-Quantum Multi-Agentic AI Governance System with Provable Security*.

**Problem:** secure governance of agent-to-agent communication and interaction policies with accountability under post-quantum cryptography.

**System focus:** MAGIQ defines one-to-one agent sessions and one-to-many coordinating-agent sessions. A structured task message combines intent, payload, context and agent identity.

**Policy model:** public paper material describes cryptographic enforcement of communication/access-control policies including which agents may initiate/receive contact, limits on sessions, limits on task messages, and task-duration budgets.

**Cryptography/formal security:** quantum-resistant protocols with formal correctness/security modeling in the Universal Composability framework. The paper evaluates computation/communication overhead and compares against SAGA.

**Accountability:** message attribution ties agent communications back to users/owners.

**Revocation:** the reviewed MAGIQ material does not establish a Guardian/AITH-style revocation lifecycle. A July 2026 IETF draft surveying adjacent work states that MAGIQ provides no revocation; treat this as secondary evidence and verify against the MAGIQ paper before making a public categorical claim.

**Major overlap:** PQ agent governance, policy enforcement outside model reasoning, agent identity/accountability, bounded interactions, formal security.

**Meaningful differences:** MAGIQ is primarily multi-agent communication/session governance. Guardian is centered on consequential action authority and protected execution for an autonomous application, including human exceptional judgment and operational authority revocation. UCII also models non-agent actors and economic interactions. Conversely, MAGIQ currently has a much stronger formal-security story than Guardian because it supplies UC-framework proofs.

**Claims Guardian must not make:** first PQ governance framework for multi-agent systems; first cryptographic agent communication policy; first formally secured PQ agent governance.

**Lessons for UCII:** formal modeling matters. Long-term UCII work should consider formalizing domain separation and the authorization/execution invariants rather than relying only on tests and architecture prose.

## Heartbeat-Bound Hierarchical Credentials (HBHC)

**Reviewed public source:** 2026 paper *Heartbeat-Bound Hierarchical Credentials: Cryptographic Revocation for AI Agent Swarms*.

**Problem:** bound the "zombie agent" window when hierarchical agents/sub-agents continue using credentials after a parent/operator stops them.

**Mechanism:** child credential validity is tied to periodic signed parent heartbeat/liveness proofs. Verifiers use cached public keys and local clocks rather than a central revocation round trip. When heartbeats stop, descendant credentials become unusable within a bounded window under stated clock/key-custody assumptions.

**Scale/evidence:** paper reports 0.26 ms authentication, more than 18,000 verifications/second, testing from 10 to 10,000 agents, 0.71% end-to-end overhead in GPT-4o-mini tool-call experiments, zero post-revocation tool calls in the reported prompt-injection experiment, and cascading revocation across a 49-agent/four-level hierarchy.

**Major overlap:** cryptographic revocation, fail-closed tool use, hierarchical agents and external enforcement.

**Meaningful difference:** HBHC solves a specialized distributed liveness/cascading-revocation problem. Guardian/UCII currently revokes an explicit delegated action authority through an authoritative control plane and demonstrates identity remaining valid while action authority disappears. HBHC's parent-liveness approach is potentially complementary rather than mutually exclusive.

**Claims Guardian must not make:** first cryptographic agent revocation; first external revocation that survives prompt injection; first hierarchical/cascading agent revocation.

**Lesson for UCII:** if UCII later governs spawned agent swarms, deterministic bounded descendant revocation is a serious design problem worth studying. Do not bolt HBHC into Guardian during the hackathon.

## OAuth 2.0 — adjacent baseline

OAuth 2.0 is not an AI-agent competitor. RFC 6749 already separates resource owner, client, authorization server and resource server and enables limited delegated access. It therefore proves that delegated authorization itself is not novel.

Guardian's distinction is the composition for autonomous principals: cryptographic UCII identity, action-bound authority, current lifecycle evaluation, protected execution, one-off human exception, revocation and provenance. Do not say "OAuth cannot do authorization"; it is literally an authorization framework.

Bearer-token OAuth also illustrates why proof-of-possession and identity/authority separation matter: RFC 6750 notes that possession of a bearer token is sufficient to use it, whereas Guardian's UCII path cryptographically binds its principal/action proof.

## SPIFFE/SPIRE — adjacent workload-identity baseline

SPIFFE provides portable cryptographic workload identity across heterogeneous environments through SPIFFE IDs, SVIDs and the Workload API. SVIDs can be X.509, JWT and newer WIT forms and are used for workload authentication and secure channels.

SPIFFE is therefore a strong counterexample to any claim that cryptographic non-human/workload identity is novel. Its focus, however, is workload identity infrastructure, not Guardian's complete human-controlled consequential-action lifecycle.

SPIFFE documentation itself warns that assertions have trust-domain scope and interpretation. SPIRE's Delegated Identity API also explicitly notes that a delegate able to obtain another workload's SVID can impersonate that workload. These are useful reminders that identity issuance and delegated action authority are separate design concerns.

## Comparative matrix — current public evidence

Legend: **Yes** = explicitly established in reviewed source; **Guardian-specific** = demonstrated Guardian property; **Not established** = not established by reviewed public sources, not proof of absence; **Different model** = related feature exists but semantics materially differ.

| Capability | UCII Guardian | AstraCipher | AITH | KXCO | MAGIQ | HBHC |
|---|---|---|---|---|---|---|
| PQ cryptography | Yes | Yes | Yes | Yes | Yes | Different focus |
| Agent holds cryptographic identity key | Yes | Yes | No — model hash, human key | Yes | Agent identity exists; exact key model differs | Hierarchical credentials |
| Independent identity vs action-authority lifecycle | **Guardian-specific demonstrated separation** | Not established in same form | Different model | Scope bound to sponsored credential | Not established | Different model |
| External deterministic enforcement | Yes | Permission verification | Yes — six-check engine | Yes — relay | Yes — policy protocols | Yes — verifier freshness |
| Protected consequential executor demonstrated | Yes | Not established as core protocol invariant | Target verifier/system model | Yes for chain operations | Communication/task focus | Tool-call revocation experiments |
| Human escalation | Yes | Not established in reviewed core docs | Yes | Not established | Not established | Not core focus |
| Exact one-shot approval leaving standing authority unchanged | **Yes** | Not established | Not established in exact form | Not established | Not established | Not applicable |
| Operational revocation | Yes | Yes, credential revocation checking | Yes, push revocation | Yes, on-chain credential revocation | Not established in reviewed paper | Yes, heartbeat expiry/cascade |
| Revocation while same identity credential remains valid | **Yes, demonstrated** | Not established in same form | Different identity model | Credential revocation model | Not established | Different credential model |
| Provenance/audit | Lifecycle provenance | Signed append-only audit | Three-tier responsibility chain | Audit-root anchoring | Message attribution/accountability | Not primary focus |
| Economic/payment plane | Separate x402/economic domain | Not core | Not core | Payments are first-class scoped operations | Not core | Not core |
| Universal heterogeneous actor taxonomy | Human/AI/robot/device/service/org | AI-agent centered | Human + AI protocol | Human/institution + llm/robot/iot/process | Multi-agent | Agent swarm |
| MCP/A2A packaged integration | UCII has broader interoperability work; Guardian demo is Strands | Yes | Not core | Not core | Not core | Not core |
| Formal cryptographic/security proof | Not yet | Not established from reviewed material | Tamarin | Not established | UC framework | Protocol analysis/theoretical bound |
| Working Guardian-style product demo | **Yes** | Working SDK/platform/demo, different product | Research protocol/simulation | Working package/relay stack | Research framework | Research + LLM experiments |

## The most defensible differentiation statement

After comparing the closest public work, the strongest position is **not** that every Guardian primitive is individually novel. It is that Guardian demonstrates a particularly clean composition and domain separation:

> **A cryptographically identifiable autonomous principal can remain operational while an independent authority plane determines whether each consequential action may execute; routine authority stays autonomous, exceptional human approval stays one-off, revocation removes the specific standing authority without destroying identity, and provenance preserves the causal lifecycle.**

AITH overlaps strongly with the external-boundary/autonomy/escalation/revocation idea. AstraCipher overlaps strongly with PQ identity/capability/delegation/audit. KXCO overlaps strongly with PQ machine identity, server-enforced scope and economic operations. MAGIQ overlaps strongly with PQ governance and formal policy enforcement. HBHC overlaps strongly with operational revocation.

Guardian's story survives all of those comparisons because its demonstrated value is the **composition**, the **separation of authority domains**, and the **working cause-and-effect application**.

## Where competitors are currently stronger

Competitive analysis should improve UCII rather than merely produce marketing language.

- **AstraCipher:** standards packaging (DID/VC), MCP/A2A adapters, compliance modules, quick-start developer UX.
- **AITH:** formal verification, quantified performance, rich constraint engine, anomaly/rate-limit semantics, sub-second push revocation.
- **KXCO:** concrete institutional sponsorship, constrained payment/action schemas, on-chain enforcement and audit anchoring.
- **MAGIQ:** formal UC security treatment and multi-agent communication policy budgets.
- **HBHC:** deterministic hierarchical/cascading revocation under distributed conditions.

UCII should study these strengths after the hackathon rather than pretending they do not exist.

## Where Guardian/UCII should press its advantage

1. **Make identity / authority / execution separation impossible to miss.**
2. **Keep `APPROVE_ONCE` truly one-shot and non-mutating.**
3. **Make revocation a visible human control that preserves identity.**
4. **Keep protected execution structurally downstream of authority.**
5. **Preserve economic authorization as a separate domain.**
6. **Use UCII's broader actor model rather than narrowing to LLMs.**
7. **Turn the complete lifecycle into an SDK/reference integration developers can adopt quickly.**
8. **Measure Time to First Authorized Action and drive it from days to hours/minutes.**
9. **Add formal analysis over time for the domain-separation and fail-closed invariants.**
10. **Build adapters without compromising UCII's public-boundary/self-hosting model.**

## Why Guardian is not merely "RBAC for an LLM"

The working composition includes cryptographically established agent identity, action-bound signed requests, externally evaluated current delegated authority, fail-closed lifecycle mapping, protected consequential execution, exceptional human judgment that does not create standing authority, permanent revocation of a specific delegated authority, fresh post-revocation checks, and causal provenance.

The important question is:

> **Does this identified autonomous principal currently possess authority for this exact consequential action under the applicable constraints?**

## Why Guardian is not merely an "AI safety wrapper"

Guardian does not claim to ensure every model thought, plan or output is correct or benevolent. It establishes a hard operational boundary around consequential action:

> **The model may remain probabilistic; consequential authority does not have to be.**

## Hackathon differentiation hierarchy

If presentation time is limited, emphasize:

1. **The LLM cannot grant itself authority.**
2. **Identity, authority, and execution are separate facts.**
3. **Routine authorized work stays autonomous.**
4. **Exceptional work uses exact `APPROVE_ONCE`, not privilege expansion.**
5. **Human revocation removes authority without destroying identity.**
6. **The same request after revocation is freshly checked and denied.**
7. **Provenance explains the complete lifecycle.**
8. **UCII generalizes beyond AI agents to other actor classes.**
9. **Economic permission remains separate from action authority.**
10. **PQC strengthens the substrate but is not the only value proposition.**

## Claims appropriate for the demo

> **UCII Guardian demonstrates how an autonomous AI can operate without ever possessing unlimited authority.**

> **Capability is not authority.**

> **The model proposes the action; independent cryptographic infrastructure decides whether it is authorized to execute.**

> **A human can revoke the agent's standing authority without destroying the agent's identity.**

> **One-time human approval does not silently become permanent agent authority.**

> **Identity, authority, execution, and provenance remain separate, auditable facts.**

## Claims to avoid

Do not claim "first cryptographic identity system for AI agents," "first post-quantum AI-agent authorization system," "first revocable agent delegation system," "only system that separates identity and authority," "solves AI alignment," "prevents all rogue-agent behavior," "guarantees safe AI," or "better than every competing system."

## Best-practice standard Guardian should aim to establish

```text
identify the principal
-> authenticate cryptographically
-> bind the exact proposed action
-> evaluate current delegated authority outside the model
-> escalate only when authority is insufficient
-> keep one-off approval one-off
-> require authorization at the executor
-> permit revocation without deleting identity
-> re-check after revocation
-> preserve causal provenance
```

If UCII can make this lifecycle easy for developers to adopt, the competitive advantage is not merely a novel security idea. It becomes a **usable default architecture for consequential autonomous systems**.

## Research maintenance rule

This comparison is a September 2026 snapshot. External projects are moving quickly. Re-verify competitor claims against current primary sources before publishing a final comparison table, Devpost text, investor material, or public claim. Record uncertainty rather than converting missing documentation into an assertion of absence.
