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

- [x] Guardian runs through Strands.
- [x] A request becomes a bounded action envelope.
- [x] No consequential executor exists yet.
- [x] Model output cannot itself create authorization.


**Verified completion evidence ? 2026-09-09:**

- Live AWS Strands/Bedrock invocation succeeded using the Guardian agent.
- Natural-language purchase intent was normalized through Strands structured
  output into a validated `ActionRequest`.
- The live boundary stopped at `ActionRequest`; authorization remained
  explicitly not established and no action was executed.
- Guardian had no consequential or authority-granting tools.
- `ActionRequest` parameters are immutable after validation while preserving
  Strands-compatible JSON-object structured output.
- Normalization boundary tests verify successful structured output, rejection
  of blank requests before agent invocation, and fail-closed behavior when
  structured output is absent.
- Final Objective 1 regression: `6 passed`.
- Verified implementation checkpoint:
  `ac9c1c3af43e6a2370d722c020e54b2d7870756f`.

**Status: COMPLETE.**

## Objective 2 — UCII Guardian identity binding

**Goal:** Bind the running Guardian to a real UCII identity and credential through the public UCII boundary.

Acceptance:

- [x] Guardian authenticates as its own UCII identity.
- [x] Credential proof is verifiable.
- [x] Authentication failure fails closed.
- [x] No private UCII implementation bypass is introduced.

**Verified completion evidence — 2026-09-10:**

- Guardian identity `35c1db3d-61d7-4d0d-a5d7-db3ab7f79520`
  was verified through the real public UCII SDK/HTTPS boundary.
- Active Credential B fingerprint
  `9d14f6f5a53629709afb1574ef9d14bead52d6da5ecb1334cfaf930abd321559`
  was proven using the Guardian-held ML-DSA-65 signing key; the private key
  remained in local Guardian custody.
- UCII returned `UCII_VERIFIED` for the live peer-authentication proof.
- Guardian's first-party service entitlement satisfied only the economic
  access gate for `POST /v1/credentials/verify`; Guardian did not pay itself.
- No controller authority, action authorization, approval authority, or
  execution authority was created by identity verification.
- Runtime implementation uses the public `ucii-sdk` boundary and contains no
  private `pq_auth` server import or implementation bypass.
- Authentication and UCII verification failures fail closed through
  `GuardianIdentityVerificationError`.
- Verification results deliberately expose only established identity,
  credential-fingerprint, and verification-status facts; they carry no
  authorization grant.
- Final targeted Objective 2 regression: `7 passed`.
- Final full Guardian regression: `34 passed`.
- Verified implementation checkpoint:
  `0f46eae19fd15cf8cc09e503bb38632fcec13f34`.
- Screen-record milestone 2 was captured from the successful live verification.

**Status: COMPLETE.**

## Objective 3 — Authority decision tool

**Goal:** Give the Strands agent one narrow authority-checking capability.

Canonical interface concept:

```text
check_authority(action) -> ALLOW | ESCALATION_REQUIRED | DENY
```

Acceptance:

- [x] In-scope active authority returns ALLOW.
- [x] Legitimate but out-of-scope action returns ESCALATION_REQUIRED.
- [x] Revoked/expired/invalid/unverifiable authority returns DENY.
- [x] Authentication/verification alone never returns ALLOW.

**Verified completion evidence — 2026-09-10:**

- Guardian implements the narrow `check_authority(action)` adapter through the
  public `ucii-sdk` delegated-authority boundary; no private UCII server import
  or execution shortcut is present.
- The Guardian-held ML-DSA-65 credential signs a canonical representation of
  the proposed `ActionRequest`, binding the proof to its identity, operation,
  target, parameters, request ID, requester, and request timestamp.
- Canonical mapping is fail-closed: `ACTIVE -> ALLOW`,
  `NOT_GRANTED -> ESCALATION_REQUIRED`, and
  `REVOKED` / `EXPIRED` / `INVALID -> DENY`.
- Inconsistent, malformed, unknown, or failed UCII authority responses do not
  produce `ALLOW`.
- Live negative production proof established that Guardian can be
  `UCII_VERIFIED` with its active cryptographically proven Credential B while
  UCII returns `NOT_GRANTED`; Guardian returned `ESCALATION_REQUIRED` and no
  execution occurred. This proves authentication/verification alone is not
  action authorization.
- One bounded production demo authority was then established for Guardian
  identity `35c1db3d-61d7-4d0d-a5d7-db3ab7f79520`, scoped only to exact
  operation `guardian.purchase.office_supply`; no controller, payment,
  credential-lifecycle, approval, or execution authority was created by that
  grant.
- Live positive production proof then returned authority state `ACTIVE` and
  Guardian decision `ALLOW` through the real public UCII SDK/HTTPS boundary,
  while the authority check itself still performed no execution.
- The active demo authority record created for this proof is
  `bea80670-e7ea-4176-a491-e3c0130d00cf`.
- Final targeted Objective 3 authority regression: `20 passed`.
- Final Objective 2 + 3 composition regression: `27 passed`.
- Final full Guardian regression: `54 passed`.
- Verified implementation checkpoint:
  `8dad3a8e29d379b5dcbc409dc3d8d89b62d0e353`.

