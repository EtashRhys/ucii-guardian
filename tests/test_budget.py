"""Tests for Guardian human-controlled budget policy."""

import pytest

from ucii_guardian.budget import (
    GuardianBudgetError,
    GuardianBudgetPolicy,
    MAX_BUDGET_USD,
    MIN_BUDGET_USD,
)


def test_budget_range_is_exact() -> None:
    assert str(MIN_BUDGET_USD) == "0.00"
    assert str(MAX_BUDGET_USD) == "5000.00"


@pytest.mark.parametrize(
    ("budget", "requested", "expected"),
    [
        ("0.00", "0.00", True),
        ("0.00", "0.01", False),
        ("500.00", "35.00", True),
        ("500.00", "500.00", True),
        ("500.00", "500.01", False),
        ("5000.00", "5000.00", True),
    ],
)
def test_budget_per_transaction_decision(
    budget: str,
    requested: str,
    expected: bool,
) -> None:
    policy = GuardianBudgetPolicy.from_value(budget)
    assert policy.permits(requested) is expected


@pytest.mark.parametrize("budget", ["-0.01", "5000.01", "not-money"])
def test_invalid_human_budget_fails_closed(budget: str) -> None:
    with pytest.raises(GuardianBudgetError):
        GuardianBudgetPolicy.from_value(budget)
