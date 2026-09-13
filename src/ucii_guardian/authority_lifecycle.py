"""Guardian delegated-authority lifecycle boundary.

Guardian may request grant or revocation only through the public UCII SDK
boundary.

Guardian supplies its own fresh service-entitlement proof for economic access.
It never receives, stores, transports, or supplies UCII controller authority.
Lifecycle authority remains inside UCII's protected lifecycle boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ucii import (
    EntitlementProofChallenge,
    UCIIClient,
    create_entitlement_proof,
    generate_entitlement_nonce,
)

from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)
from ucii_guardian.custody import load_guardian_signing_provider
from ucii_guardian.identity import GuardianIdentityConfig


class GuardianAuthorityLifecycleError(RuntimeError):
    """Guardian lifecycle request failed closed."""


@dataclass(frozen=True)
class AuthorityGrantResult:
    """Authoritative UCII confirmation of one fresh delegated grant."""

    authority_id: str
    identity_id: str
    authority_state: str
    allowed_operations: tuple[str, ...]
    granted_by: str
    granted_at: str


@dataclass(frozen=True)
class AuthorityRevocationResult:
    """Authoritative UCII confirmation of exact delegated revocation."""

    authority_id: str
    identity_id: str
    authority_state: str
    allowed_operations: tuple[str, ...]
    granted_by: str
    revoked_at: str
    revocation_reason: str


def _non_empty(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuardianAuthorityLifecycleError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _grant_entitlement(
    *,
    config: GuardianIdentityConfig,
):
    signer = load_guardian_signing_provider(
        config.custody_path
    )

    if signer.fingerprint != config.credential_fingerprint:
        raise GuardianAuthorityLifecycleError(
            "Guardian custody fingerprint does not match configured credential"
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        seconds=config.proof_lifetime_seconds
    )

    challenge = EntitlementProofChallenge(
        nonce=generate_entitlement_nonce(),
        subject_identity_id=config.identity_id,
        credential_fingerprint=config.credential_fingerprint,
        method="POST",
        path="/v1/authorization/delegated/grant",
        issued_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
    )

    return create_entitlement_proof(
        challenge,
        signing_provider=signer,
    )


def _revocation_entitlement(
    *,
    authority_id: str,
    config: GuardianIdentityConfig,
):
    signer = load_guardian_signing_provider(
        config.custody_path
    )

    if signer.fingerprint != config.credential_fingerprint:
        raise GuardianAuthorityLifecycleError(
            "Guardian custody fingerprint does not match configured credential"
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        seconds=config.proof_lifetime_seconds
    )

    challenge = EntitlementProofChallenge(
        nonce=generate_entitlement_nonce(),
        subject_identity_id=config.identity_id,
        credential_fingerprint=config.credential_fingerprint,
        method="POST",
        path=(
            "/v1/authorization/delegated/"
            f"{authority_id}/revoke"
        ),
        issued_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
    )

    return create_entitlement_proof(
        challenge,
        signing_provider=signer,
    )


def grant_standing_authority(
    *,
    config: GuardianIdentityConfig,
    operation: str,
    granted_by: str,
) -> AuthorityGrantResult:
    """Request one fresh bounded standing-authority grant for Guardian."""

    try:
        if not isinstance(config, GuardianIdentityConfig):
            raise GuardianAuthorityLifecycleError(
                "Grant requires Guardian identity configuration"
            )

        normalized_operation = _non_empty(
            operation,
            field_name="operation",
        )

        normalized_granted_by = _non_empty(
            granted_by,
            field_name="granted_by",
        )

        entitlement = _grant_entitlement(
            config=config,
        )

        with UCIIClient(
            base_url=config.base_url,
            timeout=30.0,
        ) as client:
            response = client.authorization.grant_delegated(
                identity_id=config.identity_id,
                allowed_operations=[normalized_operation],
                granted_by=normalized_granted_by,
                service_entitlement_proof=entitlement,
            )

        if not isinstance(response, dict):
            raise GuardianAuthorityLifecycleError(
                "UCII grant response must be an object"
            )

        authority_id = _non_empty(
            response.get("authority_id"),
            field_name="authority_id",
        )

        if response.get("identity_id") != config.identity_id:
            raise GuardianAuthorityLifecycleError(
                "UCII grant response identity mismatch"
            )

        if response.get("authority_state") != "ACTIVE":
            raise GuardianAuthorityLifecycleError(
                "UCII did not confirm ACTIVE authority state"
            )

        raw_operations = response.get("allowed_operations")

        if (
            not isinstance(raw_operations, list)
            or len(raw_operations) != 1
            or not isinstance(raw_operations[0], str)
            or not raw_operations[0].strip()
        ):
            raise GuardianAuthorityLifecycleError(
                "UCII grant operations are invalid"
            )

        allowed_operations = tuple(
            item.strip()
            for item in raw_operations
        )

        if allowed_operations != (normalized_operation,):
            raise GuardianAuthorityLifecycleError(
                "UCII grant operation scope mismatch"
            )

        returned_granted_by = _non_empty(
            response.get("granted_by"),
            field_name="granted_by",
        )

        if returned_granted_by != normalized_granted_by:
            raise GuardianAuthorityLifecycleError(
                "UCII grant grantor mismatch"
            )

        granted_at = _non_empty(
            response.get("granted_at"),
            field_name="granted_at",
        )

        return AuthorityGrantResult(
            authority_id=authority_id,
            identity_id=config.identity_id,
            authority_state="ACTIVE",
            allowed_operations=allowed_operations,
            granted_by=returned_granted_by,
            granted_at=granted_at,
        )

    except GuardianAuthorityLifecycleError:
        raise
    except Exception as exc:
        raise GuardianAuthorityLifecycleError(
            "Guardian authority grant failed closed"
        ) from exc


def revoke_active_authority(
    *,
    authority: AuthorityDecisionResult,
    config: GuardianIdentityConfig,
    reason: str,
) -> AuthorityRevocationResult:
    """Request permanent revocation of one exact trusted ACTIVE authority."""

    try:
        if not isinstance(authority, AuthorityDecisionResult):
            raise GuardianAuthorityLifecycleError(
                "Revocation requires established Guardian authority evidence"
            )

        if not isinstance(config, GuardianIdentityConfig):
            raise GuardianAuthorityLifecycleError(
                "Revocation requires Guardian identity configuration"
            )

        if authority.decision is not AuthorityDecision.ALLOW:
            raise GuardianAuthorityLifecycleError(
                "Revocation requires an ALLOW authority result"
            )

        if authority.authority_state != "ACTIVE":
            raise GuardianAuthorityLifecycleError(
                "Revocation requires ACTIVE delegated authority"
            )

        authority_id = _non_empty(
            authority.authority_id,
            field_name="authority_id",
        )

        if authority.identity_id != config.identity_id:
            raise GuardianAuthorityLifecycleError(
                "Authority identity does not match Guardian"
            )

        operation = _non_empty(
            authority.operation,
            field_name="operation",
        )

        normalized_reason = _non_empty(
            reason,
            field_name="reason",
        )

        entitlement = _revocation_entitlement(
            authority_id=authority_id,
            config=config,
        )

        with UCIIClient(
            base_url=config.base_url,
            timeout=30.0,
        ) as client:
            response = client.authorization.revoke_delegated(
                authority_id=authority_id,
                reason=normalized_reason,
                service_entitlement_proof=entitlement,
            )

        if not isinstance(response, dict):
            raise GuardianAuthorityLifecycleError(
                "UCII revocation response must be an object"
            )

        if response.get("authority_id") != authority_id:
            raise GuardianAuthorityLifecycleError(
                "UCII revocation response authority mismatch"
            )

        if response.get("identity_id") != config.identity_id:
            raise GuardianAuthorityLifecycleError(
                "UCII revocation response identity mismatch"
            )

        if response.get("authority_state") != "REVOKED":
            raise GuardianAuthorityLifecycleError(
                "UCII did not confirm REVOKED authority state"
            )

        raw_operations = response.get("allowed_operations")

        if (
            not isinstance(raw_operations, list)
            or not raw_operations
            or any(
                not isinstance(item, str)
                or not item.strip()
                for item in raw_operations
            )
        ):
            raise GuardianAuthorityLifecycleError(
                "UCII revocation operations are invalid"
            )

        allowed_operations = tuple(
            item.strip()
            for item in raw_operations
        )

        if operation not in allowed_operations:
            raise GuardianAuthorityLifecycleError(
                "Returned authority does not cover trusted operation"
            )

        granted_by = _non_empty(
            response.get("granted_by"),
            field_name="granted_by",
        )

        revoked_at = _non_empty(
            response.get("revoked_at"),
            field_name="revoked_at",
        )

        revocation_reason = _non_empty(
            response.get("revocation_reason"),
            field_name="revocation_reason",
        )

        if revocation_reason != normalized_reason:
            raise GuardianAuthorityLifecycleError(
                "UCII revocation reason mismatch"
            )

        return AuthorityRevocationResult(
            authority_id=authority_id,
            identity_id=config.identity_id,
            authority_state="REVOKED",
            allowed_operations=allowed_operations,
            granted_by=granted_by,
            revoked_at=revoked_at,
            revocation_reason=revocation_reason,
        )

    except GuardianAuthorityLifecycleError:
        raise
    except Exception as exc:
        raise GuardianAuthorityLifecycleError(
            "Guardian authority revocation failed closed"
        ) from exc
