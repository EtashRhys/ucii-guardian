from starlette.testclient import TestClient

from ucii_guardian.web import app, render_guardian_page


def test_guardian_page_contains_required_demo_surfaces() -> None:
    page = render_guardian_page()

    required = (
        "UCII Guardian",
        "Human request",
        "Guardian Decision",
        "Authority",
        "Execution",
        "Grant Standing Authority",
        "Approve Once",
        "Deny",
        "Activity &amp; provenance",
        "Capability is not authority",
    )

    for marker in required:
        assert marker in page


def test_guardian_homepage_renders_successfully() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "UCII Guardian" in response.text


def test_initial_approval_controls_are_disabled() -> None:
    page = render_guardian_page()

    assert 'class="approve" type="submit" name="decision" value="APPROVE_ONCE" disabled' in page
    assert 'class="deny" type="submit" name="decision" value="DENY" disabled' in page


def test_evaluate_route_renders_workflow_result(monkeypatch, tmp_path) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision
    from ucii_guardian.provenance import ProvenanceEventType

    fake_outcome = SimpleNamespace(
        authority=SimpleNamespace(
            decision=AuthorityDecision.DENY,
            authority_state="REVOKED",
        ),
        execution=None,
        escalation=None,
        human_decision=None,
        provenance=(
            SimpleNamespace(
                event_type=ProvenanceEventType.REQUEST_RECEIVED,
                reason="Guardian received the request.",
            ),
            SimpleNamespace(
                event_type=ProvenanceEventType.AUTHORITY_REVOKED,
                reason="UCII reported revoked authority.",
            ),
            SimpleNamespace(
                event_type=ProvenanceEventType.EXECUTION_REFUSED,
                reason="Guardian refused execution.",
            ),
        ),
    )

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (
            object(),
            object(),
            object(),
            tmp_path,
        ),
    )

    monkeypatch.setattr(
        web,
        "run_guardian_request",
        lambda **kwargs: fake_outcome,
    )

    client = TestClient(web.app)

    response = client.post(
        "/evaluate",
        data={"request": "Purchase one printer cartridge under $80."},
    )

    assert response.status_code == 200
    assert "DENY" in response.text
    assert "REVOKED" in response.text
    assert "No execution" in response.text
    assert "AUTHORITY_REVOKED" in response.text
    assert "EXECUTION_REFUSED" in response.text


def test_escalation_enables_human_controls(monkeypatch, tmp_path) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision

    fake_outcome = SimpleNamespace(
        authority=SimpleNamespace(
            decision=AuthorityDecision.ESCALATION_REQUIRED,
            authority_state="NOT_GRANTED",
        ),
        execution=None,
        escalation=object(),
        human_decision=None,
        provenance=(),
    )

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (
            object(),
            object(),
            object(),
            tmp_path,
        ),
    )

    monkeypatch.setattr(
        web,
        "run_guardian_request",
        lambda **kwargs: fake_outcome,
    )

    client = TestClient(web.app)

    response = client.post(
        "/evaluate",
        data={"request": "Exceptional purchase request"},
    )

    assert response.status_code == 200
    assert "ESCALATION_REQUIRED" in response.text
    assert "NOT_GRANTED" in response.text
    assert 'class="approve" type="submit" name="decision" value="APPROVE_ONCE" >Approve Once' in response.text
    assert 'class="deny" type="submit" name="decision" value="DENY" >Deny' in response.text


def test_blank_evaluate_request_fails_before_runtime(monkeypatch) -> None:
    from ucii_guardian import web

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (_ for _ in ()).throw(
            AssertionError("runtime must not start for blank request")
        ),
    )

    client = TestClient(web.app)

    response = client.post(
        "/evaluate",
        data={"request": "   "},
    )

    assert response.status_code == 400



