"""Minimal Guardian browser interface.

This layer presents Guardian state only.
It does not create authority, approve actions, or execute consequential work.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from ucii_guardian.agent import build_guardian_agent
from ucii_guardian.authority import AuthorityDecision
from ucii_guardian.authority_lifecycle import (
    AuthorityRevocationResult,
    GuardianAuthorityLifecycleError,
    revoke_active_authority,
)
from ucii_guardian.identity import GuardianIdentityConfig
from ucii_guardian.provenance_recorder import GuardianProvenanceRecorder
from ucii_guardian.approval import HumanDecision
from ucii_guardian.workflow import (
    GuardianWorkflowOutcome,
    continue_guardian_escalation,
    run_guardian_request,
)


@dataclass(frozen=True)
class PendingEscalationContext:
    """Exact browser continuation state for one pending escalation."""

    outcome: GuardianWorkflowOutcome
    request_value: str
    recorder: GuardianProvenanceRecorder
    receipt_directory: Path


@dataclass(frozen=True)
class ActiveAuthorityContext:
    """Trusted server-held ACTIVE authority available for revocation."""

    outcome: GuardianWorkflowOutcome
    request_value: str
    config: GuardianIdentityConfig


_pending_context: PendingEscalationContext | None = None
_active_authority_context: ActiveAuthorityContext | None = None


def _set_pending_context(
    context: PendingEscalationContext | None,
) -> None:
    global _pending_context
    _pending_context = context


def _take_pending_context() -> PendingEscalationContext | None:
    global _pending_context
    context = _pending_context
    _pending_context = None
    return context


def _set_active_authority_context(
    context: ActiveAuthorityContext | None,
) -> None:
    global _active_authority_context
    _active_authority_context = context


def _get_active_authority_context() -> ActiveAuthorityContext | None:
    return _active_authority_context


def _render_outcome(outcome: GuardianWorkflowOutcome | None) -> dict[str, str]:
    if outcome is None:
        return {
            "decision": "Awaiting request",
            "authority": "Not evaluated",
            "execution": "No action",
            "reason": "Submit a request to evaluate current authority.",
            "timeline": (
                "<li><strong>Waiting for a request</strong>"
                "<span class=\"muted\">Guardian will show identity verification, "
                "authority evaluation, human decisions, execution, refusal, and "
                "revocation evidence here.</span></li>"
            ),
            "approve_disabled": "disabled",
            "deny_disabled": "disabled",
            "revoke_disabled": "disabled",
        }

    decision = escape(outcome.authority.decision.value)
    authority = escape(outcome.authority.authority_state)

    pending_escalation = (
        outcome.escalation is not None
        and outcome.human_decision is None
        and outcome.execution is None
    )

    if outcome.human_decision is not None:
        decision = escape(outcome.human_decision.decision.value)

    if outcome.execution is not None:
        execution = "Completed"
    elif pending_escalation:
        execution = "Awaiting human decision"
    else:
        execution = "No execution"

    if pending_escalation:
        reason = (
            "Current UCII authority does not cover this action. "
            "Human judgment is required."
        )
        approve_disabled = ""
        deny_disabled = ""
    elif outcome.human_decision is not None:
        if outcome.execution is not None:
            reason = (
                "Human approved this exact action once. "
                "Guardian completed only that approved action."
            )
        else:
            reason = (
                "Human denied this exact action. "
                "Guardian did not execute it."
            )
        approve_disabled = "disabled"
        deny_disabled = "disabled"
    elif outcome.authority.decision.value == "DENY":
        reason = (
            "Current UCII authority is not usable. "
            "Guardian will not execute this action."
        )
        approve_disabled = "disabled"
        deny_disabled = "disabled"
    else:
        reason = "Current delegated authority permits this action."
        approve_disabled = "disabled"
        deny_disabled = "disabled"

    timeline_items = []
    for event in outcome.provenance:
        timeline_items.append(
            "<li>"
            f"<strong>{escape(event.event_type.value)}</strong>"
            f"<span class=\"muted\">{escape(event.reason)}</span>"
            "</li>"
        )

    revoke_disabled = "disabled"

    if (
        outcome.authority.decision is AuthorityDecision.ALLOW
        and outcome.authority.authority_state == "ACTIVE"
        and outcome.authority.authority_id
    ):
        revoke_disabled = ""

    return {
        "decision": decision,
        "authority": authority,
        "execution": execution,
        "reason": reason,
        "timeline": "".join(timeline_items),
        "approve_disabled": approve_disabled,
        "deny_disabled": deny_disabled,
        "revoke_disabled": revoke_disabled,
    }


def render_guardian_page(
    *,
    outcome: GuardianWorkflowOutcome | None = None,
    request_value: str = "",
    revocation: AuthorityRevocationResult | None = None,
    lifecycle_message: str | None = None,
) -> str:
    state = _render_outcome(outcome)

    if revocation is not None:
        state["authority"] = "REVOKED"
        state["revoke_disabled"] = "disabled"
        state["reason"] = (
            "Authority revoked. This delegated authority grant is no longer "
            "valid. Guardian's UCII identity remains verified. Future "
            "protected actions must perform a fresh authority check and will "
            "be denied unless a new authority grant is issued."
        )
        state["timeline"] += (
            "<li><strong>AUTHORITY_REVOKED</strong>"
            "<span class=\"muted\">UCII authoritatively confirmed the "
            "exact delegated authority as REVOKED.</span></li>"
        )

    if lifecycle_message is not None:
        state["reason"] = lifecycle_message

    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UCII Guardian</title>
<style>
:root {
    color-scheme: dark;
    font-family: Inter, system-ui, sans-serif;
}
body {
    margin: 0;
    background: #0b1020;
    color: #eef3ff;
}
main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 48px 24px 72px;
}
header {
    margin-bottom: 32px;
}
.eyebrow {
    text-transform: uppercase;
    letter-spacing: .14em;
    font-size: 12px;
    color: #8ea5ff;
    font-weight: 700;
}
h1 {
    margin: 8px 0 10px;
    font-size: clamp(38px, 6vw, 68px);
    line-height: 1;
}
.subtitle {
    max-width: 780px;
    color: #b9c4df;
    font-size: 18px;
    line-height: 1.55;
}
.grid {
    display: grid;
    grid-template-columns: 1.25fr .75fr;
    gap: 20px;
}
.card {
    background: #121a30;
    border: 1px solid #26314f;
    border-radius: 18px;
    padding: 22px;
}
label, .label {
    display: block;
    color: #9eaccb;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 10px;
}
textarea {
    width: 100%;
    box-sizing: border-box;
    min-height: 125px;
    resize: vertical;
    border: 1px solid #34415f;
    border-radius: 12px;
    padding: 14px;
    background: #0d1427;
    color: #fff;
    font: inherit;
}
button {
    border: 0;
    border-radius: 10px;
    padding: 11px 17px;
    font-weight: 700;
    cursor: pointer;
}
.primary {
    background: #6f8cff;
    color: #081022;
}
.approve {
    background: #2dba7c;
    color: #071c13;
}
.deny {
    background: #df5f6b;
    color: #25080b;
}
.revoke {
    background: #f0a45d;
    color: #271305;
}
.actions {
    display: flex;
    gap: 10px;
    margin-top: 14px;
}
.status {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 20px;
}
.status-box {
    background: #0d1427;
    border: 1px solid #26314f;
    border-radius: 12px;
    padding: 14px;
}
.value {
    font-size: 17px;
    font-weight: 800;
}
.muted {
    color: #7f8ba7;
}
.timeline {
    margin: 0;
    padding: 0;
    list-style: none;
}
.timeline li {
    border-left: 2px solid #34415f;
    padding: 0 0 20px 18px;
    margin-left: 5px;
}
.timeline strong {
    display: block;
    margin-bottom: 4px;
}
.footer-note {
    margin-top: 32px;
    color: #7784a1;
    font-size: 13px;
}
@media (max-width: 800px) {
    .grid {
        grid-template-columns: 1fr;
    }
    .status {
        grid-template-columns: 1fr;
    }
}
</style>
</head>
<body>
<main>
<header>
<div class="eyebrow">Bounded Autonomous Authority</div>
<h1>UCII Guardian</h1>
<div class="subtitle">
AI agents should be autonomous without having unlimited authority.
Guardian lets routine authorized work proceed quietly and escalates only
when the requested action exceeds the authority a human actually granted.
</div>
</header>

<div class="grid">
<section class="card">
<form method="post" action="/evaluate">
<label for="request">Human request</label>
<textarea id="request" name="request"
placeholder="Example: Purchase one printer cartridge under $80.">{request_value}</textarea>

<div class="actions">
<button class="primary" type="submit">Evaluate request</button>
</div>
</form>

<div class="status">
<div class="status-box">
<div class="label">Guardian Decision</div>
<div class="value">{decision}</div>
</div>
<div class="status-box">
<div class="label">Authority</div>
<div class="value">{authority}</div>
</div>
<div class="status-box">
<div class="label">Execution</div>
<div class="value">{execution}</div>
</div>
</div>
</section>

<aside class="card">
<div class="label">Human judgment</div>
<p class="muted">{reason}</p>
<form method="post" action="/decision">
<div class="actions">
<button class="approve" type="submit" name="decision" value="APPROVE_ONCE" {approve_disabled}>Approve Once</button>
<button class="deny" type="submit" name="decision" value="DENY" {deny_disabled}>Deny</button>
</div>
</form>

<form method="post" action="/revoke">
<div class="actions">
<button class="revoke" type="submit" {revoke_disabled}>Revoke Authority</button>
</div>
</form>
</aside>
</div>

<section class="card" style="margin-top:20px">
<div class="label">Activity &amp; provenance</div>
<ul class="timeline">
{timeline}
</ul>
</section>

<div class="footer-note">
Capability is not authority. Identity verification does not itself grant
permission to execute a consequential action.
</div>
</main>
</body>
</html>"""

    replacements = {
        "{request_value}": escape(request_value),
        "{decision}": state["decision"],
        "{authority}": state["authority"],
        "{execution}": state["execution"],
        "{reason}": escape(state["reason"]),
        "{timeline}": state["timeline"],
        "{approve_disabled}": state["approve_disabled"],
        "{deny_disabled}": state["deny_disabled"],
        "{revoke_disabled}": state["revoke_disabled"],
    }

    for placeholder, value in replacements.items():
        page = page.replace(placeholder, value)

    return page


