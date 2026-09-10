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

    web._set_pending_outcome(None)

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
    assert runtime_calls == ["RUNTIME"]
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

    web._set_pending_outcome(None)

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
    assert "Awaiting human decision" not in response.text


def test_decision_without_pending_escalation_fails_closed(
    monkeypatch,
) -> None:
    from ucii_guardian import web

    web._set_pending_outcome(None)

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