**Status: COMPLETE.**

## Objective 4 — Protected executor

**Goal:** Implement exactly one consequential action domain and make authorization structurally mandatory.

Acceptance:

- [x] One executor interface exists.
- [x] Executor requires action-bound verified authorization evidence.
- [x] Authorized action succeeds.
- [x] Missing/invalid authorization cannot execute.
- [x] LLM instruction alone cannot execute.

**Verified completion evidence — 2026-09-10:**

- Guardian implements exactly one protected consequential executor domain:
  `guardian.purchase.office_supply`.
- `execute_office_supply(...)` requires an `AuthorityDecisionResult` whose
  decision is exactly `ALLOW`, authority state is exactly `ACTIVE`, and whose
  Guardian identity, operation, and request ID exactly match the proposed
  `ActionRequest` before any side effect can occur.
- The executor validates the bounded office-supply domain and quantity/price
  limits independently of model output and writes a uniquely keyed durable
  execution receipt only after all authorization and domain guards pass.
- Executor tests prove non-`ALLOW`, mismatched identity/operation/request ID,
  invalid domain parameters, direct LLM instruction without authorization, and
  replay of the same request cannot execute.
- A first live Strands attempt emitted generic operation `purchase`; Guardian
  rejected it before the UCII authority check or executor was reached. No
  receipt was created. This demonstrated fail-closed behavior for model output
  outside the canonical protected execution contract.
- The Strands normalization contract was then bounded to the exact operation
  `guardian.purchase.office_supply` and canonical `office-supply:` target
  vocabulary without adding execution tools or allowing the model to create
  authority.
- A fresh live end-to-end run then produced canonical request ID
  `44879bd8-d09b-40a3-be24-6bcb7ee3011d`, verified Guardian's real UCII
  identity and Credential B through the public UCII SDK/HTTPS boundary, and
  received delegated authority state `ACTIVE` with decision `ALLOW`.
- The authority check itself still performed no execution; only the subsequent
  protected executor invocation completed the action and wrote durable receipt
  `guardian-office-supply-44879bd8-d09b-40a3-be24-6bcb7ee3011d` outside the
  repository.
- The live receipt was verified to match the exact Guardian identity,
  operation, target, and request ID of the authorized action.
- The live proof used no human approval, no controller authority, no Guardian
  self-payment, and did not expose the private ML-DSA-65 signing key.
- Final Objective 1-4 composition regression: `55 passed`.
- Final full Guardian regression: `79 passed`.
- Protected executor implementation checkpoint:
  `34bbcc0b2229717145d7f569c232e3f7ee7402cb`.
- Strands real-identity binding checkpoint:
  `a3bcf9490e3ea82585fd250a656833e7f1734975`.
- Canonical Strands normalization checkpoint:
  `972b5f8d1d31546a39a16fac22bcee00fb95e998`.
- Screen-record milestone 3 was captured from a successful fresh live
  `Strands -> UCII -> ALLOW -> EXECUTE` run.

**Status: COMPLETE.**

## Objective 5 — Human escalation and bounded approval

**Goal:** Preserve human judgment when Guardian's delegated authority is insufficient.

Acceptance:

- [x] Guardian produces a clear escalation request.
- [x] Human can approve or deny.
- [x] Denial causes no execution.
- [x] Approval is bounded to the exceptional action by default.
- [x] Approval does not silently become broad standing authority.

**Verified completion evidence — 2026-09-10:**

- Guardian implements a bounded escalation contract that accepts only an
  existing `ESCALATION_REQUIRED` decision backed by authoritative UCII state
  `NOT_GRANTED`; `ALLOW`, `REVOKED`, `EXPIRED`, and `INVALID` cannot enter the
  human-approval path.
- Human review supports exactly two decisions: `APPROVE_ONCE` and `DENY`.
  Automated Objective 5 tests prove `DENY` creates no approval fact and causes
  no protected execution.
- `APPROVE_ONCE` is bound to the exact Guardian identity, requester,
  operation, target, parameters, and request ID. It is not a standing
  delegated-authority record and cannot broaden UCII authority.
- The protected office-supply executor accepts the exceptional operation
  `guardian.purchase.office_supply.exception` only through exact one-off human
  approval. A standing `ALLOW` authority result cannot execute that
  exceptional operation.
- A real live AWS Strands run normalized explicit exceptional human intent into
  request ID `1c4f0661-3a49-413c-852a-5e65935a31be` for exact operation
  `guardian.purchase.office_supply.exception` and target
  `office-supply:printer-cartridge`.
- Guardian then verified its real UCII identity and active Credential B through
  the public UCII SDK/HTTPS boundary. UCII returned delegated authority state
  `NOT_GRANTED`, which Guardian mapped to `ESCALATION_REQUIRED`.
- Before human judgment, no execution occurred and no durable receipt existed.
- The human explicitly entered `APPROVE_ONCE` at the terminal. The model did
  not grant authority, make the human decision, or directly execute.