def build_runtime() -> tuple[
    object,
    GuardianIdentityConfig,
    GuardianProvenanceRecorder,
    Path,
]:
    root = Path.home() / "AppData" / "Local" / "UCII" / "Guardian"

    config = GuardianIdentityConfig(
        base_url="https://api.ucii.sportgen-ai.com",
        identity_id="35c1db3d-61d7-4d0d-a5d7-db3ab7f79520",
        credential_id="9e2ee693-ca6d-426a-80ae-cf226e69c1e6",
        credential_fingerprint=(
            "9d14f6f5a53629709afb1574ef9d14bead52d6da5ecb1334cfaf930abd321559"
        ),
        custody_path=(
            root / "custody" / "guardian-mldsa65-v2.json"
        ),
    )

    recorder = GuardianProvenanceRecorder(
        root / "provenance" / "guardian-web.jsonl"
    )

    agent = build_guardian_agent(
        guardian_identity=config.identity_id
    )

    return (
        agent,
        config,
        recorder,
        root / "executions",
    )


async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse(render_guardian_page())


async def evaluate(request: Request) -> HTMLResponse:
    form = await request.form()
    human_request = str(form.get("request", "")).strip()

    if not human_request:
        return HTMLResponse(
            render_guardian_page(),
            status_code=400,
        )

    agent, config, recorder, receipts = build_runtime()

    outcome = run_guardian_request(
        agent=agent,
        request=human_request,
        config=config,
        recorder=recorder,
        receipt_directory=receipts,
    )

    if (
        outcome.escalation is not None
        and outcome.human_decision is None
        and outcome.execution is None
    ):
        _set_pending_context(
            PendingEscalationContext(
                outcome=outcome,
                request_value=human_request,
                recorder=recorder,
                receipt_directory=receipts,
            )
        )
    else:
        _set_pending_context(None)

    if (
        outcome.authority.decision is AuthorityDecision.ALLOW
        and outcome.authority.authority_state == "ACTIVE"
        and outcome.authority.authority_id
    ):
        _set_active_authority_context(
            ActiveAuthorityContext(
                outcome=outcome,
                request_value=human_request,
                config=config,
            )
        )
    else:
        _set_active_authority_context(None)

    return HTMLResponse(
        render_guardian_page(
            outcome=outcome,
            request_value=human_request,
        )
    )


