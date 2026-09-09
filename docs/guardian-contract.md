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

Provenance observes and records authority decisions; it must never create authority.

## System boundary

Guardian is a new hackathon application. Existing UCII production systems, Scout, Ambassador, and Mission Control remain outside Guardian's implementation scope unless a later explicit design decision says otherwise. Guardian integrates with UCII rather than embedding or duplicating UCII's trust model.
