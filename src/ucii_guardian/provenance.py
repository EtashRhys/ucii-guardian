"""Durable provenance primitives for UCII Guardian.

Provenance records established facts about Guardian activity. It never grants,
modifies, broadens, revokes, or substitutes for authority.

The recorder is intentionally small: immutable event envelopes are appended as
one canonical JSON object per line to a local JSONL ledger.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


class ProvenanceError(RuntimeError):
    """Raised when provenance cannot be recorded or reconstructed safely."""


class ProvenanceEventType(str, Enum):
    """Minimum Guardian event vocabulary required by Objective 7."""

    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    AUTHORITY_CHECKED = "AUTHORITY_CHECKED"
    AUTHORIZED = "AUTHORIZED"
    ESCALATED = "ESCALATED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_DENIED = "HUMAN_DENIED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    AUTHORITY_REVOKED = "AUTHORITY_REVOKED"
    EXECUTION_REFUSED = "EXECUTION_REFUSED"


_FORBIDDEN_DETAIL_KEY_FRAGMENTS = (
    "private_key",
    "private-key",
    "secret",
    "password",
    "token",
    "signature",
    "controller_authority",
    "controller-authority",
    "recovery",
    "wallet",
    "payment_proof",
    "payment-proof",
    "api_key",
    "api-key",
)


def _validate_non_empty(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _validate_safe_details(
    value: Any,
    *,
    path: str = "details",
) -> None:
    """Reject secret-bearing field names recursively before persistence."""

    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if not isinstance(raw_key, str) or not raw_key.strip():
                raise ProvenanceError(
                    f"{path} keys must be non-empty strings"
                )

            key = raw_key.strip()
            normalized = key.lower()

            if any(
                fragment in normalized
                for fragment in _FORBIDDEN_DETAIL_KEY_FRAGMENTS
            ):
                raise ProvenanceError(
                    f"Sensitive provenance field is forbidden: {path}.{key}"
                )

            _validate_safe_details(
                child,
                path=f"{path}.{key}",
            )

        return

    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _validate_safe_details(
                child,
                path=f"{path}[{index}]",
            )


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                str(key): _freeze_value(child)
                for key, child in value.items()
            }
        )

    if isinstance(value, list):
        return tuple(
            _freeze_value(child)
            for child in value
        )

    if isinstance(value, tuple):
        return tuple(
            _freeze_value(child)
            for child in value
        )

    return value


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(child)
            for key, child in value.items()
        }

    if isinstance(value, tuple):
        return [
            _json_value(child)
            for child in value
        ]

    return value


@dataclass(frozen=True)
class ProvenanceEvent:
    """Immutable non-authoritative fact about one Guardian lifecycle."""

    event_type: ProvenanceEventType
    request_id: str
    guardian_identity: str
    reason: str
    operation: str | None = None
    details: Mapping[str, Any] = field(
        default_factory=dict
    )
    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.event_type,
            ProvenanceEventType,
        ):
            raise ProvenanceError(
                "event_type must be a ProvenanceEventType"
            )

        object.__setattr__(
            self,
            "request_id",
            _validate_non_empty(
                self.request_id,
                field_name="request_id",
            ),
        )

        object.__setattr__(
            self,
            "guardian_identity",
            _validate_non_empty(
                self.guardian_identity,
                field_name="guardian_identity",
            ),
        )

        object.__setattr__(
            self,
            "reason",
            _validate_non_empty(
                self.reason,
                field_name="reason",
            ),
        )

        object.__setattr__(
            self,
            "event_id",
            _validate_non_empty(
                self.event_id,
                field_name="event_id",
            ),
        )

        if self.operation is not None:
            object.__setattr__(
                self,
                "operation",
                _validate_non_empty(
                    self.operation,
                    field_name="operation",
                ),
            )

        if (
            not isinstance(self.occurred_at, datetime)
            or self.occurred_at.tzinfo is None
            or self.occurred_at.utcoffset() is None
        ):
            raise ProvenanceError(
                "occurred_at must be timezone-aware"
            )

        if not isinstance(self.details, Mapping):
            raise ProvenanceError(
                "details must be a mapping"
            )

        _validate_safe_details(
            self.details
        )

        object.__setattr__(
            self,
            "details",
            _freeze_value(
                dict(self.details)
            ),
        )

    def to_record(self) -> dict[str, Any]:
        """Return the canonical persisted representation."""

        return {
            "details": _json_value(self.details),
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "guardian_identity": self.guardian_identity,
            "occurred_at": self.occurred_at.isoformat(),
            "operation": self.operation,
            "reason": self.reason,
            "request_id": self.request_id,
        }


def append_provenance_event(
    ledger_path: Path,
    event: ProvenanceEvent,
) -> None:
    """Append exactly one validated event to a durable local JSONL ledger."""

    if not isinstance(event, ProvenanceEvent):
        raise ProvenanceError(
            "provenance recorder requires a ProvenanceEvent"
        )

    ledger_path = Path(
        ledger_path
    )

    try:
        ledger_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        encoded = json.dumps(
            event.to_record(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        with ledger_path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(encoded)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

    except OSError as exc:
        raise ProvenanceError(
            "provenance event could not be persisted"
        ) from exc


def read_provenance_events(
    ledger_path: Path,
) -> tuple[ProvenanceEvent, ...]:
    """Reconstruct validated provenance events in durable append order."""

    ledger_path = Path(
        ledger_path
    )

    if not ledger_path.exists():
        return ()

    events: list[ProvenanceEvent] = []

    try:
        with ledger_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line_number, raw_line in enumerate(
                handle,
                start=1,
            ):
                if not raw_line.strip():
                    raise ProvenanceError(
                        "provenance ledger contains an empty record "
                        f"at line {line_number}"
                    )

                try:
                    record = json.loads(
                        raw_line
                    )
                except json.JSONDecodeError as exc:
                    raise ProvenanceError(
                        "provenance ledger contains invalid JSON "
                        f"at line {line_number}"
                    ) from exc

                if not isinstance(record, dict):
                    raise ProvenanceError(
                        "provenance ledger record must be an object "
                        f"at line {line_number}"
                    )

                expected_keys = {
                    "details",
                    "event_id",
                    "event_type",
                    "guardian_identity",
                    "occurred_at",
                    "operation",
                    "reason",
                    "request_id",
                }

                if set(record) != expected_keys:
                    raise ProvenanceError(
                        "provenance ledger record schema mismatch "
                        f"at line {line_number}"
                    )

                try:
                    event = ProvenanceEvent(
                        event_type=ProvenanceEventType(
                            record["event_type"]
                        ),
                        request_id=record["request_id"],
                        guardian_identity=record[
                            "guardian_identity"
                        ],
                        reason=record["reason"],
                        operation=record["operation"],
                        details=record["details"],
                        event_id=record["event_id"],
                        occurred_at=datetime.fromisoformat(
                            record["occurred_at"]
                        ),
                    )
                except (
                    TypeError,
                    ValueError,
                    ProvenanceError,
                ) as exc:
                    raise ProvenanceError(
                        "provenance ledger record is invalid "
                        f"at line {line_number}"
                    ) from exc

                events.append(
                    event
                )

    except ProvenanceError:
        raise
    except OSError as exc:
        raise ProvenanceError(
            "provenance ledger could not be read"
        ) from exc

    return tuple(
        events
    )
