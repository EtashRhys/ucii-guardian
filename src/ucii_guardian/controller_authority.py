"""Protected local controller-authority secret boundary for UCII Guardian.

Controller authority is distinct from Guardian's operational signing
credential. It remains local to the Guardian server process and is never
part of browser state, LLM context, provenance, or public result objects.
"""

from __future__ import annotations

import os
from pathlib import Path

from ucii_guardian.custody import (
    _harden_private_path,
)


class GuardianControllerAuthorityError(RuntimeError):
    """Raised when Guardian cannot safely load controller authority."""


def default_controller_authority_path() -> Path:
    """Return Guardian's user-local controller-authority secret path."""

    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if not local_app_data:
        raise GuardianControllerAuthorityError(
            "LOCALAPPDATA is required for Guardian controller authority"
        )

    return (
        Path(local_app_data)
        / "UCII"
        / "Guardian"
        / "authority"
        / "controller-authority-v1"
    )


def load_controller_authority(
    path: Path | None = None,
) -> str:
    """Load one existing protected controller-authority secret.

    This function never creates, rotates, logs, returns metadata about,
    or persists controller authority. Provisioning is deliberately
    outside this runtime loading boundary.
    """

    resolved = (
        Path(path)
        if path is not None
        else default_controller_authority_path()
    )

    if not resolved.is_file():
        raise GuardianControllerAuthorityError(
            "Guardian controller authority file does not exist"
        )

    try:
        _harden_private_path(
            resolved.parent,
            directory=True,
        )

        _harden_private_path(
            resolved,
            directory=False,
        )

        raw = resolved.read_bytes()

    except GuardianControllerAuthorityError:
        raise
    except Exception as exc:
        raise GuardianControllerAuthorityError(
            "Guardian controller authority could not be read safely"
        ) from exc

    try:
        secret = raw.decode(
            "utf-8"
        )
    except UnicodeDecodeError as exc:
        raise GuardianControllerAuthorityError(
            "Guardian controller authority must be valid UTF-8"
        ) from exc

    secret = secret.strip()

    if not secret:
        raise GuardianControllerAuthorityError(
            "Guardian controller authority must be non-empty"
        )

    if "\x00" in secret:
        raise GuardianControllerAuthorityError(
            "Guardian controller authority contains invalid data"
        )

    return secret
