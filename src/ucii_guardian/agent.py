"""Minimum AWS Strands orchestration boundary for UCII Guardian."""

from __future__ import annotations

from strands import Agent


GUARDIAN_SYSTEM_PROMPT = """
You are UCII Guardian. Your present capability is intentionally limited.

Interpret the user's requested action, but do not claim that the action is
permitted, authorized, approved, verified, or executed. You currently have no
execution tools and no authority-granting tools.

Your role in this build stage is reasoning/orchestration only. Authorization
will later be established outside model output through the UCII authority
boundary.
""".strip()


def build_guardian_agent() -> Agent:
    """Construct the minimum Strands Guardian with no consequential tools."""

    return Agent(
        system_prompt=GUARDIAN_SYSTEM_PROMPT,
        tools=[],
    )
