"""Guardian delegated-authority lifecycle boundary.

This module may mutate delegated action authority only through the public UCII
SDK lifecycle surface.

It does not authenticate Guardian, grant authority, reactivate revoked
authority, execute consequential actions, obtain human approval, invoke
Strands, or expose controller authority to the browser or provenance layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ucii import UCIIClient

from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)
from ucii_guardian.identity import GuardianIdentityConfig


class GuardianAuthorityLifecycleError(RuntimeError):
    """Raised when an authority lifecycle mutation cannot be established safely."""


@dataclass(frozen=True)
class AuthorityRevocationResult:
    """Authoritative confirmation that one exact authority was revoked."""

    authority_id: str
    identity_id: str
    authority_state: str
    allowed_operations: tuple[str, ...]
    granted_by: str
    revoked_at: str
    revocation_reason: str


def _non_empty(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuardianAuthorityLifecycleError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def revoke_active_authority(
    *,
    authority: AuthorityDecisionResult,
    config: GuardianIdentityConfig,
    controller_authority: str,
    reason: str,
) -> AuthorityRevocationResult:
    """Permanently revoke one exact trusted ACTIVE delegated authority.

    The authority ID comes only from an already-established Guardian authority
    result. The caller supplies controller authority from a server-side secret
    boundary; this function never persists or returns that secret.

    Revocation uses only the public UCII SDK.
    """

    try:
        if not isinstance(
            authority,
            AuthorityDecisionResult,
        ):
            raise GuardianAuthorityLifecycleError(
                "Revocation requires established Guardian authority evidence"
            )

        if not isinstance(
            config,
            GuardianIdentityConfig,
        ):
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
                "Authority identity does not match Guardian configuration"
            )

        operation = _non_empty(
            authority.operation,
            field_name="operation",
        )

        controller_secret = _non_empty(
            controller_authority,
            field_name="controller_authority",
        )

        normalized_reason = _non_empty(
            reason,
            field_name="reason",
        )

        with UCIIClient(
            base_url=config.base_url,
            timeout=30.0,
        ) as client:
            response = (
                client.authorization.revoke_delegated(
                    authority_id=authority_id,
                    reason=normalized_reason,
                    controller_authority=controller_secret,
                )
            )

        if not isinstance(response, dict):
            raise GuardianAuthorityLifecycleError(
                "UCII revocation response must be an object"
            )

        response_authority_id = response.get(
            "authority_id"
        )

        if response_authority_id != authority_id:
            raise GuardianAuthorityLifecycleError(
                "UCII revocation response authority mismatch"
            )

        response_identity_id = response.get(
            "identity_id"
        )

        if response_identity_id != config.identity_id:
            raise GuardianAuthorityLifecycleError(
                "UCII revocation response identity mismatch"
            )

        authority_state = response.get(
            "authority_state"
        )

        if authority_state != "REVOKED":
            raise GuardianAuthorityLifecycleError(
                "UCII did not confirm REVOKED authority state"
            )

        raw_operations = response.get(
            "allowed_operations"
        )

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
                "UCII revocation response operations are invalid"
            )

        allowed_operations = tuple(
            item.strip()
            for item in raw_operations
        )

        if operation not in allowed_operations:
            raise GuardianAuthorityLifecycleError(
                "Revoked authority does not cover the trusted operation"
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
                "UCII revocation response reason mismatch"
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
