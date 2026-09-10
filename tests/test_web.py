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
