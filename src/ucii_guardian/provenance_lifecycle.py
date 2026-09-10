"""Lifecycle fact projection into Guardian provenance events.

This module is deliberately observational. It translates already-established
Guardian facts into provenance events. It does not authenticate Guardian,
check or mutate UCII authority, obtain human decisions, invoke Strands, or
execute consequential actions.
"""

from __future__ import annotations

from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    EscalationRequest,
    HumanDecision,
    HumanDecisionResult,
)
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)
from ucii_guardian.executor import (
    OfficeSupplyExecutionResult,
)
from ucii_guardian.identity import (
    GUARDIAN_VERIFIED,
    GuardianIdentityVerification,
)
from ucii_guardian.provenance import (
    ProvenanceError,
    ProvenanceEvent,
    ProvenanceEventType,
)


def request_received_event(
    action: ActionRequest,
) -> ProvenanceEvent:
    """Record that Guardian received one normalized proposed action."""

    if not isinstance(action, ActionRequest):
        raise ProvenanceError(
            "REQUEST_RECEIVED requires ActionRequest"
        )

    return ProvenanceEvent(
        event_type=ProvenanceEventType.REQUEST_RECEIVED,
        request_id=action.request_id,
        guardian_identity=action.guardian_identity,
        operation=action.operation,
        reason=(
            "Guardian received a normalized bounded action request."
        ),
        details={
            "requester": action.requester,
            "target": action.target,
            "parameters": dict(action.parameters),
            "requested_at": action.requested_at.isoformat(),
        },
    )


def identity_verified_event(
    action: ActionRequest,
    *,
    identity: GuardianIdentityVerification,
) -> ProvenanceEvent:
    """Record independently established UCII identity verification."""

    if not isinstance(
        identity,
        GuardianIdentityVerification,
    ):
        raise ProvenanceError(
            "IDENTITY_VERIFIED requires Guardian identity evidence"
        )

    if identity.status != GUARDIAN_VERIFIED:
        raise ProvenanceError(
            "IDENTITY_VERIFIED requires UCII_VERIFIED"
        )

    if identity.identity_id != action.guardian_identity:
        raise ProvenanceError(
            "Verified identity does not match action"
        )

    return ProvenanceEvent(
        event_type=ProvenanceEventType.IDENTITY_VERIFIED,
        request_id=action.request_id,
        guardian_identity=identity.identity_id,
        operation=action.operation,
        reason=(
            "Guardian identity and active credential were verified "
            "through the UCII boundary."
        ),
        details={
            "verification_status": identity.status,
            "credential_fingerprint": (
                identity.credential_fingerprint
            ),
        },
    )


def authority_events(
    action: ActionRequest,
    *,
    authority: AuthorityDecisionResult,
) -> tuple[ProvenanceEvent, ...]:
    """Project one established authority result into explanatory events."""

    if not isinstance(
        authority,
        AuthorityDecisionResult,
    ):
        raise ProvenanceError(
            "AUTHORITY_CHECKED requires Guardian authority evidence"
        )

    if authority.identity_id != action.guardian_identity:
        raise ProvenanceError(
            "Authority identity does not match action"
        )

    if authority.operation != action.operation:
        raise ProvenanceError(
            "Authority operation does not match action"
        )

    if authority.request_id != action.request_id:
        raise ProvenanceError(
            "Authority request ID does not match action"
        )

    checked = ProvenanceEvent(
        event_type=ProvenanceEventType.AUTHORITY_CHECKED,
        request_id=action.request_id,
        guardian_identity=action.guardian_identity,
        operation=action.operation,
        reason=(
            "Guardian evaluated current delegated authority "
            "for the exact proposed operation."
        ),
        details={
            "authority_state": authority.authority_state,
            "decision": authority.decision.value,
        },
    )

    if authority.decision is AuthorityDecision.ALLOW:
        if authority.authority_state != "ACTIVE":
            raise ProvenanceError(
                "ALLOW provenance requires ACTIVE authority"
            )

        outcome = ProvenanceEvent(
            event_type=ProvenanceEventType.AUTHORIZED,
            request_id=action.request_id,
            guardian_identity=action.guardian_identity,
            operation=action.operation,
            reason=(
                "Current UCII delegated authority was ACTIVE "
                "for the proposed operation."
            ),
            details={
                "authority_state": authority.authority_state,
                "decision": authority.decision.value,
            },
        )

        return checked, outcome

    if (
        authority.decision
        is AuthorityDecision.ESCALATION_REQUIRED
    ):
        if authority.authority_state != "NOT_GRANTED":
            raise ProvenanceError(
                "ESCALATION_REQUIRED provenance requires NOT_GRANTED"
            )

        outcome = ProvenanceEvent(
            event_type=ProvenanceEventType.ESCALATED,
            request_id=action.request_id,
            guardian_identity=action.guardian_identity,
            operation=action.operation,
            reason=(
                "Current delegated authority did not cover "
                "the proposed action; human judgment was required."
            ),
            details={
                "authority_state": authority.authority_state,
                "decision": authority.decision.value,
            },
        )

        return checked, outcome

    if authority.decision is AuthorityDecision.DENY:
        events = [checked]

        if authority.authority_state == "REVOKED":
            events.append(
                ProvenanceEvent(
                    event_type=(
                        ProvenanceEventType.AUTHORITY_REVOKED
                    ),
                    request_id=action.request_id,
                    guardian_identity=action.guardian_identity,
                    operation=action.operation,
                    reason=(
                        "UCII reported the delegated authority "
                        "for this operation as REVOKED."
                    ),
                    details={
                        "authority_state": "REVOKED",
                    },
                )
            )

        events.append(
            ProvenanceEvent(
                event_type=ProvenanceEventType.EXECUTION_REFUSED,
                request_id=action.request_id,
                guardian_identity=action.guardian_identity,
                operation=action.operation,
                reason=(
                    "Guardian denied consequential execution "
                    "because current authority was not usable."
                ),
                details={
                    "authority_state": authority.authority_state,
                    "decision": authority.decision.value,
                },
            )
        )

        return tuple(events)

    raise ProvenanceError(
        "Unsupported Guardian authority decision"
    )


