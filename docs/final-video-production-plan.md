# UCII Guardian — Final Video Production Plan

**Status:** LOCKED — Step 5 submission production package
**Event:** Agents for Humans Hackathon
**Target runtime:** 4:35–4:50
**Hard ceiling:** under 5:00

## Production objective

The video is a cause-and-effect product demonstration, not a code tour.

A judge should understand the problem in the first 30 seconds, see useful autonomy before seeing escalation, and finish with one unmistakable proof:

> **Same Guardian. Same verified identity. Same request. Same budget. Different authority state — different execution outcome.**

The story is:

**grant → human budget → autonomous execution → exception → approve once → deny → revoke → post-revocation refusal → architecture → close**

Primary line:

> **Capability is not authority.**

Supporting line:

> **Humans define the operating boundaries. Agents act autonomously inside them.**

Closing line:

> **Guardian is not designed to prevent autonomous AI. It is designed to make autonomous AI governable.**

---

## Recording format

Use a clean 16:9 desktop capture at 1080p if available. Keep the Guardian UI large enough that status labels, request text, Budget Range, human controls, and provenance can be read without zooming.

Record voice narration cleanly over the screen capture. Camera presence is unnecessary. Avoid background music unless it is extremely subtle; clarity matters more than production decoration.

Do not show terminals during the primary product story. The working UI is the evidence. The architecture diagram is the technical reveal after the behavior has been demonstrated.

Use hard cuts or very short fades only. Do not spend time on animated title sequences.

---

# Exact shot list and narration

## SHOT 1 — 0:00–0:25 — Open on the problem

### Screen

Guardian interface, clean initial state. No terminal, browser tabs, bookmarks, credentials, hostnames, or unrelated windows visible.

If useful, briefly overlay or show the line:

**CAPABILITY IS NOT AUTHORITY**

### Narration

> “Autonomous AI agents can increasingly make decisions and take real actions. But there is a missing layer: who is the agent, what is it actually allowed to do, how much economic authority does it have, and how can a human revoke that authority without destroying the agent’s identity?
>
> This is UCII Guardian. Capability is not authority.”

### Judge takeaway

This is an authority/governance problem, not another chatbot demo.

### Editing note

Do not explain cryptography, x402, SDK internals, or infrastructure here.

---

## SHOT 2 — 0:25–0:55 — Grant standing authority

### Screen action

Show that Guardian does not begin with usable standing authority for the demo action.

Click **Grant Standing Authority**.

Hold long enough for **ACTIVE** to be clearly visible.

### Narration

> “Guardian has a cryptographically verifiable identity, but identity alone does not grant permission to act. I’m granting this Guardian a bounded standing authority. The grant is explicit, attributable to the human, and independently revocable.”

Then:

> “Guardian now has authority. But authority still is not unlimited economic permission.”

### Judge takeaway

**Identity != standing authority.**

The human establishes delegation; the model does not grant authority to itself.

---

## SHOT 3 — 0:55–1:20 — Set Budget Range

### Screen action

Set **Budget Range** to exactly **$101.28** and apply it.

Hold on the accepted value.

### Narration

> “Now I set the maximum amount Guardian may spend autonomously on a request. I’ll choose one hundred one dollars and twenty-eight cents. Guardian cannot change this boundary itself.”

Then:

> “Humans define the operating boundaries. Agents act autonomously inside them.”

### Judge takeaway

**Standing authority != human economic policy.**

The unusual `$101.28` value helps demonstrate that the control is genuinely human-selectable rather than a canned `$100` threshold.

---

## SHOT 4 — 1:20–1:50 — Routine work proceeds autonomously

### Screen action

Enter exactly:

`Purchase one printer cartridge for $35.`

Click **Evaluate request**.

Hold on:

- Guardian Decision: **ALLOW**
- Authority: **ACTIVE**
- Execution: **Completed**
- Budget: `$101.28`

If the activity/provenance panel is visible without clutter, allow the completed lifecycle to appear naturally.

