"""Guardian delegated action-authority boundary.

This module maps authoritative UCII delegated-action state into Guardian's
three canonical authority decisions.

Identity verification, credential possession, model output, and action intent
never grant authority by themselves.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ucii import UCIIClient

from ucii_guardian.action import ActionRequest
from ucii_guardian.custody import (
    load_guardian_signing_provider,
)
from ucii_guardian.identity import (
    GUARDIAN_VERIFIED,
    GuardianIdentityConfig,
    GuardianIdentityVerification,
)


class AuthorityDecision(str, Enum):
    """Guardian's canonical action-authority outcomes."""

    ALLOW = "ALLOW"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    DENY = "DENY"


class GuardianAuthorityError(RuntimeError):
    """Raised when an authority decision cannot be established safely."""


@dataclass(frozen=True)
class AuthorityDecisionResult:
    """Established Guardian authority decision.

    This result is non-executing. It reports only the decision and the
    authoritative UCII state that produced it.
    """

    decision: AuthorityDecision
    authority_state: str
    authority_id: str | None
    identity_id: str
    credential_fingerprint: str
    operation: str
    request_id: str


def _canonical_action_message(
    action: ActionRequest,
) -> bytes:
    """Create deterministic bytes binding the credential proof to one action."""

    payload = {
        "guardian_identity": action.guardian_identity,
        "operation": action.operation,
        "parameters": dict(action.parameters),
        "request_id": action.request_id,
        "requested_at": action.requested_at.isoformat(),
        "requester": action.requester,
        "target": action.target,
    }

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _validate_identity_fact(
    action: ActionRequest,
    *,
    identity: GuardianIdentityVerification,
    config: GuardianIdentityConfig,
) -> None:
    if identity.status != GUARDIAN_VERIFIED:
        raise GuardianAuthorityError(
            "Guardian identity is not UCII_VERIFIED"
        )

    if identity.identity_id != config.identity_id:
        raise GuardianAuthorityError(
            "Verified identity does not match Guardian configuration"
        )

    if (
        identity.credential_fingerprint
        != config.credential_fingerprint
    ):
        raise GuardianAuthorityError(
            "Verified credential does not match Guardian configuration"
        )

    if action.guardian_identity != identity.identity_id:
        raise GuardianAuthorityError(
            "Action Guardian identity does not match verified identity"
        )


def _map_authority_state(
    *,
    authority_state: str,
    authorized: bool,
    executed: bool,
) -> AuthorityDecision:
    """Map authoritative UCII state into Guardian's bounded decision."""

    if executed is not False:
        raise GuardianAuthorityError(
            "Authority check unexpectedly reported execution"
        )

    if authority_state == "ACTIVE":
        if authorized is not True:
            raise GuardianAuthorityError(
                "ACTIVE authority was not reported authorized"
            )
        return AuthorityDecision.ALLOW

    if authorized is not False:
        raise GuardianAuthorityError(
            "Non-active authority unexpectedly reported authorized"
        )

    if authority_state == "NOT_GRANTED":
        return AuthorityDecision.ESCALATION_REQUIRED

    if authority_state in {
        "REVOKED",
        "EXPIRED",
        "INVALID",
    }:
        return AuthorityDecision.DENY

    raise GuardianAuthorityError(
        "UCII returned an unknown authority state"
    )


def check_authority(
    action: ActionRequest,
    *,
    identity: GuardianIdentityVerification,
    config: GuardianIdentityConfig,
) -> AuthorityDecisionResult:
    """Evaluate one proposed action through the public UCII authority boundary.

    The caller must supply an independently established UCII_VERIFIED identity
    fact. That authentication fact is necessary but never sufficient for ALLOW.

    Guardian signs a canonical representation of the proposed action with its
    locally held ML-DSA credential, then asks UCII for current delegated
    authority state for the exact operation.

    This function cannot execute the action.
    """

    try:
        _validate_identity_fact(
            action,
            identity=identity,
            config=config,
        )

        signer = load_guardian_signing_provider(
            Path(config.custody_path)
        )

        if (
            signer.fingerprint
            != config.credential_fingerprint
        ):
            raise GuardianAuthorityError(
                "Guardian custody fingerprint does not match configuration"
            )

        message_bytes = _canonical_action_message(
            action
        )

        signature_bytes = signer.sign(
            message_bytes
        )

        message = message_bytes.decode(
            "utf-8"
        )

        signature = base64.b64encode(
            signature_bytes
        ).decode(
            "ascii"
        )

        with UCIIClient(
            base_url=config.base_url,
            timeout=30.0,
        ) as client:
            response = (
                client.authorization.check_delegated(
                    identity_id=config.identity_id,
                    credential_fingerprint=(
                        config.credential_fingerprint
                    ),
                    operation=action.operation,
                    message=message,
                    signature=signature,
                )
            )

        if not isinstance(response, dict):
            raise GuardianAuthorityError(
                "UCII authority response must be an object"
            )

        expected_identity = response.get(
            "identity_id"
        )

        expected_fingerprint = response.get(
            "credential_fingerprint"
        )

        expected_operation = response.get(
            "operation"
        )

        if expected_identity != config.identity_id:
            raise GuardianAuthorityError(
                "UCII authority response identity mismatch"
            )

        if (
            expected_fingerprint
            != config.credential_fingerprint
        ):
            raise GuardianAuthorityError(
                "UCII authority response credential mismatch"
            )

        if expected_operation != action.operation:
            raise GuardianAuthorityError(
                "UCII authority response operation mismatch"
            )

        credential_status = response.get(
            "credential_status"
        )

        if credential_status != "ACTIVE":
            raise GuardianAuthorityError(
                "UCII authority response credential is not ACTIVE"
            )

        authority_state = response.get(
            "authority_state"
        )

        if not isinstance(
            authority_state,
            str,
        ):
            raise GuardianAuthorityError(
                "UCII authority state is invalid"
            )

        authority_id = response.get(
            "authority_id"
        )

        if authority_state == "ACTIVE":
            if (
                not isinstance(authority_id, str)
                or not authority_id.strip()
            ):
                raise GuardianAuthorityError(
                    "ACTIVE UCII authority response has no authority ID"
                )

            authority_id = authority_id.strip()
        elif authority_id is not None:
            raise GuardianAuthorityError(
                "Non-active UCII authority response unexpectedly identified authority"
            )

        decision = _map_authority_state(
            authority_state=authority_state,
            authorized=response.get(
                "authorized"
            ),
            executed=response.get(
                "executed"
            ),
        )

        return AuthorityDecisionResult(
            decision=decision,
            authority_state=authority_state,
            authority_id=authority_id,
            identity_id=config.identity_id,
            credential_fingerprint=(
                config.credential_fingerprint
            ),
            operation=action.operation,
            request_id=action.request_id,
        )

    except GuardianAuthorityError:
        raise
    except Exception as exc:
        raise GuardianAuthorityError(
            "Guardian authority check failed closed"
        ) from exc