async def revoke(request: Request) -> HTMLResponse:
    context = _get_active_authority_context()

    if context is None:
        return HTMLResponse(
            render_guardian_page(),
            status_code=409,
        )

    try:
        result = revoke_active_authority(
            authority=context.outcome.authority,
            config=context.config,
            reason="human_revoked_guardian_web_authority",
        )
    except GuardianAuthorityLifecycleError:
        return HTMLResponse(
            render_guardian_page(
                outcome=context.outcome,
                request_value=context.request_value,
                lifecycle_message=(
                    "Revocation failed closed. The delegated authority "
                    "remains ACTIVE."
                ),
            ),
            status_code=409,
        )

    _set_active_authority_context(None)
    _set_pending_context(None)

    return HTMLResponse(
        render_guardian_page(
            outcome=context.outcome,
            request_value=context.request_value,
            revocation=result,
        )
    )


async def decide(request: Request) -> HTMLResponse:
    form = await request.form()
    raw_decision = str(form.get("decision", "")).strip()

    try:
        decision = HumanDecision(raw_decision)
    except ValueError:
        return HTMLResponse(
            render_guardian_page(),
            status_code=400,
        )

    pending = _take_pending_context()

    if pending is None:
        return HTMLResponse(
            render_guardian_page(),
            status_code=409,
        )

    outcome = continue_guardian_escalation(
        outcome=pending.outcome,
        decision=decision,
        recorder=pending.recorder,
        receipt_directory=pending.receipt_directory,
    )

    return HTMLResponse(
        render_guardian_page(
            outcome=outcome,
            request_value=pending.request_value,
        )
    )


app = Starlette(
    debug=False,
    routes=[
        Route("/", homepage, methods=["GET"]),
        Route("/evaluate", evaluate, methods=["POST"]),
        Route("/revoke", revoke, methods=["POST"]),
        Route("/decision", decide, methods=["POST"]),
    ],
)
