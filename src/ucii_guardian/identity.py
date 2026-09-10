"""Public UCII identity verification boundary for Guardian.

This module proves Guardian identity and active credential possession through
the public UCII SDK/HTTP boundary.

UCII_VERIFIED establishes authentication/credential verification only.
It never establishes action authorization, approval, payment authority,
or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ucii import (
    EntitlementProofChallenge,
    PeerChallenge,
    PeerChallengeStore,
    UCIIClient,
    create_entitlement_proof,
    create_peer_proof,
    generate_entitlement_nonce,
    generate_peer_nonce,
    verify_peer_proof,
)

from ucii_guardian.custody import (
    load_guardian_signing_provider,
)


GUARDIAN_VERIFIED = "UCII_VERIFIED"
GUARDIAN_VERIFICATION_OPERATION = (
    "POST /v1/credentials/verify"
)


class GuardianIdentityVerificationError(RuntimeError):
    """Raised when Guardian cannot establish its UCII identity."""


@dataclass(frozen=True)
class GuardianIdentityConfig:
    """Non-secret configuration required to verify Guardian identity."""

    base_url: str
    identity_id: str
    credential_id: str
    credential_fingerprint: str
    custody_path: Path
    verifier_identity_id: str = (
        "ucii-guardian-local-verifier"
    )
    context: str = (
        "ucii-guardian-runtime-identity-verification"
    )
    proof_lifetime_seconds: int = 300


@dataclass(frozen=True)
class GuardianIdentityVerification:
    """Established Guardian authentication fact.

    This result deliberately carries no authorization or execution grant.
    """

    identity_id: str
    credential_fingerprint: str
    status: str


def _require_non_empty(
    value: str,
    *,
    field: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise GuardianIdentityVerificationError(
            f"{field} must be a non-empty string"
        )


def _validate_config(
    config: GuardianIdentityConfig,
) -> None:
    _require_non_empty(
        config.base_url,
        field="base_url",
    )
    _require_non_empty(
        config.identity_id,
        field="identity_id",
    )
    _require_non_empty(
        config.credential_id,
        field="credential_id",
    )
    _require_non_empty(
        config.credential_fingerprint,
        field="credential_fingerprint",
    )
    _require_non_empty(
        config.verifier_identity_id,
        field="verifier_identity_id",
    )
    _require_non_empty(
        config.context,
        field="context",
    )

    if config.proof_lifetime_seconds <= 0:
        raise GuardianIdentityVerificationError(
            "proof_lifetime_seconds must be positive"
        )


def verify_guardian_identity(
    config: GuardianIdentityConfig,
) -> GuardianIdentityVerification:
    """Verify Guardian through the public UCII boundary.

    Every invocation creates fresh peer-authentication and economic-entitlement
    proof challenges. Failure at any point fails closed.
    """

    _validate_config(
        config
    )

    try:
        signer = load_guardian_signing_provider(
            Path(config.custody_path)
        )

        if (
            signer.fingerprint
            != config.credential_fingerprint
        ):
            raise GuardianIdentityVerificationError(
                "Guardian custody fingerprint does not match "
                "configured UCII credential"
            )

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            now
            + timedelta(
                seconds=config.proof_lifetime_seconds
            )
        )

        peer_challenge = PeerChallenge(
            nonce=generate_peer_nonce(),
            verifier_identity_id=(
                config.verifier_identity_id
            ),
            prover_identity_id=config.identity_id,
            credential_fingerprint=(
                config.credential_fingerprint
            ),
            context=config.context,
            issued_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
        )

        peer_proof = create_peer_proof(
            peer_challenge,
            signing_provider=signer,
        )

        economic_now = datetime.now(
            timezone.utc
        )

        economic_expires_at = (
            economic_now
            + timedelta(
                seconds=config.proof_lifetime_seconds
            )
        )

        entitlement_challenge = (
            EntitlementProofChallenge(
                nonce=generate_entitlement_nonce(),
                subject_identity_id=(
                    config.identity_id
                ),
                credential_fingerprint=(
                    config.credential_fingerprint
                ),
                method=(
                    GUARDIAN_VERIFICATION_OPERATION.split(
                        " ",
                        1,
                    )[0]
                ),
                path=(
                    GUARDIAN_VERIFICATION_OPERATION.split(
                        " ",
                        1,
                    )[1]
                ),
                issued_at=economic_now.isoformat(),
                expires_at=(
                    economic_expires_at.isoformat()
                ),
            )
        )

        entitlement_proof = (
            create_entitlement_proof(
                entitlement_challenge,
                signing_provider=signer,
            )
        )

        challenge_store = PeerChallengeStore()

        with UCIIClient(
            base_url=config.base_url,
            timeout=30.0,
        ) as client:
            outcome = verify_peer_proof(
                peer_proof,
                credentials=client.credentials,
                challenge_store=challenge_store,
                service_entitlement_proof=(
                    entitlement_proof
                ),
            )

    except GuardianIdentityVerificationError:
        raise
    except Exception as exc:
        raise GuardianIdentityVerificationError(
            "Guardian UCII identity verification failed closed"
        ) from exc

    if outcome != GUARDIAN_VERIFIED:
        raise GuardianIdentityVerificationError(
            "Guardian UCII identity was not verified"
        )

    return GuardianIdentityVerification(
        identity_id=config.identity_id,
        credential_fingerprint=(
            config.credential_fingerprint
        ),
        status=GUARDIAN_VERIFIED,
    )
