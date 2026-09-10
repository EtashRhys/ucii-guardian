"""Tests for Guardian human-escalation decision coordination."""

from __future__ import annotations

from pathlib import Path

import pytest

from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    GuardianApprovalError,
    HumanDecision,
)
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)
from ucii_guardian.escalation import resolve_escalation
from ucii_guardian.executor import (
    GuardianExecutionError,
    OFFICE_SUPPLY_OPERATION,
)


IDENTITY_ID = "guardian:test-identity"
FINGERPRINT = "guardian-test-fingerprint"


def make_action() -> ActionRequest:
    return ActionRequest(
        requester="human:test-owner",
        guardian_identity=IDENTITY_ID,
        operation=OFFICE_SUPPLY_OPERATION,
        target="office-supply:printer-cartridge",
        parameters={
            "quantity": 1,
            "max_price_usd": 80,
        },
    )


def make_authority(
    action: ActionRequest,
    *,
    decision: AuthorityDecision = (
        AuthorityDecision.ESCALATION_REQUIRED
    ),
    authority_state: str = "NOT_GRANTED",
) -> AuthorityDecisionResult:
    return AuthorityDecisionResult(
        decision=decision,
        authority_state=authority_state,
        identity_id=action.guardian_identity,
        credential_fingerprint=FINGERPRINT,
        operation=action.operation,
        request_id=action.request_id,
    )


def test_escalation_denial_returns_clear_request_without_execution(
    tmp_path: Path,
) -> None:
    action = make_action()

    result = resolve_escalation(
        action,
        authority=make_authority(action),
        human_decision=HumanDecision.DENY,
        receipt_directory=tmp_path,
    )

    assert result.escalation.guardian_identity == action.guardian_identity
    assert result.escalation.requester == action.requester
    assert result.escalation.operation == action.operation
    assert result.escalation.target == action.target
    assert dict(result.escalation.parameters) == dict(action.parameters)
    assert result.escalation.request_id == action.request_id
    assert result.escalation.authority_state == "NOT_GRANTED"
    assert result.escalation.reason

    assert result.human_decision.decision is HumanDecision.DENY
    assert result.human_decision.request_id == action.request_id
    assert result.human_decision.approval is None
    assert result.execution is None
    assert list(tmp_path.iterdir()) == []


def test_escalation_approve_once_executes_exact_action(
    tmp_path: Path,
) -> None:
    action = make_action()

    result = resolve_escalation(
        action,
        authority=make_authority(action),
        human_decision=HumanDecision.APPROVE_ONCE,
        receipt_directory=tmp_path,
    )

    assert (
        result.human_decision.decision
        is HumanDecision.APPROVE_ONCE
    )
    assert result.human_decision.approval is not None

    approval = result.human_decision.approval

    assert approval.guardian_identity == action.guardian_identity
    assert approval.requester == action.requester
    assert approval.operation == action.operation
    assert approval.target == action.target
    assert dict(approval.parameters) == dict(action.parameters)
    assert approval.request_id == action.request_id

    assert result.execution is not None
    assert result.execution.executed is True
    assert result.execution.guardian_identity == action.guardian_identity
    assert result.execution.operation == action.operation
    assert result.execution.target == action.target
    assert result.execution.request_id == action.request_id
    assert result.execution.receipt_path.exists()


@pytest.mark.parametrize(
    ("decision", "authority_state"),
    [
        (
            AuthorityDecision.ALLOW,
            "ACTIVE",
        ),
        (
            AuthorityDecision.DENY,
            "REVOKED",
        ),
        (
            AuthorityDecision.DENY,
            "EXPIRED",
        ),
        (
            AuthorityDecision.DENY,
            "INVALID",
        ),
    ],
)
def test_only_escalation_required_not_granted_can_enter_human_flow(
    tmp_path: Path,
    decision: AuthorityDecision,
    authority_state: str,
) -> None:
    action = make_action()

    with pytest.raises(GuardianApprovalError):
        resolve_escalation(
            action,
            authority=make_authority(
                action,
                decision=decision,
                authority_state=authority_state,
            ),
            human_decision=HumanDecision.APPROVE_ONCE,
            receipt_directory=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_approve_once_does_not_create_standing_authority(
    tmp_path: Path,
) -> None:
    action = make_action()

    result = resolve_escalation(
        action,
        authority=make_authority(action),
        human_decision=HumanDecision.APPROVE_ONCE,
        receipt_directory=tmp_path,
    )

    approval = result.human_decision.approval

    assert approval is not None
    assert not hasattr(approval, "authority_id")
    assert not hasattr(approval, "allowed_operations")
    assert not hasattr(approval, "granted_by")
    assert not hasattr(result, "standing_authority")


def test_approve_once_cannot_be_reused_for_second_execution(
    tmp_path: Path,
) -> None:
    action = make_action()
    authority = make_authority(action)

    first = resolve_escalation(
        action,
        authority=authority,
        human_decision=HumanDecision.APPROVE_ONCE,
        receipt_directory=tmp_path,
    )

    assert first.execution is not None
    assert first.execution.executed is True

    with pytest.raises(
        GuardianExecutionError,
        match="Protected action has already been executed",
    ):
        resolve_escalation(
            action,
            authority=authority,
            human_decision=HumanDecision.APPROVE_ONCE,
            receipt_directory=tmp_path,
        )

    assert len(list(tmp_path.iterdir())) == 1
