"""Tests for Guardian delegated-authority lifecycle mutation."""

from __future__ import annotations

from pathlib import Path

import pytest

import ucii_guardian.authority_lifecycle as lifecycle
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)
from ucii_guardian.authority_lifecycle import (
    GuardianAuthorityLifecycleError,
    revoke_active_authority,
)
from ucii_guardian.identity import GuardianIdentityConfig


IDENTITY_ID = (
    "35c1db3d-61d7-4d0d-a5d7-db3ab7f79520"
)
CREDENTIAL_ID = (
    "9e2ee693-ca6d-426a-80ae-cf226e69c1e6"
)
FINGERPRINT = (
    "9d14f6f5a53629709afb1574ef9d14be"
    "ad52d6da5ecb1334cfaf930abd321559"
)
AUTHORITY_ID = "guardian-authority-c"
OPERATION = "guardian.purchase.office_supply"
REASON = "Human operator revoked delegated routine authority."
CONTROLLER = "test-controller-authority-secret"


class FakeAuthorization:
    response = None
    calls = []

    def revoke_delegated(self, **kwargs):
        type(self).calls.append(dict(kwargs))

        if isinstance(type(self).response, Exception):
            raise type(self).response

        return type(self).response


class FakeClient:
    instances = []

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.authorization = FakeAuthorization()
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False


@pytest.fixture(autouse=True)
def reset_fakes():
    FakeAuthorization.calls = []
    FakeAuthorization.response = None
    FakeClient.instances = []


@pytest.fixture
def config(tmp_path: Path) -> GuardianIdentityConfig:
    return GuardianIdentityConfig(
        base_url="https://api.ucii.sportgen-ai.com",
        identity_id=IDENTITY_ID,
        credential_id=CREDENTIAL_ID,
        credential_fingerprint=FINGERPRINT,
        custody_path=(
            tmp_path
            / "guardian-mldsa65-v2.json"
        ),
    )


@pytest.fixture
def active_authority() -> AuthorityDecisionResult:
    return AuthorityDecisionResult(
        decision=AuthorityDecision.ALLOW,
        authority_state="ACTIVE",
        authority_id=AUTHORITY_ID,
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        operation=OPERATION,
        request_id="request-authority-revoke",
    )


def response_for(**overrides):
    response = {
        "authority_id": AUTHORITY_ID,
        "identity_id": IDENTITY_ID,
        "authority_state": "REVOKED",
        "allowed_operations": [OPERATION],
        "granted_by": "guardian-human-owner",
        "revoked_at": "2026-09-11T17:30:00+00:00",
        "revocation_reason": REASON,
    }
    response.update(overrides)
    return response


def install_fake_client(monkeypatch, response):
    FakeAuthorization.response = response

    monkeypatch.setattr(
        lifecycle,
        "UCIIClient",
        FakeClient,
    )


def test_revoke_active_authority_uses_exact_public_sdk_boundary(
    monkeypatch,
    config,
    active_authority,
) -> None:
    install_fake_client(
        monkeypatch,
        response_for(),
    )

    result = revoke_active_authority(
        authority=active_authority,
        config=config,
        controller_authority=CONTROLLER,
        reason=REASON,
    )

    assert len(FakeClient.instances) == 1
    assert FakeClient.instances[0].base_url == config.base_url
    assert FakeClient.instances[0].timeout == 30.0

    assert FakeAuthorization.calls == [
        {
            "authority_id": AUTHORITY_ID,
            "reason": REASON,
            "controller_authority": CONTROLLER,
        }
    ]

    assert result.authority_id == AUTHORITY_ID
    assert result.identity_id == IDENTITY_ID
    assert result.authority_state == "REVOKED"
    assert result.allowed_operations == (OPERATION,)
    assert result.granted_by == "guardian-human-owner"
    assert result.revoked_at == "2026-09-11T17:30:00+00:00"
    assert result.revocation_reason == REASON


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("decision", AuthorityDecision.DENY),
        ("authority_state", "REVOKED"),
        ("authority_id", None),
        ("authority_id", ""),
        ("authority_id", "   "),
        ("identity_id", "different-identity"),
    ],
)
def test_untrusted_or_non_active_authority_fails_before_transport(
    monkeypatch,
    config,
    active_authority,
    field,
    value,
) -> None:
    install_fake_client(
        monkeypatch,
        response_for(),
    )

    values = {
        "decision": active_authority.decision,
        "authority_state": active_authority.authority_state,
        "authority_id": active_authority.authority_id,
        "identity_id": active_authority.identity_id,
        "credential_fingerprint": (
            active_authority.credential_fingerprint
        ),
        "operation": active_authority.operation,
        "request_id": active_authority.request_id,
    }
    values[field] = value

    candidate = AuthorityDecisionResult(
        **values
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        revoke_active_authority(
            authority=candidate,
            config=config,
            controller_authority=CONTROLLER,
            reason=REASON,
        )

    assert FakeAuthorization.calls == []


@pytest.mark.parametrize(
    "controller_authority",
    [
        "",
        "   ",
        None,
    ],
)
def test_missing_controller_authority_fails_before_transport(
    monkeypatch,
    config,
    active_authority,
    controller_authority,
) -> None:
    install_fake_client(
        monkeypatch,
        response_for(),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            controller_authority=controller_authority,
            reason=REASON,
        )

    assert FakeAuthorization.calls == []


@pytest.mark.parametrize(
    "reason",
    [
        "",
        "   ",
        None,
    ],
)
def test_missing_revocation_reason_fails_before_transport(
    monkeypatch,
    config,
    active_authority,
    reason,
) -> None:
    install_fake_client(
        monkeypatch,
        response_for(),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            controller_authority=CONTROLLER,
            reason=reason,
        )

    assert FakeAuthorization.calls == []


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        {},
        response_for(
            authority_id="different-authority",
        ),
        response_for(
            identity_id="different-identity",
        ),
        response_for(
            authority_state="ACTIVE",
        ),
        response_for(
            allowed_operations=[],
        ),
        response_for(
            allowed_operations=["different.operation"],
        ),
        response_for(
            granted_by="",
        ),
        response_for(
            revoked_at="",
        ),
        response_for(
            revocation_reason="different reason",
        ),
    ],
)
def test_malformed_or_mismatched_ucii_response_fails_closed(
    monkeypatch,
    config,
    active_authority,
    response,
) -> None:
    install_fake_client(
        monkeypatch,
        response,
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            controller_authority=CONTROLLER,
            reason=REASON,
        )


def test_transport_failure_fails_closed(
    monkeypatch,
    config,
    active_authority,
) -> None:
    install_fake_client(
        monkeypatch,
        RuntimeError("network failure"),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError,
        match="failed closed",
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            controller_authority=CONTROLLER,
            reason=REASON,
        )


def test_result_does_not_retain_controller_authority(
    monkeypatch,
    config,
    active_authority,
) -> None:
    install_fake_client(
        monkeypatch,
        response_for(),
    )

    result = revoke_active_authority(
        authority=active_authority,
        config=config,
        controller_authority=CONTROLLER,
        reason=REASON,
    )

    assert "controller_authority" not in result.__dataclass_fields__
    assert CONTROLLER not in repr(result)