- The resulting exact-action one-off approval unlocked one protected execution
  and created durable receipt
  `guardian-office-supply-1c4f0661-3a49-413c-852a-5e65935a31be`.
- A fresh public UCII authority check after execution still returned
  `NOT_GRANTED` / `ESCALATION_REQUIRED`, proving the one-off approval did not
  become or silently create broad standing authority.
- Reuse of the same one-off approval for the same request was denied with
  `Protected action has already been executed`, proving the approved action
  could not be replayed into a second execution.
- No standing UCII authority record was mutated, no controller authority was
  used, Guardian did not pay itself, and the private ML-DSA-65 key remained in
  local Guardian custody.
- Final Objective 5 composition regression before live proof: `58 passed`.
- Final Objectives 3-5 composition regression before live proof: `78 passed`.
- Final full Guardian regression before live proof: `115 passed`.
- Bounded escalation contract checkpoint:
  `72589b47397915fec50d200b897c8f4d55d841ed`.
- One-off approval execution-gate checkpoint:
  `00d53c1676f69526abc33fca0d463384dbeb970a`.
- Human escalation decision-flow checkpoint:
  `d5a7a898e3abba6256f3e9806266bf3efa813e31`.
- Exceptional human-approved action checkpoint:
  `d2fa31e2296897988be27a9804ec10656ed0d04a`.
- Screen-record milestones 4 and 5 were captured from the successful live
  `Strands -> UCII NOT_GRANTED -> HUMAN APPROVE_ONCE -> EXECUTE` proof.

**Status: COMPLETE.**

## Objective 6 — Revocation proof

**Goal:** Demonstrate that authority is operationally revocable.

Acceptance:

- [x] An action succeeds while authority is active.
- [x] Authority can be revoked.
- [x] A later equivalent attempt is denied.
- [x] No stale/cached authorization bypasses revocation.

**Verified completion evidence — 2026-09-10:**

- UCII added a bounded delegated action-authority lifecycle service that can
  permanently transition an existing `ACTIVE` authority record to `REVOKED`
  while preserving historical revocation timestamp and reason.
- The revocation service does not modify identity credentials, authenticate a
  caller, create controller authority, establish economic/payment authority,
  execute an operation, broaden authority, or reactivate historical authority.
- UCII revocation-service regression completed with `48 passed` across action
  authority persistence, evaluation, lifecycle mutation, and the public
  delegated-authority check boundary.
- Verified UCII revocation-service checkpoint:
  `e0ddb5cbba73e1742015b0d41f542ac54037ec9b`.
- Before the live revocation event, Guardian produced a fresh real AWS Strands
  routine request for exact operation `guardian.purchase.office_supply`.
  Guardian verified identity
  `35c1db3d-61d7-4d0d-a5d7-db3ab7f79520` and active Credential B through the
  public UCII SDK/HTTPS boundary.
- The fresh pre-revocation request ID
  `d06cdc36-cba8-4743-8f26-3932dec3a2fa` received authoritative UCII state
  `ACTIVE` and Guardian decision `ALLOW`.
- The protected executor then completed that action and wrote durable receipt
  `guardian-office-supply-d06cdc36-cba8-4743-8f26-3932dec3a2fa`, proving the
  delegated authority was genuinely operational before revocation.
- The human then permanently revoked the exact production demo authority
  `bea80670-e7ea-4176-a491-e3c0130d00cf`, scoped only to
  `guardian.purchase.office_supply`.
- The persisted authority transitioned from `ACTIVE` to `REVOKED` at
  `2026-09-10 20:47:51.593073` with bounded reason
  `human_revoked_guardian_demo_authority`.
- An independent post-mutation database read confirmed the historical record
  remained `REVOKED`, no active authority remained for the routine operation,
  and the UCII evaluator independently returned `REVOKED`.
- Guardian then generated a completely fresh equivalent AWS Strands request,
  request ID `1647c91d-e4b0-4f94-991f-d99acc5e0dc9`.
- Guardian identity and Credential B still verified as `UCII_VERIFIED`,
  demonstrating that delegated-action revocation is independent from identity
  authentication and credential validity.
- The fresh public UCII delegated-authority check returned `REVOKED`; Guardian
  deterministically mapped that state to `DENY`.
- The protected executor rejected the denied action with
  `Protected execution requires ALLOW`; no post-revocation durable receipt was
  created.
- The post-revocation request used a fresh action envelope and fresh public
  UCII authority check rather than reusing the earlier `ALLOW`, and no
  stale/cached authorization bypass survived revocation.
- Authority A is now permanent historical evidence and must never be
  reactivated. Any later delegated routine authority requires a fresh authority
  record rather than mutation of the revoked record.
- Identity credential B remained active; no credential revocation, controller
  mutation, Guardian self-payment, or private-key disclosure occurred.
- Screen-record milestone 6 captured the coherent live sequence:
  `ACTIVE -> ALLOW -> EXECUTE -> HUMAN REVOKE -> REVOKED -> DENY -> NO EXECUTION`.

**Status: COMPLETE.**

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
