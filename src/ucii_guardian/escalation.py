"""Human escalation decision coordination for UCII Guardian.

This module composes existing authority, human-approval, and protected-
execution contracts. It does not establish UCII authority, mutate standing
authority, authenticate Guardian, or ask the model to make human decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    EscalationRequest,
    HumanDecision,
    HumanDecisionResult,
    create_escalation_request,
    decide_escalation,
)
from ucii_guardian.authority import AuthorityDecisionResult
from ucii_guardian.executor import (
    OfficeSupplyExecutionResult,
    execute_office_supply,
)


@dataclass(frozen=True)
class EscalationOutcome:
    """Completed human-review outcome for one exact proposed action."""

    escalation: EscalationRequest
    human_decision: HumanDecisionResult
    execution: OfficeSupplyExecutionResult | None


def resolve_escalation(
    action: ActionRequest,
    *,
    authority: AuthorityDecisionResult,
    human_decision: HumanDecision,
    receipt_directory: Path,
) -> EscalationOutcome:
    """Resolve one authority escalation through explicit human judgment.

    Only a pre-existing ESCALATION_REQUIRED / NOT_GRANTED authority result can
    enter this flow. DENY returns without execution. APPROVE_ONCE passes the
    exact one-off approval fact into the existing protected executor.

    This function never creates, modifies, broadens, or revokes standing UCII
    delegated authority.
    """

    escalation = create_escalation_request(
        action,
        authority=authority,
    )

    decision_result = decide_escalation(
        escalation,
        decision=human_decision,
    )

    if decision_result.decision is HumanDecision.DENY:
        return EscalationOutcome(
            escalation=escalation,
            human_decision=decision_result,
            execution=None,
        )

    approval = decision_result.approval

    if approval is None:
        raise RuntimeError(
            "APPROVE_ONCE did not produce one-off approval evidence"
        )

    execution = execute_office_supply(
        action,
        approval=approval,
        receipt_directory=receipt_directory,
    )

    return EscalationOutcome(
        escalation=escalation,
        human_decision=decision_result,
        execution=execution,
    )