def human_decision_event(
    action: ActionRequest,
    *,
    escalation: EscalationRequest,
    result: HumanDecisionResult,
) -> ProvenanceEvent:
    """Record one already-made human decision without granting authority."""

    if not isinstance(
        escalation,
        EscalationRequest,
    ):
        raise ProvenanceError(
            "Human provenance requires EscalationRequest"
        )

    if not isinstance(
        result,
        HumanDecisionResult,
    ):
        raise ProvenanceError(
            "Human provenance requires HumanDecisionResult"
        )

    if escalation.request_id != action.request_id:
        raise ProvenanceError(
            "Escalation request ID does not match action"
        )

    if result.request_id != action.request_id:
        raise ProvenanceError(
            "Human decision request ID does not match action"
        )

    if (
        escalation.guardian_identity
        != action.guardian_identity
    ):
        raise ProvenanceError(
            "Escalation identity does not match action"
        )

    if result.decision is HumanDecision.APPROVE_ONCE:
        event_type = ProvenanceEventType.HUMAN_APPROVED
        reason = (
            "Human explicitly approved this exact exceptional "
            "action once."
        )

    elif result.decision is HumanDecision.DENY:
        event_type = ProvenanceEventType.HUMAN_DENIED
        reason = (
            "Human explicitly denied the escalated action."
        )

    else:
        raise ProvenanceError(
            "Unsupported human decision"
        )

    return ProvenanceEvent(
        event_type=event_type,
        request_id=action.request_id,
        guardian_identity=action.guardian_identity,
        operation=action.operation,
        reason=reason,
        details={
            "human_decision": result.decision.value,
            "target": action.target,
        },
    )


def execution_started_event(
    action: ActionRequest,
    *,
    authority_path: str,
) -> ProvenanceEvent:
    """Record that protected execution is beginning after its gate passed."""

    if authority_path not in {
        "DELEGATED_AUTHORITY",
        "HUMAN_APPROVE_ONCE",
    }:
        raise ProvenanceError(
            "execution authority path is invalid"
        )

    return ProvenanceEvent(
        event_type=ProvenanceEventType.EXECUTION_STARTED,
        request_id=action.request_id,
        guardian_identity=action.guardian_identity,
        operation=action.operation,
        reason=(
            "Protected execution began after the applicable "
            "authority gate passed."
        ),
        details={
            "authority_path": authority_path,
            "target": action.target,
        },
    )


def execution_completed_event(
    action: ActionRequest,
    *,
    execution: OfficeSupplyExecutionResult,
) -> ProvenanceEvent:
    """Record an already-completed protected execution result."""

    if not isinstance(
        execution,
        OfficeSupplyExecutionResult,
    ):
        raise ProvenanceError(
            "EXECUTION_COMPLETED requires execution result"
        )

    if execution.executed is not True:
        raise ProvenanceError(
            "EXECUTION_COMPLETED requires executed result"
        )

    if execution.request_id != action.request_id:
        raise ProvenanceError(
            "Execution request ID does not match action"
        )

    if execution.guardian_identity != action.guardian_identity:
        raise ProvenanceError(
            "Execution identity does not match action"
        )

    if execution.operation != action.operation:
        raise ProvenanceError(
            "Execution operation does not match action"
        )

    if execution.target != action.target:
        raise ProvenanceError(
            "Execution target does not match action"
        )

    return ProvenanceEvent(
        event_type=ProvenanceEventType.EXECUTION_COMPLETED,
        request_id=action.request_id,
        guardian_identity=action.guardian_identity,
        operation=action.operation,
        reason=(
            "Protected consequential execution completed."
        ),
        details={
            "target": action.target,
            "receipt_id": execution.receipt_id,
            "completed_at": execution.completed_at.isoformat(),
        },
    )
