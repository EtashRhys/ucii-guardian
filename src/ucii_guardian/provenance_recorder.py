"""Durable lifecycle provenance composition for UCII Guardian.

This module persists provenance events derived from already-established
Guardian facts. It does not establish identity, create or mutate authority,
obtain human decisions, invoke Strands, or execute consequential actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    EscalationRequest,
    HumanDecisionResult,
)
from ucii_guardian.authority import (
    AuthorityDecisionResult,
)
from ucii_guardian.executor import (
    OfficeSupplyExecutionResult,
)
from ucii_guardian.identity import (
    GuardianIdentityVerification,
)
from ucii_guardian.provenance import (
    ProvenanceEvent,
    append_provenance_event,
    read_provenance_events,
)
from ucii_guardian.provenance_lifecycle import (
    authority_events,
    execution_completed_event,
    execution_started_event,
    human_decision_event,
    identity_verified_event,
    request_received_event,
)


@dataclass(frozen=True)
class GuardianProvenanceRecorder:
    """Append-only recorder for one Guardian provenance ledger."""

    ledger_path: Path

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "ledger_path",
            Path(self.ledger_path),
        )

    def _append(
        self,
        event: ProvenanceEvent,
    ) -> ProvenanceEvent:
        append_provenance_event(
            self.ledger_path,
            event,
        )
        return event

    def record_request(
        self,
        action: ActionRequest,
    ) -> ProvenanceEvent:
        """Persist REQUEST_RECEIVED for an established ActionRequest."""

        return self._append(
            request_received_event(
                action
            )
        )

    def record_identity(
        self,
        action: ActionRequest,
        *,
        identity: GuardianIdentityVerification,
    ) -> ProvenanceEvent:
        """Persist IDENTITY_VERIFIED from established verification."""

        return self._append(
            identity_verified_event(
                action,
                identity=identity,
            )
        )

    def record_authority(
        self,
        action: ActionRequest,
        *,
        authority: AuthorityDecisionResult,
    ) -> tuple[ProvenanceEvent, ...]:
        """Persist explanatory events for an established authority result."""

        events = authority_events(
            action,
            authority=authority,
        )

        for event in events:
            self._append(
                event
            )

        return events

    def record_human_decision(
        self,
        action: ActionRequest,
        *,
        escalation: EscalationRequest,
        result: HumanDecisionResult,
    ) -> ProvenanceEvent:
        """Persist one already-established human decision."""

        return self._append(
            human_decision_event(
                action,
                escalation=escalation,
                result=result,
            )
        )

    def record_execution_started(
        self,
        action: ActionRequest,
        *,
        authority_path: str,
    ) -> ProvenanceEvent:
        """Persist execution-start fact after an external gate passes."""

        return self._append(
            execution_started_event(
                action,
                authority_path=authority_path,
            )
        )

    def record_execution_completed(
        self,
        action: ActionRequest,
        *,
        execution: OfficeSupplyExecutionResult,
    ) -> ProvenanceEvent:
        """Persist an already-completed protected execution fact."""

        return self._append(
            execution_completed_event(
                action,
                execution=execution,
            )
        )

    def history(
        self,
    ) -> tuple[ProvenanceEvent, ...]:
        """Return the complete validated append-order ledger."""

        return read_provenance_events(
            self.ledger_path
        )

    def history_for_request(
        self,
        request_id: str,
    ) -> tuple[ProvenanceEvent, ...]:
        """Reconstruct one request lifecycle from the durable ledger."""

        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError(
                "request_id must be a non-empty string"
            )

        normalized = request_id.strip()

        return tuple(
            event
            for event in self.history()
            if event.request_id == normalized
        )
