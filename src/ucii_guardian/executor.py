"""Protected consequential executor for UCII Guardian.

The executor is deliberately narrow. It supports exactly one demo operation
and refuses to perform its durable side effect unless authority evidence is
bound to the exact proposed action.

An ActionRequest, model instruction, identity-verification fact, or authority
state by itself is never sufficient to execute.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ucii_guardian.action import ActionRequest
from ucii_guardian.approval import (
    HumanDecision,
    OneOffApproval,
)
from ucii_guardian.authority import (
    AuthorityDecision,
    AuthorityDecisionResult,
)


OFFICE_SUPPLY_OPERATION = "guardian.purchase.office_supply"
OFFICE_SUPPLY_TARGET_PREFIX = "office-supply:"

MAX_OFFICE_SUPPLY_QUANTITY = 10
MAX_OFFICE_SUPPLY_PRICE_USD = 500.0


class GuardianExecutionError(RuntimeError):
    """Raised when protected execution cannot proceed safely."""


@dataclass(frozen=True)
class OfficeSupplyExecutionResult:
    """Result of one completed protected office-supply execution."""

    executed: bool
    operation: str
    target: str
    request_id: str
    guardian_identity: str
    receipt_id: str
    completed_at: datetime
    receipt_path: Path


def _require_exact_authority(
    action: ActionRequest,
    *,
    authority: AuthorityDecisionResult | None,
    approval: OneOffApproval | None,
) -> None:
    """Require one valid execution-authority path for this exact action."""

    if authority is not None and approval is not None:
        raise GuardianExecutionError(
            "Protected execution requires exactly one authority path"
        )

    if authority is not None:
        if not isinstance(
            authority,
            AuthorityDecisionResult,
        ):
            raise GuardianExecutionError(
                "Protected execution requires Guardian authority evidence"
            )

        if authority.decision is not AuthorityDecision.ALLOW:
            raise GuardianExecutionError(
                "Protected execution requires ALLOW"
            )

        if authority.authority_state != "ACTIVE":
            raise GuardianExecutionError(
                "Protected execution requires ACTIVE delegated authority"
            )

        if authority.identity_id != action.guardian_identity:
            raise GuardianExecutionError(
                "Authority identity does not match action"
            )

        if authority.operation != action.operation:
            raise GuardianExecutionError(
                "Authority operation does not match action"
            )

        if authority.request_id != action.request_id:
            raise GuardianExecutionError(
                "Authority request ID does not match action"
            )

        return

    if approval is not None:
        if not isinstance(
            approval,
            OneOffApproval,
        ):
            raise GuardianExecutionError(
                "Protected execution requires valid one-off approval"
            )

        if approval.decision is not HumanDecision.APPROVE_ONCE:
            raise GuardianExecutionError(
                "Protected execution requires APPROVE_ONCE"
            )

        if approval.guardian_identity != action.guardian_identity:
            raise GuardianExecutionError(
                "Approval identity does not match action"
            )

        if approval.requester != action.requester:
            raise GuardianExecutionError(
                "Approval requester does not match action"
            )

        if approval.operation != action.operation:
            raise GuardianExecutionError(
                "Approval operation does not match action"
            )

        if approval.target != action.target:
            raise GuardianExecutionError(
                "Approval target does not match action"
            )

        if dict(approval.parameters) != dict(action.parameters):
            raise GuardianExecutionError(
                "Approval parameters do not match action"
            )

        if approval.request_id != action.request_id:
            raise GuardianExecutionError(
                "Approval request ID does not match action"
            )

        return

    raise GuardianExecutionError(
        "Protected execution requires delegated authority "
        "or one-off human approval"
    )


def _validate_office_supply_action(
    action: ActionRequest,
) -> tuple[int, float]:
    """Validate the one bounded consequential demo domain."""

    if action.operation != OFFICE_SUPPLY_OPERATION:
        raise GuardianExecutionError(
            "Unsupported protected execution operation"
        )

    if not action.target.startswith(
        OFFICE_SUPPLY_TARGET_PREFIX
    ):
        raise GuardianExecutionError(
            "Office-supply target is outside the protected domain"
        )

    quantity: Any = action.parameters.get(
        "quantity"
    )

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity < 1
        or quantity > MAX_OFFICE_SUPPLY_QUANTITY
    ):
        raise GuardianExecutionError(
            "Office-supply quantity is outside the executor boundary"
        )

    max_price: Any = action.parameters.get(
        "max_price_usd"
    )

    if (
        isinstance(max_price, bool)
        or not isinstance(max_price, (int, float))
    ):
        raise GuardianExecutionError(
            "Office-supply maximum price is invalid"
        )

    max_price = float(max_price)

    if (
        not math.isfinite(max_price)
        or max_price <= 0.0
        or max_price > MAX_OFFICE_SUPPLY_PRICE_USD
    ):
        raise GuardianExecutionError(
            "Office-supply maximum price is outside the executor boundary"
        )

    return quantity, max_price


def execute_office_supply(
    action: ActionRequest,
    *,
    authority: AuthorityDecisionResult | None = None,
    approval: OneOffApproval | None = None,
    receipt_directory: Path,
) -> OfficeSupplyExecutionResult:
    """Execute exactly one bounded office-supply action.

    Execution here is a controlled consequential demo action: a durable,
    uniquely keyed order receipt is created outside the model boundary.

    The receipt write is intentionally performed only after every authority
    and domain guard succeeds. Existing receipt IDs fail closed so the same
    request cannot be replayed into a second execution.

    Execution may proceed through either current ACTIVE + ALLOW delegated
    authority or an exact-action human APPROVE_ONCE fact. The approval path
    does not create or broaden standing UCII delegated authority.

    This function does not grant authority, authenticate Guardian, call an
    LLM, request human approval, or broaden the operation scope.
    """

    _require_exact_authority(
        action,
        authority=authority,
        approval=approval,
    )

    quantity, max_price = (
        _validate_office_supply_action(
            action
        )
    )

    receipt_directory = Path(
        receipt_directory
    )

    receipt_id = (
        f"guardian-office-supply-{action.request_id}"
    )

    receipt_path = (
        receipt_directory
        / f"{receipt_id}.json"
    )

    completed_at = datetime.now(
        timezone.utc
    )

    receipt = {
        "executed": True,
        "operation": action.operation,
        "target": action.target,
        "request_id": action.request_id,
        "guardian_identity": (
            action.guardian_identity
        ),
        "requester": action.requester,
        "quantity": quantity,
        "max_price_usd": max_price,
        "receipt_id": receipt_id,
        "completed_at": (
            completed_at.isoformat()
        ),
    }

    receipt_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with receipt_path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            json.dump(
                receipt,
                handle,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            handle.write("\n")
    except FileExistsError as exc:
        raise GuardianExecutionError(
            "Protected action has already been executed"
        ) from exc
    except OSError as exc:
        raise GuardianExecutionError(
            "Protected execution receipt could not be persisted"
        ) from exc

    return OfficeSupplyExecutionResult(
        executed=True,
        operation=action.operation,
        target=action.target,
        request_id=action.request_id,
        guardian_identity=(
            action.guardian_identity
        ),
        receipt_id=receipt_id,
        completed_at=completed_at,
        receipt_path=receipt_path,
    )
