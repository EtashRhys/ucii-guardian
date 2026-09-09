"""Bounded action representation for UCII Guardian."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """A normalized proposed action.

    This object describes intent only. Possessing an ActionRequest never implies
    that Guardian is authorized to execute it.
    """

    requester: str
    guardian_identity: str
    operation: str
    target: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    requested_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        for name in ("requester", "guardian_identity", "operation", "target"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")

        object.__setattr__(
            self,
            "parameters",
            MappingProxyType(dict(self.parameters)),
        )

        if self.requested_at.tzinfo is None:
            raise ValueError("requested_at must be timezone-aware")