def test_human_approve_once_continues_exact_pending_web_outcome(
    monkeypatch,
    tmp_path,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision

    pending = SimpleNamespace(
        authority=SimpleNamespace(
            decision=AuthorityDecision.ESCALATION_REQUIRED,
            authority_state="NOT_GRANTED",
        ),
        escalation=object(),
        human_decision=None,
        execution=None,
        provenance=(),
    )

    completed = SimpleNamespace(
        authority=pending.authority,
        escalation=pending.escalation,
        human_decision=SimpleNamespace(
            decision=web.HumanDecision.APPROVE_ONCE,
        ),
        execution=SimpleNamespace(executed=True),
        provenance=(),
    )

    runtime_calls = []
    continuation_calls = []

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (
            runtime_calls.append("RUNTIME")
            or (object(), object(), object(), tmp_path)
        ),
    )

    monkeypatch.setattr(
        web,
        "run_guardian_request",
        lambda **kwargs: pending,
    )

    def fake_continue(**kwargs):
        continuation_calls.append(kwargs)
        return completed

    monkeypatch.setattr(
        web,
        "continue_guardian_escalation",
        fake_continue,
    )

    web._set_pending_context(None)

    client = TestClient(web.app)

    first = client.post(
        "/evaluate",
        data={"request": "Exceptional purchase request"},
    )

    assert first.status_code == 200
    assert "ESCALATION_REQUIRED" in first.text

    runtime_calls.clear()

    second = client.post(
        "/decision",
        data={"decision": "APPROVE_ONCE"},
    )

    assert second.status_code == 200
    assert "Completed" in second.text
    assert "Exceptional purchase request" in second.text
    assert runtime_calls == []
    assert len(continuation_calls) == 1
    assert continuation_calls[0]["outcome"] is pending

    replay = client.post(
        "/decision",
        data={"decision": "APPROVE_ONCE"},
    )

    assert replay.status_code == 409


def test_human_deny_continues_pending_web_outcome_without_execution(
    monkeypatch,
    tmp_path,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision

    pending = SimpleNamespace(
        authority=SimpleNamespace(
            decision=AuthorityDecision.ESCALATION_REQUIRED,
            authority_state="NOT_GRANTED",
        ),
        escalation=object(),
        human_decision=None,
        execution=None,
        provenance=(),
    )

    denied = SimpleNamespace(
        authority=pending.authority,
        escalation=pending.escalation,
        human_decision=SimpleNamespace(
            decision=web.HumanDecision.DENY,
        ),
        execution=None,
        provenance=(),
    )

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (object(), object(), object(), tmp_path),
    )

    monkeypatch.setattr(
        web,
        "run_guardian_request",
        lambda **kwargs: pending,
    )

    seen = []

    def fake_continue(**kwargs):
        seen.append(kwargs["decision"])
        return denied

    monkeypatch.setattr(
        web,
        "continue_guardian_escalation",
        fake_continue,
    )

    web._set_pending_context(None)

    client = TestClient(web.app)

    assert client.post(
        "/evaluate",
        data={"request": "Exceptional purchase request"},
    ).status_code == 200

    response = client.post(
        "/decision",
        data={"decision": "DENY"},
    )

    assert response.status_code == 200
    assert seen == [web.HumanDecision.DENY]
    assert "DENY" in response.text
    assert "No execution" in response.text
    assert "Exceptional purchase request" in response.text
    assert "Awaiting human decision" not in response.text


def test_decision_without_pending_escalation_fails_closed(
    monkeypatch,
) -> None:
    from ucii_guardian import web

    web._set_pending_context(None)

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (_ for _ in ()).throw(
            AssertionError("runtime must not build without pending escalation")
        ),
    )

    client = TestClient(web.app)

    response = client.post(
        "/decision",
        data={"decision": "APPROVE_ONCE"},
    )

    assert response.status_code == 409


def test_guardian_page_has_single_human_request_label() -> None:
    page = render_guardian_page()

    assert page.count(
        '<label for="request">Human request</label>'
    ) == 1


def test_active_authority_enables_revoke_control(
    monkeypatch,
    tmp_path,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision

    active_authority = SimpleNamespace(
        decision=AuthorityDecision.ALLOW,
        authority_state="ACTIVE",
        authority_id="trusted-authority-c",
    )

    outcome = SimpleNamespace(
        authority=active_authority,
        execution=SimpleNamespace(executed=True),
        escalation=None,
        human_decision=None,
        provenance=(),
    )

    config = SimpleNamespace(
        identity_id="guardian-id",
    )

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (
            object(),
            config,
            object(),
            tmp_path,
        ),
    )

    monkeypatch.setattr(
        web,
        "run_guardian_request",
        lambda **kwargs: outcome,
    )

    web._set_active_authority_context(None)

    client = TestClient(web.app)

    response = client.post(
        "/evaluate",
        data={
            "request": (
                "Purchase one printer cartridge under $80."
            )
        },
    )

    assert response.status_code == 200

    assert (
        'class="revoke" type="submit" >'
        "Revoke Authority</button>"
        in response.text
    )


