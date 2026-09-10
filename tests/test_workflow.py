"""Tests for Guardian provenance-aware runtime workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import ucii_guardian.workflow as workflow
from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    HumanDecision,
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
    GuardianIdentityConfig,
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

CREDENTIAL_ID = (
    "9e2ee693-ca6d-426a-80ae-cf226e69c1e6"
)

FINGERPRINT = (
    "9d14f6f5a53629709afb1574ef9d14be"
    "ad52d6da5ecb1334cfaf930abd321559"
)

ROUTINE_OPERATION = (
    "guardian.purchase.office_supply"
)

EXCEPTION_OPERATION = (
    "guardian.purchase.office_supply.exception"
)


@pytest.fixture
def config(
    tmp_path: Path,
) -> GuardianIdentityConfig:
    return GuardianIdentityConfig(
        base_url="https://api.ucii.sportgen-ai.com",
        identity_id=IDENTITY_ID,
        credential_id=CREDENTIAL_ID,
        credential_fingerprint=FINGERPRINT,
        custody_path=(
            tmp_path / "guardian-mldsa65-v2.json"
        ),
    )


def make_action(
    *,
    request_id: str,
    operation: str = ROUTINE_OPERATION,
) -> ActionRequest:
    return ActionRequest(
        requester="human:test",
        guardian_identity=IDENTITY_ID,
        operation=operation,
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
            30,
            tzinfo=timezone.utc,
        ),
    )


def identity_fact() -> GuardianIdentityVerification:
    return GuardianIdentityVerification(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        status=GUARDIAN_VERIFIED,
    )


def authority_fact(
    action: ActionRequest,
    *,
    decision: AuthorityDecision,
    state: str,
) -> AuthorityDecisionResult:
    return AuthorityDecisionResult(
        decision=decision,
        authority_state=state,
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        operation=action.operation,
        request_id=action.request_id,
    )


def execution_fact(
    action: ActionRequest,
    receipt_directory: Path,
) -> OfficeSupplyExecutionResult:
    return OfficeSupplyExecutionResult(
        executed=True,
        operation=action.operation,
        target=action.target,
        request_id=action.request_id,
        guardian_identity=IDENTITY_ID,
        receipt_id=(
            f"guardian-office-supply-{action.request_id}"
        ),
        completed_at=datetime(
            2026,
            9,
            10,
            22,
            35,
            tzinfo=timezone.utc,
        ),
        receipt_path=(
            receipt_directory
            / f"guardian-office-supply-{action.request_id}.json"
        ),
    )


def install_boundaries(
    monkeypatch,
    *,
    action: ActionRequest,
    authority: AuthorityDecisionResult,
):
    calls = []

    def fake_propose(
        agent,
        request,
    ):
        calls.append("STRANDS")
        return action

    def fake_verify(
        config,
    ):
        calls.append("IDENTITY")
        return identity_fact()

    def fake_check(
        proposed,
        *,
        identity,
        config,
    ):
        calls.append("AUTHORITY")
        assert proposed is action
        assert identity.status == GUARDIAN_VERIFIED
        return authority

    def fake_execute(
        proposed,
        *,
        authority=None,
        approval=None,
        receipt_directory,
    ):
        calls.append("EXECUTE")
        assert proposed is action

        if authority is not None:
            assert authority.decision is AuthorityDecision.ALLOW
            assert approval is None
        else:
            assert approval is not None
            assert authority is None

        return execution_fact(
            action,
            Path(receipt_directory),
        )

    monkeypatch.setattr(
        workflow,
        "propose_action",
        fake_propose,
    )

    monkeypatch.setattr(
        workflow,
        "verify_guardian_identity",
        fake_verify,
    )

    monkeypatch.setattr(
        workflow,
        "check_authority",
        fake_check,
    )

    monkeypatch.setattr(
        workflow,
        "execute_office_supply",
        fake_execute,
    )

    return calls


def event_types(
    outcome,
):
    return tuple(
        event.event_type
        for event in outcome.provenance
    )


def test_active_authority_executes_and_records_complete_history(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    action = make_action(
        request_id="request-active"
    )

    authority = authority_fact(
        action,
        decision=AuthorityDecision.ALLOW,
        state="ACTIVE",
    )

    calls = install_boundaries(
        monkeypatch,
        action=action,
        authority=authority,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    outcome = workflow.run_guardian_request(
        agent=object(),
        request="buy one printer cartridge",
        config=config,
        recorder=recorder,
        receipt_directory=tmp_path / "receipts",
    )

    assert calls == [
        "STRANDS",
        "IDENTITY",
        "AUTHORITY",
        "EXECUTE",
    ]

    assert outcome.execution is not None
    assert outcome.execution.executed is True

    assert event_types(outcome) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.AUTHORIZED,
        ProvenanceEventType.EXECUTION_STARTED,
        ProvenanceEventType.EXECUTION_COMPLETED,
    )


def test_not_granted_without_human_decision_stops_at_escalation(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    action = make_action(
        request_id="request-escalate",
        operation=EXCEPTION_OPERATION,
    )

    authority = authority_fact(
        action,
        decision=AuthorityDecision.ESCALATION_REQUIRED,
        state="NOT_GRANTED",
    )

    calls = install_boundaries(
        monkeypatch,
        action=action,
        authority=authority,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    outcome = workflow.run_guardian_request(
        agent=object(),
        request="exceptional printer cartridge purchase",
        config=config,
        recorder=recorder,
        receipt_directory=tmp_path / "receipts",
    )

    assert calls == [
        "STRANDS",
        "IDENTITY",
        "AUTHORITY",
    ]

    assert outcome.escalation is not None
    assert outcome.human_decision is None
    assert outcome.execution is None

    assert event_types(outcome) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.ESCALATED,
    )


def test_human_approve_once_executes_exact_escalated_action(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    action = make_action(
        request_id="request-approve",
        operation=EXCEPTION_OPERATION,
    )

    authority = authority_fact(
        action,
        decision=AuthorityDecision.ESCALATION_REQUIRED,
        state="NOT_GRANTED",
    )

    calls = install_boundaries(
        monkeypatch,
        action=action,
        authority=authority,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    outcome = workflow.run_guardian_request(
        agent=object(),
        request="exceptional printer cartridge purchase",
        config=config,
        recorder=recorder,
        receipt_directory=tmp_path / "receipts",
        human_decision=HumanDecision.APPROVE_ONCE,
    )

    assert calls == [
        "STRANDS",
        "IDENTITY",
        "AUTHORITY",
        "EXECUTE",
    ]

    assert outcome.escalation is not None
    assert outcome.human_decision is not None
    assert outcome.execution is not None

    assert event_types(outcome) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.ESCALATED,
        ProvenanceEventType.HUMAN_APPROVED,
        ProvenanceEventType.EXECUTION_STARTED,
        ProvenanceEventType.EXECUTION_COMPLETED,
    )


def test_human_denial_never_enters_executor(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    action = make_action(
        request_id="request-human-deny",
        operation=EXCEPTION_OPERATION,
    )

    authority = authority_fact(
        action,
        decision=AuthorityDecision.ESCALATION_REQUIRED,
        state="NOT_GRANTED",
    )

    calls = install_boundaries(
        monkeypatch,
        action=action,
        authority=authority,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    outcome = workflow.run_guardian_request(
        agent=object(),
        request="exceptional printer cartridge purchase",
        config=config,
        recorder=recorder,
        receipt_directory=tmp_path / "receipts",
        human_decision=HumanDecision.DENY,
    )

    assert calls == [
        "STRANDS",
        "IDENTITY",
        "AUTHORITY",
    ]

    assert "EXECUTE" not in calls
    assert outcome.execution is None

    assert event_types(outcome) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.ESCALATED,
        ProvenanceEventType.HUMAN_DENIED,
    )


def test_revoked_authority_never_enters_executor(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    action = make_action(
        request_id="request-revoked"
    )

    authority = authority_fact(
        action,
        decision=AuthorityDecision.DENY,
        state="REVOKED",
    )

    calls = install_boundaries(
        monkeypatch,
        action=action,
        authority=authority,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    outcome = workflow.run_guardian_request(
        agent=object(),
        request="buy one printer cartridge",
        config=config,
        recorder=recorder,
        receipt_directory=tmp_path / "receipts",
    )

    assert calls == [
        "STRANDS",
        "IDENTITY",
        "AUTHORITY",
    ]

    assert "EXECUTE" not in calls
    assert outcome.execution is None

    assert event_types(outcome) == (
        ProvenanceEventType.REQUEST_RECEIVED,
        ProvenanceEventType.IDENTITY_VERIFIED,
        ProvenanceEventType.AUTHORITY_CHECKED,
        ProvenanceEventType.AUTHORITY_REVOKED,
        ProvenanceEventType.EXECUTION_REFUSED,
    )


def test_human_approval_cannot_override_deny(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    action = make_action(
        request_id="request-deny-override"
    )

    authority = authority_fact(
        action,
        decision=AuthorityDecision.DENY,
        state="REVOKED",
    )

    calls = install_boundaries(
        monkeypatch,
        action=action,
        authority=authority,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    with pytest.raises(
        ValueError,
        match="cannot override DENY",
    ):
        workflow.run_guardian_request(
            agent=object(),
            request="buy one printer cartridge",
            config=config,
            recorder=recorder,
            receipt_directory=tmp_path / "receipts",
            human_decision=HumanDecision.APPROVE_ONCE,
        )

    assert calls == [
        "STRANDS",
        "IDENTITY",
        "AUTHORITY",
    ]

    assert "EXECUTE" not in calls


def test_every_request_performs_fresh_identity_and_authority_checks(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    actions = iter(
        [
            make_action(
                request_id="request-fresh-1"
            ),
            make_action(
                request_id="request-fresh-2"
            ),
        ]
    )

    calls = []

    monkeypatch.setattr(
        workflow,
        "propose_action",
        lambda agent, request: next(actions),
    )

    def fake_verify(config):
        calls.append("IDENTITY")
        return identity_fact()

    def fake_check(
        action,
        *,
        identity,
        config,
    ):
        calls.append(
            ("AUTHORITY", action.request_id)
        )

        return authority_fact(
            action,
            decision=AuthorityDecision.DENY,
            state="REVOKED",
        )

    monkeypatch.setattr(
        workflow,
        "verify_guardian_identity",
        fake_verify,
    )

    monkeypatch.setattr(
        workflow,
        "check_authority",
        fake_check,
    )

    def forbidden_execute(*args, **kwargs):
        raise AssertionError(
            "revoked authority entered executor"
        )

    monkeypatch.setattr(
        workflow,
        "execute_office_supply",
        forbidden_execute,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    first = workflow.run_guardian_request(
        agent=object(),
        request="first request",
        config=config,
        recorder=recorder,
        receipt_directory=tmp_path / "receipts",
    )

    second = workflow.run_guardian_request(
        agent=object(),
        request="second request",
        config=config,
        recorder=recorder,
        receipt_directory=tmp_path / "receipts",
    )

    assert first.authority.authority_state == "REVOKED"
    assert second.authority.authority_state == "REVOKED"

    assert calls == [
        "IDENTITY",
        ("AUTHORITY", "request-fresh-1"),
        "IDENTITY",
        ("AUTHORITY", "request-fresh-2"),
    ]


def test_model_output_never_bypasses_identity_or_authority(
    tmp_path: Path,
    monkeypatch,
    config,
) -> None:
    action = make_action(
        request_id="request-model-no-authority"
    )

    monkeypatch.setattr(
        workflow,
        "propose_action",
        lambda agent, request: action,
    )

    def verification_failure(config):
        raise RuntimeError(
            "identity verification failed"
        )

    monkeypatch.setattr(
        workflow,
        "verify_guardian_identity",
        verification_failure,
    )

    def forbidden_check(*args, **kwargs):
        raise AssertionError(
            "authority called after identity failure"
        )

    def forbidden_execute(*args, **kwargs):
        raise AssertionError(
            "executor called after identity failure"
        )

    monkeypatch.setattr(
        workflow,
        "check_authority",
        forbidden_check,
    )

    monkeypatch.setattr(
        workflow,
        "execute_office_supply",
        forbidden_execute,
    )

    recorder = GuardianProvenanceRecorder(
        tmp_path / "provenance.jsonl"
    )

    with pytest.raises(
        RuntimeError,
        match="identity verification failed",
    ):
        workflow.run_guardian_request(
            agent=object(),
            request="model proposal only",
            config=config,
            recorder=recorder,
            receipt_directory=tmp_path / "receipts",
        )

    history = recorder.history_for_request(
        action.request_id
    )

    assert tuple(
        event.event_type
        for event in history
    ) == (
        ProvenanceEventType.REQUEST_RECEIVED,
    )


def test_workflow_uses_only_public_guardian_security_modules() -> None:
    source = Path(
        workflow.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "pq_auth" not in source
    assert "src.pq_auth" not in source

    required = (
        "propose_action(",
        "verify_guardian_identity(",
        "check_authority(",
        "execute_office_supply(",
        "record_request(",
        "record_identity(",
        "record_authority(",
    )

    for marker in required:
        assert marker in source