### Narration

> “Thirty-five dollars is inside the human-selected budget. Guardian’s identity verifies, its standing authority is active, and the request is inside my economic boundary, so Guardian completes the routine task without interrupting me.”

Then, briefly:

> “This is bounded autonomy — not constant human approval.”

### Judge takeaway

Guardian is useful. It does not ask a human before every action.

---

## SHOT 5 — 1:50–2:30 — Cross the boundary and Approve Once

### Screen action

Enter exactly:

`Purchase one printer cartridge for $150.`

Click **Evaluate request**.

Hold on:

- Guardian Decision: **ALLOW**
- Authority: **ACTIVE**
- Execution: **Awaiting human decision**
- `BUDGET_RANGE_EXCEEDED`
- **Approve Once** and **Deny** available

Make sure the judge has time to see that execution has not occurred.

Then click **Approve Once**.

Hold on completed execution and unchanged `$101.28` Budget Range.

### Narration

> “Now I’ll request one hundred fifty dollars. UCII still says Guardian has authority for this class of action, but the request exceeds the economic boundary I established. Guardian stops before execution.”

After clicking Approve Once:

> “I can approve this exact exception once. That allows this request to complete, but it does not increase Guardian’s budget or broaden its standing authority.”

### Judge takeaway

**One-time approval != standing authority != budget modification.**

This is human exception handling without silently expanding future autonomy.

---

## SHOT 6 — 2:30–2:55 — Deny another exception

### Screen action

Enter exactly:

`Purchase one printer cartridge for $175.`

Click **Evaluate request**.

After the escalation appears, click **Deny**.

Hold briefly on:

- Human decision: **DENY**
- Authority: **ACTIVE**
- Execution: **No execution**
- Budget still `$101.28`

### Narration

> “A different exception reaches the same boundary. This time I deny it. Nothing executes, and Guardian’s standing authority and budget remain unchanged.”

### Judge takeaway

The human retains judgment over exceptions without destroying ordinary standing authority.

Keep this scene fast.

---

## SHOT 7 — 2:55–3:40 — Revoke and prove the difference

### Screen action

Click **Revoke Authority**.

Hold on:

- Authority: **REVOKED**
- Execution: **No execution**

Then enter exactly the original routine request again:

`Purchase one printer cartridge for $35.`

Click **Evaluate request**.

Hold on:

- identity still verified
- Guardian Decision: **DENY**
- Authority: **REVOKED**
- Execution: **No execution**

Do not rush this screen. This is the strongest proof in the video.

### Narration

> “Now I revoke Guardian’s standing authority.”

After the UI shows REVOKED:

> “I’ll submit the same thirty-five-dollar request that previously executed automatically.”

After denial:

> **“Same Guardian. Same verified identity. Same request. Same budget. Different authority state — different execution outcome.”**

Then:

> “Nothing happened to the AI. It is still running. Its identity still verifies. It still knows how to request the action. What changed is its authority. I revoked it, so it cannot cross the protected execution boundary.”

### Judge takeaway

This is the central Guardian proof:

**running software != identity != continuing authority.**

Revocation changes real execution behavior rather than merely changing a UI label.

---

## SHOT 8 — 3:40–4:20 — Technical reveal

### Screen

Cut to `docs/guardian-architecture.svg`, rendered cleanly at readable size.

Optionally use a simple pointer/highlight while narrating, but do not animate the entire diagram.

### Narration

> “The reason this behavior is meaningful is that Guardian separates things autonomous systems often blur together: capability, identity, standing authority, human policy, one-time approval, execution, and provenance.”

> “AWS Strands Agents handles the agent reasoning and turns natural-language intent into bounded action requests. But the model is not the source of its own authority.”

> “UCII independently establishes Guardian’s cryptographic identity and delegated authority. Guardian then applies the human-controlled Budget Range and requires valid authority before protected consequential execution.”

> “The activity record preserves why the action was allowed, escalated, denied, executed, or refused.”

