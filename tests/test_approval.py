from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    EscalationRequest,
    GuardianApprovalError,
    HumanDecision,
    OneOffApproval,
    create_escalation_request,
    decide_escalation,
)
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)


IDENTITY = "guardian:test-identity"
FINGERPRINT = "a" * 64
OPERATION = "guardian.purchase.office_supply"


def _action() -> ActionRequest:
    return ActionRequest(
        requester="human:test-owner",
        guardian_identity=IDENTITY,
        operation=OPERATION,
        target="office-supply:printer-cartridge",
        parameters={
            "quantity": 1,
            "max_price_usd": 80,
        },
        request_id=str(uuid4()),
        requested_at=datetime.now(timezone.utc),
    )


def _authority(
    action: ActionRequest,
    *,
    decision: AuthorityDecision = (
        AuthorityDecision.ESCALATION_REQUIRED
    ),
    authority_state: str = "NOT_GRANTED",
    identity_id: str | None = None,
    operation: str | None = None,
    request_id: str | None = None,
) -> AuthorityDecisionResult:
    return AuthorityDecisionResult(
        decision=decision,
        authority_state=authority_state,
        authority_id=(
            "test-active-authority"
            if (
                decision is AuthorityDecision.ALLOW
                and authority_state == "ACTIVE"
            )
            else None
        ),
        identity_id=identity_id or action.guardian_identity,
        credential_fingerprint=FINGERPRINT,
        operation=operation or action.operation,
        request_id=request_id or action.request_id,
    )


def test_create_escalation_request_binds_exact_action() -> None:
    action = _action()

    escalation = create_escalation_request(
        action,
        authority=_authority(action),
    )

    assert isinstance(
        escalation,
        EscalationRequest,
    )

    assert escalation.guardian_identity == action.guardian_identity
    assert escalation.requester == action.requester
    assert escalation.operation == action.operation
    assert escalation.target == action.target
    assert dict(escalation.parameters) == dict(action.parameters)
    assert escalation.request_id == action.request_id
    assert escalation.authority_state == "NOT_GRANTED"
    assert "human judgment" in escalation.reason


@pytest.mark.parametrize(
    ("decision", "authority_state"),
    [
        (AuthorityDecision.ALLOW, "ACTIVE"),
        (AuthorityDecision.DENY, "REVOKED"),
        (AuthorityDecision.DENY, "EXPIRED"),
        (AuthorityDecision.DENY, "INVALID"),
    ],
)
def test_escalation_rejects_non_escalation_authority(
    decision: AuthorityDecision,
    authority_state: str,
) -> None:
    action = _action()

    with pytest.raises(
        GuardianApprovalError,
        match="ESCALATION_REQUIRED",
    ):
        create_escalation_request(
            action,
            authority=_authority(
                action,
                decision=decision,
                authority_state=authority_state,
            ),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("identity_id", "guardian:other"),
        ("operation", "guardian.other"),
        ("request_id", "other-request"),
    ],
)
def test_escalation_rejects_mismatched_authority(
    field: str,
    value: str,
) -> None:
    action = _action()

    kwargs = {field: value}

    with pytest.raises(
        GuardianApprovalError,
    ):
        create_escalation_request(
            action,
            authority=_authority(
                action,
                **kwargs,
            ),
        )


def test_human_deny_creates_no_approval() -> None:
    action = _action()

    escalation = create_escalation_request(
        action,
        authority=_authority(action),
    )

    result = decide_escalation(
        escalation,
        decision=HumanDecision.DENY,
    )

    assert result.decision is HumanDecision.DENY
    assert result.request_id == action.request_id
    assert result.approval is None


def test_human_approve_once_creates_exact_one_off_approval() -> None:
    action = _action()

    escalation = create_escalation_request(
        action,
        authority=_authority(action),
    )

    result = decide_escalation(
        escalation,
        decision=HumanDecision.APPROVE_ONCE,
    )

    assert result.decision is HumanDecision.APPROVE_ONCE
    assert result.request_id == action.request_id

    approval = result.approval

    assert isinstance(
        approval,
        OneOffApproval,
    )

    assert approval.decision is HumanDecision.APPROVE_ONCE
    assert approval.guardian_identity == action.guardian_identity
    assert approval.requester == action.requester
    assert approval.operation == action.operation
    assert approval.target == action.target
    assert dict(approval.parameters) == dict(action.parameters)
    assert approval.request_id == action.request_id


def test_one_off_approval_parameters_are_immutable() -> None:
    action = _action()

    escalation = create_escalation_request(
        action,
        authority=_authority(action),
    )

    result = decide_escalation(
        escalation,
        decision=HumanDecision.APPROVE_ONCE,
    )

    assert result.approval is not None

    with pytest.raises(TypeError):
        result.approval.parameters["quantity"] = 2


def test_approval_does_not_create_standing_authority_fields() -> None:
    action = _action()

    escalation = create_escalation_request(
        action,
        authority=_authority(action),
    )

    result = decide_escalation(
        escalation,
        decision=HumanDecision.APPROVE_ONCE,
    )

    assert result.approval is not None

    assert not hasattr(
        result.approval,
        "allowed_operations",
    )
    assert not hasattr(
        result.approval,
        "authority_id",
    )
    assert not hasattr(
        result.approval,
        "expires_at",
    )
    assert not hasattr(
        result.approval,
        "granted_by",
    )


def test_human_decision_does_not_execute() -> None:
    action = _action()

    escalation = create_escalation_request(
        action,
        authority=_authority(action),
    )

    result = decide_escalation(
        escalation,
        decision=HumanDecision.APPROVE_ONCE,
    )

    assert result.approval is not None

    assert not hasattr(
        result,
        "executed",
    )
    assert not hasattr(
        result.approval,
        "executed",
    )
