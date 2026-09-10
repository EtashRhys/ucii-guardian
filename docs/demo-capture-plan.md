# UCII Guardian — Development Demo Capture Plan

## Purpose

Capture short, high-value development proofs as Guardian reaches meaningful milestones. These clips are backup/demo material, not a continuous development recording and not automatically the final Devpost video.

## Recording rule

Do **not** continuously screen-record development. Record only when a milestone below has been verified and is ready to demonstrate cleanly.

Before every capture:

- close or hide unrelated/private windows;
- ensure terminals do not display API keys, tokens, passwords, private keys, credentials, environment variables, host secrets, or other sensitive values;
- use sanitized/demo identities and data where practical;
- start recording immediately before the proof;
- stop immediately after the proof;
- keep the clip short and focused;
- name/store the clip by milestone and date so it can be found later.

## Capture milestones

### Capture 1 — First real Strands Guardian

**When:** Objective 1 has passed its targeted verification.

Capture:

- Guardian receiving a natural-language request;
- AWS Strands actually orchestrating the request;
- Guardian producing the normalized bounded `ActionRequest` / action envelope;
- clear evidence that no consequential action is executable yet.

**Why it matters:** Proves Strands is genuinely central rather than decorative.

### Capture 2 — Guardian proves its UCII identity

**When:** Objective 2 is verified.

Capture:

- Guardian authenticating through the public UCII boundary;
- its UCII identity being established/verified;
- a clean failure example if it can be shown quickly without clutter.

**Why it matters:** Shows the agent is a cryptographically identifiable actor rather than an anonymous model process.

### Capture 3 — First autonomous authorized action

**When:** Objectives 3 and 4 are verified together end-to-end.

Capture:

- a routine request;
- Guardian checking authority;
- an `ALLOW` decision;
- protected executor accepting the verified authorization;
- successful consequential execution without human interruption.

**Why it matters:** This is the first proof that Guardian provides useful autonomy, not merely security prompts.

### Capture 4 — Guardian refuses to exceed authority

**When:** The out-of-scope/escalation path is verified.

Capture:

- a legitimate request exceeding the delegated boundary;
- Guardian identifying the exact boundary that was exceeded;
- `ESCALATION_REQUIRED`;
- proof that execution did **not** occur.

**Why it matters:** Demonstrates bounded autonomy and preserves human judgment.

### Capture 5 — Human approval unlocks one exceptional action

**When:** Objective 5 is verified.

Capture:

- Guardian's concise approval request;
- the reason approval is required;
- the human selecting `Approve Once`;
- the bounded approval being recognized;
- the exceptional action executing successfully.

If practical, separately capture `Deny` causing no execution.

**Why it matters:** Shows the complete human/agent authority handoff.

### Capture 6 — Revocation actually stops Guardian

**When:** Objective 6 is verified.

This is a **priority capture**.

Capture as one coherent sequence if possible:

1. authority is active;
2. an authorized action succeeds;
3. the human revokes the authority;
4. an equivalent/new attempt is made;
5. Guardian re-checks authority;
6. the request is denied;
7. no consequential execution occurs.

**Why it matters:** This is likely one of Guardian's strongest differentiators. It proves revocation is operational, not merely a UI label or policy statement.

### Capture 7 — Full provenance reconstruction

**When:** Objective 7 is verified.

Capture:

- the readable Guardian activity/provenance history;
- request received;
- identity verification;
- authority decision;
- escalation/human decision where applicable;
- execution or refusal;
- revocation and post-revocation denial.

**Why it matters:** Shows that a human can determine what happened, why it happened, and who held the consequential decision.

### Capture 8 — First polished end-to-end Guardian UI run

**When:** Objective 8 is verified.

Capture the entire intended product story through the minimal interface:

1. routine authorized action proceeds quietly;
2. boundary-exceeding action escalates;
3. human approves or denies;
4. approved exceptional action executes;
5. authority is revoked;
6. later reuse is denied;
7. provenance explains the lifecycle.

**Why it matters:** This becomes rehearsal/reference material for the final hackathon recording.

### Capture 9 — Final submission candidate

**When:** Objectives 9+ are stable and the demo environment has passed a clean rehearsal.

Record a **fresh** deliberate submission video rather than stitching together development footage unless there is a strong reason to reuse a milestone clip.

Target structure:

- problem;
- who Guardian is for;
- why the problem matters;
- architecture/Strands role briefly;
- complete working Guardian demonstration;
- UCII authority/identity/revocation value;
- concise closing impact statement.

The public Devpost video must remain within the hackathon's maximum duration.

## Canonical autonomy / authority story

The Guardian demo should make this distinction prominent rather than burying it in implementation detail:

> **We don't prevent AI from being autonomous. We prevent autonomy from becoming unlimited authority.**

Guardian is not intended to suppress useful autonomy. An autonomous agent may continue reasoning, planning, running, calling non-consequential tools, and proposing work. What it must not be able to do is convert technical capability into unlimited consequential authority merely because the model wants to proceed.

