# Guardian Human Authority Revocation Control

## Objective 8F — Revoke Authority button

**Status:** NEXT

**Goal:** Expose Guardian's already-proven UCII delegated-authority revocation capability as a narrow human/operator control in the demo interface before Objective 9 hardening begins.

Guardian is already able to operate autonomously inside active delegated authority, escalate when authority is insufficient, accept an exact one-time human approval, and fail closed after real UCII revocation. Objective 8F turns the revocation step from a behind-the-scenes operator action into an explicit product control without weakening the existing authority boundary.

## Product behavior

When the currently displayed delegated action authority is `ACTIVE`, the Guardian interface may present a **Revoke Authority** control to the human/operator.

The control must:

- act only on the exact delegated authority currently identified by the trusted Guardian runtime;
- invoke the legitimate UCII delegated-authority revocation lifecycle through an authenticated/authorized public boundary;
- permanently transition that authority from `ACTIVE` to `REVOKED`;
- preserve revocation timestamp and reason as historical evidence;
- refresh the interface so the authority state is visibly `REVOKED`;
- preserve or record provenance showing that human revocation occurred;
- cause every later equivalent action relying on that revoked authority to fail closed with `DENY` and no execution.

The control must **not**:

- allow Guardian or the LLM to grant, broaden, reactivate, or replace its own authority;
- provide an Undo, Reactivate, or Unrevoke path;
- mutate Guardian's UCII identity credential;
- create controller authority, payment authority, approval authority, or execution authority;
- use a private UCII implementation import, direct database mutation, or hidden backend shortcut from Guardian merely to make the button work;
- treat identity verification as authorization;
- reuse a stale `ALLOW` decision after revocation.

## Public-boundary requirement

Before implementation, inspect the existing UCII API/SDK surface for a legitimate authorized delegated-authority revocation operation.

If that public operation already exists, Guardian must use it.

If it does not yet exist, add only the smallest legitimate UCII public API/SDK revocation boundary needed for a human/operator to revoke an existing delegated action authority. The server-side lifecycle service remains authoritative. Guardian must not bypass the UCII boundary.

The LLM remains above the authority boundary: it may interpret and propose an action, but it cannot invoke revocation as a self-authorizing mechanism or decide that authority should be restored.

## Demo lifecycle

The final proof should make the control relationship visible in one coherent product flow:

1. A fresh delegated routine authority is `ACTIVE`.
2. Guardian receives an in-scope routine request and autonomously executes it: `ALLOW -> ACTIVE -> Completed`.
3. The human/operator selects **Revoke Authority**.
4. UCII permanently records that exact authority as `REVOKED`.
5. Guardian displays the revoked state.
6. The same class of routine request is submitted again.
7. Guardian performs fresh identity verification and a fresh UCII authority check.
8. UCII returns `REVOKED`; Guardian returns `DENY`; execution does not occur.
9. Provenance makes the lifecycle understandable without reading source code.

## Authority records for testing

Historical delegated Authority A `bea80670-e7ea-4176-a491-e3c0130d00cf` is permanently `REVOKED` and must never be restored.

Historical delegated Authority B `51417346-4bc9-419e-8785-92309360cf94` is permanently `REVOKED` and must never be restored.

If Objective 8F requires a live active authority for its final proof, create a **fresh Authority C** through the legitimate human-owner grant path. Do not mutate either historical revoked authority.

Guardian identity Credential B remains independent from delegated action authority and is not part of this revocation control.

## Implementation sequence

Follow the normal Guardian engineering discipline:

**inspect -> reason -> bounded change -> targeted verify -> diff/review -> commit -> checkpoint**

### 8F-A — Read-only boundary inspection

- Inspect Guardian's current browser/runtime authority state handling.
- Inspect UCII's existing public API/SDK delegated-authority lifecycle surface.
- Determine the smallest legitimate revocation path.
- Make no mutation during this step.

### 8F-B — Revocation adapter/public boundary

- Implement only the missing revocation boundary required by 8F-A.
- Preserve server-side UCII lifecycle authority.
- Fail closed on malformed, unauthorized, missing, non-active, or already-revoked authority.

### 8F-C — Browser control

- Add **Revoke Authority** only when revocation is meaningful and permitted.
- Require explicit human/operator action.
- Bind the request to the exact authority ID supplied by trusted runtime state, not arbitrary browser input.
- Render the resulting authoritative state clearly.

### 8F-D — Live proof

Using fresh Authority C if required, prove:

`ACTIVE -> ALLOW -> EXECUTE -> HUMAN REVOKE -> REVOKED -> DENY -> NO EXECUTION`

Verify that the post-revocation request performs a fresh UCII authority check and that no execution receipt is created after revocation.

### 8F-E — Closure

- Run targeted and full Guardian regression.
- Record verified implementation evidence.
- Update the roadmap only after proof.
- Commit and synchronize the closure separately.

## Acceptance

- [ ] A human/operator can revoke the exact active delegated authority from the Guardian interface.
- [ ] Revocation uses the legitimate UCII authority lifecycle and public boundary; Guardian does not perform a private implementation bypass.
- [ ] The LLM cannot invoke the control to grant, broaden, restore, or substitute authority.
- [ ] Revocation is permanent for that authority record and no Undo/Reactivate control exists.
- [ ] The interface visibly transitions the authority to `REVOKED` after authoritative confirmation.
- [ ] A fresh equivalent request after revocation returns `DENY` and performs no execution.
- [ ] No stale or cached `ALLOW` can survive revocation.
- [ ] Provenance makes the human revocation and post-revocation refusal visible.
- [ ] Historical Authorities A and B remain revoked; any new live proof uses fresh Authority C rather than reactivation.
- [ ] Targeted and full regression pass before Objective 8F is closed.

## Relationship to Objective 9

Objective 9 hackathon hardening begins **after Objective 8F is implemented and proven**. This avoids hardening a demo interface that is still missing Guardian's most important human control: the ability to withdraw an autonomous agent's delegated authority to act.
