"""Local cryptographic custody for UCII Guardian.

This module owns Guardian's bounded ML-DSA-65 signing boundary.

Raw private-key material remains inside GuardianSigningProvider and is
never returned through Guardian's public custody interface.
"""

from __future__ import annotations

import oqs

from ucii.credentials import generate_fingerprint
from ucii.signing import SigningProvider


GUARDIAN_SIGNING_ALGORITHM = "ML-DSA-65"


class GuardianCustodyError(RuntimeError):
    """Raised when Guardian signing custody cannot safely operate."""


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
        if not isinstance(public_key, bytes) or not public_key:
            raise GuardianCustodyError(
                "Guardian public key must be non-empty bytes"
            )

        if not isinstance(secret_key, bytes) or not secret_key:
            raise GuardianCustodyError(
                "Guardian secret key must be non-empty bytes"
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

        if not public_key:
            raise GuardianCustodyError(
                "Guardian public key is empty"
            )

        if not secret_key:
            raise GuardianCustodyError(
                "Guardian secret key is empty"
            )

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
