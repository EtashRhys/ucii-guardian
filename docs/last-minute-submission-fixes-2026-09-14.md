# UCII Guardian — Final Submission Lock

Date: 2026-09-14
Status: FINAL SUBMISSION CHECKLIST — NO FEATURE CREEP
Track: Professional Agents — Agents for Humans Hackathon

## Purpose

This is the single final checklist for the remaining work before UCII Guardian is submitted.

Production Guardian engineering is complete and stable. Do not reopen implementation work unless a concrete submission blocker is discovered.

Submission-day sequence:

> Judge/Test Mode → prove it → regression → video cleanup → repository audit → make Guardian public → verify externally → upload video → complete Devpost → final audit → submit.

No new features. No UCII redesign. Do not weaken production UCII security for judging convenience.

## 1. Judge/Test Mode — Remaining Engineering Item

The production Guardian lifecycle intentionally uses protected, short-lived, one-use authorization for consequential Grant Standing Authority and Revoke Authority operations. That production security property stays intact.

Add one narrowly scoped, resettable **Guardian Judge/Test Mode** so judges can exercise the complete Guardian story without relying on the expiring production lifecycle window.

Required judge flow:

1. Start/reset with verified Guardian identity and authority `NOT GRANTED`.
2. **Grant Standing Authority** → isolated test authority becomes `ACTIVE`.
3. Set the human-controlled **Budget Range**.
4. Submit an in-budget request → normal Guardian policy path permits autonomous execution.
5. Submit an over-budget request → Guardian stops and requests a human decision.
6. **Approve Once** → exactly that exceptional request executes without changing the standing budget or standing authority.
7. Submit another over-budget request and **Deny** → no execution.
8. **Revoke Authority** → isolated test authority becomes `REVOKED`.
9. Submit another consequential request → fresh authority evaluation finds revoked authority and no protected execution occurs.
10. **Reset Demo/Test** → restore a known initial judge state.

Architecture boundary:

`Production Guardian → real UCII lifecycle → protected authorization → protected execution`

`Judge/Test Guardian → isolated non-production authority state → same Guardian policy behavior → non-production execution demonstration`

Implementation rules:

- Begin with read-only inspection of the existing Guardian authority/lifecycle seam.
- Reuse existing tests, fixtures, abstractions, and policy logic wherever possible.
- Do not build a parallel Guardian application.
- Select Judge/Test Mode server-side at startup/configuration, not from browser-controlled state.
- Make Judge/Test Mode visibly identifiable in the UI.
- Keep it structurally isolated from production lifecycle authority.
- Do not add a new daemon, custody system, authorization subsystem, or production dependency.
- Do not modify UCII's production timeout, one-use lifecycle authorization, or controller-authority mechanism.

Judge disclosure should clearly state that the judging environment uses isolated non-production authority state so the complete lifecycle can be exercised repeatedly, while production Guardian uses UCII's protected expiring and one-use lifecycle authorization mechanism.

Completion gate:

- targeted Judge/Test Mode tests pass;
- production-path tests remain passing;
- full Guardian regression passes;
- complete judge flow succeeds end to end;
- reset restores known initial state;
- production lifecycle path remains unchanged;
- final local smoke test passes.

Known stable production baseline before this judging-access addition:

- Guardian checkpoint: `4bef04e5a01f6065c6cbdd89fb9cc416119af926`
- full regression: `272 passed, 2 warnings`
- smoke: `GET /` HTTP 200 and `UCII Guardian` present.

This item does not reopen unrelated production engineering.

## 2. Final Video Cleanup

Keep the final video under the hackathon's five-minute maximum. Target roughly 3:45–3:55 after dead-air cleanup if all proof states remain clear.

Preserve:

- Grant Standing Authority;
- human Budget Range;
- `$35` → autonomous allowed/completed path;
- `$150` → outside budget → awaiting human decision;
- **Approve Once** → exact exceptional request executes;
- `$175` → **Deny** → no execution;
- Revoke Authority;
- post-revocation consequential request → no protected execution;
- identity remains verified while delegated authority is revoked.

Actual final demo Budget Range is **$111.02**. Narration must match the recording.

Cut dead air, cursor travel, unnecessary waiting, and excessive holds. Do not cut evidence needed to understand authority transitions.

Correct the generated end-card typo:

- WRONG: `Fresh buthority checks`
- CORRECT: `Fresh authority checks`

Final watch-through must confirm narration matches the visual state and dollar values, text remains readable, audio is clear, proof states are visible, architecture is understandable, and duration is under five minutes.

## 3. Revised Closing Narration — LOCKED

The purchasing Budget Range is the **demonstration policy boundary**, not the definition of Guardian.

Use this closing narration:

> The architecture keeps these domains deliberately separate. AWS Strands handles agent reasoning and request normalization. UCII establishes cryptographic identity and delegated authority. Guardian applies human-defined policy boundaries, and protected execution occurs only after the required checks pass.
>
> In this demonstration, that boundary is a purchasing budget. But the same authority model can extend much further: which actions an agent may perform, which systems or resources it may access, who it may interact with, when and where it may operate, transaction and usage limits, time-bounded permissions, and actions that always require explicit human approval.
>
> The result is not just control over AI spending. It is a framework for giving increasingly capable autonomous agents precisely bounded authority — authority that can be verified, constrained, audited, and revoked.
>
> UCII Guardian: autonomous inside the boundary, human-controlled beyond it.

Use future/extension language such as **“can extend”** for controls not implemented in the hackathon build. Do not imply every future restriction above is already enforced today.

Core conceptual takeaway:

> We are not trying to predict every dangerous thing an autonomous agent might someday do. We are creating an architecture in which consequential capabilities can be placed behind independently enforceable authority boundaries.

Guardian is not merely an AI purchasing-budget application. The budget is one concrete proof of the broader authority-control architecture.

## 4. Final Private Repository Audit

Before changing visibility, verify:

- README is accurate and judge-facing;
- architecture diagram exists and renders;
- Devpost submission copy is current;
- demo/video documentation matches the actual final demo;
- Judge/Test Mode startup and reset instructions are explicit;
- setup instructions are sufficient for a judge to run the test build;
- root Apache License 2.0 `LICENSE` remains present;
- prior-work disclosure remains clear: **UCII Guardian is the new hackathon project; UCII is pre-existing infrastructure**;
- nothing suggests the private UCII implementation is licensed as part of Guardian;
- repository commands and paths are current;
- temporary demo/debug artifacts are not included;
- final regression and smoke evidence is truthful.

Only Guardian is intended to become public. UCII remains private.

## 5. Public Repository Transition — Last Practical Moment

After the private audit and Judge/Test Mode verification:

1. Switch `EtashRhys/ucii-guardian` from private to public.
2. Verify it opens unauthenticated.
3. Verify README renders correctly.
4. Verify architecture SVG renders correctly.
5. Verify Judge/Test instructions are visible and usable.
6. Verify root `LICENSE` is visible.
7. Verify GitHub recognizes/displays Apache-2.0 license metadata.
8. Verify Guardian's public repository does not expose private UCII implementation material.

Do not change UCII visibility.

## 6. Final Video Upload

After final export and watch-through:

- upload the final demo publicly to YouTube or Vimeo;
- verify playback unauthenticated;
- confirm duration is under five minutes;
- use that exact public URL in Devpost.

## 7. Devpost Submission

Track: **Professional Agents**

Tagline:

> **Capability is not authority. Give autonomous AI bounded, human-controlled, cryptographically verifiable authority.**

For the AWS Builder ID field, use the email address associated with the Builder ID.

The pitch must clearly communicate:

1. **Problem** — increasingly capable autonomous agents should not automatically receive unlimited consequential authority.
2. **Who it is for** — people and organizations that want autonomous agents to perform useful work while retaining enforceable human control over consequential actions.
3. **Why it matters** — identity alone is not permission; autonomy needs bounded, independently verifiable, revocable authority.

Key proof sentence:

> **Same Guardian. Same verified identity. Different authority state — different execution outcome.**

Core domain separation:

> **Capability ≠ Identity ≠ Authority ≠ Human Policy ≠ Approval ≠ Execution**

Use the final public Guardian repository URL and final public video URL.

## 8. Final Submission Gate

Immediately before Submit, confirm:

- Guardian repository is public and opens unauthenticated;
- Apache-2.0 license is present and visible;
- Judge/Test Mode is documented, reproducible, and isolated from production lifecycle authority;
- setup/test instructions work from a clean environment as far as practical;
- final demo video is public and plays unauthenticated;
- video is under five minutes;
- narration matches the recorded demo;
- Professional Agents track is selected;
- Builder ID email field is complete;
- project description is complete;
- repository URL is correct;
- video URL is correct;
- prior-work disclosure is accurate;
- architecture diagram is included/accessible;
- no required field remains blank;
- no last-minute feature has been added without verification.

Then submit with time to spare.

## 9. Explicitly Optional — Do Not Prioritize

Do not spend submission-day time chasing optional opportunities while any mandatory item above remains unfinished.

Do not prioritize bonus/promotional posts, additional Guardian capabilities, new UCII features, implementation of future restriction types, unrelated infrastructure deployment, or cosmetic work beyond correcting real errors.

## Final Lock

The submission story is:

> Powerful AI agents need a way to work autonomously without automatically receiving unlimited authority.
>
> UCII Guardian separates capability, cryptographic identity, delegated authority, human policy, approval, and execution. It allows autonomous work inside human-defined boundaries, requires explicit human intervention outside them, and supports revocation without destroying the agent's identity.
>
> The purchasing budget is one concrete demonstration of a broader model for precisely bounded, verifiable, auditable, and revocable autonomous authority.

**Submission-day rule: prove what is already built, make it easy to judge, remove avoidable friction, and submit.**
