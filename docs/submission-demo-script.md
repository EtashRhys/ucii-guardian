# UCII Guardian — Hackathon Submission Demo Script

**Status:** LOCKED — Step 1 submission narrative
**Event:** Agents for Humans Hackathon
**Purpose:** Judge-facing five-minute demo sequence and core positioning

## Core Story

> **AI agents are becoming capable enough to act for us. But capability is not authority.**
>
> **UCII Guardian lets humans define the boundaries, then lets the agent work autonomously inside them.**

The demo should make the human problem understandable before introducing implementation detail. Do not lead with cryptographic primitives, SDK internals, lifecycle services, entitlement proofs, controller authority, x402, or other infrastructure. First show the problem, then show the working product, then explain the architecture that makes the behavior trustworthy.

## Target Runtime

Target total runtime: **approximately 4:30–4:50**.

The video must remain below the five-minute submission limit, leaving a safety margin for transitions and recording variance.

---

## 0:00–0:30 — The Problem

Show the Guardian interface.

Narration:

> “Autonomous AI agents can increasingly make decisions and take real actions. But there is a missing layer: who is the agent, what is it actually allowed to do, how much economic authority does it have, and how can a human revoke that authority without destroying the agent’s identity?
>
> UCII Guardian solves that problem.”

Primary idea:

> **Capability is not authority.**

---

## 0:30–1:05 — Establish Standing Authority

Explain that Guardian has a cryptographically verifiable identity, but identity alone does not grant permission to act.

Click:

**Grant Standing Authority**

Narration:

> “I’m granting this Guardian a bounded standing authority. The grant is explicit, attributable to the human, and independently revocable.”

Show the authority state becoming **ACTIVE**.

Then state:

> “Guardian now has authority. But authority still isn't unlimited economic permission.”

Key distinction:

**Identity != standing authority.**

---

## 1:05–1:35 — Set the Human Operating Boundary

Set:

**Budget Range → $101.28**

Use the specific value `$101.28` intentionally. It demonstrates that the control is real and human-selectable rather than a canned `$100` demonstration.

Narration:

> “The human sets the maximum amount Guardian may spend autonomously on a request. Guardian cannot change this limit itself.”

Primary product line:

> **Humans define the operating boundaries. Agents act autonomously inside them.**

Key distinction:

**Standing authority != human economic policy.**

---

## 1:35–2:05 — Routine Work Proceeds Autonomously

Enter exactly:

`Purchase one printer cartridge for $35.`

Click **Evaluate request**.

Expected result:

- Guardian Decision: **ALLOW**
- Authority: **ACTIVE**
- Execution: **Completed**
- Human control: current delegated authority permits this action

Narration:

> “Thirty-five dollars is inside the human-selected budget, Guardian's identity verifies, its standing authority is active, so it completes the routine task without interrupting me.”

This scene demonstrates the hackathon’s core human-agent behavior: routine work proceeds without unnecessary human interruption.

---

## 2:05–2:45 — Escalate Only When Human Judgment Is Required

Enter exactly:

`Purchase one printer cartridge for $150.`

Click **Evaluate request**.

Expected result:

- Guardian Decision: **ALLOW**
- Authority: **ACTIVE**
- Execution: **Awaiting human decision**
- Human control: `BUDGET_RANGE_EXCEEDED`
- No execution begins

Narration:

> “Notice what happened. UCII still says Guardian has authority to perform this type of action. But $150 exceeds the economic boundary I established. Guardian stops before execution.”

Click:

**Approve Once**

Expected result:

- Human decision: **APPROVE_ONCE**
- Execution: **Completed**
- Budget remains `$101.28`
- Standing authority is unchanged

Narration:

> “I can approve this exact exception once. That does not increase Guardian's budget or expand its standing authority.”

Key distinction:

**One-time approval != standing authority != budget modification.**

---

## 2:45–3:15 — Deny an Exception

Enter exactly:

`Purchase one printer cartridge for $175.`

Click **Evaluate request**.

Guardian should again stop before execution because the request exceeds the human-selected budget.

Click:

**Deny**

Expected result:

- Human decision: **DENY**
- Execution: **No execution**
- Standing authority remains unchanged
- Budget remains `$101.28`

Narration:

> “Or I can deny the exception. Nothing executes.”

Keep this scene short. The UI should carry most of the explanation.

---

## 3:15–4:00 — Revoke Standing Authority

Click:

**Revoke Authority**

Expected result:

- Authority: **REVOKED**
- Execution: **No execution**
- Guardian identity remains verified

Then enter the original routine request again:

`Purchase one printer cartridge for $35.`

Click **Evaluate request**.

Expected result:

- Guardian Decision: **DENY**
- Authority: **REVOKED**
- Execution: **No execution**

Primary narration:

> **“Same Guardian. Same verified identity. Same request. Same budget. Different authority state — different execution outcome.”**

Then explain:

> “Revocation did not destroy Guardian's identity. It removed the delegated authority.”

This is the central live proof of the Guardian authority architecture.

---

## 4:00–4:35 — Explain the Architecture the Judge Just Saw

Transition to the architecture diagram.

Narration:

> “Guardian separates things that autonomous systems often blur together: capability, identity, standing authority, human policy, one-time approval, execution, and provenance.”
>
> “The Strands agent proposes and performs work. It is not the source of its own authority. UCII independently establishes identity and delegated authority, while Guardian enforces the human-controlled operating boundary before consequential execution.”

Display the conceptual separation prominently:

**Capability != Identity != Authority != Human Policy != Approval != Execution**

The architecture diagram should be optimized for this story rather than attempting to show the entire UCII platform.

---

## 4:35–4:50 — Close

End on either Guardian or the architecture graphic.

Closing narration:

> **“UCII Guardian is not designed to prevent autonomous AI. It's designed to make autonomous AI governable.”**
>
> **“Capability is not authority.”**

Stop there. Do not dilute the ending with implementation detail.

---

## Judge-Facing Success Criteria

The demo must visibly prove all of the following:

1. A verified Guardian identity does not itself create authority.
2. A human can grant bounded standing authority.
3. A human can establish a per-request autonomous Budget Range.
4. Routine work inside both standing authority and human policy executes autonomously.
5. An over-budget request stops before consequential execution.
6. **Approve Once** permits only the exact exception without increasing the budget or broadening standing authority.
7. **Deny** prevents execution.
8. A human can revoke the standing delegation without destroying Guardian's identity.
9. The same previously allowed request is denied after revocation.
10. Provenance/activity evidence explains the important state transitions and outcomes.

---

## Submission Positioning

The submission should consistently use these lines:

> **Capability is not authority.**

> **Humans define the operating boundaries. Agents act autonomously inside them.**

> **Guardian is not designed to prevent autonomous AI. It is designed to make autonomous AI governable.**

The judge should understand within the first 30 seconds that Guardian is not merely a chatbot, approval UI, or spending-limit demo. It is a human-governed authority layer for autonomous agents in which identity, standing authority, human policy, one-time approval, execution, and provenance remain distinct.

## Scope Firewall

For the submission demo, do not expand into unrelated UCII systems or additional product surfaces. Do not introduce Scout, Ambassador, Mission Control, D.8, Grokbot work, generalized RBAC, generalized accounting, voice architecture, or speculative future features.

The demo is deliberately one complete authority story:

**grant → human budget → autonomous execution → exception → approve once / deny → revoke → post-revocation refusal**

That complete cause-and-effect story is the product demonstration.
