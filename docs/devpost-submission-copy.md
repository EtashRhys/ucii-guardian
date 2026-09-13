# UCII Guardian — Devpost Submission Copy

## Project name

**UCII Guardian**

## Tagline

**Capability is not authority. Give autonomous AI bounded, human-controlled, cryptographically verifiable authority.**

## Track

**Professional Agents**

## Short description

UCII Guardian is a human-governed autonomous agent built with AWS Strands Agents and UCII. Humans grant bounded standing authority and set an economic Budget Range; Guardian operates autonomously inside those limits, stops before execution when a request crosses them, supports exact one-time approval or denial, and allows standing authority to be permanently revoked without destroying the agent's identity.

## Inspiration

AI agents are rapidly becoming capable of doing real work: purchasing, deploying software, accessing data, operating infrastructure, moving money, and coordinating with other systems. But capability creates a new problem.

**Just because an AI can do something does not mean it should have authority to do it.**

Most agent demonstrations focus on making the agent more capable. We wanted to explore the other side of autonomy: how do you give an AI enough authority to be genuinely useful without giving it unlimited permission?

The model should be able to reason and propose actions. It should not be able to manufacture the permission required to execute them.

That became the central idea behind UCII Guardian:

> **Capability is not authority.**

A useful analogy is an employee with a corporate card. A company does not give an employee unlimited access to its bank account. It gives them an identity, a role, bounded spending authority, limits, an exception process, an audit trail, and the ability to revoke access. Guardian brings that authority model to autonomous AI.

## What it does

Guardian demonstrates a complete human-controlled authority lifecycle for an autonomous agent.

A human can **Grant Standing Authority** for a bounded class of work and set a **Budget Range** defining how much Guardian may spend autonomously on an individual request. Guardian then uses AWS Strands Agents to interpret natural-language intent and normalize the proposed action.

Before consequential execution, Guardian independently verifies its cryptographic UCII identity and performs a fresh check of its delegated authority. It then applies the human-controlled budget policy outside the language model.

If the request is authorized and inside the Budget Range, Guardian executes autonomously without interrupting the human.

If the request exceeds the Budget Range, Guardian stops **before execution** and returns the decision to the human. The human can choose **Approve Once**, which authorizes only that exact pending exception, or **Deny**, which causes no execution. Approve Once does not increase Guardian's standing budget or broaden its ongoing authority.

The human can also **Revoke Authority**. Revocation ends the exact standing delegation while Guardian's identity remains valid. A fresh request that previously succeeded is then denied at the protected execution boundary.

Guardian also records provenance across the lifecycle so the human can reconstruct what was requested, which identity was verified, what authority was checked, whether human judgment was required, and whether execution occurred.

The core separation is:

`Capability != Identity != Authority != Human Policy != Approval != Execution`

## The demo

The demo uses an office-supply purchase because the boundary is immediately understandable, but the architecture is intended for consequential autonomous actions generally.

The human grants Guardian standing authority and sets a Budget Range of **$101.28**.

A request to purchase a printer cartridge for **$35** verifies Guardian's identity, receives an ACTIVE/ALLOW authority result, falls inside the human budget, and executes automatically. There is no additional human approval because the human already delegated this class of work within these limits.

A **$150** request still has valid standing authority, but exceeds the human Budget Range. Guardian stops before execution. The human selects **Approve Once**, and only that exact exception executes.

A new **$175** request again exceeds the budget. This time the human selects **Deny**, and no execution occurs.

Finally, the human revokes Guardian's standing authority and submits the same **$35** request that previously executed automatically. Guardian's identity still cryptographically verifies, but the fresh authority result is REVOKED and execution is refused.

That final comparison is the key proof:

> **Same Guardian. Same verified identity. Same request. Same budget. Different authority state — different execution outcome.**

Nothing happened to the AI's capability. What changed was its authority.

## How we built it

Guardian is built in Python with **AWS Strands Agents** as the agentic reasoning/orchestration layer.

The Strands agent receives natural-language requests and produces a structured action representation. Its system boundary is deliberately narrow: it has no authority-granting tools and no protected execution tools. Model output can describe a proposed action, but it cannot establish that the action is permitted.

**UCII (Universal Cryptographic Identity Infrastructure)** provides the independent identity and delegated-authority boundary. Guardian uses the public UCII SDK/API path to establish cryptographic identity, evaluate current delegated authority, grant bounded standing authority, and revoke that authority.

Guardian then applies a deterministic, server-held human policy layer. The Budget Range is controlled by the human and cannot be changed by the language model. It defaults to **$0.00** on a fresh start and supports a human-selected per-request ceiling up to **$5,000.00**.

Protected execution sits downstream of these checks. The important ordering is:

`human request -> Strands normalization -> UCII identity verification -> fresh UCII authority evaluation -> Guardian human policy -> human exception decision if required -> protected execution -> provenance`

The web experience is implemented with **Starlette** and **Uvicorn**. UCII's cryptographic stack includes post-quantum cryptographic support through liboqs, while Guardian's protected custody and authority lifecycle are kept outside the LLM.

The final submission build passed **272 tests** and a clean HTTP startup/root smoke test.

## Why AWS Strands Agents matters

Strands is not decorative in Guardian. It owns the probabilistic agentic reasoning boundary: understanding the human's natural-language request and turning it into a structured proposed action.

That role is deliberately contrasted with deterministic authority enforcement.

