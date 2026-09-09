# UCII Guardian — Hackathon Build Roadmap

## Governing principle

Build the smallest Guardian that proves bounded autonomous authority end to end. Complete one objective at a time. Do not expand scope until the current objective is verified.

Workflow:

**inspect → reason → bounded change → targeted verify → diff/review → commit → checkpoint**

## Objective 0 — Foundation and authority contract

**Goal:** Freeze what Guardian is and is not before application code exists.

Acceptance:

- [x] Dedicated Guardian repository exists.
- [x] Repository is private during development.
- [x] Core product promise documented.
- [x] Guardian authority contract documented.
- [x] Protected execution invariant documented.
- [x] Human approval invariant documented.
- [x] Revocation invariant documented.
- [x] Provenance invariant documented.
- [x] Hackathon demonstration target documented.
- [x] Monolith/non-goal boundary documented.

## Objective 1 — Minimum AWS Strands Guardian

**Goal:** Prove AWS Strands Agents is the real orchestration core.

Build only:

- minimal Python project/package;
- Strands dependency and configuration;
- one Guardian agent entry point;
- deterministic action-envelope model;
- natural-language request → normalized proposed action;
- tests for normalization boundaries.

Acceptance:

- [ ] Guardian runs through Strands.
- [ ] A request becomes a bounded action envelope.
- [ ] No consequential executor exists yet.
- [ ] Model output cannot itself create authorization.

## Objective 2 — UCII Guardian identity binding

**Goal:** Bind the running Guardian to a real UCII identity and credential through the public UCII boundary.

Acceptance:

- [ ] Guardian authenticates as its own UCII identity.
- [ ] Credential proof is verifiable.
- [ ] Authentication failure fails closed.
- [ ] No private UCII implementation bypass is introduced.

## Objective 3 — Authority decision tool

**Goal:** Give the Strands agent one narrow authority-checking capability.

Canonical interface concept:

```text
check_authority(action) -> ALLOW | ESCALATION_REQUIRED | DENY
```

Acceptance:

- [ ] In-scope active authority returns ALLOW.
- [ ] Legitimate but out-of-scope action returns ESCALATION_REQUIRED.
- [ ] Revoked/expired/invalid/unverifiable authority returns DENY.
- [ ] Authentication/verification alone never returns ALLOW.

## Objective 4 — Protected executor

**Goal:** Implement exactly one consequential action domain and make authorization structurally mandatory.

Acceptance:

- [ ] One executor interface exists.
- [ ] Executor requires action-bound verified authorization evidence.
- [ ] Authorized action succeeds.
- [ ] Missing/invalid authorization cannot execute.
- [ ] LLM instruction alone cannot execute.

## Objective 5 — Human escalation and bounded approval

**Goal:** Preserve human judgment when Guardian's delegated authority is insufficient.

Acceptance:

- [ ] Guardian produces a clear escalation request.
- [ ] Human can approve or deny.
- [ ] Denial causes no execution.
- [ ] Approval is bounded to the exceptional action by default.
- [ ] Approval does not silently become broad standing authority.

## Objective 6 — Revocation proof

**Goal:** Demonstrate that authority is operationally revocable.

Acceptance:

- [ ] An action succeeds while authority is active.
- [ ] Authority can be revoked.
- [ ] A later equivalent attempt is denied.
- [ ] No stale/cached authorization bypasses revocation.

## Objective 7 — Durable provenance

**Goal:** Make Guardian's behavior explainable and auditable without creating a new analytics platform.

Minimum event classes:

- REQUEST_RECEIVED
- IDENTITY_VERIFIED
- AUTHORITY_CHECKED
- AUTHORIZED
- ESCALATED
- HUMAN_APPROVED
- HUMAN_DENIED
- EXECUTION_STARTED
- EXECUTION_COMPLETED
- AUTHORITY_REVOKED
- EXECUTION_REFUSED

Acceptance:

- [ ] Complete demo lifecycle can be reconstructed.
- [ ] Provenance explains why each consequential decision occurred.
- [ ] Provenance does not create authority.
- [ ] Sensitive secrets are excluded from records.

## Objective 8 — Minimal demo interface

**Goal:** Present Guardian as a coherent product without building a frontend platform.

Minimum surfaces:

- current request/action;
- Guardian decision and reason;
- current authority status;
- Approve Once / Deny escalation controls;
- readable activity/provenance timeline.

Acceptance:

- [ ] Routine authorization is visually obvious.
- [ ] Escalation is visually obvious.
- [ ] Human approval/denial is obvious.
- [ ] Revocation and post-revocation denial are obvious.
- [ ] Demo can be understood without reading source code.

## Objective 9 — Hackathon hardening

**Goal:** Turn the verified vertical slice into a reliable submission.

Acceptance:

- [ ] Targeted and end-to-end tests pass.
- [ ] Failure paths fail closed.
- [ ] README includes setup and demo instructions.
- [ ] Architecture diagram exists.
- [ ] MIT or Apache-2.0 license exists before public submission.
- [ ] Existing UCII technology usage/disclosure is documented appropriately.
- [ ] No secrets or private infrastructure details are exposed.
- [ ] Repository is suitable for public release.

## Objective 10 — Optional scoring enhancements

Only after Objectives 1–9 are stable:

- [ ] Evaluate AWS AgentCore deployment.
- [ ] Add a live demo URL if reliable.
- [ ] Prepare builder.aws post(s) with `#AgentsforHumans` if useful.
- [ ] Improve visual polish without expanding product scope.

## Objective 11 — Submission package

- [ ] Public repository.
- [ ] AWS Builder ID ready.
- [ ] Devpost project description.
- [ ] Maximum five-minute public YouTube/Vimeo demo.
- [ ] Video includes working demo and pitch.
- [ ] Pitch clearly states problem, audience, and importance.
- [ ] Final submission completed before September 14, 2026 at 5:00 PM PT.

## Scope firewall

Until the hackathon is complete, Guardian development must not require changes to Scout, Ambassador, Mission Control, or unrelated UCII roadmap work. Any proposed expansion must first demonstrate that it is necessary for the seven-part Guardian authority lifecycle or hackathon submission quality.
