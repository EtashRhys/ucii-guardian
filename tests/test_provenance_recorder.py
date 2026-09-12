"""Tests for Guardian durable lifecycle provenance recording."""

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
    ProvenanceEventType,
)
from ucii_guardian.provenance_recorder import (
    GuardianProvenanceRecorder,
)


IDENTITY_ID = (
    "35c1db3d-61d7-4d0d-a5d7-db3ab7f79520"
)
FINGERPRINT = "9d14" + ("b" * 60)
OPERATION = "guardian.purchase.office_supply"


def make_action(
    request_id: str = "request-recorder-1",
) -> ActionRequest:
    return ActionRequest(
        requester="human:test",
        guardian_identity=IDENTITY_ID,
        operation=OPERATION,
        target="office-supply:printer-cartridge",
        parameters={
            "quantity": 1,
            "max_price_usd": 80,
        },
        request_id=request_id,
        requested_at=datetime(
            2026,
            9,
            10,
            22,
            0,
            tzinfo=timezone.utc,
        ),
    )


def make_identity() -> GuardianIdentityVerification:
    return GuardianIdentityVerification(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        status=GUARDIAN_VERIFIED,
    )


def make_authority(
    action: ActionRequest,
    *,
    decision: AuthorityDecision,
    state: str,
) -> AuthorityDecisionResult:
    return AuthorityDecisionResult(
        decision=decision,
        authority_state=state,
        authority_id=(
            "test-active-authority"
            if (
                decision is AuthorityDecision.ALLOW
                and state == "ACTIVE"
            )
            else None
        ),
        identity_id=action.guardian_identity,
        credential_fingerprint=FINGERPRINT,
        operation=action.operation,
        request_id=action.request_id,
    )


def make_execution(
    action: ActionRequest,
    tmp_path: Path,
) -> OfficeSupplyExecutionResult:
    return OfficeSupplyExecutionResult(
        executed=True,
        operation=action.operation,
        target=action.target,
        request_id=action.request_id,
        guardian_identity=action.guardian_identity,
        receipt_id=(
            f"guardian-office-supply-{action.request_id}"
        ),
        completed_at=datetime(
            2026,
            9,
            10,
            22,
            5,
            tzinfo=timezone.utc,
        ),
        receipt_path=(
            tmp_path
            / f"guardian-office-supply-{action.request_id}.json"
        ),
    )


def test_delegated_authority_lifecycle_is_reconstructable(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "guardian-provenance.jsonl"
    recorder = GuardianProvenanceRecorder(
        ledger
    )

    action = make_action()
    identity = make_identity()

    authority = make_authority(
        action,
        decision=AuthorityDecision.ALLOW,
        state="ACTIVE",
    )

    execution = make_execution(
        action,
        tmp_path,
    )

    recorder.record_request(
        action
    )

    recorder.record_identity(
        action,
        identity=identity,
    )

    recorder.record_authority(
        action,
        authority=authority,
    )

    recorder.record_execution_started(
        action,
        authority_path="DELEGATED_AUTHORITY",
    )

    recorder.record_execution_completed(
        action,
        execution=execution,
    )

    history = recorder.history_for_request(
        action.request_id
    )

    assert tuple(
        event.event_type
        for event in history
    ) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.AUTHORIZED,
        ProvenanceEventType.EXECUTION_STARTED,
        ProvenanceEventType.EXECUTION_COMPLETED,
    )

    assert ledger.exists()


def test_human_approval_lifecycle_is_reconstructable(
    tmp_path: Path,
) -> None:
    recorder = GuardianProvenanceRecorder(
        tmp_path / "guardian-provenance.jsonl"
    )

    action = make_action(
        "request-human-approval"
    )

    authority = make_authority(
        action,
        decision=AuthorityDecision.ESCALATION_REQUIRED,
        state="NOT_GRANTED",
    )

    escalation = create_escalation_request(
        action,
        authority=authority,
    )

    decision = decide_escalation(
        escalation,
        decision=HumanDecision.APPROVE_ONCE,
    )

    recorder.record_request(
        action
    )

    recorder.record_identity(
        action,
        identity=make_identity(),
    )

    recorder.record_authority(
        action,
        authority=authority,
    )

    recorder.record_human_decision(
        action,
        escalation=escalation,
        result=decision,
    )

    recorder.record_execution_started(
        action,
        authority_path="HUMAN_APPROVE_ONCE",
    )

    recorder.record_execution_completed(
        action,
        execution=make_execution(
            action,
            tmp_path,
        ),
    )

    history = recorder.history_for_request(
        action.request_id
    )

    assert tuple(
        event.event_type
        for event in history
    ) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.ESCALATED,
        ProvenanceEventType.HUMAN_APPROVED,
        ProvenanceEventType.EXECUTION_STARTED,
        ProvenanceEventType.EXECUTION_COMPLETED,
    )


