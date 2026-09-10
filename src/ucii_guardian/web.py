"""Minimal Guardian browser interface.

This layer presents Guardian state only.
It does not create authority, approve actions, or execute consequential work.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from ucii_guardian.agent import build_guardian_agent
from ucii_guardian.identity import GuardianIdentityConfig
from ucii_guardian.provenance_recorder import GuardianProvenanceRecorder
from ucii_guardian.workflow import GuardianWorkflowOutcome, run_guardian_request


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
        }

    decision = escape(outcome.authority.decision.value)
    authority = escape(outcome.authority.authority_state)

    if outcome.execution is not None:
        execution = "Completed"
    elif outcome.escalation is not None:
        execution = "Awaiting human decision"
    else:
        execution = "No execution"

    if outcome.escalation is not None:
        reason = (
            "Current UCII authority does not cover this action. "
            "Human judgment is required."
        )
        approve_disabled = ""
        deny_disabled = ""
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

    return {
        "decision": decision,
        "authority": authority,
        "execution": execution,
        "reason": reason,
        "timeline": "".join(timeline_items),
        "approve_disabled": approve_disabled,
        "deny_disabled": deny_disabled,
    }


def render_guardian_page(
    *,
    outcome: GuardianWorkflowOutcome | None = None,
    request_value: str = "",
) -> str:
    state = _render_outcome(outcome)

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
<label for="request">Human request</label>
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
<div class="actions">
<button class="approve" type="button" {approve_disabled}>Approve Once</button>
<button class="deny" type="button" {deny_disabled}>Deny</button>
</div>
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

    return HTMLResponse(
        render_guardian_page(
            outcome=outcome,
            request_value=human_request,
        )
    )


app = Starlette(
    debug=False,
    routes=[
        Route("/", homepage, methods=["GET"]),
        Route("/evaluate", evaluate, methods=["POST"]),
    ],
)
