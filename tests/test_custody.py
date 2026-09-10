"""Tests for Guardian local ML-DSA-65 signing custody."""

from __future__ import annotations

import hashlib
import inspect

import oqs
import pytest

from ucii.signing import SigningProvider

from ucii_guardian.custody import (
    GUARDIAN_SIGNING_ALGORITHM,
    GuardianCustodyError,
    GuardianSigningProvider,
    generate_guardian_signing_provider,
)


def test_generated_guardian_provider_matches_ucii_contract():
    provider = GuardianSigningProvider.generate()

    assert provider.algorithm == "ML-DSA-65"

    assert isinstance(
        provider.public_key,
        bytes,
    )

    assert len(
        provider.public_key
    ) == 1952

    expected_fingerprint = hashlib.sha256(
        provider.public_key
    ).hexdigest()

    assert (
        provider.fingerprint
        == expected_fingerprint
    )


def test_generated_provider_satisfies_public_ucii_protocol():
    provider = generate_guardian_signing_provider()

    assert isinstance(
        provider,
        SigningProvider,
    )

    assert (
        provider.algorithm
        == GUARDIAN_SIGNING_ALGORITHM
    )


def test_guardian_signing_provider_produces_verifiable_ml_dsa_signature():
    provider = GuardianSigningProvider.generate()

    message = (
        b"ucii-guardian-local-custody-proof"
    )

    signature = provider.sign(
        message
    )

    assert isinstance(
        signature,
        bytes,
    )

    assert len(signature) == 3309

    with oqs.Signature(
        GUARDIAN_SIGNING_ALGORITHM
    ) as verifier:
        assert verifier.verify(
            message,
            signature,
            provider.public_key,
        ) is True


def test_guardian_signature_fails_for_different_message():
    provider = GuardianSigningProvider.generate()

    signature = provider.sign(
        b"authorized-message"
    )

    with oqs.Signature(
        GUARDIAN_SIGNING_ALGORITHM
    ) as verifier:
        assert verifier.verify(
            b"different-message",
            signature,
            provider.public_key,
        ) is False


def test_guardian_provider_rejects_non_bytes_messages():
    provider = GuardianSigningProvider.generate()

    with pytest.raises(
        TypeError,
        match="must be bytes",
    ):
        provider.sign(
            "not-bytes"  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("public_key", "secret_key"),
    (
        (b"", b"secret"),
        (b"public", b""),
    ),
)
def test_guardian_provider_rejects_empty_key_material(
    public_key,
    secret_key,
):
    with pytest.raises(
        GuardianCustodyError
    ):
        GuardianSigningProvider(
            public_key=public_key,
            secret_key=secret_key,
        )


def test_guardian_public_interface_exposes_no_secret_key():
    provider = GuardianSigningProvider.generate()

    assert not hasattr(
        provider,
        "secret_key",
    )

    assert not hasattr(
        provider,
        "export_secret_key",
    )

    public_members = {
        name
        for name, _ in inspect.getmembers(
            type(provider)
        )
        if not name.startswith("_")
    }

    assert public_members == {
        "algorithm",
        "fingerprint",
        "generate",
        "public_key",
        "sign",
    }


def test_normal_generation_api_never_returns_secret_key_material():
    provider = generate_guardian_signing_provider()

    assert isinstance(
        provider,
        SigningProvider,
    )

    assert not hasattr(
        provider,
        "secret_key",
    )

    assert not hasattr(
        provider,
        "export_secret_key",
    )


def test_custody_module_has_no_ucii_server_internal_imports():
    import ucii_guardian.custody as custody

    source = inspect.getsource(
        custody
    )

    prohibited = (
        "from pq_auth",
        "import pq_auth",
        "from fastapi",
        "import fastapi",
        "from sqlalchemy",
        "import sqlalchemy",
    )

    for value in prohibited:
        assert value not in source
