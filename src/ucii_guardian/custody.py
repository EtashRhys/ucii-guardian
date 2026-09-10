"""Local cryptographic custody for UCII Guardian.

This module owns Guardian's bounded ML-DSA-65 signing boundary.

Raw private-key material remains inside GuardianSigningProvider and is
never returned through Guardian's public custody interface.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile

import oqs

from ucii.credentials import generate_fingerprint
from ucii.signing import SigningProvider


GUARDIAN_SIGNING_ALGORITHM = "ML-DSA-65"
GUARDIAN_CUSTODY_RECORD_VERSION = "ucii-guardian-custody-v1"

_EXPECTED_PUBLIC_KEY_BYTES = 1952
_EXPECTED_SECRET_KEY_BYTES = 4032
_PAIRING_CHALLENGE = (
    b"ucii-guardian-custody-pairing-check-v1"
)


class GuardianCustodyError(RuntimeError):
    """Raised when Guardian signing custody cannot safely operate."""


class GuardianCustodyAlreadyExistsError(GuardianCustodyError):
    """Raised when a custody record already exists at the target path."""


class GuardianSigningProvider:
    """Software-backed local ML-DSA-65 Guardian signing provider.

    The provider satisfies the public UCII SigningProvider protocol while
    retaining raw private-key material inside this custody boundary.
    """

    def __init__(
        self,
        *,
        public_key: bytes,
        secret_key: bytes,
    ) -> None:
        if (
            not isinstance(public_key, bytes)
            or len(public_key) != _EXPECTED_PUBLIC_KEY_BYTES
        ):
            raise GuardianCustodyError(
                "Guardian public key has invalid ML-DSA-65 length"
            )

        if (
            not isinstance(secret_key, bytes)
            or len(secret_key) != _EXPECTED_SECRET_KEY_BYTES
        ):
            raise GuardianCustodyError(
                "Guardian secret key has invalid ML-DSA-65 length"
            )

        self._public_key = public_key
        self._secret_key = secret_key

    @classmethod
    def generate(cls) -> "GuardianSigningProvider":
        """Generate a new process-local Guardian ML-DSA-65 signer.

        Raw secret-key material is generated and retained inside the provider
        rather than being returned to the caller.
        """

        try:
            with oqs.Signature(
                GUARDIAN_SIGNING_ALGORITHM
            ) as signer:
                public_key = signer.generate_keypair()
                secret_key = signer.export_secret_key()
        except Exception as exc:
            raise GuardianCustodyError(
                "Guardian ML-DSA-65 credential generation failed"
            ) from exc

        return cls(
            public_key=public_key,
            secret_key=secret_key,
        )

    @property
    def algorithm(self) -> str:
        """Return Guardian's public signing algorithm identifier."""

        return GUARDIAN_SIGNING_ALGORITHM

    @property
    def public_key(self) -> bytes:
        """Return Guardian's public verification key."""

        return self._public_key

    @property
    def fingerprint(self) -> str:
        """Return the canonical UCII fingerprint for this credential."""

        return generate_fingerprint(
            self._public_key
        )

    def sign(self, message: bytes) -> bytes:
        """Sign one authorized byte message using local ML-DSA-65 custody."""

        if not isinstance(message, bytes):
            raise TypeError(
                "Guardian signing message must be bytes"
            )

        try:
            with oqs.Signature(
                self.algorithm,
                secret_key=self._secret_key,
            ) as signer:
                return signer.sign(message)
        except Exception as exc:
            raise GuardianCustodyError(
                "Guardian ML-DSA-65 signing failed"
            ) from exc


def generate_guardian_signing_provider() -> SigningProvider:
    """Generate Guardian's bounded public UCII signing provider."""

    return GuardianSigningProvider.generate()


def default_guardian_custody_path() -> Path:
    """Return Guardian's default user-local custody record path."""

    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if not local_app_data:
        raise GuardianCustodyError(
            "LOCALAPPDATA is required for default Guardian custody"
        )

    return (
        Path(local_app_data)
        / "UCII"
        / "Guardian"
        / "custody"
        / "guardian-mldsa65-v1.json"
    )


def _encode_key(value: bytes) -> str:
    return base64.b64encode(
        value
    ).decode(
        "ascii"
    )


def _decode_key(
    record: dict[str, object],
    field: str,
) -> bytes:
    value = record.get(
        field
    )

    if not isinstance(value, str):
        raise GuardianCustodyError(
            f"Guardian custody {field} must be a base64 string"
        )

    try:
        return base64.b64decode(
            value,
            validate=True,
        )
    except Exception as exc:
        raise GuardianCustodyError(
            f"Guardian custody {field} is not valid base64"
        ) from exc


def _verify_key_pair(
    provider: GuardianSigningProvider,
) -> None:
    """Fail closed unless the stored public and private material match."""

    signature = provider.sign(
        _PAIRING_CHALLENGE
    )

    try:
        with oqs.Signature(
            GUARDIAN_SIGNING_ALGORITHM
        ) as verifier:
            verified = verifier.verify(
                _PAIRING_CHALLENGE,
                signature,
                provider.public_key,
            )
    except Exception as exc:
        raise GuardianCustodyError(
            "Guardian custody key-pair verification failed"
        ) from exc

    if verified is not True:
        raise GuardianCustodyError(
            "Guardian custody public and secret keys do not match"
        )


