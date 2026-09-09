"""Bounded action representation for UCII Guardian."""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)


class ActionRequest(BaseModel):
    """A normalized proposed action.

    This object describes intent only. Possessing an ActionRequest never implies
    that Guardian is authorized to execute it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    requester: str = Field(description="Human or external requester identifier")
    guardian_identity: str = Field(description="Guardian identity handling the request")
    operation: str = Field(description="Bounded operation being proposed")
    target: str = Field(description="Specific action target")
    parameters: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("requester", "guardian_identity", "operation", "target")
    @classmethod
    def require_non_empty_string(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-empty string")
        return value

    @field_validator("parameters")
    @classmethod
    def freeze_parameters(cls, value: dict[str, Any]) -> dict[str, Any]:
        return MappingProxyType(dict(value))

    @field_serializer("parameters")
    def serialize_parameters(self, value: dict[str, Any]) -> dict[str, Any]:
        return dict(value)

    @field_validator("requested_at")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("requested_at must be timezone-aware")
        return value
