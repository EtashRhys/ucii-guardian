from datetime import datetime

import pytest

from ucii_guardian.action import ActionRequest


def test_action_request_is_bounded_and_immutable() -> None:
    action = ActionRequest(
        requester="human:demo",
        guardian_identity="guardian:pending-ucii-binding",
        operation="purchase_office_supply",
        target="printer_cartridge",
        parameters={"amount": "67.00", "currency": "USD"},
    )

    assert action.operation == "purchase_office_supply"
    assert action.target == "printer_cartridge"
    assert action.parameters["amount"] == "67.00"
    assert action.request_id
    assert action.requested_at.tzinfo is not None

    with pytest.raises(TypeError):
        action.parameters["amount"] = "999.00"  # type: ignore[index]


def test_action_request_rejects_empty_required_fields() -> None:
    with pytest.raises(ValueError, match="operation"):
        ActionRequest(
            requester="human:demo",
            guardian_identity="guardian:pending-ucii-binding",
            operation=" ",
            target="printer_cartridge",
        )


def test_action_request_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ActionRequest(
            requester="human:demo",
            guardian_identity="guardian:pending-ucii-binding",
            operation="purchase_office_supply",
            target="printer_cartridge",
            requested_at=datetime(2026, 9, 9, 12, 0, 0),
        )
