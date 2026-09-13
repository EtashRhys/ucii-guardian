# UCII Guardian — Final Build Day Plan — 2026-09-13

## Purpose

This is the no-drift execution plan for the final Guardian engineering day before the Devpost deadline.

Target: finish engineering, hardening, demo proof, and submission preparation on Sunday, September 13, 2026 so Monday, September 14 remains an emergency cushion rather than a build day.

Deadline: Monday, September 14, 2026 at 5:00 PM PT / 8:00 PM ET.

## Starting checkpoints

- Guardian: `ba06e2e86ac907b6e285b982d0e3a6fbb51ec92c`
- UCII grant backend: `f2d2ad5558f490f3e78199eb290b18d3e53650f6`

Before implementation, verify branch, HEAD, origin/main parity, and clean worktree in both repositories.

## Already complete — do not rebuild

Guardian already has:

- UCII identity binding;
- authority evaluation;
- protected consequential execution;
- autonomous execution for routine `ACTIVE -> ALLOW` work;
- `APPROVE_ONCE`;
- `DENY`;
- delegated authority revocation;
- durable provenance;
- minimal demo interface.

UCII already has the protected standing-authority grant lifecycle and public grant API.

`APPROVE_ONCE` and `DENY` are COMPLETE and live-proven. Do not build second versions.

## Final human control model

1. **Grant Standing Authority** — create a new bounded ongoing delegation.
2. **Approve Once** — approve one exact exceptional request without changing standing authority.
3. **Deny** — refuse the exact exceptional request; no execution.
4. **Revoke Standing Authority** — permanently terminate one exact standing delegation.

Normal autonomous behavior:

```text
ACTIVE standing authority
+ request inside standing scope
+ request inside economic budget
= automatic protected execution
```

No additional human approval is required for ordinary in-budget work.

## A. Wire Grant Standing Authority into Guardian

Inspect first:

- `src/ucii_guardian/authority_lifecycle.py`
- `src/ucii_guardian/web.py`
- relevant lifecycle/web tests
- current SDK/client authorization surface
- current UI authority controls
- server-held ACTIVE authority context

Determine whether the pinned UCII SDK already exposes grant support. If not, add only the minimum SDK support required through the legitimate public UCII boundary.

Required behavior:

- human-only Grant Standing Authority control;
- exact demo operation `guardian.purchase.office_supply`;
- browser cannot invent arbitrary identity, state, or operation scope;
- fresh authority ID;
- exact Guardian identity;
- `ACTIVE` state;
- exact operation and `granted_by` validation;
- trusted server-side authority context;
- fresh authoritative evaluation;
- UI reflects ACTIVE;
- routine request can execute normally.

Historical revoked grants remain REVOKED. New standing permission is a distinct new grant, never a REVOKED -> ACTIVE mutation.

Gate: targeted grant tests, revocation regression, live public grant proof, reviewed diff, commit, sync, parity.

## B. Add bounded budget enforcement

Demo policy:

```text
per-transaction standing limit: $80
monthly aggregate standing limit: $300
```

Required ordering:

```text
normalize request
-> verify Guardian identity
-> fresh UCII standing-authority evaluation
-> require ACTIVE / ALLOW
-> evaluate budget
-> within budget: automatic protected execution
-> budget exceeded: stop before execution and escalate
```

Budget invariants:

- in-budget routine work never interrupts the human;
- count successful completed executions only;
- denied or failed attempts do not count as completed spend;
- successful `APPROVE_ONCE` exceptions count as actual completed spend;
- `APPROVE_ONCE` does not change the standing $80 or $300 limits;
- exhausted monthly capacity blocks further autonomous spend until reset;
- reuse durable receipts/provenance where possible;
- fail closed if budget state cannot be established;
- do not build generalized accounting/analytics infrastructure.

Minimum proof cases:

- `$35` with capacity -> autonomous execution;
- `$80` boundary with capacity -> autonomous execution;
- `$81` -> escalation before execution;
- request `<= $80` but above remaining monthly capacity -> escalation;
- failed/denied action -> no spend increase;
- successful action -> durable completed-spend increase.

