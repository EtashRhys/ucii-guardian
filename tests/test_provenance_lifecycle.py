"""Tests for Guardian lifecycle-to-provenance projection."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    HumanDecision,
    create_escalation_request,
    decide_escalation,
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
    ProvenanceEventType,
)
from ucii_guardian.provenance_lifecycle import (
    authority_events,
    execution_completed_event,
    execution_started_event,
    human_decision_event,
    identity_verified_event,
    request_received_event,
)


IDENTITY_ID = (
    "35c1db3d-61d7-4d0d-a5d7-db3ab7f79520"
)
FINGERPRINT = "9d14" + ("a" * 60)
OPERATION = "guardian.purchase.office_supply"


@pytest.fixture
def action() -> ActionRequest:
    return ActionRequest(
        requester="human:test",
        guardian_identity=IDENTITY_ID,
        operation=OPERATION,
        target="office-supply:printer-cartridge",
        parameters={
            "quantity": 1,
            "max_price_usd": 80,
        },
        request_id="request-provenance-flow",
        requested_at=datetime(
            2026,
            9,
            10,
            21,
            30,
            tzinfo=timezone.utc,
        ),
    )


@pytest.fixture
def identity() -> GuardianIdentityVerification:
    return GuardianIdentityVerification(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        status=GUARDIAN_VERIFIED,
    )


def authority_for(
    action: ActionRequest,
    *,
    decision: AuthorityDecision,
    state: str,
) -> AuthorityDecisionResult:
    return AuthorityDecisionResult(
        decision=decision,
        authority_state=state,
        identity_id=action.guardian_identity,
        credential_fingerprint=FINGERPRINT,
        operation=action.operation,
        request_id=action.request_id,
    )


def test_request_received_projects_action_without_authority(
    action,
) -> None:
    event = request_received_event(action)

    assert event.event_type is ProvenanceEventType.REQUEST_RECEIVED
    assert event.request_id == action.request_id
    assert event.details["target"] == action.target
    assert "authorized" not in event.details


def test_identity_verified_projects_verified_fact(
    action,
    identity,
) -> None:
    event = identity_verified_event(
        action,
        identity=identity,
    )

    assert event.event_type is ProvenanceEventType.IDENTITY_VERIFIED
    assert event.details["verification_status"] == "UCII_VERIFIED"


def test_identity_projection_rejects_non_verified_fact(
    action,
) -> None:
    identity = GuardianIdentityVerification(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        status="NOT_VERIFIED",
    )

    with pytest.raises(
        ProvenanceError,
        match="UCII_VERIFIED",
    ):
        identity_verified_event(
            action,
            identity=identity,
        )


def test_active_allow_projects_checked_then_authorized(
    action,
) -> None:
    events = authority_events(
        action,
        authority=authority_for(
            action,
            decision=AuthorityDecision.ALLOW,
            state="ACTIVE",
        ),
    )

    assert tuple(
        event.event_type
        for event in events
    ) == (
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.AUTHORIZED,
    )


def test_not_granted_projects_checked_then_escalated(
    action,
) -> None:
    events = authority_events(
        action,
        authority=authority_for(
            action,
            decision=AuthorityDecision.ESCALATION_REQUIRED,
            state="NOT_GRANTED",
        ),
    )

    assert tuple(
        event.event_type
        for event in events
    ) == (
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.ESCALATED,
    )


def test_revoked_deny_projects_revocation_and_refusal(
    action,
) -> None:
    events = authority_events(
        action,
        authority=authority_for(
            action,
            decision=AuthorityDecision.DENY,
            state="REVOKED",
        ),
    )

    assert tuple(
        event.event_type
        for event in events
    ) == (
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.AUTHORITY_REVOKED,
        ProvenanceEventType.EXECUTION_REFUSED,
    )


@pytest.mark.parametrize(
    "state",
    [
        "EXPIRED",
        "INVALID",
    ],
)
def test_other_denials_project_checked_and_refused(
    action,
    state,
) -> None:
    events = authority_events(
        action,
        authority=authority_for(
            action,
            decision=AuthorityDecision.DENY,
            state=state,
        ),
    )

    assert tuple(
        event.event_type
        for event in events
    ) == (
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.EXECUTION_REFUSED,
    )


def test_inconsistent_allow_fails_closed(
    action,
) -> None:
    with pytest.raises(
        ProvenanceError,
        match="ACTIVE",
    ):
        authority_events(
            action,
            authority=authority_for(
                action,
                decision=AuthorityDecision.ALLOW,
                state="REVOKED",
            ),
        )


@pytest.mark.parametrize(
    ("decision", "expected_type"),
    [
        (
            HumanDecision.APPROVE_ONCE,
            ProvenanceEventType.HUMAN_APPROVED,
        ),
        (
            HumanDecision.DENY,
            ProvenanceEventType.HUMAN_DENIED,
        ),
    ],
)
def test_human_decision_projects_existing_human_fact(
    action,
    decision,
    expected_type,
) -> None:
    authority = authority_for(
        action,
        decision=AuthorityDecision.ESCALATION_REQUIRED,
        state="NOT_GRANTED",
    )

    escalation = create_escalation_request(
        action,
        authority=authority,
    )

    result = decide_escalation(
        escalation,
        decision=decision,
    )

    event = human_decision_event(
        action,
        escalation=escalation,
        result=result,
    )

    assert event.event_type is expected_type
    assert event.details["human_decision"] == decision.value


@pytest.mark.parametrize(
    "authority_path",
    [
        "DELEGATED_AUTHORITY",
        "HUMAN_APPROVE_ONCE",
    ],
)
def test_execution_started_records_existing_gate_path(
    action,
    authority_path,
) -> None:
    event = execution_started_event(
        action,
        authority_path=authority_path,
    )

    assert event.event_type is ProvenanceEventType.EXECUTION_STARTED
    assert event.details["authority_path"] == authority_path


def test_execution_started_rejects_unknown_authority_path(
    action,
) -> None:
    with pytest.raises(
        ProvenanceError,
        match="authority path",
    ):
        execution_started_event(
            action,
            authority_path="MODEL_DECISION",
        )


def test_execution_completed_projects_receipt_fact(
    action,
    tmp_path: Path,
) -> None:
    completed = datetime(
        2026,
        9,
        10,
        21,
        45,
        tzinfo=timezone.utc,
    )

    execution = OfficeSupplyExecutionResult(
        executed=True,
        operation=action.operation,
        target=action.target,
        request_id=action.request_id,
        guardian_identity=action.guardian_identity,
        receipt_id="guardian-office-supply-test",
        completed_at=completed,
        receipt_path=(
            tmp_path / "guardian-office-supply-test.json"
        ),
    )

    event = execution_completed_event(
        action,
        execution=execution,
    )

    assert event.event_type is ProvenanceEventType.EXECUTION_COMPLETED
    assert event.details["receipt_id"] == execution.receipt_id
    assert "receipt_path" not in event.details


def test_projection_module_exposes_no_authority_or_execution_calls() -> None:
    source = Path(
        __import__(
            "ucii_guardian.provenance_lifecycle",
            fromlist=[""],
        ).__file__
    ).read_text(
        encoding="utf-8"
    )

    forbidden = (
        "UCIIClient",
        "check_authority(",
        "verify_guardian_identity(",
        "execute_office_supply(",
        "resolve_escalation(",
        "decide_escalation(",
        "Agent(",
        "pq_auth",
    )

    for marker in forbidden:
        assert marker not in source
