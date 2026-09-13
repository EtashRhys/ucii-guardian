"""Tests for Guardian delegated-authority lifecycle mutation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import ucii_guardian.authority_lifecycle as lifecycle
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)
from ucii_guardian.authority_lifecycle import (
    GuardianAuthorityLifecycleError,
    grant_standing_authority,
    revoke_active_authority,
)
from ucii_guardian.identity import GuardianIdentityConfig


IDENTITY_ID = "35c1db3d-61d7-4d0d-a5d7-db3ab7f79520"
CREDENTIAL_ID = "9e2ee693-ca6d-426a-80ae-cf226e69c1e6"
FINGERPRINT = (
    "9d14f6f5a53629709afb1574ef9d14be"
    "ad52d6da5ecb1334cfaf930abd321559"
)
AUTHORITY_ID = "guardian-authority-c"
OPERATION = "guardian.purchase.office_supply"
REASON = "human_revoked_guardian_web_authority"

ENTITLEMENT_PROOF = object()


class FakeAuthorization:
    response = None
    calls = []

    def grant_delegated(self, **kwargs):
        type(self).calls.append(dict(kwargs))

        if isinstance(type(self).response, Exception):
            raise type(self).response

        return type(self).response

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
            tmp_path / "guardian-mldsa65-v2.json"
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
        request_id="guardian-revoke-test-request",
    )


def response_for(**overrides):
    response = {
        "authority_id": AUTHORITY_ID,
        "identity_id": IDENTITY_ID,
        "authority_state": "REVOKED",
        "allowed_operations": [OPERATION],
        "granted_by": "guardian-human-owner",
        "revoked_at": "2026-09-11T20:00:00+00:00",
        "revocation_reason": REASON,
    }

    response.update(overrides)

    return response


def install_fakes(
    monkeypatch,
    response,
):
    FakeAuthorization.response = response

    monkeypatch.setattr(
        lifecycle,
        "UCIIClient",
        FakeClient,
    )

    signer = SimpleNamespace(
        fingerprint=FINGERPRINT,
    )

    monkeypatch.setattr(
        lifecycle,
        "load_guardian_signing_provider",
        lambda path: signer,
    )

    monkeypatch.setattr(
        lifecycle,
        "generate_entitlement_nonce",
        lambda: "synthetic-entitlement-nonce",
    )

    proof_calls = []

    def fake_create_entitlement_proof(
        challenge,
        *,
        signing_provider,
    ):
        proof_calls.append(
            {
                "challenge": challenge,
                "signer": signing_provider,
            }
        )

        return ENTITLEMENT_PROOF

    monkeypatch.setattr(
        lifecycle,
        "create_entitlement_proof",
        fake_create_entitlement_proof,
    )

    return proof_calls


def test_revoke_uses_exact_public_sdk_entitlement_boundary(
    monkeypatch,
    config,
    active_authority,
) -> None:
    proof_calls = install_fakes(
        monkeypatch,
        response_for(),
    )

    result = revoke_active_authority(
        authority=active_authority,
        config=config,
        reason=REASON,
    )

    assert len(FakeClient.instances) == 1

    assert FakeClient.instances[0].base_url == (
        config.base_url
    )

    assert FakeAuthorization.calls == [
        {
            "authority_id": AUTHORITY_ID,
            "reason": REASON,
            "service_entitlement_proof": ENTITLEMENT_PROOF,
        }
    ]

    assert (
        "controller_authority"
        not in FakeAuthorization.calls[0]
    )

    assert len(proof_calls) == 1

    challenge = proof_calls[0]["challenge"]

    assert challenge.subject_identity_id == IDENTITY_ID
    assert challenge.credential_fingerprint == FINGERPRINT
    assert challenge.method == "POST"
    assert challenge.path == (
        "/v1/authorization/delegated/"
        f"{AUTHORITY_ID}/revoke"
    )

    assert result.authority_id == AUTHORITY_ID
    assert result.identity_id == IDENTITY_ID
    assert result.authority_state == "REVOKED"
    assert result.allowed_operations == (OPERATION,)
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
    install_fakes(
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
def test_missing_reason_fails_before_transport(
    monkeypatch,
    config,
    active_authority,
    reason,
) -> None:
    install_fakes(
        monkeypatch,
        response_for(),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            reason=reason,
        )

    assert FakeAuthorization.calls == []


def test_guardian_custody_fingerprint_mismatch_fails_closed(
    monkeypatch,
    config,
    active_authority,
) -> None:
    install_fakes(
        monkeypatch,
        response_for(),
    )

    monkeypatch.setattr(
        lifecycle,
        "load_guardian_signing_provider",
        lambda path: SimpleNamespace(
            fingerprint="different-fingerprint",
        ),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError,
        match="fingerprint",
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            reason=REASON,
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
            revocation_reason="different-reason",
        ),
    ],
)
def test_invalid_ucii_revocation_response_fails_closed(
    monkeypatch,
    config,
    active_authority,
    response,
) -> None:
    install_fakes(
        monkeypatch,
        response,
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            reason=REASON,
        )


def test_transport_failure_fails_closed(
    monkeypatch,
    config,
    active_authority,
) -> None:
    install_fakes(
        monkeypatch,
        RuntimeError("synthetic transport failure"),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError,
        match="failed closed",
    ):
        revoke_active_authority(
            authority=active_authority,
            config=config,
            reason=REASON,
        )


def grant_response_for(**overrides):
    response = {
        "authority_id": "guardian-authority-new",
        "identity_id": IDENTITY_ID,
        "authority_state": "ACTIVE",
        "allowed_operations": [OPERATION],
        "granted_by": "guardian-human-owner",
        "granted_at": "2026-09-13T19:00:00+00:00",
    }

    response.update(overrides)

    return response


def test_grant_uses_exact_public_sdk_entitlement_boundary(
    monkeypatch,
    config,
) -> None:
    proof_calls = install_fakes(
        monkeypatch,
        grant_response_for(),
    )

    result = grant_standing_authority(
        config=config,
        operation=OPERATION,
        granted_by="guardian-human-owner",
    )

    assert FakeAuthorization.calls == [
        {
            "identity_id": IDENTITY_ID,
            "allowed_operations": [OPERATION],
            "granted_by": "guardian-human-owner",
            "service_entitlement_proof": ENTITLEMENT_PROOF,
        }
    ]

    assert (
        "controller_authority"
        not in FakeAuthorization.calls[0]
    )

    assert len(proof_calls) == 1
    challenge = proof_calls[0]["challenge"]

    assert challenge.subject_identity_id == IDENTITY_ID
    assert challenge.credential_fingerprint == FINGERPRINT
    assert challenge.method == "POST"
    assert challenge.path == (
        "/v1/authorization/delegated/grant"
    )

    assert result.authority_id == "guardian-authority-new"
    assert result.identity_id == IDENTITY_ID
    assert result.authority_state == "ACTIVE"
    assert result.allowed_operations == (OPERATION,)
    assert result.granted_by == "guardian-human-owner"
    assert result.granted_at == (
        "2026-09-13T19:00:00+00:00"
    )


@pytest.mark.parametrize(
    ("operation", "granted_by"),
    [
        ("", "guardian-human-owner"),
        ("   ", "guardian-human-owner"),
        (None, "guardian-human-owner"),
        (OPERATION, ""),
        (OPERATION, "   "),
        (OPERATION, None),
    ],
)
def test_invalid_grant_input_fails_before_transport(
    monkeypatch,
    config,
    operation,
    granted_by,
) -> None:
    install_fakes(
        monkeypatch,
        grant_response_for(),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        grant_standing_authority(
            config=config,
            operation=operation,
            granted_by=granted_by,
        )

    assert FakeAuthorization.calls == []


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        {},
        grant_response_for(authority_id=""),
        grant_response_for(identity_id="different-identity"),
        grant_response_for(authority_state="REVOKED"),
        grant_response_for(allowed_operations=[]),
        grant_response_for(
            allowed_operations=["different.operation"],
        ),
        grant_response_for(
            allowed_operations=[OPERATION, "different.operation"],
        ),
        grant_response_for(granted_by="different-grantor"),
        grant_response_for(granted_at=""),
    ],
)
def test_invalid_ucii_grant_response_fails_closed(
    monkeypatch,
    config,
    response,
) -> None:
    install_fakes(
        monkeypatch,
        response,
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError
    ):
        grant_standing_authority(
            config=config,
            operation=OPERATION,
            granted_by="guardian-human-owner",
        )


def test_grant_custody_fingerprint_mismatch_fails_closed(
    monkeypatch,
    config,
) -> None:
    install_fakes(
        monkeypatch,
        grant_response_for(),
    )

    monkeypatch.setattr(
        lifecycle,
        "load_guardian_signing_provider",
        lambda path: SimpleNamespace(
            fingerprint="different-fingerprint",
        ),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError,
        match="fingerprint",
    ):
        grant_standing_authority(
            config=config,
            operation=OPERATION,
            granted_by="guardian-human-owner",
        )

    assert FakeAuthorization.calls == []


def test_grant_transport_failure_fails_closed(
    monkeypatch,
    config,
) -> None:
    install_fakes(
        monkeypatch,
        RuntimeError("synthetic grant transport failure"),
    )

    with pytest.raises(
        GuardianAuthorityLifecycleError,
        match="failed closed",
    ):
        grant_standing_authority(
            config=config,
            operation=OPERATION,
            granted_by="guardian-human-owner",
        )