The Strands agent can understand that the human wants a printer cartridge, identify the operation and amount, and propose the action. But the model's belief that an action is appropriate cannot make authorization true. UCII and Guardian's policy/execution boundaries independently determine whether the proposed action may actually happen.

This lets us preserve useful agent intelligence without treating model reasoning as a security boundary.

## Challenges we ran into

The hardest challenge was preserving strict separation between concepts that are easy to accidentally collapse together in an agent application.

A verified identity is not authorization. Authorization is not a budget decision. A payment mechanism is not permission to act. A one-time human exception is not standing authority. A browser button is not lifecycle authority. And successful execution cannot be allowed to retroactively imply that permission existed.

Revocation was particularly important. We did not want a cosmetic REVOKED badge. We needed a fresh request after revocation to travel through the real authority path and fail before protected execution, while the same Guardian identity continued to verify normally.

We also had to make one-time human approval truly one-time. Approving an exceptional request cannot silently expand Guardian's standing privileges or increase its Budget Range.

Finally, we deliberately resisted feature expansion. The strongest demonstration was not another general-purpose assistant. It was one narrow vertical slice where judges can see autonomy, authority, exception handling, revocation, and provenance work together end to end.

## Accomplishments that we're proud of

We built a working autonomous agent where the LLM is **not the authority source**.

Routine work inside deliberately granted authority executes without human interruption, so Guardian preserves the value of autonomy rather than turning every action into an approval dialog.

At the same time, a human-controlled economic boundary can stop a capable, authenticated, otherwise-authorized agent before execution and require one-time human judgment.

We implemented fresh bounded standing-authority grants, exact one-time approval, explicit denial, permanent delegated-authority revocation, protected consequential execution, and attributable provenance as separate domains.

The strongest live result is the post-revocation proof: Guardian remains running, its cryptographic identity still verifies, it still understands the request, but the exact action that previously executed is now denied because the human revoked its authority.

The final Guardian build passed **272 tests**.

## What we learned

The most important lesson was that useful autonomy and human control are not opposites.

If humans must approve every routine action, the agent is not very autonomous. If the agent can decide its own permissions, human control becomes largely advisory. The useful middle ground is **bounded autonomy**: humans define the operating envelope, and the agent acts independently inside it.

We also learned how important domain separation becomes once AI can take consequential actions. Identity, authentication, delegated authority, economic limits, one-time approval, payment, execution, and provenance answer different questions. Keeping those facts separate makes the system easier to reason about and makes revocation meaningful.

A final lesson was that the best security property is one you can demonstrate through cause and effect. `UCII_VERIFIED + ACTIVE -> execution`, followed by `UCII_VERIFIED + REVOKED -> no execution`, communicates the architecture more clearly than a long security lecture.

## What's next for UCII Guardian

The hackathon build intentionally proves one complete authority lifecycle rather than expanding into many integrations.

Next, the Guardian pattern can be applied to additional consequential domains such as software deployment, enterprise infrastructure, data access, communications, financial operations, robots/devices, and agent-to-agent work.

The human policy layer can also grow beyond a transaction ceiling into other explicit boundaries such as approved vendors, time windows, geographic constraints, data classifications, tool scopes, operational limits, and organizational policy.

For UCII, Guardian also gives us a concrete developer-experience target: reduce **Time to First Authorized Action** for any autonomous agent that needs identity, delegated authority, revocable execution, and auditable provenance.

The goal is not to make AI less autonomous. It is to make powerful autonomy deployable under explicit human authority.

## Built with

- AWS Strands Agents
- Python 3.11+
- UCII / UCII SDK
- Starlette
- Uvicorn
- liboqs / post-quantum cryptographic support
- Pytest
- Git / GitHub

## Prior-work disclosure

**UCII Guardian is the new hackathon project.** Guardian was built for the Agents for Humans Hackathon as the autonomous agent, human authority experience, Strands orchestration, policy enforcement workflow, protected execution path, exception-handling experience, provenance integration, web interface, and associated tests.

Guardian integrates with **UCII (Universal Cryptographic Identity Infrastructure)**, which is pre-existing infrastructure developed before the hackathon. UCII provides the underlying identity, credential, authorization, delegated-authority, revocation, cryptographic trust, and public SDK/API capabilities consumed by Guardian.

We do **not** claim that the underlying UCII platform was created during the hackathon. The submission is Guardian and the hackathon-specific integration/extension work required to expose Guardian's bounded human-controlled authority lifecycle through UCII's public boundary.

## Repository

**Guardian:** `EtashRhys/ucii-guardian`

**UCII infrastructure:** `EtashRhys/UCII`

## Submission positioning

### One sentence

**UCII Guardian lets autonomous AI operate inside authority a human deliberately granted, while enforcing the boundary outside the model.**

### Opening line

> **AI agents are becoming capable of taking real actions. But capability is not authority.**

### Closing line

> **We don't prevent AI from being autonomous. We prevent autonomy from becoming unlimited authority.**

### Strongest defensible technical claim

**Guardian is a working autonomous application demonstrating a complete human-controlled authority lifecycle against real UCII infrastructure, with protected execution outside the LLM's authority.**

## Claim discipline

Do not claim that Guardian solves AI alignment, eliminates prompt injection, guarantees benevolent model behavior, eliminates all AI risk, or invented cryptographic identity/delegated authorization for agents.

The submission's provable claim is narrower and stronger: Guardian externally limits what an autonomous AI is authorized to do independently of what the AI decides it wants to do.