### On-screen concept

Display or point to:

**Capability != Identity != Authority != Human Policy != Approval != Execution**

### Judge takeaway

Strands is real and central to the agent behavior, but authority is deliberately outside the model’s self-assertion.

---

## SHOT 9 — 4:20–4:45 — Generalize and close

### Screen

Remain on architecture diagram or cut back to Guardian’s post-revocation state. Prefer whichever looks cleaner in the final edit.

### Narration

> “This demo uses an office-supply purchase because the boundary is easy to see. But the same authority model can apply to deploying code, moving funds, accessing enterprise infrastructure, or operating other consequential systems.”

Then close deliberately:

> **“UCII Guardian is not designed to prevent autonomous AI. It is designed to make autonomous AI governable.”**

> **“Capability is not authority.”**

### End

Stop. No additional technical appendix, credits sequence, or rambling outro.

Target final runtime: **approximately 4:45**.

---

# Screen-state rehearsal table

| Scene | Request / action | Decision | Authority | Execution | Budget |
|---|---|---|---|---|---|
| Grant | Grant Standing Authority | — | ACTIVE | No execution | $0.00 initially |
| Budget | Set Budget Range | — | ACTIVE | No execution | $101.28 |
| Routine | $35 purchase | ALLOW | ACTIVE | Completed | $101.28 |
| Exception 1 | $150 purchase | ALLOW + escalation | ACTIVE | Awaiting human decision | $101.28 |
| Approve Once | exact $150 exception | APPROVE_ONCE | ACTIVE | Completed | $101.28 |
| Exception 2 | $175 purchase | ALLOW + escalation | ACTIVE | Awaiting human decision | $101.28 |
| Deny | exact $175 exception | DENY | ACTIVE | No execution | $101.28 |
| Revoke | Revoke standing authority | — | REVOKED | No execution | $101.28 |
| Post-revoke | same $35 purchase | DENY | REVOKED | No execution | $101.28 |

The final edit must not claim a UI state that is not visibly produced by the recorded run.

---

# Provenance moments to preserve

Do not turn the video into a provenance log tour. Let the activity evidence support the visible decisions.

The most valuable lifecycle evidence to leave readable where practical is:

- `REQUEST_RECEIVED`
- `IDENTITY_VERIFIED`
- `AUTHORITY_CHECKED`
- `AUTHORIZED`
- `HUMAN_APPROVED` for the one-time exception
- `HUMAN_DENIED` for the denied exception
- `EXECUTION_STARTED`
- `EXECUTION_COMPLETED`
- `AUTHORITY_REVOKED`
- `EXECUTION_REFUSED`

The post-revocation sequence is especially important: identity verification should coexist visibly with revoked authority and refused execution.

---

# Pre-recording checklist

Before recording the final take:

- Fast-forward the local Guardian checkout to the synchronized submission tip.
- Confirm the worktree is clean.
- Confirm the Guardian app starts normally.
- Confirm the UCII service required by the demo is healthy.
- Use a fresh demo state that can complete the full grant-to-revoke lifecycle once.
- Confirm the starting Budget Range is `$0.00`.
- Confirm there is no usable standing authority for the fresh demo grant before clicking Grant Standing Authority.
- Confirm Grant Standing Authority is available.
- Confirm Budget Range accepts `$101.28`.
- Confirm the exact `$35`, `$150`, and `$175` requests normalize correctly.
- Confirm Approve Once and Deny controls appear only for the pending exception state.
- Confirm Revoke Authority is available only for the active evaluated authority context required by the product.
- Confirm post-revocation `$35` produces `DENY / REVOKED / No execution`.
- Confirm the architecture SVG renders correctly at recording size.
- Close email, chat, password managers, cloud consoles, unrelated browser tabs, and private documents.
- Hide bookmarks/favorites if they expose private information.
- Disable desktop notifications and operating-system popups.
- Do not display API keys, bearer tokens, passwords, private keys, controller credentials, entitlement proofs, environment variables, private host information, or production-sensitive terminal output.
- Use a clean browser window containing only Guardian and the architecture diagram.
- Set browser zoom so all important Guardian controls and status values are legible.
- Put the mouse pointer somewhere unobtrusive before each narration segment.
- Record a short audio test and verify microphone level before the real take.
- Have the narration visible on a second device or screen that is not captured.

