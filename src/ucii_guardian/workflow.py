"""Provenance-aware runtime workflow for UCII Guardian.

This is Guardian's narrow runtime composition boundary:

Strands interprets human intent into an ActionRequest.
UCII independently verifies Guardian identity.
UCII independently evaluates current delegated authority.
The protected executor acts only after an established authority path.
Human judgment may authorize one exact escalated action.

Provenance observes and records those established facts. It never creates,
modifies, broadens, revokes, or substitutes for authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ucii_guardian.action import ActionRequest
from ucii_guardian.agent import propose_action
from ucii_guardian.approval import (
    EscalationRequest,
    HumanDecision,
    HumanDecisionResult,
    create_escalation_request,
    decide_escalation,
)
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
    check_authority,
)
from ucii_guardian.executor import (
    OfficeSupplyExecutionResult,
    execute_office_supply,
)
from ucii_guardian.identity import (
    GuardianIdentityConfig,
    GuardianIdentityVerification,
    verify_guardian_identity,
)
from ucii_guardian.provenance import (
    ProvenanceEvent,
)
from ucii_guardian.provenance_recorder import (
    GuardianProvenanceRecorder,
)


@dataclass(frozen=True)
class GuardianWorkflowOutcome:
    """Completed or safely stopped result for one Guardian request."""

    action: ActionRequest
    identity: GuardianIdentityVerification
    authority: AuthorityDecisionResult
    escalation: EscalationRequest | None
    human_decision: HumanDecisionResult | None
    execution: OfficeSupplyExecutionResult | None
    provenance: tuple[ProvenanceEvent, ...]



def continue_guardian_escalation(
    *,
    outcome: GuardianWorkflowOutcome,
    decision: HumanDecision,
    recorder: GuardianProvenanceRecorder,
    receipt_directory: Path,
) -> GuardianWorkflowOutcome:
    """Continue one exact previously-established pending escalation.

    This boundary never invokes Strands, reinterprets human intent, creates a
    new ActionRequest, or mutates standing UCII authority.
    """

    if not isinstance(
        recorder,
        GuardianProvenanceRecorder,
    ):
        raise TypeError(
            "recorder must be GuardianProvenanceRecorder"
        )

    if not isinstance(
        outcome,
        GuardianWorkflowOutcome,
    ):
        raise TypeError(
            "outcome must be GuardianWorkflowOutcome"
        )

    if outcome.escalation is None:
        raise ValueError(
            "Guardian continuation requires a pending escalation"
        )

    if outcome.human_decision is not None:
        raise ValueError(
            "Guardian escalation already has a human decision"
        )

    if outcome.execution is not None:
        raise ValueError(
            "Guardian escalation has already executed"
        )

    if (
        outcome.authority.decision
        is not AuthorityDecision.ESCALATION_REQUIRED
    ):
        raise ValueError(
            "Guardian continuation requires ESCALATION_REQUIRED"
        )

    if outcome.authority.authority_state != "NOT_GRANTED":
        raise ValueError(
            "Guardian continuation requires NOT_GRANTED authority"
        )

    if outcome.escalation.request_id != outcome.action.request_id:
        raise ValueError(
            "Escalation request ID does not match action"
        )

    existing_history = recorder.history_for_request(
        outcome.action.request_id
    )

    if existing_history != outcome.provenance:
        raise ValueError(
            "Pending escalation provenance does not match recorder"
        )

    decision_result = decide_escalation(
        outcome.escalation,
        decision=decision,
    )

    recorder.record_human_decision(
        outcome.action,
        escalation=outcome.escalation,
        result=decision_result,
    )

    if decision_result.decision is HumanDecision.DENY:
        return GuardianWorkflowOutcome(
            action=outcome.action,
            identity=outcome.identity,
            authority=outcome.authority,
            escalation=outcome.escalation,
            human_decision=decision_result,
            execution=None,
            provenance=recorder.history_for_request(
                outcome.action.request_id
            ),
        )

    approval = decision_result.approval

    if approval is None:
        raise RuntimeError(
            "APPROVE_ONCE did not produce approval evidence"
        )

    recorder.record_execution_started(
        outcome.action,
        authority_path="HUMAN_APPROVE_ONCE",
    )

    execution = execute_office_supply(
        outcome.action,
        approval=approval,
        receipt_directory=receipt_directory,
    )

    recorder.record_execution_completed(
        outcome.action,
        execution=execution,
    )

    return GuardianWorkflowOutcome(
        action=outcome.action,
        identity=outcome.identity,
        authority=outcome.authority,
        escalation=outcome.escalation,
        human_decision=decision_result,
        execution=execution,
        provenance=recorder.history_for_request(
            outcome.action.request_id
        ),
    )

def run_guardian_request(
    *,
    agent: Any,
    request: str,
    config: GuardianIdentityConfig,
    recorder: GuardianProvenanceRecorder,
    receipt_directory: Path,
    human_decision: HumanDecision | None = None,
) -> GuardianWorkflowOutcome:
    """Run one bounded Guardian request through fresh security boundaries.

    The model only produces ActionRequest intent.

    Identity and delegated authority are independently established outside
    model output. Every request performs a fresh UCII identity verification
    and a fresh delegated-authority check.

    ALLOW may execute only through current ACTIVE delegated authority.

    ESCALATION_REQUIRED may stop for human review, be denied, or execute once
    through an exact APPROVE_ONCE fact.

    DENY never enters the executor.

    This workflow cannot create or mutate standing delegated authority.
    """

    if not isinstance(
        recorder,
        GuardianProvenanceRecorder,
    ):
        raise TypeError(
            "recorder must be GuardianProvenanceRecorder"
        )

    action = propose_action(
        agent,
        request,
    )

    recorder.record_request(
        action
    )

    identity = verify_guardian_identity(
        config
    )

    recorder.record_identity(
        action,
        identity=identity,
    )

    authority = check_authority(
        action,
        identity=identity,
        config=config,
    )

    recorder.record_authority(
        action,
        authority=authority,
    )

    if authority.decision is AuthorityDecision.DENY:
        if human_decision is not None:
            raise ValueError(
                "Human approval cannot override DENY"
            )

        return GuardianWorkflowOutcome(
            action=action,
            identity=identity,
            authority=authority,
            escalation=None,
            human_decision=None,
            execution=None,
            provenance=recorder.history_for_request(
                action.request_id
            ),
        )

    if authority.decision is AuthorityDecision.ALLOW:
        if human_decision is not None:
            raise ValueError(
                "Human decision is not applicable to ALLOW"
            )

        recorder.record_execution_started(
            action,
            authority_path="DELEGATED_AUTHORITY",
        )

        execution = execute_office_supply(
            action,
            authority=authority,
            receipt_directory=receipt_directory,
        )

        recorder.record_execution_completed(
            action,
            execution=execution,
        )

        return GuardianWorkflowOutcome(
            action=action,
            identity=identity,
            authority=authority,
            escalation=None,
            human_decision=None,
            execution=execution,
            provenance=recorder.history_for_request(
                action.request_id
            ),
        )

    if (
        authority.decision
        is not AuthorityDecision.ESCALATION_REQUIRED
    ):
        raise RuntimeError(
            "Guardian received unsupported authority decision"
        )

    escalation = create_escalation_request(
        action,
        authority=authority,
    )

    pending = GuardianWorkflowOutcome(
        action=action,
        identity=identity,
        authority=authority,
        escalation=escalation,
        human_decision=None,
        execution=None,
        provenance=recorder.history_for_request(
            action.request_id
        ),
    )

    if human_decision is None:
        return pending

    return continue_guardian_escalation(
        outcome=pending,
        decision=human_decision,
        recorder=recorder,
        receipt_directory=receipt_directory,
    )