def test_human_denial_lifecycle_ends_without_execution(
    tmp_path: Path,
) -> None:
    recorder = GuardianProvenanceRecorder(
        tmp_path / "guardian-provenance.jsonl"
    )

    action = make_action(
        "request-human-denial"
    )

    authority = make_authority(
        action,
        decision=AuthorityDecision.ESCALATION_REQUIRED,
        state="NOT_GRANTED",
    )

    escalation = create_escalation_request(
        action,
        authority=authority,
    )

    decision = decide_escalation(
        escalation,
        decision=HumanDecision.DENY,
    )

    recorder.record_request(
        action
    )

    recorder.record_authority(
        action,
        authority=authority,
    )

    recorder.record_human_decision(
        action,
        escalation=escalation,
        result=decision,
    )

    history = recorder.history_for_request(
        action.request_id
    )

    assert tuple(
        event.event_type
        for event in history
    ) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.ESCALATED,
        ProvenanceEventType.HUMAN_DENIED,
    )

    assert ProvenanceEventType.EXECUTION_STARTED not in {
        event.event_type
        for event in history
    }

    assert ProvenanceEventType.EXECUTION_COMPLETED not in {
        event.event_type
        for event in history
    }


def test_revoked_authority_lifecycle_records_refusal(
    tmp_path: Path,
) -> None:
    recorder = GuardianProvenanceRecorder(
        tmp_path / "guardian-provenance.jsonl"
    )

    action = make_action(
        "request-revoked"
    )

    authority = make_authority(
        action,
        decision=AuthorityDecision.DENY,
        state="REVOKED",
    )

    recorder.record_request(
        action
    )

    recorder.record_identity(
        action,
        identity=make_identity(),
    )

    recorder.record_authority(
        action,
        authority=authority,
    )

    history = recorder.history_for_request(
        action.request_id
    )

    assert tuple(
        event.event_type
        for event in history
    ) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.AUTHORITY_REVOKED,
        ProvenanceEventType.EXECUTION_REFUSED,
    )


def test_request_histories_remain_separate(
    tmp_path: Path,
) -> None:
    recorder = GuardianProvenanceRecorder(
        tmp_path / "guardian-provenance.jsonl"
    )

    first = make_action(
        "request-first"
    )

    second = make_action(
        "request-second"
    )

    recorder.record_request(
        first
    )

    recorder.record_request(
        second
    )

    assert tuple(
        event.request_id
        for event in recorder.history_for_request(
            "request-first"
        )
    ) == (
        "request-first",
    )

    assert tuple(
        event.request_id
        for event in recorder.history_for_request(
            "request-second"
        )
    ) == (
        "request-second",
    )


def test_reconstruction_preserves_explanatory_reasons(
    tmp_path: Path,
) -> None:
    recorder = GuardianProvenanceRecorder(
        tmp_path / "guardian-provenance.jsonl"
    )

    action = make_action()

    authority = make_authority(
        action,
        decision=AuthorityDecision.ALLOW,
        state="ACTIVE",
    )

    recorder.record_request(
        action
    )

    recorder.record_authority(
        action,
        authority=authority,
    )

    history = recorder.history_for_request(
        action.request_id
    )

    assert all(
        event.reason.strip()
        for event in history
    )

    authorized = next(
        event
        for event in history
        if event.event_type
        is ProvenanceEventType.AUTHORIZED
    )

    assert authorized.details["authority_state"] == "ACTIVE"
    assert authorized.details["decision"] == "ALLOW"


def test_recorder_does_not_expose_authority_or_execution_calls() -> None:
    source = Path(
        __import__(
            "ucii_guardian.provenance_recorder",
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


def test_empty_request_id_is_rejected(
    tmp_path: Path,
) -> None:
    recorder = GuardianProvenanceRecorder(
        tmp_path / "guardian-provenance.jsonl"
    )

    with pytest.raises(
        ValueError,
        match="request_id",
    ):
        recorder.history_for_request(
            " "
        )