## C. Route budget exceptions into existing Approve Once / Deny

Do not build another approval system.

```text
ACTIVE authority
+ budget exceeded
-> ESCALATION_REQUIRED
-> existing APPROVE_ONCE / DENY
```

`APPROVE_ONCE` remains exact-request, one-use, non-replayable, and must not increase standing limits or broaden standing authority.

`DENY` causes no protected execution and no standing authority/budget change.

## D. Re-prove revocation after grant + budget integration

```text
fresh ACTIVE grant
-> in-budget request executes automatically
-> human revokes exact standing authority
-> fresh authority check
-> same class of in-budget request
-> REVOKED / DENY / no execution
```

Guardian identity must remain cryptographically verified after revocation.

## E. Final four-control live proof

1. No usable standing authority -> no protected execution.
2. **Grant Standing Authority** -> fresh ACTIVE authority ID.
3. Routine `$35` request -> automatic execution, no extra approval.
4. Over-budget `$125` request -> stop before execution and escalate.
5. **Approve Once** -> exact request executes once; replay does not authorize another execution.
6. Another over-budget request -> **Deny** -> no execution.
7. **Revoke Standing Authority** -> exact authority becomes REVOKED.
8. Fresh normal `$35` request -> `UCII_VERIFIED + REVOKED + DENY + No execution`.

This must prove all four controls while preserving normal bounded autonomy.

## F. Provenance completeness

Reuse the existing durable Guardian provenance/receipt system. Add only minimum missing grant/budget evidence so the record explains why each action executed automatically, escalated, executed once, was denied, or was refused after revocation.

## G. Objective 9 — hackathon hardening

Only after the authority lifecycle is stable:

- targeted and full regression tests;
- failure paths fail closed;
- README setup/demo instructions;
- architecture diagram;
- MIT or Apache-2.0 license;
- accurate disclosure of existing UCII technology;
- no secrets/private infrastructure details exposed;
- public-release hygiene;
- exact final code-freeze commit;
- clean worktree and origin/main parity.

After code freeze, do not add optional features.

## H. Objective 11 — submission package

Complete Sunday if possible:

- public repo ready;
- AWS Builder ID ready;
- Devpost description complete;
- architecture graphic/screenshots ready;
- public demo video `<= 5 minutes`;
- video includes working demo and concise pitch;
- submission fields populated;
- public links tested logged out/private;
- final proofreading;
- submit Sunday if ready.

Monday should ideally contain no engineering. If needed, Monday is for final verification/submission only, well before 8:00 PM ET.

## Definition of 100% complete

- fresh standing authority can be granted through legitimate UCII path;
- old revoked authority remains revoked;
- `ACTIVE + in-budget` executes autonomously;
- `$80` transaction and `$300` monthly limits enforced;
- completed spend durable enough for demo policy;
- over-budget work cannot execute before human judgment;
- existing `APPROVE_ONCE` works once for exact exception and does not change standing limits/authority;
- existing `DENY` causes no execution;
- Revoke terminates exact standing authority while identity remains valid;
- post-revocation request cannot execute under revoked grant;
- provenance explains lifecycle;
- targeted/full regressions pass;
- Guardian and UCII repos clean/synced;
- final demo proves Grant, autonomous bounded execution, Approve Once, Deny, Revoke, and post-revocation denial;
- Objective 9 complete;
- Objective 11 complete or ready to submit immediately.

## Scope firewall

Until the hackathon is complete, do not drift into Scout, Ambassador, Mission Control, D.8, Grokbot integration, multi-agent expansion, generalized RBAC, generalized accounting, broad x402 demos, voice architecture, or unrelated UCII roadmap work.

If a proposed task does not directly contribute to standing grant, budget enforcement, existing Approve Once/Deny integration, revocation regression, final proof, hardening, or submission readiness, do not do it.

## Stop condition

Once this definition of done is satisfied, stop building. Preserve Monday as the emergency cushion.