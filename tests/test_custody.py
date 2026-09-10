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




def test_persistent_custody_round_trip_preserves_identity(
    tmp_path,
    monkeypatch,
):
    import ucii_guardian.custody as custody

    monkeypatch.setattr(
        custody,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    path = (
        tmp_path
        / "guardian-mldsa65-v1.json"
    )

    original = GuardianSigningProvider.generate()

    custody.persist_guardian_signing_provider(
        original,
        path,
    )

    restored = custody.load_guardian_signing_provider(
        path
    )

    assert (
        restored.public_key
        == original.public_key
    )

    assert (
        restored.fingerprint
        == original.fingerprint
    )

    message = b"guardian-persistence-restart-proof"

    signature = restored.sign(
        message
    )

    with oqs.Signature(
        GUARDIAN_SIGNING_ALGORITHM
    ) as verifier:
        assert verifier.verify(
            message,
            signature,
            original.public_key,
        ) is True


def test_load_or_create_reuses_existing_guardian_identity(
    tmp_path,
    monkeypatch,
):
    import ucii_guardian.custody as custody

    monkeypatch.setattr(
        custody,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    path = (
        tmp_path
        / "guardian-mldsa65-v1.json"
    )

    first = custody.load_or_create_guardian_signing_provider(
        path
    )

    first_bytes = path.read_bytes()

    second = custody.load_or_create_guardian_signing_provider(
        path
    )

    second_bytes = path.read_bytes()

    assert first.public_key == second.public_key
    assert first.fingerprint == second.fingerprint
    assert first_bytes == second_bytes


def test_load_or_create_does_not_mask_non_race_persistence_failure(
    tmp_path,
    monkeypatch,
):
    import ucii_guardian.custody as custody

    path = (
        tmp_path
        / "guardian-mldsa65-v1.json"
    )

    original_persist = (
        custody.persist_guardian_signing_provider
    )

    def fail_after_creating_path(
        provider,
        target,
    ):
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_bytes(
            b"not-a-valid-custody-record"
        )

        raise GuardianCustodyError(
            "simulated persistence security failure"
        )

    monkeypatch.setattr(
        custody,
        "persist_guardian_signing_provider",
        fail_after_creating_path,
    )

    with pytest.raises(
        GuardianCustodyError,
        match="simulated persistence security failure",
    ):
        custody.load_or_create_guardian_signing_provider(
            path
        )

    monkeypatch.setattr(
        custody,
        "persist_guardian_signing_provider",
        original_persist,
    )


def test_load_or_create_accepts_only_explicit_already_exists_race(
    tmp_path,
    monkeypatch,
):
    import ucii_guardian.custody as custody

    monkeypatch.setattr(
        custody,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    path = (
        tmp_path
        / "guardian-mldsa65-v1.json"
    )

    winner = GuardianSigningProvider.generate()

    custody.persist_guardian_signing_provider(
        winner,
        path,
    )

    real_load = custody.load_guardian_signing_provider

    monkeypatch.setattr(
        custody.Path,
        "exists",
        lambda self: False,
    )

    def lose_creation_race(
        provider,
        target,
    ):
        raise custody.GuardianCustodyAlreadyExistsError(
            "Guardian custody record already exists"
        )

    monkeypatch.setattr(
        custody,
        "persist_guardian_signing_provider",
        lose_creation_race,
    )

    restored = real_load(
        path
    )

    assert (
        restored.public_key
        == winner.public_key
    )

    generated = GuardianSigningProvider.generate()

    try:
        custody.persist_guardian_signing_provider(
            generated,
            path,
        )
    except custody.GuardianCustodyAlreadyExistsError:
        loaded = real_load(
            path
        )
    else:
        raise AssertionError(
            "expected explicit already-exists race"
        )

    assert (
        loaded.public_key
        == winner.public_key
    )


def test_persistence_refuses_to_overwrite_existing_custody(
    tmp_path,
    monkeypatch,
):
    import ucii_guardian.custody as custody

    monkeypatch.setattr(
        custody,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    path = (
        tmp_path
        / "guardian-mldsa65-v1.json"
    )

    first = GuardianSigningProvider.generate()
    second = GuardianSigningProvider.generate()

    custody.persist_guardian_signing_provider(
        first,
        path,
    )

    before = path.read_bytes()

    with pytest.raises(
        GuardianCustodyError,
        match="already exists",
    ):
        custody.persist_guardian_signing_provider(
            second,
            path,
        )

    assert path.read_bytes() == before


def test_persistent_custody_fails_closed_on_invalid_base64(
    tmp_path,
):
    import json

    import ucii_guardian.custody as custody

    path = tmp_path / "custody.json"

    record = {
        "version": custody.GUARDIAN_CUSTODY_RECORD_VERSION,
        "algorithm": GUARDIAN_SIGNING_ALGORITHM,
        "public_key_b64": "not valid base64!",
        "secret_key_b64": "not valid base64!",
        "fingerprint": "0" * 64,
    }

    path.write_text(
        json.dumps(record),
        encoding="utf-8",
    )

    with pytest.raises(
        GuardianCustodyError,
        match="not valid base64",
    ):
        custody.load_guardian_signing_provider(
            path
        )


def test_persistent_custody_fails_closed_on_fingerprint_mismatch(
    tmp_path,
    monkeypatch,
):
    import json

    import ucii_guardian.custody as custody

    monkeypatch.setattr(
        custody,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    path = tmp_path / "custody.json"

    provider = GuardianSigningProvider.generate()

    custody.persist_guardian_signing_provider(
        provider,
        path,
    )

    record = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    record["fingerprint"] = "0" * 64

    path.write_text(
        json.dumps(record),
        encoding="utf-8",
    )

    with pytest.raises(
        GuardianCustodyError,
        match="fingerprint does not match",
    ):
        custody.load_guardian_signing_provider(
            path
        )


def test_persistent_custody_fails_closed_on_mismatched_key_pair(
    tmp_path,
    monkeypatch,
):
    import base64
    import json

    import ucii_guardian.custody as custody

    monkeypatch.setattr(
        custody,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    path = tmp_path / "custody.json"

    first = GuardianSigningProvider.generate()
    second = GuardianSigningProvider.generate()

    custody.persist_guardian_signing_provider(
        first,
        path,
    )

    record = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    record["secret_key_b64"] = base64.b64encode(
        second._secret_key
    ).decode(
        "ascii"
    )

    path.write_text(
        json.dumps(record),
        encoding="utf-8",
    )

    with pytest.raises(
        GuardianCustodyError,
        match="public and secret keys do not match",
    ):
        custody.load_guardian_signing_provider(
            path
        )


def test_persistent_custody_fails_closed_on_wrong_algorithm(
    tmp_path,
    monkeypatch,
):
    import json

    import ucii_guardian.custody as custody

    monkeypatch.setattr(
        custody,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    path = tmp_path / "custody.json"

    provider = GuardianSigningProvider.generate()

    custody.persist_guardian_signing_provider(
        provider,
        path,
    )

    record = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    record["algorithm"] = "not-ml-dsa-65"

    path.write_text(
        json.dumps(record),
        encoding="utf-8",
    )

    with pytest.raises(
        GuardianCustodyError,
        match="algorithm is invalid",
    ):
        custody.load_guardian_signing_provider(
            path
        )


def test_default_custody_path_is_user_local_and_outside_repository(
    tmp_path,
    monkeypatch,
):
    import ucii_guardian.custody as custody

    monkeypatch.setenv(
        "LOCALAPPDATA",
        str(tmp_path),
    )

    expected = (
        tmp_path
        / "UCII"
        / "Guardian"
        / "custody"
        / "guardian-mldsa65-v1.json"
    )

    assert (
        custody.default_guardian_custody_path()
        == expected
    )


def test_default_custody_path_fails_closed_without_localappdata(
    monkeypatch,
):
    import ucii_guardian.custody as custody

    monkeypatch.delenv(
        "LOCALAPPDATA",
        raising=False,
    )

    with pytest.raises(
        GuardianCustodyError,
        match="LOCALAPPDATA",
    ):
        custody.default_guardian_custody_path()


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