def _serialize_provider(
    provider: GuardianSigningProvider,
) -> bytes:
    """Serialize local custody material without exposing it publicly."""

    record = {
        "version": GUARDIAN_CUSTODY_RECORD_VERSION,
        "algorithm": provider.algorithm,
        "public_key_b64": _encode_key(
            provider._public_key
        ),
        "secret_key_b64": _encode_key(
            provider._secret_key
        ),
        "fingerprint": provider.fingerprint,
    }

    return (
        json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def _deserialize_provider(
    raw: bytes,
) -> GuardianSigningProvider:
    try:
        text = raw.decode(
            "utf-8"
        )

        record = json.loads(
            text
        )
    except Exception as exc:
        raise GuardianCustodyError(
            "Guardian custody record is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(record, dict):
        raise GuardianCustodyError(
            "Guardian custody record must be a JSON object"
        )

    expected_fields = {
        "version",
        "algorithm",
        "public_key_b64",
        "secret_key_b64",
        "fingerprint",
    }

    if set(record) != expected_fields:
        raise GuardianCustodyError(
            "Guardian custody record has unexpected fields"
        )

    if (
        record.get("version")
        != GUARDIAN_CUSTODY_RECORD_VERSION
    ):
        raise GuardianCustodyError(
            "Guardian custody record version is unsupported"
        )

    if (
        record.get("algorithm")
        != GUARDIAN_SIGNING_ALGORITHM
    ):
        raise GuardianCustodyError(
            "Guardian custody algorithm is invalid"
        )

    public_key = _decode_key(
        record,
        "public_key_b64",
    )

    secret_key = _decode_key(
        record,
        "secret_key_b64",
    )

    provider = GuardianSigningProvider(
        public_key=public_key,
        secret_key=secret_key,
    )

    fingerprint = record.get(
        "fingerprint"
    )

    if (
        not isinstance(fingerprint, str)
        or fingerprint != provider.fingerprint
    ):
        raise GuardianCustodyError(
            "Guardian custody fingerprint does not match public key"
        )

    _verify_key_pair(
        provider
    )

    return provider


def _harden_private_path(
    path: Path,
    *,
    directory: bool,
) -> None:
    """Apply a private user-only filesystem boundary."""

    if os.name == "nt":
        try:
            user = subprocess.run(
                ["whoami"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            if not user:
                raise GuardianCustodyError(
                    "Windows user identity could not be determined"
                )

            permission = (
                "(OI)(CI)(F)"
                if directory
                else "(F)"
            )

            subprocess.run(
                [
                    "icacls.exe",
                    str(path),
                    "/inheritance:r",
                    "/grant:r",
                    f"{user}:{permission}",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except GuardianCustodyError:
            raise
        except Exception as exc:
            raise GuardianCustodyError(
                "Guardian custody Windows ACL hardening failed"
            ) from exc

        return

    try:
        path.chmod(
            0o700 if directory else 0o600
        )
    except Exception as exc:
        raise GuardianCustodyError(
            "Guardian custody permission hardening failed"
        ) from exc


def _ensure_private_directory(
    directory: Path,
) -> None:
    try:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )
    except Exception as exc:
        raise GuardianCustodyError(
            "Guardian custody directory creation failed"
        ) from exc

    _harden_private_path(
        directory,
        directory=True,
    )


def load_guardian_signing_provider(
    path: Path,
) -> GuardianSigningProvider:
    """Load and cryptographically validate persistent Guardian custody."""

    try:
        raw = path.read_bytes()
    except Exception as exc:
        raise GuardianCustodyError(
            "Guardian custody record could not be read"
        ) from exc

    provider = _deserialize_provider(
        raw
    )

    return provider


def persist_guardian_signing_provider(
    provider: GuardianSigningProvider,
    path: Path,
) -> None:
    """Persist Guardian custody atomically without overwriting an existing key."""

    path = Path(
        path
    )

    _verify_key_pair(
        provider
    )

    _ensure_private_directory(
        path.parent
    )

    raw = _serialize_provider(
        provider
    )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(
                handle.name
            )

            handle.write(
                raw
            )

            handle.flush()
            os.fsync(
                handle.fileno()
            )

        _harden_private_path(
            temporary_path,
            directory=False,
        )

        try:
            os.link(
                temporary_path,
                path,
            )
        except FileExistsError as exc:
            raise GuardianCustodyAlreadyExistsError(
                "Guardian custody record already exists"
            ) from exc

        _harden_private_path(
            path,
            directory=False,
        )

    except GuardianCustodyError:
        raise
    except Exception as exc:
        raise GuardianCustodyError(
            "Guardian custody record persistence failed"
        ) from exc
    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            try:
                temporary_path.unlink()
            except OSError:
                pass


def load_or_create_guardian_signing_provider(
    path: Path | None = None,
) -> GuardianSigningProvider:
    """Load stable Guardian custody or create it once if absent."""

    resolved = (
        Path(path)
        if path is not None
        else default_guardian_custody_path()
    )

    if resolved.exists():
        return load_guardian_signing_provider(
            resolved
        )

    generated = GuardianSigningProvider.generate()

    try:
        persist_guardian_signing_provider(
            generated,
            resolved,
        )
    except GuardianCustodyAlreadyExistsError:
        return load_guardian_signing_provider(
            resolved
        )

    return load_guardian_signing_provider(
        resolved
    )
