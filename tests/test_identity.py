"""Tests for Guardian public UCII identity verification."""

from __future__ import annotations

from pathlib import Path

import pytest

import ucii_guardian.identity as identity
from ucii_guardian.identity import (
    GUARDIAN_VERIFIED,
    GuardianIdentityConfig,
    GuardianIdentityVerificationError,
    verify_guardian_identity,
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


class FakeSigner:
    fingerprint = FINGERPRINT

    def sign(
        self,
        message: bytes,
    ) -> bytes:
        assert isinstance(
            message,
            bytes,
        )
        return b"guardian-test-signature"


class FakeCredentials:
    pass


class FakeClient:
    credentials = FakeCredentials()

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float,
    ):
        self.base_url = base_url
        self.timeout = timeout

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
def config(
    tmp_path,
):
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


def install_success_boundary(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        identity,
        "load_guardian_signing_provider",
        lambda path: FakeSigner(),
    )

    monkeypatch.setattr(
        identity,
        "UCIIClient",
        FakeClient,
    )

    monkeypatch.setattr(
        identity,
        "create_peer_proof",
        lambda challenge, *, signing_provider: (
            captured.setdefault(
                "peer_challenge",
                challenge,
            )
            or object()
        ),
    )

    monkeypatch.setattr(
        identity,
        "create_entitlement_proof",
        lambda challenge, *, signing_provider: (
            captured.setdefault(
                "entitlement_challenge",
                challenge,
            )
            or object()
        ),
    )

    def fake_verify(
        proof,
        *,
        credentials,
        challenge_store,
        service_entitlement_proof,
    ):
        captured["verify_called"] = True
        captured["credentials"] = credentials
        captured["service_entitlement_proof"] = (
            service_entitlement_proof
        )

        return GUARDIAN_VERIFIED

    monkeypatch.setattr(
        identity,
        "verify_peer_proof",
        fake_verify,
    )

    return captured


def test_identity_verification_uses_public_ucii_boundary(
    config,
    monkeypatch,
):
    captured = install_success_boundary(
        monkeypatch
    )

    result = verify_guardian_identity(
        config
    )

    assert result.status == GUARDIAN_VERIFIED
    assert result.identity_id == IDENTITY_ID
    assert (
        result.credential_fingerprint
        == FINGERPRINT
    )

    assert (
        captured["peer_challenge"].prover_identity_id
        == IDENTITY_ID
    )
    assert (
        captured[
            "peer_challenge"
        ].credential_fingerprint
        == FINGERPRINT
    )

    entitlement = captured[
        "entitlement_challenge"
    ]

    assert (
        entitlement.subject_identity_id
        == IDENTITY_ID
    )
    assert (
        entitlement.credential_fingerprint
        == FINGERPRINT
    )
    assert entitlement.method == "POST"
    assert (
        entitlement.path
        == "/v1/credentials/verify"
    )

    assert (
        captured["verify_called"]
        is True
    )


def test_identity_verification_creates_fresh_nonces(
    config,
    monkeypatch,
):
    captured = install_success_boundary(
        monkeypatch
    )

    peer_nonces = iter(
        (
            "peer-nonce-1",
            "peer-nonce-2",
        )
    )

    entitlement_nonces = iter(
        (
            "entitlement-nonce-1",
            "entitlement-nonce-2",
        )
    )

    monkeypatch.setattr(
        identity,
        "generate_peer_nonce",
        lambda: next(peer_nonces),
    )

    monkeypatch.setattr(
        identity,
        "generate_entitlement_nonce",
        lambda: next(entitlement_nonces),
    )

    seen = []

    original_peer_creator = (
        identity.create_peer_proof
    )

    original_entitlement_creator = (
        identity.create_entitlement_proof
    )

    def capture_peer(
        challenge,
        *,
        signing_provider,
    ):
        seen.append(
            (
                "peer",
                challenge.nonce,
            )
        )
        return original_peer_creator(
            challenge,
            signing_provider=signing_provider,
        )

    def capture_entitlement(
        challenge,
        *,
        signing_provider,
    ):
        seen.append(
            (
                "entitlement",
                challenge.nonce,
            )
        )
        return original_entitlement_creator(
            challenge,
            signing_provider=signing_provider,
        )

    monkeypatch.setattr(
        identity,
        "create_peer_proof",
        capture_peer,
    )

    monkeypatch.setattr(
        identity,
        "create_entitlement_proof",
        capture_entitlement,
    )

    verify_guardian_identity(
        config
    )
    verify_guardian_identity(
        config
    )

    assert seen == [
        (
            "peer",
            "peer-nonce-1",
        ),
        (
            "entitlement",
            "entitlement-nonce-1",
        ),
        (
            "peer",
            "peer-nonce-2",
        ),
        (
            "entitlement",
            "entitlement-nonce-2",
        ),
    ]

    assert captured["verify_called"] is True


def test_identity_verification_fails_closed_on_fingerprint_mismatch(
    config,
    monkeypatch,
):
    class WrongSigner:
        fingerprint = (
            "0" * 64
        )

    monkeypatch.setattr(
        identity,
        "load_guardian_signing_provider",
        lambda path: WrongSigner(),
    )

    with pytest.raises(
        GuardianIdentityVerificationError,
        match="fingerprint does not match",
    ):
        verify_guardian_identity(
            config
        )


def test_identity_verification_fails_closed_on_ucii_error(
    config,
    monkeypatch,
):
    install_success_boundary(
        monkeypatch
    )

    def fail_verification(
        proof,
        *,
        credentials,
        challenge_store,
        service_entitlement_proof,
    ):
        raise RuntimeError(
            "simulated UCII failure"
        )

    monkeypatch.setattr(
        identity,
        "verify_peer_proof",
        fail_verification,
    )

    with pytest.raises(
        GuardianIdentityVerificationError,
        match="failed closed",
    ):
        verify_guardian_identity(
            config
        )


def test_identity_verification_rejects_non_verified_outcome(
    config,
    monkeypatch,
):
    install_success_boundary(
        monkeypatch
    )

    monkeypatch.setattr(
        identity,
        "verify_peer_proof",
        lambda *args, **kwargs: (
            "NOT_VERIFIED"
        ),
    )

    with pytest.raises(
        GuardianIdentityVerificationError,
        match="was not verified",
    ):
        verify_guardian_identity(
            config
        )


def test_identity_result_carries_no_authorization_grant(
    config,
    monkeypatch,
):
    install_success_boundary(
        monkeypatch
    )

    result = verify_guardian_identity(
        config
    )

    assert set(
        result.__dataclass_fields__
    ) == {
        "identity_id",
        "credential_fingerprint",
        "status",
    }

    assert not hasattr(
        result,
        "authorized",
    )
    assert not hasattr(
        result,
        "execution_authority",
    )


def test_identity_module_has_no_private_ucii_server_imports():
    source = Path(
        identity.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "pq_auth" not in source
    assert "src.pq_auth" not in source
