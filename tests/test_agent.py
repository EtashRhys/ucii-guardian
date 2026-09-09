from types import SimpleNamespace

import pytest

from ucii_guardian.action import ActionRequest
from ucii_guardian.agent import propose_action


class FakeAgent:
    def __init__(self, structured_output: ActionRequest | None) -> None:
        self.structured_output = structured_output
        self.calls: list[tuple[str, type[ActionRequest]]] = []

    def __call__(
        self,
        request: str,
        *,
        structured_output_model: type[ActionRequest],
    ) -> SimpleNamespace:
        self.calls.append((request, structured_output_model))
        return SimpleNamespace(structured_output=self.structured_output)


def test_propose_action_returns_validated_structured_output() -> None:
    expected = ActionRequest(
        requester="human:demo",
        guardian_identity="guardian:pending-ucii-binding",
        operation="purchase",
        target="printer_cartridge",
        parameters={
            "quantity": 1,
            "price_usd": 67.0,
            "currency": "USD",
        },
    )
    agent = FakeAgent(expected)

    actual = propose_action(
        agent,  # type: ignore[arg-type]
        "Purchase one printer cartridge for 67 US dollars.",
    )

    assert actual is expected
    assert agent.calls == [
        (
            "Purchase one printer cartridge for 67 US dollars.",
            ActionRequest,
        )
    ]


def test_propose_action_rejects_blank_request_before_agent_call() -> None:
    agent = FakeAgent(None)

    with pytest.raises(ValueError, match="non-empty string"):
        propose_action(agent, "   ")  # type: ignore[arg-type]

    assert agent.calls == []


def test_propose_action_fails_closed_without_structured_output() -> None:
    agent = FakeAgent(None)

    with pytest.raises(
        RuntimeError,
        match="did not return a structured ActionRequest",
    ):
        propose_action(
            agent,  # type: ignore[arg-type]
            "Purchase one printer cartridge.",
        )

    assert len(agent.calls) == 1
    assert agent.calls[0][1] is ActionRequest