---

# Recording strategy

Prefer one clean continuous product run for Shots 1–7 so the lifecycle feels real and causal. If a mistake occurs, restart the demo from a genuinely valid fresh state rather than editing together states that imply a lifecycle that did not happen.

The architecture/closing section can be recorded separately and cut onto the end.

Record at least two complete clean takes if time permits. Keep the first successful take; do not risk losing a valid submission while chasing cosmetic perfection.

Do not make production edits that alter the apparent order of security-relevant events.

---

# Narration discipline

Speak slightly slower than normal conversation. Pause after the strongest visual state changes, especially:

- `ACTIVE`
- `$101.28`
- `$35 -> Completed`
- `$150 -> Awaiting human decision`
- Approve Once -> Completed while budget stays `$101.28`
- `$175 -> Deny -> No execution`
- `REVOKED`
- post-revocation `$35 -> DENY / No execution`

Do not narrate every field on screen. Explain the cause-and-effect relationship.

Do not say Guardian “asks permission for every action.” It does not.

Do not say UCII identity itself authorizes execution. It does not.

Do not say Approve Once changes standing authority or budget. It does not.

Do not say revocation deletes Guardian’s identity. It does not.

Do not claim Guardian solves all AI alignment, prompt injection, or AI safety problems.

Do not claim historical priority over other identity/authorization systems.

---

# Editing checklist

After recording:

- Keep final runtime below 5:00; target 4:35–4:50.
- Remove dead air, setup delays, cursor hunting, and loading pauses that add no proof.
- Preserve enough time to read every decisive state change.
- Keep text overlays sparse and large.
- If captions are added, verify technical terms manually: `UCII`, `Strands`, `Approve Once`, `Budget Range`, `REVOKED`, and `Capability is not authority`.
- Normalize voice volume; avoid aggressive noise processing that makes speech difficult to understand.
- Do not add copyrighted music or assets without appropriate rights.
- Verify no single frame exposes credentials or private information.
- Watch the exported video once from beginning to end before upload.
- Verify the uploaded video itself plays correctly and remains under the hackathon duration limit.

---

# Five-minute emergency cut plan

If the first edit runs long, cut in this order:

1. shorten the Deny scene narration;
2. shorten transitions between requests;
3. shorten the architecture explanation;
4. shorten the opening by 5–10 seconds.

Do **not** cut:

- the `$35` autonomous success;
- the `$150` budget escalation;
- Approve Once preserving the budget;
- revocation;
- the post-revocation `$35` denial;
- the statement that identity remains valid after authority is revoked.

Those are the core proofs.

---

# Final judge test

Before accepting the final video, watch it once without looking at code or README and answer yes/no:

1. Is it obvious within 30 seconds what human problem Guardian solves?
2. Is Guardian visibly autonomous for routine authorized work?
3. Is the `$101.28` boundary visibly human-controlled?
4. Does `$150` visibly stop before execution?
5. Does Approve Once visibly avoid changing the standing budget?
6. Does Deny visibly result in no execution?
7. Does revocation visibly change a real subsequent execution outcome?
8. Is Guardian’s identity still valid after revocation?
9. Is Strands’ role explained without implying the LLM grants its own authority?
10. Can a non-specialist explain the idea afterward as “the AI can act, but it only has the authority the human gave it”?

If all ten answers are yes, the video is doing its job.

---

# Final production rule

The video does not need to prove every line of the codebase.

It needs to prove one complete, credible human-governed authority lifecycle so clearly that the judge cannot miss the point:

> **The industry is making AI agents more capable. Guardian demonstrates how humans can let them use that capability without granting unlimited authority.**
