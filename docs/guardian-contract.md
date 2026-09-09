# UCII Guardian Authority Contract

## Purpose

This document defines the non-negotiable authority boundary for UCII Guardian. Every implementation choice must preserve these invariants.

## Guardian may

Guardian may:

- interpret a human request;
- normalize natural-language intent into a bounded action request;
- authenticate its own UCII identity;
- request UCII identity, credential, verification, authorization, and revocation facts;
- ask whether a proposed action is currently permitted;
- execute only through a protected executor after verified authorization;
- request the minimum human approval necessary when existing authority is insufficient;
- record durable provenance for requests, checks, decisions, approvals, refusals, revocations, and executions.

## Guardian may not

Guardian may not:

- manufacture, infer, broaden, or self-grant authority;
- treat model output as authorization;
- treat an external message as authority;
- treat authentication or verification as authorization;
- treat payment or settlement as authorization;
- treat prior authorization as perpetual authority;
- execute after authority has been revoked, expired, invalidated, or cannot be verified;
- silently convert a one-time human approval into standing authority;
- bypass the UCII public trust boundary through private implementation shortcuts;
- allow the executor to act without a verified authorization result bound to the requested action.

## Canonical outcomes

Every consequential action request must resolve to one of three outcomes:

### ALLOW

Current verified authority permits the exact requested action under its present constraints. Execution may proceed through the protected executor.

### ESCALATION_REQUIRED

The request may be legitimate, but current verified authority is insufficient. Guardian must not execute. It may request explicit bounded human approval.

### DENY

The request is prohibited, invalid, revoked, expired, unverifiable, malformed, or otherwise not executable. Guardian must fail closed.

## Action normalization

Natural-language requests must not flow directly into consequential execution. Guardian must first produce a normalized action envelope containing, at minimum:

- `request_id`
- `requester`
- `guardian_identity`
- `operation`
- `target`
- `parameters`
- `requested_at`

The exact schema may evolve, but the executor must receive a bounded action representation rather than unconstrained model prose.

## Protected execution invariant

The core implementation invariant is:

```text
NO VERIFIED AUTHORIZATION
        ↓
NO EXECUTION
```

The executor must independently require authorization evidence sufficient for the exact action it performs. A model instruction, conversational assertion, cached decision, or previous success is insufficient.

## Human approval invariant

When escalation is required, human approval should be as narrow as practical. The default hackathon behavior is approval for the specific action, target, parameters, and execution attempt rather than a broad standing delegation.

## Revocation invariant

Revocation must have observable operational effect. After revocation, any later attempt relying on the revoked authority must be denied before consequential execution.

A revoked authority, credential, or grant must remain revoked. Guardian must never restore a revoked object merely to resume operation. Continued operation requires a fresh valid credential, grant, or authority as appropriate.

## Lifecycle continuity invariant

Guardian is intended to remain operational over a long-lived UCII identity lifecycle. Revocation must not impose a finite lifetime limit on an otherwise valid Guardian identity's ability to receive fresh credentials or fresh delegated authority.

The canonical lifecycle is:

```text
Authority A → active → revoked → permanently unusable
Authority B → active → revoked → permanently unusable
Authority C → active
...
```

There must be no semantic counter such as `revocations_remaining`, `max_reissues`, or a fixed number of allowed re-authorization cycles. Hundreds or thousands of legitimate revoke-and-reissue cycles must remain possible subject only to normal operational, storage, cryptographic, and abuse-protection constraints.

Revocation history must remain durable. Later re-authorization must not erase, rewrite, reactivate, or reinterpret prior revoked authority.

## Guardian first-party UCII service entitlement

Guardian must exercise real UCII identity, credential, verification, authorization, revocation, recovery/replacement, and other applicable UCII capabilities through the public UCII trust boundary.

For Guardian's own first-party use of UCII infrastructure, applicable x402 economic requirements may be satisfied by an explicit operator-established UCII service entitlement rather than by Guardian paying UCII for each covered operation.

The entitlement must be:

- bound to Guardian's cryptographically authenticated UCII identity;
- explicitly established by UCII operator authority;
- scoped to allowed UCII operations;
- independently revocable;
- auditable through provenance;
- incapable of creating identity, credential, controller, revocation, or action authority by itself;
- incapable of bypassing cryptographic verification or the public UCII trust boundary.

The entitlement is an alternative satisfaction mechanism for the economic gate only. It must never mean:

```text
FREE ECONOMIC ACCESS = AUTHORIZED ACTION
```

Instead the required separation is:

```text
IDENTITY / CREDENTIAL PROOF
        ↓
CONTROLLER / ACTION AUTHORITY
        ↓
ECONOMIC ACCESS POLICY
        ↓
REAL UCII OPERATION
```

Guardian's first-party entitlement may satisfy the economic-access step for covered operations, including real revocation, without weakening any preceding authority requirement.

## Economic continuity invariant

Guardian's first-party service entitlement must support repeated legitimate UCII lifecycle operations, including repeated credential replacement, revocation, and fresh authorization, without per-cycle x402 settlement.

The entitlement must not be implemented as a hard-coded Guardian bypass, secret `skip_x402` switch, IP allowlist, development mode, or private implementation shortcut. It should be represented as an explicit UCII policy/entitlement that can later serve as a model for legitimate enterprise contracts, prepaid service, partner access, promotional/free-trial access, or other non-per-call economic arrangements without changing UCII's authority model.

## Abuse-control invariant

Unlimited lifecycle continuity does not imply unlimited instantaneous request velocity.

UCII may temporarily throttle covered lifecycle mutations when an authenticated identity or entitlement exhibits abnormal burst behavior consistent with a runaway loop, automation defect, or deliberate spam.

Abuse controls must:

- be based primarily on authenticated UCII identity and/or entitlement rather than IP address alone;
- use configurable policy rather than a permanent lifetime counter;
- apply temporary cooldowns or fail-closed review states rather than consume a finite revocation allowance;
- preserve all already-established credential, authorization, and revocation state;
- never reactivate revoked authority when a cooldown expires;
- allow normal lifecycle operations to resume after the applicable cooldown or operator resolution.

The governing rule is:

```text
UNBOUNDED LEGITIMATE LIFECYCLE
        +
BOUNDED REQUEST VELOCITY
```

Specific thresholds and cooldown durations are implementation policy and must be inspected against existing UCII protections before new controls are introduced.

## Provenance invariant

Guardian must preserve enough evidence to answer:

- What action was requested?
- Which Guardian identity handled it?
- What authority was checked?
- What result was returned?
- Why was the action allowed, escalated, or denied?
- Did a human approve or deny an escalation?
- Did execution occur?
- Was the authority later revoked?
- Was fresh replacement authority established after revocation?
- Did an applicable first-party entitlement satisfy an economic gate?
- Did abuse throttling or a cooldown affect a lifecycle request?

Provenance observes and records authority decisions; it must never create authority.

## System boundary

Guardian is a new hackathon application. Existing UCII production systems, Scout, Ambassador, and Mission Control remain outside Guardian's implementation scope unless a later explicit design decision says otherwise. Guardian integrates with UCII rather than embedding or duplicating UCII's trust model.