The practical control problem Guardian demonstrates is:

> **How do we prevent an autonomous agent from taking consequential actions beyond the authority its human actually gave it?**

Do **not** overclaim that Guardian solves every form of AI alignment, model behavior, or hypothetical rogue-AI risk. The narrower claim is stronger because the demo can prove it directly:

> **UCII Guardian demonstrates how autonomous AI agents can remain under human-controlled, cryptographically verifiable, revocable authority even while the agents themselves continue operating autonomously.**

A second canonical line should be explicit in the presentation:

> **Capability is not authority.**

The model may still work. The Strands process may still be running. The agent may still know how to invoke a tool. It may still have network connectivity, credentials, or access to a payment mechanism. None of those facts independently establish permission to perform a particular consequential action.

Guardian makes several UCII distinctions visible to a judge through cause and effect:

- identity is not authentication;
- authentication is not authorization;
- authorization is not execution;
- capability is not authority;
- payment proves settlement, not permission.

The architectural point is that the consequential authority decision is evaluated outside the agent's probabilistic reasoning loop. Guardian should not depend on a prompt such as `never spend more than $25` as the security boundary. The agent proposes the action; the deterministic authority boundary decides whether the action is permitted.

### Recommended cause-and-effect sequence

The demo should make the control model understandable before explaining the cryptography:

```text
$12.40 REQUEST
    -> WITHIN DELEGATED AUTHORITY
    -> ALLOW
    -> NO HUMAN INTERRUPTION

$89.00 REQUEST
    -> OUTSIDE DELEGATED AUTHORITY
    -> STOP / ESCALATE
    -> HUMAN DECISION

HUMAN REVOKES AUTHORITY
    -> AGENT REMAINS RUNNING
    -> AGENT TRIES AGAIN
    -> CURRENT AUTHORITY CHECK FAILS
    -> DENIED
```

The revocation moment should be explained explicitly:

> **The agent is still running. Its model still works. It still knows how to request the action. What changed is its authority. The human revoked it, so the consequential action cannot proceed.**

This demonstrates another important line:

> **Running software does not equal continuing authority.**

### Why this matters beyond purchasing

The purchasing workflow is deliberately simple, but the demonstrated authority pattern generalizes to consequential autonomous actions involving:

- money and payments;
- data access or disclosure;
- communications;
- contracts and documents;
- infrastructure changes and software deployment;
- other agents and tools;
- devices, robots, vehicles, and industrial systems.

The broader question remains the same:

> **Does this autonomous principal currently possess authority for this specific consequential action under the applicable constraints?**

The demo should explain this broader relevance without adding additional hackathon workflows or expanding implementation scope.

### Judging significance

The strongest contrast is not "our agent can do more." It is:

> **The industry is making agents more capable. Guardian demonstrates how humans can let them use that capability without granting unlimited authority.**

This supports the judging story directly:

- **Technological Implementation:** real Strands behavior combined with UCII identity, authority enforcement, human escalation, revocation, and attributable evidence;
- **Design:** routine authorized work proceeds quietly, while only insufficient-authority cases interrupt the human;
- **Potential Impact:** the authority model applies to many consequential autonomous workflows;
- **Creativity & Originality:** Guardian is a human authority/control layer for autonomous agents rather than another task-performing assistant;
- **Presentation:** judges can see `$12.40 -> allow`, `$89 -> escalate`, and `revoke -> deny` before any architecture lecture.

### Suggested opening and closing framing

Potential opening:

> **AI agents are becoming capable of doing real work on our behalf. But capability is not authority. UCII Guardian lets an agent remain autonomous without allowing that autonomy to become unlimited authority.**

Potential closing:

> **We don't prevent AI from being autonomous. We prevent autonomy from becoming unlimited authority.**

These are presentation notes, not permission to add features. The stronger story changes how the existing minimum Guardian vertical slice is demonstrated; it does **not** expand what must be built before the hackathon deadline.

## Assistant/operator reminder protocol

Before beginning work that is expected to complete one of the capture milestones above, explicitly flag it in the development session:

> **SCREEN-RECORD MILESTONE APPROACHING — do not record yet. I will tell you after verification when the proof is ready.**

After the milestone has passed verification and immediately before demonstrating it, explicitly say:

> **SCREEN-RECORD NOW — Milestone N: [name].**

Do not ask the operator to record unverified, broken, secret-bearing, or noisy development output.

## Priority if time becomes constrained

If only a few development captures are possible, prioritize:

1. Capture 6 — revocation actually stops Guardian;
2. Capture 3 — autonomous authorized execution;
3. Capture 4/5 — escalation and bounded human approval;
4. Capture 7 — provenance reconstruction;
5. Capture 8 — polished end-to-end UI run.

## Security rule

A useful demo clip is never worth exposing a reusable secret. If a milestone cannot be captured safely, sanitize the environment first or skip the development capture and reproduce the behavior later with demo-safe credentials/data.
