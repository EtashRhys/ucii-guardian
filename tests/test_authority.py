"""Tests for Guardian delegated action-authority decisions."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path

import pytest

import ucii_guardian.authority as authority
from ucii_guardian.action import ActionRequest
from ucii_guardian.authority import (
    AuthorityDecision,
    GuardianAuthorityError,
    check_authority,
)
from ucii_guardian.identity import (
    GUARDIAN_VERIFIED,
    GuardianIdentityConfig,
    GuardianIdentityVerification,
)


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
OPERATION = "guardian.purchase.office_supply"


class FakeSigner:
    fingerprint = FINGERPRINT

    def __init__(self):
        self.messages = []

    def sign(self, message: bytes) -> bytes:
        self.messages.append(message)
        return b"guardian-authority-signature"


class FakeAuthorization:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def check_delegated(self, **kwargs):
        self.calls.append(kwargs)
        return dict(self.response)


class FakeClient:
    response = None
    instances = []

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.authorization = FakeAuthorization(
            self.response
        )
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


@pytest.fixture
def config(tmp_path):
    return GuardianIdentityConfig(
        base_url=(
            "https://api.ucii.sportgen-ai.com"
        ),
        identity_id=IDENTITY_ID,
        credential_id=CREDENTIAL_ID,
        credential_fingerprint=FINGERPRINT,
        custody_path=(
            tmp_path
            / "guardian-mldsa65-v2.json"
        ),
    )


@pytest.fixture
def identity():
    return GuardianIdentityVerification(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        status=GUARDIAN_VERIFIED,
    )


@pytest.fixture
def action():
    return ActionRequest(
        requester="human:test",
        guardian_identity=IDENTITY_ID,
        operation=OPERATION,
        target="office-supply:test-cartridge",
        parameters={
            "quantity": 1,
            "max_price_usd": 80,
        },
        request_id="request-123",
        requested_at=datetime(
            2026,
            9,
            10,
            18,
            0,
            tzinfo=timezone.utc,
        ),
    )


@pytest.fixture
def install_boundary(monkeypatch):
    signer = FakeSigner()

    monkeypatch.setattr(
        authority,
        "load_guardian_signing_provider",
        lambda path: signer,
    )

    monkeypatch.setattr(
        authority,
        "UCIIClient",
        FakeClient,
    )

    FakeClient.instances = []

    return signer


def response_for(state):
    return {
        "authorized": state == "ACTIVE",
        "executed": False,
        "identity_id": IDENTITY_ID,
        "credential_fingerprint": FINGERPRINT,
        "operation": OPERATION,
        "credential_status": "ACTIVE",
        "authority_state": state,
    }


def test_active_authority_maps_to_allow(
    config,
    identity,
    action,
    install_boundary,
):
    FakeClient.response = response_for(
        "ACTIVE"
    )

    result = check_authority(
        action,
        identity=identity,
        config=config,
    )

    assert result.decision == AuthorityDecision.ALLOW
    assert result.authority_state == "ACTIVE"
    assert result.operation == OPERATION
    assert result.request_id == "request-123"

    assert len(FakeClient.instances) == 1

    client = FakeClient.instances[0]

    assert (
        client.base_url
        == "https://api.ucii.sportgen-ai.com"
    )
    assert client.timeout == 30.0

    assert len(
        client.authorization.calls
    ) == 1

    call = client.authorization.calls[0]

    assert call["identity_id"] == IDENTITY_ID
    assert (
        call["credential_fingerprint"]
        == FINGERPRINT
    )
    assert call["operation"] == OPERATION

    assert (
        base64.b64decode(
            call["signature"]
        )
        == b"guardian-authority-signature"
    )


def test_not_granted_maps_to_escalation_required(
    config,
    identity,
    action,
    install_boundary,
):
    FakeClient.response = response_for(
        "NOT_GRANTED"
    )

    result = check_authority(
        action,
        identity=identity,
        config=config,
    )

    assert (
        result.decision
        == AuthorityDecision.ESCALATION_REQUIRED
    )


@pytest.mark.parametrize(
    "state",
    [
        "REVOKED",
        "EXPIRED",
        "INVALID",
    ],
)
def test_invalid_authority_states_map_to_deny(
    config,
    identity,
    action,
    install_boundary,
    state,
):
    FakeClient.response = response_for(
        state
    )

    result = check_authority(
        action,
        identity=identity,
        config=config,
    )

    assert result.decision == AuthorityDecision.DENY


def test_verified_identity_alone_never_returns_allow(
    config,
    identity,
    action,
    install_boundary,
):
    assert identity.status == GUARDIAN_VERIFIED

    FakeClient.response = response_for(
        "NOT_GRANTED"
    )

    result = check_authority(
        action,
        identity=identity,
        config=config,
    )

    assert (
        result.decision
        != AuthorityDecision.ALLOW
    )


def test_action_identity_must_match_verified_identity(
    config,
    identity,
    install_boundary,
):
    action = ActionRequest(
        requester="human:test",
        guardian_identity="different-identity",
        operation=OPERATION,
        target="office-supply:test",
    )

    with pytest.raises(
        GuardianAuthorityError,
        match="does not match verified identity",
    ):
        check_authority(
            action,
            identity=identity,
            config=config,
        )

    assert FakeClient.instances == []


def test_non_verified_identity_fails_closed(
    config,
    action,
    install_boundary,
):
    identity = GuardianIdentityVerification(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        status="NOT_VERIFIED",
    )

    with pytest.raises(
        GuardianAuthorityError,
        match="not UCII_VERIFIED",
    ):
        check_authority(
            action,
            identity=identity,
            config=config,
        )

    assert FakeClient.instances == []


def test_custody_fingerprint_mismatch_fails_closed(
    config,
    identity,
    action,
    monkeypatch,
):
    class WrongSigner:
        fingerprint = "0" * 64

    monkeypatch.setattr(
        authority,
        "load_guardian_signing_provider",
        lambda path: WrongSigner(),
    )

    with pytest.raises(
        GuardianAuthorityError,
        match="custody fingerprint",
    ):
        check_authority(
            action,
            identity=identity,
            config=config,
        )


def test_action_proof_binds_full_normalized_action(
    config,
    identity,
    action,
    install_boundary,
):
    FakeClient.response = response_for(
        "ACTIVE"
    )

    check_authority(
        action,
        identity=identity,
        config=config,
    )

    signed = (
        install_boundary.messages[0]
        .decode("utf-8")
    )

    assert '"guardian_identity":' in signed
    assert '"operation":' in signed
    assert '"parameters":' in signed
    assert '"request_id":' in signed
    assert '"requested_at":' in signed
    assert '"requester":' in signed
    assert '"target":' in signed
    assert OPERATION in signed
    assert "request-123" in signed


@pytest.mark.parametrize(
    "field,value",
    [
        ("authorized", False),
        ("executed", True),
        ("identity_id", "different-identity"),
        (
            "credential_fingerprint",
            "0" * 64,
        ),
        ("operation", "different.operation"),
        ("credential_status", "REVOKED"),
        ("authority_state", "UNKNOWN"),
    ],
)
def test_inconsistent_ucii_response_fails_closed(
    config,
    identity,
    action,
    install_boundary,
    field,
    value,
):
    response = response_for(
        "ACTIVE"
    )

    response[field] = value

    FakeClient.response = response

    with pytest.raises(
        GuardianAuthorityError,
    ):
        check_authority(
            action,
            identity=identity,
            config=config,
        )


def test_public_ucii_error_fails_closed(
    config,
    identity,
    action,
    install_boundary,
):
    class FailingAuthorization:
        def check_delegated(
            self,
            **kwargs,
        ):
            raise RuntimeError(
                "simulated UCII failure"
            )

    class FailingClient(FakeClient):
        def __init__(
            self,
            *,
            base_url,
            timeout,
        ):
            self.authorization = (
                FailingAuthorization()
            )

    authority.UCIIClient = FailingClient

    with pytest.raises(
        GuardianAuthorityError,
        match="failed closed",
    ):
        check_authority(
            action,
            identity=identity,
            config=config,
        )


def test_result_carries_no_execution_grant(
    config,
    identity,
    action,
    install_boundary,
):
    FakeClient.response = response_for(
        "ACTIVE"
    )

    result = check_authority(
        action,
        identity=identity,
        config=config,
    )

    assert set(
        result.__dataclass_fields__
    ) == {
        "decision",
        "authority_state",
        "identity_id",
        "credential_fingerprint",
        "operation",
        "request_id",
    }

    assert not hasattr(
        result,
        "executed",
    )

    assert not hasattr(
        result,
        "execution_authority",
    )


def test_authority_module_has_no_private_ucii_server_imports():
    source = Path(
        authority.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "pq_auth" not in source
    assert "src.pq_auth" not in source
