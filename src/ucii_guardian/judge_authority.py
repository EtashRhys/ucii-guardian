"""Isolated non-production authority state for Guardian Judge/Test Mode.

This module exists only to make the Guardian lifecycle repeatable in a
non-production judging environment.

It does not call UCII, possess controller authority, mutate production
delegated authority, grant execution authority by itself, or perform any
consequential action.

Production authority and lifecycle components remain separate and untouched.
"""

from __future__ import annotations

from uuid import uuid4

from ucii_guardian.action import ActionRequest
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)
from ucii_guardian.identity import (
    GUARDIAN_VERIFIED,
    GuardianIdentityConfig,
    GuardianIdentityVerification,
)


JUDGE_NOT_GRANTED = "NOT_GRANTED"
JUDGE_ACTIVE = "ACTIVE"
JUDGE_REVOKED = "REVOKED"


class JudgeAuthorityError(RuntimeError):
    """Raised when isolated Judge/Test authority cannot be established safely."""


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JudgeAuthorityError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


class JudgeAuthorityState:
    """Resettable, isolated authority state for the judging environment.

    The state machine is intentionally narrow:

    NOT_GRANTED -> ACTIVE -> REVOKED
           ^                    |
           |------ reset -------|

    Reset is also permitted from NOT_GRANTED or ACTIVE so a judge can always
    return the demonstration to a known initial state.

    A revoked grant cannot be silently reactivated. It must be reset first,
    after which a later grant receives a new isolated authority identifier.
    """

    def __init__(
        self,
        *,
        identity_id: str,
        credential_fingerprint: str,
        operation: str,
    ) -> None:
        self._identity_id = _required_text(
            identity_id,
            field_name="identity_id",
        )
        self._credential_fingerprint = _required_text(
            credential_fingerprint,
            field_name="credential_fingerprint",
        )
        self._operation = _required_text(
            operation,
            field_name="operation",
        )
        self._authority_state = JUDGE_NOT_GRANTED
        self._active_authority_id: str | None = None

    @property
    def authority_state(self) -> str:
        """Return the current isolated Judge/Test authority state."""

        return self._authority_state

    @property
    def active_authority_id(self) -> str | None:
        """Return the current isolated ACTIVE grant identifier, if any."""

        return self._active_authority_id

    def grant(self) -> str:
        """Create one fresh isolated ACTIVE grant.

        Granting is allowed only from NOT_GRANTED. REVOKED must be reset first.
        """

        if self._authority_state != JUDGE_NOT_GRANTED:
            raise JudgeAuthorityError(
                "Judge authority grant requires NOT_GRANTED state"
            )

        self._authority_state = JUDGE_ACTIVE
        self._active_authority_id = (
            f"judge-test-authority-{uuid4()}"
        )

        return self._authority_state

    def revoke(self) -> str:
        """Revoke the current isolated ACTIVE grant."""

        if self._authority_state != JUDGE_ACTIVE:
            raise JudgeAuthorityError(
                "Judge authority revocation requires ACTIVE state"
            )

        if self._active_authority_id is None:
            raise JudgeAuthorityError(
                "ACTIVE Judge authority has no authority identifier"
            )

        self._authority_state = JUDGE_REVOKED
        self._active_authority_id = None

        return self._authority_state

    def reset(self) -> str:
        """Return Judge/Test authority to its known initial state."""

        self._authority_state = JUDGE_NOT_GRANTED
        self._active_authority_id = None

        return self._authority_state

    def check(
        self,
        action: ActionRequest,
        *,
        identity: GuardianIdentityVerification,
        config: GuardianIdentityConfig,
    ) -> AuthorityDecisionResult:
        """Evaluate one action against current isolated Judge/Test authority.

        Identity remains independently verified through the normal Guardian
        identity boundary before this checker is invoked.
        """

        if not isinstance(action, ActionRequest):
            raise JudgeAuthorityError(
                "Judge authority check requires ActionRequest"
            )

        if not isinstance(
            identity,
            GuardianIdentityVerification,
        ):
            raise JudgeAuthorityError(
                "Judge authority check requires verified identity evidence"
            )

        if not isinstance(config, GuardianIdentityConfig):
            raise JudgeAuthorityError(
                "Judge authority check requires GuardianIdentityConfig"
            )

        if identity.status != GUARDIAN_VERIFIED:
            raise JudgeAuthorityError(
                "Guardian identity is not UCII_VERIFIED"
            )

        if identity.identity_id != config.identity_id:
            raise JudgeAuthorityError(
                "Verified identity does not match Guardian configuration"
            )

        if (
            identity.credential_fingerprint
            != config.credential_fingerprint
        ):
            raise JudgeAuthorityError(
                "Verified credential does not match Guardian configuration"
            )

        if config.identity_id != self._identity_id:
            raise JudgeAuthorityError(
                "Guardian configuration does not match Judge authority identity"
            )

        if (
            config.credential_fingerprint
            != self._credential_fingerprint
        ):
            raise JudgeAuthorityError(
                "Guardian configuration does not match Judge authority credential"
            )

        if action.guardian_identity != identity.identity_id:
            raise JudgeAuthorityError(
                "Action Guardian identity does not match verified identity"
            )

        if action.operation != self._operation:
            raise JudgeAuthorityError(
                "Action operation is outside Judge authority scope"
            )

        if self._authority_state == JUDGE_NOT_GRANTED:
            decision = AuthorityDecision.ESCALATION_REQUIRED
            authority_id = None

        elif self._authority_state == JUDGE_ACTIVE:
            if self._active_authority_id is None:
                raise JudgeAuthorityError(
                    "ACTIVE Judge authority has no authority identifier"
                )

            decision = AuthorityDecision.ALLOW
            authority_id = self._active_authority_id

        elif self._authority_state == JUDGE_REVOKED:
            decision = AuthorityDecision.DENY
            authority_id = None

        else:
            raise JudgeAuthorityError(
                "Judge authority entered unsupported state"
            )

        return AuthorityDecisionResult(
            decision=decision,
            authority_state=self._authority_state,
            authority_id=authority_id,
            identity_id=config.identity_id,
            credential_fingerprint=(
                config.credential_fingerprint
            ),
            operation=action.operation,
            request_id=action.request_id,
        )
