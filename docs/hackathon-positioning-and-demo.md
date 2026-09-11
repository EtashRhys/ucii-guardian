# UCII Guardian — Hackathon Positioning and Demo Narrative

## Purpose

This file freezes the product story, claim discipline, and final-demo emphasis for the hackathon so the implementation can stay narrow while the presentation remains precise.

Guardian should be judged on what the working system can actually demonstrate, not on an overbroad claim that nobody else has explored cryptographic identity, delegated authority, or revocation for AI agents.

## Core positioning

> **UCII + Guardian show how an autonomous AI can operate without ever possessing unlimited authority.**

The model interprets human intent and proposes actions. Independent cryptographic infrastructure (UCII) verifies the agent's identity and its current delegated authority before any consequential execution is allowed.

- Routine authorized work proceeds autonomously.
- Exceptional requests return to a human for one-time judgment (`APPROVE_ONCE`).
- A human can revoke standing authority without destroying the agent's identity.
- Identity, authority, human judgment, execution, economic permission, and provenance remain separate facts.

The strongest concise line remains:

> **Capability is not authority.**

A running model may know how to perform an action, possess network access, hold a valid identity credential, or be technically capable of invoking a tool. None of those facts independently establish permission for the consequential action.

## Claim discipline

Do **not** claim that Guardian or UCII is the first system to place cryptographic identity, authorization, delegated capability, or revocation outside an LLM. Adjacent research and engineering efforts exist in this area.

Examples currently worth tracking include AstraCipher, AITH (AI Trust Handshake), kxco-pq-agent, MAGIQ, and related work on agent identity, cryptographic delegation, post-quantum authentication, policy enforcement, and revocation.

Before naming or comparing any external project in public submission material, verify the current public source and exact technical claim. The hackathon submission does not require a priority argument.

The safer and stronger claim is:

> **Guardian is a working autonomous application that demonstrates a complete, human-controlled authority lifecycle against real UCII infrastructure.**

## What Guardian should visibly prove

Guardian's demo should make three orthogonal facts obvious:

```text
IDENTITY
  UCII_VERIFIED

AUTHORITY
  ACTIVE | NOT_GRANTED | REVOKED

EXECUTION
  Completed | Awaiting human decision | No execution
```

The key security property is that these facts do not collapse into one another.

A particularly strong post-revocation state is:

```text
IDENTITY_VERIFIED
+ AUTHORITY_REVOKED
+ EXECUTION_REFUSED
```

This demonstrates that Guardian can continue proving **who it is** while simultaneously proving that it no longer has permission to perform the consequential action.

The exceptional path should also remain explicit:

```text
IDENTITY_VERIFIED
-> NOT_GRANTED
-> ESCALATION_REQUIRED
-> HUMAN APPROVE_ONCE
-> EXECUTE
```

After that one exceptional action, standing delegated authority must remain unchanged. `APPROVE_ONCE` is human judgment for one exact action, not a hidden authority grant.

## UCII/Guardian architectural distinction

**UCII** is the identity and authority infrastructure.

**Guardian** is an autonomous application that demonstrates what becomes possible when an agent is integrated with that infrastructure correctly.

Guardian should therefore not be presented as merely another identity protocol. The demo is about the composition of:

1. real Strands-based agent reasoning;
2. independent UCII identity verification;
3. independent delegated-action authority;
4. protected consequential execution;
5. bounded human escalation and `APPROVE_ONCE`;
6. permanent authority revocation;
7. human-readable provenance.

The LLM remains above the authority boundary. It can interpret, propose, and reason. It cannot grant itself permission.

## UCII differentiation to preserve in the story

### Universal actor model

UCII is designed for more than AI agents. Its identity model includes:

- humans;
- AI agents;
- robots;
- devices;
- services;
- organizations.

Guardian is one application of that broader infrastructure.

### Identity is not authority

A valid UCII identity credential proves identity/authentication facts. It does not create action authority.

Guardian's demonstrated state `UCII_VERIFIED + REVOKED + DENY` should be highlighted because it makes this separation visible.

### One-off approval is not standing authority

`APPROVE_ONCE` must remain bound to the exact exceptional request and must not create, broaden, or reactivate a UCII delegated-authority record.

### Revocation is historical, not reversible state cleanup

Revoking an authority record should preserve it as historical evidence. Continued delegated authority requires a fresh legitimate authority grant rather than an `Unrevoke` or `Reactivate` operation.

### Economic permission is separate

UCII's economic/x402 dimension should remain conceptually separate from identity, delegated action authority, human approval, and execution.

The demo does not need to expand into a payment workflow merely to explain this. The important architectural point is:

```text
identity != authority != approval != payment/settlement != execution
```

### Provenance explains cause and effect

The provenance record should make it possible to reconstruct the actual lifecycle rather than merely display a final status badge.

## Final demo story

The strongest final video is a cause-and-effect demonstration, not an architecture lecture.

### Scene 1 — Autonomous routine work

Human request is within active delegated authority.

```text
REQUEST
-> UCII_VERIFIED
-> ACTIVE
-> ALLOW
-> EXECUTE
-> Completed
```

