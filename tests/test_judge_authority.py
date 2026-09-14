"""Tests for isolated Guardian Judge/Test authority state."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from ucii_guardian.action import ActionRequest
from ucii_guardian.authority import AuthorityDecision
from ucii_guardian.identity import (
    GUARDIAN_VERIFIED,
    GuardianIdentityConfig,
    GuardianIdentityVerification,
)
from ucii_guardian.judge_authority import (
    JUDGE_ACTIVE,
    JUDGE_NOT_GRANTED,
    JUDGE_REVOKED,
    JudgeAuthorityError,
    JudgeAuthorityState,
)


IDENTITY_ID = (
    "35c1db3d-61d7-4d0d-a5d7-db3ab7f79520"
)

CREDENTIAL_ID = (
    "9e2ee693-ca6d-426a-80ae-cf226e69c1e6"
)

FINGERPRINT = (
    "9d14f6f5a53629709afb1574ef9d14be"
    "ad52d6da5ecb1334cfaf930abd321559"
)

OPERATION = "guardian.purchase.office_supply"


@pytest.fixture
def config(
    tmp_path: Path,
) -> GuardianIdentityConfig:
    return GuardianIdentityConfig(
        base_url="https://api.ucii.sportgen-ai.com",
        identity_id=IDENTITY_ID,
        credential_id=CREDENTIAL_ID,
        credential_fingerprint=FINGERPRINT,
        custody_path=tmp_path / "guardian-mldsa65-v2.json",
    )


@pytest.fixture
def identity() -> GuardianIdentityVerification:
    return GuardianIdentityVerification(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        status=GUARDIAN_VERIFIED,
    )


@pytest.fixture
def action() -> ActionRequest:
    return ActionRequest(
        requester="human:test",
        guardian_identity=IDENTITY_ID,
        operation=OPERATION,
        target="office-supply:printer-cartridge",
        parameters={
            "quantity": 1,
            "max_price_usd": 35,
        },
        request_id="judge-request-1",
        requested_at=datetime(
            2026,
            9,
            14,
            16,
            10,
            tzinfo=timezone.utc,
        ),
    )


@pytest.fixture
def state() -> JudgeAuthorityState:
    return JudgeAuthorityState(
        identity_id=IDENTITY_ID,
        credential_fingerprint=FINGERPRINT,
        operation=OPERATION,
    )


def test_initial_state_is_not_granted_and_requires_escalation(
    state,
    action,
    identity,
    config,
) -> None:
    result = state.check(
        action,
        identity=identity,
        config=config,
    )

    assert state.authority_state == JUDGE_NOT_GRANTED
    assert state.active_authority_id is None

    assert (
        result.decision
        is AuthorityDecision.ESCALATION_REQUIRED
    )
    assert result.authority_state == "NOT_GRANTED"
    assert result.authority_id is None
    assert result.identity_id == IDENTITY_ID
    assert result.credential_fingerprint == FINGERPRINT
    assert result.operation == OPERATION
    assert result.request_id == action.request_id


def test_grant_creates_fresh_active_authority(
    state,
    action,
    identity,
    config,
) -> None:
    assert state.grant() == JUDGE_ACTIVE

    authority_id = state.active_authority_id

    assert authority_id is not None
    assert authority_id.startswith(
        "judge-test-authority-"
    )

    result = state.check(
        action,
        identity=identity,
        config=config,
    )

    assert result.decision is AuthorityDecision.ALLOW
    assert result.authority_state == "ACTIVE"
    assert result.authority_id == authority_id


def test_revoke_causes_fresh_check_to_deny(
    state,
    action,
    identity,
    config,
) -> None:
    state.grant()

    active = state.check(
        action,
        identity=identity,
        config=config,
    )

    assert active.decision is AuthorityDecision.ALLOW

    assert state.revoke() == JUDGE_REVOKED

    revoked = state.check(
        action,
        identity=identity,
        config=config,
    )

    assert revoked.decision is AuthorityDecision.DENY
    assert revoked.authority_state == "REVOKED"
    assert revoked.authority_id is None
    assert state.active_authority_id is None


def test_reset_restores_known_initial_state_and_new_grant(
    state,
    action,
    identity,
    config,
) -> None:
    state.grant()
    first_authority_id = state.active_authority_id

    state.revoke()

    assert state.reset() == JUDGE_NOT_GRANTED

    reset_result = state.check(
        action,
        identity=identity,
        config=config,
    )

    assert (
        reset_result.decision
        is AuthorityDecision.ESCALATION_REQUIRED
    )
    assert reset_result.authority_state == "NOT_GRANTED"
    assert reset_result.authority_id is None

    state.grant()
    second_authority_id = state.active_authority_id

    assert first_authority_id is not None
    assert second_authority_id is not None
    assert second_authority_id != first_authority_id


def test_revoked_authority_requires_reset_before_new_grant(
    state,
) -> None:
    state.grant()
    state.revoke()

    with pytest.raises(
        JudgeAuthorityError,
        match="requires NOT_GRANTED",
    ):
        state.grant()

    state.reset()

    assert state.grant() == JUDGE_ACTIVE


def test_invalid_lifecycle_transitions_fail_closed(
    state,
) -> None:
    with pytest.raises(
        JudgeAuthorityError,
        match="revocation requires ACTIVE",
    ):
        state.revoke()

    state.grant()

    with pytest.raises(
        JudgeAuthorityError,
        match="grant requires NOT_GRANTED",
    ):
        state.grant()


def test_checker_rejects_identity_or_scope_mismatch(
    state,
    action,
    identity,
    config,
) -> None:
    wrong_identity = GuardianIdentityVerification(
        identity_id="different-identity",
        credential_fingerprint=FINGERPRINT,
        status=GUARDIAN_VERIFIED,
    )

    with pytest.raises(
        JudgeAuthorityError,
        match="does not match Guardian configuration",
    ):
        state.check(
            action,
            identity=wrong_identity,
            config=config,
        )

    wrong_operation = ActionRequest(
        requester=action.requester,
        guardian_identity=action.guardian_identity,
        operation="guardian.purchase.other",
        target=action.target,
        parameters=dict(action.parameters),
        request_id="judge-request-wrong-operation",
        requested_at=action.requested_at,
    )

    with pytest.raises(
        JudgeAuthorityError,
        match="outside Judge authority scope",
    ):
        state.check(
            wrong_operation,
            identity=identity,
            config=config,
        )


def test_module_contains_no_ucii_client_or_production_lifecycle_dependency(
) -> None:
    source = Path(
        __import__(
            "ucii_guardian.judge_authority",
            fromlist=["__file__"],
        ).__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "UCIIClient" not in source
    assert "authority_lifecycle" not in source
    assert "grant_standing_authority" not in source
    assert "revoke_active_authority" not in source
