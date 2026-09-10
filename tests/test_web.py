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

    assert 'class="approve" type="button" disabled' in page
    assert 'class="deny" type="button" disabled' in page


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
    assert 'class="approve" type="button" >Approve Once' in response.text
    assert 'class="deny" type="button" >Deny' in response.text


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
