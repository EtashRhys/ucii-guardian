"""Tests for Guardian durable provenance primitives."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ucii_guardian.provenance import (
    ProvenanceError,
    ProvenanceEvent,
    ProvenanceEventType,
    append_provenance_event,
    read_provenance_events,
)


IDENTITY_ID = (
    "35c1db3d-61d7-4d0d-a5d7-db3ab7f79520"
)

REQUEST_ID = "request-provenance-123"
OPERATION = "guardian.purchase.office_supply"


def make_event(
    *,
    event_type: ProvenanceEventType = (
        ProvenanceEventType.REQUEST_RECEIVED
    ),
    reason: str = "Human submitted a bounded Guardian request.",
    details=None,
    event_id: str = "event-123",
    occurred_at: datetime | None = None,
) -> ProvenanceEvent:
    return ProvenanceEvent(
        event_type=event_type,
        request_id=REQUEST_ID,
        guardian_identity=IDENTITY_ID,
        operation=OPERATION,
        reason=reason,
        details=(
            {
                "target": "office-supply:test-cartridge",
                "quantity": 1,
                "max_price_usd": 80,
            }
            if details is None
            else details
        ),
        event_id=event_id,
        occurred_at=(
            occurred_at
            or datetime(
                2026,
                9,
                10,
                21,
                0,
                tzinfo=timezone.utc,
            )
        ),
    )


def test_event_vocabulary_matches_objective_7_contract() -> None:
    assert {
        item.value
        for item in ProvenanceEventType
    } == {
        "REQUEST_RECEIVED",
        "IDENTITY_VERIFIED",
        "AUTHORITY_CHECKED",
        "AUTHORIZED",
        "ESCALATED",
        "HUMAN_APPROVED",
        "HUMAN_DENIED",
        "EXECUTION_STARTED",
        "EXECUTION_COMPLETED",
        "AUTHORITY_REVOKED",
        "EXECUTION_REFUSED",
    }


def test_provenance_event_is_immutable() -> None:
    event = make_event()

    with pytest.raises(FrozenInstanceError):
        event.reason = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError):
        event.details["quantity"] = 2  # type: ignore[index]


def test_provenance_event_requires_non_empty_core_fields() -> None:
    with pytest.raises(
        ProvenanceError,
        match="request_id",
    ):
        ProvenanceEvent(
            event_type=ProvenanceEventType.REQUEST_RECEIVED,
            request_id=" ",
            guardian_identity=IDENTITY_ID,
            operation=OPERATION,
            reason="request received",
        )


def test_provenance_event_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(
        ProvenanceError,
        match="timezone-aware",
    ):
        make_event(
            occurred_at=datetime(
                2026,
                9,
                10,
                21,
                0,
            )
        )


@pytest.mark.parametrize(
    "details",
    [
        {"private_key": "do-not-record"},
        {"nested": {"password": "do-not-record"}},
        {"auth": {"access_token": "do-not-record"}},
        {"signature": "do-not-record"},
        {"controller_authority": "do-not-record"},
        {"payment_proof": "do-not-record"},
        {"api_key": "do-not-record"},
    ],
)
def test_sensitive_detail_fields_are_rejected(
    details,
) -> None:
    with pytest.raises(
        ProvenanceError,
        match="Sensitive provenance field",
    ):
        make_event(
            details=details
        )


def test_event_record_contains_facts_not_authority_capability() -> None:
    event = make_event(
        event_type=ProvenanceEventType.AUTHORIZED,
        reason="UCII returned ACTIVE delegated authority.",
        details={
            "authority_state": "ACTIVE",
            "decision": "ALLOW",
        },
    )

    record = event.to_record()

    assert record["event_type"] == "AUTHORIZED"
    assert record["details"]["decision"] == "ALLOW"

    assert "grant_authority" not in record
    assert "execution_authority" not in record
    assert "controller_authority" not in record


def test_append_creates_one_canonical_jsonl_record(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "guardian-provenance.jsonl"
    event = make_event()

    append_provenance_event(
        ledger,
        event,
    )

    lines = ledger.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    stored = json.loads(
        lines[0]
    )

    assert stored == event.to_record()


def test_append_preserves_event_order(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "guardian-provenance.jsonl"

    first = make_event(
        event_type=ProvenanceEventType.REQUEST_RECEIVED,
        event_id="event-1",
    )

    second = make_event(
        event_type=ProvenanceEventType.IDENTITY_VERIFIED,
        event_id="event-2",
        reason="Guardian identity verified through UCII.",
    )

    append_provenance_event(
        ledger,
        first,
    )

    append_provenance_event(
        ledger,
        second,
    )

    events = read_provenance_events(
        ledger
    )

    assert tuple(
        event.event_id
        for event in events
    ) == (
        "event-1",
        "event-2",
    )


def test_readback_reconstructs_validated_event(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "guardian-provenance.jsonl"
    expected = make_event()

    append_provenance_event(
        ledger,
        expected,
    )

    actual = read_provenance_events(
        ledger
    )

    assert len(actual) == 1
    assert actual[0] == expected


def test_missing_ledger_reconstructs_as_empty_history(
    tmp_path: Path,
) -> None:
    assert read_provenance_events(
        tmp_path / "missing.jsonl"
    ) == ()


def test_corrupt_ledger_fails_closed(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "guardian-provenance.jsonl"

    ledger.write_text(
        "{not-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ProvenanceError,
        match="invalid JSON",
    ):
        read_provenance_events(
            ledger
        )


def test_unknown_event_type_fails_closed_on_read(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "guardian-provenance.jsonl"

    record = make_event().to_record()
    record["event_type"] = "MODEL_GRANTED_AUTHORITY"

    ledger.write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ProvenanceError,
        match="record is invalid",
    ):
        read_provenance_events(
            ledger
        )


def test_extra_record_fields_fail_closed(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "guardian-provenance.jsonl"

    record = make_event().to_record()
    record["unexpected"] = "value"

    ledger.write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ProvenanceError,
        match="schema mismatch",
    ):
        read_provenance_events(
            ledger
        )
