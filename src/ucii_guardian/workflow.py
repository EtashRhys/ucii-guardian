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

    if human_decision is None:
        return GuardianWorkflowOutcome(
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

    decision_result = decide_escalation(
        escalation,
        decision=human_decision,
    )

    recorder.record_human_decision(
        action,
        escalation=escalation,
        result=decision_result,
    )

    if decision_result.decision is HumanDecision.DENY:
        return GuardianWorkflowOutcome(
            action=action,
            identity=identity,
            authority=authority,
            escalation=escalation,
            human_decision=decision_result,
            execution=None,
            provenance=recorder.history_for_request(
                action.request_id
            ),
        )

    approval = decision_result.approval

    if approval is None:
        raise RuntimeError(
            "APPROVE_ONCE did not produce approval evidence"
        )

    recorder.record_execution_started(
        action,
        authority_path="HUMAN_APPROVE_ONCE",
    )

    execution = execute_office_supply(
        action,
        approval=approval,
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
        escalation=escalation,
        human_decision=decision_result,
        execution=execution,
        provenance=recorder.history_for_request(
            action.request_id
        ),
    )