def test_revoke_route_uses_server_held_exact_authority(
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision

    trusted_authority = SimpleNamespace(
        decision=AuthorityDecision.ALLOW,
        authority_state="ACTIVE",
        authority_id="trusted-authority-c",
    )

    outcome = SimpleNamespace(
        authority=trusted_authority,
        execution=SimpleNamespace(executed=True),
        escalation=None,
        human_decision=None,
        provenance=(),
    )

    config = SimpleNamespace(
        identity_id="guardian-id",
    )

    web._set_active_authority_context(
        web.ActiveAuthorityContext(
            outcome=outcome,
            request_value=(
                "Purchase one printer cartridge under $80."
            ),
            config=config,
        )
    )

    calls = []

    def fake_revoke_active_authority(**kwargs):
        calls.append(kwargs)

        return web.AuthorityRevocationResult(
            authority_id="trusted-authority-c",
            identity_id="guardian-id",
            authority_state="REVOKED",
            allowed_operations=(
                "guardian.purchase.office_supply",
            ),
            granted_by="guardian-human-owner",
            revoked_at="2026-09-11T20:00:00+00:00",
            revocation_reason=(
                "human_revoked_guardian_web_authority"
            ),
        )

    monkeypatch.setattr(
        web,
        "revoke_active_authority",
        fake_revoke_active_authority,
    )

    client = TestClient(web.app)

    response = client.post(
        "/revoke",
        data={
            # Browser input must not select the authority.
            "authority_id": "attacker-supplied-authority",
        },
    )

    assert response.status_code == 200
    assert len(calls) == 1

    assert calls[0]["authority"] is trusted_authority
    assert calls[0]["config"] is config

    assert calls[0]["reason"] == (
        "human_revoked_guardian_web_authority"
    )

    assert "attacker-supplied-authority" not in repr(
        calls[0]
    )

    assert "REVOKED" in response.text
    assert "AUTHORITY_REVOKED" in response.text
    assert "Authority revoked." in response.text

    assert (
        'class="revoke" type="submit" disabled>'
        "Revoke Authority</button>"
        in response.text
    )

    replay = client.post(
        "/revoke",
        data={},
    )

    assert replay.status_code == 409


def test_revoke_failure_keeps_active_authority_fail_closed(
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision

    trusted_authority = SimpleNamespace(
        decision=AuthorityDecision.ALLOW,
        authority_state="ACTIVE",
        authority_id="trusted-authority-c",
    )

    outcome = SimpleNamespace(
        authority=trusted_authority,
        execution=SimpleNamespace(executed=True),
        escalation=None,
        human_decision=None,
        provenance=(),
    )

    web._set_active_authority_context(
        web.ActiveAuthorityContext(
            outcome=outcome,
            request_value=(
                "Purchase one printer cartridge under $80."
            ),
            config=SimpleNamespace(
                identity_id="guardian-id",
            ),
        )
    )

    def fail_closed(**kwargs):
        raise web.GuardianAuthorityLifecycleError(
            "synthetic protected lifecycle unavailable"
        )

    monkeypatch.setattr(
        web,
        "revoke_active_authority",
        fail_closed,
    )

    client = TestClient(web.app)

    response = client.post(
        "/revoke",
        data={},
    )

    assert response.status_code == 409
    assert "ACTIVE" in response.text

    assert (
        "Revocation failed closed. "
        "The delegated authority remains ACTIVE."
        in response.text
    )

    assert (
        'class="revoke" type="submit" >'
        "Revoke Authority</button>"
        in response.text
    )


def test_initial_grant_control_is_enabled() -> None:
    page = render_guardian_page()

    assert (
        'class="grant" type="submit" >'
        "Grant Standing Authority</button>"
        in page
    )


def test_grant_route_uses_server_held_identity_scope_and_grantor(
    monkeypatch,
    tmp_path,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web

    config = SimpleNamespace(
        identity_id="guardian-id",
    )

    calls = []

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (
            object(),
            config,
            object(),
            tmp_path,
        ),
    )

    def fake_grant_standing_authority(**kwargs):
        calls.append(kwargs)

        return web.AuthorityGrantResult(
            authority_id="fresh-authority-e",
            identity_id="guardian-id",
            authority_state="ACTIVE",
            allowed_operations=(
                "guardian.purchase.office_supply",
            ),
            granted_by="guardian-human-owner",
            granted_at="2026-09-13T20:00:00+00:00",
        )

    monkeypatch.setattr(
        web,
        "grant_standing_authority",
        fake_grant_standing_authority,
    )

    web._set_pending_context(None)
    web._set_active_authority_context(None)

    client = TestClient(web.app)

    response = client.post(
        "/grant",
        data={
            "identity_id": "attacker-identity",
            "operation": "attacker.operation",
            "granted_by": "attacker",
            "controller_authority": "attacker-secret",
        },
    )

    assert response.status_code == 200
    assert len(calls) == 1

    assert calls[0] == {
        "config": config,
        "operation": web.GUARDIAN_STANDING_OPERATION,
        "granted_by": web.GUARDIAN_STANDING_GRANTED_BY,
    }

    assert calls[0]["operation"] == (
        "guardian.purchase.office_supply"
    )

    assert calls[0]["granted_by"] == (
        "guardian-human-owner"
    )

    assert "attacker-identity" not in repr(calls[0])
    assert "attacker.operation" not in repr(calls[0])
    assert "attacker-secret" not in repr(calls[0])

    assert "ACTIVE" in response.text
    assert "AUTHORITY_GRANTED" in response.text
    assert "Standing authority granted." in response.text

    assert (
        'class="grant" type="submit" disabled>'
        "Grant Standing Authority</button>"
        in response.text
    )

    assert (
        'class="revoke" type="submit" disabled>'
        "Revoke Authority</button>"
        in response.text
    )


def test_grant_failure_fails_closed_without_active_claim(
    monkeypatch,
    tmp_path,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (
            object(),
            SimpleNamespace(identity_id="guardian-id"),
            object(),
            tmp_path,
        ),
    )

    def fail_closed(**kwargs):
        raise web.GuardianAuthorityLifecycleError(
            "synthetic grant failure"
        )

    monkeypatch.setattr(
        web,
        "grant_standing_authority",
        fail_closed,
    )

    client = TestClient(web.app)

    response = client.post(
        "/grant",
        data={},
    )

    assert response.status_code == 409

    assert (
        "Grant failed closed. Guardian has not established "
        "a new standing authority grant."
        in response.text
    )

    assert "AUTHORITY_GRANTED" not in response.text

    assert (
        'class="grant" type="submit" >'
        "Grant Standing Authority</button>"
        in response.text
    )


def test_active_authority_disables_grant_control(
    monkeypatch,
    tmp_path,
) -> None:
    from types import SimpleNamespace

    from ucii_guardian import web
    from ucii_guardian.authority import AuthorityDecision

    active_authority = SimpleNamespace(
        decision=AuthorityDecision.ALLOW,
        authority_state="ACTIVE",
        authority_id="trusted-authority-e",
    )

    outcome = SimpleNamespace(
        authority=active_authority,
        execution=SimpleNamespace(executed=True),
        escalation=None,
        human_decision=None,
        provenance=(),
    )

    monkeypatch.setattr(
        web,
        "build_runtime",
        lambda: (
            object(),
            SimpleNamespace(identity_id="guardian-id"),
            object(),
            tmp_path,
        ),
    )

    monkeypatch.setattr(
        web,
        "run_guardian_request",
        lambda **kwargs: outcome,
    )

    client = TestClient(web.app)

    response = client.post(
        "/evaluate",
        data={
            "request": (
                "Purchase one printer cartridge under $80."
            )
        },
    )

    assert response.status_code == 200

    assert (
        'class="grant" type="submit" disabled>'
        "Grant Standing Authority</button>"
        in response.text
    )

    assert (
        'class="revoke" type="submit" >'
        "Revoke Authority</button>"
        in response.text
    )
