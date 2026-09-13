"""Human escalation and bounded one-off approval for UCII Guardian.

Escalation preserves human judgment when current delegated action authority is
insufficient. Human approval here is deliberately narrow: it applies to one
exact ActionRequest only and never mutates or broadens standing UCII authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Any

from ucii_guardian.action import ActionRequest
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)


class HumanDecision(str, Enum):
    """Human response to one Guardian escalation."""

    APPROVE_ONCE = "APPROVE_ONCE"
    DENY = "DENY"


class GuardianApprovalError(RuntimeError):
    """Raised when an escalation or human decision is invalid."""


@dataclass(frozen=True)
class EscalationRequest:
    """Human-review request bound to one exact proposed action."""

    guardian_identity: str
    requester: str
    operation: str
    target: str
    parameters: Mapping[str, Any]
    request_id: str
    authority_state: str
    reason: str


@dataclass(frozen=True)
class OneOffApproval:
    """Human approval fact for exactly one ActionRequest.

    This fact is not standing delegated authority and does not alter UCII.
    """

    guardian_identity: str
    requester: str
    operation: str
    target: str
    parameters: Mapping[str, Any]
    request_id: str
    decision: HumanDecision


@dataclass(frozen=True)
class HumanDecisionResult:
    """Result of human review without executing the action."""

    decision: HumanDecision
    request_id: str
    approval: OneOffApproval | None


def create_escalation_request(
    action: ActionRequest,
    *,
    authority: AuthorityDecisionResult,
    reason: str | None = None,
) -> EscalationRequest:
    """Create a human-review request only for ESCALATION_REQUIRED."""

    if not isinstance(
        authority,
        AuthorityDecisionResult,
    ):
        raise GuardianApprovalError(
            "Escalation requires Guardian authority evidence"
        )

    standard_authority_escalation = (
        authority.decision is AuthorityDecision.ESCALATION_REQUIRED
        and authority.authority_state == "NOT_GRANTED"
    )
    budget_exception = (
        authority.decision is AuthorityDecision.ALLOW
        and authority.authority_state == "ACTIVE"
        and isinstance(reason, str)
        and reason.startswith("BUDGET_RANGE_EXCEEDED:")
    )

    if not standard_authority_escalation and not budget_exception:
        raise GuardianApprovalError(
            "Escalation requires ESCALATION_REQUIRED / NOT_GRANTED "
            "authority or an established ACTIVE budget exception"
        )

    if authority.identity_id != action.guardian_identity:
        raise GuardianApprovalError(
            "Authority identity does not match action"
        )

    if authority.operation != action.operation:
        raise GuardianApprovalError(
            "Authority operation does not match action"
        )

    if authority.request_id != action.request_id:
        raise GuardianApprovalError(
            "Authority request ID does not match action"
        )

    return EscalationRequest(
        guardian_identity=action.guardian_identity,
        requester=action.requester,
        operation=action.operation,
        target=action.target,
        parameters=MappingProxyType(
            dict(action.parameters)
        ),
        request_id=action.request_id,
        authority_state=authority.authority_state,
        reason=(
            reason
            if reason is not None
            else (
                "Current delegated authority does not cover this "
                "specific action; human judgment is required."
            )
        ),
    )


def decide_escalation(
    escalation: EscalationRequest,
    *,
    decision: HumanDecision,
) -> HumanDecisionResult:
    """Record one human decision without performing execution."""

    if not isinstance(
        escalation,
        EscalationRequest,
    ):
        raise GuardianApprovalError(
            "Human decision requires a valid escalation request"
        )

    if not isinstance(
        decision,
        HumanDecision,
    ):
        raise GuardianApprovalError(
            "Human decision is invalid"
        )

    if decision is HumanDecision.DENY:
        return HumanDecisionResult(
            decision=decision,
            request_id=escalation.request_id,
            approval=None,
        )

    if decision is not HumanDecision.APPROVE_ONCE:
        raise GuardianApprovalError(
            "Unsupported human decision"
        )

    approval = OneOffApproval(
        guardian_identity=escalation.guardian_identity,
        requester=escalation.requester,
        operation=escalation.operation,
        target=escalation.target,
        parameters=MappingProxyType(
            dict(escalation.parameters)
        ),
        request_id=escalation.request_id,
        decision=HumanDecision.APPROVE_ONCE,
    )

    return HumanDecisionResult(
        decision=decision,
        request_id=escalation.request_id,
        approval=approval,
    )