Emphasize that no human interruption was needed.

### Scene 2 — Boundary exceeded

Human asks for a legitimate action that does not have standing delegated authority.

```text
REQUEST
-> UCII_VERIFIED
-> NOT_GRANTED
-> ESCALATION_REQUIRED
-> NO EXECUTION
```

### Scene 3 — One-time human judgment

Human chooses `Approve Once` for that exact pending request.

```text
APPROVE_ONCE
-> exact request only
-> EXECUTE
-> Completed
```

Then make clear that standing authority remains `NOT_GRANTED`.

### Scene 4 — Human revokes standing authority

After Objective 8F, the human should perform this directly through Guardian's **Revoke Authority** control.

The control must invoke the legitimate UCII revocation lifecycle through the public authorized boundary. It must not be a UI-only state change, a direct database mutation from Guardian, or an LLM-accessible self-revocation/self-restoration mechanism.

The visible transition should be:

```text
ACTIVE
-> HUMAN REVOKE
-> UCII REVOKED
-> UI shows REVOKED
```

There is no Undo, Reactivate, or Unrevoke path.

### Scene 5 — Same class of request after revocation

Submit the same class of routine request again.

Guardian must perform a fresh identity verification / authority check and visibly produce:

```text
UCII_VERIFIED
-> REVOKED
-> DENY
-> No execution
```

The model, identity, and request class can remain the same. The changed fact is **authority**.

Recommended spoken explanation:

> **The agent is still running. Its identity still verifies. It still knows how to request the action. What changed is its authority. The human revoked it, so the consequential action cannot proceed.**

## The three-column visual argument

The current interface already exposes one of Guardian's strongest ideas:

```text
Guardian Decision | Authority | Execution
```

Use those columns deliberately in the final recording.

Before revocation:

```text
ALLOW | ACTIVE | Completed
```

After revocation:

```text
DENY | REVOKED | No execution
```

Meanwhile provenance can still show `IDENTITY_VERIFIED`.

This visual cause-and-effect is more persuasive than a long explanation of the architecture.

## Optional voice enhancement — only after 8F and Objective 9

Voice input is a **bonus presentation enhancement**, not part of Guardian's authority architecture.

Only attempt it after:

1. Objective 8F is implemented and proven;
2. Objective 9 hardening is complete;
3. the final text-input demo path is stable.

Preferred scope is deliberately tiny:

```text
microphone
-> speech-to-text
-> existing Human Request field
-> existing Guardian workflow unchanged
```

Voice must gain **zero authority**. It is only another way to populate the exact same human-request text field.

Prefer a browser-native implementation if it is reliable in the final demo browser and requires no new backend service, credential, audio-storage pipeline, or security boundary.

Abort the enhancement immediately if it becomes a subsystem, requires significant new infrastructure, destabilizes the demo, or threatens submission timing.

If it remains tiny and reliable, the ideal visual sequence is:

1. speak the routine request;
2. Guardian returns `ALLOW -> ACTIVE -> Completed`;
3. human clicks **Revoke Authority**;
4. speak the same request again;
5. Guardian returns `DENY -> REVOKED -> No execution`.

That sequence should be treated as presentation polish, not as a requirement for a successful submission.

## Judge-facing framing

Recommended opening:

> **AI agents are becoming capable of doing real work on our behalf. But capability is not authority. UCII Guardian lets an agent remain autonomous without allowing that autonomy to become unlimited authority.**

Recommended compact product explanation:

> **The model interprets intent and proposes actions. UCII independently verifies who the agent is and whether it currently has delegated authority for the exact consequential action. Routine authorized work proceeds autonomously. Exceptional work returns to the human for one-time judgment. Standing authority can be revoked without destroying the agent's identity.**

Recommended closing:

> **We don't prevent AI from being autonomous. We prevent autonomy from becoming unlimited authority.**

## What not to spend demo time proving

Do not dilute the submission by expanding into:

- a generalized workflow builder;
- many executor domains;
- a multi-agent swarm;
- Guardian-to-Guardian networking;
- a broad payment demo merely because x402 exists;
- a generalized RBAC system;
- a large voice assistant architecture;
- claims that Guardian solves all AI alignment or model-safety problems;
- claims of historical priority that are not required by the judging criteria.

The strongest submission is the already-working narrow vertical slice, made easy to understand.

## Post-hackathon product lesson: Time-to-UCII

Guardian also provides a useful integration baseline.

Guardian was built as a new application while simultaneously integrating UCII identity, delegated authority, protected execution, escalation, revocation, and provenance. This suggests a future UCII developer-experience metric:

> **Time to First Authorized Action**

Measure how long it takes an existing autonomous agent to move from:

```text
unidentified/unbounded agent
-> UCII identity
-> authenticated agent
-> delegated authority
-> protected tool/executor
-> revocable autonomous execution
-> auditable provenance
```

The post-hackathon goal should be to reduce that integration cost dramatically through SDKs, reference patterns, and documented first-party entitlement behavior.

This is a future UCII engineering initiative, not additional Guardian hackathon scope.
