"""Minimum AWS Strands orchestration boundary for UCII Guardian."""

from __future__ import annotations

from strands import Agent

from .action import ActionRequest


GUARDIAN_SYSTEM_PROMPT_TEMPLATE = """
You are UCII Guardian. Your capability is intentionally bounded.

Interpret the user's requested action and normalize it into the requested
ActionRequest schema. Do not claim that the action is permitted, authorized,
approved, verified, or executed. You have no execution tools and no
authority-granting tools.

For every ActionRequest, use this exact Guardian UCII identity:

{guardian_identity}

That identity is an authentication binding only. It does not mean the proposed
action is authorized. Authorization is established independently outside model
output through the UCII authority boundary.
""".strip()


def build_guardian_agent(
    *,
    guardian_identity: str,
) -> Agent:
    """Construct Guardian bound to one explicit UCII identity."""

    if (
        not isinstance(guardian_identity, str)
        or not guardian_identity.strip()
    ):
        raise ValueError(
            "guardian_identity must be a non-empty string"
        )

    system_prompt = GUARDIAN_SYSTEM_PROMPT_TEMPLATE.format(
        guardian_identity=guardian_identity,
    )

    return Agent(
        system_prompt=system_prompt,
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
