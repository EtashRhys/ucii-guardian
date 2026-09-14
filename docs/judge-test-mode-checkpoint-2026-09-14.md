# UCII Guardian — Judge/Test Mode Engineering Checkpoint

**Date:** 2026-09-14  
**Status:** FROZEN FOR HACKATHON SUBMISSION  
**Reason:** Finish and submit all required hackathon artifacts first. Resume Judge/Test Mode immediately after submission and complete it the same day.

## Governing boundary

Judge/Test Mode exists only to make the Guardian lifecycle safely replayable for judges.

It must never weaken or replace the production UCII lifecycle.

Production:

`Guardian -> real UCII lifecycle -> protected authorization -> protected execution`

Judge/Test:

`Guardian -> isolated non-production authority state -> same Guardian policy behavior -> non-production execution demonstration`

The browser must never select the operating mode. Mode selection is server-side.

---

## Production lifecycle invariants

Do not modify these for judging convenience:

- production UCII controller-authority requirements
- expiring lifecycle authorization
- one-use lifecycle authorization
- production delegated-authority semantics
- production identity verification
- executor authority requirements
- fresh authority evaluation
- APPROVE_ONCE exact-request semantics
- production UCII grant/revoke paths

Capability is not authority.

Identity, authority, human policy, approval, execution, payment, and provenance remain separate domains.

---

## Objective 1 — COMPLETE

Commit:

`cc5270e6c49e2f1f1389f4191bbcc122bfc584e6`

Message:

`Add Guardian authority evaluation seam`

Implemented an explicit `authority_checker` composition seam in `run_guardian_request`.

Production behavior remains the default when no checker is supplied.

Real Guardian identity verification remains in the workflow before authority evaluation.

An injected checker replaces only the delegated-authority evaluation boundary.

Targeted proof at completion:

- 15 tests passed
- production default preserved
- executor still inaccessible without valid authority/approval

---

## Objective 2 — COMPLETE

Commit:

`f935945045c3de00aed8a5bbf04c56fb42fbd01f`

Message:

`Add isolated Guardian judge authority state`

Added:

- `src/ucii_guardian/judge_authority.py`
- `tests/test_judge_authority.py`

Canonical Judge/Test authority states:

- `NOT_GRANTED`
- `ACTIVE`
- `REVOKED`

`JudgeAuthorityState`:

- begins NOT_GRANTED
- grant: NOT_GRANTED -> ACTIVE
- revoke: ACTIVE -> REVOKED
- reset: any state -> NOT_GRANTED
- returns normal `AuthorityDecisionResult`
- binds exact Guardian identity
- binds exact credential fingerprint
- binds exact Guardian operation
- performs no UCII lifecycle mutation
- performs no network call
- has no executor access
- has no production lifecycle dependency

Targeted proof:

- Judge authority tests passed
- workflow tests passed
- production modules unchanged

---

## Objective 3A — IMPLEMENTED LOCALLY / NOT COMMITTED

Objective 3A is intentionally preserved as WIP while the hackathon submission is shipped.

Modified files only:

- `src/ucii_guardian/web.py`
- `tests/test_web.py`

Implemented:

### Server-side mode selection

Constants:

- `GUARDIAN_MODE_PRODUCTION = "production"`
- `GUARDIAN_MODE_JUDGE_TEST = "judge-test"`
- `GUARDIAN_MODE_ENVIRONMENT_VARIABLE = "UCII_GUARDIAN_MODE"`

Default:

`production`

Invalid configured modes fail closed.

### Judge/Test evaluation wiring

In Judge/Test Mode, `/evaluate` calls the existing Guardian workflow and injects:

`_get_judge_authority_state(config).check`

as `authority_checker`.

Therefore the Judge/Test path reuses:

- Strands reasoning/request normalization
- real Guardian workflow
- real Guardian identity verification
- real budget policy
- real escalation behavior
- real APPROVE_ONCE behavior
- real executor structural authority enforcement

Only the delegated-authority state source is isolated.

### Production evaluation

The production `/evaluate` branch retains the original workflow call without an injected `authority_checker`.

Production grant and revoke routes have not been modified by Objective 3A.

### Objective 3A proof

Latest targeted regression:

`48 passed, 2 warnings`

Warnings are environmental/deprecation warnings already known:

- liboqs 0.15.0 vs liboqs-python 0.16.0 version warning
- Starlette/AnyIO BlockingPortal deprecation warning

`git diff --check` passed.

No Objective 3A commit has been created yet.

---

## Verification-shell issue discovered

Do not re-investigate Guardian code because of the failed PowerShell staged-source assertions seen immediately before this checkpoint.

The source was successfully loaded using:

`git show ':src/ucii_guardian/web.py'`

but assigning native command output directly in PowerShell produces an array of lines.

Using:

`$StagedWeb -notmatch 'pattern'`

against that array returns the non-matching elements rather than one scalar Boolean test, causing a false failure even when the pattern exists.

When resuming, convert staged source to one string first, for example:

`$StagedWeb = (git show ':src/ucii_guardian/web.py') -join "`n"`

or:

`$StagedWeb = git show ':src/ucii_guardian/web.py' | Out-String`

Do not repeat the previous verification loop.

---

## Objective 3B — NEXT

Resume here immediately after the hackathon submission is safely sent.

Implement the smallest bounded Judge/Test web lifecycle addition:

1. Judge/Test Grant Standing Authority
   - use `JudgeAuthorityState.grant()`
   - do not call production `grant_standing_authority`

2. Judge/Test Revoke Authority
   - use `JudgeAuthorityState.revoke()`
   - do not call production `revoke_active_authority`

3. Judge/Test Reset
   - `JudgeAuthorityState.reset()`
   - clear pending escalation context
   - clear active-authority UI context
   - reset budget policy to known initial value
   - do not erase production authority
   - do not mutate UCII lifecycle state

4. Mode-aware rendering
   - visibly identify Judge/Test Mode
   - explicitly state authority state is isolated/non-production
   - continue real Guardian identity verification
   - never display Judge lifecycle actions as UCII-authoritative production grants/revocations

5. Production rendering/path
   - unchanged

---

## Required Judge lifecycle after Objective 3B

The completed judge flow must prove:

1. Reset -> verified Guardian identity + authority NOT_GRANTED
2. Grant Standing Authority -> isolated Judge authority ACTIVE
3. Set human-controlled Budget Range
4. In-budget request -> autonomous execution permitted
5. Over-budget request -> execution stops for human decision
6. APPROVE_ONCE -> exact exceptional request executes
7. Standing budget/authority remains unchanged
8. Another over-budget request + DENY -> no execution
9. Revoke Authority -> Judge authority REVOKED
10. New consequential request -> fresh authority evaluation sees REVOKED
11. No protected execution occurs
12. Reset -> known initial Judge/Test state

Core demonstration:

**Same Guardian. Same verified identity. Different authority state — different execution outcome.**

---

## Completion gate after submission

Do not add unrelated features.

Complete only:

1. Objective 3B implementation
2. targeted Judge/Test tests
3. complete Judge lifecycle E2E proof
4. production-path regression
5. full Guardian regression
6. production smoke verification

Then stop engineering.

---

## Submission priority

The hackathon submission takes priority over completing this optional replayability layer before submission.

The existing production Guardian is the authoritative system.

Judge/Test Mode is a repeatable judging-access layer, not a replacement for the production architecture.
