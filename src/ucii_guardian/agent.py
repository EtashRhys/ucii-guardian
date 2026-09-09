"""Minimum AWS Strands orchestration boundary for UCII Guardian."""

from __future__ import annotations

from strands import Agent

from .action import ActionRequest


GUARDIAN_SYSTEM_PROMPT = """
You are UCII Guardian. Your present capability is intentionally limited.

Interpret the user's requested action and normalize it into the requested
ActionRequest schema. Do not claim that the action is permitted, authorized,
approved, verified, or executed. You currently have no execution tools and no
authority-granting tools.

Use `guardian:pending-ucii-binding` as guardian_identity until UCII identity
binding is implemented. Authorization will later be established outside model
output through the UCII authority boundary.
""".strip()


def build_guardian_agent() -> Agent:
    """Construct the minimum Strands Guardian with no consequential tools."""

    return Agent(
        system_prompt=GUARDIAN_SYSTEM_PROMPT,
        tools=[],
    )


def propose_action(agent: Agent, request: str) -> ActionRequest:
    """Use Strands structured output to normalize intent without executing it."""

    if not isinstance(request, str) or not request.strip():
        raise ValueError("request must be a non-empty string")

    result = agent(request, structured_output_model=ActionRequest)
    action = result.structured_output
    if action is None:
        raise RuntimeError("Guardian did not return a structured ActionRequest")
    return action
