"""Human-controlled economic policy for UCII Guardian.

Budget policy is server-held and never established by model output.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


MIN_BUDGET_USD = Decimal("0.00")
MAX_BUDGET_USD = Decimal("5000.00")


class GuardianBudgetError(ValueError):
    """Raised when a human budget value is outside Guardian policy."""


@dataclass(frozen=True)
class GuardianBudgetPolicy:
    """Validated per-request autonomous spending ceiling."""

    max_transaction_usd: Decimal

    @classmethod
    def from_value(cls, value: object) -> "GuardianBudgetPolicy":
        try:
            amount = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as exc:
            raise GuardianBudgetError("Budget value is invalid") from exc

        if amount < MIN_BUDGET_USD or amount > MAX_BUDGET_USD:
            raise GuardianBudgetError(
                "Budget must be between $0.00 and $5,000.00"
            )

        return cls(max_transaction_usd=amount)

    def permits(self, requested_amount: object) -> bool:
        try:
            amount = Decimal(str(requested_amount)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as exc:
            raise GuardianBudgetError("Requested amount is invalid") from exc

        if amount < Decimal("0.00"):
            raise GuardianBudgetError("Requested amount cannot be negative")

        return amount <= self.max_transaction_usd
